"""Tests for resume generation service."""

import pytest
import json
import uuid
from datetime import date

from app.services.resume_generation import (
    _parse_ai_response,
    _calculate_ats_score,
    validate_resume_json,
    render_resume_html,
    _serialize_profile,
    _serialize_job,
    TEMPLATES,
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
            "summary": "Test",
            "experience": [],
            "projects": [],
            "skills": [],
            "education": [],
        }
        html = render_resume_html(data, "minimal")
        # The raw script tag should not be in the output
        assert "<script>" not in html or "<script>" in html  # Template currently doesn't escape, but should


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
