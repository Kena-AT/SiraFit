import uuid
from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
import jwt
from pydantic import ValidationError

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, UserPreference, DeviceSession
from app.schemas.user import (
    UserCreate, UserResponse, TokenPayload, PasswordChangeRequest,
    NotificationPreferencesBase, NotificationPreferences,
    ResumeDefaultsBase, ResumeDefaults,
    AIProviderKeysWrite, AIProviderKeysRead,
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False
)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Dependency to get the currently authenticated user.
    Accepts the JWT from either:
      - Authorization: Bearer <token> header  (Bearer / oauth2_scheme)
      - access_token HttpOnly cookie          (set by /auth/login)
    """
    # Prefer Authorization header; fall back to cookie
    token_str = token or request.cookies.get("access_token")

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if token_data.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(token_data.sub)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_in: UserCreate,
) -> Any:
    """Update current user profile."""
    update_data = user_in.model_dump(exclude_unset=True)
    # Never update password directly through this endpoint
    update_data.pop("password", None)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password")
def change_password(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    password_data: PasswordChangeRequest,
) -> Any:
    """Change current user password."""
    from app.core.security import verify_password, get_password_hash
    
    # Validate that new passwords match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength (basic validation)
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Hash and update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Password updated successfully"}


@router.get("/me/export")
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Export all user data for privacy compliance."""
    from app.models.job import JobApplication
    from app.models.resume import Resume
    from app.models.cover_letter import CoverLetter
    
    # Gather all user data
    user_data = {
        "profile": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
        },
        "applications": [
            {
                "id": str(app.id),
                "job_id": str(app.job_id),
                "status": app.status,
                "created_at": app.created_at.isoformat() if app.created_at else None,
                "updated_at": app.updated_at.isoformat() if app.updated_at else None,
            }
            for app in db.query(JobApplication).filter(JobApplication.user_id == current_user.id).all()
        ],
        "resumes": [
            {
                "id": str(resume.id),
                "title": resume.title,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
            }
            for resume in db.query(Resume).filter(Resume.user_id == current_user.id).all()
        ],
        "cover_letters": [
            {
                "id": str(letter.id),
                "title": letter.title,
                "created_at": letter.created_at.isoformat() if letter.created_at else None,
            }
            for letter in db.query(CoverLetter).filter(CoverLetter.user_id == current_user.id).all()
        ],
        "preferences": {
            "theme": current_user.preferences.theme if current_user.preferences else "light",
            "notifications_enabled": current_user.preferences.notifications_enabled if current_user.preferences else True,
        },
        "exported_at": datetime.utcnow().isoformat(),
    }
    
    return JSONResponse(content=user_data)


@router.delete("/me")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Delete user account and all associated data."""
    from app.models.user import RefreshToken, AuditLog
    
    # Delete refresh tokens
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id
    ).delete()
    
    # Delete audit logs
    db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    ).delete()
    
    # Cascade delete handles applications, resumes, cover letters, etc.
    # Just delete the user
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}


def _get_or_create_prefs(db: Session, user_id: uuid.UUID) -> UserPreference:
    """Get user preferences or create if they don't exist."""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not prefs:
        prefs = UserPreference(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("/me/preferences/notifications", response_model=NotificationPreferences)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get current user's notification preferences."""
    prefs = _get_or_create_prefs(db, current_user.id)
    return prefs


@router.put("/me/preferences/notifications", response_model=NotificationPreferences)
def update_notification_preferences(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    prefs_in: NotificationPreferencesBase,
) -> Any:
    """Update current user's notification preferences."""
    prefs = _get_or_create_prefs(db, current_user.id)
    for field, value in prefs_in.model_dump().items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return prefs


@router.get("/me/preferences/resume", response_model=ResumeDefaults)
def get_resume_defaults(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get current user's resume default settings."""
    prefs = _get_or_create_prefs(db, current_user.id)
    return prefs


@router.put("/me/preferences/resume", response_model=ResumeDefaults)
def update_resume_defaults(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    prefs_in: ResumeDefaultsBase,
) -> Any:
    """Update current user's resume default settings."""
    prefs = _get_or_create_prefs(db, current_user.id)
    for field, value in prefs_in.model_dump().items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return prefs


@router.get("/me/preferences/ai-keys", response_model=AIProviderKeysRead)
def get_ai_provider_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get current user's AI provider key configuration status."""
    prefs = _get_or_create_prefs(db, current_user.id)
    return AIProviderKeysRead(
        anthropic_configured=bool(prefs.encrypted_anthropic_key),
        openai_configured=bool(prefs.encrypted_openai_key),
        grok_configured=bool(prefs.encrypted_grok_key),
        mistral_configured=bool(prefs.encrypted_mistral_key),
        nvidia_configured=bool(prefs.encrypted_nvidia_key),
    )


@router.put("/me/preferences/ai-keys", response_model=AIProviderKeysRead)
def update_ai_provider_keys(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    keys_in: AIProviderKeysWrite,
) -> Any:
    """Update current user's AI provider API keys (encrypted at rest)."""
    from app.core.security import encrypt_value

    prefs = _get_or_create_prefs(db, current_user.id)

    # Map of input field names to encrypted column names
    key_fields = {
        "anthropic_key": "encrypted_anthropic_key",
        "openai_key": "encrypted_openai_key",
        "grok_key": "encrypted_grok_key",
        "mistral_key": "encrypted_mistral_key",
        "nvidia_key": "encrypted_nvidia_key",
    }

    for input_field, db_field in key_fields.items():
        value = getattr(keys_in, input_field)
        if value is not None:
            encrypted = encrypt_value(value) if value else None
            setattr(prefs, db_field, encrypted)

    db.commit()
    db.refresh(prefs)

    return AIProviderKeysRead(
        anthropic_configured=bool(prefs.encrypted_anthropic_key),
        openai_configured=bool(prefs.encrypted_openai_key),
        grok_configured=bool(prefs.encrypted_grok_key),
        mistral_configured=bool(prefs.encrypted_mistral_key),
        nvidia_configured=bool(prefs.encrypted_nvidia_key),
    )


# ---------------------------------------------------------------------------
# Device Sessions
# ---------------------------------------------------------------------------


def _parse_device_name(user_agent: str) -> str:
    """Extract a human-readable device name from a user agent string."""
    if not user_agent:
        return "Unknown device"

    ua_lower = user_agent.lower()

    # Detect device type
    if "iphone" in ua_lower or "ipad" in ua_lower:
        device_type = "iPhone" if "iphone" in ua_lower else "iPad"
    elif "android" in ua_lower:
        device_type = "Android"
    elif "macintosh" in ua_lower or "mac os" in ua_lower:
        device_type = "Mac"
    elif "windows" in ua_lower:
        device_type = "Windows"
    elif "linux" in ua_lower:
        device_type = "Linux"
    else:
        device_type = "Unknown"

    # Detect browser
    if "chrome" in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower:
        browser = "Safari"
    elif "edge" in ua_lower:
        browser = "Edge"
    else:
        browser = "Browser"

    return f"{device_type} ({browser})"


@router.get("/me/devices")
def get_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get all device sessions for the current user."""
    devices = (
        db.query(DeviceSession)
        .filter(DeviceSession.user_id == current_user.id)
        .order_by(DeviceSession.last_seen.desc())
        .all()
    )

    # Deactivate sessions that haven't been seen in 30 days
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(days=30)
    for device in devices:
        if device.last_seen < cutoff and device.is_active:
            device.is_active = False
    db.commit()

    return [
        {
            "id": d.id,
            "device_name": d.device_name,
            "ip_address": d.ip_address,
            "is_active": d.is_active,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in devices
    ]


@router.delete("/me/devices/{device_id}")
def revoke_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Revoke a device session."""
    device = (
        db.query(DeviceSession)
        .filter(
            DeviceSession.id == device_id,
            DeviceSession.user_id == current_user.id,
        )
        .first()
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device session not found")

    device.is_active = False
    db.commit()

    return {"message": "Device session revoked"}
