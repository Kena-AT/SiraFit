"""
Notification helper service for managing user notifications in the database.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: uuid.UUID,
    title: str,
    body: str,
    kind: str = "alert",
) -> Notification:
    """Create a new notification for a user."""
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        kind=kind,
        status="unread",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications(
    db: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
) -> tuple[list[Notification], int]:
    """Get a list of notifications for a user with optional status filter."""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if status:
        query = query.filter(Notification.status == status)
    total = query.count()
    notifications = (
        query.order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notifications, total


def mark_as_read(
    db: Session,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
) -> Notification | None:
    """Mark a specific notification as read."""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notification:
        return None
    notification.status = "read"
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(
    db: Session,
    user_id: uuid.UUID,
) -> int:
    """Mark all unread notifications as read for a user."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.status == "unread")
        .update({"status": "read", "read_at": datetime.now(timezone.utc)})
    )
    db.commit()
    return count


def get_unread_count(
    db: Session,
    user_id: uuid.UUID,
) -> int:
    """Get count of unread notifications for a user."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.status == "unread")
        .count()
    )
