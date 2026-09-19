"""Unit tests for analytics weekly trends and market demand dynamic change."""

from datetime import datetime, timezone, timedelta
import uuid
from unittest.mock import MagicMock
from app.services.analytics import generate_analytics_metrics
from app.models.job import JobApplication, Job


def test_analytics_weekly_trend_calculation():
    db = MagicMock()
    user_id = uuid.uuid4()

    now = datetime.now(timezone.utc)
    app_this_week = JobApplication(
        id=uuid.uuid4(),
        user_id=user_id,
        status="applied",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )
    app_this_week.job = None

    app_last_week = JobApplication(
        id=uuid.uuid4(),
        user_id=user_id,
        status="screening",
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=10),
    )
    app_last_week.job = None

    # Setup query mock
    query_mock = MagicMock()
    query_mock.filter.return_value.options.return_value.all.return_value = [
        app_this_week,
        app_last_week,
    ]
    # For subqueries inside generate_analytics_metrics
    db.query.return_value = query_mock

    metrics = generate_analytics_metrics(db, user_id)
    assert metrics["total_applications"] == 2
    assert metrics["applications_this_week"] == 1
    assert metrics["applications_last_week"] == 1
    assert "this week" in metrics["applications_trend"]
