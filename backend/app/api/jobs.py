from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Job, JobImport
from app.schemas.job import (
    JobCreate, JobResponse, JobImportCreate,
    JobImportResponse, ImportResultResponse, JobData,
)
from app.services.job_import import process_import

router = APIRouter()


@router.get("/", response_model=List[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    """List all jobs."""
    return db.query(Job).offset(skip).limit(limit).all()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/import", response_model=ImportResultResponse)
def import_jobs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    import_in: JobImportCreate,
) -> Any:
    """Import jobs from a URL or pasted description."""
    import_record, jobs_data, errors = process_import(
        db, current_user.id, import_in.source_type, import_in.data,
    )

    return ImportResultResponse(
        import_record=JobImportResponse.model_validate(import_record),
        jobs=[JobData(**job, is_duplicate=False) for job in jobs_data],
        errors=errors,
    )


@router.get("/import/history", response_model=List[JobImportResponse])
def get_import_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    """Get import history for the current user."""
    return (
        db.query(JobImport)
        .filter(JobImport.user_id == current_user.id)
        .order_by(JobImport.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/import/{import_id}", response_model=ImportResultResponse)
def get_import_detail(
    import_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get details of a specific import."""
    import_record = db.query(JobImport).filter(JobImport.id == import_id).first()
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    if import_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return ImportResultResponse(
        import_record=JobImportResponse.model_validate(import_record),
        jobs=[],
        errors=[],
    )
