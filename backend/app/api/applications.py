from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import JobApplication, Job, AuditLog
from app.models.profile import Profile
from app.schemas.job import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
    ApplicationEventResponse,
    ApplicationNoteCreate,
    ApplicationNoteUpdate,
    ApplicationNoteResponse,
    ApplicationContactCreate,
    ApplicationContactUpdate,
    ApplicationContactResponse,
    StatusTransitionRequest,
    FollowUpSet,
    FollowUpItem,
)
from app.services.scoring import analyze_match_score
from app.services.application import (
    transition_application,
    get_events_for_application,
    get_all_events_for_user,
    create_note,
    get_notes_for_application,
    update_note,
    delete_note,
    create_contact,
    get_contacts_for_application,
    update_contact,
    delete_contact,
)

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
async def create_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_in: JobApplicationCreate,
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key"),
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
) -> Any:
    """Create a new job application and calculate initial score."""
    job = db.query(Job).filter(Job.id == app_in.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = (
        db.query(JobApplication)
        .filter(
            JobApplication.user_id == current_user.id,
            JobApplication.job_id == app_in.job_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Application already exists for this job"
        )

    application = JobApplication(user_id=current_user.id, **app_in.model_dump())

    # Calculate score
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if profile:
        score, reason = await analyze_match_score(
            profile,
            job,
            req_api_key=x_ai_api_key,
            provider=x_ai_provider,
            model=x_ai_model,
        )
        application.score = score
        application.score_reason = reason

    db.add(application)

    # Add audit log
    log = AuditLog(
        user_id=current_user.id,
        action="created_application",
        entity_type="application",
        details={"job_title": job.title},
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
    application = (
        db.query(JobApplication)
        .filter(JobApplication.id == app_id, JobApplication.user_id == current_user.id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    update_data = app_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)

    db.add(application)
    db.commit()
    db.refresh(application)
    return application


# --- Sprint 9: Timeline Events ---
# NOTE: /timeline is registered BEFORE /{app_id} so the static path wins route
# matching. FastAPI matches routes in registration order, and "timeline" would
# otherwise be captured as the {app_id} UUID parameter (422 validation error).


@router.get("/timeline", response_model=List[ApplicationEventResponse])
def user_timeline(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 100,
) -> Any:
    """Get all events across applications (global timeline page)."""
    return get_all_events_for_user(db, current_user.id, limit)


# --- Follow-up Center ---
# Registered before /{app_id} so "followups" is not captured as a UUID.


@router.get("/followups", response_model=List[FollowUpItem])
def list_followups(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_past: bool = Query(
        False, description="Include already-passed follow-up dates"
    ),
) -> Any:
    """List all applications that have a follow-up date set, soonest first."""
    from datetime import datetime, timezone

    query = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.follow_up_at.isnot(None),
    )
    if not include_past:
        query = query.filter(JobApplication.follow_up_at >= datetime.now(timezone.utc))

    applications = query.order_by(asc(JobApplication.follow_up_at)).all()

    items = []
    for app in applications:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        items.append(
            FollowUpItem(
                application_id=app.id,
                job_title=job.title if job else "Unknown",
                company=job.company if job else "Unknown",
                status=app.status or "saved",
                follow_up_at=app.follow_up_at,
                follow_up_note=app.follow_up_note,
                score=app.score,
            )
        )
    return items


@router.put("/{app_id}/followup", response_model=JobApplicationResponse)
def set_followup(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
    payload: FollowUpSet,
) -> Any:
    """Set or clear the follow-up date on an application."""
    application = (
        db.query(JobApplication)
        .filter(JobApplication.id == app_id, JobApplication.user_id == current_user.id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.follow_up_at = payload.follow_up_at
    application.follow_up_note = payload.follow_up_note
    db.commit()
    db.refresh(application)
    return application


@router.get("/{app_id}", response_model=JobApplicationResponse)
def get_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
) -> Any:
    """Get a single application."""
    application = (
        db.query(JobApplication)
        .filter(JobApplication.id == app_id, JobApplication.user_id == current_user.id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


# --- Sprint 9: Status Transitions ---


@router.post("/{app_id}/status", response_model=JobApplicationResponse)
def transition_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
    req: StatusTransitionRequest,
) -> Any:
    """Transition an application to a new status (deterministic workflow)."""
    try:
        return transition_application(db, app_id, current_user.id, req.to_status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Sprint 9: Timeline Events (per-application) ---


@router.get("/{app_id}/events", response_model=List[ApplicationEventResponse])
def list_application_events(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
) -> Any:
    """Get timeline events for an application."""
    return get_events_for_application(db, app_id, current_user.id)


# --- Sprint 9: Notes ---


@router.post("/{app_id}/notes", response_model=ApplicationNoteResponse)
def add_note(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
    note_in: ApplicationNoteCreate,
) -> Any:
    """Create a note on an application."""
    return create_note(
        db, app_id, current_user.id, note_in.body, note_in.author, note_in.pinned
    )


@router.get("/{app_id}/notes", response_model=List[ApplicationNoteResponse])
def list_notes(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
) -> Any:
    """List all notes for an application (pinned first)."""
    return get_notes_for_application(db, app_id, current_user.id)


@router.put("/notes/{note_id}", response_model=ApplicationNoteResponse)
def edit_note(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    note_id: uuid.UUID,
    note_in: ApplicationNoteUpdate,
) -> Any:
    """Update a note."""
    note = update_note(
        db,
        note_id,
        current_user.id,
        body=note_in.body,
        pinned=note_in.pinned,
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/notes/{note_id}", status_code=204)
def remove_note(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    note_id: uuid.UUID,
) -> None:
    """Delete a note."""
    if not delete_note(db, note_id, current_user.id):
        raise HTTPException(status_code=404, detail="Note not found")


# --- Sprint 9: Contacts ---


@router.post("/{app_id}/contacts", response_model=ApplicationContactResponse)
def add_contact(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
    contact_in: ApplicationContactCreate,
) -> Any:
    """Create a contact on an application."""
    return create_contact(
        db,
        app_id,
        current_user.id,
        name=contact_in.name,
        email=contact_in.email,
        phone=contact_in.phone,
        role=contact_in.role,
        company=contact_in.company,
        linkedin=contact_in.linkedin,
        notes=contact_in.notes,
        is_primary=contact_in.is_primary,
    )


@router.get("/{app_id}/contacts", response_model=List[ApplicationContactResponse])
def list_contacts(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    app_id: uuid.UUID,
) -> Any:
    """List all contacts for an application (primary first)."""
    return get_contacts_for_application(db, app_id, current_user.id)


@router.put("/contacts/{contact_id}", response_model=ApplicationContactResponse)
def edit_contact(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    contact_id: uuid.UUID,
    contact_in: ApplicationContactUpdate,
) -> Any:
    """Update a contact."""
    contact = update_contact(
        db, contact_id, current_user.id, **contact_in.model_dump(exclude_unset=True)
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/contacts/{contact_id}", status_code=204)
def remove_contact(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    contact_id: uuid.UUID,
) -> None:
    """Delete a contact."""
    if not delete_contact(db, contact_id, current_user.id):
        raise HTTPException(status_code=404, detail="Contact not found")
