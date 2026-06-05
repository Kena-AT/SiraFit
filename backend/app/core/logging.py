import structlog
import uuid
import time
from typing import Callable, Any
from fastapi import Request, Response


def get_request_id() -> str:
    """Generate or get request ID for correlation"""
    return str(uuid.uuid4())


def add_request_id(logger, method_name, event_dict):
    """Add request ID to all log entries"""
    if "request_id" not in event_dict:
        event_dict["request_id"] = get_request_id()
    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """Add timestamp to all log entries"""
    if "timestamp" not in event_dict:
        event_dict["timestamp"] = structlog.stdlib.now()
    return event_dict


def configure_logging():
    """Configure structlog for structured logging"""
    processor_chain = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_timestamp,
        add_request_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            add_timestamp,
            add_request_id,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return processor_chain


def log_audit_event(
    event_name: str,
    user_id: str = None,
    entity_type: str = None,
    entity_id: str = None,
    details: dict = None
):
    """Log audit events with structured context"""
    logger = structlog.get_logger("audit")
    
    log_dict = {
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
