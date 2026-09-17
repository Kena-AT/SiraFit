"""Unit and integration tests for Sprint 4: Offline Processing via Celery (Tier A).

Tests cover:
  - Phase B / D.2: POST /jobs/import returns 202 and queues background task
  - Phase D.2: Status polling endpoint GET /jobs/import/{id} with auth checks
  - Phase D.2: Broker failure triggers graceful synchronous fallback without 500
  - Phase D.2: Worker execution completes successfully and updates JobImport to 'completed'
  - Phase D.2: Parse failure / zero jobs marks JobImport as 'failed'
  - Phase D.2: Celery SoftTimeLimitExceeded marks JobImport as 'failed'
  - Phase D.2: Retry idempotency — duplicate jobs are never created on retries
  - Phase D.2: Partial success behavior preserves created jobs while marking import status
  - Phase D.2: Stuck job detector (Celery Beat) recovers imports processing > 5 min
  - Phase D.3: Database session lifecycle (closed on success, error, and recovery)
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from celery.exceptions import SoftTimeLimitExceeded
from fastapi.testclient import TestClient

_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from app.main import app
from app.core.database import get_db, SessionLocal
from app.api.users import get_current_user
from app.models.job import Job, JobImport, JobImportItem
from app.models.user import User
from app.services.job_import import (
    process_import,
    _scrape_and_import_job_sync,
    enqueue_job_import,
)
from app.worker.tasks.scraping import scrape_and_import_job
from app.worker.tasks.monitoring import detect_stuck_imports

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> str:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def client(db, test_user):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── 1. REST Endpoints & Async Enqueueing ───────────────────────────────────


class TestAsyncImportEndpoints:
    """Verify POST /jobs/import returns 202 and GET /jobs/import/{id} polls status."""

    def test_happy_path_url_import_async(self, client, db, test_user):
        """POST /jobs/import returns 202 Accepted when task is queued."""
        html = _load_fixture("greenhouse_job.html")

        # Mock Celery delay to simulate successful task queueing
        with patch("app.services.job_import.enqueue_job_import", return_value={"queued": True}):
            resp = client.post(
                "/api/v1/jobs/import",
                json={
                    "source_type": "url",
                    "data": "https://boards.greenhouse.io/acme/jobs/async_happy_path",
                },
            )

        assert resp.status_code == 202
        body = resp.json()
        assert body["scrape_method"] == "async"
        import_record = body["import_record"]
        assert import_record["status"] == "processing"
        import_id = import_record["id"]

        # Simulate the worker running the background task
        with patch("app.services.job_import.fetch_job_html", return_value=html):
            result = _scrape_and_import_job_sync(
                import_id,
                "https://boards.greenhouse.io/acme/jobs/async_happy_path",
                "url",
                str(test_user.id),
            )

        assert result["status"] == "completed"

        # Verify through the status endpoint
        poll_resp = client.get(f"/api/v1/jobs/import/{import_id}")
        assert poll_resp.status_code == 200
        poll_data = poll_resp.json()
        assert poll_data["import_record"]["status"] == "completed"
        assert poll_data["import_record"]["ok_count"] == 1
        assert len(poll_data["jobs"]) == 1

    def test_import_status_authorization(self, client, db):
        """Cross-user import access returns 403 Forbidden."""
        other_user = User(
            id=uuid.uuid4(),
            email="other_user@example.com",
            hashed_password="hash",
            is_active=True,
        )
        db.add(other_user)
        db.commit()

        # Create import owned by other_user
        other_import = JobImport(
            user_id=other_user.id,
            source="url",
            status="completed",
        )
        db.add(other_import)
        db.commit()

        # Current user attempts to read other user's import
        resp = client.get(f"/api/v1/jobs/import/{other_import.id}")
        assert resp.status_code == 403

    def test_celery_broker_down_falls_back_to_sync(self, client, db, test_user):
        """When the Celery broker is unavailable, fallback runs synchronously inline without 500."""
        html = _load_fixture("greenhouse_job.html")

        def fake_enqueue(import_id, url, source, user_id):
            result = _scrape_and_import_job_sync(import_id, url, source, user_id)
            return {"queued": False, "status": result.get("status", "completed")}

        with patch("app.services.job_import.enqueue_job_import", side_effect=fake_enqueue):
            with patch("app.services.job_import.fetch_job_html", return_value=html):
                resp = client.post(
                    "/api/v1/jobs/import",
                    json={
                        "source_type": "url",
                        "data": "https://boards.greenhouse.io/acme/jobs/broker_fallback_test",
                    },
                )

        # Fallback executed synchronously and returned 200 with completed import
        assert resp.status_code == 200
        body = resp.json()
        assert body["import_record"]["status"] == "completed"
        assert body["import_record"]["ok_count"] == 1

    def test_enqueue_job_import_handles_broker_down(self, db, test_user):
        """enqueue_job_import catches broker exception and returns queued=False."""
        import_record = JobImport(user_id=test_user.id, source="url", status="processing")
        db.add(import_record)
        db.commit()

        html = _load_fixture("greenhouse_job.html")
        target_task = getattr(scrape_and_import_job, "_get_current_object", lambda: scrape_and_import_job)()

        with patch.object(target_task, "apply_async", side_effect=Exception("Redis connection refused")):
            with patch("app.services.job_import.fetch_job_html", return_value=html):
                outcome = enqueue_job_import(
                    str(import_record.id),
                    "https://boards.greenhouse.io/acme/jobs/broker_down_direct",
                    "url",
                    str(test_user.id),
                )

        assert outcome["queued"] is False
        assert outcome["status"] == "completed"


# ─── 2. Worker Task Execution & Failure Modes ───────────────────────────────


class TestWorkerTaskExecution:
    """Verify worker execution, error handling, retries, and timeout handling."""

    def test_parse_failure_marks_import_failed(self, db, test_user):
        """Parse failure marks the JobImport as failed and populates error details."""
        job_import = JobImport(
            user_id=test_user.id,
            source="url",
            status="processing",
            source_data="https://boards.greenhouse.io/acme/jobs/invalid_parse",
        )
        db.add(job_import)
        db.commit()

        # Simulate parse crash
        with patch("app.services.job_import.fetch_job_html", return_value="<html></html>"):
            with patch("app.services.job_import.detect_platform", side_effect=ValueError("Corrupt platform data")):
                result = _scrape_and_import_job_sync(
                    str(job_import.id),
                    "https://boards.greenhouse.io/acme/jobs/invalid_parse",
                    "url",
                    str(test_user.id),
                )

        assert result["status"] == "failed"

        db.refresh(job_import)
        assert job_import.status == "failed"
        assert job_import.processed_at is not None
        assert "Corrupt platform data" in str(job_import.errors)

    def test_no_jobs_found_marks_import_failed(self, db, test_user):
        """An import that yields zero jobs marks JobImport as failed."""
        job_import = JobImport(
            user_id=test_user.id,
            source="csv",
            status="processing",
            source_data="invalid",
        )
        db.add(job_import)
        db.commit()

        with patch("app.services.job_import.parse_job_csv", return_value=[]):
            result = _scrape_and_import_job_sync(
                str(job_import.id),
                "",
                "csv",
                str(test_user.id),
            )

        assert result["status"] == "failed"
        db.refresh(job_import)
        assert job_import.status == "failed"
        assert job_import.processed_at is not None

    def test_soft_timeout_marks_import_failed(self, db, test_user):
        """Celery SoftTimeLimitExceeded is caught and marks JobImport as failed in DB."""
        job_import = JobImport(
            user_id=test_user.id,
            source="url",
            status="processing",
            source_data="https://boards.greenhouse.io/acme/jobs/timeout_test",
        )
        db.add(job_import)
        db.commit()

        # Call scrape_and_import_job with _scrape_and_import_job_sync raising SoftTimeLimitExceeded
        with patch(
            "app.worker.tasks.scraping._scrape_and_import_job_sync",
            side_effect=SoftTimeLimitExceeded(),
        ):
            res = scrape_and_import_job(
                str(job_import.id),
                "https://boards.greenhouse.io/acme/jobs/timeout_test",
                "url",
                str(test_user.id),
            )

        assert res["status"] == "failed"
        assert res["error"] == "Scraping timed out"

        db.refresh(job_import)
        assert job_import.status == "failed"
        assert job_import.error == "Scraping timed out"
        assert job_import.processed_at is not None

    def test_scrape_and_import_retry_does_not_create_duplicate_jobs(self, db, test_user):
        """Simulated worker retry does not create duplicate Job records."""
        html = _load_fixture("greenhouse_job.html")
        url = "https://boards.greenhouse.io/acme/jobs/idempotency_test"

        # Attempt 1
        import_1 = JobImport(user_id=test_user.id, source="url", status="processing")
        db.add(import_1)
        db.commit()

        with patch("app.services.job_import.fetch_job_html", return_value=html):
            res1 = _scrape_and_import_job_sync(str(import_1.id), url, "url", str(test_user.id))
        assert res1["status"] == "completed"

        jobs_count_1 = db.query(Job).filter(Job.url == url).count()
        assert jobs_count_1 == 1

        # Attempt 2 (Retry / Second import with same URL)
        import_2 = JobImport(user_id=test_user.id, source="url", status="processing")
        db.add(import_2)
        db.commit()

        with patch("app.services.job_import.fetch_job_html", return_value=html):
            res2 = _scrape_and_import_job_sync(str(import_2.id), url, "url", str(test_user.id))

        jobs_count_2 = db.query(Job).filter(Job.url == url).count()
        assert jobs_count_2 == 1  # Still exactly 1 Job row

        items_2 = db.query(JobImportItem).filter(JobImportItem.import_id == import_2.id).all()
        assert len(items_2) == 1
        assert items_2[0].status == "duplicate"

    def test_partial_success_behavior(self, db, test_user):
        """Created jobs persist even when an exception occurs later in import processing."""
        job_import = JobImport(user_id=test_user.id, source="url", status="processing")
        db.add(job_import)
        db.commit()

        # Job is created and committed, then ScrapeHistory throws
        html = _load_fixture("greenhouse_job.html")
        with patch("app.services.job_import.fetch_job_html", return_value=html):
            with patch("app.services.job_import.ScrapeHistory", side_effect=IOError("Telemetry failure")):
                # Should not crash the import because logging failures are caught
                res = _scrape_and_import_job_sync(
                    str(job_import.id),
                    "https://boards.greenhouse.io/acme/jobs/partial_success_test",
                    "url",
                    str(test_user.id),
                )

        assert res["status"] == "completed"
        # Job exists
        created_job = db.query(Job).filter(Job.import_id == job_import.id).first()
        assert created_job is not None

    def test_database_commit_failure_handled(self, db, test_user):
        """A database commit failure in _scrape_and_import_job_sync rolls back cleanly and marks failure."""
        job_import = JobImport(user_id=test_user.id, source="url", status="processing")
        db.add(job_import)
        db.commit()

        # Patch Session.commit on the primary session to fail on second call
        original_commit = SessionLocal().commit
        call_count = [0]

        def flaky_commit(self):
            call_count[0] += 1
            if call_count[0] >= 2:
                raise RuntimeError("Database connection lost during commit")
            return original_commit()

        with patch("sqlalchemy.orm.Session.commit", flaky_commit):
            res = _scrape_and_import_job_sync(
                str(job_import.id),
                "https://boards.greenhouse.io/acme/jobs/commit_fail_test",
                "url",
                str(test_user.id),
            )

        assert res["status"] == "failed"


# ─── 3. Stuck Job Monitoring (Celery Beat) ──────────────────────────────────


class TestStuckJobDetector:
    """Verify detect_stuck_imports marks old processing jobs as failed."""

    def test_stuck_job_detector_finds_5min_old_processing_jobs(self, db, test_user):
        """Imports stuck in 'processing' for > 5 minutes are marked failed."""
        six_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=6)

        stuck_import = JobImport(
            user_id=test_user.id,
            source="url",
            status="processing",
            created_at=six_minutes_ago,
        )
        recent_import = JobImport(
            user_id=test_user.id,
            source="url",
            status="processing",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        db.add_all([stuck_import, recent_import])
        db.commit()

        # Run detector
        result = detect_stuck_imports()
        assert result["stuck_jobs_fixed"] >= 1

        db.refresh(stuck_import)
        db.refresh(recent_import)

        assert stuck_import.status == "failed"
        assert stuck_import.error == "Scraping job lost (worker timeout or crash)"
        assert stuck_import.processed_at is not None

        # Recent import should remain processing
        assert recent_import.status == "processing"

    def test_hard_timeout_recovered_by_stuck_detector(self, db, test_user):
        """A worker killed by SIGKILL (hard limit 90s) leaves status='processing', recovered after 5 min."""
        ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=10)

        killed_import = JobImport(
            user_id=test_user.id,
            source="url",
            status="processing",
            created_at=ten_minutes_ago,
        )
        db.add(killed_import)
        db.commit()

        detect_stuck_imports()

        db.refresh(killed_import)
        assert killed_import.status == "failed"
        assert killed_import.error == "Scraping job lost (worker timeout or crash)"


# ─── 4. Database Session Lifecycle ──────────────────────────────────────────


class TestSessionLifecycle:
    """Verify that worker tasks always close their database sessions."""

    def test_session_closed_on_success(self, db, test_user):
        """Worker task closes db session on success."""
        job_import = JobImport(user_id=test_user.id, source="url", status="processing")
        db.add(job_import)
        db.commit()

        html = _load_fixture("greenhouse_job.html")

        with patch("app.services.job_import.fetch_job_html", return_value=html):
            with patch("sqlalchemy.orm.Session.close", autospec=True) as mock_close:
                _scrape_and_import_job_sync(
                    str(job_import.id),
                    "https://boards.greenhouse.io/acme/jobs/session_test",
                    "url",
                    str(test_user.id),
                )

        assert mock_close.called

    def test_session_closed_on_error(self, db, test_user):
        """Worker task closes db session on error."""
        with patch("sqlalchemy.orm.Session.close", autospec=True) as mock_close:
            _scrape_and_import_job_sync(
                str(uuid.uuid4()),  # Nonexistent
                "https://boards.greenhouse.io/acme/jobs/session_err_test",
                "url",
                str(test_user.id),
            )

        assert mock_close.called

    def test_detect_stuck_imports_session_closed(self):
        """detect_stuck_imports closes its session in finally block."""
        with patch("sqlalchemy.orm.Session.close", autospec=True) as mock_close:
            detect_stuck_imports()

        assert mock_close.called
