from flask import Flask, request, jsonify
from payments import handle_payment_webhook, verify_webhook, YookassaPaymentError
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/webhook/yookassa", methods=["POST"])
def yookassa_webhook():
    """Вебхук для подтверждения платежей от Yookassa"""
    
    try:
        # Получить подпись и тело запроса
        signature = request.headers.get("X-Yookassa-Webhook-Signature")
        body = request.get_data(as_text=True)
        
        if not signature or not body:
            return jsonify({"error": "Missing signature or body"}), 400
        
        # Проверить подпись
        webhook_data = verify_webhook(body, signature)
        
        # Обработать вебхук
        success = handle_payment_webhook(webhook_data)
        
        if success:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"error": "Processing failed"}), 500
    
    except YookassaPaymentError as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal error"}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
