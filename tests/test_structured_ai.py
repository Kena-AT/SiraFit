"""Unit tests for Structured AI Adapter, Schemas, Telemetry, and Call Sites (Sprint 7)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import BaseModel, Field, ValidationError

from app.schemas.ai_output import (
    AIJobAnalysisOutput,
    AIResumeOutput,
    AIResumeExperienceItem,
    AIResumeProjectItem,
    AIResumeEducationItem,
    AICoverLetterOutput,
)
from app.services.structured_ai import (
    classify_ai_exception,
    structured_completion_with_fallback,
)
from app.models.ai_completion import AICompletion, AICompletionAttempt


class SimpleSampleOutput(BaseModel):
    message: str
    count: int = Field(ge=0, le=10)


def test_classify_ai_exception():
    """Verify error classification into stable bounded categories."""
    assert classify_ai_exception(ValueError("Unknown error")) == "unknown"
    assert classify_ai_exception(Exception("Rate limit exceeded 429")) == "rate_limit"
    assert classify_ai_exception(Exception("Request timed out")) == "timeout"
    assert classify_ai_exception(Exception("401 Unauthorized invalid api key")) == "auth_error"
    assert classify_ai_exception(Exception("Invalid json schema format")) == "schema_error"

    try:
        SimpleSampleOutput(message="hi", count=50)
    except ValidationError as val_err:
        assert classify_ai_exception(val_err) == "validation_error"


def test_schema_validators_and_post_init():
    """Verify post-init clamping and trimming on AI output schemas."""
    job_out = AIJobAnalysisOutput(
        score=150,  # Clamped to 100
        summary="This candidate is a great match for the fullstack software engineering position.",
        pros=["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"],
        cons=["c1", "c2"],
        skills_gap=["s1"],
    )
    assert job_out.score == 100
    assert len(job_out.pros) == 6

    resume_out = AIResumeOutput(
        name="Jane Doe",
        email="jane@example.com",
        summary="A passionate software architect with more than ten years of production cloud experience.",
        skills=["python", "fastapi", "react", "python", "docker"],
    )
    assert len(resume_out.skills) == 4  # Duplicates removed

    cl_out = AICoverLetterOutput(
        body="I am writing to express my strong interest in the senior platform engineer role.",
        key_points=["Scalability", "Reliability"],
    )
    assert cl_out.salutation == "Dear Hiring Manager,"
    assert "senior platform engineer" in cl_out.body


@pytest.mark.asyncio
async def test_structured_completion_success(db, test_user):
    """Verify structured_completion_with_fallback succeeds on candidate 1 and writes telemetry."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_completions = MagicMock()
    mock_client.chat = mock_chat
    mock_chat.completions = mock_completions

    expected_output = AIJobAnalysisOutput(
        score=88,
        summary="Strong candidate with good overlap in python backend technologies and distributed systems.",
        pros=["Python mastery", "Cloud architecture"],
        cons=["Lacks Vue.js experience"],
        skills_gap=["Vue.js"],
        key_requirements=["Python", "Postgres"],
        seniority="Senior",
    )
    mock_completions.create = AsyncMock(return_value=expected_output)

    with patch("app.services.structured_ai.get_instructor_client", return_value=mock_client):
        candidates = [("openai", "gpt-4o-mini", "test-key-1")]
        messages = [{"role": "user", "content": "Analyze candidate"}]
        result, completion_rec = await structured_completion_with_fallback(
            operation="job_analysis",
            response_model=AIJobAnalysisOutput,
            messages=messages,
            candidates=candidates,
            db=db,
            user_id=test_user.id,
        )

    assert result.score == 88
    assert completion_rec is not None
    assert completion_rec.status == "success"
    assert completion_rec.provider == "openai"
    assert completion_rec.attempt_count == 1

    # Check attempt record in db
    attempts = db.query(AICompletionAttempt).filter_by(completion_id=completion_rec.id).all()
    assert len(attempts) == 1
    assert attempts[0].status == "success"


@pytest.mark.asyncio
async def test_structured_completion_candidate_fallback(db, test_user):
    """Verify fallback to second candidate when first candidate fails."""
    client_fail = MagicMock()
    client_fail.chat.completions.create = AsyncMock(side_effect=Exception("429 Too Many Requests"))

    expected_output = AICoverLetterOutput(
        salutation="Dear Team,",
        body="I am excited to apply for the DevOps Engineer position at Acme Corp with proven experience.",
        sign_off="Best regards,",
        key_points=["Kubernetes", "Terraform"],
    )
    client_success = MagicMock()
    client_success.chat.completions.create = AsyncMock(return_value=expected_output)

    def get_client_side_effect(provider, api_key):
        if provider == "gemini":
            return client_fail
        return client_success

    with patch("app.services.structured_ai.get_instructor_client", side_effect=get_client_side_effect):
        candidates = [
            ("gemini", "gemini-1.5-flash", "gemini-bad-key"),
            ("openrouter", "anthropic/claude-3-5-sonnet", "openrouter-good-key"),
        ]
        messages = [{"role": "user", "content": "Generate cover letter"}]

        result, completion_rec = await structured_completion_with_fallback(
            operation="cover_letter_generation",
            response_model=AICoverLetterOutput,
            messages=messages,
            candidates=candidates,
            db=db,
            user_id=test_user.id,
        )

    assert "DevOps Engineer" in result.body
    assert completion_rec is not None
    assert completion_rec.status == "fallback"
    assert completion_rec.provider == "openrouter"
    assert completion_rec.attempt_count == 2

    attempts = db.query(AICompletionAttempt).filter_by(completion_id=completion_rec.id).order_by(AICompletionAttempt.attempt_number).all()
    assert len(attempts) == 2
    assert attempts[0].provider == "gemini"
    assert attempts[0].status == "failed"
    assert attempts[0].failure_code == "rate_limit"
    assert attempts[1].provider == "openrouter"
    assert attempts[1].status == "success"


@pytest.mark.asyncio
async def test_telemetry_db_error_isolation(test_user):
    """Verify telemetry database error does not fail the AI generation (Issue #53)."""
    mock_client = MagicMock()
    expected_output = AIJobAnalysisOutput(
        score=75,
        summary="Competent mid-level developer meeting baseline technical requirements.",
        pros=["Fast learner"],
        cons=["Limited experience"],
    )
    mock_client.chat.completions.create = AsyncMock(return_value=expected_output)

    # Broken DB session mock that throws on flush/commit
    broken_db = MagicMock()
    broken_db.flush.side_effect = RuntimeError("DB connection dropped")

    with patch("app.services.structured_ai.get_instructor_client", return_value=mock_client):
        candidates = [("mistral", "mistral-large-latest", "mistral-key")]
        messages = [{"role": "user", "content": "test"}]

        result, completion_rec = await structured_completion_with_fallback(
            operation="job_analysis",
            response_model=AIJobAnalysisOutput,
            messages=messages,
            candidates=candidates,
            db=broken_db,
            user_id=test_user.id,
        )

    # Output is still delivered despite DB telemetry error!
    assert result.score == 75
    assert completion_rec is None


@pytest.mark.asyncio
async def test_structured_completion_all_candidates_exhausted(db, test_user):
    """Verify RuntimeError when all candidate providers fail."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API connection error"))

    with patch("app.services.structured_ai.get_instructor_client", return_value=mock_client):
        candidates = [
            ("openai", "gpt-4o-mini", "key1"),
            ("anthropic", "claude-3-5-sonnet", "key2"),
        ]
        messages = [{"role": "user", "content": "test"}]

        with pytest.raises(Exception) as excinfo:
            await structured_completion_with_fallback(
                operation="job_analysis",
                response_model=AIJobAnalysisOutput,
                messages=messages,
                candidates=candidates,
                db=db,
                user_id=test_user.id,
            )
        assert "API connection error" in str(excinfo.value)

    # Verify a failed completion record was created in DB
    failed_comp = db.query(AICompletion).filter_by(status="failed").order_by(AICompletion.created_at.desc()).first()
    assert failed_comp is not None
    assert failed_comp.attempt_count == 2


@pytest.mark.asyncio
async def test_analyze_job_with_fallback_uses_structured():
    """Verify analyze_job_with_fallback integrates structured completion."""
    from app.services.ai import analyze_job_with_fallback

    mock_out = AIJobAnalysisOutput(
        score=92,
        summary="Exceptional fit for backend engineering position.",
        pros=["Python", "FastAPI"],
        cons=[],
        skills_gap=[],
    )

    with patch(
        "app.services.structured_ai.structured_completion_with_fallback",
        new=AsyncMock(return_value=(mock_out, None)),
    ) as mock_struct:
        res = await analyze_job_with_fallback(
            prompt_context="Job and candidate details",
            candidates=[("openrouter", "openai/gpt-4o-mini", "fake-key")],
        )

    assert mock_struct.await_count == 1
    assert res.score == 92
    assert "Exceptional fit" in res.summary


@pytest.mark.asyncio
async def test_generate_cover_letter_uses_structured(db, test_user):
    """Verify generate_cover_letter uses structured generation and returns formatted text."""
    from app.services.cover_letter_generation import generate_cover_letter
    from app.models.profile import Profile
    from app.models.job import Job

    profile = Profile(user_id=test_user.id, first_name="Alex", last_name="Mercer")
    job = Job(title="DevOps Lead", company="TechCorp", description="Need a lead")

    mock_cl = AICoverLetterOutput(
        salutation="Dear Hiring Team,",
        body="I am thrilled to apply for the DevOps Lead position at TechCorp.",
        sign_off="Sincerely,\nAlex Mercer",
        key_points=["CI/CD", "Docker"],
    )

    with patch(
        "app.services.structured_ai.structured_completion_with_fallback",
        new=AsyncMock(return_value=(mock_cl, None)),
    ):
        body = await generate_cover_letter(
            profile=profile,
            job=job,
            api_key="explicit-key",
            provider="openai",
            model="gpt-4o-mini",
            db=db,
            user_id=str(test_user.id),
        )

    assert "Dear Hiring Team," in body
    assert "DevOps Lead position" in body
    assert "Alex Mercer" in body
