"""
Settings API routes.
Provides CRUD for user-stored AI configuration (encrypted API keys).
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User, UserPreference
from app.core.security import encrypt_value, decrypt_value

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AIConfigResponse(BaseModel):
    has_gemini_key: bool = False
    has_openrouter_key: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None

    model_config = {"from_attributes": True}


class AIConfigUpdate(BaseModel):
    gemini_key: Optional[str] = None
    openrouter_key: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/me/ai-config", response_model=AIConfigResponse)
def get_ai_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's AI configuration. Actual API keys are NEVER returned."""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if prefs is None:
        return AIConfigResponse()

    return AIConfigResponse(
        has_gemini_key=bool(prefs.encrypted_gemini_key),
        has_openrouter_key=bool(prefs.encrypted_openrouter_key),
        provider=prefs.ai_provider,
        model=prefs.ai_model,
    )


@router.post("/me/ai-config", response_model=AIConfigResponse)
def save_ai_config(
    body: AIConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save AI configuration. API keys are encrypted before storage."""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if prefs is None:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)

    if body.gemini_key is not None:
        if body.gemini_key:
            encrypted = encrypt_value(body.gemini_key)
            if encrypted is None:
                raise HTTPException(status_code=500, detail="Encryption is not configured. Set DATA_ENCRYPTION_KEY in your environment.")
            prefs.encrypted_gemini_key = encrypted
        else:
            prefs.encrypted_gemini_key = None

    if body.openrouter_key is not None:
        if body.openrouter_key:
            encrypted = encrypt_value(body.openrouter_key)
            if encrypted is None:
                raise HTTPException(status_code=500, detail="Encryption is not configured. Set DATA_ENCRYPTION_KEY in your environment.")
            prefs.encrypted_openrouter_key = encrypted
        else:
            prefs.encrypted_openrouter_key = None

    if body.provider is not None:
        prefs.ai_provider = body.provider
    if body.model is not None:
        prefs.ai_model = body.model

    db.commit()
    db.refresh(prefs)

    return AIConfigResponse(
        has_gemini_key=bool(prefs.encrypted_gemini_key),
        has_openrouter_key=bool(prefs.encrypted_openrouter_key),
        provider=prefs.ai_provider,
        model=prefs.ai_model,
    )


@router.delete("/me/ai-config", response_model=AIConfigResponse)
def delete_ai_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete the user's AI configuration (clear encrypted keys and reset preferences)."""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if prefs:
        prefs.encrypted_gemini_key = None
        prefs.encrypted_openrouter_key = None
        prefs.ai_provider = None
        prefs.ai_model = None
        db.commit()

    return AIConfigResponse()
