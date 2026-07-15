"""
Shared pytest fixtures for backend tests.
Uses an in-memory SQLite database for speed — no external services needed.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Provide all required env vars BEFORE any app imports
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test_secret_key_not_for_production_use")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("SMTP_HOST", "smtp.example.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "dummy")
os.environ.setdefault("SMTP_FROM", "noreply@sirafit.com")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3030")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault(
    "REDIS_URL", "redis://localhost:6379/0"
)  # Use localhost for tests; sync fallback when no Redis
# In-process Celery so enqueue helpers fail the broker fast (memory://) and fall back to sync —
# without this, Celery retries the broker/redis result backend 20× with 1s backoff before the
# sync fallback fires, turning a <60s suite into ~8 minutes.
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

# Now import after env is set
from app.main import app as fastapi_app
from app.core.database import Base, get_db

# Import ALL models so SQLite creates every table
import app.models.user  # noqa: F401
import app.models.job  # noqa: F401
import app.models.profile  # noqa: F401
import app.models.cover_letter  # noqa: F401
import app.models.batch  # noqa: F401
import app.models.notification  # noqa: F401
import app.models.analytics  # noqa: F401

SQLALCHEMY_DATABASE_URL = "sqlite:///test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once per test session, then drop them."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(setup_db):
    """Shared test client for the whole session."""
    return TestClient(fastapi_app)


@pytest.fixture(scope="session")
def registered_user(client):
    """Register a user once and return the response data."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "fixture@example.com",
            "password": "Password123!",
            "full_name": "Fixture User",
        },
    )
    assert response.status_code == 201, response.text

    # Mark the fixture user as verified so login-based fixtures succeed in tests.
    db = TestingSessionLocal()
    user = db.query(app.models.user.User).filter_by(email="fixture@example.com").first()
    if user:
        user.is_verified = True
        db.commit()
    db.close()

    return response.json()


@pytest.fixture(scope="session")
def auth_tokens(client, registered_user):
    """Log in the fixture user and return the token pair."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "fixture@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture(scope="function")
def db():
    """Provide a fresh database session for each test function."""
    db_session = TestingSessionLocal()

    # Override the app's get_db dependency to use this session
    def _get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _get_db

    try:
        yield db_session
    finally:
        db_session.close()
        # Restore the original override
        fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_user(db):
    """Create a test user for function-scoped tests."""
    from app.models.user import User
    from app.core.security import get_password_hash
    import uuid

    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        full_name="Test User",
        hashed_password=get_password_hash("password123"),
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Generate auth headers for function-scoped tests."""
    from app.core.security import create_access_token

    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}
