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
    Histogram,
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

# Scraping / import observability (Sprint 3). Labels are bounded and stable —
# never the full URL, title, or raw exception text.
SCRAPE_ATTEMPTS = Counter(
    "scrape_attempts_total",
    "Total job scrape attempts.",
    ["platform", "method"],
)
SCRAPE_SUCCESS = Counter(
    "scrape_success_total",
    "Successful Scrapling extractions.",
    ["platform", "method"],
)
SCRAPE_FAILURE = Counter(
    "scrape_failure_total",
    "Failed scrapes by failure code.",
    ["platform", "failure_code"],
)
SCRAPE_PARTIAL = Counter(
    "scrape_partial_total",
    "Heuristic/partial imports (no clean scrape).",
    ["platform"],
)
JOB_IMPORTS_TOTAL = Counter(
    "job_imports_total",
    "Total job imports.",
    ["source_type"],
)
JOB_IMPORTS_DUPLICATE = Counter(
    "job_imports_duplicate_total",
    "Jobs identified as duplicates during import.",
)
JOB_IMPORTS_FAILED = Counter(
    "job_imports_failed_total",
    "Import pipelines that ended in failure.",
)

# AI Structured Generation & Observability (Sprint 7)
AI_COMPLETIONS_TOTAL = Counter(
    "ai_completions_total",
    "Total structured AI completion operations.",
    ["operation", "provider", "model", "status"],
)
AI_COMPLETION_DURATION_SECONDS = Histogram(
    "ai_completion_duration_seconds",
    "Duration of structured AI completions in seconds.",
    ["operation", "provider"],
    buckets=(0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0),
)
AI_COMPLETION_FAILURES_TOTAL = Counter(
    "ai_completion_failures_total",
    "Structured AI completion failures categorized by failure code.",
    ["operation", "provider", "failure_code"],
)
AI_VALIDATION_RETRIES_TOTAL = Counter(
    "ai_validation_retries_total",
    "Validation retries triggered by schema mismatches during generation.",
    ["operation", "provider"],
)

# Semantic Search & Embeddings Observability (Sprint 8)
EMBEDDING_GENERATION_TOTAL = Counter(
    "embedding_generation_total",
    "Total job embedding generation operations.",
    ["operation", "status", "model"],
)
EMBEDDING_GENERATION_DURATION_SECONDS = Histogram(
    "embedding_generation_duration_seconds",
    "Duration of job embedding generation in seconds.",
    ["model"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
SEMANTIC_SEARCH_TOTAL = Counter(
    "semantic_search_total",
    "Total job searches executed by search mode.",
    ["mode", "status"],
)
SEMANTIC_SEARCH_DURATION_SECONDS = Histogram(
    "semantic_search_duration_seconds",
    "Latency of job searches in seconds.",
    ["mode"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)

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
