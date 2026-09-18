from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.api.dependencies import get_user_profile
from app.models.user import User
from app.models.profile import Profile
from app.models.job import Job
from app.services.gap_to_plan import generate_learning_plan

router = APIRouter()

@router.get("/gap-to-plan/{job_id}", response_model=Dict[str, Any])
def get_gap_to_plan(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: Profile = Depends(get_user_profile),
) -> Any:
    """
    Generate a deterministic Gap-to-Plan for a specific job based on the user's profile.
    Identifies missing skills and returns relevant learning resources and project templates.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    plan = generate_learning_plan(db, profile, job)
    return plan
