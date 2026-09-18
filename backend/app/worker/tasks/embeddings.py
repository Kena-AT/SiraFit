"""Celery background tasks for job embedding generation (Sprint 8).

Handles asynchronous embedding generation, idempotency checking,
retry classification, and embedding status transitions.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.core.config import settings
from app.core import metrics
from app.models.job import Job
from app.services.embeddings import (
    generate_job_embedding,
    build_job_embedding_text,
    compute_source_hash,
    EMBEDDING_VERSION,
)
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _utcnow():
    return datetime.now(timezone.utc)


@celery_app.task(
    bind=True,
    name="app.worker.tasks.embeddings.generate_job_embedding_task",
    max_retries=3,
    default_retry_delay=15,
)
def generate_job_embedding_task(self, job_id: str | uuid.UUID) -> dict:
    """Generate and persist vector embedding for a Job.

    Idempotent: skips if the job's embedding_source_hash matches current content
    and status is ready.
    """
    if not settings.ENABLE_EMBEDDINGS:
        logger.info("Embeddings disabled via configuration. Skipping job %s", job_id)
        return {"status": "skipped", "reason": "embeddings_disabled"}

    start_time = time.perf_counter()
    session = SessionLocal()
    try:
        if isinstance(job_id, str):
            try:
                job_uuid = uuid.UUID(job_id)
            except ValueError:
                job_uuid = job_id
        else:
            job_uuid = job_id

        job = session.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            logger.warning("Job %s not found for embedding generation", job_id)
            return {"status": "error", "reason": "job_not_found"}

        # Calculate current canonical text and hash
        canonical_text = build_job_embedding_text(job)
        current_hash = compute_source_hash(canonical_text)

        # Check if already current and ready
        if (
            job.embedding_status == "ready"
            and job.embedding_source_hash == current_hash
            and job.embedding_version
            == (settings.EMBEDDING_VERSION or EMBEDDING_VERSION)
            and job.embedding is not None
        ):
            logger.debug("Job %s embedding is already up-to-date", job_id)
            return {"status": "noop", "job_id": str(job_id)}

        # Transition to processing
        job.embedding_status = "processing"
        session.commit()

        # Generate embedding
        result = generate_job_embedding(job)

        # Store vector and update metadata
        job.embedding = result.vector
        job.embedding_model = result.model
        job.embedding_version = result.version
        job.embedding_source_hash = result.source_hash
        job.embedding_status = "ready"
        job.embedding_updated_at = _utcnow()
        session.commit()

        duration = time.perf_counter() - start_time
        metrics.EMBEDDING_GENERATION_TOTAL.labels(
            operation="generate", status="success", model=result.model
        ).inc()
        metrics.EMBEDDING_GENERATION_DURATION_SECONDS.labels(
            model=result.model
        ).observe(duration)

        logger.info(
            "Successfully generated embedding for job %s in %.3fs", job_id, duration
        )
        return {"status": "ready", "job_id": str(job_id), "duration": duration}

    except Exception as exc:
        session.rollback()
        logger.exception("Failed to generate embedding for job %s: %s", job_id, exc)

        model_name = settings.EMBEDDING_MODEL or "unknown"
        metrics.EMBEDDING_GENERATION_TOTAL.labels(
            operation="generate", status="failure", model=model_name
        ).inc()

        # Retry transient exceptions
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2**self.request.retries * 5)

        # Mark failed if max retries exceeded
        try:
            job_failed = session.query(Job).filter(Job.id == job_uuid).first()
            if job_failed:
                job_failed.embedding_status = "failed"
                session.commit()
        except Exception:
            session.rollback()

        return {"status": "failed", "job_id": str(job_id), "error": str(exc)}

    finally:
        session.close()


def enqueue_job_embedding(job_id: str | uuid.UUID) -> None:
    """Helper to dispatch generate_job_embedding_task or run inline if broker unavailable."""
    if not settings.ENABLE_EMBEDDINGS:
        return

    try:
        generate_job_embedding_task.delay(str(job_id))
    except Exception as err:
        logger.warning(
            "Celery broker unavailable (%s); running embedding generation inline for job %s",
            err,
            job_id,
        )
        try:
            generate_job_embedding_task(str(job_id))
        except Exception as inline_err:
            logger.error("Inline embedding generation failed: %s", inline_err)
