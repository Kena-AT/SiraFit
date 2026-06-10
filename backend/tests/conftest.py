"""
Shared pytest fixtures for backend tests.
Uses an in-memory SQLite database for speed and zero external dependencies.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once per test session, then drop them."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    """Shared test client for the whole session."""
    return TestClient(app)


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
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="session")
def auth_tokens(client, registered_user):
    """Log in the fixture user and return the token pair."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "fixture@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    return response.json()
