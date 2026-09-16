"""Unit and API tests for Job deletion, archive/unarchive, and cascade lifecycle.

Sprint 3 requirements:
- DELETE /jobs/{job_id} returns 204 No Content.
- Deleting a job sets JobImportItem.job_id to NULL.
- Deleting a job removes dependent analysis/score rows.
- Deleting non-existent job returns 404.
- Archive / unarchive updates is_archived without deleting the job.
"""

import os
import sys
import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from app.main import app
from app.services.job_import import process_import
from app.models.job import Job, JobImport, JobImportItem, JobAnalysis
from app.models.score import JobMatchScore
from app.api.users import get_current_user
from app.core.database import get_db

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


class TestJobLifecycle:
    """Verify delete and archive endpoints."""

    def test_delete_job_returns_204(self, client, db, test_user):
        """DELETE /api/v1/jobs/{id} returns 204 and removes the job."""
        html = _load_fixture("greenhouse_job.html")

        with patch("app.services.job_import.fetch_job_html", return_value=html):
            import_record, _, _, _ = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/acme/jobs/delete_test",
            )

        job = db.query(Job).filter(Job.import_id == import_record.id).first()
        assert job is not None
        job_id = str(job.id)

        # Add dummy analysis and score records
        db.add(JobAnalysis(job_id=job.id, status="done", score=85))
        db.add(JobMatchScore(user_id=test_user.id, job_id=job.id, score=90, breakdown={}))
        db.commit()

        # Delete job via API
        resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 204

        # Verify job is gone
        assert db.query(Job).filter(Job.id == uuid.UUID(job_id)).first() is None

        # Verify dependent records are cleaned up
        assert db.query(JobAnalysis).filter(JobAnalysis.job_id == uuid.UUID(job_id)).first() is None
        assert db.query(JobMatchScore).filter(JobMatchScore.job_id == uuid.UUID(job_id)).first() is None

        # Verify JobImportItem.job_id was set to NULL
        item = db.query(JobImportItem).filter(JobImportItem.import_id == import_record.id).first()
        assert item is not None
        assert item.job_id is None

    def test_delete_nonexistent_job_returns_404(self, client):
        """Deleting a non-existent job returns 404."""
        random_id = str(uuid.uuid4())
        resp = client.delete(f"/api/v1/jobs/{random_id}")
        assert resp.status_code == 404

    def test_archive_and_unarchive_job(self, client, db, test_user):
        """POST /api/v1/jobs/{id}/archive toggles is_archived without deleting."""
        html = _load_fixture("greenhouse_job.html")

        with patch("app.services.job_import.fetch_job_html", return_value=html):
            import_record, _, _, _ = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/acme/jobs/archive_test",
            )

        job = db.query(Job).filter(Job.import_id == import_record.id).first()
        assert job is not None
        job_id = str(job.id)
        assert job.is_archived is False

        # Archive
        resp = client.post(f"/api/v1/jobs/{job_id}/archive", json={"archived": True})
        assert resp.status_code == 200
        db.refresh(job)
        assert job.is_archived is True

        # Unarchive
        resp = client.post(f"/api/v1/jobs/{job_id}/archive", json={"archived": False})
        assert resp.status_code == 200
        db.refresh(job)
        assert job.is_archived is False
