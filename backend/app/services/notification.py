"""
Notification service for creating and managing notifications.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.notification import Notification
from app.models.user import User


def _utcnow():
    return datetime.now(timezone.utc)


def create_notification(
    db: Session,
    user_id: uuid.UUID,
    title: str,
    body: str,
    kind: str = "system_event"
) -> Notification:
    """
    Create a new notification for a user.
    """
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


def create_notifications_bulk(
    db: Session,
    user_id: uuid.UUID,
    notifications: List[dict]
) -> List[Notification]:
    """
    Create multiple notifications at once.
    """
    created = []
    for n in notifications:
        notification = Notification(
            user_id=user_id,
            title=n.get("title", ""),
            body=n.get("body", ""),
            kind=n.get("kind", "system_event"),
            status="unread",
        )
        db.add(notification)
        created.append(notification)
    db.commit()
    for n in created:
        db.refresh(n)
    return created


def get_notifications(
    db: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None
):
    """
    Get paginated notifications for a user.
    """
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if status:
        query = query.filter(Notification.status == status)
    
    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications, total


def mark_as_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> Optional[Notification]:
    """
    Mark a notification as read.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if notification:
        notification.status = "read"
        notification.read_at = _utcnow()
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user_id: uuid.UUID) -> int:
    """
    Mark all unread notifications as read.
    """
    result = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.status == "unread"
    ).update({
        "status": "read",
        "read_at": _utcnow()
    }, synchronize_session=False)
    db.commit()
    return result


def get_unread_count(db: Session, user_id: uuid.UUID) -> int:
    """
    Get count of unread notifications.
    """
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.status == "unread"
    ).count()


def create_job_alert_notification(db: Session, user_id: uuid.UUID, job_title: str, company: str) -> Notification:
    """
    Create a notification for a new job match.
    """
    return create_notification(
        db=db,
        user_id=user_id,
        title="New Job Match",
        body=f"New {job_title} position at {company} matches your profile",
        kind="alert"
    )


def create_application_update_notification(
    db: Session, 
    user_id: uuid.UUID, 
    company: str, 
    role: str, 
    new_status: str
) -> Notification:
    """
    Create a notification for application status update.
    """
    return create_notification(
        db=db,
        user_id=user_id,
        title="Application Update",
        body=f"Your application for {role} at {company} is now {new_status}",
        kind="alert"
    )


def create_follow_up_reminder(
    db: Session,
    user_id: uuid.UUID,
    action: str,
    company: str,
    due_date: str
) -> Notification:
    """
    Create a follow-up reminder notification.
    """
    return create_notification(
        db=db,
        user_id=user_id,
        title="Follow-up Reminder",
        body=f"Remember to {action} for {company} by {due_date}",
        kind="reminder"
    )


def create_system_event_notification(
    db: Session,
    user_id: uuid.UUID,
    title: str,
    body: str
) -> Notification:
    """
    Create a system event notification.
    """
    return create_notification(
        db=db,
        user_id=user_id,
        title=title,
        body=body,
        kind="system_event"
    )