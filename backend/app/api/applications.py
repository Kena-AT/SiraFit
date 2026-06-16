from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import JobApplication, Job, AuditLog
from app.models.profile import Profile
from app.schemas.job import JobApplicationCreate, JobApplicationResponse, JobApplicationUpdate
from app.services.scoring import calculate_match_score

router = APIRouter()

@router.get("/", response_model=List[JobApplicationResponse])
def get_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve current user's job applications."""
    applications = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return applications

@router.post("/", response_model=JobApplicationResponse)
def create_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_in: JobApplicationCreate,
) -> Any:
    """Create a new job application and calculate initial score."""
    job = db.query(Job).filter(Job.id == app_in.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.job_id == app_in.job_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Application already exists for this job")

    application = JobApplication(
        user_id=current_user.id,
        **app_in.model_dump()
    )
    
    # Calculate score
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if profile:
        score, reason = calculate_match_score(profile, job)
        application.score = score
        application.score_reason = reason

    db.add(application)
    
    # Add audit log
    log = AuditLog(
        user_id=current_user.id,
        action="created_application",
        entity_type="application",
        details={"job_title": job.title}
    )
    db.add(log)
    
    db.commit()
    db.refresh(application)
    return application

@router.put("/{app_id}", response_model=JobApplicationResponse)
def update_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
    app_in: JobApplicationUpdate,
) -> Any:
    """Update a job application."""
    application = db.query(JobApplication).filter(
        JobApplication.id == app_id,
        JobApplication.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    update_data = app_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)

    db.add(application)
    db.commit()
    db.refresh(application)
    return application
