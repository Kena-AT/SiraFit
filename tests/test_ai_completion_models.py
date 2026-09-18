"""Tests for AICompletion and AICompletionAttempt models (Sprint 7 Issue #49)."""

import uuid
from datetime import datetime, timezone
from app.models.ai_completion import AICompletion, AICompletionAttempt


def test_create_ai_completion_and_attempts(db, test_user):
    """Verify AICompletion and AICompletionAttempt persistence, relationships, and queries."""
    gen_id = str(uuid.uuid4())

    completion = AICompletion(
        id=uuid.uuid4(),
        generation_id=gen_id,
        user_id=test_user.id,
        operation="job_analysis",
        provider="openrouter",
        model="openai/gpt-4o-mini",
        response_model="AIJobAnalysisOutput",
        status="success",
        attempt_count=2,
        duration_ms=1250,
        total_tokens=450,
        prompt_tokens=300,
        completion_tokens=150,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)

    assert completion.id is not None
    assert completion.generation_id == gen_id
    assert completion.user_id == test_user.id
    assert completion.total_tokens == 450

    # Add attempts
    attempt1 = AICompletionAttempt(
        id=uuid.uuid4(),
        completion_id=completion.id,
        attempt_number=1,
        provider="gemini",
        model="gemini-1.5-flash",
        status="failed",
        failure_code="rate_limit",
        validation_errors={"detail": "Too many requests"},
        duration_ms=400,
        created_at=datetime.now(timezone.utc),
    )
    attempt2 = AICompletionAttempt(
        id=uuid.uuid4(),
        completion_id=completion.id,
        attempt_number=2,
        provider="openrouter",
        model="openai/gpt-4o-mini",
        status="success",
        failure_code=None,
        validation_errors=None,
        duration_ms=850,
        created_at=datetime.now(timezone.utc),
    )
    db.add_all([attempt1, attempt2])
    db.commit()

    # Query by generation_id
    queried = db.query(AICompletion).filter_by(generation_id=gen_id).first()
    assert queried is not None
    assert len(queried.attempts) == 2
    assert queried.attempts[0].attempt_number == 1
    assert queried.attempts[0].failure_code == "rate_limit"
    assert queried.attempts[1].status == "success"

    # Test cascade delete
    db.delete(completion)
    db.commit()

    remaining_attempts = (
        db.query(AICompletionAttempt).filter_by(completion_id=completion.id).all()
    )
    assert len(remaining_attempts) == 0
