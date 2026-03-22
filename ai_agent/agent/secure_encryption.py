import os
import base64
import hashlib
import hmac
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

MASTER_KEY = os.getenv("OMNIGUARD_SECRET")
if not MASTER_KEY:
    raise ValueError("OMNIGUARD_SECRET not set")

MASTER_KEY = MASTER_KEY.encode()


def derive_user_key(user_id: str, salt: str) -> bytes:
    salt_bytes = base64.urlsafe_b64decode(salt.encode())

    kdf = hashlib.pbkdf2_hmac(
        "sha256",
        user_id.encode() + MASTER_KEY,
        salt_bytes,
        200_000
    )

    return base64.urlsafe_b64encode(kdf)


def generate_salt() -> str:
    return base64.urlsafe_b64encode(os.urandom(16)).decode()


def encrypt_for_user(user_id: str, data: str, salt: str) -> bytes:
    key = derive_user_key(user_id, salt)
    f = Fernet(key)

    encrypted = f.encrypt(data.encode())

    signature = hmac.new(MASTER_KEY, encrypted, hashlib.sha256).digest()

    return signature + encrypted


def decrypt_for_user(user_id: str, token: bytes, salt: str) -> str:
    signature = token[:32]
    encrypted = token[32:]

    expected = hmac.new(MASTER_KEY, encrypted, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise Exception("Data tampering detected")

    key = derive_user_key(user_id, salt)
    f = Fernet(key)

    return f.decrypt(encrypted).decode()
