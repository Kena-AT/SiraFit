from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.services.notification import (
    get_notifications,
    mark_as_read,
    mark_all_as_read,
    get_unread_count,
)
from app.services.analytics import (
    generate_analytics_metrics,
    create_analytics_snapshot,
    get_latest_snapshot,
    get_snapshots,
)
from app.schemas.notification import (
    AnalyticsSnapshotResponse,
    AnalyticsSnapshotListResponse,
    MetricsResponse,
)

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
):
    """List user's notifications with pagination."""
    notifications, total = get_notifications(db, current_user.id, skip, limit, status)
    return NotificationListResponse(
        notifications=notifications, total=total, skip=skip, limit=limit
    )


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get count of unread notifications."""
    count = get_unread_count(db, current_user.id)
    return {"count": count}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    notification = mark_as_read(db, current_user.id, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    count = mark_all_as_read(db, current_user.id)
    return {"marked_read": count}


# Analytics endpoints


@router.get("/analytics/metrics", response_model=MetricsResponse)
def get_analytics_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current analytics metrics for the user."""
    metrics = generate_analytics_metrics(db, current_user.id)
    return metrics


@router.post("/analytics/snapshots", response_model=AnalyticsSnapshotResponse)
def create_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new analytics snapshot."""
    snapshot = create_analytics_snapshot(db, current_user.id)
    return snapshot


@router.get("/analytics/snapshots", response_model=AnalyticsSnapshotListResponse)
def list_snapshots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List analytics snapshots for the user."""
    snapshots, total = get_snapshots(db, current_user.id, skip, limit)
    return AnalyticsSnapshotListResponse(
        snapshots=snapshots, total=total, skip=skip, limit=limit
    )


@router.get("/analytics/snapshots/latest", response_model=AnalyticsSnapshotResponse)
def latest_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the latest analytics snapshot."""
    snapshot = get_latest_snapshot(db, current_user.id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No analytics snapshot found")
    return snapshot
