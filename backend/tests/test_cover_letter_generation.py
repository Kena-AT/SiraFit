"""Tests for cover letter generation service."""

import pytest
import uuid


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
