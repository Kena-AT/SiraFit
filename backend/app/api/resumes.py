from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.core.cache import invalidate_job_related
from app.api.users import get_current_user
from app.api.dependencies import get_user_profile
from app.models.user import User
from app.models.job import Resume, ResumeVersion, Job, AuditLog
from app.models.profile import Profile
from app.schemas.resume import (
    ResumeCreate,
    ResumeDiffResponse,
    ResumeResponse,
    ResumeUpdate,
    ResumeVersionCreate,
    ResumeVersionResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------


def _enrich_resume(db: Session, resume: Resume) -> dict:
    count = db.query(ResumeVersion).filter(ResumeVersion.resume_id == resume.id).count()
    data = ResumeResponse.model_validate(resume).model_dump()
    data["versions_count"] = count
    return data


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
    return [_enrich_resume(db, r) for r in resumes]


@router.post("/", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def create_resume(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    resume_in: ResumeCreate,
) -> Any:
    """Create a new resume."""
    resume = Resume(user_id=current_user.id, **resume_in.model_dump())
    db.add(resume)

    # Add audit log
    log = AuditLog(
        user_id=current_user.id,
        action="created_resume",
        entity_type="resume",
        details={"title": resume.title},
    )
    db.add(log)

    db.commit()
    invalidate_job_related(current_user.id)
    db.refresh(resume)
    return _enrich_resume(db, resume)


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a specific resume."""
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return _enrich_resume(db, resume)


@router.put("/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: uuid.UUID,
    resume_in: ResumeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update a resume."""
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
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
        details={"title": resume.title},
    )
    db.add(log)
    db.commit()
    invalidate_job_related(current_user.id)

    return _enrich_resume(db, resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a resume and all its versions."""
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="deleted_resume",
            entity_type="resume",
            entity_id=resume_id,
            details={"title": resume.title},
        )
    )
    db.delete(resume)
    db.commit()
    invalidate_job_related(current_user.id)


# ---------------------------------------------------------------------------
# Resume Versions
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Resume Versions
# ---------------------------------------------------------------------------


def _enrich_version(version: ResumeVersion) -> ResumeVersionResponse:
    job_title = version.job.title if version.job else None
    job_company = version.job.company if version.job else None
    return ResumeVersionResponse(
        id=version.id,
        resume_id=version.resume_id,
        version_number=version.version_number,
        content=version.content,
        template=version.template,
        job_id=version.job_id,
        parent_version_id=version.parent_version_id,
        source_type=version.source_type or "base",
        job_title=job_title,
        job_company=job_company,
        tailoring_notes=version.tailoring_notes,
        score=version.score,
        status=version.status,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


@router.get("/{resume_id}/versions", response_model=List[ResumeVersionResponse])
def get_resume_versions(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: Profile = Depends(get_user_profile),
) -> Any:
    """Get all versions for a resume, ensuring at least one base version exists."""
    from app.services.resume_versioning import create_base_version_from_profile

    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    versions = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_number.desc())
        .all()
    )

    # Invariant: Each resume has at least one base snapshot
    has_base = any(v.source_type == "base" for v in versions)
    if not has_base:
        create_base_version_from_profile(db, resume, profile)
        versions = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .all()
        )

    return [_enrich_version(v) for v in versions]


@router.post(
    "/{resume_id}/versions",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_resume_version(
    resume_id: uuid.UUID,
    version_in: ResumeVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new version of a resume (manual or from generation)."""
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Validate parent_version_id if provided
    if version_in.parent_version_id:
        parent = (
            db.query(ResumeVersion)
            .filter(
                ResumeVersion.id == version_in.parent_version_id,
                ResumeVersion.resume_id == resume_id,
            )
            .first()
        )
        if not parent:
            raise HTTPException(
                status_code=400,
                detail="Parent version does not belong to this resume or does not exist",
            )

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
        parent_version_id=version_in.parent_version_id,
        source_type=version_in.source_type or ("tailored" if version_in.job_id else "base"),
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
        details={"resume_id": str(resume_id), "version_number": next_version},
    )
    db.add(log)
    db.commit()

    return _enrich_version(version)


@router.get(
    "/{resume_id}/versions/{version_a_id}/diff/{version_b_id}",
    response_model=ResumeDiffResponse,
)
def diff_resume_versions(
    resume_id: uuid.UUID,
    version_a_id: uuid.UUID,
    version_b_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Compare two immutable versions of a resume and return structured semantic differences."""
    from app.services.resume_versioning import compare_resume_versions

    return compare_resume_versions(
        db=db,
        resume_id=resume_id,
        version_a_id=version_a_id,
        version_b_id=version_b_id,
        current_user_id=current_user.id,
    )


@router.post(
    "/{resume_id}/versions/{version_id}/revert",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def revert_resume_version(
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Revert to a historical version by creating a new immutable snapshot with identical content.
    The historical version is never modified or overwritten.
    """
    from app.services.resume_versioning import revert_to_version

    new_version = revert_to_version(
        db=db,
        resume_id=resume_id,
        target_version_id=version_id,
        current_user_id=current_user.id,
    )

    log = AuditLog(
        user_id=current_user.id,
        action="reverted_resume_version",
        entity_type="resume_version",
        entity_id=new_version.id,
        details={
            "resume_id": str(resume_id),
            "target_version_id": str(version_id),
            "new_version_number": new_version.version_number,
        },
    )
    db.add(log)
    db.commit()

    return _enrich_version(new_version)


# ---------------------------------------------------------------------------
# AI Resume Generation
# ---------------------------------------------------------------------------


@router.post("/{resume_id}/generate", response_model=ResumeVersionResponse)
async def generate_resume(
    resume_id: uuid.UUID,
    job_id: uuid.UUID = Query(..., description="Target job ID"),
    parent_version_id: Optional[uuid.UUID] = Query(
        None, description="Source version to tailor from"
    ),
    template: str = Query("minimal", description="Template name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: Profile = Depends(get_user_profile),
) -> Any:
    """
    Generate a tailored resume version for a specific job.

    Enqueues the generation onto the Celery `resume_generation` queue and
    returns immediately with the created version (status=processing). Falls
    back to synchronous execution when Celery/Redis is unavailable.
    """
    from app.worker.tasks import enqueue_resume_generation

    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # If parent_version_id was specified, validate it belongs to this resume
    if parent_version_id:
        parent_v = (
            db.query(ResumeVersion)
            .filter(
                ResumeVersion.id == parent_version_id,
                ResumeVersion.resume_id == resume_id,
            )
            .first()
        )
        if not parent_v:
            raise HTTPException(
                status_code=400,
                detail="Specified parent version not found on this resume",
            )
    else:
        # Default parent to base or latest version
        base_v = (
            db.query(ResumeVersion)
            .filter(
                ResumeVersion.resume_id == resume_id,
                ResumeVersion.source_type == "base",
            )
            .first()
        )
        if base_v:
            parent_version_id = base_v.id
        else:
            latest_v = (
                db.query(ResumeVersion)
                .filter(ResumeVersion.resume_id == resume_id)
                .order_by(ResumeVersion.version_number.desc())
                .first()
            )
            if latest_v:
                parent_version_id = latest_v.id

    # Get next version number
    latest = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_number.desc())
        .first()
    )
    next_version = (latest.version_number + 1) if latest else 1

    # Create processing version with source_type='tailored'
    version = ResumeVersion(
        resume_id=resume_id,
        version_number=next_version,
        content="",
        template=template,
        job_id=job_id,
        parent_version_id=parent_version_id,
        source_type="tailored",
        status="processing",
    )
    db.add(version)

    log = AuditLog(
        user_id=current_user.id,
        action="resume_generation_requested",
        entity_type="resume_version",
        details={
            "resume_id": str(resume_id),
            "job_id": str(job_id),
            "parent_version_id": str(parent_version_id) if parent_version_id else None,
            "template": template,
        },
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

    return _enrich_version(version)


# ---------------------------------------------------------------------------
# Resume Export
# ---------------------------------------------------------------------------


@router.get("/{resume_id}/versions/{version_id}/export")
def export_resume_version(
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
    format: str = Query("html", description="Export format: html, docx, pdf"),
    async_export: bool = Query(
        False, description="If true, queue PDF rendering on a worker and return 202"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export a resume version in the requested format.

    Supported formats:
    - `html` — standalone HTML file rendered via the template engine
    - `docx` — Microsoft Word document
    - `pdf`  — PDF rendered via the HTML template engine + xhtml2pdf

    When ``async_export=True`` and ``format=pdf``, the PDF is rendered on the
    Celery ``pdf_rendering`` queue and a 202 with a polling URL is returned.
    """
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    version = (
        db.query(ResumeVersion)
        .filter(
            ResumeVersion.id == version_id,
            ResumeVersion.resume_id == resume_id,
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    from app.services.resume_export import (
        export_resume_html,
        export_resume_docx,
        export_resume_pdf,
    )
    from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse

    # Asynchronous PDF rendering path
    if async_export and format == "pdf":
        from app.worker.tasks import enqueue_resume_pdf_render

        version.status = "processing"
        db.commit()

        enqueue_resume_pdf_render(version.id)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "processing",
                "version_id": str(version_id),
                "message": "PDF rendering queued. Poll the version to check status.",
                "poll_url": f"/api/v1/resumes/{resume_id}/versions/{version_id}",
            },
        )

    if format == "docx":
        buf = export_resume_docx(version)
        filename = f"resume-{resume_id}-v{version.version_number}.docx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    if format == "pdf":
        buf = export_resume_pdf(version)
        filename = f"resume-{resume_id}-v{version.version_number}.pdf"
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(buf.getbuffer().nbytes),
            },
        )

    # Default: HTML
    html = export_resume_html(version)
    filename = f"resume-{resume_id}-v{version.version_number}.html"
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
