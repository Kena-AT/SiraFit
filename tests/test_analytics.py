from app.services.analytics import generate_analytics_metrics, create_analytics_snapshot
from app.models.job import Job, JobApplication
from app.models.profile import Profile, Skill
import uuid


def test_generate_analytics_metrics(test_user, db):
    """Test generating analytics metrics for a user."""
    # Create a profile with skills
    profile = Profile(
        user_id=test_user.id,
        skills=[Skill(name="python"), Skill(name="react"), Skill(name="aws")],
        experiences=[],
        educations=[],
    )
    db.add(profile)
    db.commit()

    # Create some jobs
    job1 = Job(
        external_id=f"analytics-job-1-{uuid.uuid4().hex[:8]}",
        title="Software Engineer",
        company="Acme",
        tags=["python", "react"],
    )
    job2 = Job(
        external_id=f"analytics-job-2-{uuid.uuid4().hex[:8]}",
        title="Backend Engineer",
        company="Beta",
        tags=["python", "aws"],
    )
    job3 = Job(
        external_id=f"analytics-job-3-{uuid.uuid4().hex[:8]}",
        title="Frontend Engineer",
        company="Gamma",
        tags=["react", "typescript"],
    )
    db.add_all([job1, job2, job3])
    db.commit()

    # Create applications with various statuses
    apps = [
        JobApplication(user_id=test_user.id, job_id=job1.id, status="applied"),
        JobApplication(user_id=test_user.id, job_id=job2.id, status="screening"),
        JobApplication(user_id=test_user.id, job_id=job3.id, status="interview"),
    ]
    db.add_all(apps)
    db.commit()

    metrics = generate_analytics_metrics(db, test_user.id)

    assert metrics["total_applications"] == 3
    assert "interview_rate" in metrics
    assert "avg_response_time_days" in metrics
    assert "offer_rate" in metrics
    assert "conversion_funnel" in metrics
    assert "rejection_stages" in metrics
    assert "skill_coverage" in metrics
    assert "market_roles" in metrics
    assert "top_technologies" in metrics
    assert "salary_medians" in metrics


def test_create_analytics_snapshot(test_user, db):
    """Test creating an analytics snapshot."""
    snapshot = create_analytics_snapshot(db, test_user.id)

    assert snapshot is not None
    assert snapshot.user_id == test_user.id
    assert snapshot.snapshot_date is not None
    assert snapshot.metrics is not None
    assert "total_applications" in snapshot.metrics


def test_get_latest_snapshot(test_user, db):
    """Test getting the latest analytics snapshot."""
    from app.services.analytics import get_latest_snapshot

    # Create a snapshot
    create_analytics_snapshot(db, test_user.id)

    # Get the latest
    latest = get_latest_snapshot(db, test_user.id)

    assert latest is not None
    assert latest.user_id == test_user.id


def test_list_snapshots(test_user, db):
    """Test listing analytics snapshots."""
    from app.services.analytics import get_snapshots

    # Create multiple snapshots
    for _ in range(3):
        create_analytics_snapshot(db, test_user.id)

    snapshots, total = get_snapshots(db, test_user.id, skip=0, limit=10)

    assert total == 3
    assert len(snapshots) == 3
