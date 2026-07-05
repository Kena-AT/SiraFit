"""
Celery tasks for asynchronous resume generation.

The main entry point is `enqueue_resume_generation`, which dispatches work to the
Celery queue when Celery + Redis are available, and otherwise runs the work
synchronously inside the request lifecycle (useful for tests and local dev).

The task itself reuses the existing `app.services.resume_generation` service so
all validation, ATS scoring, and template rendering logic is shared between the
foreground and background paths.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from app.core.database import SessionLocal
from app.models.job import ResumeVersion, Job, AuditLog
from app.models.profile import Profile

logger = logging.getLogger(__name__)


def _run_generation(
    version_id: uuid.UUID,
    user_id: str,
    profile_id: uuid.UUID,
    job_id: uuid.UUID,
    template: str,
) -> None:
    """
    Synchronous helper that performs the real work.

    Opens its own DB session (Celery tasks don't have access to the request
    session), rehydrates the profile and job, calls the generation service, and
    persists the result back onto the ResumeVersion row.
    """
    import asyncio

    from app.services.resume_generation import generate_tailored_resume

    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        job = db.query(Job).filter(Job.id == job_id).first()
        if not profile or not job:
            logger.error(
                "resume_generation_missing_inputs",
                extra={"version_id": str(version_id), "profile_id": str(profile_id), "job_id": str(job_id)},
            )
            version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
            if version:
                version.status = "failed"
                version.tailoring_notes = "Missing profile or job"
                db.commit()
            return

        result = asyncio.run(
            generate_tailored_resume(
                db=db,
                user_id=user_id,
                profile=profile,
                job=job,
                template=template,
            )
        )

        version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
        if not version:
            logger.error("resume_generation_version_not_found", extra={"version_id": str(version_id)})
            return

        version.content = json.dumps(result["resume_data"])
        version.score = result["ats_score"]
        version.status = "completed" if result["is_valid"] else "failed"
        if not result["is_valid"] and result.get("issues"):
            version.tailoring_notes = "; ".join(result["issues"])[:500]
        db.commit()

        log = AuditLog(
            user_id=user_id,
            action="generated_resume",
            entity_type="resume_version",
            details={
                "version_id": str(version_id),
                "job_id": str(job_id),
                "template": template,
                "ats_score": result["ats_score"],
                "valid": result["is_valid"],
            },
        )
        db.add(log)
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("resume_generation_failed", extra={"version_id": str(version_id)})
        db.rollback()
        version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
        if version:
            version.status = "failed"
            version.tailoring_notes = f"Generation failed: {exc}"[:500]
            db.commit()
    finally:
        db.close()


def enqueue_resume_generation(
    version_id: uuid.UUID,
    user_id: str,
    profile_id: uuid.UUID,
    job_id: uuid.UUID,
    template: str = "minimal",
) -> None:
    """
    Dispatch resume generation to the Celery queue.

    Falls back to synchronous execution when the broker is unreachable so the
    API keeps working in environments without Redis (tests, local dev). The
    fallback is logged at warning level so it is visible in production.
    """
    try:
        from app.worker.celery_app import celery_app

        celery_app.send_task(
            "app.worker.tasks.generate_resume_task",
            kwargs={
                "version_id": str(version_id),
                "user_id": user_id,
                "profile_id": str(profile_id),
                "job_id": str(job_id),
                "template": template,
            },
            queue="resume_generation",
        )
        logger.info("resume_generation_enqueued", extra={"version_id": str(version_id)})
    except Exception as exc:
        logger.warning(
            "resume_generation_celery_unavailable_running_sync",
            extra={"error": str(exc)},
        )
        _run_generation(version_id, user_id, profile_id, job_id, template)


# ---------------------------------------------------------------------------
# Celery task definition
# ---------------------------------------------------------------------------

try:
    from app.worker.celery_app import celery_app

    @celery_app.task(
        name="app.worker.tasks.generate_resume_task",
        bind=True,
        max_retries=3,
        default_retry_delay=10,
        acks_late=True,
    )
    def generate_resume_task(
        self,
        version_id: str,
        user_id: str,
        profile_id: str,
        job_id: str,
        template: str = "minimal",
    ) -> dict[str, Any]:
        """Celery task wrapper around `_run_generation`."""
        _run_generation(
            uuid.UUID(version_id),
            user_id,
            uuid.UUID(profile_id),
            uuid.UUID(job_id),
            template,
        )
        return {"version_id": version_id, "status": "dispatched"}

except Exception as exc:  # pragma: no cover - import-time broker failure
    logger.warning("celery_task_registration_skipped", extra={"error": str(exc)})


__all__ = ["enqueue_resume_generation", "generate_resume_task"]
