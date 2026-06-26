from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Job, JobImport
from app.schemas.job import JobCreate, JobResponse, JobImportCreate, JobImportResponse
from app.services.job_import import process_import

router = APIRouter()

@router.get("/", response_model=List[JobResponse])
# ... (rest of the file)
@router.post("/import", response_model=JobImportResponse)
def import_jobs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    import_in: JobImportCreate,
) -> Any:
    """Import jobs."""
    return process_import(db, current_user.id, import_in.source_type, import_in.data)

@router.get("/import/history", response_model=List[JobImportResponse])
def get_import_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get import history."""
    return db.query(JobImport).filter(JobImport.user_id == current_user.id).order_by(JobImport.created_at.desc()).all()

@router.get("/{job_id}", response_model=JobResponse)
# ... (rest of the file)
