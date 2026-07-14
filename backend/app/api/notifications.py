from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationListResponse

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
) -> Any:
    """List user's notifications with optional status filter."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if status:
        query = query.filter(Notification.status == status)

    total = query.count()
    notifications = (
        query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    )

    return NotificationListResponse(
        notifications=notifications, total=total, skip=skip, limit=limit
    )


@router.get("/unread-count", response_model=Dict[str, int])
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get count of unread notifications."""
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id, Notification.status == "unread"
        )
        .count()
    )

    return {"count": count}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Mark a notification as read."""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    from datetime import datetime, timezone

    notification.status = "read"
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)

    return notification


@router.post("/mark-all-read", response_model=Dict[str, int])
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Mark all notifications as read."""
    from datetime import datetime, timezone

    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id, Notification.status == "unread"
        )
        .update({"status": "read", "read_at": datetime.now(timezone.utc)})
    )
    db.commit()

    return {"updated": count}


@router.delete("/{notification_id}", response_model=Dict[str, str])
def delete_notification(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Delete a notification."""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()

    return {"message": "Notification deleted"}
