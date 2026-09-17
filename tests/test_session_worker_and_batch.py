"""
Tests for Session Import Celery Worker Tasks (Sprint 5).

Verifies async batch discovery, decoupled JobImportItem dispatching,
external_id deduplication, error handling, and stuck import detection.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import pytest

from app.models.job import Job, JobImport, JobImportItem
from app.services.session_management import store_user_session
from app.services.scraping.session_importer import (
    SavedJobsImporter,
    SavedJobReference,
    SessionExpiredError,
)
from app.worker.tasks.session_import import (
    import_saved_jobs_task,
    import_single_saved_job,
)
from app.worker.tasks.monitoring import detect_stuck_imports


def test_import_saved_jobs_task_missing_session(db, test_user):
    """Verify task marks import failed if session was deleted before execution."""
    job_import = JobImport(
        user_id=test_user.id,
        source="session_linkedin",
        status="processing",
    )
    db.add(job_import)
    db.commit()

    # Run discovery without saving a session in DB
    result = import_saved_jobs_task.run(
        user_id=str(test_user.id),
        import_id=str(job_import.id),
        platform="linkedin",
    )

    assert result["status"] == "failed"
    assert "unavailable or deleted" in result["error"]

    db.refresh(job_import)
    assert job_import.status == "failed"


def test_import_saved_jobs_task_expired_session(db, test_user):
    """Verify task marks import failed if scraper raises SessionExpiredError."""
    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
        session_data={"cookies": {"li_at": "bad_token"}},
    )
    job_import = JobImport(
        user_id=test_user.id,
        source="session_linkedin",
        status="processing",
    )
    db.add(job_import)
    db.commit()

    with patch.object(SavedJobsImporter, "fetch_saved_jobs_list") as mock_fetch:
        mock_fetch.side_effect = SessionExpiredError("Login required")
        result = import_saved_jobs_task.run(
            user_id=str(test_user.id),
            import_id=str(job_import.id),
            platform="linkedin",
        )

    assert result["status"] == "failed"
    assert "expired" in result["error"].lower()

    db.refresh(job_import)
    assert job_import.status == "failed"


def test_import_saved_jobs_task_empty_feed(db, test_user):
    """Verify task marks import completed_empty when feed is empty."""
    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
        session_data={"cookies": {"li_at": "token"}},
    )
    job_import = JobImport(
        user_id=test_user.id,
        source="session_linkedin",
        status="processing",
    )
    db.add(job_import)
    db.commit()

    with patch.object(SavedJobsImporter, "fetch_saved_jobs_list") as mock_fetch:
        mock_fetch.return_value = ([], "completed_empty")
        result = import_saved_jobs_task.run(
            user_id=str(test_user.id),
            import_id=str(job_import.id),
            platform="linkedin",
        )

    assert result["status"] == "completed_empty"
    assert result["discovered"] == 0

    db.refresh(job_import)
    assert job_import.status == "completed_empty"
    assert job_import.total_found == 0


def test_import_saved_jobs_task_discovery_and_batch_dispatch(db, test_user):
    """Verify discovery creates JobImportItem records and dispatches single job tasks."""
    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
        session_data={"cookies": {"li_at": "token"}},
    )
    job_import = JobImport(
        user_id=test_user.id,
        source="session_linkedin",
        status="processing",
    )
    db.add(job_import)
    db.commit()

    mock_refs = [
        SavedJobReference(url="https://www.linkedin.com/jobs/view/111", external_id="linkedin:111"),
        SavedJobReference(url="https://www.linkedin.com/jobs/view/222", external_id="linkedin:222"),
    ]

    with patch.object(SavedJobsImporter, "fetch_saved_jobs_list", return_value=(mock_refs, "completed")):
        with patch.object(import_single_saved_job, "delay") as mock_single_task:
            result = import_saved_jobs_task.run(
                user_id=str(test_user.id),
                import_id=str(job_import.id),
                platform="linkedin",
            )

    assert result["status"] == "queued_batch"
    assert result["discovered"] == 2
    assert mock_single_task.call_count == 2

    # Verify items persisted in DB in pending status
    items = db.query(JobImportItem).filter_by(import_id=job_import.id).all()
    assert len(items) == 2


def test_import_single_saved_job_success(db, test_user):
    """Verify single job item is fetched, parsed, and created in DB."""
    job_import = JobImport(
        user_id=test_user.id,
        source="session_linkedin",
        status="queued_batch",
        total_found=1,
        ok_count=0,
        fail_count=0,
    )
    db.add(job_import)
    db.commit()

    import_item = JobImportItem(
        import_id=job_import.id,
        status="pending",
        title_guess="Senior Python Developer",
    )
    db.add(import_item)
    db.commit()

    mock_enriched = {
        "title": "Senior Python Developer",
        "company": "PyFirm",
        "location": "Chicago, IL",
        "description": "Full job description with Python and FastAPI.",
    }

    with patch("app.worker.tasks.session_import.fetch_job_html", return_value="<html>job</html>"):
        with patch("app.worker.tasks.session_import.parse_job_html", return_value=mock_enriched):
            result = import_single_saved_job.run(
                item_id=str(import_item.id),
                import_id=str(job_import.id),
                url="https://www.linkedin.com/jobs/view/333",
                external_id="linkedin:333",
                user_id=str(test_user.id),
            )

    assert result["status"] == "imported"
    assert result["job_id"] is not None

    # Verify Job record created
    job = db.query(Job).filter_by(external_id="linkedin:333").first()
    assert job is not None
    assert job.title == "Senior Python Developer"
    assert job.company == "PyFirm"

    # Verify item status updated
    db.refresh(import_item)
    assert import_item.status == "imported"
    assert import_item.job_id == job.id

    # Verify JobImport completed
    db.refresh(job_import)
    assert job_import.status == "completed"
    assert job_import.ok_count == 1


def test_import_single_saved_job_deduplication(db, test_user):
    """Verify if job with external_id exists, duplicate job is skipped."""
    existing_job = Job(
        title="Existing Engineer",
        company="OldCo",
        external_id="linkedin:444",
        description="Already imported",
    )
    db.add(existing_job)

    job_import = JobImport(
        user_id=test_user.id,
        source="session_linkedin",
        status="queued_batch",
        total_found=1,
        ok_count=0,
        fail_count=0,
    )
    db.add(job_import)
    db.commit()

    import_item = JobImportItem(
        import_id=job_import.id,
        status="pending",
        title_guess="Existing Engineer",
    )
    db.add(import_item)
    db.commit()

    result = import_single_saved_job.run(
        item_id=str(import_item.id),
        import_id=str(job_import.id),
        url="https://www.linkedin.com/jobs/view/444",
        external_id="linkedin:444",
        user_id=str(test_user.id),
    )

    assert result["status"] == "duplicate"
    assert result["job_id"] == str(existing_job.id)

    # Total jobs with this external_id remains 1
    total = db.query(Job).filter_by(external_id="linkedin:444").count()
    assert total == 1

    db.refresh(import_item)
    assert import_item.status == "duplicate"
    assert import_item.job_id == existing_job.id


def test_detect_stuck_imports_handles_queued_batch(db, test_user):
    """Verify detect_stuck_imports identifies stale queued_batch imports."""
    stale_time = datetime.now(timezone.utc) - timedelta(hours=3)

    job_import = JobImport(
        user_id=test_user.id,
        source="session_linkedin",
        status="queued_batch",
        created_at=stale_time,
        updated_at=stale_time,
    )
    db.add(job_import)
    db.commit()

    result = detect_stuck_imports.run()
    assert result["stuck_jobs_fixed"] >= 1

    db.refresh(job_import)
    assert job_import.status == "failed"
    assert "timeout or crash" in (job_import.error or "")
