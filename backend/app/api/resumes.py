from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Resume, AuditLog
from app.schemas.resume import ResumeCreate, ResumeResponse, ResumeUpdate

router = APIRouter()

@router.get("/", response_model=List[ResumeResponse])
def get_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve current user's resumes."""
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return resumes

@router.post("/", response_model=ResumeResponse)
def create_resume(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    resume_in: ResumeCreate,
) -> Any:
    """Create a new resume."""
    resume = Resume(
        user_id=current_user.id,
        **resume_in.model_dump()
    )
    db.add(resume)
    
    # Add audit log
    log = AuditLog(
        user_id=current_user.id,
        action="created_resume",
        entity_type="resume",
        details={"title": resume.title}
    )
    db.add(log)

    db.commit()
    db.refresh(resume)
    return resume

@router.put("/{resume_id}", response_model=ResumeResponse)
def update_resume(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    resume_id: uuid.UUID,
    resume_in: ResumeUpdate,
) -> Any:
    """Update a resume."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    update_data = resume_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resume, field, value)

    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume
