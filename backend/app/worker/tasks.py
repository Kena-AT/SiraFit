"""
Celery tasks for asynchronous resume generation and PDF rendering.

Three queues are used:
  - ``resume_generation`` — AI resume tailoring (slow, I/O-bound)
  - ``pdf_rendering``     — HTML → PDF conversion (CPU-bound but offloads
                            heavy work from the request thread)
  - ``batch_processing``  — Batch operations (analyze, score, tag, archive)
  - ``notifications``     — Email reminders and notification processing

Every enqueue helper falls back to synchronous execution when the Celery
broker (Redis) is unreachable, so the API keeps working in environments
without Redis (tests, local dev). The fallback is logged at WARNING level
so it is visible in production.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
from typing import Any

from app.core.database import SessionLocal
from app.models.cover_letter import CoverLetter
from app.models.job import ResumeVersion, Job, AuditLog
from app.models.profile import Profile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dead-letter queue base task
# ---------------------------------------------------------------------------


def _define_base_task():
    """Build a Celery base Task that routes exhausted retries to a DLQ."""
    try:
        from app.worker.celery_app import celery_app as _celery

        class _BaseRetryTask(_celery.Task):
            abstract = True
            max_retries = 3
            default_retry_delay = 30

            def on_failure(self, exc, task_id, args, kwargs, einfo):
                # Only dead-letter once retries are actually exhausted.
                if self.request.retries >= self.max_retries:
                    try:
                        _celery.send_task(
                            "app.worker.tasks.handle_dead_letter",
                            kwargs={
                                "task_name": self.name,
                                "args": list(args),
                                "kwargs": kwargs,
                                "error": str(exc),
                            },
                        )
                    except Exception:
                        logger.warning(
                            "dlq_dispatch_failed",
                            extra={"task": self.name, "error": str(exc)},
                        )

        return _BaseRetryTask
    except Exception:
        logger.warning("celery_base_task_unavailable")
        return None


BaseRetryTask = _define_base_task()


# ---------------------------------------------------------------------------
# Storage helper for rendered PDFs
# ---------------------------------------------------------------------------


def _pdf_storage_dir() -> str:
    """Return (creating if needed) the directory used to store rendered PDFs.

    Uses the OS temp dir so it works in any deployment without extra config.
    The path is deterministic per-process so workers and the API agree.
    """
    base = os.path.join(tempfile.gettempdir(), "sirafit_pdfs")
    os.makedirs(base, exist_ok=True)
    return base


def _save_pdf_bytes(pdf_bytes: bytes, name: str) -> str:
    """Persist ``pdf_bytes`` to disk under ``name`` and return the full path."""
    path = os.path.join(_pdf_storage_dir(), f"{name}.pdf")
    with open(path, "wb") as fh:
        fh.write(pdf_bytes)
    return path


# ---------------------------------------------------------------------------
# Resume generation
# ---------------------------------------------------------------------------


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
                extra={
                    "version_id": str(version_id),
                    "profile_id": str(profile_id),
                    "job_id": str(job_id),
                },
            )
            version = (
                db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
            )
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
            logger.error(
                "resume_generation_version_not_found",
                extra={"version_id": str(version_id)},
            )
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
        logger.exception(
            "resume_generation_failed", extra={"version_id": str(version_id)}
        )
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
    """Dispatch resume generation to the Celery queue (sync fallback)."""
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
# PDF rendering — resume
# ---------------------------------------------------------------------------


def _run_resume_pdf_render(version_id: uuid.UUID) -> None:
    """Render a ResumeVersion to PDF and persist the path on the row."""
    from app.services.resume_export import export_resume_pdf

    db = SessionLocal()
    try:
        version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
        if not version:
            logger.error(
                "resume_pdf_version_not_found", extra={"version_id": str(version_id)}
            )
            return

        version.status = "processing"
        db.commit()

        buf = export_resume_pdf(version)
        path = _save_pdf_bytes(buf.getvalue(), f"resume-{version_id}")

        version.status = "completed"
        # ResumeVersion has no pdf_url column; we surface the path via the
        # owning Resume row so the download endpoint can find it.
        if version.resume:
            version.resume.pdf_url = path
        db.commit()

        log = AuditLog(
            user_id=version.resume.user_id if version.resume else None,
            action="rendered_resume_pdf",
            entity_type="resume_version",
            details={"version_id": str(version_id), "path": path},
        )
        db.add(log)
        db.commit()
    except Exception:  # pragma: no cover - defensive
        logger.exception(
            "resume_pdf_render_failed", extra={"version_id": str(version_id)}
        )
        db.rollback()
        version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
        if version:
            version.status = "failed"
            db.commit()
    finally:
        db.close()


def enqueue_resume_pdf_render(version_id: uuid.UUID) -> None:
    """Dispatch resume PDF rendering to the ``pdf_rendering`` queue (sync fallback)."""
    try:
        from app.worker.celery_app import celery_app

        celery_app.send_task(
            "app.worker.tasks.render_resume_pdf_task",
            kwargs={"version_id": str(version_id)},
            queue="pdf_rendering",
        )
        logger.info("resume_pdf_enqueued", extra={"version_id": str(version_id)})
    except Exception as exc:
        logger.warning(
            "resume_pdf_celery_unavailable_running_sync",
            extra={"error": str(exc)},
        )
        _run_resume_pdf_render(version_id)


# ---------------------------------------------------------------------------
# PDF rendering — cover letter
# ---------------------------------------------------------------------------


def _run_cover_letter_pdf_render(letter_id: uuid.UUID) -> None:
    """Render a CoverLetter to PDF and persist the path on the row."""
    from app.services.cover_letter_generation import render_cover_letter_html
    from app.services.pdf_rendering import render_html_to_pdf

    db = SessionLocal()
    try:
        letter = db.query(CoverLetter).filter(CoverLetter.id == letter_id).first()
        if not letter:
            logger.error(
                "cover_letter_pdf_not_found", extra={"letter_id": str(letter_id)}
            )
            return

        letter.status = "processing"
        db.commit()

        html = render_cover_letter_html(
            letter.body, template=letter.template or "classic"
        )
        pdf_bytes = render_html_to_pdf(html)
        path = _save_pdf_bytes(pdf_bytes, f"cover-letter-{letter_id}")

        letter.pdf_url = path
        letter.status = "completed"
        db.commit()

        log = AuditLog(
            user_id=letter.user_id,
            action="rendered_cover_letter_pdf",
            entity_type="cover_letter",
            details={"letter_id": str(letter_id), "path": path},
        )
        db.add(log)
        db.commit()
    except Exception:  # pragma: no cover - defensive
        logger.exception(
            "cover_letter_pdf_render_failed", extra={"letter_id": str(letter_id)}
        )
        db.rollback()
        letter = db.query(CoverLetter).filter(CoverLetter.id == letter_id).first()
        if letter:
            letter.status = "failed"
            db.commit()
    finally:
        db.close()


def enqueue_cover_letter_pdf_render(letter_id: uuid.UUID) -> None:
    """Dispatch cover letter PDF rendering to the ``pdf_rendering`` queue (sync fallback)."""
    try:
        from app.worker.celery_app import celery_app

        celery_app.send_task(
            "app.worker.tasks.render_cover_letter_pdf_task",
            kwargs={"letter_id": str(letter_id)},
            queue="pdf_rendering",
        )
        logger.info("cover_letter_pdf_enqueued", extra={"letter_id": str(letter_id)})
    except Exception as exc:
        logger.warning(
            "cover_letter_pdf_celery_unavailable_running_sync",
            extra={"error": str(exc)},
        )
        _run_cover_letter_pdf_render(letter_id)


# ---------------------------------------------------------------------------
# Celery task definitions
# ---------------------------------------------------------------------------

try:
    from app.worker.celery_app import celery_app

    @celery_app.task(
        name="app.worker.tasks.generate_resume_task",
        bind=True,
        base=BaseRetryTask,
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

    @celery_app.task(
        name="app.worker.tasks.render_resume_pdf_task",
        bind=True,
        base=BaseRetryTask,
        max_retries=2,
        default_retry_delay=5,
        acks_late=True,
    )
    def render_resume_pdf_task(self, version_id: str) -> dict[str, Any]:
        """Celery task wrapper around `_run_resume_pdf_render`."""
        _run_resume_pdf_render(uuid.UUID(version_id))
        return {"version_id": version_id, "status": "rendered"}

    @celery_app.task(
        name="app.worker.tasks.render_cover_letter_pdf_task",
        bind=True,
        base=BaseRetryTask,
        max_retries=2,
        default_retry_delay=5,
        acks_late=True,
    )
    def render_cover_letter_pdf_task(self, letter_id: str) -> dict[str, Any]:
        """Celery task wrapper around `_run_cover_letter_pdf_render`."""
        _run_cover_letter_pdf_render(uuid.UUID(letter_id))
        return {"letter_id": letter_id, "status": "rendered"}

except Exception as exc:  # pragma: no cover - import-time broker failure
    logger.warning("celery_task_registration_skipped", extra={"error": str(exc)})


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

# Batch job processing is implemented in app/services/batch.py (enqueue_batch_job)
# and app/services/batch_operations.py (item handlers).
# This file only registers the Celery task wrapper.

try:
    from app.worker.celery_app import celery_app

    @celery_app.task(
        name="app.worker.tasks.process_batch_job",
        bind=True,
        base=BaseRetryTask,
        max_retries=3,
        default_retry_delay=30,
        acks_late=True,
        time_limit=1800,
    )
    def process_batch_job(self, batch_job_id: str) -> dict:
        """Celery task wrapper - delegates to app.services.batch._run_batch_job."""
        from app.services.batch import _run_batch_job

        _run_batch_job(uuid.UUID(batch_job_id))
        return {"batch_job_id": batch_job_id, "status": "dispatched"}

except Exception as exc:  # pragma: no cover - import-time broker failure
    logger.warning("celery_task_registration_skipped_batch", extra={"error": str(exc)})


# Notification worker tasks

try:

    @celery_app.task(
        name="app.worker.tasks.send_notification_task",
        bind=True,
        base=BaseRetryTask,
        max_retries=3,
        default_retry_delay=60,
        acks_late=True,
    )
    def send_notification_task(self, notification_id: str) -> dict:
        """Celery task to send a notification (email, push, etc.)."""
        from app.services.notification_service import send_notification_email

        send_notification_email(uuid.UUID(notification_id))
        return {"notification_id": notification_id, "status": "sent"}

    @celery_app.task(
        name="app.worker.tasks.check_reminders_task",
        bind=True,
        base=BaseRetryTask,
        max_retries=0,
        acks_late=True,
    )
    def check_reminders_task(self) -> dict:
        """Celery task to check for upcoming follow-ups and send reminders."""
        from app.services.notification_service import check_and_send_reminders

        check_and_send_reminders()
        return {"status": "checked"}

except Exception as exc:  # pragma: no cover - import-time broker failure
    logger.warning(
        "celery_task_registration_skipped_notifications", extra={"error": str(exc)}
    )


try:
    from app.worker.celery_app import celery_app

    @celery_app.task(
        name="app.worker.tasks.handle_dead_letter", bind=True, max_retries=0
    )
    def handle_dead_letter(
        self, task_name=None, args=None, kwargs=None, error=None
    ) -> dict:
        """Dead-letter collector: records permanently failed tasks for inspection."""
        logger.error(
            "task_dead_lettered",
            extra={
                "task_name": task_name,
                "args": args,
                "kwargs": kwargs,
                "error": error,
            },
        )
        return {"dead_lettered": task_name}
except Exception as exc:  # pragma: no cover - import-time broker failure
    logger.warning("celery_dlq_task_unavailable", extra={"error": str(exc)})


__all__ = [
    "enqueue_resume_generation",
    "enqueue_resume_pdf_render",
    "enqueue_cover_letter_pdf_render",
    "generate_resume_task",
    "render_resume_pdf_task",
    "render_cover_letter_pdf_task",
    "process_batch_job",
    "send_notification_task",
    "check_reminders_task",
]
