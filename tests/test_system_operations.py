# ========================================
# FROM FILE: test_analytics.py
# ========================================

from app.services.analytics import generate_analytics_metrics, create_analytics_snapshot
from app.models.job import Job, JobApplication
from app.models.profile import Profile, Skill
import uuid


def test_generate_analytics_metrics(test_user, db):
    """Test generating analytics metrics for a user."""
    # Create a profile with skills
    profile = Profile(
        user_id=test_user.id,
        skills=[Skill(name="python"), Skill(name="react"), Skill(name="aws")],
        experiences=[],
        educations=[],
    )
    db.add(profile)
    db.commit()

    # Create some jobs
    job1 = Job(
        external_id=f"analytics-job-1-{uuid.uuid4().hex[:8]}",
        title="Software Engineer",
        company="Acme",
        tags=["python", "react"],
    )
    job2 = Job(
        external_id=f"analytics-job-2-{uuid.uuid4().hex[:8]}",
        title="Backend Engineer",
        company="Beta",
        tags=["python", "aws"],
    )
    job3 = Job(
        external_id=f"analytics-job-3-{uuid.uuid4().hex[:8]}",
        title="Frontend Engineer",
        company="Gamma",
        tags=["react", "typescript"],
    )
    db.add_all([job1, job2, job3])
    db.commit()

    # Create applications with various statuses
    apps = [
        JobApplication(user_id=test_user.id, job_id=job1.id, status="applied"),
        JobApplication(user_id=test_user.id, job_id=job2.id, status="screening"),
        JobApplication(user_id=test_user.id, job_id=job3.id, status="interview"),
    ]
    db.add_all(apps)
    db.commit()

    metrics = generate_analytics_metrics(db, test_user.id)

    assert metrics["total_applications"] == 3
    assert "interview_rate" in metrics
    assert "avg_response_time_days" in metrics
    assert "offer_rate" in metrics
    assert "conversion_funnel" in metrics
    assert "rejection_stages" in metrics
    assert "skill_coverage" in metrics
    assert "market_demand" in metrics


def test_create_analytics_snapshot(test_user, db):
    """Test creating an analytics snapshot."""
    snapshot = create_analytics_snapshot(db, test_user.id)

    assert snapshot is not None
    assert snapshot.user_id == test_user.id
    assert snapshot.snapshot_date is not None
    assert snapshot.metrics is not None
    assert "total_applications" in snapshot.metrics


def test_get_latest_snapshot(test_user, db):
    """Test getting the latest analytics snapshot."""
    from app.services.analytics import get_latest_snapshot

    # Create a snapshot
    create_analytics_snapshot(db, test_user.id)

    # Get the latest
    latest = get_latest_snapshot(db, test_user.id)

    assert latest is not None
    assert latest.user_id == test_user.id


def test_list_snapshots(test_user, db):
    """Test listing analytics snapshots."""
    from app.services.analytics import get_snapshots

    # Create multiple snapshots
    for _ in range(3):
        create_analytics_snapshot(db, test_user.id)

    snapshots, total = get_snapshots(db, test_user.id, skip=0, limit=10)

    assert total == 3
    assert len(snapshots) == 3


# ========================================
# FROM FILE: test_batch_api.py
# ========================================


def test_batch_job_create(client, auth_headers, db):
    """Test creating a batch job."""
    from app.models.job import Job

    # Create test jobs using the db fixture session
    job_ids = []
    for i in range(3):
        job = Job(
            external_id=f"batch-test-{i}-{uuid.uuid4().hex[:8]}",
            title="Engineer",
            company="Co",
            tags=["python"],
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_ids.append(str(job.id))

    response = client.post(
        "/api/v1/batch",
        json={"operation_type": "score", "job_ids": job_ids, "params": {}},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["operation_type"] == "score"
    assert data["status"] == "pending"
    assert data["total_items"] == 3
    assert data["processed_items"] == 0
    assert len(data["payload"]["job_ids"]) == 3
    return data["id"]


def test_batch_job_list(client, auth_headers):
    """Test listing batch jobs."""
    response = client.get("/api/v1/batch", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data


def test_batch_job_get(client, auth_headers, db):
    """Test getting a single batch job."""
    batch_id = test_batch_job_create(client, auth_headers, db)

    response = client.get(f"/api/v1/batch/{batch_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == batch_id


def test_batch_job_retry(client, auth_headers, db):
    """Test retrying a batch job."""
    from app.models.job import Job
    from app.models.batch import BatchJob
    import uuid

    # Create a test job with string UUID
    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        external_id=f"retry-test-job-{job_id.hex[:8]}",
        title="Engineer",
        company="Co",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Create batch job
    response = client.post(
        "/api/v1/batch",
        json={"operation_type": "score", "job_ids": [str(job_id)], "params": {}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    batch_id = uuid.UUID(response.json()["id"])  # Convert string back to UUID

    # Manually set status to partial (simulate completion)
    batch_job = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
    batch_job.status = "partial"
    batch_job.result_summary = {str(job_id): {"status": "error", "error": "test error"}}
    db.commit()

    # Try retry
    response = client.post(f"/api/v1/batch/{str(batch_id)}/retry", headers=auth_headers)
    assert response.status_code in (200, 400)


def test_batch_job_cancel(client, auth_headers, db):
    """Test cancelling a batch job."""
    batch_id = test_batch_job_create(client, auth_headers, db)

    # Should be able to cancel pending job
    response = client.post(f"/api/v1/batch/{batch_id}/cancel", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["cancel_requested"] is True


def test_batch_job_invalid_operation(client, auth_headers):
    """Test creating batch job with invalid operation type."""
    response = client.post(
        "/api/v1/batch",
        json={"operation_type": "invalid", "job_ids": [], "params": {}},
        headers=auth_headers,
    )
    assert response.status_code == 422  # Validation error


def test_batch_job_empty_job_ids(client, auth_headers):
    """Test creating batch job with empty job_ids."""
    response = client.post(
        "/api/v1/batch",
        json={"operation_type": "score", "job_ids": [], "params": {}},
        headers=auth_headers,
    )
    # Pydantic validation returns 422 for min_length validation
    assert response.status_code == 422


def test_batch_job_too_many_job_ids(client, auth_headers):
    """Test creating batch job with >500 job_ids."""
    job_ids = [str(uuid.uuid4()) for _ in range(501)]
    response = client.post(
        "/api/v1/batch",
        json={"operation_type": "score", "job_ids": job_ids, "params": {}},
        headers=auth_headers,
    )
    # Pydantic validation returns 422 for max_length validation
    assert response.status_code == 422


# ========================================
# FROM FILE: test_batch_operations.py
# ========================================

from app.services.batch_operations import (
    batch_score_item,
    batch_tag_item,
    batch_archive_item,
)


def test_batch_score_item(test_user, db):
    job = Job(
        external_id="score-job",
        title="Engineer",
        company="Co",
        tags=["python", "react"],
    )
    db.add(job)
    db.commit()
    profile = Profile(
        user_id=test_user.id,
        skills=[Skill(name="python")],
        experiences=[],
        educations=[],
    )
    db.add(profile)
    db.commit()
    result = batch_score_item(job.id, test_user.id, {}, db)
    assert "score" in result
    assert 0 <= result["score"] <= 100
    assert "breakdown" in result


def test_batch_tag_item_add(test_user, db):
    job = Job(external_id="tag-job", title="Engineer", company="Co", tags=["python"])
    db.add(job)
    db.commit()
    result = batch_tag_item(
        job.id, test_user.id, {"tags": ["remote", "senior"], "action": "add"}, db
    )
    assert "remote" in result["tags"]
    assert "senior" in result["tags"]
    assert "python" in result["tags"]


def test_batch_tag_item_remove(test_user, db):
    job = Job(
        external_id="tag-job2",
        title="Engineer",
        company="Co",
        tags=["python", "remote", "senior"],
    )
    db.add(job)
    db.commit()
    result = batch_tag_item(
        job.id, test_user.id, {"tags": ["remote"], "action": "remove"}, db
    )
    assert "remote" not in result["tags"]
    assert "senior" in result["tags"]
    assert "python" in result["tags"]


def test_batch_archive_job(test_user, db):
    job = Job(external_id="arch-job", title="Engineer", company="Co")
    db.add(job)
    db.commit()
    result = batch_archive_item(job.id, test_user.id, {"target": "jobs"}, db)
    assert result["archived"] is True
    db.refresh(job)
    assert job.source == "archived"


def test_batch_archive_application(test_user, db):
    job = Job(external_id="arch-app-job", title="Engineer", company="Co")
    db.add(job)
    db.commit()
    from app.models.job import JobApplication

    app = JobApplication(user_id=test_user.id, job_id=job.id, status="applied")
    db.add(app)
    db.commit()
    db.refresh(app)
    result = batch_archive_item(app.id, test_user.id, {"target": "applications"}, db)
    assert result["archived"] is True
    assert result["target"] == "applications"
    db.refresh(app)
    assert app.status == "archived"


# ========================================
# FROM FILE: test_worker_tasks.py
# ========================================

"""Tests for Celery worker tasks (resume generation + PDF rendering)."""

import json
import os
from unittest.mock import patch, MagicMock

from app.worker.tasks import (
    _save_pdf_bytes,
    _pdf_storage_dir,
    enqueue_resume_pdf_render,
    enqueue_cover_letter_pdf_render,
)


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


class TestPdfStorage:
    """Tests for the PDF file storage helpers."""

    def test_pdf_storage_dir_exists(self):
        path = _pdf_storage_dir()
        assert os.path.isdir(path)
        assert "sirafit_pdfs" in path

    def test_save_pdf_bytes_creates_file(self):
        pdf_bytes = b"%PDF-1.4 test content"
        path = _save_pdf_bytes(pdf_bytes, "test-resume-123")

        assert os.path.isfile(path)
        assert path.endswith("test-resume-123.pdf")
        with open(path, "rb") as fh:
            assert fh.read() == pdf_bytes
        # Cleanup
        os.remove(path)

    def test_save_pdf_bytes_overwrites_existing(self):
        path = _save_pdf_bytes(b"old", "test-overwrite")
        path = _save_pdf_bytes(b"new content", "test-overwrite")

        with open(path, "rb") as fh:
            assert fh.read() == b"new content"
        os.remove(path)

    def test_storage_dir_is_deterministic(self):
        path1 = _pdf_storage_dir()
        path2 = _pdf_storage_dir()
        assert path1 == path2


# ---------------------------------------------------------------------------
# Resume PDF rendering helper
# ---------------------------------------------------------------------------


class TestRunResumePdfRender:
    """Tests for _run_resume_pdf_render (the synchronous helper)."""

    def test_render_with_valid_version(self):
        """Test that a valid ResumeVersion gets rendered and persisted."""
        from app.models.job import Resume, ResumeVersion
        from app.worker.tasks import _run_resume_pdf_render

        version_id = uuid.uuid4()
        resume = Resume(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="Test Resume",
            content="{}",
            is_primary=False,
        )
        version = ResumeVersion(
            id=version_id,
            resume_id=resume.id,
            version_number=1,
            content=json.dumps(
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    "summary": "A developer.",
                    "experience": [],
                    "projects": [],
                    "skills": ["Python"],
                    "education": [],
                }
            ),
            template="minimal",
            status="completed",
            score=80,
        )
        version.resume = resume

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = version

        with patch("app.worker.tasks.SessionLocal", return_value=mock_db):
            _run_resume_pdf_render(version_id)

        assert version.status == "completed"
        assert resume.pdf_url is not None
        assert resume.pdf_url.endswith(".pdf")
        assert os.path.isfile(resume.pdf_url)
        # Cleanup
        if os.path.isfile(resume.pdf_url):
            os.remove(resume.pdf_url)

    def test_render_missing_version_logs_and_returns(self):
        """Test that a missing version doesn't crash."""
        from app.worker.tasks import _run_resume_pdf_render

        version_id = uuid.uuid4()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.worker.tasks.SessionLocal", return_value=mock_db):
            # Should not raise
            _run_resume_pdf_render(version_id)

    def test_render_with_invalid_content_succeeds(self):
        """Test that invalid JSON renders gracefully (no crash)."""
        from app.models.job import Resume, ResumeVersion
        from app.worker.tasks import _run_resume_pdf_render

        version_id = uuid.uuid4()
        version = ResumeVersion(
            id=version_id,
            resume_id=uuid.uuid4(),
            version_number=1,
            content="not valid json {",
            template="minimal",
            status="completed",
        )
        version.resume = Resume(
            id=version.resume_id,
            user_id=uuid.uuid4(),
            title="R",
            content="{}",
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = version

        with patch("app.worker.tasks.SessionLocal", return_value=mock_db):
            _run_resume_pdf_render(version_id)

        # Graceful handling: should still produce a PDF with empty data
        assert version.status == "completed"
        assert version.resume.pdf_url is not None
        if os.path.isfile(version.resume.pdf_url):
            os.remove(version.resume.pdf_url)


# ---------------------------------------------------------------------------
# Cover letter PDF rendering helper
# ---------------------------------------------------------------------------


class TestRunCoverLetterPdfRender:
    """Tests for _run_cover_letter_pdf_render (the synchronous helper)."""

    def test_render_with_valid_letter(self):
        """Test that a valid CoverLetter gets rendered and persisted."""
        from app.models.cover_letter import CoverLetter
        from app.worker.tasks import _run_cover_letter_pdf_render

        letter_id = uuid.uuid4()
        user_id = uuid.uuid4()
        letter = CoverLetter(
            id=letter_id,
            user_id=user_id,
            title="Test Letter",
            body="Dear Hiring Manager,\n\nI am writing to apply.\n\nSincerely,\nTest",
            tone="formal",
            template="classic",
            status="completed",
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = letter

        with patch("app.worker.tasks.SessionLocal", return_value=mock_db):
            _run_cover_letter_pdf_render(letter_id)

        assert letter.status == "completed"
        assert letter.pdf_url is not None
        assert letter.pdf_url.endswith(".pdf")
        assert os.path.isfile(letter.pdf_url)
        # Cleanup
        if os.path.isfile(letter.pdf_url):
            os.remove(letter.pdf_url)

    def test_render_missing_letter_returns_silently(self):
        """Test that a missing letter doesn't crash."""
        from app.worker.tasks import _run_cover_letter_pdf_render

        letter_id = uuid.uuid4()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.worker.tasks.SessionLocal", return_value=mock_db):
            _run_cover_letter_pdf_render(letter_id)

    def test_render_with_compact_template(self):
        """Test rendering with the compact template."""
        from app.models.cover_letter import CoverLetter
        from app.worker.tasks import _run_cover_letter_pdf_render

        letter = CoverLetter(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="Compact Letter",
            body="Short body.\n\nThanks.",
            template="compact",
            status="completed",
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = letter

        with patch("app.worker.tasks.SessionLocal", return_value=mock_db):
            _run_cover_letter_pdf_render(letter.id)

        assert letter.status == "completed"
        assert letter.pdf_url is not None
        assert os.path.isfile(letter.pdf_url)
        # Cleanup
        if os.path.isfile(letter.pdf_url):
            os.remove(letter.pdf_url)


# ---------------------------------------------------------------------------
# Enqueue helpers (sync fallback path — no broker in tests)
# ---------------------------------------------------------------------------


class TestEnqueueResumePdfRender:
    """Tests for enqueue_resume_pdf_render (sync fallback)."""

    def test_fallback_runs_synchronously(self):
        """Without a broker, the enqueue helper falls back to sync execution."""
        from app.models.job import Resume, ResumeVersion

        version = ResumeVersion(
            id=uuid.uuid4(),
            resume_id=uuid.uuid4(),
            version_number=1,
            content=json.dumps(
                {
                    "name": "Test",
                    "email": "t@e.com",
                    "summary": "Dev",
                    "experience": [],
                    "projects": [],
                    "skills": [],
                    "education": [],
                }
            ),
            template="minimal",
            status="completed",
        )
        version.resume = Resume(
            id=version.resume_id,
            user_id=uuid.uuid4(),
            title="R",
            content="{}",
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = version

        # Simulate broker unavailability so the sync fallback is triggered
        with (
            patch("app.worker.tasks.SessionLocal", return_value=mock_db),
            patch(
                "app.worker.tasks.celery_app.send_task",
                side_effect=ConnectionError("No broker"),
            ),
        ):
            enqueue_resume_pdf_render(version.id)

        assert version.status == "completed"
        assert version.resume.pdf_url is not None
        if os.path.isfile(version.resume.pdf_url):
            os.remove(version.resume.pdf_url)


class TestEnqueueCoverLetterPdfRender:
    """Tests for enqueue_cover_letter_pdf_render (sync fallback)."""

    def test_fallback_runs_synchronously(self):
        """Without a broker, the enqueue helper falls back to sync execution."""
        from app.models.cover_letter import CoverLetter

        letter = CoverLetter(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="L",
            body="Hello.\n\nBye.",
            template="modern",
            status="completed",
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = letter

        with (
            patch("app.worker.tasks.SessionLocal", return_value=mock_db),
            patch(
                "app.worker.tasks.celery_app.send_task",
                side_effect=ConnectionError("No broker"),
            ),
        ):
            enqueue_cover_letter_pdf_render(letter.id)

        assert letter.status == "completed"
        assert letter.pdf_url is not None
        if os.path.isfile(letter.pdf_url):
            os.remove(letter.pdf_url)


# ========================================
# FROM FILE: test_notifications.py
# ========================================

import uuid

from app.services.notification import (
    create_notification,
    get_notifications,
    mark_as_read,
    mark_all_as_read,
    get_unread_count,
)
from app.models.notification import Notification


def test_create_notification(test_user, db):
    """Test creating a notification."""
    notification = create_notification(
        db=db,
        user_id=test_user.id,
        title="Test Notification",
        body="This is a test notification",
        kind="alert",
    )

    assert notification is not None
    assert notification.id is not None
    assert notification.user_id == test_user.id
    assert notification.title == "Test Notification"
    assert notification.body == "This is a test notification"
    assert notification.kind == "alert"
    assert notification.status == "unread"
    assert notification.read_at is None


def test_get_notifications(test_user, db):
    """Test getting notifications with pagination."""
    # Create multiple notifications
    for i in range(5):
        create_notification(
            db=db,
            user_id=test_user.id,
            title=f"Notification {i}",
            body=f"Body {i}",
            kind="system_event",
        )

    # Get all
    notifications, total = get_notifications(db, test_user.id, skip=0, limit=10)
    assert total == 5
    assert len(notifications) == 5

    # Get with pagination
    notifications, total = get_notifications(db, test_user.id, skip=2, limit=2)
    assert total == 5
    assert len(notifications) == 2

    # Filter by status
    notifications, total = get_notifications(db, test_user.id, status="unread")
    assert total == 5
    assert len(notifications) == 5


def test_mark_as_read(test_user, db):
    """Test marking a notification as read."""
    notification = create_notification(
        db=db, user_id=test_user.id, title="Test", body="Test body", kind="alert"
    )

    # Mark as read
    updated = mark_as_read(db, test_user.id, notification.id)

    assert updated is not None
    assert updated.status == "read"
    assert updated.read_at is not None

    # Verify it's read in the database
    db.refresh(notification)
    assert notification.status == "read"


def test_mark_all_as_read(test_user, db):
    """Test marking all notifications as read."""
    # Create multiple notifications
    for i in range(3):
        create_notification(
            db=db,
            user_id=test_user.id,
            title=f"Test {i}",
            body=f"Body {i}",
            kind="system_event",
        )

    # Mark all as read
    count = mark_all_as_read(db, test_user.id)

    assert count == 3

    # Verify all are read
    notifications, total = get_notifications(db, test_user.id, status="read")
    assert total == 3


def test_get_unread_count(test_user, db):
    """Test getting unread notification count."""
    # Create some notifications
    for i in range(3):
        create_notification(
            db=db,
            user_id=test_user.id,
            title=f"Test {i}",
            body=f"Body {i}",
            kind="system_event",
        )

    count = get_unread_count(db, test_user.id)
    assert count == 3

    # Mark one as read
    notification = (
        db.query(Notification).filter(Notification.user_id == test_user.id).first()
    )
    mark_as_read(db, test_user.id, notification.id)

    count = get_unread_count(db, test_user.id)
    assert count == 2


# ========================================
# FROM FILE: test_email.py
# ========================================

"""
Simple script to test email configuration
Run: python test_email.py
"""

import os

from dotenv import load_dotenv
from app.services.email import email_service

# Load environment variables
load_dotenv()


def test_email():
    """Test sending a verification email"""
    test_email_address = os.getenv("TEST_EMAIL", "kenakaye11@gmail.com")  # Send to yourself for testing
    test_token = os.getenv("TEST_TOKEN", "test_token_12345")

    print("=" * 60)
    print("Testing Email Configuration")
    print("=" * 60)
    print(f"SMTP Host: {os.getenv('SMTP_HOST')}")
    print(f"SMTP Port: {os.getenv('SMTP_PORT')}")
    print(f"SMTP User: {os.getenv('SMTP_USER')[:3]}***")  # Mask user
    print(f"SMTP From: {os.getenv('SMTP_FROM')}")
    print(f"Sending test email to: {test_email_address}")
    print("=" * 60)

    try:
        result = email_service.send_verification_email(test_email_address, test_token)

        if result:
            print("\n✅ SUCCESS! Email sent successfully!")
            print(f"\nCheck your inbox at {test_email_address}")
            print("(Also check spam folder)")
            print("\nVerification link in email:")
            print(f"http://localhost:3030/verify-email?token={test_token}")
        else:
            print("\n❌ FAILED! Email could not be sent.")
            print("Check the error messages above.")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nCommon issues:")
        print("1. Wrong SMTP credentials")
        print("2. Sender email not verified in Brevo")
        print("3. Network/firewall blocking SMTP")


if __name__ == "__main__":
    test_email()
