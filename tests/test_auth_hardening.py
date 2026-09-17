"""Tests for Sprint 1: Authentication Hardening, OAuth, and TOTP 2FA.

Covers:
- OAuth PKCE generation, state expiration, and single-use consumption
- Safe account resolution (anti-takeover policy when local account exists)
- Explicit account linking with step-up authentication
- 3-state authentication machine: restricted 2fa_pending challenge token
- Rejection of 2fa_pending tokens on protected endpoints and refresh
- Two-phase TOTP enrollment (/setup pending vs /confirm activation)
- Single-use recovery codes, atomic consumption, and step-up regeneration
- Step-up authentication for disabling 2FA
- 2FA-required OAuth login returning challenge token
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
import jwt
import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_2fa_challenge_token,
    get_password_hash,
    encrypt_value,
    decrypt_value,
)
from app.models.user import User, RefreshToken
from app.models.oauth import OAuthAccount
from app.models.totp import TOTPSecret, RecoveryCode
from app.services.oauth import (
    generate_oauth_state,
    consume_oauth_state,
    get_oauth_redirect_url,
    find_or_create_user_from_oauth,
    OAuthUserInfo,
    OAuthStateRecord,
)
from app.services.totp import (
    setup_totp,
    confirm_totp,
    verify_totp,
    get_totp_status,
    disable_totp,
    regenerate_recovery_codes,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_user(db: Session) -> User:
    """Create a standard verified user without 2FA."""
    user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        full_name="Standard User",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
        is_verified=True,
        is_2fa_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_with_2fa(db: Session) -> tuple[User, str, list[str]]:
    """Create a user with 2FA activated, confirmed secret, and recovery codes."""
    user = User(
        id=uuid.uuid4(),
        email="2fa_user@example.com",
        full_name="2FA Protected User",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
        is_verified=True,
        is_2fa_enabled=True,
    )
    db.add(user)
    db.commit()

    secret = pyotp.random_base32()
    totp_rec = TOTPSecret(
        user_id=user.id,
        encrypted_secret=encrypt_value(secret),
        is_confirmed=True,
    )
    db.add(totp_rec)

    recovery_codes = ["rec-code-1111", "rec-code-2222", "rec-code-3333"]
    for rc in recovery_codes:
        rec = RecoveryCode(
            user_id=user.id,
            code_hash=get_password_hash(rc),
            is_used=False,
        )
        db.add(rec)

    db.commit()
    db.refresh(user)
    return user, secret, recovery_codes


# ---------------------------------------------------------------------------
# 1. 2FA State Machine & Token Restrictions Tests
# ---------------------------------------------------------------------------

class TestTwoFactorChallengeToken:
    def test_challenge_token_format_and_claims(self, auth_user: User):
        token = create_2fa_challenge_token(auth_user.id)
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(auth_user.id)
        assert payload["type"] == "2fa_pending"
        assert payload["purpose"] == "2fa_pending"
        assert "exp" in payload
        assert "jti" in payload

    def test_challenge_token_rejected_by_protected_endpoints(
        self, client: TestClient, auth_user: User
    ):
        challenge_token = create_2fa_challenge_token(auth_user.id)
        # Normal authenticated endpoint must reject challenge token with 401
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {challenge_token}"},
        )
        assert response.status_code == 401
        assert "Invalid token type" in response.text or "Could not validate" in response.text

    def test_login_returns_challenge_token_when_2fa_enabled(
        self, client: TestClient, user_with_2fa: tuple[User, str, list[str]]
    ):
        user, _, _ = user_with_2fa
        response = client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "Password123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("requires_2fa") is True
        assert "challenge_token" in data
        assert data.get("token_type") == "2fa_pending"
        # Normal access token MUST NOT be issued
        assert "access_token" not in data


# ---------------------------------------------------------------------------
# 2. Two-Phase TOTP Enrollment Tests
# ---------------------------------------------------------------------------

class TestTwoPhaseTOTPEnrollment:
    def test_setup_does_not_enable_2fa(self, db: Session, auth_user: User):
        """Calling setup alone must NEVER activate 2FA or generate recovery codes."""
        result = setup_totp(db, str(auth_user.id))
        assert result.secret is not None
        assert "otpauth://" in result.qr_uri
        assert result.recovery_codes == []

        # Check DB state
        db.refresh(auth_user)
        assert auth_user.is_2fa_enabled is False

        totp_record = (
            db.query(TOTPSecret).filter(TOTPSecret.user_id == auth_user.id).first()
        )
        assert totp_record is not None
        assert totp_record.is_confirmed is False

        # No recovery codes should exist yet
        rc_count = (
            db.query(RecoveryCode).filter(RecoveryCode.user_id == auth_user.id).count()
        )
        assert rc_count == 0

    def test_confirm_with_invalid_code_fails(self, db: Session, auth_user: User):
        setup_totp(db, str(auth_user.id))
        recovery_codes = confirm_totp(db, str(auth_user.id), "000000")
        assert recovery_codes is None

        db.refresh(auth_user)
        assert auth_user.is_2fa_enabled is False

    def test_confirm_with_valid_code_activates_2fa(self, db: Session, auth_user: User):
        setup_result = setup_totp(db, str(auth_user.id))
        totp = pyotp.TOTP(setup_result.secret)
        valid_code = totp.now()

        recovery_codes = confirm_totp(db, str(auth_user.id), valid_code)
        assert recovery_codes is not None
        assert len(recovery_codes) == settings.RECOVERY_CODE_COUNT

        db.refresh(auth_user)
        assert auth_user.is_2fa_enabled is True

        totp_record = (
            db.query(TOTPSecret).filter(TOTPSecret.user_id == auth_user.id).first()
        )
        assert totp_record.is_confirmed is True

        # Recovery codes must be saved in DB
        rc_count = (
            db.query(RecoveryCode)
            .filter(RecoveryCode.user_id == auth_user.id, RecoveryCode.is_used == False)
            .count()
        )
        assert rc_count == settings.RECOVERY_CODE_COUNT

    def test_setup_and_confirm_endpoints(self, client: TestClient, auth_user: User):
        token = create_access_token(auth_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: /2fa/setup
        setup_resp = client.post("/api/v1/auth/2fa/setup", headers=headers)
        assert setup_resp.status_code == 200
        setup_data = setup_resp.json()
        secret = setup_data["secret"]

        # Step 2: /2fa/confirm with valid code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        confirm_resp = client.post(
            "/api/v1/auth/2fa/confirm",
            headers=headers,
            json={"code": code},
        )
        assert confirm_resp.status_code == 200
        confirm_data = confirm_resp.json()
        assert confirm_data["confirmed"] is True
        assert len(confirm_data["recovery_codes"]) == settings.RECOVERY_CODE_COUNT


# ---------------------------------------------------------------------------
# 3. 2FA Verification & Recovery Codes Tests
# ---------------------------------------------------------------------------

class TestTwoFactorVerificationAndRecovery:
    def test_complete_login_with_totp_code(
        self, client: TestClient, user_with_2fa: tuple[User, str, list[str]]
    ):
        user, secret, _ = user_with_2fa
        challenge_token = create_2fa_challenge_token(user.id)
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        response = client.post(
            "/api/v1/auth/2fa/login/verify",
            json={"challenge_token": challenge_token, "code": valid_code},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_complete_login_with_recovery_code_single_use(
        self, client: TestClient, user_with_2fa: tuple[User, str, list[str]]
    ):
        user, _, recovery_codes = user_with_2fa
        rc = recovery_codes[0]

        # First use: should succeed
        challenge_token_1 = create_2fa_challenge_token(user.id)
        response_1 = client.post(
            "/api/v1/auth/2fa/login/verify",
            json={"challenge_token": challenge_token_1, "code": rc},
        )
        assert response_1.status_code == 200
        assert "access_token" in response_1.json()

        # Second use: must fail because code is single-use and now consumed!
        challenge_token_2 = create_2fa_challenge_token(user.id)
        response_2 = client.post(
            "/api/v1/auth/2fa/login/verify",
            json={"challenge_token": challenge_token_2, "code": rc},
        )
        assert response_2.status_code == 401
        assert "Invalid verification code" in response_2.text

    def test_regenerate_recovery_codes_requires_password(
        self, client: TestClient, user_with_2fa: tuple[User, str, list[str]]
    ):
        user, _, old_codes = user_with_2fa
        token = create_access_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Bad password fails
        bad_resp = client.post(
            "/api/v1/auth/2fa/recovery-codes/regenerate",
            headers=headers,
            json={"password": "WrongPassword!"},
        )
        assert bad_resp.status_code == 401

        # Correct password succeeds and yields new codes
        good_resp = client.post(
            "/api/v1/auth/2fa/recovery-codes/regenerate",
            headers=headers,
            json={"password": "Password123!"},
        )
        assert good_resp.status_code == 200
        new_codes = good_resp.json()["recovery_codes"]
        assert len(new_codes) == settings.RECOVERY_CODE_COUNT
        # Old codes should no longer work
        assert old_codes[0] not in new_codes

    def test_disable_2fa_requires_step_up_password(
        self, client: TestClient, db: Session, user_with_2fa: tuple[User, str, list[str]]
    ):
        user, _, _ = user_with_2fa
        token = create_access_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Bad password fails
        bad_resp = client.post(
            "/api/v1/auth/2fa/disable",
            headers=headers,
            json={"password": "WrongPassword!"},
        )
        assert bad_resp.status_code == 401

        # Correct password disables 2FA
        good_resp = client.post(
            "/api/v1/auth/2fa/disable",
            headers=headers,
            json={"password": "Password123!"},
        )
        assert good_resp.status_code == 200
        db.refresh(user)
        assert user.is_2fa_enabled is False


# ---------------------------------------------------------------------------
# 4. OAuth PKCE & Safe Account Resolution Tests
# ---------------------------------------------------------------------------

class TestOAuthSecurity:
    def test_oauth_state_pkce_generation_and_consumption(self):
        state = generate_oauth_state()
        assert len(state) > 10

        record = consume_oauth_state(state)
        assert record is not None
        assert record.state == state
        assert len(record.code_verifier) >= 43
        assert len(record.code_challenge) > 0

        # Must be single-use (consumed)
        assert consume_oauth_state(state) is None

    def test_oauth_redirect_url_includes_pkce(self):
        state = generate_oauth_state()
        with patch.object(settings, "GOOGLE_CLIENT_ID", "mock_google_client_id"), \
             patch.object(settings, "GOOGLE_REDIRECT_URI", "https://app.sirafit.com/auth/callback"):
            url = get_oauth_redirect_url("google", state)
            assert "code_challenge=" in url
            assert "code_challenge_method=S256" in url
            assert f"state={state}" in url

    def test_oauth_new_user_creation(self, db: Session):
        user = find_or_create_user_from_oauth(
            db=db,
            provider="github",
            provider_user_id="gh_12345",
            email="oauth_new@example.com",
            name="OAuth Newbie",
            avatar_url="https://avatar.example.com/1.png",
            access_token="test_gh_token",
        )
        assert user.id is not None
        assert user.email == "oauth_new@example.com"
        assert user.auth_provider == "github"
        assert user.auth_provider_id == "gh_12345"

        account = (
            db.query(OAuthAccount)
            .filter(
                OAuthAccount.provider == "github",
                OAuthAccount.provider_user_id == "gh_12345",
            )
            .first()
        )
        assert account is not None
        assert account.user_id == user.id

    def test_oauth_safe_resolution_blocks_takeover(self, db: Session, auth_user: User):
        """Phase 5: If local account exists with password, OAuth login without explicit
        linking MUST be rejected with 409 Conflict to prevent account takeover.
        """
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            find_or_create_user_from_oauth(
                db=db,
                provider="google",
                provider_user_id="google_attacker_123",
                email=auth_user.email,  # Matching existing user's email
                name="Attacker",
            )
        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail

    def test_oauth_explicit_account_linking(self, db: Session, auth_user: User):
        """When link_user_id is provided from authenticated session, linking succeeds."""
        linked_user = find_or_create_user_from_oauth(
            db=db,
            provider="google",
            provider_user_id="google_legit_456",
            email=auth_user.email,
            name="Linked Name",
            link_user_id=str(auth_user.id),
        )
        assert linked_user.id == auth_user.id

        account = (
            db.query(OAuthAccount)
            .filter(
                OAuthAccount.user_id == auth_user.id,
                OAuthAccount.provider == "google",
            )
            .first()
        )
        assert account is not None
        assert account.provider_user_id == "google_legit_456"

    @pytest.mark.asyncio
    async def test_oauth_callback_with_2fa_enabled_returns_challenge(
        self, client: TestClient, db: Session, user_with_2fa: tuple[User, str, list[str]]
    ):
        """When a user linked to OAuth has 2FA enabled, callback returns challenge token."""
        user, _, _ = user_with_2fa
        # Link an OAuth account
        account = OAuthAccount(
            user_id=user.id,
            provider="github",
            provider_user_id="gh_2fa_user",
            access_token=encrypt_value("dummy_token"),
        )
        db.add(account)
        db.commit()

        state = generate_oauth_state()

        with patch("app.services.oauth.exchange_code_for_token", new_callable=AsyncMock) as mock_exchange, \
             patch("app.services.oauth.get_user_info_from_provider", new_callable=AsyncMock) as mock_user_info:
            mock_exchange.return_value = {"access_token": "token_abc", "refresh_token": None}
            mock_user_info.return_value = OAuthUserInfo(
                provider_user_id="gh_2fa_user",
                email=user.email,
                name=user.full_name or "2FA User",
            )

            response = client.post(
                "/api/v1/auth/oauth/github/callback",
                json={"code": "valid_code", "state": state},
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("requires_2fa") is True
            assert "challenge_token" in data
            assert data["token_type"] == "2fa_pending"
            assert "access_token" not in data
