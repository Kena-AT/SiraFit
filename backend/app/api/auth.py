from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
import uuid
from concurrent.futures import ThreadPoolExecutor

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from app.core.rate_limiting import check_rate_limit
from app.models.user import User, RefreshToken
from app.schemas.user import Token, UserCreate, UserResponse
from app.api.users import get_current_user
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    RefreshTokenRequest,
    LogoutRequest,
)

from app.core.config import settings
from app.services.email import email_service
router = APIRouter()
_email_executor = ThreadPoolExecutor(max_workers=2)

# ─── Cookie helpers ────────────────────────────────────────────────────────────

COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Write tokens into secure, HttpOnly cookies.
    In production: SameSite=Lax + Secure=True (HTTPS required).
    In development: SameSite=Lax + Secure=False (plain HTTP on localhost).
    NOTE: SameSite=None requires Secure=True; browsers reject SameSite=None on plain HTTP,
    so we always use Lax which works across different ports on the same localhost host.
    """
    is_production = settings.ENVIRONMENT == "production"
    samesite_mode = "lax"       # Lax works in both dev and prod
    secure_flag = is_production  # True only in production (HTTPS)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite=samesite_mode,
        secure=secure_flag,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite=samesite_mode,
        secure=secure_flag,
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
    # Apply rate limit: 5 login attempts per 5 minutes
    check_rate_limit(request, "auth_login")
    
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

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
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_token)
    db.commit()

    # Set HttpOnly cookies
    _set_auth_cookies(response, access_token, refresh_token_str)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    request: Request,
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """Register a new user."""
    # Apply rate limit: 3 registrations per hour
    check_rate_limit(request, "auth_register")
    
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

    # Create default preferences
    from app.models.user import UserPreference
    prefs = UserPreference(user_id=user.id)
    db.add(prefs)
    db.commit()

    # Send verification email in background (best-effort — don't block registration)
    verification_token = create_access_token(user.id, token_type="verification")
    _email_executor.submit(email_service.send_verification_email, user.email, verification_token)

    return user


# ─── Resend verification email ────────────────────────────────────────────────────────

@router.post("/resend-verification", status_code=200)
def resend_verification(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Resend a verification link to the currently logged‑in user.
    The endpoint generates a fresh verification token and sends the email in the
    background, returning a simple success message.
    """
    verification_token = create_access_token(current_user.id, token_type="verification")
    _email_executor.submit(email_service.send_verification_email, current_user.email, verification_token)
    return {"detail": "Verification email resent"}



@router.post("/verify-email")
def verify_email(
    request: Request,
    *,
    db: Session = Depends(get_db),
    body: VerifyEmailRequest,
) -> Any:
    """Verify user email with token."""
    # Apply rate limit: 5 verification attempts per 5 minutes
    check_rate_limit(request, "auth_verify_email")
    
    try:
        payload = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != "verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    except (jwt.PyJWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate token",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token subject")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
    # Apply rate limit: 3 password reset requests per hour
    check_rate_limit(request, "auth_forgot_password")
    
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
        payload = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != "reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    except (jwt.PyJWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate token",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token subject")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
    # Apply rate limit: 10 refresh attempts per minute
    check_rate_limit(request, "auth_refresh")
    
    # Accept token from cookie or request body
    token_str = request.cookies.get("refresh_token") or (body.refresh_token if body else None)

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    try:
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user_id = payload.get("sub")
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token subject")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Check that the refresh token has not been revoked
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == token_str,
        RefreshToken.user_id == user_uuid,
    ).first()
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
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
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
    token_str = request.cookies.get("refresh_token") or (body.refresh_token if body else None)

    if token_str:
        try:
            payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")

            if user_id:
                try:
                    user_uuid = uuid.UUID(user_id)
                except ValueError:
                    user_uuid = None

                if user_uuid:
                    token = db.query(RefreshToken).filter(
                        RefreshToken.token == token_str,
                        RefreshToken.user_id == user_uuid,
                        RefreshToken.is_revoked == False,
                    ).first()

                if token:
                    token.is_revoked = True
                    db.commit()

        except Exception:
            pass  # Best effort — always clear cookies

    _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}
