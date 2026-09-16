"""Unit and integration tests for JobImportItem tracking and import isolation.

Sprint 3 requirement:
- JobImportItem is the durable source of truth for import results.
- New jobs create JobImportItem(status="imported") linked to the job.
- Duplicate imports create JobImportItem(status="duplicate") linked to existing job.
- Failed imports create JobImportItem(status="failed") with error_message.
- Rapid sequential imports within the same minute remain strictly isolated.
"""

import os
import sys
import uuid
import pytest
from unittest.mock import patch

_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from app.services.job_import import process_import
from app.models.job import Job, JobImport, JobImportItem

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> str:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class TestJobImportItems:
    """Test durable per-item tracking."""

    def test_new_job_creates_imported_item(self, db, test_user):
        """A new job creates a JobImportItem with status='imported'."""
        html = _load_fixture("greenhouse_job.html")

        with patch("app.services.job_import.fetch_job_html", return_value=html):
            import_record, jobs_data, errors, _ = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/acme/jobs/12345",
            )

        items = db.query(JobImportItem).filter(JobImportItem.import_id == import_record.id).all()
        assert len(items) == 1
        assert items[0].status == "imported"
        assert items[0].job_id is not None
        assert items[0].title_guess is not None

        # Verify job is linked
        job = db.query(Job).filter(Job.id == items[0].job_id).first()
        assert job is not None
        assert job.import_id == import_record.id

    def test_duplicate_job_creates_duplicate_item(self, db, test_user):
        """Re-importing an existing job creates JobImportItem with status='duplicate' linked to existing job."""
        html = _load_fixture("greenhouse_job.html")

        with patch("app.services.job_import.fetch_job_html", return_value=html):
            import_1, _, _, _ = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/acme/jobs/12345",
            )

        existing_job = db.query(Job).filter(Job.import_id == import_1.id).first()
        assert existing_job is not None

        # Import again
        with patch("app.services.job_import.fetch_job_html", return_value=html):
            import_2, _, _, _ = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/acme/jobs/12345",
            )

        items_2 = db.query(JobImportItem).filter(JobImportItem.import_id == import_2.id).all()
        assert len(items_2) == 1
        assert items_2[0].status == "duplicate"
        assert items_2[0].job_id == existing_job.id

    def test_failed_import_creates_failed_item(self, db, test_user):
        """A failed import creates JobImportItem with status='failed' and error_message."""
        with patch("app.services.job_import.detect_platform", side_effect=RuntimeError("Parsing crash")):
            import_record, _, errors, _ = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/acme/jobs/fail_url",
            )

        assert import_record.status == "failed"
        items = db.query(JobImportItem).filter(JobImportItem.import_id == import_record.id).all()
        assert len(items) == 1
        assert items[0].status == "failed"
        assert "Parsing crash" in items[0].error_message
        assert items[0].job_id is None

    def test_import_isolation_concurrent_timestamp(self, db, test_user):
        """Two imports performed in rapid succession have isolated items and never cross-contaminate."""
        html_greenhouse = _load_fixture("greenhouse_job.html")
        html_lever = _load_fixture("lever_job.html")

        # Import A
        with patch("app.services.job_import.fetch_job_html", return_value=html_greenhouse):
            import_a, _, _, _ = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/companyA/jobs/111",
            )

        # Import B immediately after (same second/minute window)
        with patch("app.services.job_import.fetch_job_html", return_value=html_lever):
            import_b, _, _, _ = process_import(
                db,
                test_user.id,
                "url",
                "https://jobs.lever.co/companyB/222",
            )

        # Query items for A
        items_a = db.query(JobImportItem).filter(JobImportItem.import_id == import_a.id).all()
        # Query items for B
        items_b = db.query(JobImportItem).filter(JobImportItem.import_id == import_b.id).all()

        assert len(items_a) == 1
        assert len(items_b) == 1
        assert items_a[0].id != items_b[0].id
        assert items_a[0].job_id != items_b[0].job_id

        # Verify API detail response for A does not contain B's jobs
        from app.api.jobs import _import_detail_response
        detail_a = _import_detail_response(db, import_a)
        detail_b = _import_detail_response(db, import_b)

        job_ids_in_a = {j.id for j in detail_a.jobs}
        job_ids_in_b = {j.id for j in detail_b.jobs}

        assert not (job_ids_in_a & job_ids_in_b)
        assert str(items_a[0].job_id) in job_ids_in_a
        assert str(items_b[0].job_id) in job_ids_in_b
