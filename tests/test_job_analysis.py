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
import uuid
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
