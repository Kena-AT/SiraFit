"""OAuth social login service.

Handles OAuth flow initiation, code exchange, and user creation/linking
for Google, GitHub, and LinkedIn providers.
"""
import secrets
import logging
from dataclasses import dataclass
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import encrypt_value, decrypt_value
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
# State management for CSRF protection
# ---------------------------------------------------------------------------

_oauth_states: dict[str, str] = {}


def generate_oauth_state() -> str:
    """Generate and store a random state token for CSRF protection."""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = state
    return state


def validate_oauth_state(state: str) -> bool:
    """Validate and consume an OAuth state token."""
    if state in _oauth_states:
        del _oauth_states[state]
        return True
    return False


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


def get_oauth_redirect_url(provider: str, state: str) -> str:
    """Build the authorization URL to redirect the user to."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    config = PROVIDERS[provider]
    client_id = config["client_id"]()
    redirect_uri = config["redirect_uri"]()

    if not client_id:
        raise ValueError(f"OAuth not configured for {provider}: missing client ID")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
    }

    # LinkedIn uses a different param name
    if provider == "linkedin":
        params["response_type"] = "code"

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{config['authorize_url']}?{query}"


async def exchange_code_for_token(provider: str, code: str) -> dict:
    """Exchange an authorization code for an access token."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    config = PROVIDERS[provider]
    client_id = config["client_id"]()
    client_secret = config["client_secret"]()
    redirect_uri = config["redirect_uri"]()

    if not client_id or not client_secret:
        raise ValueError(f"OAuth not configured for {provider}: missing credentials")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            config["token_url"],
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()


async def get_user_info_from_provider(provider: str, access_token: str) -> OAuthUserInfo:
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
    return OAuthUserInfo(**extracted)


def find_or_create_user_from_oauth(
    db: Session,
    provider: str,
    provider_user_id: str,
    email: str,
    name: str,
    avatar_url: Optional[str] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> User:
    """Find an existing user by OAuth identity or create a new one.

    Links the OAuth account to the user. If a user with the same email
    exists but isn't linked to this provider, links it.
    """
    # Check if this OAuth account is already linked
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

    # Check if a user with this email already exists
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user
        user = User(
            email=email,
            full_name=name,
            avatar_url=avatar_url,
            is_active=True,
            is_verified=True,  # OAuth emails are pre-verified
            auth_provider=provider,
            auth_provider_id=provider_user_id,
            hashed_password="",  # No password for OAuth-only users
        )
        db.add(user)
        db.flush()

    # Link the OAuth account
    oauth_account = OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        access_token=encrypt_value(access_token) if access_token else "",
        refresh_token=encrypt_value(refresh_token) if refresh_token else None,
    )
    db.add(oauth_account)
    db.commit()
    db.refresh(user)

    return user
