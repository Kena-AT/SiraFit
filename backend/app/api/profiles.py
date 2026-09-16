from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User, UserPreference
from app.models.profile import (
    Profile,
    Experience,
    Education,
    Skill,
    Project,
    Certification,
)
from app.models.profile_version import ProfileVersion
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile_validation import validate_profile
from app.services.profile_versioning import (
    create_profile_version,
    get_profile_history,
    revert_to_version,
)

router = APIRouter()


class BulletPolishRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000)


@router.post("/me/polish-bullet")
async def polish_resume_bullet(
    body: BulletPolishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Rewrite resume achievement bullet(s) with AI using the STAR method.

    Resolves the API key via the shared multi-provider resolver (request has
    no header key here, so: user's UI-stored key -> env key -> fallback
    providers). Falls back across providers/models automatically.
    """
    from app.services.ai_keys import build_candidates
    from app.services.ai import complete_with_fallback

    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    provider = (prefs.ai_provider if prefs else None) or None
    model = (prefs.ai_model if prefs else None) or None

    candidates = build_candidates(
        db=db, user_id=current_user.id, provider=provider, model=model
    )
    if not candidates:
        raise HTTPException(
            status_code=503,
            detail="No AI API key configured. Add one in Settings → AI or set provider keys in your env file.",
        )

    system_prompt = (
        "You are an expert technical resume writer. Rewrite the user's resume achievement "
        "bullet points using the STAR method: strong past-tense action verbs, concrete "
        "technologies, and quantified impact. Where a metric is unknown, insert a realistic "
        "placeholder metric. Return ONLY the rewritten bullets, one per line, each starting "
        "with '• '. No preamble, no explanation."
    )
    try:
        polished = await complete_with_fallback(
            body.text, candidates, system=system_prompt, max_tokens=512
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"All AI providers failed: {exc}")

    return {"polished": polished.strip()}


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get the current user's profile.
    If no profile exists, creates one and populates it from the user's signup data.
    Backfills missing first_name/last_name/email from the User table for legacy profiles.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()

    if not profile:
        # Create profile from user signup data
        name_parts = current_user.full_name.split(" ", 1) if current_user.full_name else ["", ""]
        profile = Profile(
            user_id=current_user.id,
            first_name=name_parts[0] if name_parts[0] else None,
            last_name=name_parts[1] if len(name_parts) > 1 else None,
            email=current_user.email,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        # Backfill missing fields from User table for legacy profiles
        updated = False
        if not profile.email and current_user.email:
            profile.email = current_user.email
            updated = True
        if not profile.first_name and current_user.full_name:
            name_parts = current_user.full_name.split(" ", 1)
            if name_parts[0]:
                profile.first_name = name_parts[0]
                updated = True
        if not profile.last_name and current_user.full_name:
            name_parts = current_user.full_name.split(" ", 1)
            if len(name_parts) > 1 and name_parts[1]:
                profile.last_name = name_parts[1]
                updated = True
        if updated:
            db.commit()
            db.refresh(profile)

    return profile


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile_in: ProfileUpdate,
) -> Any:
    """
    Update the current user's profile with business validation and versioning.
    Creates an immutable snapshot before each update for rollback support.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()

    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    update_data = profile_in.model_dump(exclude_unset=True)

    # Sprint 2: Run business validation before any destructive changes
    errors = validate_profile(update_data)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    # Sprint 2: Create version snapshot before update
    create_profile_version(current_user.id, profile, db)

    # Validate nested list items BEFORE deleting existing records
    nested_fields = {
        "experiences": (Experience, "profile_id"),
        "educations": (Education, "profile_id"),
        "skills": (Skill, "profile_id"),
        "projects": (Project, "profile_id"),
        "certifications": (Certification, "profile_id"),
    }

    for field_name, (ModelClass, fkey_name) in nested_fields.items():
        if field_name in update_data:
            items_data = update_data[field_name]
            # Delete existing records
            getattr(profile, field_name).clear()
            db.query(ModelClass).filter(
                getattr(ModelClass, fkey_name) == profile.id
            ).delete()

            # Add new records
            new_items = []
            for item_data in items_data:
                item_data.pop("id", None)
                new_item = ModelClass(**item_data)
                new_items.append(new_item)
            setattr(profile, field_name, new_items)

    # Update top-level primitive fields
    for field, value in update_data.items():
        if field not in nested_fields:
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


class ProfileVersionResponse(BaseModel):
    id: str
    version: int
    created_at: str | None = None
    summary: str


@router.get("/me/history", response_model=List[ProfileVersionResponse])
def get_my_profile_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get the version history of the current user's profile.
    Returns versions in reverse chronological order.
    """
    return get_profile_history(current_user.id, db)


@router.put("/me/revert/{version_id}", response_model=ProfileResponse)
def revert_my_profile(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Revert the current user's profile to a specific version.
    Creates a version of the current state before reverting.
    """
    try:
        profile = revert_to_version(current_user.id, version_id, db)
        db.commit()
        db.refresh(profile)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
