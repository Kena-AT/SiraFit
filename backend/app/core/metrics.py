"""Prometheus metrics endpoint and observability instruments (Sprint 15).

Exposes a standard ``/metrics`` scrape target with:
- Normalized HTTP request counters & latency histograms
- Database connection pool gauges (dynamically sampled without DB writes)
- Celery worker & task metrics
- AI provider requests, token usage, and latency metrics
- Security event counters (auth failures, rate limit events)
"""

from __future__ import annotations

import re
import time
from typing import Any
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

# ── 1. HTTP Metrics (Sprint 15 + Core) ───────────────────────────
# Legacy metrics kept for backward-compatibility
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests handled.",
    ["method", "status"],
)
IN_PROGRESS = Gauge("http_requests_in_progress", "In-flight HTTP requests.")

# Sprint 15 specification HTTP metrics with normalized routes
SIRAFIT_HTTP_REQUESTS_TOTAL = Counter(
    "sirafit_http_requests_total",
    "Total HTTP requests handled by method, normalized route, and status.",
    ["method", "route", "status"],
)
SIRAFIT_HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "sirafit_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ── 2. Database Connection Pool Metrics (Sprint 15) ─────────────
SIRAFIT_DB_POOL_SIZE = Gauge(
    "sirafit_db_pool_size",
    "Configured steady-state database connection pool capacity.",
)
SIRAFIT_DB_POOL_CHECKED_OUT = Gauge(
    "sirafit_db_pool_checked_out",
    "Current number of connections checked out from the pool.",
)
SIRAFIT_DB_POOL_CHECKED_IN = Gauge(
    "sirafit_db_pool_checked_in",
    "Current number of idle connections checked into the pool.",
)
SIRAFIT_DB_POOL_OVERFLOW = Gauge(
    "sirafit_db_pool_overflow",
    "Current overflow connections beyond steady-state pool size.",
)
SIRAFIT_DB_POOL_CONNECTIONS = Gauge(
    "sirafit_db_pool_connections",
    "Total active connections (checked out + checked in).",
)


def update_db_pool_metrics():
    """Poll SQLAlchemy engine pool without querying the database."""
    try:
        from app.core.database import engine

        if engine and hasattr(engine, "pool"):
            pool = engine.pool
            size = pool.size()
            checked_out = pool.checkedout()
            checked_in = pool.checkedin()
            overflow = pool.overflow()

            SIRAFIT_DB_POOL_SIZE.set(size if size is not None else 0)
            SIRAFIT_DB_POOL_CHECKED_OUT.set(checked_out if checked_out is not None else 0)
            SIRAFIT_DB_POOL_CHECKED_IN.set(checked_in if checked_in is not None else 0)
            SIRAFIT_DB_POOL_OVERFLOW.set(overflow if overflow is not None else 0)
            SIRAFIT_DB_POOL_CONNECTIONS.set(
                (checked_out or 0) + (checked_in or 0)
            )
    except Exception:
        pass


# ── 3. Celery Worker & Queue Metrics (Sprint 15) ────────────────
SIRAFIT_CELERY_WORKER_ALIVE = Gauge(
    "sirafit_celery_worker_alive",
    "1 if at least one Celery worker is active, 0 otherwise.",
)
SIRAFIT_CELERY_TASK_SUCCESS_TOTAL = Counter(
    "sirafit_celery_task_success_total",
    "Total successful Celery task completions.",
    ["task"],
)
SIRAFIT_CELERY_TASK_FAILURE_TOTAL = Counter(
    "sirafit_celery_task_failure_total",
    "Total failed Celery tasks.",
    ["task", "exception_type"],
)
SIRAFIT_CELERY_TASK_DURATION_SECONDS = Histogram(
    "sirafit_celery_task_duration_seconds",
    "Duration of Celery task execution in seconds.",
    ["task"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 15.0, 30.0, 60.0, 120.0),
)

# ── 4. AI Metrics (Sprint 15 & Sprint 7) ────────────────────────
SIRAFIT_AI_REQUESTS_TOTAL = Counter(
    "sirafit_ai_requests_total",
    "Total AI generation requests.",
    ["provider", "model", "status", "operation"],
)
SIRAFIT_AI_REQUEST_DURATION_SECONDS = Histogram(
    "sirafit_ai_request_duration_seconds",
    "AI request latency in seconds.",
    ["provider", "operation"],
    buckets=(0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0),
)
SIRAFIT_AI_TOKENS_TOTAL = Counter(
    "sirafit_ai_tokens_total",
    "Total tokens consumed by AI provider operations.",
    ["provider", "model", "direction"],  # direction: prompt | completion | total
)

# Backward-compatible AI metric references
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

# ── 5. Security / Application Metrics (Sprint 15) ───────────────
SIRAFIT_AUTH_FAILURES_TOTAL = Counter(
    "sirafit_auth_failures_total",
    "Aggregate authentication and token failures.",
    ["reason"],  # e.g. "invalid_credentials", "expired_token", "invalid_2fa"
)
SIRAFIT_RATE_LIMIT_EXCEEDED_TOTAL = Counter(
    "sirafit_rate_limit_exceeded_total",
    "Aggregate rate limit violations.",
    ["limiter_type"],  # e.g. "auth", "api"
)

# ── Scraping & Import Observability (Sprint 3) ──────────────────
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

# ── Semantic Search Observability (Sprint 8) ────────────────────
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


# ── Route Normalization Helper ──────────────────────────────────
_UUID_REGEX = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_INT_REGEX = re.compile(r"/\d+(?=/|$)")


def normalize_route_path(path: str) -> str:
    """Normalize dynamic IDs in path to maintain bounded Prometheus label cardinality."""
    # Replace UUIDs with {id}
    normalized = _UUID_REGEX.sub("{id}", path)
    # Replace numeric IDs with {id}
    normalized = _INT_REGEX.sub("/{id}", normalized)
    return normalized


_SKIP_PREFIXES = ("/metrics", "/docs", "/openapi.json", "/health")

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape endpoint."""
    # Update dynamic gauges before generating the scrape payload
    update_db_pool_metrics()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Increment HTTP request counters and duration histograms with bounded labels."""

    async def dispatch(self, request, call_next):
        path = request.url.path
        if path.startswith(_SKIP_PREFIXES):
            return await call_next(request)

        normalized_route = normalize_route_path(path)
        method = request.method

        IN_PROGRESS.inc()
        start_time = time.time()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.time() - start_time
            IN_PROGRESS.dec()

            # Record legacy counters
            REQUEST_COUNT.labels(method, str(status_code)).inc()

            # Record Sprint 15 HTTP metrics
            SIRAFIT_HTTP_REQUESTS_TOTAL.labels(
                method, normalized_route, str(status_code)
            ).inc()
            SIRAFIT_HTTP_REQUEST_DURATION_SECONDS.labels(
                method, normalized_route
            ).observe(duration)
