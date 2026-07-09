"""Tests for Celery worker tasks (resume generation + PDF rendering)."""

import json
import os
import uuid
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
            content=json.dumps({
                "name": "Test User",
                "email": "test@example.com",
                "summary": "A developer.",
                "experience": [],
                "projects": [],
                "skills": ["Python"],
                "education": [],
            }),
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
            content=json.dumps({
                "name": "Test",
                "email": "t@e.com",
                "summary": "Dev",
                "experience": [],
                "projects": [],
                "skills": [],
                "education": [],
            }),
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
        with patch("app.worker.tasks.SessionLocal", return_value=mock_db), \
             patch("app.worker.tasks.celery_app.send_task", side_effect=ConnectionError("No broker")):
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

        with patch("app.worker.tasks.SessionLocal", return_value=mock_db), \
             patch("app.worker.tasks.celery_app.send_task", side_effect=ConnectionError("No broker")):
            enqueue_cover_letter_pdf_render(letter.id)

        assert letter.status == "completed"
        assert letter.pdf_url is not None
        if os.path.isfile(letter.pdf_url):
            os.remove(letter.pdf_url)
