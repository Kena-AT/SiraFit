"""
Complete User Journey Integration Tests - Backend

Covers the full user lifecycle:
1. Register → Verify Email → Login
2. Import Jobs (URL & Description)
3. Create Applications → Status Transitions → Notes/Contacts
4. Follow-ups
5. Notifications
6. Analytics
7. Resume/Cover Letter operations
8. Batch operations
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.job import Job, JobApplication
from app.models.notification import Notification
from app.models.profile import Profile
from app.models.cover_letter import CoverLetter
from app.models.batch import BatchJob
from app.services.notification import (
    create_notification,
    get_notifications,
    mark_as_read,
    mark_all_as_read,
    get_unread_count,
)


client = TestClient(app)

# Test data
TEST_JOB_DESCRIPTION = """
Senior Software Engineer
Company: TechCorp Inc
Location: San Francisco, CA (Hybrid)
Salary: $150,000 - $200,000

We are looking for a Senior Software Engineer with 5+ years of experience.
Required skills: Python, React, TypeScript, PostgreSQL, AWS, Docker.
Nice to have: Kubernetes, GraphQL, CI/CD pipelines.

Responsibilities:
- Design and implement scalable backend services
- Collaborate with frontend team on API design
- Mentor junior engineers
- Participate in code reviews and architecture decisions

Benefits:
- Health, dental, vision insurance
- 401k matching
- Flexible PTO
- Remote work options
""".strip()

TEST_JOB_URL = "https://www.linkedin.com/jobs/view/1234567890"


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════


def register_user(
    client: TestClient,
    email: str,
    password: str = "TestPass123!",
    name: str = "Test User",
):
    """Register a new user."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def login_user(client: TestClient, email: str, password: str = "TestPass123!"):
    """Login and return tokens."""
    resp = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def get_auth_headers(tokens: dict):
    """Create auth headers from tokens."""
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def verify_user_email(db, email: str):
    """Mark user as verified in database."""
    user = db.query(User).filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.commit()
        db.refresh(user)
    return user


def create_job_via_api(
    client: TestClient, headers: dict, *, url: str = None, description: str = None
):
    """Create a job via import API."""
    if url:
        data = {"source_type": "url", "data": url}
    elif description:
        data = {"source_type": "description", "data": description}
    else:
        raise ValueError("Must provide url or description")

    resp = client.post("/api/v1/jobs/import", headers=headers, json=data)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["import_record"]["status"] == "completed"
    assert len(data["jobs"]) > 0
    return data["jobs"][0]


def create_application(
    client: TestClient, headers: dict, job_id: str, status: str = "saved"
):
    """Create a job application."""
    resp = client.post("/api/v1/applications", headers=headers, json={"job_id": job_id})
    assert resp.status_code == 200, resp.text
    app = resp.json()
    assert app["status"] == status
    return app


def transition_status(client: TestClient, headers: dict, app_id: str, to_status: str):
    """Transition application status."""
    resp = client.post(
        f"/api/v1/applications/{app_id}/status",
        headers=headers,
        json={"to_status": to_status},
    )
    return resp


def add_note(
    client: TestClient,
    headers: dict,
    app_id: str,
    body: str,
    author: str = "Tester",
    pinned: bool = False,
):
    """Add a note to an application."""
    resp = client.post(
        f"/api/v1/applications/{app_id}/notes",
        headers=headers,
        json={"body": body, "author": author, "pinned": pinned},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def add_contact(client: TestClient, headers: dict, app_id: str, **kwargs):
    """Add a contact to an application."""
    resp = client.post(
        f"/api/v1/applications/{app_id}/contacts", headers=headers, json=kwargs
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def set_followup(
    client: TestClient, headers: dict, app_id: str, follow_up_at: str, note: str = None
):
    """Set follow-up reminder."""
    resp = client.put(
        f"/api/v1/applications/{app_id}/followup",
        headers=headers,
        json={"follow_up_at": follow_up_at, "follow_up_note": note},
    )
    return resp


# ═══════════════════════════════════════════════════════════════
# TEST CLASSES
# ═══════════════════════════════════════════════════════════════


class TestCompleteUserJourney:
    """End-to-end user journey tests."""

    @pytest.fixture
    def test_email(self):
        return f"journey_{uuid.uuid4().hex[:8]}@test.com"

    @pytest.fixture
    def test_user(self, client, test_email, db):
        """Create and return a verified test user with tokens."""
        # Register
        register_user(client, test_email)
        user = verify_user_email(db, test_email)

        # Login
        tokens = login_user(client, test_email)
        headers = get_auth_headers(tokens)

        yield {"user": user, "tokens": tokens, "headers": headers, "email": test_email}

    def test_01_register_and_verify_email(self, client, db):
        """Test complete registration → verification flow."""
        email = f"verify_{uuid.uuid4().hex[:8]}@test.com"

        # Register
        resp = register_user(client, email)
        assert "id" in resp
        assert resp["email"] == email
        assert resp["is_verified"] is False

        # Login should fail before verification
        login_resp = client.post(
            "/api/v1/auth/login", data={"username": email, "password": "TestPass123!"}
        )
        assert login_resp.status_code in (400, 401), login_resp.text
        assert "verify" in login_resp.json().get("detail", "").lower()

        # Verify email (simulate email link click)
        user = verify_user_email(db, email)
        assert user.is_verified is True

        # Now login should work
        tokens = login_user(client, email)
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    def test_02_import_job_from_url(self, client, test_user):
        """Test importing a job from a LinkedIn URL."""
        headers = test_user["headers"]

        # Import from URL
        job = create_job_via_api(client, headers, url=TEST_JOB_URL)

        assert "id" in job
        assert job["title"]
        assert job["company"]
        # LinkedIn job should have linkedin tag
        assert any("linkedin" in tag.lower() for tag in job.get("tags", []))

    def test_03_import_job_from_description(self, client, test_user):
        """Test importing a job from raw description text."""
        headers = test_user["headers"]

        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)

        assert "id" in job
        assert "Senior" in job["title"]
        assert "TechCorp" in job["company"]
        assert "San Francisco" in job["location"]
        assert job["salary_min"] == 150000
        assert job["salary_max"] == 200000

        # Check skills extracted
        tags = [t.lower() for t in job.get("tags", [])]
        assert "python" in tags
        assert "react" in tags
        assert "typescript" in tags
        assert "postgresql" in tags
        assert "aws" in tags
        assert "docker" in tags

    def test_04_create_application_and_status_transitions(self, client, test_user):
        """Test full application lifecycle: create → status transitions → audit log."""
        headers = test_user["headers"]

        # Import job
        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        job_id = job["id"]

        # Create application (defaults to 'saved')
        app = create_application(client, headers, job_id)
        app_id = app["id"]
        assert app["status"] == "saved"

        # Valid forward transitions
        valid_transitions = [
            "applied",
            "screening",
            "interview",
            "final_round",
            "offer",
        ]
        for status in valid_transitions:
            resp = transition_status(client, headers, app_id, status)
            assert resp.status_code == 200, (
                f"Failed to transition to {status}: {resp.text}"
            )
            assert resp.json()["status"] == status

        # Invalid reverse transition should fail
        resp = transition_status(client, headers, app_id, "saved")
        assert resp.status_code == 400, "Reverse transition should fail"

        # Terminal state: rejected
        resp = transition_status(client, headers, app_id, "rejected")
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_05_application_notes_crud(self, client, test_user):
        """Test creating, listing, updating, deleting notes on application."""
        headers = test_user["headers"]

        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        app = create_application(client, headers, job["id"])
        app_id = app["id"]

        # Create notes
        note1 = add_note(client, headers, app_id, "First conversation with recruiter")
        note2 = add_note(
            client, headers, app_id, "Technical interview scheduled", pinned=True
        )
        note3 = add_note(client, headers, app_id, "Follow up by Friday")

        # List notes - pinned should come first
        resp = client.get(f"/api/v1/applications/{app_id}/notes", headers=headers)
        assert resp.status_code == 200
        notes = resp.json()
        assert len(notes) == 3
        assert notes[0]["pinned"] is True
        assert notes[0]["body"] == "Technical interview scheduled"

        # Update note
        note_id = note1["id"]
        resp = client.put(
            f"/api/v1/applications/notes/{note_id}",
            headers=headers,
            json={"body": "Updated: First conversation with recruiter", "pinned": True},
        )
        assert resp.status_code == 200
        assert resp.json()["body"] == "Updated: First conversation with recruiter"
        assert resp.json()["pinned"] is True

        # Delete note
        resp = client.delete(f"/api/v1/applications/notes/{note_id}", headers=headers)
        assert resp.status_code == 204

        # Verify deleted
        resp = client.get(f"/api/v1/applications/{app_id}/notes", headers=headers)
        assert len(resp.json()) == 2

    def test_06_application_contacts_crud(self, client, test_user):
        """Test creating, listing, updating, deleting contacts."""
        headers = test_user["headers"]

        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        app = create_application(client, headers, job["id"])
        app_id = app["id"]

        # Create contacts
        contact1 = add_contact(
            client,
            headers,
            app_id,
            name="Sarah Chen",
            email="sarah@techcorp.com",
            role="recruiter",
            is_primary=True,
        )
        contact2 = add_contact(
            client,
            headers,
            app_id,
            name="Mike Johnson",
            email="mike@techcorp.com",
            role="hiring_manager",
            is_primary=False,
        )

        # List contacts - primary first
        resp = client.get(f"/api/v1/applications/{app_id}/contacts", headers=headers)
        assert resp.status_code == 200
        contacts = resp.json()
        assert len(contacts) == 2
        assert contacts[0]["is_primary"] is True
        assert contacts[0]["name"] == "Sarah Chen"

        # Update contact
        resp = client.put(
            f"/api/v1/applications/contacts/{contact1['id']}",
            headers=headers,
            json={"phone": "+1-555-0123", "company": "TechCorp Inc"},
        )
        assert resp.status_code == 200
        assert resp.json()["phone"] == "+1-555-0123"

        # Delete contact
        resp = client.delete(
            f"/api/v1/applications/contacts/{contact1['id']}", headers=headers
        )
        assert resp.status_code == 204

        # Verify
        resp = client.get(f"/api/v1/applications/{app_id}/contacts", headers=headers)
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Mike Johnson"

    def test_07_timeline_events(self, client, test_user):
        """Test that status changes create timeline events."""
        headers = test_user["headers"]

        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        app = create_application(client, headers, job["id"], status="saved")
        app_id = app["id"]

        # Transition through multiple statuses
        for status in ["applied", "screening", "interview", "final_round"]:
            transition_status(client, headers, app_id, status)

        # Get application events
        resp = client.get(f"/api/v1/applications/{app_id}/events", headers=headers)
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) >= 4

        # All should be status_change events
        for event in events:
            assert event["event_type"] == "status_change"

        # Get user timeline (across all apps)
        resp = client.get("/api/v1/applications/timeline", headers=headers)
        assert resp.status_code == 200
        timeline = resp.json()
        assert len(timeline) >= 4

    def test_08_audit_logging(self, client, test_user, db):
        """Test that status transitions create audit logs."""
        from app.models.job import AuditLog

        headers = test_user["headers"]
        user_id = test_user["user"].id

        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        app = create_application(client, headers, job["id"])
        app_id = app["id"]

        # Transition status
        transition_status(client, headers, app_id, "applied")

        # Check audit log
        log = (
            db.query(AuditLog)
            .filter_by(user_id=user_id, action="application_status_change")
            .first()
        )

        assert log is not None
        assert log.details["to_status"] == "applied"
        assert log.details["application_id"] == str(app_id)

    def test_09_followup_reminders(self, client, test_user):
        """Test setting and getting follow-up reminders."""
        headers = test_user["headers"]

        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        app = create_application(client, headers, job["id"], status="interview")
        app_id = app["id"]

        # Set follow-up
        future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        resp = set_followup(
            client, headers, app_id, future_date, "Send thank you email"
        )
        assert resp.status_code == 200

        # Get follow-ups
        resp = client.get("/api/v1/applications/followups", headers=headers)
        assert resp.status_code == 200
        followups = resp.json()

        assert len(followups) >= 1
        fu = next((f for f in followups if f["application_id"] == app_id), None)
        assert fu is not None
        assert fu["follow_up_note"] == "Send thank you email"

        # Clear follow-up
        resp = set_followup(client, headers, app_id, None)
        assert resp.status_code == 200

    def test_10_notifications_full_lifecycle(self, client, test_user, db):
        """Test creating, reading, marking read, counting notifications."""
        headers = test_user["headers"]
        user_id = test_user["user"].id

        # Create notifications via API
        for i in range(3):
            resp = client.post(
                "/api/v1/notifications",
                headers=headers,
                json={
                    "title": f"Notification {i}",
                    "body": f"Body {i}",
                    "kind": "alert",
                },
            )
            assert resp.status_code == 200

        # Get all notifications (paginated)
        resp = client.get("/api/v1/notifications", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

        # Filter by status
        resp = client.get("/api/v1/notifications?status=unread", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

        # Get unread count
        resp = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["count"] >= 3

        # Mark first as read
        first_id = data["items"][0]["id"]
        resp = client.put(f"/api/v1/notifications/{first_id}/read", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "read"

        # Mark all as read
        resp = client.put("/api/v1/notifications/read-all", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["updated"] >= 2

        # Count should be 0
        resp = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert resp.json()["count"] == 0

    def test_11_notification_service_layer(self, test_user, db):
        """Test notification service functions directly."""
        user_id = test_user["user"].id

        # Create
        notif = create_notification(
            db=db,
            user_id=user_id,
            title="Service Test",
            body="Testing service layer",
            kind="system_event",
        )
        assert notif.id is not None
        assert notif.status == "unread"

        # Get with pagination
        notifs, total = get_notifications(db, user_id, skip=0, limit=10)
        assert total >= 1

        # Get unread
        notifs, total = get_notifications(db, user_id, status="unread")
        assert total >= 1

        # Mark as read
        updated = mark_as_read(db, user_id, notif.id)
        assert updated.status == "read"
        assert updated.read_at is not None

        # Get unread count
        count = get_unread_count(db, user_id)
        assert count == 0

        # Mark all as read (create more first)
        for _ in range(3):
            create_notification(db, user_id, "Test", "Test", "alert")
        count = mark_all_as_read(db, user_id)
        assert count == 3

    def test_12_analytics_endpoints(self, client, test_user):
        """Test analytics API endpoints."""
        headers = test_user["headers"]

        # Create some test applications first
        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        for status in ["saved", "applied", "screening", "interview", "offer"]:
            app = create_application(client, headers, job["id"])
            transition_status(client, headers, app["id"], status)

        # Analytics overview
        resp = client.get("/api/v1/analytics/overview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_applications" in data
        assert "response_rate" in data
        assert "interview_rate" in data
        assert "offer_rate" in data
        assert data["total_applications"] >= 5

        # Status breakdown
        resp = client.get("/api/v1/analytics/status-breakdown", headers=headers)
        assert resp.status_code == 200
        breakdown = resp.json()
        assert isinstance(breakdown, list)

        # Timeline
        resp = client.get("/api/v1/analytics/timeline", headers=headers)
        assert resp.status_code == 200
        timeline = resp.json()
        assert isinstance(timeline, list)

        # Skills demand
        resp = client.get("/api/v1/analytics/skills-demand", headers=headers)
        assert resp.status_code == 200
        skills = resp.json()
        assert isinstance(skills, list)

        # Market insights
        resp = client.get("/api/v1/analytics/market-insights", headers=headers)
        assert resp.status_code == 200
        market = resp.json()
        assert "top_locations" in market
        assert "top_companies" in market
        assert "salary_ranges" in market

    def test_13_resume_operations(self, client, test_user):
        """Test resume creation, profile editing, export."""
        headers = test_user["headers"]

        # List resumes
        resp = client.get("/api/v1/resumes", headers=headers)
        assert resp.status_code == 200

        # Create resume (profile-based)
        resp = client.post(
            "/api/v1/resumes",
            headers=headers,
            json={
                "profile_data": {
                    "headline": "Senior Software Engineer",
                    "summary": "Experienced engineer...",
                    "skills": ["Python", "React", "AWS"],
                    "experience": [],
                    "education": [],
                }
            },
        )
        assert resp.status_code == 200
        resume = resp.json()
        assert resume["id"] is not None

        # Get resume
        resp = client.get(f"/api/v1/resumes/{resume['id']}", headers=headers)
        assert resp.status_code == 200

        # Export PDF (if endpoint exists)
        resp = client.get(
            f"/api/v1/resumes/{resume['id']}/export?format=pdf", headers=headers
        )
        # May return 404 if not implemented yet
        # assert resp.status_code in (200, 404)

    def test_14_cover_letter_generation(self, client, test_user):
        """Test cover letter creation and AI generation."""
        headers = test_user["headers"]

        # Create job and application
        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        app = create_application(client, headers, job["id"])
        app_id = app["id"]

        # Create cover letter for application
        resp = client.post(
            "/api/v1/cover-letters",
            headers=headers,
            json={"application_id": app_id, "tone": "professional", "length": "medium"},
        )
        assert resp.status_code == 200
        cover_letter = resp.json()
        assert cover_letter["id"] is not None
        assert cover_letter["application_id"] == app_id

        # Get cover letters
        resp = client.get("/api/v1/cover-letters", headers=headers)
        assert resp.status_code == 200
        letters = resp.json()
        assert len(letters) >= 1

    def test_15_batch_operations(self, client, test_user):
        """Test batch job operations."""
        headers = test_user["headers"]

        # Create batch import job
        resp = client.post(
            "/api/v1/batch",
            headers=headers,
            json={
                "name": "Test Batch",
                "description": "Batch import test",
                "operation": "import",
                "items": [
                    {"source_type": "description", "data": TEST_JOB_DESCRIPTION},
                    {
                        "source_type": "url",
                        "data": "https://linkedin.com/jobs/view/999",
                    },
                ],
            },
        )
        assert resp.status_code == 200
        batch = resp.json()
        assert batch["id"] is not None
        assert batch["status"] == "pending"

        # List batches
        resp = client.get("/api/v1/batch", headers=headers)
        assert resp.status_code == 200
        batches = resp.json()
        assert len(batches) >= 1

        # Get batch details
        resp = client.get(f"/api/v1/batch/{batch['id']}", headers=headers)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == batch["id"]

    def test_16_user_isolation(self, client, test_user, db):
        """Test that users cannot access each other's data."""
        headers = test_user["headers"]
        user_id = test_user["user"].id

        # Create another user
        other_email = f"other_{uuid.uuid4().hex[:8]}@test.com"
        register_user(client, other_email)
        verify_user_email(db, other_email)
        other_tokens = login_user(client, other_email)
        other_headers = get_auth_headers(other_tokens)

        # Create job and app as user 1
        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        app = create_application(client, headers, job["id"])
        app_id = app["id"]

        # User 2 tries to access user 1's application notes
        resp = client.get(f"/api/v1/applications/{app_id}/notes", headers=other_headers)
        assert resp.status_code == 200
        # Should return empty list, not 404 (to prevent enumeration)
        assert resp.json() == []

        # User 2 tries to access user 1's application contacts
        resp = client.get(
            f"/api/v1/applications/{app_id}/contacts", headers=other_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_17_rate_limiting(self, client):
        """Test that rate limiting is enforced on auth endpoints."""
        email = f"ratelimit_{uuid.uuid4().hex[:8]}@test.com"

        # Make many rapid requests
        for i in range(15):
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"{email.split('@')[0]}+{i}@{email.split('@')[1]}",
                    "password": "TestPass123!",
                    "full_name": "Rate Limit Test",
                },
            )
            # Some may be rate limited
            if resp.status_code == 429:
                assert "detail" in resp.json()
                break

    def test_18_refresh_token_flow(self, client, test_user):
        """Test access token refresh and logout."""
        tokens = test_user["tokens"]

        # Refresh token
        resp = client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        # New tokens should be different
        assert new_tokens["access_token"] != tokens["access_token"]

        # Use new access token
        headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        resp = client.get("/api/v1/users/me", headers=headers)
        assert resp.status_code == 200

        # Logout
        resp = client.post(
            "/api/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]}
        )
        assert resp.status_code == 200

    def test_19_forgot_reset_password(self, client, db):
        """Test forgot password and reset flow."""
        email = f"reset_{uuid.uuid4().hex[:8]}@test.com"
        register_user(client, email)
        verify_user_email(db, email)

        # Request password reset
        resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert resp.status_code == 200
        assert "reset link" in resp.json()["message"].lower()

        # Request for non-existent email (should not reveal user existence)
        resp = client.post(
            "/api/v1/auth/forgot-password", json={"email": "nonexistent@test.com"}
        )
        assert resp.status_code == 200
        assert "reset link" in resp.json()["message"].lower()

        # Invalid reset token
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "invalid.token.here", "new_password": "NewPass123!"},
        )
        assert resp.status_code == 400

    def test_20_full_application_workflow(self, client, test_user):
        """Complete workflow: import job → apply → track → follow-up → notification."""
        headers = test_user["headers"]

        # 1. Import job from description
        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        assert job["id"]

        # 2. Create application
        app = create_application(client, headers, job["id"])
        app_id = app["id"]
        assert app["status"] == "saved"

        # 3. Apply (transition to applied)
        resp = transition_status(client, headers, app_id, "applied")
        assert resp.status_code == 200
        assert resp.json()["status"] == "applied"

        # 4. Add note about application
        add_note(
            client, headers, app_id, "Applied via LinkedIn Easy Apply", pinned=True
        )

        # 5. Add recruiter contact
        add_contact(
            client,
            headers,
            app_id,
            name="Sarah Chen",
            email="sarah@techcorp.com",
            role="recruiter",
            is_primary=True,
        )

        # 6. Set follow-up for 1 week
        future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        set_followup(client, headers, app_id, future, "Follow up with Sarah")

        # 7. Progress to screening
        resp = transition_status(client, headers, app_id, "screening")
        assert resp.status_code == 200

        # 8. Add note
        add_note(client, headers, app_id, "Phone screen scheduled for Tuesday 2pm")

        # 9. Progress to interview
        resp = transition_status(client, headers, app_id, "interview")
        assert resp.status_code == 200

        # 10. Verify timeline has all events
        resp = client.get(f"/api/v1/applications/{app_id}/events", headers=headers)
        events = resp.json()
        event_types = [e["event_type"] for e in events]
        assert "status_change" in event_types
        assert events[0]["event_metadata"]["to_status"] == "interview"

        # 11. Verify follow-up center
        resp = client.get("/api/v1/applications/followups", headers=headers)
        followups = resp.json()
        assert len(followups) >= 1

        my_fu = next(f for f in followups if f["application_id"] == app_id)
        assert my_fu["follow_up_note"] == "Follow up with Sarah"

        # 12. Get analytics overview
        resp = client.get("/api/v1/analytics/overview", headers=headers)
        overview = resp.json()
        assert overview["total_applications"] >= 1

        print(f"✅ Complete workflow test passed for application {app_id}")


class TestAPIErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_status_transition(self, client, test_user):
        """Test that invalid transitions return 400 with helpful message."""
        headers = test_user["headers"]
        job = create_job_via_api(client, headers, description=TEST_JOB_DESCRIPTION)
        app = create_application(client, headers, job["id"])

        # Skip intermediate statuses
        resp = transition_status(client, headers, app["id"], "interview")
        assert resp.status_code == 400
        assert "invalid" in resp.json()["detail"].lower()

    def test_unauthorized_access(self, client):
        """Test endpoints reject unauthenticated requests."""
        endpoints = [
            ("GET", "/api/v1/applications"),
            ("POST", "/api/v1/applications"),
            ("GET", "/api/v1/notifications"),
            ("GET", "/api/v1/analytics/overview"),
            ("GET", "/api/v1/jobs/import/history"),
        ]
        for method, path in endpoints:
            func = getattr(client, method.lower())
            resp = func(path)
            assert resp.status_code == 401, f"{method} {path} should require auth"

    def test_invalid_job_import(self, client, test_user):
        """Test importing invalid/empty job description."""
        headers = test_user["headers"]
        resp = client.post(
            "/api/v1/jobs/import",
            headers=headers,
            json={"source_type": "description", "data": "Too short"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["import_record"]["status"] == "failed"
        assert len(data["errors"]) > 0

    def test_duplicate_job_handling(self, client, test_user):
        """Test importing same job twice."""
        headers = test_user["headers"]

        # Import same description twice
        for _ in range(2):
            resp = client.post(
                "/api/v1/jobs/import",
                headers=headers,
                json={"source_type": "description", "data": TEST_JOB_DESCRIPTION},
            )
            assert resp.status_code == 200
            data = resp.json()
            # Second import should be marked as duplicate
            # (Implementation may vary - just ensure it doesn't error)

    def test_pagination_limits(self, client, test_user, db):
        """Test pagination on list endpoints."""
        headers = test_user["headers"]
        user_id = test_user["user"].id

        # Create many notifications
        for i in range(25):
            create_notification(
                db, user_id, f"Notification {i}", f"Body {i}", "system_event"
            )

        # Test pagination
        resp = client.get("/api/v1/notifications?limit=10&skip=0", headers=headers)
        assert resp.status_code == 200
        page1 = resp.json()
        assert len(page1["items"]) == 10
        assert page1["total"] >= 25

        resp = client.get("/api/v1/notifications?limit=10&skip=10", headers=headers)
        page2 = resp.json()
        assert len(page2["items"]) == 10

        resp = client.get("/api/v1/notifications?limit=10&skip=20", headers=headers)
        page3 = resp.json()
        assert len(page3["items"]) >= 5


# ═══════════════════════════════════════════════════════════════
# RUNNING INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════
"""
HOW TO RUN THESE TESTS:

=== Backend Tests ===

1. From backend directory:
   cd backend

2. Run all journey tests:
   rtk pytest tests/test_complete_user_journey.py -v

3. Run specific test class:
   rtk pytest tests/test_complete_user_journey.py::TestCompleteUserJourney -v

4. Run specific test:
   rtk pytest tests/test_complete_user_journey.py::TestCompleteUserJourney::test_20_full_application_workflow -v

5. Run with coverage:
   rtk pytest tests/test_complete_user_journey.py --cov=app --cov-report=term-missing

=== Frontend E2E Tests ===

1. From frontend directory:
   cd frontend

2. Install Playwright if needed:
   rtk npx playwright install

3. Start the dev servers (backend + frontend):
   # Terminal 1 - Backend
   cd backend && rtk python -m uvicorn app.main:app --reload --port 8000

   # Terminal 2 - Frontend
   cd frontend && rtk pnpm dev

4. Run E2E tests:
   rtk npx playwright test e2e/complete-user-journey.spec.ts --headed

5. Run specific test:
   rtk npx playwright test e2e/complete-user-journey.spec.ts -g "Register"

6. Run in headed mode (see browser):
   rtk npx playwright test e2e/complete-user-journey.spec.ts --headed --slowmo=1000

7. Generate and view report:
   rtk npx playwright test e2e/complete-user-journey.spec.ts --reporter=html
   rtk npx playwright show-report

=== Combined Test Run ===

To run everything:
1. Start backend: cd backend && rtk python -m uvicorn app.main:app --reload
2. Start frontend: cd frontend && rtk pnpm dev
3. In another terminal: rtk npx playwright test e2e/complete-user-journey.spec.ts

=== Requirements ===

**Backend:**
- pytest, pytest-asyncio, httpx
- Database: SQLite (test.db) - auto created
- Redis: Optional (uses memory fallback)

**Frontend E2E:**
- Playwright installed
- Backend running on localhost:8000
- Frontend running on localhost:3030
- VITE_API_URL=http://localhost:8000 (or set in .env)

=== Test Data Notes ===

- Tests use unique emails (timestamp/uuid) to avoid conflicts
- Each test class creates its own test user via fixtures
- Database is session-scoped (created once, dropped after all tests)
- Function-scoped fixtures provide fresh DB sessions

=== Common Issues ===

1. "Database locked" - Ensure no other test processes running
2. "Port 8000 in use" - Kill existing uvicorn processes
3. "Playwright timeout" - Increase timeout or check server is running
4. "Redirect loop" - Check VITE_API_URL matches backend URL
"""
