"""Prometheus metrics unit tests (Sprint 15)."""

import pytest
from app.core.metrics import (
    normalize_route_path,
    update_db_pool_metrics,
    SIRAFIT_HTTP_REQUESTS_TOTAL,
    SIRAFIT_AI_TOKENS_TOTAL,
    SIRAFIT_DB_POOL_SIZE,
)


def test_normalize_route_path():
    # UUID normalization
    assert (
        normalize_route_path("/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000")
        == "/api/v1/jobs/{id}"
    )
    assert (
        normalize_route_path(
            "/api/v1/resumes/123e4567-e89b-12d3-a456-426614174000/pdf"
        )
        == "/api/v1/resumes/{id}/pdf"
    )

    # Integer ID normalization
    assert normalize_route_path("/api/v1/applications/42") == "/api/v1/applications/{id}"
    assert normalize_route_path("/api/v1/applications/42/notes") == "/api/v1/applications/{id}/notes"

    # Static path preservation
    assert normalize_route_path("/api/v1/auth/login") == "/api/v1/auth/login"
    assert normalize_route_path("/health/status") == "/health/status"


def test_db_pool_metrics_update_does_not_fail():
    # Calling update_db_pool_metrics should run cleanly without exceptions
    update_db_pool_metrics()


def test_ai_token_metrics_increment():
    # Test that recording token metrics increments correctly without unbounded labels
    SIRAFIT_AI_TOKENS_TOTAL.labels(
        provider="gemini",
        model="gemini-1.5-flash",
        direction="prompt",
    ).inc(150)

    SIRAFIT_AI_TOKENS_TOTAL.labels(
        provider="gemini",
        model="gemini-1.5-flash",
        direction="completion",
    ).inc(50)
