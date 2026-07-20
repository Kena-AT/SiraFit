# ========================================
# FROM FILE: test_job_import.py
# ========================================

"""
Tests for the job import system — service layer and API endpoints.
"""

import uuid


class TestImportService:
    """Direct tests of the import service functions."""

    def test_parse_job_from_url_linkedin(self):
        from app.services.job_import import parse_job_from_url

        url = "https://www.linkedin.com/jobs/view/1234567890"
        result = parse_job_from_url(url)
        assert result["source"] == "linkedin"
        assert result["external_id"] == "1234567890"
        assert "linkedin" in result["tags"]

    def test_parse_job_from_url_indeed(self):
        from app.services.job_import import parse_job_from_url

        url = "https://www.indeed.com/viewjob?jk=abc123def"
        result = parse_job_from_url(url)
        assert result["source"] == "indeed"
        assert result["external_id"] == "abc123def"

    def test_parse_job_from_url_unknown(self):
        from app.services.job_import import parse_job_from_url

        url = "https://example.com/jobs/some-position"
        result = parse_job_from_url(url)
        assert result["source"] == "url"
        assert result["title"] == "Some Position"

    def test_parse_job_from_description_basic(self):
        from app.services.job_import import parse_job_from_description

        desc = """Senior Software Engineer
        Company: Acme Corp
        Location: San Francisco, CA
        Salary: $150,000 - $200,000

        We are looking for a senior engineer with Python, React, and AWS experience.
        """
        result = parse_job_from_description(desc)
        assert "Senior" in result["title"]
        assert result["company"] == "Acme Corp"
        assert result["location"] == "San Francisco, CA"
        assert result["salary_min"] == 150000
        assert result["salary_max"] == 200000
        assert "python" in result["tags"]
        assert "react" in result["tags"]
        assert "aws" in result["tags"]

    def test_parse_job_from_description_short_fails(self):
        from app.services.job_import import parse_job_from_description

        desc = "Short text"
        result = parse_job_from_description(desc)
        assert result["title"] == "Unknown Position"

    def test_normalize_job(self):
        from app.services.job_import import normalize_job

        raw = {
            "title": "  senior engineer  ",
            "company": "at Acme Corp",
            "location": "  SF, CA  ",
            "description": "Python and React skills",
            "source": "description",
            "external_id": str(uuid.uuid4()),
        }
        result = normalize_job(raw)
        assert result["title"] == "Senior Engineer"
        assert result["company"] == "Acme Corp"
        assert result["location"] == "SF, CA"
        assert "python" in result["tags"]

    def test_check_duplicate_no_match(self, db, test_user):
        from app.services.job_import import check_duplicate

        job_data = {
            "title": "Software Engineer",
            "company": "Test Corp",
            "location": "Remote",
        }
        assert not check_duplicate(db, job_data)

    def test_check_duplicate_with_match(self, db, test_user):
        from app.services.job_import import check_duplicate
        from app.models.job import Job

        job = Job(
            external_id=str(uuid.uuid4()),
            title="Software Engineer",
            company="Test Corp",
            location="Remote",
        )
        db.add(job)
        db.commit()

        job_data = {
            "title": "Software Engineer",
            "company": "Test Corp",
            "location": "Remote",
        }
        assert check_duplicate(db, job_data)

    def test_detect_platform(self):
        from app.services.job_import import detect_platform

        assert detect_platform("https://linkedin.com/jobs/123") == "linkedin"
        assert detect_platform("https://indeed.com/viewjob") == "indeed"
        assert detect_platform("https://glassdoor.com/job") == "glassdoor"
        assert detect_platform("https://unknown.com/job") is None

    def test_extract_tags_from_text(self):
        from app.services.job_import import extract_tags_from_text

        text = "We use Python, React, and PostgreSQL in production."
        tags = extract_tags_from_text(text)
        assert "python" in tags
        assert "react" in tags
        assert "postgresql" in tags


class TestImportAPI:
    """Tests for the import API endpoints."""

    def test_import_url_unauthenticated(self, client):
        resp = client.post(
            "/api/v1/jobs/import",
            json={"source_type": "url", "data": "https://linkedin.com/jobs/view/123"},
        )
        assert resp.status_code == 401

    def test_import_url_success(self, client, auth_tokens):
        resp = client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={
                "source_type": "url",
                "data": "https://www.linkedin.com/jobs/view/123456",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "import_record" in data
        assert "jobs" in data
        assert "errors" in data
        assert data["import_record"]["status"] == "completed"
        assert data["import_record"]["source"] == "url"

    def test_import_description_success(self, client, auth_tokens):
        desc = """Backend Developer
        Company: DevCo
        Location: New York, NY
        Salary: $120,000 - $160,000

        We need a backend developer skilled in Python, PostgreSQL, and Docker.
        """
        resp = client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "description", "data": desc},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["import_record"]["status"] == "completed"
        assert len(data["jobs"]) == 1
        assert "Backend Developer" in data["jobs"][0]["title"]

    def test_import_description_too_short(self, client, auth_tokens):
        resp = client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "description", "data": "Too short"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["import_record"]["status"] == "failed"
        assert len(data["errors"]) > 0

    def test_import_history_unauthenticated(self, client):
        client.cookies.clear()
        resp = client.get("/api/v1/jobs/import/history")
        assert resp.status_code == 401

    def test_import_history_success(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/jobs/import/history",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_import_history_with_records(self, client, auth_tokens):
        # First, import a job
        client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "url", "data": "https://linkedin.com/jobs/view/999"},
        )
        # Then check history
        resp = client.get(
            "/api/v1/jobs/import/history",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["source"] == "url"
        assert data[0]["status"] == "completed"

    def test_import_detail_not_found(self, client, auth_tokens):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/jobs/import/{fake_id}",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 404

    def test_import_duplicate_detection(self, client, auth_tokens):
        url = "https://linkedin.com/jobs/view/duplicate-test"
        # First import
        client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "url", "data": url},
        )
        # Second import of same URL
        resp = client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "url", "data": url},
        )
        data = resp.json()
        assert data["import_record"]["status"] == "completed"


# ========================================
# FROM FILE: test_job_analysis.py
# ========================================

"""
Tests for Sprint 5: AI Job Analysis pipeline.

Covers:
  - AnalysisOutput schema validation (rejects bad/missing data)
  - Keyword fallback produces valid output
  - AI parsing helper strips markdown fences correctly
  - API: POST /jobs/{id}/analyze returns 200 with status=processing
  - API: GET /jobs/{id}/analysis returns stored data
  - API: 404 when no analysis exists
"""

import json
import pytest
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError

from app.services.ai import AnalysisOutput, _parse_and_validate, keyword_fallback


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestAnalysisOutputSchema:
    def test_valid_full_output(self):
        data = {
            "score": 82,
            "summary": "Strong backend candidate.",
            "pros": ["5 years Python", "Knows FastAPI"],
            "cons": ["No Kubernetes experience"],
            "skills_gap": ["Kubernetes", "Terraform"],
            "key_requirements": ["Python", "REST APIs"],
            "seniority": "Senior",
        }
        output = AnalysisOutput.model_validate(data)
        assert output.score == 82
        assert output.seniority == "Senior"

    def test_score_is_clamped_to_100(self):
        data = dict(score=150, summary="x", pros=[], cons=[], skills_gap=[])
        output = AnalysisOutput.model_validate(data)
        assert output.score == 100

    def test_score_is_clamped_to_0(self):
        data = dict(score=-20, summary="x", pros=[], cons=[], skills_gap=[])
        output = AnalysisOutput.model_validate(data)
        assert output.score == 0

    def test_lists_are_truncated_to_6(self):
        data = dict(
            score=50,
            summary="x",
            pros=["a", "b", "c", "d", "e", "f", "g", "h"],
            cons=[],
            skills_gap=[],
        )
        output = AnalysisOutput.model_validate(data)
        assert len(output.pros) == 6

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            AnalysisOutput.model_validate({"score": 50})

    def test_defaults_applied_for_optional_fields(self):
        data = dict(score=70, summary="test", pros=[], cons=[], skills_gap=[])
        output = AnalysisOutput.model_validate(data)
        assert output.key_requirements == []
        assert output.seniority == "Mid"


# ---------------------------------------------------------------------------
# JSON parsing helper
# ---------------------------------------------------------------------------


class TestParseAndValidate:
    def test_plain_json(self):
        text = json.dumps(
            {
                "score": 75,
                "summary": "Good fit",
                "pros": ["Python"],
                "cons": [],
                "skills_gap": [],
            }
        )
        result = _parse_and_validate(text)
        assert result.score == 75

    def test_markdown_fenced_json(self):
        text = '```json\n{"score": 60, "summary": "ok", "pros": [], "cons": [], "skills_gap": []}\n```'
        result = _parse_and_validate(text)
        assert result.score == 60

    def test_invalid_json_raises(self):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            _parse_and_validate("this is not json at all")

    def test_valid_json_wrong_schema_raises(self):
        with pytest.raises(ValidationError):
            _parse_and_validate('{"foo": "bar"}')


# ---------------------------------------------------------------------------
# Keyword fallback
# ---------------------------------------------------------------------------


class TestKeywordFallback:
    def test_fallback_returns_valid_output(self):
        result = keyword_fallback("Senior Python Engineer", "We need Python expertise")
        assert isinstance(result, AnalysisOutput)
        assert result.score == 0
        assert "AI integration not configured" in result.cons[0]

    def test_fallback_has_correct_structure(self):
        result = keyword_fallback("Data Scientist", "ML required")
        assert isinstance(result.pros, list)
        assert isinstance(result.cons, list)
        assert isinstance(result.skills_gap, list)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


class TestAnalysisAPI:
    def test_trigger_analysis_returns_processing_status(self, client, auth_headers, db):
        """POST /jobs/{id}/analyze should return immediately with status=processing or done."""
        from app.models.job import Job

        # Create a test job
        job = Job(
            external_id=f"test-{uuid.uuid4().hex[:8]}",
            title="Python Engineer",
            company="Acme",
            description="We need Python and FastAPI skills.",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        with patch(
            "app.services.job_analysis.run_job_analysis",
            new_callable=AsyncMock,
        ):
            response = client.post(
                f"/api/v1/jobs/{job.id}/analyze",
                headers=auth_headers,
                json={},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("processing", "done", "pending")
        assert "score" in data

    def test_get_analysis_404_when_missing(self, client, auth_headers, db):
        """GET /jobs/{id}/analysis should 404 when no analysis exists."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/jobs/{fake_id}/analysis",
            headers=auth_headers,
        )
        # 404 for job not found or analysis not found
        assert response.status_code in (404,)

    def test_get_analysis_returns_stored_data(self, client, auth_headers, db):
        """GET /jobs/{id}/analysis should return stored analysis."""
        from app.models.job import Job, JobAnalysis

        job = Job(
            external_id=f"test-{uuid.uuid4().hex[:8]}",
            title="DevOps Engineer",
            company="StackCo",
            description="Kubernetes and Terraform required.",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        analysis = JobAnalysis(
            job_id=job.id,
            score=77,
            summary="Good infrastructure candidate.",
            pros=["Kubernetes experience"],
            cons=["No Terraform"],
            skills_gap=["Terraform"],
            key_requirements=["Kubernetes", "CI/CD"],
            seniority="Mid",
            status="done",
            analysis_version="v1",
        )
        db.add(analysis)
        db.commit()

        response = client.get(
            f"/api/v1/jobs/{job.id}/analysis",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 77
        assert data["status"] == "done"
        assert data["seniority"] == "Mid"
        assert "Terraform" in data["skills_gap"]


# ========================================
# FROM FILE: test_job_match_score.py
# ========================================

from unittest.mock import MagicMock
from datetime import date
from app.models.job import Job
from app.models.profile import Profile, Experience, Education, Skill
from app.services.matching_engine import calculate_match_score, ScoringWeights


# ── Helpers ──


def _make_profile(
    skills: list[str] | None = None,
    experiences: int = 0,
    edu_years: int = 0,
    edu_degree: str = "",
) -> MagicMock:
    profile = MagicMock(spec=Profile)

    profile.skills = []
    if skills:
        for name in skills:
            s = MagicMock(spec=Skill)
            s.name = name
            profile.skills.append(s)

    profile.experiences = []
    for i in range(experiences):
        exp = MagicMock(spec=Experience)
        exp.start_date = date(2018, 1, 1)
        exp.end_date = date(2024, 6, 1)
        exp.is_current = False
        profile.experiences.append(exp)

    profile.educations = []
    if edu_years > 0:
        for _ in range(1):
            edu = MagicMock(spec=Education)
            edu.degree = edu_degree
            edu.start_date = date(2020, 9, 1)
            edu.end_date = date(2024, 6, 1)
            profile.educations.append(edu)

    return profile


def _make_job(tags: list[str] | None = None) -> MagicMock:
    job = MagicMock(spec=Job)
    job.title = "Engineer"
    job.company = "Acme"
    job.tags = tags or []
    return job


# ── Tests ──


class TestMatchingEngine:
    def test_perfect_match(self):
        profile = _make_profile(
            skills=["python", "fastapi", "docker"],
            experiences=3,
            edu_years=4,
            edu_degree="Bachelor",
        )
        job = _make_job(tags=["python", "fastapi", "docker"])
        result = calculate_match_score(profile, job)
        assert result["score"] >= 90
        assert result["breakdown"]["skills"] == 100

    def test_no_skills_match(self):
        profile = _make_profile(
            skills=["java"], experiences=1, edu_years=1, edu_degree="Bachelor"
        )
        job = _make_job(tags=["python", "fastapi", "docker"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["skills"] == 0
        assert result["score"] < 50

    def test_partial_skills_match(self):
        profile = _make_profile(
            skills=["python", "go"], experiences=1, edu_years=1, edu_degree="Bachelor"
        )
        job = _make_job(tags=["python", "fastapi", "docker", "kubernetes"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["skills"] == 25  # 1/4

    def test_no_job_tags(self):
        profile = _make_profile(skills=[], experiences=0, edu_years=0, edu_degree="")
        job = _make_job(tags=[])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["skills"] == 100  # no requirements = 100%

    def test_no_experience(self):
        profile = _make_profile(
            skills=["python"], experiences=0, edu_years=0, edu_degree=""
        )
        job = _make_job(tags=["python"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["experience"] == 20
        assert "no experience" in result["explanation"].lower()

    def test_no_education(self):
        profile = _make_profile(
            skills=["python"], experiences=1, edu_years=0, edu_degree=""
        )
        job = _make_job(tags=["python"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["education"] == 20

    def test_no_skills_and_no_experience_and_no_education(self):
        profile = _make_profile(skills=[], experiences=0, edu_years=0, edu_degree="")
        job = _make_job(tags=["python"])
        result = calculate_match_score(profile, job)
        assert result["score"] >= 0
        assert result["breakdown"]["skills"] == 0
        assert result["breakdown"]["experience"] == 20
        assert result["breakdown"]["education"] == 20

    def test_custom_weights(self):
        profile = _make_profile(
            skills=["python"], experiences=1, edu_years=1, edu_degree="Bachelor"
        )
        job = _make_job(tags=["python"])
        weights = ScoringWeights(
            skills_weight=1.0, experience_weight=0.0, education_weight=0.0
        )
        result = calculate_match_score(profile, job, weights=weights)
        assert result["score"] == result["breakdown"]["skills"]  # only skills matters

    def test_invalid_weights_raises(self):
        profile = _make_profile(skills=[], experiences=0, edu_years=0, edu_degree="")
        job = _make_job(tags=[])
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            calculate_match_score(profile, job, weights=ScoringWeights(0.5, 0.5, 0.5))

    def test_case_insensitive_skill_matching(self):
        profile = _make_profile(skills=["Python", "FastAPI"])
        job = _make_job(tags=["python", "fastapi"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["skills"] == 100

    def test_explanation_contains_all_dimensions(self):
        profile = _make_profile(
            skills=["python"], experiences=1, edu_years=1, edu_degree="Bachelor"
        )
        job = _make_job(tags=["python"])
        result = calculate_match_score(profile, job)
        expl = result["explanation"]
        assert "skills" in expl
        assert "experience" in expl
        assert "education" in expl


# ========================================
# FROM FILE: test_job_search.py
# ========================================

"""
Tests for job search, filtering, sorting, and pagination.
"""


class TestJobSearch:
    """Tests for job search functionality."""

    def test_search_by_title(self, client, auth_tokens, db):
        # Create test jobs
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Senior Python Engineer",
            company="TechCorp",
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Java Developer",
            company="DevCo",
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?search=Python",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any("Python" in job["title"] for job in data["jobs"])

    def test_search_by_company(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="Software Engineer",
            company="Unique Company Name",
            source="url",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?search=Unique Company",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any("Unique Company" in job["company"] for job in data["jobs"])

    def test_search_by_description(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="Developer",
            company="TestCo",
            description="We need someone with Kubernetes and Docker experience",
            source="lever",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?search=Kubernetes",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_case_insensitive(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="React Developer",
            company="Frontend Inc",
            source="greenhouse",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?search=react",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_no_results(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/jobs?search=nonexistentxyzabc123",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert len(data["jobs"]) == 0


class TestJobFiltering:
    """Tests for job filtering functionality."""

    def test_filter_by_company(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Engineer A",
            company="FilterTestCo",
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Engineer B",
            company="OtherCo",
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?company=FilterTestCo",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all("FilterTestCo" in job["company"] for job in data["jobs"])

    def test_filter_by_location(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Remote Engineer",
            company="RemoteCo",
            location="San Francisco, CA",
            source="lever",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Onsite Engineer",
            company="OnsiteCo",
            location="New York, NY",
            source="greenhouse",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?location=San Francisco",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all("San Francisco" in (job["location"] or "") for job in data["jobs"])

    def test_filter_by_source(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="LinkedIn Job",
            company="LinkedInCo",
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Indeed Job",
            company="IndeedCo",
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?source=linkedin",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(job["source"] == "linkedin" for job in data["jobs"])

    def test_filter_by_tags(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Python Developer",
            company="PythonCo",
            tags=["python", "django", "postgresql"],
            source="url",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="JS Developer",
            company="JSCo",
            tags=["javascript", "react"],
            source="url",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?tags=python",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all("python" in job["tags"] for job in data["jobs"])

    def test_filter_by_multiple_tags(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="Full Stack Developer",
            company="FullStackCo",
            tags=["python", "react", "postgresql"],
            source="lever",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?tags=python,react",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(
            "python" in job["tags"] and "react" in job["tags"] for job in data["jobs"]
        )

    def test_filter_by_min_salary(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="High Paying Job",
            company="HighPayCo",
            salary_min=150000,
            salary_max=200000,
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Low Paying Job",
            company="LowPayCo",
            salary_min=50000,
            salary_max=70000,
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?min_salary=100000",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for job in data["jobs"]:
            assert (job["salary_min"] and job["salary_min"] >= 100000) or (
                job["salary_max"] and job["salary_max"] >= 100000
            )

    def test_filter_by_max_salary(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Mid Paying Job",
            company="MidPayCo",
            salary_min=80000,
            salary_max=100000,
            source="greenhouse",
        )
        db.add(job1)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?max_salary=120000",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for job in data["jobs"]:
            if job["salary_max"]:
                assert job["salary_max"] <= 120000 or job["salary_min"] <= 120000

    def test_combined_filters(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="Senior Python Engineer",
            company="TestCorp",
            location="Remote",
            tags=["python", "aws"],
            salary_min=120000,
            salary_max=180000,
            source="lever",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?company=TestCorp&location=Remote&tags=python&source=lever",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestJobSorting:
    """Tests for job sorting functionality."""

    def test_sort_by_created_at_desc(self, client, auth_tokens, db):
        # Jobs are created in sequence, newest should be first
        resp = client.get(
            "/api/v1/jobs?sort_by=created_at&sort_order=desc",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data["jobs"]) > 1:
            dates = [job["created_at"] for job in data["jobs"]]
            assert dates == sorted(dates, reverse=True)

    def test_sort_by_created_at_asc(self, client, auth_tokens, db):
        resp = client.get(
            "/api/v1/jobs?sort_by=created_at&sort_order=asc",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data["jobs"]) > 1:
            dates = [job["created_at"] for job in data["jobs"]]
            assert dates == sorted(dates)

    def test_sort_by_company_asc(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Job A",
            company="Zebra Corp",
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Job B",
            company="Apple Corp",
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?sort_by=company&sort_order=asc",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data["jobs"]) > 1:
            companies = [job["company"] for job in data["jobs"]]
            assert companies == sorted(companies)

    def test_sort_by_title_desc(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="A Engineer",
            company="TestCo",
            source="lever",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Z Engineer",
            company="TestCo",
            source="greenhouse",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?sort_by=title&sort_order=desc",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data["jobs"]) > 1:
            titles = [job["title"] for job in data["jobs"]]
            assert titles == sorted(titles, reverse=True)


class TestJobPagination:
    """Tests for job pagination functionality."""

    def test_pagination_first_page(self, client, auth_tokens, db):
        # Create 10 jobs
        for i in range(10):
            job = Job(
                external_id=str(uuid.uuid4()),
                title=f"Job {i}",
                company=f"Company {i}",
                source="url",
            )
            db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?skip=0&limit=5",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["jobs"]) <= 5
        assert data["skip"] == 0
        assert data["limit"] == 5
        assert data["total"] >= 10

    def test_pagination_second_page(self, client, auth_tokens, db):
        resp = client.get(
            "/api/v1/jobs?skip=5&limit=5",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["skip"] == 5
        assert data["limit"] == 5

    def test_pagination_limit_validation(self, client, auth_tokens):
        # Test max limit
        resp = client.get(
            "/api/v1/jobs?limit=600",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 422  # Validation error

    def test_pagination_skip_validation(self, client, auth_tokens):
        # Test negative skip
        resp = client.get(
            "/api/v1/jobs?skip=-1",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 422  # Validation error

    def test_empty_page(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/jobs?skip=10000&limit=10",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["jobs"]) == 0
        assert data["skip"] == 10000


class TestJobListResponse:
    """Tests for job list response structure."""

    def test_response_structure(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "jobs" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["jobs"], list)
        assert isinstance(data["total"], int)

    def test_job_response_fields(self, client, auth_tokens, db):
        job = Job(
            external_id="test-external-id",
            title="Test Job",
            company="Test Company",
            location="Test Location",
            description="Test description",
            salary_min=100000,
            salary_max=150000,
            currency="USD",
            tags=["test", "python"],
            url="https://example.com/job",
            source="test",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?limit=1",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()

        if len(data["jobs"]) > 0:
            job_data = data["jobs"][0]
            assert "id" in job_data
            assert "external_id" in job_data
            assert "title" in job_data
            assert "company" in job_data
            assert "created_at" in job_data
            assert "updated_at" in job_data

    def test_unauthenticated_access(self, client):
        # The shared session-scoped client may carry an auth cookie from the
        # login fixture; swap in a fresh empty cookie jar (and restore it)
        # so this request is truly unauthenticated.
        import httpx

        saved = client.cookies
        client.cookies = httpx.Cookies()
        try:
            resp = client.get("/api/v1/jobs")
        finally:
            client.cookies = saved
        assert resp.status_code == 401
