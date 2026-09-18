import structlog
import uuid
import datetime as dt
from typing import Any
from app.core.config import settings

# Sensitive parameter names to scrub from log entries
_SENSITIVE_PATTERNS = (
    "password",
    "access_token",
    "refresh_token",
    "secret",
    "authorization",
    "cookie",
    "gemini_api",
    "openai_api",
    "openrouter_api",
    "anthropic_api",
    "grok_api",
    "mistral_api",
    "nvidia_api",
    "api_key",
    "totp_secret",
)


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


def add_trace_correlation(logger, method_name, event_dict):
    """Inject OpenTelemetry trace_id and span_id into log event if active."""
    # If already set by contextvars, preserve them
    if "trace_id" not in event_dict or "span_id" not in event_dict:
        try:
            from app.observability.tracing import get_current_trace_context

            trace_id, span_id = get_current_trace_context()
            if trace_id and "trace_id" not in event_dict:
                event_dict["trace_id"] = trace_id
            if span_id and "span_id" not in event_dict:
                event_dict["span_id"] = span_id
        except Exception:
            pass
    return event_dict


def sanitize_sensitive_data(logger, method_name, event_dict):
    """Scrub passwords, secrets, tokens and keys from log dictionary."""
    for key in list(event_dict.keys()):
        lower_key = str(key).lower()
        if any(pattern in lower_key for pattern in _SENSITIVE_PATTERNS):
            event_dict[key] = "[REDACTED]"
    return event_dict


def configure_logging():
    """Configure structlog for JSON structured logging with trace correlation and redaction."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        add_timestamp,
        add_request_id,
        add_trace_correlation,
        sanitize_sensitive_data,
        structlog.processors.UnicodeDecoder(),
    ]

    # Use JSONRenderer in production, pretty ConsoleRenderer in local dev/testing
    if settings.ENVIRONMENT == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
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
