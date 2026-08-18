"""
Tests for batch operation handlers.
"""
import uuid
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.orm import Session
from app.models.job import Job, JobImport, JobApplication
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
def mock_job_application(db: Session, mock_job: Job, mock_user: uuid.UUID) -> JobApplication:
    from app.models.job import JobApplication
    application = JobApplication(
        id=uuid.uuid4(),
        user_id=mock_user,
        job_id=mock_job.id,
        status="applied",
    )
    db.add(application)
    db.commit()
    return application


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
        })

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


def test_batch_score_item_success(db: Session, mock_job: Job, mock_profile: Profile, mock_user: uuid.UUID):
    with patch("app.services.batch_operations.calculate_match_score") as mock_score:
        mock_score.return_value = {
            "score": 90,
            "breakdown": {"skills": 30, "experience": 30, "education": 30},
            "explanation": "Great match.",
        }

        result = batch_score_item(
            job_id=mock_job.id,
            user_id=mock_user,
            params={},
            db=db,
        )

        assert result["score"] == 90
        assert "skills" in result["breakdown"]
        
        # Verify the score was saved
        score = db.query(JobMatchScore).filter(
            JobMatchScore.job_id == mock_job.id,
            JobMatchScore.user_id == mock_user,
        ).first()
        assert score is not None
        assert score.score == 90


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
            user_id=uuid.uuid4(),  # Different user
            params={},
            db=db,
        )


def test_batch_tag_item_add(db: Session, mock_job: Job, mock_user: uuid.UUID):
    result = batch_tag_item(
        job_id=mock_job.id,
        user_id=mock_user,
        params={"tags": ["remote", "senior"], "action": "add"},
        db=db,
    )

    assert "remote" in result["tags"]
    assert "senior" in result["tags"]
    assert result["action"] == "add"


def test_batch_tag_item_remove(db: Session, mock_job: Job, mock_user: uuid.UUID):
    # First add a tag
    mock_job.tags = ["python", "fastapi", "remote"]
    db.commit()

    result = batch_tag_item(
        job_id=mock_job.id,
        user_id=mock_user,
        params={"tags": ["remote"], "action": "remove"},
        db=db,
    )

    assert "remote" not in result["tags"]
    assert "python" in result["tags"]
    assert result["action"] == "remove"


def test_batch_tag_item_invalid_action(db: Session, mock_job: Job, mock_user: uuid.UUID):
    with pytest.raises(ValueError, match="Invalid action: invalid"):
        batch_tag_item(
            job_id=mock_job.id,
            user_id=mock_user,
            params={"tags": ["remote"], "action": "invalid"},
            db=db,
        )


def test_batch_archive_item_job(db: Session, mock_job: Job, mock_user: uuid.UUID):
    result = batch_archive_item(
        job_id=mock_job.id,
        user_id=mock_user,
        params={"target": "jobs"},
        db=db,
    )

    assert result["archived"] is True
    assert result["target"] == "jobs"
    
    # Verify the job was archived
    db.refresh(mock_job)
    assert mock_job.is_archived is True


def test_batch_archive_item_application(db: Session, mock_job: Job, mock_user: uuid.UUID):
    from app.models.job import JobApplication
    
    app = JobApplication(
        id=uuid.uuid4(),
        user_id=mock_user,
        job_id=mock_job.id,
        status="applied",
    )
    db.add(app)
    db.commit()

    result = batch_archive_item(
        job_id=app.id,
        user_id=mock_user,
        params={"target": "applications"},
        db=db,
    )

    assert result["archived"] is True
    assert result["target"] == "applications"
    
    # Verify the application was archived
    db.refresh(app)
    assert app.status == "archived"


def test_batch_archive_item_invalid_target(db: Session, mock_job: Job, mock_user: uuid.UUID):
    with pytest.raises(ValueError, match="Invalid target: invalid"):
        batch_archive_item(
            job_id=mock_job.id,
            user_id=mock_user,
            params={"target": "invalid"},
            db=db,
        )