"""TOTP 2FA service.

Handles TOTP secret generation, verification, and recovery code management
following RFC 6238 standard.
"""
import secrets
import logging
from dataclasses import dataclass, field
from typing import Optional

import pyotp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import encrypt_value, decrypt_value, get_password_hash
from app.models.totp import TOTPSecret, RecoveryCode
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class TOTPSetupResult:
    """Result from TOTP setup."""
    secret: str
    qr_uri: str
    recovery_codes: list[str]


@dataclass
class TOTPVerifyResult:
    """Result from TOTP verification."""
    is_valid: bool
    is_recovery_code: bool = False
    remaining_codes: int = 0


def _generate_recovery_codes(count: int = None) -> list[str]:
    """Generate cryptographically secure recovery codes."""
    if count is None:
        count = settings.RECOVERY_CODE_COUNT
    return [secrets.token_urlsafe(8) for _ in range(count)]


def setup_totp(db: Session, user_id: str) -> TOTPSetupResult:
    """Generate a new TOTP secret and recovery codes for a user.

    If the user already has 2FA enabled, this replaces the existing secret.
    """
    # Generate a new TOTP secret
    secret = pyotp.random_base32()

    # Create the TOTP object for QR code generation
    totp = pyotp.TOTP(secret)

    # Build the provisioning URI for QR code scanning
    qr_uri = totp.provisioning_uri(
        name=user_id,
        issuer_name=settings.TOTP_ISSUER_NAME,
    )

    # Generate recovery codes
    recovery_codes = _generate_recovery_codes()

    # Delete existing TOTP secret if any
    existing = db.query(TOTPSecret).filter(TOTPSecret.user_id == user_id).first()
    if existing:
        db.delete(existing)

    # Delete existing recovery codes
    db.query(RecoveryCode).filter(RecoveryCode.user_id == user_id).delete()

    # Store encrypted TOTP secret
    totp_record = TOTPSecret(
        user_id=user_id,
        encrypted_secret=encrypt_value(secret),
    )
    db.add(totp_record)

    # Store hashed recovery codes
    for code in recovery_codes:
        recovery_record = RecoveryCode(
            user_id=user_id,
            code_hash=get_password_hash(code),
        )
        db.add(recovery_record)

    # Enable 2FA on the user
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_2fa_enabled = True

    db.commit()

    return TOTPSetupResult(
        secret=secret,
        qr_uri=qr_uri,
        recovery_codes=recovery_codes,
    )


def verify_totp(db: Session, user_id: str, code: str) -> TOTPVerifyResult:
    """Verify a TOTP code or recovery code.

    Returns whether the code is valid and whether it was a recovery code.
    """
    # Get the user's TOTP secret
    totp_record = db.query(TOTPSecret).filter(TOTPSecret.user_id == user_id).first()
    if not totp_record:
        return TOTPVerifyResult(is_valid=False)

    # Decrypt the secret
    secret = decrypt_value(totp_record.encrypted_secret)
    if not secret:
        logger.error(f"Failed to decrypt TOTP secret for user {user_id}")
        return TOTPVerifyResult(is_valid=False)

    # Try TOTP verification first (most common case)
    totp = pyotp.TOTP(secret)
    if totp.verify(code, valid_window=1):
        return TOTPVerifyResult(is_valid=True, is_recovery_code=False)

    # Try recovery codes
    recovery_codes = (
        db.query(RecoveryCode)
        .filter(RecoveryCode.user_id == user_id, RecoveryCode.is_used == False)
        .all()
    )

    for recovery in recovery_codes:
        if get_password_hash(code) == recovery.code_hash:
            # Mark this recovery code as used
            recovery.is_used = True
            db.commit()
            remaining = len([r for r in recovery_codes if not r.is_used]) - 1
            return TOTPVerifyResult(
                is_valid=True,
                is_recovery_code=True,
                remaining_codes=max(0, remaining),
            )

    return TOTPVerifyResult(is_valid=False)


def get_totp_status(db: Session, user_id: str) -> dict:
    """Get the current 2FA status for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"enabled": False, "configured": False}

    totp_record = db.query(TOTPSecret).filter(TOTPSecret.user_id == user_id).first()
    recovery_count = (
        db.query(RecoveryCode)
        .filter(RecoveryCode.user_id == user_id, RecoveryCode.is_used == False)
        .count()
    )

    return {
        "enabled": user.is_2fa_enabled,
        "configured": totp_record is not None,
        "recovery_codes_remaining": recovery_count,
    }


def disable_totp(db: Session, user_id: str) -> bool:
    """Disable 2FA and remove all TOTP data for a user.

    Returns True if 2FA was disabled, False if it wasn't enabled.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_2fa_enabled:
        return False

    # Delete TOTP secret
    db.query(TOTPSecret).filter(TOTPSecret.user_id == user_id).delete()

    # Delete recovery codes
    db.query(RecoveryCode).filter(RecoveryCode.user_id == user_id).delete()

    # Disable 2FA on user
    user.is_2fa_enabled = False
    db.commit()

    return True
