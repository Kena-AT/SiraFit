"""Tests for Sprint 1: Authentication Hardening & OAuth/2FA

Tests OAuth user creation flow, TOTP setup/verification, and recovery codes.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.core.security import encrypt_value, decrypt_value, get_password_hash
from app.models.user import User
from app.models.oauth import OAuthAccount
from app.models.totp import TOTPSecret, RecoveryCode
from app.services.oauth import (
    find_or_create_user_from_oauth,
    generate_oauth_state,
    validate_oauth_state,
)
from app.services.totp import (
    setup_totp,
    verify_totp,
    get_totp_status,
    disable_totp,
    _generate_recovery_codes,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_with_2fa(db_session: Session):
    """Create a test user with 2FA enabled."""
    user = User(
        id=uuid.uuid4(),
        email="2fa@example.com",
        full_name="2FA User",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
        is_2fa_enabled=True,
    )
    db_session.add(user)
    db_session.commit()

    # Add TOTP secret
    secret = "JBSWY3DPEHPK3PXP"  # Test secret
    totp = TOTPSecret(
        user_id=user.id,
        encrypted_secret=encrypt_value(secret),
    )
    db_session.add(totp)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# OAuth Tests
# ---------------------------------------------------------------------------

class TestOAuth:
    def test_generate_oauth_state(self):
        """Test OAuth state generation."""
        state = generate_oauth_state()
        assert state is not None
        assert len(state) > 0

    def test_validate_oauth_state(self):
        """Test OAuth state validation."""
        state = generate_oauth_state()
        assert validate_oauth_state(state) is True
        # State should be consumed
        assert validate_oauth_state(state) is False

    def test_find_or_create_user_new_oauth(self, db_session: Session):
        """Test creating a new user from OAuth."""
        user = find_or_create_user_from_oauth(
            db=db_session,
            provider="google",
            provider_user_id="123456789",
            email="oauth@example.com",
            name="OAuth User",
            avatar_url="https://example.com/avatar.jpg",
            access_token="test_access_token",
        )
        assert user is not None
        assert user.email == "oauth@example.com"
        assert user.full_name == "OAuth User"
        assert user.is_verified is True
        assert user.auth_provider == "google"

        # Check OAuth account was created
        oauth_account = (
            db_session.query(OAuthAccount)
            .filter(
                OAuthAccount.provider == "google",
                OAuthAccount.provider_user_id == "123456789",
            )
            .first()
        )
        assert oauth_account is not None
        assert oauth_account.user_id == user.id

    def test_find_or_create_user_existing_email(self, db_session: Session, test_user):
        """Test linking OAuth to existing user with same email."""
        user = find_or_create_user_from_oauth(
            db=db_session,
            provider="github",
            provider_user_id="987654321",
            email=test_user.email,
            name="GitHub User",
        )
        assert user.id == test_user.id

        # Check OAuth account was linked
        oauth_account = (
            db_session.query(OAuthAccount)
            .filter(
                OAuthAccount.provider == "github",
                OAuthAccount.provider_user_id == "987654321",
            )
            .first()
        )
        assert oauth_account is not None

    def test_find_or_create_user_existing_oauth(self, db_session: Session, test_user):
        """Test existing OAuth account returns same user."""
        # First link
        user1 = find_or_create_user_from_oauth(
            db=db_session,
            provider="google",
            provider_user_id="111222333",
            email=test_user.email,
            name="Google User",
        )
        # Second call with same OAuth
        user2 = find_or_create_user_from_oauth(
            db=db_session,
            provider="google",
            provider_user_id="111222333",
            email=test_user.email,
            name="Google User Updated",
        )
        assert user1.id == user2.id


# ---------------------------------------------------------------------------
# TOTP Tests
# ---------------------------------------------------------------------------

class TestTOTP:
    def test_setup_totp(self, db_session: Session, test_user):
        """Test TOTP setup generates secret and recovery codes."""
        result = setup_totp(db_session, test_user.id)

        assert result.secret is not None
        assert result.qr_uri is not None
        assert "otpauth://" in result.qr_uri
        assert len(result.recovery_codes) == 8

        # Verify user is marked as 2FA enabled
        db_session.refresh(test_user)
        assert test_user.is_2fa_enabled is True

    def test_verify_totp_valid_code(self, db_session: Session, test_user_with_2fa):
        """Test valid TOTP code verification."""
        # We need to mock pyotp verification since we can't generate real codes
        with patch("app.services.totp.pyotp.TOTP") as mock_totp:
            mock_instance = MagicMock()
            mock_instance.verify.return_value = True
            mock_totp.return_value = mock_instance

            result = verify_totp(db_session, test_user_with_2fa.id, "123456")
            assert result.is_valid is True
            assert result.is_recovery_code is False

    def test_verify_totp_invalid_code(self, db_session: Session, test_user_with_2fa):
        """Test invalid TOTP code verification."""
        with patch("app.services.totp.pyotp.TOTP") as mock_totp:
            mock_instance = MagicMock()
            mock_instance.verify.return_value = False
            mock_totp.return_value = mock_instance

            result = verify_totp(db_session, test_user_with_2fa.id, "000000")
            assert result.is_valid is False

    def test_verify_recovery_code(self, db_session: Session, test_user):
        """Test recovery code verification."""
        # Setup TOTP first
        setup_result = setup_totp(db_session, test_user.id)
        recovery_code = setup_result.recovery_codes[0]

        # Verify with recovery code
        result = verify_totp(db_session, test_user.id, recovery_code)
        assert result.is_valid is True
        assert result.is_recovery_code is True

        # Same code should not work again
        result2 = verify_totp(db_session, test_user.id, recovery_code)
        assert result2.is_valid is False

    def test_get_totp_status(self, db_session: Session, test_user_with_2fa):
        """Test getting 2FA status."""
        status = get_totp_status(db_session, test_user_with_2fa.id)
        assert status["enabled"] is True
        assert status["configured"] is True
        assert status["recovery_codes_remaining"] == 0

    def test_disable_totp(self, db_session: Session, test_user):
        """Test disabling TOTP."""
        # Setup first
        setup_totp(db_session, test_user.id)

        # Disable
        result = disable_totp(db_session, test_user.id)
        assert result is True

        # Verify disabled
        db_session.refresh(test_user)
        assert test_user.is_2fa_enabled is False

        # Check TOTP secret deleted
        totp = db_session.query(TOTPSecret).filter(TOTPSecret.user_id == test_user.id).first()
        assert totp is None

    def test_recovery_codes_generation(self):
        """Test recovery codes are unique and correct length."""
        codes = _generate_recovery_codes(8)
        assert len(codes) == 8
        assert len(set(codes)) == 8  # All unique
        for code in codes:
            assert len(code) > 0


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TestAuthEndpoints:
    def test_login_with_2fa_enabled(self, db_session: Session, test_user):
        """Test login returns temp token when 2FA is enabled."""
        test_user.is_2fa_enabled = True
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("requires_2fa") is True
        assert "temp_token" in data

    def test_login_without_2fa(self, db_session: Session, test_user):
        """Test normal login without 2FA."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_2fa_setup_requires_auth(self):
        """Test 2FA setup requires authentication."""
        response = client.post("/api/v1/auth/2fa/setup")
        assert response.status_code == 401

    def test_2fa_status_requires_auth(self):
        """Test 2FA status requires authentication."""
        response = client.post("/api/v1/auth/2fa/status")
        assert response.status_code == 401

    def test_oauth_authorize_disabled(self):
        """Test OAuth authorize when disabled."""
        response = client.get("/api/v1/auth/oauth/google/authorize")
        # Should redirect or return error based on config
        assert response.status_code in [200, 307, 400]
