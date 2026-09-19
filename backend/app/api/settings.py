"""
Settings API routes.
Provides CRUD for user-stored AI configuration (provider/model, fallback order).
API keys are managed via the /users/me/preferences/ai-keys endpoint.
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User, UserPreference

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AIConfigResponse(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    fallback_order: Optional[list[str]] = None

    model_config = {"from_attributes": True}


class AIConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    # Ordered list of provider names to try when the chosen one is unavailable.
    fallback_order: Optional[list[str]] = None


class DiscoveredModel(BaseModel):
    id: str
    label: str
    description: Optional[str] = None


class DiscoveredModelsResponse(BaseModel):
    provider: str
    source: str  # "api" | "fallback"
    models: list[DiscoveredModel]
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/me/ai-config", response_model=AIConfigResponse)
def get_ai_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's AI configuration (provider, model, fallback order)."""
    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    if prefs is None:
        return AIConfigResponse()

    fallback_order = None
    if prefs.ai_fallback_order:
        try:
            fallback_order = json.loads(prefs.ai_fallback_order)
        except Exception:
            fallback_order = None

    return AIConfigResponse(
        provider=prefs.ai_provider,
        model=prefs.ai_model,
        fallback_order=fallback_order,
    )


@router.post("/me/ai-config", response_model=AIConfigResponse)
def save_ai_config(
    body: AIConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save AI configuration (provider, model, and optional fallback order)."""
    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    if prefs is None:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)

    if body.provider is not None:
        prefs.ai_provider = body.provider
    if body.model is not None:
        prefs.ai_model = body.model
    if body.fallback_order is not None:
        # Only store known providers, de-duplicated, in the given order.
        from app.services.ai_keys import _parse_fallback_order

        cleaned = _parse_fallback_order(body.fallback_order)
        prefs.ai_fallback_order = json.dumps(cleaned) if cleaned else None

    db.commit()
    db.refresh(prefs)

    fallback_order = (
        json.loads(prefs.ai_fallback_order) if prefs.ai_fallback_order else None
    )
    return AIConfigResponse(
        provider=prefs.ai_provider,
        model=prefs.ai_model,
        fallback_order=fallback_order,
    )


@router.delete("/me/ai-config", response_model=AIConfigResponse)
def delete_ai_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset the user's AI configuration (clear provider/model/fallback prefs)."""
    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    if prefs:
        prefs.ai_provider = None
        prefs.ai_model = None
        prefs.ai_fallback_order = None
        db.commit()

    return AIConfigResponse()


@router.get("/me/models", response_model=DiscoveredModelsResponse)
async def get_provider_models(
    provider: str,
    force_refresh: bool = False,
    api_key: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Discover available models for a provider using dynamic API discovery.

    Resolves active API key (User UI key first, then server/.env), executes the
    discovery call against the provider's /v1/models endpoint, and gracefully falls back
    to curated models if no key exists or external endpoint is unreachable.
    """
    from app.services.ai_keys import resolve_provider_key
    from app.services.model_discovery import fetch_provider_models

    key_to_use = api_key
    if not key_to_use:
        key_to_use = resolve_provider_key(provider, db=db, user_id=current_user.id)

    result = await fetch_provider_models(
        provider=provider,
        api_key=key_to_use,
        force_refresh=force_refresh,
    )
    return result

