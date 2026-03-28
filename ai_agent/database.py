import sqlite3
import json
from datetime import datetime, timedelta
from threading import Lock

DB_FILE = "omniuard.db"
lock = Lock()

SUBSCRIPTION_PLANS = {
    "month_1": {"days": 30, "price": 200, "name": "1 месяц"},
    "month_3": {"days": 90, "price": 450, "name": "3 месяца"},
    "month_6": {"days": 180, "price": 600, "name": "6 месяцев"},
}

def init_db():
    """Инициализация БД с таблицами"""
    with lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Таблица расширенных данных пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_extended (
                user_id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица подписок
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                plan_key TEXT NOT NULL,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users_extended(user_id)
            )
        """)
        
        # Таблица платежей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                yookassa_payment_id TEXT UNIQUE,
                plan_key TEXT NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'RUB',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users_extended(user_id)
            )
        """)
        
        # Таблица подарочных кодов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gift_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                plan_key TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                used_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP,
                is_used BOOLEAN DEFAULT 0,
                FOREIGN KEY (created_by) REFERENCES users_extended(user_id),
                FOREIGN KEY (used_by) REFERENCES users_extended(user_id)
            )
        """)
        
        conn.commit()
        conn.close()

def get_user_subscription(user_id: int):
    """Получить активную подписку пользователя"""
    with lock:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND is_active = 1 AND end_date > CURRENT_TIMESTAMP
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None

def has_active_subscription(user_id: int) -> bool:
    """Проверить есть ли активная подписка"""
    return get_user_subscription(user_id) is not None

def create_payment(user_id: int, plan_key: str) -> dict:
    """Создать запись платежа, возвращает ID платежа"""
    if plan_key not in SUBSCRIPTION_PLANS:
        raise ValueError(f"Unknown plan: {plan_key}")
    
    plan = SUBSCRIPTION_PLANS[plan_key]
    amount = plan["price"]
    
    with lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Убедиться что пользователь в таблице users_extended
        cursor.execute("INSERT OR IGNORE INTO users_extended (user_id) VALUES (?)", (user_id,))
        
        cursor.execute("""
            INSERT INTO payments (user_id, plan_key, amount, currency, status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, plan_key, amount, "RUB", "pending"))
        
        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()
    
    return {
        "payment_id": payment_id,
        "amount": amount,
        "plan_key": plan_key,
        "plan_name": plan["name"]
    }

def confirm_payment(yookassa_payment_id: str, user_id: int, plan_key: str) -> bool:
    """Подтвердить платёж и активировать подписку"""
    if plan_key not in SUBSCRIPTION_PLANS:
        return False
    
    plan = SUBSCRIPTION_PLANS[plan_key]
    end_date = datetime.now() + timedelta(days=plan["days"])
    
    with lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Убедиться что пользователь в таблице users_extended
            cursor.execute("INSERT OR IGNORE INTO users_extended (user_id) VALUES (?)", (user_id,))
            
            # Обновить платёж
            cursor.execute("""
                UPDATE payments 
                SET status = ?, yookassa_payment_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND plan_key = ? AND status = 'pending'
            """, ("succeeded", yookassa_payment_id, user_id, plan_key))
            
            # Удалить старую подписку если есть
            cursor.execute("UPDATE subscriptions SET is_active = 0 WHERE user_id = ?", (user_id,))
            
            # Создать новую подписку
            cursor.execute("""
                INSERT INTO subscriptions (user_id, plan_key, end_date)
                VALUES (?, ?, ?)
            """, (user_id, plan_key, end_date.isoformat()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Payment confirmation error: {e}")
            return False

def create_gift_code(owner_id: int, plan_key: str) -> str:
    """Создать подарочный код подписки"""
    if plan_key not in SUBSCRIPTION_PLANS:
        raise ValueError(f"Unknown plan: {plan_key}")
    
    import secrets
    code = secrets.token_urlsafe(16).upper()
    
    with lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("INSERT OR IGNORE INTO users_extended (user_id) VALUES (?)", (owner_id,))
        
        cursor.execute("""
            INSERT INTO gift_codes (code, plan_key, created_by)
            VALUES (?, ?, ?)
        """, (code, plan_key, owner_id))
        
        conn.commit()
        conn.close()
    
    return code

def redeem_gift_code(code: str, user_id: int) -> dict:
    """Активировать подарочный код"""
    with lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM gift_codes WHERE code = ? AND is_used = 0", (code,))
        gift = cursor.fetchone()
        
        if not gift:
            conn.close()
            return {"success": False, "error": "Код не найден или уже использован"}
        
        plan_key = gift[2]  # plan_key
        plan = SUBSCRIPTION_PLANS[plan_key]
        end_date = datetime.now() + timedelta(days=plan["days"])
        
        try:
            cursor.execute("INSERT OR IGNORE INTO users_extended (user_id) VALUES (?)", (user_id,))
            
            # Обновить код
            cursor.execute("""
                UPDATE gift_codes 
                SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP
                WHERE code = ?
            """, (user_id, code))
            
            # Удалить старую подписку
            cursor.execute("UPDATE subscriptions SET is_active = 0 WHERE user_id = ?", (user_id,))
            
            # Создать новую подписку
            cursor.execute("""
                INSERT INTO subscriptions (user_id, plan_key, end_date)
                VALUES (?, ?, ?)
            """, (user_id, plan_key, end_date.isoformat()))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "plan": plan_key,
                "plan_name": plan["name"]
            }
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

def get_subscription_status(user_id: int) -> dict:
    """Получить статус подписки пользователя"""
    sub = get_user_subscription(user_id)
    
    if not sub:
        return {
            "has_subscription": False,
            "message": "У вас нет активной подписки"
        }
    
    end_date = datetime.fromisoformat(sub["end_date"])
    days_left = (end_date - datetime.now()).days
    plan_name = SUBSCRIPTION_PLANS[sub["plan_key"]]["name"]
    
    return {
        "has_subscription": True,
        "plan": sub["plan_key"],
        "plan_name": plan_name,
        "end_date": sub["end_date"],
        "days_left": max(0, days_left)
    }

# Инициализировать БД при импорте
init_db()
