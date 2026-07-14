"""
Application service for Sprint 9 — status transitions, timeline events, notes, and contacts.

The module defines a deterministic status machine, creates timeline events on
every mutation, and provides CRUD helpers for notes and contacts.
"""

from __future__ import annotations

import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.job import (
    JobApplication,
    AuditLog,
    ApplicationNote,
    ApplicationContact,
    ApplicationEvent,
)


# ---------------------------------------------------------------------------
# Status Machine (Sprint 9)
# ---------------------------------------------------------------------------

# Ordered list of valid statuses for the linear workflow
ALLOWED_STATUSES = [
    "saved",
    "preparing",
    "applied",
    "screening",
    "interview",
    "final_round",
    "offer",
    "rejected",
    "withdrawn",
    "archived",
]

# Map status -> canonical order (used for validation)
STATUS_ORDER = {s: i for i, s in enumerate(ALLOWED_STATUSES)}

# Transitions that are valid from each status (prevents illegal backward moves without explicit reason)
VALID_NEXT = {
    "saved": {"preparing", "applied", "archived"},
    "preparing": {"saved", "applied", "archived"},
    "applied": {"screening", "rejected", "archived"},
    "screening": {"interview", "rejected", "archived"},
    "interview": {"final_round", "rejected", "archived"},
    "final_round": {"offer", "rejected", "archived"},
    "offer": {"rejected", "archived"},
    # Terminal states
    "rejected": {"archived"},
    "withdrawn": {"archived"},
    "archived": set(),
}


def validate_transition(from_status: str, to_status: str) -> bool:
    """Return True if the status transition is allowed."""
    return to_status in VALID_NEXT.get(from_status, set())


def transition_application(
    db: Session,
    application_id: uuid.UUID,
    user_id: uuid.UUID,
    to_status: str,
) -> JobApplication:
    """
    Transition an application to a new status.

    - Validates the transition is allowed
    - Updates the status column
    - Creates an ApplicationEvent row recording the change
    - Creates an AuditLog entry
    - Returns the updated application
    """
    application = (
        db.query(JobApplication)
        .filter(JobApplication.id == application_id, JobApplication.user_id == user_id)
        .first()
    )
    if not application:
        raise ValueError("Application not found")

    old_status = application.status or "saved"
    if not validate_transition(old_status, to_status):
        raise ValueError(f"Invalid status transition: {old_status} -> {to_status}")

    # Update the application
    application.status = to_status
    db.commit()
    db.refresh(application)

    # Create timeline event

    event = ApplicationEvent(
        application_id=application_id,
        user_id=user_id,
        event_type="status_change",
        title=f"Status changed to {to_status}",
        description=f"Changed from {old_status} to {to_status}",
        event_metadata={"from_status": old_status, "to_status": to_status},
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)

    # Audit log
    log = AuditLog(
        user_id=user_id,
        action="application_status_change",
        entity_type="application",
        entity_id=application_id,
        details={"from_status": old_status, "to_status": to_status},
    )
    db.add(log)
    db.commit()

    return application


# ---------------------------------------------------------------------------
# Notes CRUD
# ---------------------------------------------------------------------------


def create_note(
    db: Session,
    application_id: uuid.UUID,
    user_id: uuid.UUID,
    body: str,
    author: Optional[str] = None,
    pinned: bool = False,
) -> "ApplicationNote":
    """Create a note attached to an application."""

    note = ApplicationNote(
        application_id=application_id,
        user_id=user_id,
        body=body,
        author=author,
        pinned=pinned,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_notes_for_application(
    db: Session,
    application_id: uuid.UUID,
    user_id: uuid.UUID,
) -> List["ApplicationNote"]:
    """List notes for an application, pinned first."""

    return (
        db.query(ApplicationNote)
        .filter(
            ApplicationNote.application_id == application_id,
            ApplicationNote.user_id == user_id,
        )
        .order_by(ApplicationNote.pinned.desc(), ApplicationNote.created_at.desc())
        .all()
    )


def update_note(
    db: Session,
    note_id: uuid.UUID,
    user_id: uuid.UUID,
    body: Optional[str] = None,
    pinned: Optional[bool] = None,
) -> Optional["ApplicationNote"]:
    """Update a note's body or pin status."""

    note = (
        db.query(ApplicationNote)
        .filter(ApplicationNote.id == note_id, ApplicationNote.user_id == user_id)
        .first()
    )
    if not note:
        return None

    if body is not None:
        note.body = body
    if pinned is not None:
        note.pinned = pinned
    note.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Delete a note. Returns True if deleted."""

    note = (
        db.query(ApplicationNote)
        .filter(ApplicationNote.id == note_id, ApplicationNote.user_id == user_id)
        .first()
    )
    if not note:
        return False

    db.delete(note)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Contacts CRUD
# ---------------------------------------------------------------------------


def create_contact(
    db: Session,
    application_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    role: str = "recruiter",
    company: Optional[str] = None,
    linkedin: Optional[str] = None,
    notes: Optional[str] = None,
    is_primary: bool = False,
) -> "ApplicationContact":
    """Create a contact attached to an application."""

    contact = ApplicationContact(
        application_id=application_id,
        user_id=user_id,
        name=name,
        email=email,
        phone=phone,
        role=role,
        company=company,
        linkedin=linkedin,
        notes=notes,
        is_primary=is_primary,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contacts_for_application(
    db: Session,
    application_id: uuid.UUID,
    user_id: uuid.UUID,
) -> List["ApplicationContact"]:
    """List contacts for an application, primary first."""

    return (
        db.query(ApplicationContact)
        .filter(
            ApplicationContact.application_id == application_id,
            ApplicationContact.user_id == user_id,
        )
        .order_by(
            ApplicationContact.is_primary.desc(), ApplicationContact.created_at.desc()
        )
        .all()
    )


def update_contact(
    db: Session,
    contact_id: uuid.UUID,
    user_id: uuid.UUID,
    **kwargs,
) -> Optional["ApplicationContact"]:
    """Update a contact with arbitrary kwargs."""

    contact = (
        db.query(ApplicationContact)
        .filter(
            ApplicationContact.id == contact_id, ApplicationContact.user_id == user_id
        )
        .first()
    )
    if not contact:
        return None

    for field in (
        "name",
        "email",
        "phone",
        "role",
        "company",
        "linkedin",
        "notes",
        "is_primary",
    ):
        if field in kwargs:
            setattr(contact, field, kwargs[field])
    contact.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Delete a contact. Returns True if deleted."""

    contact = (
        db.query(ApplicationContact)
        .filter(
            ApplicationContact.id == contact_id, ApplicationContact.user_id == user_id
        )
        .first()
    )
    if not contact:
        return False

    db.delete(contact)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Timeline Events Fetch
# ---------------------------------------------------------------------------


def get_events_for_application(
    db: Session,
    application_id: uuid.UUID,
    user_id: uuid.UUID,
) -> List["ApplicationEvent"]:
    """List timeline events for an application, newest first."""

    return (
        db.query(ApplicationEvent)
        .filter(
            ApplicationEvent.application_id == application_id,
            ApplicationEvent.user_id == user_id,
        )
        .order_by(ApplicationEvent.occurred_at.desc())
        .all()
    )


def get_all_events_for_user(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 100,
) -> List["ApplicationEvent"]:
    """Fetch recent events across all applications for the user's timeline page."""

    return (
        db.query(ApplicationEvent)
        .filter(ApplicationEvent.user_id == user_id)
        .order_by(ApplicationEvent.occurred_at.desc())
        .limit(limit)
        .all()
    )
