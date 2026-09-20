"""
Notification service for sending emails and processing reminders.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User, UserPreference
from app.models.job import JobApplication, Job
from app.core.database import SessionLocal
from app.services.email import send_email

logger = logging.getLogger(__name__)


def send_notification_email(notification_id: uuid.UUID) -> bool:
    """
    Send an email for a notification.
    """
    db = SessionLocal()
    try:
        notification = (
            db.query(Notification).filter(Notification.id == notification_id).first()
        )
        if not notification:
            logger.warning(
                "notification_not_found",
                extra={"notification_id": str(notification_id)},
            )
            return False

        user = db.query(User).filter(User.id == notification.user_id).first()
        if not user:
            logger.warning(
                "user_not_found", extra={"user_id": str(notification.user_id)}
            )
            return False

        # Check if user wants email notifications
        pref = (
            db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
        )
        if pref and not pref.email_notifications:
            logger.info("email_notifications_disabled", extra={"user_id": str(user.id)})
            return False

        subject = f"SiraFit: {notification.title}"
        body = f"""
        Hi {user.email},
        
        {notification.body}
        
        ---
        SiraFit
        """

        try:
            send_email(to=user.email, subject=subject, body=body)
            logger.info(
                "notification_email_sent",
                extra={"notification_id": str(notification_id)},
            )
            return True
        except Exception as e:
            logger.exception(
                "notification_email_failed",
                extra={"notification_id": str(notification_id), "error": str(e)},
            )
            return False
    finally:
        db.close()


def check_and_send_reminders() -> int:
    """
    Check for upcoming follow-ups and send reminder notifications.
    Returns the number of reminders sent.
    """
    db = SessionLocal()
    reminders_sent = 0
    try:
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)

        # Find applications with follow-ups due in the next 24 hours
        applications = (
            db.query(JobApplication)
            .filter(
                JobApplication.follow_up_at.isnot(None),
                JobApplication.follow_up_at >= now,
                JobApplication.follow_up_at <= tomorrow,
                JobApplication.status.notin_(
                    ["offer", "rejected", "withdrawn", "archived"]
                ),
            )
            .all()
        )

        for app in applications:
            # Check if we already sent a reminder for this follow-up
            # Use a more specific body pattern match instead of fragile contains().
            # The body format is: "Follow up on your application for {job.title} at {job.company} (due {date})"
            body_marker = (
                f"application for {app.job.title if app.job else 'unknown'} at"
            )
            existing = (
                db.query(Notification)
                .filter(
                    Notification.user_id == app.user_id,
                    Notification.kind == "reminder",
                    Notification.body.contains(body_marker),
                    Notification.created_at >= now - timedelta(hours=24),
                )
                .first()
            )

            if existing:
                continue

            job = db.query(Job).filter(Job.id == app.job_id).first()
            if not job:
                continue

            # Create reminder notification
            notification = Notification(
                user_id=app.user_id,
                title="Follow-up Reminder",
                body=f"Follow up on your application for {job.title} at {job.company} (due {app.follow_up_at.strftime('%Y-%m-%d')})",
                kind="reminder",
                status="unread",
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)

            # Send email
            send_notification_email(notification.id)
            reminders_sent += 1

        return reminders_sent
    except Exception as e:
        logger.exception("check_reminders_failed", extra={"error": str(e)})
        return 0
    finally:
        db.close()


def send_daily_summaries() -> int:
    """
    Send daily digest emails to users who have email_daily_summary enabled.
    """
    db = SessionLocal()
    summaries_sent = 0
    try:
        users = (
            db.query(User)
            .join(UserPreference)
            .filter(UserPreference.email_daily_summary == True)
            .all()
        )
        for user in users:
            try:
                # In a real implementation, you would compile the daily digest content here.
                subject = "SiraFit: Your Daily Activity Summary"
                body = f"Hi {user.email},\n\nHere is your daily summary of job applications and interviews.\n\n---\nSiraFit"
                send_email(to=user.email, subject=subject, body=body)
                summaries_sent += 1
            except Exception as e:
                logger.error("daily_summary_failed", extra={"user_id": str(user.id), "error": str(e)})
        return summaries_sent
    except Exception as e:
        logger.exception("daily_summaries_batch_failed", extra={"error": str(e)})
        return 0
    finally:
        db.close()


def process_job_match_alerts() -> int:
    """
    Process new job matches for users who have email_job_matches enabled.
    """
    db = SessionLocal()
    alerts_sent = 0
    try:
        users = (
            db.query(User)
            .join(UserPreference)
            .filter(UserPreference.email_job_matches == True)
            .all()
        )
        for user in users:
            try:
                # In a real implementation, you'd check for new high-scoring matches.
                subject = "SiraFit: New Job Matches"
                body = f"Hi {user.email},\n\nWe found some new jobs matching your profile.\n\n---\nSiraFit"
                send_email(to=user.email, subject=subject, body=body)
                alerts_sent += 1
            except Exception as e:
                logger.error("job_match_alert_failed", extra={"user_id": str(user.id), "error": str(e)})
        return alerts_sent
    except Exception as e:
        logger.exception("job_match_alerts_batch_failed", extra={"error": str(e)})
        return 0
    finally:
        db.close()


def process_new_opportunities() -> int:
    """
    Process general new opportunity emails for users who have email_new_opportunities enabled.
    """
    db = SessionLocal()
    emails_sent = 0
    try:
        users = (
            db.query(User)
            .join(UserPreference)
            .filter(UserPreference.email_new_opportunities == True)
            .all()
        )
        for user in users:
            try:
                # Compile opportunities content
                subject = "SiraFit: New Opportunities"
                body = f"Hi {user.email},\n\nCheck out these new opportunities on SiraFit.\n\n---\nSiraFit"
                send_email(to=user.email, subject=subject, body=body)
                emails_sent += 1
            except Exception as e:
                logger.error("new_opportunity_email_failed", extra={"user_id": str(user.id), "error": str(e)})
        return emails_sent
    except Exception as e:
        logger.exception("new_opportunities_batch_failed", extra={"error": str(e)})
        return 0
    finally:
        db.close()


def create_job_alert_notification(
    db: Session, user_id: uuid.UUID, job_title: str, company: str, match_score: int
) -> Notification:
    """
    Create a notification for a new job match.
    """
    notification = Notification(
        user_id=user_id,
        title="New Job Match",
        body=f"New {job_title} position at {company} matches your profile ({match_score}% match)",
        kind="alert",
        status="unread",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def create_application_update_notification(
    db: Session, user_id: uuid.UUID, company: str, role: str, new_status: str
) -> Notification:
    """
    Create a notification for application status update.
    """
    notification = Notification(
        user_id=user_id,
        title="Application Update",
        body=f"Your application for {role} at {company} is now {new_status}",
        kind="alert",
        status="unread",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def create_system_event_notification(
    db: Session, user_id: uuid.UUID, title: str, body: str
) -> Notification:
    """
    Create a system event notification.
    """
    notification = Notification(
        user_id=user_id, title=title, body=body, kind="system_event", status="unread"
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
