import structlog
import uuid
import datetime as dt
from typing import Any


def get_request_id() -> str:
    """Generate a UUID for request correlation."""
    return str(uuid.uuid4())


def add_request_id(logger, method_name, event_dict):
    """Inject request_id into every log entry if not already present."""
    if "request_id" not in event_dict:
        event_dict["request_id"] = get_request_id()
    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """Inject an ISO-8601 timestamp into every log entry."""
    if "timestamp" not in event_dict:
        event_dict["timestamp"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return event_dict


def configure_logging():
    """Configure structlog for JSON structured logging."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        add_timestamp,
        add_request_id,
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.dev.ConsoleRenderer(),  # pretty-print in dev; swap for JSONRenderer in prod
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def log_audit_event(
    event_name: str,
    user_id: str = None,
    entity_type: str = None,
    entity_id: str = None,
    details: dict = None,
):
    """Emit a structured audit log entry."""
    logger = structlog.get_logger("audit")

    log_dict: dict[str, Any] = {
        "event": event_name,
        "service": "sirafit-api",
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
    }

    if user_id:
        log_dict["user_id"] = str(user_id)

    if details:
        log_dict.update(details)

    logger.info(**log_dict)
