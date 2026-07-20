# ========================================
# FROM FILE: test_application_tracking.py
# ========================================

"""
QA tests for Sprint 9 — Application tracking (status machine, timeline, notes, contacts).
"""

import uuid


# --- Status Machine Tests ---

VALID_STATUSES = [
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


def test_status_machine_valid_transitions():
    """Verify the status validation logic works correctly."""
    from app.services.application import validate_transition

    # Valid forwards transitions
    assert validate_transition("saved", "applied") is True
    assert validate_transition("applied", "screening") is True
    assert validate_transition("screening", "interview") is True
    assert validate_transition("interview", "final_round") is True
    assert validate_transition("final_round", "offer") is True

    # Terminal states
    assert validate_transition("rejected", "archived") is True
    assert validate_transition("offer", "rejected") is True

    # Invalid reverse transitions
    assert validate_transition("interview", "saved") is False
    assert validate_transition("applied", "saved") is False
    assert validate_transition("screening", "applied") is False

    # Invalid transitions to unknown status
    assert validate_transition("saved", "unknown") is False


def test_create_application_creates_client_default_status(client, auth_headers, db):
    """A new application defaults to 'saved' status."""
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
    assert response.status_code == 200
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
        json={
            "body": "Great conversation with recruiter!",
            "author": "Me",
            "pinned": True,
        },
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

    client.post(
        f"/api/v1/applications/{app.id}/notes",
        json={"body": "Second note", "pinned": False},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/applications/{app.id}/notes",
        json={"body": "Pinned note", "pinned": True},
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
        json={"body": "Updated body", "pinned": True},
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

    response = client.delete(
        f"/api/v1/applications/notes/{note_id}", headers=auth_headers
    )
    assert response.status_code == 204

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

    response = client.get(
        f"/api/v1/applications/{app.id}/contacts", headers=auth_headers
    )
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

    response = client.delete(
        f"/api/v1/applications/contacts/{contact_id}", headers=auth_headers
    )
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
    assert len(events) >= 1
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
        json={"to_status": "applied"},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/applications/{app.id}/status",
        json={"to_status": "screening"},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/applications/{app.id}/status",
        json={"to_status": "interview"},
        headers=auth_headers,
    )

    response = client.get("/api/v1/applications/timeline", headers=auth_headers)
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 3
    assert events[0]["event_type"] == "status_change"
    assert events[0]["event_metadata"]["to_status"] == "interview"


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


def test_cannot_access_other_users_notes(client, auth_headers, db):
    """User gets empty notes list (not 404) for another user's application."""
    from app.models.user import User
    from app.models.job import Job, JobApplication
    from app.core.security import get_password_hash

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
    assert response.json() == []


# ========================================
# FROM FILE: test_resume_generation.py
# ========================================

"""Tests for resume generation service."""

import pytest
import json

from app.services.resume_generation import (
    _parse_ai_response,
    _calculate_ats_score,
    validate_resume_json,
    render_resume_html,
    _serialize_profile,
    _serialize_job,
)


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_resume_data():
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "location": "New York, NY",
        "linkedin": "https://linkedin.com/in/johndoe",
        "github": "https://github.com/johndoe",
        "website": None,
        "summary": "Experienced software engineer specializing in distributed systems.",
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Tech Corp",
                "location": "Remote",
                "period": "2020 – Present",
                "bullets": [
                    "Led team of 5 engineers to deliver microservices platform",
                    "Reduced latency by 40% through optimization",
                ],
            }
        ],
        "projects": [
            {
                "name": "OpenSourceProject",
                "description": "A distributed cache system in Rust",
                "url": "https://github.com/johndoe/cache",
            }
        ],
        "skills": ["Python", "Rust", "Kubernetes", "PostgreSQL", "AWS"],
        "education": [
            {
                "institution": "MIT",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "period": "2016 – 2020",
            }
        ],
    }


@pytest.fixture
def sample_job():
    from app.models.job import Job

    return Job(
        id=uuid.uuid4(),
        external_id="job-123",
        title="Senior Software Engineer",
        company="Example Corp",
        location="Remote",
        description="Looking for experienced engineer with Python, Kubernetes, and distributed systems experience.",
        salary_min=150000,
        salary_max=200000,
        currency="USD",
        tags=["python", "kubernetes", "distributed-systems"],
        source="linkedin",
    )


# ---------------------------------------------------------------------------
# Parsing tests
# ---------------------------------------------------------------------------


class TestParseAIResponse:
    def test_valid_json_parsing(self, sample_resume_data):
        """Test parsing a valid JSON response."""
        json_text = json.dumps(sample_resume_data)
        result = _parse_ai_response(json_text)

        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert len(result.experience) == 1
        assert result.experience[0].title == "Senior Engineer"

    def test_json_with_markdown_fences(self, sample_resume_data):
        """Test parsing JSON wrapped in markdown code fences."""
        json_text = f"```json\n{json.dumps(sample_resume_data)}\n```"
        result = _parse_ai_response(json_text)
        assert result.name == "John Doe"

    def test_empty_name_raises_error(self):
        """Test that missing name raises validation error."""
        data = {"email": "test@example.com"}
        with pytest.raises(Exception):
            _parse_ai_response(json.dumps(data))


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidateResumeJson:
    def test_valid_resume(self, sample_resume_data, sample_job):
        """Test that a complete resume passes validation."""
        is_valid, issues = validate_resume_json(sample_resume_data, sample_job)
        assert is_valid
        assert len(issues) == 0

    def test_missing_required_fields(self, sample_resume_data, sample_job):
        """Test that missing required fields are caught."""
        data = {k: v for k, v in sample_resume_data.items() if k != "name"}
        is_valid, issues = validate_resume_json(data, sample_job)
        assert not is_valid
        assert any("Missing required field: name" in str(i) for i in issues)

    def test_experience_without_bullets(self, sample_resume_data, sample_job):
        """Test that experience entries without bullets are flagged."""
        sample_resume_data["experience"] = [
            {
                "title": "Engineer",
                "company": "Corp",
                "location": None,
                "period": "2020 – 2021",
                "bullets": [],
            }
        ]
        is_valid, issues = validate_resume_json(sample_resume_data, sample_job)
        # Should still be valid but will have lower ATS score
        assert is_valid  # Empty bullets doesn't fail validation, just lowers score

    def test_too_many_skills(self, sample_resume_data, sample_job):
        """Test that more than 30 skills are flagged."""
        sample_resume_data["skills"] = [f"skill-{i}" for i in range(35)]
        is_valid, issues = validate_resume_json(sample_resume_data, sample_job)
        assert not is_valid
        assert any("Too many skills" in str(i) for i in issues)

    def test_no_skills(self, sample_resume_data, sample_job):
        """Test that no skills fails validation."""
        sample_resume_data["skills"] = []
        is_valid, issues = validate_resume_json(sample_resume_data, sample_job)
        assert not is_valid
        assert any("No skills listed" in str(i) for i in issues)


# ---------------------------------------------------------------------------
# ATS Score tests
# ---------------------------------------------------------------------------


class TestCalculateATSScore:
    def test_perfect_score(self, sample_resume_data, sample_job):
        """Test that a complete resume gets a high ATS score."""
        score = _calculate_ats_score(sample_resume_data, sample_job)
        assert score >= 80  # Should score high with all fields present

    def test_missing_summary_lowers_score(self, sample_resume_data, sample_job):
        """Test that missing summary lowers the score."""
        sample_resume_data["summary"] = ""
        score = _calculate_ats_score(sample_resume_data, sample_job)
        assert score < 100  # Missing summary should reduce score

    def test_empty_resume(self, sample_job):
        """Test that an empty resume gets a low score."""
        score = _calculate_ats_score({}, sample_job)
        assert score == 0

    def test_keyword_match(self, sample_resume_data, sample_job):
        """Test that keyword matching affects score."""
        score = _calculate_ats_score(sample_resume_data, sample_job)
        # Should get some points for keyword matches
        assert score >= 40  # At minimum for having skills and education


# ---------------------------------------------------------------------------
# Template engine tests
# ---------------------------------------------------------------------------


class TestRenderResumeHtml:
    def test_minimal_template(self, sample_resume_data):
        """Test that minimal template produces valid HTML."""
        html = render_resume_html(sample_resume_data, "minimal")
        assert "<html>" in html
        assert "John Doe" in html
        assert "Tech Corp" in html
        assert "</html>" in html

    def test_technical_template(self, sample_resume_data):
        """Test that technical template produces valid HTML."""
        html = render_resume_html(sample_resume_data, "technical")
        assert "<html>" in html
        assert "Technical Skills" in html  # Technical template emphasizes skills
        assert "</html>" in html

    def test_unknown_template_fallback(self, sample_resume_data):
        """Test that unknown template falls back to minimal."""
        html = render_resume_html(sample_resume_data, "nonexistent")
        assert "<html>" in html  # Should still produce valid HTML

    def test_html_escaping(self):
        """Test that special characters are properly escaped in HTML."""
        data = {
            "name": "John <script>alert('xss')</script>",
            "email": "john@example.com",
            "phone": None,
            "location": None,
            "linkedin": None,
            "github": None,
            "website": None,
            "summary": "Test <b>summary</b>",
            "experience": [],
            "projects": [],
            "skills": [],
            "education": [],
        }
        html = render_resume_html(data, "minimal")
        # Raw script tag should be escaped
        assert "&lt;script&gt;" in html
        assert "<script>" not in html
        # Summary content should also be escaped
        assert "&lt;b&gt;summary&lt;/b&gt;" in html
        assert "<b>summary</b>" not in html

    def test_modern_template(self, sample_resume_data):
        """Test that modern template produces valid HTML with gradient header."""
        html = render_resume_html(sample_resume_data, "modern")
        assert "<html>" in html
        assert "John Doe" in html
        assert "linear-gradient" in html
        assert "</html>" in html

    def test_corporate_template(self, sample_resume_data):
        """Test that corporate template produces valid HTML with serif font."""
        html = render_resume_html(sample_resume_data, "corporate")
        assert "<html>" in html
        assert "Times New Roman" in html
        assert "Professional Summary" in html
        assert "</html>" in html

    def test_compact_template(self, sample_resume_data):
        """Test that compact template produces valid HTML with dense layout."""
        html = render_resume_html(sample_resume_data, "compact")
        assert "<html>" in html
        assert "John Doe" in html
        assert "font-size:12px" in html or "font-size:11px" in html
        assert "</html>" in html


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------


class TestSerializeProfile:
    def test_profile_with_all_fields(self):
        """Test serializing a profile with all fields."""
        from app.models.profile import Profile

        profile = Profile(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            headline="Senior Engineer",
            summary="Experienced developer",
            email="john@example.com",
            phone="123-456-7890",
            location="NYC",
            website="https://johndoe.com",
            linkedin="https://linkedin.com/in/johndoe",
            github="https://github.com/johndoe",
        )
        text = _serialize_profile(profile)
        assert "John Doe" in text
        assert "Senior Engineer" in text
        assert "john@example.com" in text
        assert "NYC" in text

    def test_profile_with_experiences(self):
        """Test serializing a profile with experiences."""
        from app.models.profile import Profile, Experience

        profile = Profile(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            first_name="Jane",
            last_name="Smith",
        )
        profile.experiences = [
            Experience(
                id=uuid.uuid4(),
                profile_id=profile.id,
                title="Engineer",
                company="Corp",
                location="Remote",
                description="Built things",
            )
        ]
        text = _serialize_profile(profile)
        assert "Jane Smith" in text
        assert "Corp" in text
        assert "Built things" in text


class TestSerializeJob:
    def test_job_with_all_fields(self):
        """Test serializing a job with all fields."""
        from app.models.job import Job

        job = Job(
            id=uuid.uuid4(),
            external_id="ext-123",
            title="Software Engineer",
            company="Tech Co",
            location="Remote",
            description="Build software using Python and Kubernetes",
            salary_min=100000,
            salary_max=150000,
            currency="USD",
            tags=["python", "kubernetes"],
            source="linkedin",
        )
        text = _serialize_job(job)
        assert "Software Engineer" in text
        assert "Tech Co" in text
        assert "python" in text
        assert "kubernetes" in text

    def test_job_without_description(self):
        """Test serializing a job without description."""
        from app.models.job import Job

        job = Job(
            id=uuid.uuid4(),
            external_id="ext-456",
            title="Data Scientist",
            company="Data Corp",
            source="indeed",
        )
        text = _serialize_job(job)
        assert "Data Scientist" in text
        assert "Data Corp" in text


# ========================================
# FROM FILE: test_resume_export.py
# ========================================

"""Tests for resume export service (HTML, DOCX, PDF)."""

from io import BytesIO

from app.models.job import ResumeVersion


def make_version(
    content_dict: dict, template: str = "minimal", version_number: int = 1
) -> ResumeVersion:
    """Helper to create a ResumeVersion for testing."""
    v = ResumeVersion()
    v.id = uuid.uuid4()
    v.resume_id = uuid.uuid4()
    v.version_number = version_number
    v.content = json.dumps(content_dict)
    v.template = template
    v.status = "completed"
    v.score = 80
    return v


MINIMAL_DATA = {
    "name": "Kena Ararso",
    "email": "kenaararso4@gmail.com",
    "phone": "+251911620012",
    "location": "Addis Ababa, Ethiopia",
    "linkedin": "www.linkedin.com/in/kenaararso-094939258",
    "github": "https://github.com/Kena-AT",
    "website": None,
    "summary": "Software engineering student focused on backend systems and web application development.",
    "experience": [
        {
            "title": "Software Engineering Intern",
            "company": "Berenda Technologies",
            "location": "Addis Ababa, Ethiopia",
            "period": "Feb 2026 – Present",
            "bullets": [
                "Contributed to development of MesaelGC construction company website",
                "Built features for Shegiye, a print-on-demand platform",
                "Collaborated with team to build and maintain web application features",
            ],
        },
        {
            "title": "Software Engineering Intern",
            "company": "Adwa Dynamics",
            "location": "Addis Ababa, Ethiopia",
            "period": "Jun 2024 – Sep 2024",
            "bullets": [
                "Developed and maintained React web application features",
                "Built cross-platform Flutter mobile interfaces",
                "Implemented backend services with Node.js",
            ],
        },
    ],
    "projects": [
        {
            "name": "KiloEats",
            "description": "Campus food delivery platform connecting students, restaurants, and riders.",
            "url": None,
        },
        {
            "name": "Micron",
            "description": "Cross-platform CLI tool in Go for build artifact analysis and cleanup.",
            "url": None,
        },
    ],
    "skills": [
        "Python",
        "JavaScript",
        "TypeScript",
        "Go",
        "FastAPI",
        "React",
        "PostgreSQL",
        "Docker",
    ],
    "education": [
        {
            "institution": "Addis Ababa University",
            "degree": "Bachelor of Science",
            "field_of_study": "Software Engineering",
            "period": "2023 – Expected Jun 2027",
        }
    ],
}


class TestExportResumeHtml:
    """Tests for HTML export."""

    def test_html_export_minimal_template(self):
        from app.services.resume_export import export_resume_html

        version = make_version(MINIMAL_DATA, "minimal")
        html = export_resume_html(version)

        assert "<html>" in html
        assert "Kena Ararso" in html
        assert "kenaararso4@gmail.com" in html
        assert "Berenda Technologies" in html
        assert "KiloEats" in html
        assert "Python" in html

    def test_html_export_all_templates(self):
        from app.services.resume_export import export_resume_html

        for tmpl in ("minimal", "technical", "modern", "corporate", "compact"):
            version = make_version(MINIMAL_DATA, tmpl)
            html = export_resume_html(version)
            assert "<html>" in html, f"Template {tmpl} produced invalid HTML"
            assert "Kena Ararso" in html, f"Name missing in template {tmpl}"

    def test_html_export_empty_content(self):
        from app.services.resume_export import export_resume_html

        version = make_version({}, "minimal")
        html = export_resume_html(version)

        assert "<html>" in html

    def test_html_export_xss_escaping(self):
        from app.services.resume_export import export_resume_html

        data = {
            **MINIMAL_DATA,
            "name": "John <script>alert('xss')</script>",
            "summary": "<img src=x onerror=alert(1)>",
        }
        version = make_version(data, "minimal")
        html = export_resume_html(version)

        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_html_export_is_string(self):
        from app.services.resume_export import export_resume_html

        version = make_version(MINIMAL_DATA)
        result = export_resume_html(version)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_html_export_unknown_template_fallback(self):
        from app.services.resume_export import export_resume_html

        version = make_version(MINIMAL_DATA, "nonexistent_template")
        html = export_resume_html(version)

        # Should fall back gracefully
        assert "<html>" in html

    def test_html_export_none_template_fallback(self):
        from app.services.resume_export import export_resume_html

        version = make_version(MINIMAL_DATA)
        version.template = None
        html = export_resume_html(version)

        assert "<html>" in html

    def test_html_export_invalid_json_content(self):
        from app.services.resume_export import export_resume_html

        version = make_version({})
        version.content = "not valid json {"

        # Should not raise, should handle gracefully
        html = export_resume_html(version)
        assert isinstance(html, str)


class TestExportResumePdf:
    """Tests for PDF export."""

    def test_pdf_export_returns_bytesio(self):
        from app.services.resume_export import export_resume_pdf

        version = make_version(MINIMAL_DATA)
        result = export_resume_pdf(version)

        assert isinstance(result, BytesIO)
        content = result.read()
        assert content.startswith(b"%PDF")
        assert len(content) > 500

    def test_pdf_export_positioned_at_start(self):
        from app.services.resume_export import export_resume_pdf

        version = make_version(MINIMAL_DATA)
        result = export_resume_pdf(version)

        assert result.tell() == 0

    def test_pdf_export_all_templates(self):
        from app.services.resume_export import export_resume_pdf

        for tmpl in ("minimal", "technical", "modern", "corporate", "compact"):
            version = make_version(MINIMAL_DATA, tmpl)
            result = export_resume_pdf(version)
            content = result.read()
            assert content.startswith(b"%PDF"), f"Template {tmpl} failed to produce PDF"

    def test_pdf_export_empty_content(self):
        from app.services.resume_export import export_resume_pdf

        version = make_version({})
        result = export_resume_pdf(version)
        content = result.read()

        # Should still produce a valid PDF even with empty data
        assert content.startswith(b"%PDF")


class TestExportResumeDocx:
    """Tests for DOCX export."""

    def test_docx_export_returns_bytesio(self):
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0

    def test_docx_export_positioned_at_start(self):
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        assert result.tell() == 0

    def test_docx_export_valid_zipfile(self):
        """DOCX files are ZIP archives — verify structure."""
        import zipfile
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        with zipfile.ZipFile(result) as z:
            names = z.namelist()
            assert "word/document.xml" in names

    def test_docx_export_contains_name(self):
        """Check that name appears somewhere in the docx XML."""
        import zipfile
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        with zipfile.ZipFile(result) as z:
            doc_xml = z.read("word/document.xml").decode("utf-8")
            assert "Kena Ararso" in doc_xml

    def test_docx_export_contains_experience(self):
        """Check that experience data is present in docx."""
        import zipfile
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        with zipfile.ZipFile(result) as z:
            doc_xml = z.read("word/document.xml").decode("utf-8")
            assert "Berenda Technologies" in doc_xml

    def test_docx_export_empty_content(self):
        """Empty content should produce a valid DOCX."""
        import zipfile
        from app.services.resume_export import export_resume_docx

        version = make_version({})
        result = export_resume_docx(version)

        with zipfile.ZipFile(result) as z:
            assert "word/document.xml" in z.namelist()


# ========================================
# FROM FILE: test_pdf_rendering.py
# ========================================

"""Tests for PDF rendering service."""


from app.services.pdf_rendering import render_html_to_pdf_bytes, render_html_to_pdf


class TestPdfRendering:
    """Tests for HTML-to-PDF conversion."""

    def test_simple_html_to_pdf(self):
        """Test converting basic HTML to PDF."""
        html = "<html><body><p>Hello World</p></body></html>"
        result = render_html_to_pdf_bytes(html)

        assert isinstance(result, BytesIO)
        assert result.tell() == 0  # Stream positioned at start
        content = result.read()
        assert len(content) > 0
        assert content.startswith(b"%PDF")  # PDF magic bytes

    def test_styled_html_to_pdf(self):
        """Test converting styled HTML to PDF."""
        html = """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; font-size: 24px; }
        p { line-height: 1.6; }
    </style>
</head>
<body>
    <h1>Test Document</h1>
    <p>This is a test paragraph with some <strong>bold text</strong> and <em>italic text</em>.</p>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)

        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_empty_html(self):
        """Test that empty HTML still produces a valid PDF."""
        html = "<html><body></body></html>"
        result = render_html_to_pdf_bytes(html)

        content = result.read()
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_html_with_special_characters(self):
        """Test HTML with special characters renders correctly."""
        html = """<html>
<body>
    <p>Special characters: &lt; &gt; &amp; &quot;</p>
    <p>Unicode: ñ é ü © ™</p>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)

        content = result.read()
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_multi_page_html(self):
        """Test HTML that should span multiple pages."""
        paragraphs = "\n".join(
            [
                f"<p>Paragraph {i} with some content to fill space.</p>"
                for i in range(100)
            ]
        )
        html = f"<html><body>{paragraphs}</body></html>"

        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")
        # Multi-page PDFs are significantly larger
        assert len(content) > 1000

    def test_render_html_to_pdf_bytes_returns_bytes(self):
        """Test that the bytes variant returns raw bytes."""
        html = "<html><body><h1>Test</h1></body></html>"
        result = render_html_to_pdf(html)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result.startswith(b"%PDF")

    def test_html_with_lists(self):
        """Test HTML with ordered and unordered lists."""
        html = """<html>
<body>
    <h2>Unordered List</h2>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
    <h2>Ordered List</h2>
    <ol>
        <li>First</li>
        <li>Second</li>
        <li>Third</li>
    </ol>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_html_with_table(self):
        """Test HTML with a simple table."""
        html = """<html>
<body>
    <table border="1">
        <tr>
            <th>Name</th>
            <th>Role</th>
        </tr>
        <tr>
            <td>John Doe</td>
            <td>Engineer</td>
        </tr>
        <tr>
            <td>Jane Smith</td>
            <td>Designer</td>
        </tr>
    </table>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_html_with_inline_styles(self):
        """Test HTML with inline styles."""
        html = """<html>
<body>
    <p style="color: red; font-size: 16px;">Red paragraph</p>
    <div style="background-color: #f0f0f0; padding: 10px;">
        <span style="font-weight: bold;">Bold in div</span>
    </div>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_malformed_html(self):
        """Test that malformed HTML doesn't crash the renderer."""
        html = "<html><body><p>Unclosed paragraph<div>Overlapping tags</p></div>"
        result = render_html_to_pdf_bytes(html)

        content = result.read()
        # xhtml2pdf is lenient and will still produce a PDF
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_html_with_utf8_encoding(self):
        """Test HTML with UTF-8 encoding declaration."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body>
    <p>UTF-8 content: 你好世界 مرحبا العالم</p>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_long_unbroken_line(self):
        """Test HTML with very long unbroken text."""
        long_word = "A" * 1000
        html = f"<html><body><p>{long_word}</p></body></html>"

        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_nested_elements(self):
        """Test deeply nested HTML elements."""
        html = """<html>
<body>
    <div>
        <div>
            <div>
                <div>
                    <p>Deeply nested content</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")


# ========================================
# FROM FILE: test_cover_letter_generation.py
# ========================================

"""Tests for cover letter generation service."""

import pytest


@pytest.fixture
def mock_profile():
    """Create a mock Profile for testing."""
    from app.models.profile import Profile

    profile = Profile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        first_name="Kena",
        last_name="Ararso",
        headline="Software Engineering Student",
        summary="Backend-focused developer with experience in full-stack projects.",
        email="kenaararso4@gmail.com",
        phone="+251911620012",
        location="Addis Ababa, Ethiopia",
        linkedin="linkedin.com/in/kenaararso-094939258",
        github="github.com/Kena-AT",
    )
    return profile


@pytest.fixture
def mock_job():
    """Create a mock Job for testing."""
    from app.models.job import Job

    job = Job(
        id=uuid.uuid4(),
        external_id="job-test-123",
        title="Backend Engineer",
        company="TestCorp",
        location="Remote",
        description="We need a backend engineer with Python and PostgreSQL experience.",
        salary_min=100000,
        salary_max=150000,
        currency="USD",
        tags=["python", "postgresql", "fastapi"],
        source="linkedin",
    )
    return job


class TestSerializeProfile:
    """Tests for profile serialization."""

    def test_serialize_basic_profile(self, mock_profile):
        from app.services.cover_letter_generation import _serialize_profile

        text = _serialize_profile(mock_profile)

        assert "Kena Ararso" in text
        assert "Software Engineering Student" in text
        # cover_letter _serialize_profile is minimal — only includes name/headline/summary
        assert "Backend-focused developer" in text

    def test_serialize_profile_with_experiences(self, mock_profile):
        from app.models.profile import Experience
        from app.services.cover_letter_generation import _serialize_profile

        exp = Experience(
            id=uuid.uuid4(),
            profile_id=mock_profile.id,
            title="Software Engineering Intern",
            company="Berenda Technologies",
            location="Addis Ababa",
            start_date="2026-02",
            end_date=None,
            is_current=True,
            description="Built web applications and contributed to team projects.",
        )
        mock_profile.experiences = [exp]

        text = _serialize_profile(mock_profile)

        assert "Berenda Technologies" in text
        assert "Software Engineering Intern" in text
        assert "Built web applications" in text

    def test_serialize_profile_with_skills(self, mock_profile):
        from app.models.profile import Skill
        from app.services.cover_letter_generation import _serialize_profile

        skills = [
            Skill(id=uuid.uuid4(), profile_id=mock_profile.id, name="Python"),
            Skill(id=uuid.uuid4(), profile_id=mock_profile.id, name="FastAPI"),
            Skill(id=uuid.uuid4(), profile_id=mock_profile.id, name="PostgreSQL"),
        ]
        mock_profile.skills = skills

        text = _serialize_profile(mock_profile)

        assert "Python" in text
        assert "FastAPI" in text
        assert "PostgreSQL" in text


class TestSerializeJob:
    """Tests for job serialization."""

    def test_serialize_basic_job(self, mock_job):
        from app.services.cover_letter_generation import _serialize_job

        text = _serialize_job(mock_job)

        assert "Backend Engineer" in text
        assert "TestCorp" in text
        assert "Remote" in text
        # tags are not separately serialized in the cover letter version — the
        # description contains the relevant keywords
        assert "Python" in text or "python" in text.lower()

    def test_serialize_job_with_description(self, mock_job):
        from app.services.cover_letter_generation import _serialize_job

        text = _serialize_job(mock_job)

        assert "Python and PostgreSQL experience" in text

    def test_serialize_job_without_description(self):
        from app.models.job import Job
        from app.services.cover_letter_generation import _serialize_job

        job = Job(
            id=uuid.uuid4(),
            external_id="job-minimal",
            title="Developer",
            company="MinimalCo",
            source="indeed",
        )

        text = _serialize_job(job)

        assert "Developer" in text
        assert "MinimalCo" in text


class TestRenderCoverLetterHtml:
    """Tests for HTML rendering."""

    def test_render_classic_template(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        body = "Dear Hiring Manager,\n\nI am writing to express my interest.\n\nSincerely,\nKena"
        html = render_cover_letter_html(body, "classic")

        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "Dear Hiring Manager" in html
        assert "Kena" in html

    def test_render_modern_template(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        body = "Hello team,\n\nI'm excited to apply.\n\nBest,\nKena"
        html = render_cover_letter_html(body, "modern")

        assert "<!DOCTYPE html>" in html
        assert "Hello team" in html

    def test_render_compact_template(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        body = "Short letter.\n\nThanks."
        html = render_cover_letter_html(body, "compact")

        assert "<!DOCTYPE html>" in html
        assert "Short letter" in html

    def test_render_unknown_template_fallback(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        body = "Test letter"
        html = render_cover_letter_html(body, "nonexistent")

        # Should fall back to classic
        assert "<!DOCTYPE html>" in html
        assert "Test letter" in html

    def test_render_handles_html_escaping(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        body = "Hello <script>alert('xss')</script>"
        html = render_cover_letter_html(body, "classic")

        assert "&lt;script&gt;" in html
        assert "<script>alert" not in html

    def test_render_handles_quotes_and_ampersands(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        body = 'Quote: "Hello" & Ampersand'
        html = render_cover_letter_html(body, "classic")

        assert "&quot;" in html or "&#x27;" in html  # Quoted
        assert "&amp;" in html  # Ampersand escaped

    def test_render_empty_body(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        html = render_cover_letter_html("", "classic")

        assert "<!DOCTYPE html>" in html

    def test_render_multiline_paragraphs(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        body = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        html = render_cover_letter_html(body, "classic")

        assert "<p>" in html
        assert "Paragraph one" in html
        assert "Paragraph two" in html

    def test_classic_template_has_serif_font(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        html = render_cover_letter_html("Test", "classic")
        assert "Georgia" in html or "serif" in html

    def test_modern_template_has_sans_serif(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        html = render_cover_letter_html("Test", "modern")
        assert "Segoe UI" in html or "Arial" in html or "sans-serif" in html

    def test_compact_template_has_smaller_font(self):
        from app.services.cover_letter_generation import render_cover_letter_html

        html = render_cover_letter_html("Test", "compact")
        assert "12px" in html or "font-size:12px" in html

    def test_compact_template_has_valid_css(self):
        """Regression: compact template margin must not contain corrupted chars."""
        from app.services.cover_letter_generation import render_cover_letter_html

        html = render_cover_letter_html("Test body", "compact")
        # The compact paragraph margin should be a valid CSS value
        assert "margin:0.4em 0" in html
        # No mojibake / non-ASCII junk in the inline style
        assert "惆怅" not in html


class TestEscapeHelper:
    """Tests for the _esc helper function."""

    def test_esc_basic_text(self):
        from app.services.cover_letter_generation import _esc

        assert _esc("Hello World") == "Hello World"

    def test_esc_html_tags(self):
        from app.services.cover_letter_generation import _esc

        assert _esc("<script>") == "&lt;script&gt;"
        assert _esc("<b>bold</b>") == "&lt;b&gt;bold&lt;/b&gt;"

    def test_esc_quotes(self):
        from app.services.cover_letter_generation import _esc

        result = _esc('Say "Hello"')
        assert "&quot;" in result or "&#x27;" in result

    def test_esc_ampersand(self):
        from app.services.cover_letter_generation import _esc

        assert "&amp;" in _esc("A & B")

    def test_esc_empty_string(self):
        from app.services.cover_letter_generation import _esc

        assert _esc("") == ""

    def test_esc_none_value(self):
        from app.services.cover_letter_generation import _esc

        assert _esc(None) == ""
