import json
import os
import base64
from threading import Lock

from agent.secure_encryption import (
    encrypt_for_user,
    decrypt_for_user,
    generate_salt
)

MEMORY_FILE = "memory.json"
lock = Lock()


def _load_all():
    if not os.path.exists(MEMORY_FILE):
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            secured = json.load(f)

        data = {}

        for user_id, user_data in secured.items():
            salt = user_data["salt"]
            encrypted = base64.b64decode(user_data["payload"])

            decrypted = decrypt_for_user(user_id, encrypted, salt)
            payload_data = json.loads(decrypted)

            data[user_id] = {
                "profile": {
                    **payload_data["profile"],
                    "salt": salt
                },
                "history": payload_data["history"]
            }

        return data

    except Exception:
        return {}


def _save_all(data):
    secured = {}

    for user_id, user_data in data.items():
        if "salt" not in user_data.get("profile", {}):
            user_data["profile"]["salt"] = generate_salt()

        salt = user_data["profile"]["salt"]

        payload_data = {
            "profile": {k: v for k, v in user_data["profile"].items() if k != "salt"},
            "history": user_data["history"]
        }

        encrypted = encrypt_for_user(
            user_id,
            json.dumps(payload_data, ensure_ascii=False),
            salt
        )

        secured[user_id] = {
            "salt": salt,
            "payload": base64.b64encode(encrypted).decode()
        }

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(secured, f, ensure_ascii=False, indent=2)


def get_user(user_id: int):
    with lock:
        data = _load_all()
        user_id = str(user_id)

        if user_id not in data:
            data[user_id] = {
                "profile": {
                    "salt": generate_salt()
                },
                "history": []
            }
            _save_all(data)

        return data[user_id]


def add_message(user_id: int, role: str, content: str):
    with lock:
        data = _load_all()
        user_id = str(user_id)

        if user_id not in data:
            data[user_id] = {
                "profile": {
                    "salt": generate_salt()
                },
                "history": []
            }

        content = content[:4000]

        data[user_id]["history"].append({
            "role": role,
            "content": content
        })

        data[user_id]["history"] = data[user_id]["history"][-20:]

        _save_all(data)


def get_history(user_id: int):
    user = get_user(user_id)
    return user["history"]
