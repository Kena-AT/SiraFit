"""OpenTelemetry Distributed Tracing Module (Sprint 15).

Provides idempotent, environment-aware OpenTelemetry tracing setup:
- Safe when trace collector is offline or not configured (remains disabled).
- Standard trace attributes (service, environment, version).
- Bounded trace attributes, avoiding high cardinality / sensitive fields.
- Helpers to retrieve active trace_id and span_id for log correlation.
- Clean shutdown / flush support.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_TRACING_INITIALIZED = False


def init_tracing(app=None) -> bool:
    """Initialize OpenTelemetry tracer provider and instrumentation.

    Safe to call multiple times (idempotent). If settings.ENABLE_TRACING is
    False or required libraries are missing, returns False gracefully.
    """
    global _TRACING_INITIALIZED
    if _TRACING_INITIALIZED:
        return True

    if not settings.ENABLE_TRACING:
        logger.debug("OpenTelemetry tracing is disabled by configuration.")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased, ParentBased
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        logger.warning(
            "opentelemetry packages not installed; tracing disabled."
        )
        return False

    resource = Resource.create(
        {
            "service.name": "sirafit-api",
            "service.version": settings.RELEASE_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )

    sampler = ParentBased(TraceIdRatioBased(settings.OTEL_SAMPLE_RATE))
    provider = TracerProvider(resource=resource, sampler=sampler)

    # Configure OTLP Exporter if endpoint is specified
    if settings.OTLP_ENDPOINT:
        try:
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(
                endpoint=settings.OTLP_ENDPOINT,
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTLP trace exporter configured for %s", settings.OTLP_ENDPOINT)
        except Exception as e:
            logger.warning("Failed to configure OTLP trace exporter: %s", e)

    trace.set_tracer_provider(provider)

    # Instrument FastAPI if app is supplied
    if app:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=provider,
                excluded_urls="health/live,health/ready,metrics",
            )
            logger.info("FastAPI instrumented with OpenTelemetry.")
        except Exception as e:
            logger.warning("Failed to instrument FastAPI: %s", e)

    _TRACING_INITIALIZED = True
    return True


def shutdown_tracing() -> None:
    """Flush and shut down tracer provider cleanly."""
    global _TRACING_INITIALIZED
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider

        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            provider.shutdown()
            logger.debug("OpenTelemetry tracer provider shut down cleanly.")
    except Exception as e:
        logger.warning("Error shutting down OpenTelemetry tracer provider: %s", e)
    finally:
        _TRACING_INITIALIZED = False


def get_current_trace_context() -> tuple[Optional[str], Optional[str]]:
    """Return the active (trace_id, span_id) formatted as 32-char / 16-char hex strings.

    Returns (None, None) if no active trace span exists.
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.is_recording():
            ctx = span.get_span_context()
            if ctx and ctx.is_valid:
                trace_id = f"{ctx.trace_id:032x}"
                span_id = f"{ctx.span_id:016x}"
                return trace_id, span_id
    except Exception:
        pass
    return None, None
