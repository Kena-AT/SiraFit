from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.analytics import AnalyticsSnapshot
from app.services.analytics import generate_analytics_metrics, create_analytics_snapshot, get_latest_snapshot
from app.schemas.notification import (
    AnalyticsSnapshotResponse, AnalyticsSnapshotListResponse,
    MetricsResponse
)

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current analytics metrics for the user."""
    metrics = generate_analytics_metrics(db, current_user.id)
    return metrics


@router.post("/snapshots", response_model=AnalyticsSnapshotResponse)
def create_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new analytics snapshot."""
    snapshot = create_analytics_snapshot(db, current_user.id)
    return snapshot


@router.get("/snapshots", response_model=AnalyticsSnapshotListResponse)
def list_snapshots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """List analytics snapshots for the user."""
    query = db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.user_id == current_user.id)
    total = query.count()
    snapshots = query.order_by(AnalyticsSnapshot.snapshot_date.desc()).offset(skip).limit(limit).all()
    
    return AnalyticsSnapshotListResponse(
        snapshots=snapshots,
        total=total,
        skip=skip,
        limit=limit
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