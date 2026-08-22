"""
Tests for batch operation handlers (negative / error paths).

The positive-path batch-operation tests live in
``tests/test_system_operations.py`` (migrated from the legacy
``backend/tests`` suite). This file preserves the error-path coverage that had
no equivalent in the canonical suite.
"""
import uuid
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.orm import Session
from app.models.job import Job, JobApplication
from app.models.profile import Profile
from app.models.score import JobMatchScore
from app.services.batch_operations import (
    batch_analyze_item,
    batch_score_item,
    batch_tag_item,
    batch_archive_item,
)


@pytest.fixture
def mock_user(db: Session) -> uuid.UUID:
    from app.models.user import User
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    return user.id


@pytest.fixture
def mock_job(db: Session) -> Job:
    job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Test Company",
        source="linkedin",
        external_id="123",
        tags=["python", "fastapi"],
    )
    db.add(job)
    db.commit()
    return job


@pytest.fixture
def mock_profile(db: Session, mock_user: uuid.UUID) -> Profile:
    profile = Profile(
        id=uuid.uuid4(),
        user_id=mock_user,
        first_name="Test",
        last_name="User",
        headline="Software Engineer",
        skills=[],  # Empty skills to avoid SQLAlchemy collection issues
    )
    db.add(profile)
    db.commit()
    return profile


@pytest.mark.asyncio
async def test_batch_analyze_item_success(db: Session, mock_job: Job, mock_user: uuid.UUID):
    with patch("app.services.batch_operations.run_job_analysis", new_callable=AsyncMock) as mock_analysis:
        mock_analysis.return_value = type("AnalysisResult", (), {
            "score": 85,
            "status": "done",
            "summary": "Great match for your skills.",
        })()

        result = await batch_analyze_item(
            job_id=mock_job.id,
            user_id=mock_user,
            params={"api_key": "test_key", "provider": "openai"},
            db=db,
        )

        assert result["score"] == 85
        assert result["status"] == "done"
        assert "Great match" in result["summary"]


@pytest.mark.asyncio
async def test_batch_analyze_item_job_not_found(db: Session):
    with pytest.raises(ValueError, match="Job .* not found"):
        await batch_analyze_item(
            job_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            params={},
            db=db,
        )


def test_batch_score_item_job_not_found(db: Session):
    with pytest.raises(ValueError, match="Job .* not found"):
        batch_score_item(
            job_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            params={},
            db=db,
        )


def test_batch_score_item_profile_not_found(db: Session, mock_job: Job, mock_user: uuid.UUID):
    with pytest.raises(ValueError, match="Profile for user .* not found"):
        batch_score_item(
            job_id=mock_job.id,
            user_id=mock_user,  # Has a profile? No — mock_profile not created
            params={},
            db=db,
        )


def test_batch_tag_item_invalid_action(db: Session, mock_job: Job, mock_user: uuid.UUID):
    with pytest.raises(ValueError, match="Invalid action: invalid"):
        batch_tag_item(
            job_id=mock_job.id,
            user_id=mock_user,
            params={"tags": ["remote"], "action": "invalid"},
            db=db,
        )


def test_batch_archive_item_invalid_target(db: Session, mock_job: Job, mock_user: uuid.UUID):
    with pytest.raises(ValueError, match="Invalid target: invalid"):
        batch_archive_item(
            job_id=mock_job.id,
            user_id=mock_user,
            params={"target": "invalid"},
            db=db,
        )
