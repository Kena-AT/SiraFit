from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.core.cache import cache_delete, cache_get, cache_set
from app.core.database import get_db
from app.models.analytics import AnalyticsSnapshot
from app.models.user import User
from app.schemas.notification import (
    AnalyticsSnapshotListResponse,
    AnalyticsSnapshotResponse,
    MetricsResponse,
)
from app.services.analytics import (
    create_analytics_snapshot,
    generate_analytics_metrics,
    get_latest_snapshot,
)

router = APIRouter()

_METRICS_TTL = 60


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current analytics metrics for the user (cached for 60s)."""
    cache_key = f"analytics:metrics:{current_user.id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    metrics = generate_analytics_metrics(db, current_user.id)
    cache_set(cache_key, metrics, ttl=_METRICS_TTL)
    return metrics


@router.post("/snapshots", response_model=AnalyticsSnapshotResponse)
def create_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new analytics snapshot."""
    snapshot = create_analytics_snapshot(db, current_user.id)
    # Invalidate the cached metrics so the next read reflects fresh data.
    cache_delete(f"analytics:metrics:{current_user.id}")
    return snapshot


@router.get("/snapshots", response_model=AnalyticsSnapshotListResponse)
def list_snapshots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """List analytics snapshots for the user."""
    query = db.query(AnalyticsSnapshot).filter(
        AnalyticsSnapshot.user_id == current_user.id
    )
    total = query.count()
    snapshots = (
        query.order_by(AnalyticsSnapshot.snapshot_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return AnalyticsSnapshotListResponse(
        snapshots=snapshots, total=total, skip=skip, limit=limit
    )


@router.get("/snapshots/latest", response_model=AnalyticsSnapshotResponse)
def get_latest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the latest analytics snapshot."""
    snapshot = get_latest_snapshot(db, current_user.id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No analytics snapshot found")
    return snapshot
