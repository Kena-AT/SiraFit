"""
Shared FastAPI dependencies for SiraFit.

Centralises cross-cutting concerns so route handlers stay thin.

``get_user_profile`` replaces the repeated
``db.query(Profile)...first()`` + 404 boilerplate that was duplicated across
the profile-required endpoints (Phase 3.4). It returns the authenticated
user's profile, raising 404 when one does not exist.

Design note: placed here (rather than back on ``app.api.users``) because the
auth token dependency ``get_current_user`` lives in ``users.py`` but does not
itself import this module, so importing it back here creates no import cycle.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.profile import Profile


def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    """Resolve the authenticated user's profile, 404 if it does not exist."""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Create a profile first.",
        )
    return profile


__all__ = ["get_user_profile"]
