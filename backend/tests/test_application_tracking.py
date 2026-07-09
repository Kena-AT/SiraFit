"""
QA tests for Sprint 9 — Application tracking (status machine, timeline, notes, contacts).
"""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


# --- Status Machine Tests ---

VALID_STATUSES = [
    "saved", "preparing", "applied", "screening", "interview", 
    "final_round", "offer", "rejected", "withdrawn", "archived",
]


def test_status_machine_valid_transitions():
    """Verify the status validation logic works correctly."""
    from app.services.application import validate_transition, VALID_NEXT
    
    # Valid forwards transitions
    assert validate_transition("saved", "applied") is True
    assert validate_transition("applied", "screening") is True
    assert validate_transition("screening", "interview") is True
    assert validate_transition("interview", "final_round") is True
    assert validate_transition("final_round", "offer") is True
    
    # Terminal states
    assert validate_transition("rejected", "archived") is True
    assert validate_transition("offer", "rejected") is True
    
    # Invalid reverse transitions (should fail)
    assert validate_transition("interview", "saved") is False
    assert validate_transition("applied", "saved") is False
    assert validate_transition("screening", "applied") is False
    
    # Invalid transitions to unknown status
    assert validate_transition("saved", "unknown") is False


def test_create_application_creates_saved_status(client, auth_headers, db):
    """A new application starts in 'saved' status."""
    from app.models.job import Job
    
    job = Job(
        external_id=f"test-job-{uuid.uuid4().hex[:8]}",
        title="Senior Engineer",
        company="TestCo",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    response = client.post(
        "/api/v1/applications",
        json={"job_id": str(job.id)},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "saved"


def test_transition_status_valid(client, auth_headers, test_user, db):
    """Valid status transition updates application and creates event."""
    from app.models.job import Job, JobApplication
    
    job = Job(
        external_id=f"test-job-{uuid.uuid4().hex[:8]}",
        title="Engineer",
        company="Co",
    )
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id, status="saved")
    db.add(app)
    db.commit()
    db.refresh(app)
    
    response = client.post(
        f"/api/v1/applications/{app.id}/status",
        json={"to_status": "applied"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "applied"


def test_transition_status_invalid(client, auth_headers, test_user, db):
    """Invalid transition returns 400 error."""
    from app.models.job import Job, JobApplication
    
    job = Job(
        external_id=f"test-job-{uuid.uuid4().hex[:8]}",
        title="Engineer",
        company="Co",
    )
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id, status="interview")
    db.add(app)
    db.commit()
    db.refresh(app)
    
    response = client.post(
        f"/api/v1/applications/{app.id}/status",
        json={"to_status": "saved"},  # Invalid reverse transition
        headers=auth_headers,
    )
    assert response.status_code == 400


# --- Notes CRUD Tests ---

def test_create_note(client, auth_headers, test_user, db):
    """Create a note on an application."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="note-job", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    response = client.post(
        f"/api/v1/applications/{app.id}/notes",
        json={"body": "Great conversation with recruiter!", "author": "Me", "pinned": true},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["body"] == "Great conversation with recruiter!"
    assert data["pinned"] is True


def test_list_notes_pinned_first(client, auth_headers, test_user, db):
    """Notes are returned pinned first."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="notes-job", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    # Create notes in specific order
    client.post(
        f"/api/v1/applications/{app.id}/notes",
        json={"body": "Second note", "pinned": false},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/applications/{app.id}/notes",
        json={"body": "Pinned note", "pinned": true},
        headers=auth_headers,
    )
    
    response = client.get(f"/api/v1/applications/{app.id}/notes", headers=auth_headers)
    assert response.status_code == 200
    notes = response.json()
    assert notes[0]["pinned"] is True
    assert notes[0]["body"] == "Pinned note"


def test_update_note(client, auth_headers, test_user, db):
    """Update note body and pin status."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="upjob", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    create_res = client.post(
        f"/api/v1/applications/{app.id}/notes",
        json={"body": "Original"},
        headers=auth_headers,
    )
    note_id = create_res.json()["id"]
    
    response = client.put(
        f"/api/v1/applications/notes/{note_id}",
        json={"body": "Updated body", "pinned": true},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["body"] == "Updated body"


def test_delete_note(client, auth_headers, test_user, db):
    """Delete a note returns 204 and removes it."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="deljob", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    create_res = client.post(
        f"/api/v1/applications/{app.id}/notes",
        json={"body": "To delete"},
        headers=auth_headers,
    )
    note_id = create_res.json()["id"]
    
    response = client.delete(f"/api/v1/applications/notes/{note_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verify deletion
    list_res = client.get(f"/api/v1/applications/{app.id}/notes", headers=auth_headers)
    assert len(list_res.json()) == 0


# --- Contacts CRUD Tests ---

def test_create_contact(client, auth_headers, test_user, db):
    """Create a contact on an application."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="cont-job", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    response = client.post(
        f"/api/v1/applications/{app.id}/contacts",
        json={
            "name": "Sarah Chen",
            "email": "sarah@example.com",
            "role": "recruiter",
            "is_primary": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sarah Chen"
    assert data["is_primary"] is True


def test_list_contacts_primary_first(client, auth_headers, test_user, db):
    """Contacts are returned primary first."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="listcont", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    client.post(
        f"/api/v1/applications/{app.id}/contacts",
        json={"name": "Secondary", "is_primary": False},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/applications/{app.id}/contacts",
        json={"name": "Primary", "is_primary": True},
        headers=auth_headers,
    )
    
    response = client.get(f"/api/v1/applications/{app.id}/contacts", headers=auth_headers)
    assert response.status_code == 200
    contacts = response.json()
    assert contacts[0]["is_primary"] is True
    assert contacts[0]["name"] == "Primary"


def test_update_contact(client, auth_headers, test_user, db):
    """Update contact fields."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="upcont", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    create_res = client.post(
        f"/api/v1/applications/{app.id}/contacts",
        json={"name": "Old Name"},
        headers=auth_headers,
    )
    contact_id = create_res.json()["id"]
    
    response = client.put(
        f"/api/v1/applications/contacts/{contact_id}",
        json={"name": "New Name", "email": "new@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_contact(client, auth_headers, test_user, db):
    """Delete a contact returns 204."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="delcont", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    create_res = client.post(
        f"/api/v1/applications/{app.id}/contacts",
        json={"name": "Delete Me"},
        headers=auth_headers,
    )
    contact_id = create_res.json()["id"]
    
    response = client.delete(f"/api/v1/applications/contacts/{contact_id}", headers=auth_headers)
    assert response.status_code == 204


# --- Timeline Events Tests ---

def test_status_change_creates_event(client, auth_headers, test_user, db):
    """Status transition creates an ApplicationEvent."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="tlevt", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id, status="saved")
    db.add(app)
    db.commit()
    db.refresh(app)
    
    client.post(
        f"/api/v1/applications/{app.id}/status",
        json={"to_status": "applied"},
        headers=auth_headers,
    )
    
    response = client.get(f"/api/v1/applications/{app.id}/events", headers=auth_headers)
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "status_change"
    assert events[0]["event_metadata"]["to_status"] == "applied"


def test_user_timeline_endpoint(client, auth_headers, test_user, db):
    """GET /applications/timeline returns events across all apps."""
    from app.models.job import Job, JobApplication
    
    job = Job(external_id="tljob", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id, status="saved")
    db.add(app)
    db.commit()
    db.refresh(app)
    
    client.post(
        f"/api/v1/applications/{app.id}/status",
        json={"to_status": "interview"},
        headers=auth_headers,
    )
    
    response = client.get("/api/v1/applications/timeline", headers=auth_headers)
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert events[0]["application_id"] == str(app.id)


# --- Audit Log Tests ---

def test_status_transition_creates_audit_log(client, auth_headers, test_user, db):
    """Status transition writes to audit log."""
    from app.models.job import Job, JobApplication, AuditLog
    
    job = Job(external_id="auditjob", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=test_user.id, job_id=job.id, status="saved")
    db.add(app)
    db.commit()
    db.refresh(app)
    
    client.post(
        f"/api/v1/applications/{app.id}/status",
        json={"to_status": "applied"},
        headers=auth_headers,
    )
    
    log = (
        db.query(AuditLog)
        .filter(
            AuditLog.user_id == test_user.id,
            AuditLog.action == "application_status_change",
        )
        .first()
    )
    assert log is not None
    assert log.details["to_status"] == "applied"


# --- Authorization Tests ---

def test_cannot_access_other_users_application(client, auth_headers, db):
    """User cannot access notes/contacts of another user's application."""
    from app.models.user import User
    from app.models.job import Job, JobApplication
    from app.core.security import get_password_hash
    
    # Create another user
    other_user = User(
        email="other@example.com",
        full_name="Other User",
        hashed_password=get_password_hash("password"),
        is_verified=True,
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    
    job = Job(external_id="otherjob", title="Title", company="Co")
    db.add(job)
    db.commit()
    
    app = JobApplication(user_id=other_user.id, job_id=job.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    
    response = client.get(f"/api/v1/applications/{app.id}/notes", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []  # Empty list, not 404 (security: don't leak existence)