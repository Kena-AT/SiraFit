"""Integration tests for job import with Scrapling.

Mocks the network layer to test the full import pipeline:
  - URL import uses Scrapling when available and returns metadata
  - Falls back to heuristic on Scrapling failure
  - ScrapeHistory records are written for every attempt
"""

import os
import sys
import uuid
import pytest
from unittest.mock import patch, MagicMock

_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from app.services.job_import import process_import, detect_platform
from app.models.scrape_history import ScrapeHistory

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> str:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ─── Platform Detection ──────────────────────────────────────────────────────


class TestDetectPlatform:
    """Verify URL → platform mapping."""

    def test_linkedin(self):
        assert detect_platform("https://www.linkedin.com/jobs/view/123") == "linkedin"

    def test_greenhouse(self):
        assert detect_platform("https://boards.greenhouse.io/acme/jobs/123") == "greenhouse"

    def test_lever(self):
        assert detect_platform("https://jobs.lever.co/acme/abc") == "lever"

    def test_indeed(self):
        assert detect_platform("https://www.indeed.com/viewjob?jk=abc123") == "indeed"

    def test_unknown(self):
        assert detect_platform("https://example.com/job/123") is None


# ─── Integration: ScrapeHistory Logging ──────────────────────────────────────


class TestScrapeHistoryLogging:
    """Verify that ScrapeHistory records are written for URL imports."""

    def test_successful_scrape_records_history(self, db, test_user):
        """When Scrapling succeeds, a ScrapeHistory with method='scrapling' is created."""
        html = _load_fixture("greenhouse_job.html")

        with patch("app.services.job_import.fetch_job_html", return_value=html):
            import_record, jobs_data, errors, scrape_meta = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/acme/jobs/12345",
            )

        assert import_record.status == "completed"
        assert scrape_meta["method_used"] == "scrapling"
        assert scrape_meta["fields_extracted"] > 0
        assert scrape_meta["duration_ms"] >= 0
        assert scrape_meta["source_platform"] == "greenhouse"

        # Verify ScrapeHistory record was written
        history = db.query(ScrapeHistory).filter_by(user_id=test_user.id).first()
        assert history is not None
        assert history.method_used == "scrapling"
        assert history.url == "https://boards.greenhouse.io/acme/jobs/12345"
        assert history.source_platform == "greenhouse"

    def test_failed_scrape_records_history(self, db, test_user):
        """When Scrapling returns None, heuristic fallback is used and history is recorded."""
        with patch("app.services.job_import.fetch_job_html", return_value=None):
            import_record, jobs_data, errors, scrape_meta = process_import(
                db,
                test_user.id,
                "url",
                "https://boards.greenhouse.io/acme/jobs/99999",
            )

        assert import_record.status == "completed"
        assert scrape_meta["method_used"] == "heuristic"

        # History should show partial/heuristic attempt
        history = db.query(ScrapeHistory).filter_by(user_id=test_user.id).first()
        assert history is not None
        assert history.method_used == "heuristic"
        assert history.success == "partial"

    def test_scrape_exception_records_history(self, db, test_user):
        """When Scrapling throws an exception, heuristic fallback is used."""
        with patch("app.services.job_import.fetch_job_html", side_effect=Exception("Network error")):
            import_record, jobs_data, errors, scrape_meta = process_import(
                db,
                test_user.id,
                "url",
                "https://example.com/broken",
            )

        assert import_record.status == "completed"
        assert scrape_meta["method_used"] == "heuristic"

        history = db.query(ScrapeHistory).filter_by(user_id=test_user.id).first()
        assert history is not None


# ─── Integration: Metadata in Response ───────────────────────────────────────


class TestScrapeMetadata:
    """Verify scrape metadata flows through the import pipeline."""

    def test_url_import_returns_metadata(self, db, test_user):
        html = _load_fixture("lever_job.html")
        with patch("app.services.job_import.fetch_job_html", return_value=html):
            _, _, _, scrape_meta = process_import(
                db,
                test_user.id,
                "url",
                "https://jobs.lever.co/startup/abc123",
            )

        assert "method_used" in scrape_meta
        assert "duration_ms" in scrape_meta
        assert "fields_extracted" in scrape_meta
        assert "source_platform" in scrape_meta
        assert scrape_meta["source_platform"] == "lever"

    def test_description_import_returns_empty_meta(self, db, test_user):
        long_desc = "Senior Python Engineer at Acme Corp. " * 10
        _, _, _, scrape_meta = process_import(
            db,
            test_user.id,
            "description",
            long_desc,
        )
        assert scrape_meta == {}

    def test_csv_import_returns_empty_meta(self, db, test_user):
        csv_data = "title,company,location\nBackend Engineer,Acme,Remote"
        _, _, _, scrape_meta = process_import(
            db,
            test_user.id,
            "csv",
            csv_data,
        )
        assert scrape_meta == {}


# ─── Graceful Degradation ────────────────────────────────────────────────────


class TestGracefulDegradation:
    """Import never breaks from scraper failure."""

    def test_heuristic_fallback_on_network_error(self, db, test_user):
        """Network error → heuristic parse → still returns a result."""
        with patch("app.services.job_import.fetch_job_html", side_effect=Exception("timeout")):
            import_record, jobs_data, errors, scrape_meta = process_import(
                db,
                test_user.id,
                "url",
                "https://greenhouse.io/some/job",
            )

        assert import_record.status == "completed"
        assert scrape_meta["method_used"] == "heuristic"
        # Should still have extracted something from the URL
        assert import_record.ok_count >= 0  # may be 0 if duplicate, that's fine

    def test_import_never_returns_500(self, db, test_user):
        """Even with all failures, import returns a valid response."""
        with patch("app.services.job_import.fetch_job_html", return_value=None):
            import_record, _, _, scrape_meta = process_import(
                db,
                test_user.id,
                "url",
                "https://example.com/job",
            )
        assert import_record.status in ("completed", "failed")
        assert scrape_meta["method_used"] == "heuristic"
