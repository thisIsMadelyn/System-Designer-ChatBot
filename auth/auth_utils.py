import os
import hashlib
import hmac
import json
import base64
import time
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET  = os.getenv("JWT_SECRET", "change-me-in-production-please")
JWT_EXPIRY  = int(os.getenv("JWT_EXPIRY_HOURS", "24")) * 3600


# ─── Password hashing (pbkdf2 — no bcrypt needed) ───────────────

def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"{salt}:{key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, key_hex = hashed.split(":")
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


# ─── Minimal JWT (HS256, no PyJWT needed) ────────────────────────

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _sign(msg: str) -> str:
    sig = hmac.new(JWT_SECRET.encode(), msg.encode(), hashlib.sha256).digest()
    return _b64(sig)


def create_token(user_id: int, email: str, name: str) -> str:
    header  = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(json.dumps({
        "sub":   str(user_id),
        "email": email,
        "name":  name,
        "exp":   int(time.time()) + JWT_EXPIRY,
    }).encode())
    signature = _sign(f"{header}.{payload}")
    return f"{header}.{payload}.{signature}"


def decode_token(token: str) -> dict:
    try:
        header, payload, signature = token.split(".")
        expected = _sign(f"{header}.{payload}")
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid signature")
        data = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if data["exp"] < time.time():
            raise ValueError("Token expired")
        return data
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")