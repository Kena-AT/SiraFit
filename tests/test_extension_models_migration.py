import uuid
import pytest
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.extension_token import ExtensionToken
from app.models.user import User
from app.services.extension_service import hash_token, authenticate_extension_token


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_extension_token_model_and_hash_lookup(db):
    user = User(
        email=f"token_test_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Token Test",
        hashed_password=get_password_hash("Pass123!"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_token = f"srf_ext_{uuid.uuid4().hex}"
    t_hash = hash_token(raw_token)
    expires = datetime.now(timezone.utc) + timedelta(days=7)

    token_record = ExtensionToken(
        user_id=user.id,
        token_hash=t_hash,
        name="Chrome",
        expires_at=expires,
        is_revoked=False,
    )
    db.add(token_record)
    db.commit()
    db.refresh(token_record)

    # 1. Look up by hash
    found = db.query(ExtensionToken).filter(ExtensionToken.token_hash == t_hash).first()
    assert found is not None
    assert found.user_id == user.id
    assert found.name == "Chrome"

    # 2. Authenticate
    auth_user = authenticate_extension_token(db, raw_token)
    assert auth_user is not None
    assert auth_user.id == user.id

    # 3. Cascade on user delete
    db.delete(user)
    db.commit()

    orphaned = db.query(ExtensionToken).filter(ExtensionToken.token_hash == t_hash).first()
    assert orphaned is None


def test_expired_token_rejected(db):
    user = User(
        email=f"expired_test_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Expired Test",
        hashed_password=get_password_hash("Pass123!"),
        is_active=True,
    )
    db.add(user)
    db.commit()

    raw_token = f"srf_ext_{uuid.uuid4().hex}"
    t_hash = hash_token(raw_token)
    expired_date = datetime.now(timezone.utc) - timedelta(hours=1)

    token_record = ExtensionToken(
        user_id=user.id,
        token_hash=t_hash,
        name="Old Token",
        expires_at=expired_date,
        is_revoked=False,
    )
    db.add(token_record)
    db.commit()

    auth_user = authenticate_extension_token(db, raw_token)
    assert auth_user is None

    # Cleanup
    db.delete(user)
    db.commit()
