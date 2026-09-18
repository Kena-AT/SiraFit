import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.extension_token import ExtensionToken
from app.models.job import Job, JobImport, JobImportItem
from app.models.profile import Profile, Skill
from app.models.user import User


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(db):
    email = f"ext_user_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        full_name="Alex Mercer",
        hashed_password=get_password_hash("StrongPass123!"),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Add profile with skills
    profile = Profile(
        user_id=user.id,
        first_name="Alex",
        last_name="Mercer",
        headline="Senior Full Stack Engineer",
        summary="Experienced engineer in Python and React.",
        email=email,
        phone="+15551234567",
        location="San Francisco, CA",
        website="https://alexmercer.dev",
        linkedin="https://linkedin.com/in/alexmercer",
        github="https://github.com/alexmercer",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    db.add(Skill(profile_id=profile.id, name="TypeScript"))
    db.add(Skill(profile_id=profile.id, name="Python"))
    db.commit()

    yield user

    # Cleanup
    db.query(JobImportItem).filter(
        JobImportItem.import_id.in_(
            db.query(JobImport.id).filter(JobImport.user_id == user.id)
        )
    ).delete(synchronize_session=False)
    db.query(Job).filter(
        Job.import_id.in_(db.query(JobImport.id).filter(JobImport.user_id == user.id))
    ).delete(synchronize_session=False)
    db.query(JobImport).filter(JobImport.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(ExtensionToken).filter(ExtensionToken.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(Profile).filter(Profile.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(User).filter(User.id == user.id).delete(synchronize_session=False)
    db.commit()


@pytest.fixture
def auth_headers(client: TestClient, test_user: User):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "StrongPass123!"},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestExtensionTokenLifecycle:
    def test_issue_extension_token(self, client: TestClient, auth_headers: dict):
        resp = client.post(
            "/api/v1/agent/token",
            headers=auth_headers,
            json={"name": "Chrome on MacBook", "expires_days": 14},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["token"].startswith("srf_ext_")
        assert data["token_type"] == "Bearer"
        assert data["name"] == "Chrome on MacBook"
        assert "expires_at" in data

    def test_status_with_extension_token(
        self, client: TestClient, auth_headers: dict, test_user: User
    ):
        # 1. Issue token
        issue_resp = client.post(
            "/api/v1/agent/token",
            headers=auth_headers,
            json={"name": "Firefox"},
        )
        ext_token = issue_resp.json()["token"]

        # 2. Call status with extension token
        status_resp = client.get(
            "/api/v1/agent/status",
            headers={"Authorization": f"Bearer {ext_token}"},
        )
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["connected"] is True
        assert data["user_id"] == str(test_user.id)
        assert data["user_email"] == test_user.email
        assert data["user_name"] == "Alex Mercer"

    def test_logout_revokes_extension_token(
        self, client: TestClient, auth_headers: dict
    ):
        # 1. Issue token
        issue_resp = client.post("/api/v1/agent/token", headers=auth_headers, json={})
        ext_token = issue_resp.json()["token"]

        # 2. Logout with that token
        logout_resp = client.post(
            "/api/v1/agent/logout",
            headers={"Authorization": f"Bearer {ext_token}"},
        )
        assert logout_resp.status_code == 200

        # 3. Verify subsequent calls with this token fail with 401
        status_resp = client.get(
            "/api/v1/agent/status",
            headers={"Authorization": f"Bearer {ext_token}"},
        )
        assert status_resp.status_code == 401
        assert "Invalid or expired" in status_resp.json()["detail"]


class TestAutofillProfileExport:
    def test_get_autofill_profile(
        self, client: TestClient, auth_headers: dict, test_user: User
    ):
        issue_resp = client.post("/api/v1/agent/token", headers=auth_headers, json={})
        ext_token = issue_resp.json()["token"]

        resp = client.get(
            "/api/v1/agent/profile",
            headers={"Authorization": f"Bearer {ext_token}"},
        )
        assert resp.status_code == 200
        profile = resp.json()
        assert profile["first_name"] == "Alex"
        assert profile["last_name"] == "Mercer"
        assert profile["full_name"] == "Alex Mercer"
        assert profile["email"] == test_user.email
        assert profile["phone"] == "+15551234567"
        assert profile["location"] == "San Francisco, CA"
        assert profile["linkedin"] == "https://linkedin.com/in/alexmercer"
        assert profile["github"] == "https://github.com/alexmercer"
        assert "TypeScript" in profile["skills"]
        assert "Python" in profile["skills"]

    def test_unauthenticated_profile_rejected(self, client: TestClient):
        resp = client.get("/api/v1/agent/profile")
        assert resp.status_code == 401


class TestJobCaptureImport:
    def test_successful_job_capture(self, client: TestClient, auth_headers: dict, db):
        issue_resp = client.post("/api/v1/agent/token", headers=auth_headers, json={})
        ext_token = issue_resp.json()["token"]

        capture_payload = {
            "capture_id": f"cap_{uuid.uuid4().hex[:8]}",
            "page_url": "https://boards.greenhouse.io/stripe/jobs/9876543",
            "platform": "greenhouse",
            "title": "Staff Backend Engineer",
            "company": "Stripe",
            "location": "San Francisco, CA / Remote",
            "description": "<p>Build high-scale payment APIs.</p><script>alert('xss')</script>",
            "salary_raw": "$220,000 - $280,000",
            "tags": ["python", "infrastructure"],
            "confidence": 0.95,
            "extracted_via": "dom_adapter",
        }

        resp = client.post(
            "/api/v1/agent/import",
            headers={"Authorization": f"Bearer {ext_token}"},
            json=capture_payload,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["status"] == "imported"
        assert data["job_id"] is not None
        assert data["title"] == "Staff Backend Engineer"
        assert data["company"] == "Stripe"

        # Verify Job in database
        job = db.query(Job).filter(Job.id == uuid.UUID(data["job_id"])).first()
        assert job is not None
        assert "alert" not in job.description  # Script tag stripped
        assert job.source == "extension"
        assert job.import_id == uuid.UUID(data["import_id"])

        # Verify JobImport status
        job_import = (
            db.query(JobImport)
            .filter(JobImport.id == uuid.UUID(data["import_id"]))
            .first()
        )
        assert job_import is not None
        assert job_import.status == "completed"
        assert job_import.ok_count == 1
        assert job_import.fail_count == 0

        # Verify JobImportItem
        item = (
            db.query(JobImportItem)
            .filter(JobImportItem.import_id == job_import.id)
            .first()
        )
        assert item is not None
        assert item.status == "imported"
        assert item.job_id == job.id

    def test_duplicate_capture_detection(
        self, client: TestClient, auth_headers: dict, db
    ):
        issue_resp = client.post("/api/v1/agent/token", headers=auth_headers, json={})
        ext_token = issue_resp.json()["token"]

        capture_payload = {
            "capture_id": f"cap_{uuid.uuid4().hex[:8]}",
            "page_url": "https://jobs.lever.co/netflix/11223344",
            "platform": "lever",
            "title": "Lead Platform Engineer",
            "company": "Netflix",
            "location": "Los Gatos, CA",
            "description": "Architect cloud streaming services.",
        }

        # 1. First import succeeds
        resp1 = client.post(
            "/api/v1/agent/import",
            headers={"Authorization": f"Bearer {ext_token}"},
            json=capture_payload,
        )
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "imported"
        first_job_id = resp1.json()["job_id"]

        # 2. Second import of same job returns duplicate
        capture_payload["capture_id"] = f"cap_{uuid.uuid4().hex[:8]}"
        resp2 = client.post(
            "/api/v1/agent/import",
            headers={"Authorization": f"Bearer {ext_token}"},
            json=capture_payload,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["success"] is True
        assert data2["status"] == "duplicate"
        assert data2["job_id"] == first_job_id
        assert "already exists" in data2["message"]

        # Verify only 1 Job was created
        jobs = (
            db.query(Job)
            .filter(Job.title == "Lead Platform Engineer", Job.company == "Netflix")
            .all()
        )
        assert len(jobs) == 1

    def test_validation_bounds(self, client: TestClient, auth_headers: dict):
        issue_resp = client.post("/api/v1/agent/token", headers=auth_headers, json={})
        ext_token = issue_resp.json()["token"]

        # Oversized description (>50000 chars)
        huge_payload = {
            "capture_id": "test_id",
            "page_url": "https://example.com/job/1",
            "title": "Dev",
            "company": "Tech Corp",
            "description": "x" * 50001,
        }
        resp = client.post(
            "/api/v1/agent/import",
            headers={"Authorization": f"Bearer {ext_token}"},
            json=huge_payload,
        )
        assert resp.status_code == 422

        # Invalid URL
        bad_url_payload = {
            "capture_id": "test_id",
            "page_url": "not-a-valid-url",
            "title": "Dev",
            "company": "Tech Corp",
            "description": "Valid description.",
        }
        resp = client.post(
            "/api/v1/agent/import",
            headers={"Authorization": f"Bearer {ext_token}"},
            json=bad_url_payload,
        )
        assert resp.status_code == 422
