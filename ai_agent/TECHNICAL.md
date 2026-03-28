# 🔧 OmniGuard - Техническая документация

## 📚 API и модули

### 1. Database Module (`database.py`)

Управление подписками, платежами и подарочными кодами.

#### Функции

```python
# Инициализировать БД
init_db()

# Проверить активную подписку
has_active_subscription(user_id: int) -> bool

# Получить статус подписки
get_subscription_status(user_id: int) -> dict

# Создать платёж
create_payment(user_id: int, plan_key: str) -> dict

# Подтвердить платёж
confirm_payment(yookassa_payment_id: str, user_id: int, plan_key: str) -> bool

# Создать подарочный код
create_gift_code(owner_id: int, plan_key: str) -> str

# Активировать подарочный код
redeem_gift_code(code: str, user_id: int) -> dict
```

#### Структура БД

```sql
-- Пользователи
CREATE TABLE users_extended (
    user_id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Подписки
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE,
    plan_key TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN
)

-- Платежи
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    yookassa_payment_id TEXT UNIQUE,
    plan_key TEXT,
    amount INTEGER,
    currency TEXT,
    status TEXT,  -- pending, succeeded, failed
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Подарочные коды
CREATE TABLE gift_codes (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE,
    plan_key TEXT,
    created_by INTEGER,
    used_by INTEGER,
    created_at TIMESTAMP,
    used_at TIMESTAMP,
    is_used BOOLEAN
)
```

### 2. Payments Module (`payments.py`)

Интеграция с Yookassa для обработки платежей.

#### Функции

```python
# Создать платёжную ссылку
create_payment_link(user_id: int, plan_key: str, return_url: str) -> dict

# Проверить подпись вебхука
verify_webhook(body: str, signature: str) -> dict

# Обработать вебхук платежа
handle_payment_webhook(webhook_data: dict) -> bool

# Получить статус платежа
get_payment_status(yookassa_id: str) -> dict
```

#### Пример ответа create_payment_link

```json
{
    "success": true,
    "yookassa_id": "22e12345-1234-1234-1234-123456789012",
    "payment_url": "https://yookassa.ru/...",
    "plan_name": "1 месяц",
    "amount": 200
}
```

### 3. Excel Generator (`tools/excel_generator.py`)

Создание стилизованных Excel файлов.

#### Методы

```python
gen = ExcelGenerator()

# Анализ товаров
gen.create_product_analysis(products_data: list) -> str

# Сравнение цен
gen.create_price_comparison(comparison_data: list) -> str

# Пользовательский отчёт
gen.create_custom_report(title: str, columns: list, data: list) -> str

# Отчёт о задолженности
gen.create_debt_report(debts_data: list) -> str
```

#### Структура данных

**Product Analysis**
```python
[{
    'name': 'Товар 1',
    'marketplace': 'Озон',
    'price': 5000.0,
    'rating': 4.5,
    'reviews': 120,
    'available': True,
    'description': 'Описание'
}]
```

**Price Comparison**
```python
[{
    'name': 'Товар 1',
    'ozon': 5000,
    'wildberries': 4800,
    'yandex_market': 5100,
    'min_price': 4800,
    'best_marketplace': 'Валберис'
}]
```

**Debt Report**
```python
[{
    'client': 'ООО Компания',
    'amount': 15000,
    'due_date': '2024-03-01',
    'days_overdue': 5,
    'status': 'Просрочено'
}]
```

### 4. Marketplace Parser (`tools/marketplace_parser.py`)

Парсинг товаров с маркетплейсов.

#### Классы

```python
# Озон
ozon = OzonParser()
products = ozon.parse("ноутбук")

# Валберис
wb = WildberriesParser()
products = wb.parse("смартфон")

# Яндекс Маркет
ym = YandexMarketParser()
products = ym.parse("кроссовки")

# Все маркетплейсы
registry = ParsersRegistry()
results = registry.parse_all("товар")
products_ozon = registry.parse_marketplace("ozon", "товар")
```

#### Структура результата

```python
{
    'name': 'Название товара',
    'marketplace': 'Озон',
    'price': 5000.0,
    'rating': 4.5,
    'reviews': 120,
    'available': True,
    'url': 'https://...'
}
```

### 5. File Splitter (`tools/file_splitter.py`)

Разбивка больших файлов для отправки в Telegram.

#### Функции

```python
# Проверить нужна ли разбивка
FileSplitter.needs_split(filepath: str) -> bool

# Разбить файл
success, parts = FileSplitter.split_file(filepath: str, output_dir: str) -> tuple

# Сообщение о разбивке
msg = FileSplitter.get_split_message(num_parts: int, filename: str) -> str

# Инструкции по сборке
instructions = FileSplitter.get_assembly_instructions(num_parts: int, filename: str) -> str
```

#### Лимиты

- Лимит Telegram: 50 MB (TELEGRAM_FILE_LIMIT)
- Автоматическая разбивка при превышении

## 🔌 Webhook Интеграция

### Flask приложение (`webhook.py`)

```python
# Запустить сервер
python webhook.py
# Сервер запустится на http://0.0.0.0:5000
```

#### Endpoints

**POST /webhook/yookassa**
- Получает вебхуки от Yookassa
- Проверяет подпись
- Обновляет статус платежа
- Активирует подписку при успехе

**GET /health**
- Проверка здоровья сервера

### Конфигурация вебхука в Yookassa

1. Зайдите в личный кабинет Yookassa
2. Перейдите в "Уведомления" → "Вебхуки"
3. Добавьте URL: `https://your-domain.com/webhook/yookassa`
4. Выберите события: "Платеж прошёл успешно"
5. Скопируйте Secret Key для подписи

## 🤖 AI Agent (`agent/core.py`)

### System Prompt

```
Ты OmniGuard — персональный AI ассистент в Telegram.
Ты умный, спокойный и структурированный.
Даёшь чёткие и полезные ответы без воды.
Не раскрываешь внутренние размышления.
Не прощаешься в конце ответа.
Учитываешь историю общения и стиль пользователя.
```

### Поддерживаемые инструменты

- `calculator` - Математические вычисления
- `unit_converter` - Конвертация единиц
- `marketplace_parser` - Парсинг маркетплейсов
- `price_comparison` - Сравнение цен
- `custom_report` - Создание пользовательских отчётов

## 🔒 Безопасность

### Шифрование памяти

```python
# Дешифровка истории чатов
from agent.secure_encryption import decrypt_for_user
decrypted = decrypt_for_user(user_id, encrypted_data, salt)

# Шифрование
encrypted = encrypt_for_user(user_id, plain_text, salt)
```

### Проверка подписей

```python
# В webhook.py
signature = request.headers.get("X-Yookassa-Webhook-Signature")
webhook_data = verify_webhook(body, signature)
```

## 📊 Мониторинг

### Логирование

```python
# Все события логируются в консоль
# Уровень: INFO

# Примеры:
# 📩 Новое сообщение: ...
# ⏳ Отправка запроса к модели...
# ✅ Ответ получен
# ✅ Платёж подтверждён
# ❌ Ошибка обработки
```

### База данных

```bash
# Посмотреть активные подписки
sqlite3 omniuard.db "SELECT * FROM subscriptions WHERE is_active = 1"

# Проверить платежи
sqlite3 omniuard.db "SELECT * FROM payments ORDER BY created_at DESC LIMIT 10"

# Просмотреть использованные коды
sqlite3 omniuard.db "SELECT * FROM gift_codes WHERE is_used = 1"
```

## 🚀 Развёртывание

### Production требования

1. **Зависимости**
```bash
pip install -r requirements.txt
```

2. **Переменные окружения** в .env
```env
TELEGRAM_TOKEN=...
OPENROUTER_API_KEY=...
YOOKASSA_SHOP_ID=...
YOOKASSA_SECRET_KEY=...
```

3. **Запуск бота**
```bash
python bot.py
```

4. **Запуск вебхука** (в отдельном окне/процессе)
```bash
python webhook.py
```

5. **Для production рекомендуется использовать**
- Gunicorn для Flask сервера
- systemd или Docker для управления процессами
- nginx как reverse proxy
- SSL сертификат для вебхука

### Docker (опционально)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "bot.py"]
```

## 🐛 Debugging

### Включить debug логирование

```python
# В bot.py
logging.basicConfig(level=logging.DEBUG)
```

### Проверить парсер

```python
from tools.marketplace_parser import OzonParser
parser = OzonParser()
results = parser.parse("ноутбук")
print(results)
```

### Проверить платежи

```python
from payments import get_payment_status
status = get_payment_status("yookassa_payment_id")
print(status)
```

---

**Версия**: 1.0.0  
**Последнее обновление**: 2024-03-28
