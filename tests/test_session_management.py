"""
Tests for Session Management Service (Sprint 5).

Verifies encrypted storage, secure retrieval, deletion, expiration handling,
and audit logging for platform session credentials.
"""

from datetime import datetime, timezone, timedelta
from app.models.user_session import UserSession
from app.models.session_access_log import SessionAccessLog
from app.services.session_management import (
    store_user_session,
    get_user_session,
    delete_user_session,
    list_user_sessions,
)
from app.core.security import decrypt_value


def test_store_user_session_encrypts_data(db, test_user):
    """Verify session data is encrypted at rest and audit log is created."""
    session_data = {
        "cookies": {"li_at": "AQED_TEST_COOKIE_12345", "JSESSIONID": "ajax:998877"}
    }

    session = store_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
        session_data=session_data,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    assert session.id is not None
    assert session.user_id == test_user.id
    assert session.platform == "linkedin"
    assert session.is_active is True
    assert session.encrypted_session_data is not None

    # Verify encrypted data is NOT plaintext in the database
    raw_in_db = db.query(UserSession).filter_by(id=session.id).first()
    assert "AQED_TEST_COOKIE_12345" not in raw_in_db.encrypted_session_data
    assert "ajax:998877" not in raw_in_db.encrypted_session_data

    # Verify decrypting the raw column retrieves the original JSON
    decrypted_str = decrypt_value(raw_in_db.encrypted_session_data)
    assert "AQED_TEST_COOKIE_12345" in decrypted_str

    # Verify audit log recorded
    logs = db.query(SessionAccessLog).filter_by(user_id=test_user.id).all()
    assert len(logs) == 1
    assert logs[0].action == "stored"
    assert logs[0].result == "success"
    assert logs[0].platform == "linkedin"


def test_get_user_session_decrypts_data(db, test_user):
    """Verify retrieving session returns decrypted cookies."""
    session_data = {"cookies": {"CTK": "indeed_cookie_tok", "CSRF": "csrf_token_xyz"}}

    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="indeed",
        session_data=session_data,
    )

    session_rec, retrieved = get_user_session(
        db=db,
        user_id=test_user.id,
        platform="indeed",
    )

    assert session_rec is not None
    assert retrieved is not None
    assert retrieved["cookies"]["CTK"] == "indeed_cookie_tok"
    assert retrieved["cookies"]["CSRF"] == "csrf_token_xyz"

    # Verify retrieval audit log
    logs = (
        db.query(SessionAccessLog).filter_by(user_id=test_user.id, action="used").all()
    )
    assert len(logs) == 1
    assert logs[0].result == "success"


def test_delete_user_session(db, test_user):
    """Verify session is deactivated on delete and subsequent lookups fail."""
    session_data = {"cookies": {"li_at": "linkedin_secret_token"}}

    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
        session_data=session_data,
    )

    deleted = delete_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
    )
    assert deleted is True

    # Lookup should now return (None, None)
    session_rec, retrieved = get_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
    )
    assert session_rec is None
    assert retrieved is None

    # Deleting non-existent session returns False
    deleted_again = delete_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
    )
    assert deleted_again is False


def test_session_expiration_handling(db, test_user):
    """Verify expired sessions return None for decrypted data."""
    # Store with expiration in the past
    session = UserSession(
        user_id=test_user.id,
        platform="linkedin",
        encrypted_session_data="dummy_ciphertext",
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(session)
    db.commit()

    session_rec, retrieved = get_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
    )
    assert session_rec is not None
    assert retrieved is None


def test_list_user_sessions_metadata_only(db, test_user):
    """Verify list_user_sessions returns metadata and never secrets."""
    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
        session_data={"cookies": {"li_at": "secret1"}},
    )
    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="indeed",
        session_data={"cookies": {"CTK": "secret2"}},
    )

    sessions = list_user_sessions(db=db, user_id=test_user.id)
    assert len(sessions) == 2

    platforms = {s["platform"] for s in sessions}
    assert platforms == {"linkedin", "indeed"}

    for s in sessions:
        assert "platform" in s
        assert "stored_at" in s
        assert "expires_at" in s
        assert "last_used_at" in s
        # Ensure credentials/ciphertext are never returned
        assert "cookies" not in s
        assert "encrypted_session_data" not in s


def test_audit_logs_contain_no_secrets(db, test_user):
    """Verify audit log table never stores cookie data."""
    cookies = {"li_at": "SUPER_SECRET_COOKIE_VAL_ABCXYZ"}
    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
        session_data={"cookies": cookies},
    )

    logs = db.query(SessionAccessLog).filter_by(user_id=test_user.id).all()
    for log in logs:
        assert (
            log.error_code is None
            or "SUPER_SECRET_COOKIE_VAL_ABCXYZ" not in log.error_code
        )
        assert log.action in ("stored", "used", "deleted", "expired", "failed")
