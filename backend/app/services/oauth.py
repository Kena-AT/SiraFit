"""OAuth social login service.

Handles OAuth flow initiation with PKCE, single-use state CSRF protection,
code exchange, safe account resolution (anti-takeover), and explicit account linking.
"""

import base64
import hashlib
import secrets
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import encrypt_value
from app.models.oauth import OAuthAccount
from app.models.user import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider configurations
# ---------------------------------------------------------------------------

PROVIDERS = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
        "supports_pkce": True,
        "client_id": lambda: settings.GOOGLE_CLIENT_ID,
        "client_secret": lambda: settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": lambda: settings.GOOGLE_REDIRECT_URI,
        "extract_user": lambda data: {
            "provider_user_id": data.get("sub"),
            "email": data.get("email"),
            "name": data.get("name"),
            "avatar_url": data.get("picture"),
        },
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user user:email",
        "supports_pkce": True,
        "client_id": lambda: settings.GITHUB_CLIENT_ID,
        "client_secret": lambda: settings.GITHUB_CLIENT_SECRET,
        "redirect_uri": lambda: settings.GITHUB_REDIRECT_URI,
        "extract_user": lambda data: {
            "provider_user_id": str(data.get("id")),
            "email": data.get("email"),
            "name": data.get("name") or data.get("login"),
            "avatar_url": data.get("avatar_url"),
        },
    },
    "linkedin": {
        "authorize_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "userinfo_url": "https://api.linkedin.com/v2/userinfo",
        "scope": "openid profile email",
        "supports_pkce": True,
        "client_id": lambda: settings.LINKEDIN_CLIENT_ID,
        "client_secret": lambda: settings.LINKEDIN_CLIENT_SECRET,
        "redirect_uri": lambda: settings.LINKEDIN_REDIRECT_URI,
        "extract_user": lambda data: {
            "provider_user_id": data.get("sub"),
            "email": data.get("email"),
            "name": data.get("name"),
            "avatar_url": data.get("picture"),
        },
    },
}


# ---------------------------------------------------------------------------
# PKCE and State management for CSRF protection
# ---------------------------------------------------------------------------


@dataclass
class OAuthStateRecord:
    state: str
    code_verifier: str
    code_challenge: str
    created_at: datetime
    link_user_id: Optional[str] = None


_oauth_states: dict[str, OAuthStateRecord] = {}
STATE_TTL_MINUTES = 10


def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and S256 code_challenge according to RFC 7636."""
    verifier = (
        base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
    )
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge


def generate_oauth_state(link_user_id: Optional[str] = None) -> str:
    """Generate and store a random single-use state token with PKCE parameters."""
    _cleanup_expired_states()
    state = secrets.token_urlsafe(32)
    verifier, challenge = generate_pkce_pair()
    now = datetime.now(timezone.utc)
    _oauth_states[state] = OAuthStateRecord(
        state=state,
        code_verifier=verifier,
        code_challenge=challenge,
        created_at=now,
        link_user_id=str(link_user_id) if link_user_id else None,
    )
    return state


def consume_oauth_state(state: str) -> Optional[OAuthStateRecord]:
    """Consume single-use OAuth state record and return its details if valid and unexpired."""
    _cleanup_expired_states()
    record = _oauth_states.pop(state, None)
    if not record:
        return None

    now = datetime.now(timezone.utc)
    if (now - record.created_at).total_seconds() > STATE_TTL_MINUTES * 60:
        return None

    return record


def validate_oauth_state(state: str) -> bool:
    """Backwards-compatible boolean check that consumes the state."""
    return consume_oauth_state(state) is not None


def _cleanup_expired_states() -> None:
    now = datetime.now(timezone.utc)
    expired_keys = [
        k
        for k, v in _oauth_states.items()
        if (now - v.created_at).total_seconds() > STATE_TTL_MINUTES * 60
    ]
    for k in expired_keys:
        _oauth_states.pop(k, None)


# ---------------------------------------------------------------------------
# Core OAuth functions
# ---------------------------------------------------------------------------


@dataclass
class OAuthUserInfo:
    """Result from OAuth user info extraction."""

    provider_user_id: str
    email: str
    name: str
    avatar_url: Optional[str] = None


def get_oauth_redirect_url(
    provider: str,
    state: str,
    code_challenge: Optional[str] = None,
) -> str:
    """Build the authorization URL to redirect the user to, with PKCE where supported."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    config = PROVIDERS[provider]
    client_id = config["client_id"]()
    redirect_uri = config["redirect_uri"]()

    if not client_id:
        raise ValueError(f"OAuth not configured for {provider}: missing client ID")

    # If code_challenge wasn't explicitly passed, check if state record exists
    if not code_challenge and state in _oauth_states:
        code_challenge = _oauth_states[state].code_challenge

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
    }

    if code_challenge and config.get("supports_pkce", True):
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{config['authorize_url']}?{query}"


async def exchange_code_for_token(
    provider: str, code: str, code_verifier: Optional[str] = None
) -> dict:
    """Exchange an authorization code for an access token, verifying PKCE if available."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    config = PROVIDERS[provider]
    client_id = config["client_id"]()
    client_secret = config["client_secret"]()
    redirect_uri = config["redirect_uri"]()

    if not client_id or not client_secret:
        raise ValueError(f"OAuth not configured for {provider}: missing credentials")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    if code_verifier:
        data["code_verifier"] = code_verifier

    async with httpx.AsyncClient() as client:
        response = await client.post(
            config["token_url"],
            data=data,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()


async def get_user_info_from_provider(
    provider: str, access_token: str
) -> OAuthUserInfo:
    """Fetch user profile info from the OAuth provider."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    config = PROVIDERS[provider]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            config["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()

    extracted = config["extract_user"](data)
    return OAuthUserInfo(
        provider_user_id=str(extracted.get("provider_user_id", "")),
        email=str(extracted.get("email", "")),
        name=str(extracted.get("name", "")),
        avatar_url=extracted.get("avatar_url"),
    )


def find_or_create_user_from_oauth(
    db: Session,
    provider: str,
    provider_user_id: str,
    email: str,
    name: str,
    avatar_url: Optional[str] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    link_user_id: Optional[str] = None,
) -> User:
    """Find an existing user by OAuth identity, create a new one, or link explicitly.

    Security Rule (Phase 5 - Anti-Takeover):
    If an existing local password user matches the OAuth email and is NOT already linked,
    DO NOT automatically link unless link_user_id was supplied (indicating an authenticated
    account linking session). Otherwise, raise 409 Conflict to prevent account takeover.
    """
    # 1. Check if this OAuth account is already linked
    existing_account = (
        db.query(OAuthAccount)
        .filter(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
        .first()
    )

    if existing_account:
        # Update tokens if they changed
        if access_token:
            existing_account.access_token = encrypt_value(access_token)
        if refresh_token:
            existing_account.refresh_token = encrypt_value(refresh_token)
        db.commit()
        return existing_account.user

    # 2. Check if this is an explicit account linking flow for an authenticated user
    if link_user_id:
        try:
            target_uuid = uuid.UUID(str(link_user_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid linking user ID",
            )
        target_user = db.query(User).filter(User.id == target_uuid).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user for account linking not found",
            )

        # Ensure this user doesn't already have this provider linked
        user_provider_account = (
            db.query(OAuthAccount)
            .filter(
                OAuthAccount.user_id == target_user.id,
                OAuthAccount.provider == provider,
            )
            .first()
        )
        if user_provider_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have a {provider} account linked",
            )

        oauth_account = OAuthAccount(
            user_id=target_user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            access_token=encrypt_value(access_token) if access_token else "",
            refresh_token=encrypt_value(refresh_token) if refresh_token else None,
        )
        db.add(oauth_account)
        db.commit()
        db.refresh(target_user)
        return target_user

    # 3. Standard Login / Registration: Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        # Safe Account Resolution: Prevent automatic account takeover!
        logger.warning(
            f"OAuth login for {email} blocked: user already exists with different credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An account with this email already exists. "
                "Please log in with your credentials and link this provider in Account Settings."
            ),
        )

    # 4. New user: Create user and link OAuth identity
    new_user = User(
        email=email,
        full_name=name,
        avatar_url=avatar_url,
        is_active=True,
        is_verified=True,  # OAuth email pre-verified by provider
        auth_provider=provider,
        auth_provider_id=provider_user_id,
        hashed_password="",  # No password for OAuth-only users
    )
    db.add(new_user)
    db.flush()

    oauth_account = OAuthAccount(
        user_id=new_user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        access_token=encrypt_value(access_token) if access_token else "",
        refresh_token=encrypt_value(refresh_token) if refresh_token else None,
    )
    db.add(oauth_account)
    db.commit()
    db.refresh(new_user)

    return new_user
