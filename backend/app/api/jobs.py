from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse

router = APIRouter()

@router.get("/", response_model=List[JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve jobs."""
    jobs = db.query(Job).offset(skip).limit(limit).all()
    return jobs

@router.post("/", response_model=JobResponse)
def create_job(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_in: JobCreate,
) -> Any:
    """Create a new job."""
    job = db.query(Job).filter(Job.external_id == job_in.external_id).first()
    if job:
        raise HTTPException(
            status_code=400,
            detail="A job with this external_id already exists.",
        )
    job = Job(**job_in.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_id: uuid.UUID,
) -> Any:
    """Get job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
