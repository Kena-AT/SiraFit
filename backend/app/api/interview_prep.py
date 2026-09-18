from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.api.dependencies import get_user_profile
from app.models.user import User
from app.models.profile import Profile
from app.models.job import Job
from app.services.interview_prep import generate_prep_questions, RateLimitExceeded

router = APIRouter()

@router.post("/{job_id}", response_model=Dict[str, Any])
async def create_interview_prep(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: Profile = Depends(get_user_profile),
) -> Any:
    """
    Generate 3 highly specific interview questions based on the candidate's skill gaps to the job.
    Enforces a strict rate limit of 10 generations per user per 24 hours.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        prep_data = await generate_prep_questions(db, current_user.id, profile, job)
        return prep_data
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
