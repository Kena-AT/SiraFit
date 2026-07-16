"""Prometheus metrics endpoint and request-counting middleware.

Exposes a standard ``/metrics`` scrape target (default process + custom HTTP
counters) and increments per-request counters. Self-scrape endpoints
(``/metrics``, ``/docs``, ``/openapi.json``) are excluded from counting to
avoid noise.
"""

from __future__ import annotations

from fastapi import APIRouter
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests handled.",
    ["method", "status"],
)
IN_PROGRESS = Gauge("http_requests_in_progress", "In-flight HTTP requests.")

_SKIP_PREFIXES = ("/metrics", "/docs", "/openapi.json", "/health")


router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Increment HTTP request counters in a non-blocking way."""

    async def dispatch(self, request, call_next):
        if request.url.path.startswith(_SKIP_PREFIXES):
            return await call_next(request)

        IN_PROGRESS.inc()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            IN_PROGRESS.dec()
            REQUEST_COUNT.labels(request.method, status_code).inc()
