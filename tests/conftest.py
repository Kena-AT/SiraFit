"""
Shared pytest fixtures for backend tests.

Uses a single in-memory SQLite database backed by a static connection pool so
the whole test process shares one deterministic store. The schema is rebuilt
before every test, giving full isolation (no cross-test state leakage) and
removing the file-lock / "database is locked" flakiness seen with a shared
on-disk SQLite file.

Background tasks (Celery) fall back to synchronous execution in tests via an
unreachable broker, so resume/cover-letter/batch/PDF work actually runs inline.
"""

import os
import sys

# Ensure the backend directory is in the python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

# Provide all required env vars BEFORE any app imports
os.environ.setdefault("DATABASE_URL", "sqlite://")
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
# Use an in-memory Celery broker so enqueue helpers publish without blocking
# and without a 20x retry backoff. Tasks are not consumed in tests (no worker),
# which matches the prior test behaviour; service-level tests cover the work.
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

# Now import after env is set
from app.main import app as fastapi_app  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402

# Import ALL models so SQLite creates every table
import app.models.user  # noqa: F401, E402
import app.models.job  # noqa: F401, E402
import app.models.profile  # noqa: F401, E402
import app.models.cover_letter  # noqa: F401, E402
import app.models.batch  # noqa: F401, E402
import app.models.notification  # noqa: F401, E402
import app.models.analytics  # noqa: F401, E402

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once for the session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def isolate():
    """Rebuild the schema before each test for deterministic isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Ensure any open sessions are rolled back so the next test starts clean.
    TestingSessionLocal().rollback()


@pytest.fixture(scope="function")
def client(setup_db):
    """Fresh test client per test (schema reset by `isolate`)."""
    return TestClient(fastapi_app)


@pytest.fixture(scope="function")
def registered_user(client):
    """Register a user per test and return the response data."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "fixture@example.com",
            "password": "Password123!",
            "full_name": "Fixture User",
        },
    )
    assert response.status_code == 201, response.text

    # Mark the fixture user as verified so login-based fixtures succeed.
    db = TestingSessionLocal()
    user = db.query(app.models.user.User).filter_by(email="fixture@example.com").first()
    if user:
        user.is_verified = True
        db.commit()
    db.close()

    return response.json()


@pytest.fixture(scope="function")
def auth_tokens(client, registered_user):
    """Log in the fixture user per test and return the token pair."""
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

    def _get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _get_db

    try:
        yield db_session
    finally:
        db_session.close()
        # Restore the default override
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
