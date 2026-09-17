import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.security import encrypt_value, decrypt_value
from app.models.user_session import UserSession
from app.models.session_access_log import SessionAccessLog

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_session_data(platform: str, session_data: Dict[str, Any]) -> None:
    """Validate structure of session credential input.

    Ensures cookies exist and are string-string mappings, and optional fields
    conform to expected types.
    """
    if not isinstance(session_data, dict):
        raise ValueError("Session data must be a dictionary")

    cookies = session_data.get("cookies")
    if not isinstance(cookies, dict) or not cookies:
        raise ValueError("Cookies must be a non-empty dictionary of string key-value pairs")

    for k, v in cookies.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError("All cookie names and values must be strings")

    headers = session_data.get("headers")
    if headers is not None:
        if not isinstance(headers, dict):
            raise ValueError("Headers must be a dictionary of string key-value pairs")
        for hk, hv in headers.items():
            if not isinstance(hk, str) or not isinstance(hv, str):
                raise ValueError("All header names and values must be strings")

    user_agent = session_data.get("user_agent")
    if user_agent is not None and not isinstance(user_agent, str):
        raise ValueError("User-Agent must be a string")


def record_session_audit(
    db: Session,
    user_id: uuid.UUID,
    platform: str,
    action: str,
    result: str,
    error_code: Optional[str] = None,
) -> Optional[SessionAccessLog]:
    """Lightweight audit recording. NEVER passes secrets to this function."""
    try:
        log = SessionAccessLog(
            user_id=user_id,
            platform=platform,
            action=action,
            result=result,
            error_code=error_code,
            created_at=_utcnow(),
        )
        db.add(log)
        db.commit()
        return log
    except Exception as exc:
        logger.warning(
            "session_audit_log_failed",
            extra={"action": action, "platform": platform, "error": str(exc)},
        )
        db.rollback()
        return None


def store_user_session(
    db: Session,
    user_id: uuid.UUID,
    platform: str,
    session_data: Dict[str, Any],
    expires_at: Optional[datetime] = None,
) -> UserSession:
    """Validate, encrypt, and store user platform session.

    Never logs or persists plaintext credentials.
    """
    validate_session_data(platform, session_data)

    payload_json = json.dumps(session_data)
    encrypted = encrypt_value(payload_json)
    if not encrypted:
        record_session_audit(
            db, user_id, platform, action="stored", result="failure", error_code="encryption_failed"
        )
        raise RuntimeError("Failed to encrypt session credentials. Encryption service unavailable.")

    # Check if active session already exists for this user and platform
    session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user_id,
            UserSession.platform == platform,
            UserSession.is_active == True,
        )
        .first()
    )

    now = _utcnow()
    if session:
        session.encrypted_session_data = encrypted
        session.stored_at = now
        session.expires_at = expires_at or session_data.get("expires_at")
        session.is_active = True
        session.updated_at = now
    else:
        session = UserSession(
            user_id=user_id,
            platform=platform,
            encrypted_session_data=encrypted,
            stored_at=now,
            expires_at=expires_at or session_data.get("expires_at"),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(session)

    db.commit()
    db.refresh(session)

    record_session_audit(db, user_id, platform, action="stored", result="success")
    return session


def get_user_session(
    db: Session,
    user_id: uuid.UUID,
    platform: str,
    decrypt: bool = True,
) -> Tuple[Optional[UserSession], Optional[Dict[str, Any]]]:
    """Retrieve and optionally decrypt active user session.

    Returns (session_record, decrypted_data_or_None).
    If expired or decryption fails, decrypted_data will be None.
    """
    session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user_id,
            UserSession.platform == platform,
            UserSession.is_active == True,
        )
        .first()
    )

    if not session:
        return None, None

    # Expiration check
    if session.expires_at is not None:
        exp = session.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < _utcnow():
            record_session_audit(
                db, user_id, platform, action="expired", result="failure", error_code="session_expired"
            )
            return session, None

    if not decrypt:
        return session, None

    # Decrypt in memory
    decrypted_str = decrypt_value(session.encrypted_session_data)
    if not decrypted_str:
        record_session_audit(
            db, user_id, platform, action="failed", result="failure", error_code="decryption_failed"
        )
        return session, None

    try:
        data = json.loads(decrypted_str)
    except Exception:
        record_session_audit(
            db, user_id, platform, action="failed", result="failure", error_code="invalid_payload_json"
        )
        return session, None

    session.last_used_at = _utcnow()
    db.commit()
    db.refresh(session)

    record_session_audit(db, user_id, platform, action="used", result="success")
    return session, data


def delete_user_session(db: Session, user_id: uuid.UUID, platform: str) -> bool:
    """Soft-delete the active session for user and platform."""
    session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user_id,
            UserSession.platform == platform,
            UserSession.is_active == True,
        )
        .first()
    )

    if not session:
        record_session_audit(
            db, user_id, platform, action="deleted", result="failure", error_code="session_not_found"
        )
        return False

    session.is_active = False
    session.updated_at = _utcnow()
    db.commit()

    record_session_audit(db, user_id, platform, action="deleted", result="success")
    return True


def list_user_sessions(db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Return safe metadata of all active stored sessions.

    NEVER returns raw cookies, headers, or encrypted data.
    """
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.is_active == True)
        .order_by(UserSession.created_at.desc())
        .all()
    )

    return [
        {
            "platform": s.platform,
            "stored_at": s.stored_at,
            "expires_at": s.expires_at,
            "last_used_at": s.last_used_at,
        }
        for s in sessions
    ]


def enqueue_session_import(import_id: str, platform: str, user_id: str) -> Dict[str, Any]:
    """Dispatch a saved jobs discovery to the Celery scraping queue."""
    try:
        from app.worker.tasks.session_import import import_saved_jobs_task

        import_saved_jobs_task.delay(
            user_id=str(user_id),
            import_id=str(import_id),
            platform=platform,
        )
        return {"queued": True}
    except Exception as exc:
        logger.warning(
            "celery_broker_unavailable_session_fallback", extra={"error": str(exc)}
        )
        try:
            from app.worker.tasks.session_import import import_saved_jobs_task

            import_saved_jobs_task.run(
                user_id=str(user_id),
                import_id=str(import_id),
                platform=platform,
            )
        except Exception as sync_exc:
            logger.error(
                "sync_fallback_session_import_failed", extra={"error": str(sync_exc)}
            )
        return {"queued": False}

