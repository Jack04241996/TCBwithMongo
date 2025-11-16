# security.py
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
ACCESS_TTL = int(os.getenv("ACCESS_EXPIRES_SECONDS", "1800"))  # 30min

def create_jwt(claims: dict, expires_in: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    ttl = expires_in if expires_in is not None else ACCESS_TTL
    to_encode = {
        **claims,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
