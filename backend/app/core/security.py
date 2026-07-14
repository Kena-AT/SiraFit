import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

import jwt
import uuid
from passlib.context import CryptContext
from app.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Symmetric encryption for user-stored API keys (AES-128-CBC via Fernet)
# ---------------------------------------------------------------------------

_fernet_instance = None


def _get_fernet():
    """Lazy-initialize Fernet with DATA_ENCRYPTION_KEY (or SECRET_KEY)."""
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance
    try:
        from cryptography.fernet import Fernet

        key = settings.DATA_ENCRYPTION_KEY or settings.SECRET_KEY
        if not key:
            logger.warning(
                "No DATA_ENCRYPTION_KEY or SECRET_KEY configured; user API key storage disabled."
            )
            return None
        # Fernet keys must be 32 bytes, URL-safe base64 encoded.
        # We'll derive a proper key using a stable hash if the raw key is too short/long.
        import hashlib

        key_bytes = hashlib.sha256(key.encode("utf-8")).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        _fernet_instance = Fernet(fernet_key)
        return _fernet_instance
    except ImportError:
        logger.warning(
            "'cryptography' not installed; user API key encryption disabled."
        )
        return None


def encrypt_value(value: str) -> Optional[str]:
    """Encrypt a string value. Returns None if encryption is unavailable."""
    if not value:
        return None
    fernet = _get_fernet()
    if fernet is None:
        return None
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(encrypted: str) -> Optional[str]:
    """Decrypt a previously encrypted string. Returns None on failure."""
    if not encrypted:
        return None
    fernet = _get_fernet()
    if fernet is None:
        return None
    try:
        return fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except Exception:
        logger.warning(
            "Failed to decrypt user API key; possibly corrupted or wrong DATA_ENCRYPTION_KEY."
        )
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: timedelta = None,
    token_type: str = "access",
) -> str:
    """Create JWT access or refresh token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        if token_type == "refresh":
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": token_type,
        "jti": str(uuid.uuid4()),  # Add unique ID for token revocation
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create a refresh token"""
    return create_access_token(subject, expires_delta, "refresh")


def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
