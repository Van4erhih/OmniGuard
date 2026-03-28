import uuid
import hmac
import hashlib
import json
from datetime import datetime
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from database import create_payment, confirm_payment, SUBSCRIPTION_PLANS
import requests

YOOKASSA_API_URL = "https://api.yookassa.ru/v3"

class YookassaPaymentError(Exception):
    pass

def create_payment_link(user_id: int, plan_key: str, return_url: str) -> dict:
    """Создать платёж в Yookassa"""
    
    if plan_key not in SUBSCRIPTION_PLANS:
        raise YookassaPaymentError(f"Unknown plan: {plan_key}")
    
    plan = SUBSCRIPTION_PLANS[plan_key]
    
    # Создать запись платежа в БД
    payment_info = create_payment(user_id, plan_key)
    payment_id = payment_info["payment_id"]
    
    # Создать платёж в Yookassa
    idempotency_key = str(uuid.uuid4())
    
    payload = {
        "amount": {
            "value": str(plan["price"]),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url
        },
        "capture": True,
        "description": f"Подписка {plan['name']} - OmniGuard",
        "metadata": {
            "user_id": str(user_id),
            "plan_key": plan_key,
            "payment_id": str(payment_id)
        }
    }
    
    headers = {
        "Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{YOOKASSA_API_URL}/payments",
            json=payload,
            headers=headers,
            auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            error_data = response.json()
            raise YookassaPaymentError(f"Yookassa API error: {error_data}")
        
        yookassa_data = response.json()
        
        return {
            "success": True,
            "yookassa_id": yookassa_data["id"],
            "payment_url": yookassa_data["confirmation"]["confirmation_url"],
            "plan_name": plan["name"],
            "amount": plan["price"]
        }
    
    except requests.exceptions.RequestException as e:
        raise YookassaPaymentError(f"Network error: {e}")

def verify_webhook(body: str, signature: str) -> dict:
    """Проверить подпись вебхука Yookassa"""
    
    # Yookassa отправляет подпись в формате: Base64(sha256(body + secret_key))
    expected_signature = hmac.new(
        YOOKASSA_SECRET_KEY.encode(),
        body.encode(),
        hashlib.sha256
    ).digest()
    
    import base64
    expected_signature_b64 = base64.b64encode(expected_signature).decode()
    
    if signature != expected_signature_b64:
        raise YookassaPaymentError("Invalid webhook signature")
    
    return json.loads(body)

def handle_payment_webhook(webhook_data: dict) -> bool:
    """Обработать вебхук платежа"""
    
    try:
        if webhook_data.get("type") != "payment.succeeded":
            return False
        
        payment = webhook_data.get("object", {})
        yookassa_id = payment.get("id")
        status = payment.get("status")
        
        if status != "succeeded":
            return False
        
        metadata = payment.get("metadata", {})
        user_id = int(metadata.get("user_id"))
        plan_key = metadata.get("plan_key")
        
        # Подтвердить платёж в БД
        success = confirm_payment(yookassa_id, user_id, plan_key)
        
        if success:
            print(f"✅ Платёж {yookassa_id} подтверждён для пользователя {user_id}")
        
        return success
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return False

def get_payment_status(yookassa_id: str) -> dict:
    """Получить статус платежа из Yookassa"""
    
    try:
        response = requests.get(
            f"{YOOKASSA_API_URL}/payments/{yookassa_id}",
            auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
            timeout=10
        )
        
        if response.status_code != 200:
            raise YookassaPaymentError(f"Error: {response.status_code}")
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        raise YookassaPaymentError(f"Network error: {e}")
