from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
import uuid
from concurrent.futures import ThreadPoolExecutor

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.models.user import User, RefreshToken
from app.schemas.user import Token, UserCreate, UserResponse
from app.api.users import get_current_user
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    RefreshTokenRequest,
    LogoutRequest,
    ResendVerificationRequest,
)

from app.core.config import settings
from app.services.email import email_service

router = APIRouter()
_email_executor = ThreadPoolExecutor(max_workers=2)

# ─── Cookie helpers ────────────────────────────────────────────────────────────

COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds


def _set_auth_cookies(
    response: Response, access_token: str, refresh_token: str
) -> None:
    """Write tokens into secure, HttpOnly cookies.

    In production: SameSite=None + Secure=True (HTTPS required).
    In development: SameSite=None + Secure=False (plain HTTP on localhost).

    SameSite=Lax would BLOCK cookies on cross-origin XHR (which we have in dev:
    frontend on :3030 → backend on :8000), so we use None for cross-site API requests.
    """
    is_production = settings.ENVIRONMENT == "production"
    # SameSite=None requires Secure=True in production, but works on localhost without HTTPS in dev
    samesite_mode = "none"  # Allow cross-site (needed for dev: localhost:3030 → localhost:8000)
    secure_flag = True  # Must be True if samesite is none
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite=samesite_mode,
        secure=secure_flag,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite=samesite_mode,
        secure=secure_flag,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


# ─── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/login", response_model=Token)
def login_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox or request a new verification link.",
        )

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token(user.id)

    # Persist refresh token in DB
    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_token)

    # Register device session
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else None
    try:
        from app.api.users import _create_device_session
        _create_device_session(db, user.id, user_agent, ip_address)
    except Exception as e:
        # Device registration should not block login
        import logging
        logging.getLogger(__name__).warning(f"Failed to create device session: {e}")

    db.commit()

    # Set HttpOnly cookies
    _set_auth_cookies(response, access_token, refresh_token_str)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register_user(
    request: Request,
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """Register a new user."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create profile with name and email from signup
    name_parts = user.full_name.split(" ", 1) if user.full_name else ["", ""]
    from app.models.profile import Profile
    profile = Profile(
        user_id=user.id,
        first_name=name_parts[0] if name_parts[0] else None,
        last_name=name_parts[1] if len(name_parts) > 1 else None,
        email=user.email,
    )
    db.add(profile)

    # Create default preferences
    from app.models.user import UserPreference

    prefs = UserPreference(user_id=user.id)
    db.add(prefs)
    db.commit()

    # Send verification email in background (best-effort — don't block registration)
    verification_token = create_access_token(user.id, token_type="verification")
    _email_executor.submit(
        email_service.send_verification_email, user.email, verification_token
    )

    return user


# ─── Resend verification email ────────────────────────────────────────────────────────


@router.post("/resend-verification", status_code=200)
def resend_verification(
    body: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> Any:
    """Resend a verification link.
    The endpoint generates a fresh verification token and sends the email in the
    background, returning a simple success message.
    """
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return {"detail": "If the email is registered and not verified, a verification link has been sent."}
        
    if user.is_verified:
        return {"detail": "Email is already verified."}

    verification_token = create_access_token(user.id, token_type="verification")
    _email_executor.submit(
        email_service.send_verification_email, user.email, verification_token
    )
    return {"detail": "If the email is registered and not verified, a verification link has been sent."}


@router.post("/verify-email")
def verify_email(
    request: Request,
    *,
    db: Session = Depends(get_db),
    body: VerifyEmailRequest,
) -> Any:
    """Verify user email with token."""
    try:
        payload = jwt.decode(
            body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )

    except (jwt.PyJWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate token",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token subject"
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_verified = True
    db.commit()
    db.refresh(user)

    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
def forgot_password(
    request: Request,
    *,
    db: Session = Depends(get_db),
    body: ForgotPasswordRequest,
) -> Any:
    """Request password reset — always returns 200 to avoid email enumeration."""
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        reset_token = create_access_token(user.id, token_type="reset")
        email_service.send_password_reset_email(user.email, reset_token)

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(
    *,
    db: Session = Depends(get_db),
    body: ResetPasswordRequest,
) -> Any:
    """Reset password with token."""
    try:
        payload = jwt.decode(
            body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )

    except (jwt.PyJWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate token",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token subject"
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.hashed_password = get_password_hash(body.new_password)
    db.commit()

    return {"message": "Password reset successfully"}


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    response: Response,
    *,
    request: Request,
    db: Session = Depends(get_db),
    body: Optional[RefreshTokenRequest] = None,
) -> Any:
    """Refresh access token using refresh token (cookie or body)."""
    # Accept token from cookie or request body
    token_str = request.cookies.get("refresh_token") or (
        body.refresh_token if body else None
    )

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    try:
        payload = jwt.decode(
            token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type"
            )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user_id = payload.get("sub")
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token subject"
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Check that the refresh token has not been revoked
    stored_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == token_str,
            RefreshToken.user_id == user_uuid,
        )
        .first()
    )
    if not stored_token or stored_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or is invalid",
        )

    # Revoke old token (rotation)
    stored_token.is_revoked = True

    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    # Persist new refresh token
    db_token = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_token)
    db.commit()

    _set_auth_cookies(response, new_access_token, new_refresh_token)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
    response: Response,
    *,
    request: Request,
    db: Session = Depends(get_db),
    body: Optional[LogoutRequest] = None,
) -> Any:
    """Revoke refresh token and clear auth cookies."""
    token_str = request.cookies.get("refresh_token") or (
        body.refresh_token if body else None
    )

    if token_str:
        try:
            payload = jwt.decode(
                token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")

            if user_id:
                try:
                    user_uuid = uuid.UUID(user_id)
                except ValueError:
                    user_uuid = None

                if user_uuid:
                    token = (
                        db.query(RefreshToken)
                        .filter(
                            RefreshToken.token == token_str,
                            RefreshToken.user_id == user_uuid,
                            RefreshToken.is_revoked.is_(False),
                        )
                        .first()
                    )

                if token:
                    token.is_revoked = True
                    db.commit()

        except Exception:
            pass  # Best effort — always clear cookies

    _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}
