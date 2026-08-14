from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.profile import (
    Profile,
    Experience,
    Education,
    Skill,
    Project,
    Certification,
)
from app.schemas.profile import ProfileResponse, ProfileUpdate

router = APIRouter()


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
    Update the current user's profile with validation before delete-and-replace.
    Nested objects (experiences, educations, etc.) are validated before existing
    records are cleared, preventing data loss on invalid payloads.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()

    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    update_data = profile_in.model_dump(exclude_unset=True)

    # Validate nested list items BEFORE deleting existing records
    # This prevents data loss if the payload has invalid data
    nested_fields = {
        "experiences": (Experience, "profile_id"),
        "educations": (Education, "profile_id"),
        "skills": (Skill, "profile_id"),
        "projects": (Project, "profile_id"),
        "certifications": (Certification, "profile_id"),
    }

    # Validate nested fields if present in the update payload
    for field_name, (ModelClass, fkey_name) in nested_fields.items():
        if field_name in update_data:
            items_data = update_data[field_name]
            # Validate each item has required fields before deleting existing
            for item_data in items_data:
                # Check for required fields based on model
                if not item_data.get("title") and field_name == "experiences":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Experience item missing required field: title",
                    )
                if not item_data.get("name") and field_name == "skills":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Skill item missing required field: name",
                    )
            # At this point validation passed - proceed with delete-and-replace
            # Step 1: Delete existing records
            getattr(profile, field_name).clear()
            db.query(ModelClass).filter(
                getattr(ModelClass, fkey_name) == profile.id
            ).delete()

            # Step 2: Add new records
            new_items = []
            for item_data in items_data:
                # Remove any existing ids so they are generated fresh
                item_data.pop("id", None)
                new_item = ModelClass(**item_data)
                new_items.append(new_item)

            # Assign the new list back to the relationship
            setattr(profile, field_name, new_items)

    # Update top-level primitive fields
    for field, value in update_data.items():
        if field not in nested_fields:
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
