"""
Celery application instance for SiraFit.

Configuration sources (in order of precedence):
  1. Explicit environment variables (CELERY_BROKER_URL, CELERY_RESULT_BACKEND)
  2. Fall back to REDIS_URL for the broker when no explicit Celery URLs are set.

The Celery app is imported by the worker container (see Dockerfile.celery) and
by application code that needs to enqueue background tasks (e.g. resume
generation). When Celery is not available (e.g. local dev without Redis), the
task wrappers in `app.worker.tasks` gracefully fall back to synchronous
execution so the API keeps working.
"""
from __future__ import annotations

import logging

from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)


def _broker_url() -> str:
    if settings.CELERY_BROKER_URL:
        return settings.CELERY_BROKER_URL
    return settings.REDIS_URL


def _result_backend() -> str:
    if settings.CELERY_RESULT_BACKEND:
        return settings.CELERY_RESULT_BACKEND
    return settings.REDIS_URL


celery_app = Celery(
    "sirafit",
    broker=_broker_url(),
    backend=_result_backend(),
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_queue="sirafit",
    task_routes={
        "app.worker.tasks.generate_resume_task": {"queue": "resume_generation"},
        "app.worker.tasks.render_cover_letter_pdf_task": {"queue": "pdf_rendering"},
        "app.worker.tasks.render_resume_pdf_task": {"queue": "pdf_rendering"},
    },
)

celery_app.autodiscover_tasks(["app.worker"])


__all__ = ["celery_app"]
