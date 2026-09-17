"""TOTP 2FA service.

Handles TOTP secret generation, two-phase enrollment, verification,
and single-use recovery code management following RFC 6238 standard.
"""
import uuid
import secrets
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Any

import pyotp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import encrypt_value, decrypt_value, get_password_hash, verify_password
from app.models.totp import TOTPSecret, RecoveryCode
from app.models.user import User

logger = logging.getLogger(__name__)


def _parse_uuid(val: Any) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


@dataclass
class TOTPSetupResult:
    """Result from TOTP setup (phase 1: pending activation)."""
    secret: str
    qr_uri: str
    recovery_codes: list[str] = field(default_factory=list)


@dataclass
class TOTPVerifyResult:
    """Result from TOTP verification."""
    is_valid: bool
    is_recovery_code: bool = False
    remaining_codes: int = 0


def _generate_recovery_codes(count: int = None) -> list[str]:
    """Generate cryptographically secure recovery codes."""
    if count is None:
        count = settings.RECOVERY_CODE_COUNT or 10
    return [secrets.token_urlsafe(8) for _ in range(count)]


def setup_totp(db: Session, user_id: Any) -> TOTPSetupResult:
    """Generate a new unconfirmed TOTP secret for a user.

    In accordance with Phase 7 of the 2FA spec:
    Calling setup alone MUST NEVER activate 2FA or generate recovery codes.
    Activation only occurs when the user calls confirm_totp with a valid code.
    """
    user_uuid = _parse_uuid(user_id)
    user = db.query(User).filter(User.id == user_uuid).first()
    user_label = user.email if user and user.email else str(user_uuid)

    # Generate a new TOTP secret
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)

    # Build provisioning URI for QR code scanning
    qr_uri = totp.provisioning_uri(
        name=user_label,
        issuer_name=settings.TOTP_ISSUER_NAME,
    )

    # Replace or create unconfirmed TOTPSecret record
    existing = db.query(TOTPSecret).filter(TOTPSecret.user_id == user_uuid).first()
    if existing:
        existing.encrypted_secret = encrypt_value(secret)
        existing.is_confirmed = False
    else:
        totp_record = TOTPSecret(
            user_id=user_uuid,
            encrypted_secret=encrypt_value(secret),
            is_confirmed=False,
        )
        db.add(totp_record)

    db.commit()

    return TOTPSetupResult(
        secret=secret,
        qr_uri=qr_uri,
        recovery_codes=[],
    )


def confirm_totp(db: Session, user_id: Any, code: str) -> Optional[list[str]]:
    """Confirm TOTP enrollment with first code and activate 2FA.

    On successful verification:
    1. Sets totp_secret.is_confirmed = True
    2. Sets user.is_2fa_enabled = True
    3. Generates, hashes, and stores single-use recovery codes
    4. Returns plaintext recovery codes list (shown once to user)

    Returns None if verification fails or no pending secret exists.
    """
    user_uuid = _parse_uuid(user_id)
    totp_record = db.query(TOTPSecret).filter(TOTPSecret.user_id == user_uuid).first()
    if not totp_record:
        return None

    secret = decrypt_value(totp_record.encrypted_secret)
    if not secret:
        logger.error(f"Failed to decrypt TOTP secret for user {user_uuid}")
        return None

    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        return None

    # Code is valid - activate 2FA
    totp_record.is_confirmed = True

    user = db.query(User).filter(User.id == user_uuid).first()
    if user:
        user.is_2fa_enabled = True

    # Generate single-use recovery codes
    recovery_codes = _generate_recovery_codes()

    # Clear old recovery codes for this user
    db.query(RecoveryCode).filter(RecoveryCode.user_id == user_uuid).delete()

    # Store hashed recovery codes (using secure password hasher)
    for rc in recovery_codes:
        rec_record = RecoveryCode(
            user_id=user_uuid,
            code_hash=get_password_hash(rc),
            is_used=False,
        )
        db.add(rec_record)

    db.commit()
    return recovery_codes


def verify_totp(db: Session, user_id: Any, code: str) -> TOTPVerifyResult:
    """Verify a TOTP code or recovery code.

    Only confirmed TOTP credentials are used.
    Recovery codes are verified and atomically marked as used.
    """
    user_uuid = _parse_uuid(user_id)

    # 1. Try TOTP code verification against confirmed secret
    totp_record = (
        db.query(TOTPSecret)
        .filter(TOTPSecret.user_id == user_uuid, TOTPSecret.is_confirmed == True)
        .first()
    )

    if totp_record:
        secret = decrypt_value(totp_record.encrypted_secret)
        if secret:
            totp = pyotp.TOTP(secret)
            if totp.verify(code, valid_window=1):
                return TOTPVerifyResult(is_valid=True, is_recovery_code=False)

    # 2. Try recovery codes (if TOTP failed or user entered a recovery code)
    active_recovery_codes = (
        db.query(RecoveryCode)
        .filter(RecoveryCode.user_id == user_uuid, RecoveryCode.is_used == False)
        .all()
    )

    for recovery in active_recovery_codes:
        if verify_password(code, recovery.code_hash):
            # Atomically mark as used
            recovery.is_used = True
            db.commit()
            remaining = len([r for r in active_recovery_codes if not r.is_used]) - 1
            return TOTPVerifyResult(
                is_valid=True,
                is_recovery_code=True,
                remaining_codes=max(0, remaining),
            )

    return TOTPVerifyResult(is_valid=False)


def regenerate_recovery_codes(db: Session, user_id: Any) -> list[str]:
    """Regenerate single-use recovery codes for a 2FA-enabled user.
    Existing codes are invalidated.
    """
    user_uuid = _parse_uuid(user_id)
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user or not user.is_2fa_enabled:
        raise ValueError("2FA is not enabled for this user")

    recovery_codes = _generate_recovery_codes()

    # Invalidate previous codes
    db.query(RecoveryCode).filter(RecoveryCode.user_id == user_uuid).delete()

    for rc in recovery_codes:
        rec_record = RecoveryCode(
            user_id=user_uuid,
            code_hash=get_password_hash(rc),
            is_used=False,
        )
        db.add(rec_record)

    db.commit()
    return recovery_codes


def get_totp_status(db: Session, user_id: Any) -> dict:
    """Get the current 2FA status for a user."""
    user_uuid = _parse_uuid(user_id)
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        return {"enabled": False, "configured": False, "recovery_codes_remaining": 0}

    totp_record = (
        db.query(TOTPSecret)
        .filter(TOTPSecret.user_id == user_uuid, TOTPSecret.is_confirmed == True)
        .first()
    )
    recovery_count = (
        db.query(RecoveryCode)
        .filter(RecoveryCode.user_id == user_uuid, RecoveryCode.is_used == False)
        .count()
    )

    return {
        "enabled": bool(user.is_2fa_enabled),
        "configured": totp_record is not None,
        "recovery_codes_remaining": recovery_count,
    }


def disable_totp(db: Session, user_id: Any) -> bool:
    """Disable 2FA and remove all TOTP data for a user.

    Returns True if 2FA was disabled, False if it wasn't enabled.
    """
    user_uuid = _parse_uuid(user_id)
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user or not user.is_2fa_enabled:
        return False

    db.query(TOTPSecret).filter(TOTPSecret.user_id == user_uuid).delete()
    db.query(RecoveryCode).filter(RecoveryCode.user_id == user_uuid).delete()

    user.is_2fa_enabled = False
    db.commit()
    return True
