from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.profile import Profile, Experience, Education, Skill, Project, Certification
from app.schemas.profile import ProfileResponse, ProfileUpdate

router = APIRouter()

@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get the current user's profile.
    If no profile exists, creates an empty one and returns it.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
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
    Update the current user's profile monolithically.
    Nested objects (experiences, educations, etc.) are fully replaced if provided in the payload.
    This simplifies autosave functionality on the frontend.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    update_data = profile_in.model_dump(exclude_unset=True)
    
    # Extract nested lists if they are present in the update payload
    nested_fields = {
        "experiences": (Experience, "profile_id"),
        "educations": (Education, "profile_id"),
        "skills": (Skill, "profile_id"),
        "projects": (Project, "profile_id"),
        "certifications": (Certification, "profile_id")
    }

    # Update top-level primitive fields
    for field, value in update_data.items():
        if field not in nested_fields:
            setattr(profile, field, value)

    # Process nested objects
    for field_name, (ModelClass, fkey_name) in nested_fields.items():
        if field_name in update_data:
            # We completely replace the list if it's provided in the payload
            # Step 1: Delete existing records
            getattr(profile, field_name).clear()
            db.query(ModelClass).filter(getattr(ModelClass, fkey_name) == profile.id).delete()
            
            # Step 2: Add new records
            items_data = update_data[field_name]
            new_items = []
            for item_data in items_data:
                # Remove any existing ids so they are generated fresh
                item_data.pop("id", None)
                new_item = ModelClass(**item_data)
                new_items.append(new_item)
                
            # Assign the new list back to the relationship
            setattr(profile, field_name, new_items)

    db.commit()
    db.refresh(profile)
    return profile
