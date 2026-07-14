from app.services.email import email_service, EmailService
from app.services.batch_operations import (
    batch_analyze_item,
    batch_score_item,
    batch_tag_item,
    batch_archive_item,
)
from app.services.batch import enqueue_batch_job
from app.services.analytics import (
    generate_analytics_metrics,
    create_analytics_snapshot,
    get_latest_snapshot,
    get_snapshots,
)
from app.services.notification import (
    create_notification,
    create_notifications_bulk,
    get_notifications,
    mark_as_read,
    mark_all_as_read,
    get_unread_count,
    create_job_alert_notification,
    create_application_update_notification,
    create_follow_up_reminder,
    create_system_event_notification,
)

__all__ = [
    "email_service",
    "EmailService",
    "batch_analyze_item",
    "batch_score_item",
    "batch_tag_item",
    "batch_archive_item",
    "enqueue_batch_job",
    "generate_analytics_metrics",
    "create_analytics_snapshot",
    "get_latest_snapshot",
    "get_snapshots",
    "create_notification",
    "create_notifications_bulk",
    "get_notifications",
    "mark_as_read",
    "mark_all_as_read",
    "get_unread_count",
    "create_job_alert_notification",
    "create_application_update_notification",
    "create_follow_up_reminder",
    "create_system_event_notification",
]
