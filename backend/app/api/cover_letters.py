"""Cover letter API endpoints."""

from typing import Any, List

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.cover_letter import CoverLetter
from app.schemas.cover_letter import (
    CoverLetterCreate,
    CoverLetterResponse,
    CoverLetterUpdate,
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[CoverLetterResponse])
def get_cover_letters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve current user's cover letters."""
    return (
        db.query(CoverLetter)
        .filter(CoverLetter.user_id == current_user.id)
        .order_by(CoverLetter.created_at.desc())
        .all()
    )


@router.post("/", response_model=CoverLetterResponse, status_code=status.HTTP_201_CREATED)
def create_cover_letter(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    letter_in: CoverLetterCreate,
) -> Any:
    """Create a new cover letter."""
    letter = CoverLetter(
        user_id=current_user.id,
        **letter_in.model_dump()
    )
    db.add(letter)
    db.commit()
    db.refresh(letter)
    return letter


@router.get("/{letter_id}", response_model=CoverLetterResponse)
def get_cover_letter(
    letter_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a specific cover letter."""
    letter = db.query(CoverLetter).filter(
        CoverLetter.id == letter_id,
        CoverLetter.user_id == current_user.id,
    ).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return letter


@router.put("/{letter_id}", response_model=CoverLetterResponse)
def update_cover_letter(
    letter_id: uuid.UUID,
    letter_in: CoverLetterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update a cover letter."""
    letter = db.query(CoverLetter).filter(
        CoverLetter.id == letter_id,
        CoverLetter.user_id == current_user.id,
    ).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")

    update_data = letter_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(letter, field, value)

    db.add(letter)
    db.commit()
    db.refresh(letter)
    return letter


@router.delete("/{letter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cover_letter(
    letter_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a cover letter."""
    letter = db.query(CoverLetter).filter(
        CoverLetter.id == letter_id,
        CoverLetter.user_id == current_user.id,
    ).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")

    db.delete(letter)
    db.commit()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@router.get("/{letter_id}/export")
def export_cover_letter(
    letter_id: uuid.UUID,
    format: str = Query("pdf", description="Export format: pdf, html"),
    async_export: bool = Query(False, description="If true, queue PDF rendering on a worker and return 202"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Export a cover letter as PDF or HTML.

    When ``async_export=True`` and ``format=pdf``, the PDF is rendered on the
    Celery ``pdf_rendering`` queue and a 202 with a polling URL is returned.
    """
    from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
    from app.services.cover_letter_generation import render_cover_letter_html
    from app.services.pdf_rendering import render_html_to_pdf_bytes

    letter = db.query(CoverLetter).filter(
        CoverLetter.id == letter_id,
        CoverLetter.user_id == current_user.id,
    ).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")

    # Asynchronous PDF rendering path
    if async_export and format == "pdf":
        from app.worker.tasks import enqueue_cover_letter_pdf_render

        letter.status = "processing"
        db.commit()

        enqueue_cover_letter_pdf_render(letter.id)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "processing",
                "letter_id": str(letter_id),
                "message": "PDF rendering queued. Poll the cover letter to check status.",
                "poll_url": f"/api/v1/cover-letters/{letter_id}",
            },
        )

    html = render_cover_letter_html(letter.body, template=letter.template or "classic")

    if format == "html":
        filename = f"cover-letter-{letter_id}.html"
        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Default: PDF (synchronous)
    buf = render_html_to_pdf_bytes(html)
    filename = f"cover-letter-{letter_id}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(buf.getbuffer().nbytes),
        },
    )


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=CoverLetterGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_cover_letter_new(
    letter_in: CoverLetterGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate a brand-new cover letter using AI (creates a new record)."""
    from app.models.job import Job
    from app.models.profile import Profile
    from app.services.cover_letter_generation import generate_cover_letter as _generate

    job = db.query(Job).filter(Job.id == letter_in.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile required to generate cover letter")

    body = asyncio.run(_generate(profile, job, tone=letter_in.tone or "matching"))

    letter = CoverLetter(
        user_id=current_user.id,
        resume_id=letter_in.resume_id,
        job_id=letter_in.job_id,
        title=f"Cover letter for {job.company} — {job.title}",
        body=body,
        tone=letter_in.tone or "matching",
        template=letter_in.template or "classic",
        status="completed",
    )
    db.add(letter)
    db.commit()
    db.refresh(letter)

    return {
        "cover_letter_id": letter.id,
        "status": letter.status,
        "message": "Cover letter generated successfully.",
    }


@router.post("/{letter_id}/generate", response_model=CoverLetterGenerateResponse)
def regenerate_cover_letter(
    letter_id: uuid.UUID,
    letter_in: CoverLetterGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Re-generate an existing cover letter using AI (updates the existing record)."""
    from app.models.job import Job
    from app.models.profile import Profile
    from app.services.cover_letter_generation import generate_cover_letter as _generate

    # Verify ownership of the existing letter
    letter = db.query(CoverLetter).filter(
        CoverLetter.id == letter_id,
        CoverLetter.user_id == current_user.id,
    ).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")

    job = db.query(Job).filter(Job.id == letter_in.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile required to generate cover letter")

    body = asyncio.run(_generate(profile, job, tone=letter_in.tone or "matching"))

    # Update the EXISTING letter instead of creating a new one
    letter.body = body
    letter.job_id = letter_in.job_id
    letter.resume_id = letter_in.resume_id
    letter.tone = letter_in.tone or "matching"
    letter.template = letter_in.template or letter.template or "classic"
    letter.status = "completed"
    letter.pdf_url = None  # Invalidate cached PDF

    db.add(letter)
    db.commit()
    db.refresh(letter)

    return {
        "cover_letter_id": letter.id,
        "status": letter.status,
        "message": "Cover letter regenerated successfully.",
    }
