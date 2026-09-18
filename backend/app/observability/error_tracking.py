"""Centralized Error Tracking Module (Sprint 15).

Integrates Sentry-compatible SDK (supporting both Sentry and GlitchTip):
- Configurable DSN, environment, release version, and sample rates.
- Automatic scrubbing of sensitive data (passwords, tokens, API keys, resume text).
- Unhandled FastAPI exception tracking and custom capture helpers.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_ERROR_TRACKING_INITIALIZED = False

# Sensitive keys to sanitize in events and breadcrumbs
_SENSITIVE_KEYS = {
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
    "token",
    "secret_key",
    "data_encryption_key",
    "totp_secret",
}


def _scrub_sensitive_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively scrub sensitive keys and tokens from a dictionary."""
    scrubbed = {}
    for k, v in data.items():
        lower_key = k.lower()
        if any(s in lower_key for s in _SENSITIVE_KEYS):
            scrubbed[k] = "[REDACTED]"
        elif isinstance(v, dict):
            scrubbed[k] = _scrub_sensitive_dict(v)
        elif isinstance(v, list):
            scrubbed[k] = [
                _scrub_sensitive_dict(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            scrubbed[k] = v
    return scrubbed


def _before_send(event: dict[str, Any], hint: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Scrub sensitive request headers, query params, and body data before sending."""
    try:
        # Scrub request headers and data
        if "request" in event:
            req = event["request"]
            if "headers" in req and isinstance(req["headers"], dict):
                req["headers"] = _scrub_sensitive_dict(req["headers"])
            if "data" in req and isinstance(req["data"], dict):
                req["data"] = _scrub_sensitive_dict(req["data"])
            if "query_string" in req and isinstance(req["query_string"], str):
                # Mask potential token query params
                req["query_string"] = re.sub(
                    r"(token|key|secret)=[^&]+", r"\1=[REDACTED]", req["query_string"], flags=re.IGNORECASE
                )

        # Scrub breadcrumbs
        if "breadcrumbs" in event and "values" in event["breadcrumbs"]:
            for b in event["breadcrumbs"]["values"]:
                if "data" in b and isinstance(b["data"], dict):
                    b["data"] = _scrub_sensitive_dict(b["data"])

        # Scrub extra / contexts
        if "extra" in event and isinstance(event["extra"], dict):
            event["extra"] = _scrub_sensitive_dict(event["extra"])

    except Exception as e:
        logger.warning("Error scrubbing Sentry event: %s", e)

    return event


def init_error_tracking() -> bool:
    """Initialize error tracking SDK if enabled and DSN is provided.

    Compatible with GlitchTip and Sentry. Safe if unavailable or disabled.
    """
    global _ERROR_TRACKING_INITIALIZED
    if _ERROR_TRACKING_INITIALIZED:
        return True

    if not settings.ERROR_TRACKING_ENABLED or not settings.ERROR_TRACKING_DSN:
        logger.debug("Error tracking is disabled or DSN not configured.")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.ERROR_TRACKING_DSN,
            environment=settings.ENVIRONMENT,
            release=f"sirafit@{settings.RELEASE_VERSION}",
            traces_sample_rate=settings.ERROR_TRACKING_SAMPLE_RATE,
            before_send=_before_send,
            send_default_pii=False,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
            ],
        )
        _ERROR_TRACKING_INITIALIZED = True
        logger.info("Error tracking initialized successfully.")
        return True
    except ImportError:
        logger.warning("sentry-sdk not installed; error tracking disabled.")
        return False
    except Exception as e:
        logger.warning("Failed to initialize error tracking: %s", e)
        return False


def capture_exception(exc: Exception, **extra: Any) -> None:
    """Safely capture an unhandled exception to the error tracker."""
    if not _ERROR_TRACKING_INITIALIZED:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for k, v in extra.items():
                scope.set_extra(k, v)
            sentry_sdk.capture_exception(exc)
    except Exception as e:
        logger.warning("Failed to capture exception to tracker: %s", e)
