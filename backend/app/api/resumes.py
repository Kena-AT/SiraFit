from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import json

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Resume, ResumeVersion, Job, AuditLog
from app.models.profile import Profile
from app.schemas.resume import (
    ResumeCreate, ResumeResponse, ResumeUpdate,
    ResumeVersionCreate, ResumeVersionResponse, ResumeVersionListResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[ResumeResponse])
def get_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve current user's resumes."""
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a specific resume."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.put("/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: uuid.UUID,
    resume_in: ResumeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    # Add audit log
    log = AuditLog(
        user_id=current_user.id,
        action="updated_resume",
        entity_type="resume",
        details={"title": resume.title}
    )
    db.add(log)
    db.commit()

    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a resume and all its versions."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    db.delete(resume)
    db.commit()


# ---------------------------------------------------------------------------
# Resume Versions
# ---------------------------------------------------------------------------

@router.get("/{resume_id}/versions", response_model=List[ResumeVersionResponse])
def get_resume_versions(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get all versions for a resume."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_number.desc())
        .all()
    )


@router.post("/{resume_id}/versions", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_resume_version(
    resume_id: uuid.UUID,
    version_in: ResumeVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new version of a resume (manual or from generation)."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Get next version number
    latest = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_number.desc())
        .first()
    )
    next_version = (latest.version_number + 1) if latest else 1

    version = ResumeVersion(
        resume_id=resume_id,
        version_number=next_version,
        content=version_in.content,
        template=version_in.template,
        job_id=version_in.job_id,
        tailoring_notes=version_in.tailoring_notes,
        score=version_in.score,
        status=version_in.status or "completed",
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    # Add audit log
    log = AuditLog(
        user_id=current_user.id,
        action="created_resume_version",
        entity_type="resume_version",
        details={"resume_id": str(resume_id), "version_number": next_version}
    )
    db.add(log)
    db.commit()

    return version


# ---------------------------------------------------------------------------
# AI Resume Generation
# ---------------------------------------------------------------------------

@router.post("/{resume_id}/generate", response_model=ResumeVersionResponse)
async def generate_resume(
    resume_id: uuid.UUID,
    job_id: uuid.UUID = Query(..., description="Target job ID"),
    template: str = Query("minimal", description="Template name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate a tailored resume version for a specific job.

    Enqueues the generation onto the Celery `resume_generation` queue and
    returns immediately with the created version (status=processing). Falls
    back to synchronous execution when Celery/Redis is unavailable.
    """
    from app.worker.tasks import enqueue_resume_generation

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create a profile first.")

    # Get next version number
    latest = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_number.desc())
        .first()
    )
    next_version = (latest.version_number + 1) if latest else 1

    # Create processing version
    version = ResumeVersion(
        resume_id=resume_id,
        version_number=next_version,
        content="",
        template=template,
        job_id=job_id,
        status="processing",
    )
    db.add(version)

    log = AuditLog(
        user_id=current_user.id,
        action="resume_generation_requested",
        entity_type="resume_version",
        details={"resume_id": str(resume_id), "job_id": str(job_id), "template": template},
    )
    db.add(log)
    db.commit()
    db.refresh(version)

    # Enqueue background generation (synchronous fallback handled inside)
    enqueue_resume_generation(
        version_id=version.id,
        user_id=str(current_user.id),
        profile_id=profile.id,
        job_id=job.id,
        template=template,
    )

    return version


# ---------------------------------------------------------------------------
# Resume Export
# ---------------------------------------------------------------------------

@router.get("/{resume_id}/versions/{version_id}/export")
def export_resume_version(
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
    format: str = Query("html", description="Export format: html, docx"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export a resume version in the requested format.

    Supported formats:
    - `html` — standalone HTML file rendered via the template engine
    - `docx` — Microsoft Word document
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    version = db.query(ResumeVersion).filter(
        ResumeVersion.id == version_id,
        ResumeVersion.resume_id == resume_id,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    from app.services.resume_export import export_resume_html, export_resume_docx
    from fastapi.responses import StreamingResponse, HTMLResponse

    if format == "docx":
        buf = export_resume_docx(version)
        filename = f"resume-{resume_id}-v{version.version_number}.docx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Default: HTML
    html = export_resume_html(version)
    filename = f"resume-{resume_id}-v{version.version_number}.html"
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )