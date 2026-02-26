"""
HubMind Backend - JWT and password hashing
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

# Use a secret key from env in production
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hubmind-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# bcrypt 只接受最多 72 字节的密码
BCRYPT_MAX_BYTES = 72


def _password_to_bytes(password: str) -> bytes:
    """转为字节并截断为最多 72 字节，避免 bcrypt 报错。"""
    if not password:
        return b""
    raw = password.encode("utf-8")
    return raw[:BCRYPT_MAX_BYTES] if len(raw) > BCRYPT_MAX_BYTES else raw


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            _password_to_bytes(plain_password),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        _password_to_bytes(password),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
