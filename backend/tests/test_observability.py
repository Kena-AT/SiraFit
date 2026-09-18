"""Observability and Tracing unit tests (Sprint 15)."""

import pytest
from app.core.config import settings
from app.core.logging import (
    add_request_id,
    add_timestamp,
    add_trace_correlation,
    sanitize_sensitive_data,
)
from app.observability.tracing import (
    init_tracing,
    shutdown_tracing,
    get_current_trace_context,
)
from app.observability.error_tracking import _scrub_sensitive_dict


def test_request_id_and_timestamp_processors():
    event = {}
    event = add_request_id(None, "info", event)
    assert "request_id" in event
    assert len(event["request_id"]) == 36

    event = add_timestamp(None, "info", event)
    assert "timestamp" in event


def test_sanitize_sensitive_data_processor():
    event = {
        "event": "user_login",
        "password": "super-secret-password",
        "access_token": "jwt-token-value",
        "gemini_api": "AIzaSyD...",
        "user_email": "user@example.com",
    }
    cleaned = sanitize_sensitive_data(None, "info", event)
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["access_token"] == "[REDACTED]"
    assert cleaned["gemini_api"] == "[REDACTED]"
    assert cleaned["user_email"] == "user@example.com"


def test_error_tracking_scrubber():
    payload = {
        "authorization": "Bearer secret123",
        "headers": {
            "Cookie": "session=abc",
            "Content-Type": "application/json",
        },
        "safe_key": "safe_value",
    }
    scrubbed = _scrub_sensitive_dict(payload)
    assert scrubbed["authorization"] == "[REDACTED]"
    assert scrubbed["headers"]["Cookie"] == "[REDACTED]"
    assert scrubbed["headers"]["Content-Type"] == "application/json"
    assert scrubbed["safe_key"] == "safe_value"


def test_tracing_gracefully_handles_disabled_state():
    original_state = settings.ENABLE_TRACING
    try:
        settings.ENABLE_TRACING = False
        shutdown_tracing()
        res = init_tracing()
        assert res is False
        trace_id, span_id = get_current_trace_context()
        assert trace_id is None
        assert span_id is None
    finally:
        settings.ENABLE_TRACING = original_state
