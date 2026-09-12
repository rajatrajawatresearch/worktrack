"""Password hashing (Argon2) and JWT access/refresh token helpers."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from app.core.config import settings

_ph = PasswordHasher()


# ---- Passwords ----
def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _ph.verify(password_hash, password)
        return True
    except Argon2Error:
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _ph.check_needs_rehash(password_hash)
    except Argon2Error:
        return False


# ---- Time ----
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---- JWT ----
def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id, role: str, company_id=None) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "role": role,
        "company_id": str(company_id) if company_id else None,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return _encode(payload)


def create_refresh_token(user_id, role: str, company_id=None) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at)."""
    now = utcnow()
    expires_at = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "role": role,
        "company_id": str(company_id) if company_id else None,
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return _encode(payload), jti, expires_at


def decode_token(token: str) -> dict:
    """Decodes and validates signature + expiry. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def hash_token(token: str) -> str:
    """SHA-256 hash used to store refresh tokens (never store the raw token)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
