"""
Batch job service functions.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from app.models.batch import BatchJob


logger = logging.getLogger(__name__)


def _utcnow():
    return datetime.now(timezone.utc)


def _run_batch_job(batch_job_id: uuid.UUID) -> dict:
    """Synchronous helper that processes a batch job."""
    from app.services.batch_operations import (
        batch_analyze_item, batch_score_item, batch_tag_item, batch_archive_item
    )
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        batch_job = db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        if not batch_job:
            return {"error": "BatchJob not found"}

        batch_job.status = "running"
        batch_job.started_at = _utcnow()
        batch_job.total_items = len(batch_job.payload["job_ids"])
        db.commit()

        task_map = {
            "analyze": batch_analyze_item,
            "score": batch_score_item,
            "tag": batch_tag_item,
            "archive": batch_archive_item,
        }
        task_fn = task_map[batch_job.operation_type]
        params = batch_job.payload.get("params", {})

        for item_id in batch_job.payload["job_ids"]:
            # Check cancel flag
            db.refresh(batch_job)
            if batch_job.cancel_requested:
                batch_job.status = "cancelled"
                batch_job.completed_at = _utcnow()
                db.commit()
                return {"status": "cancelled", "processed": batch_job.processed_items}

            try:
                result = task_fn(
                    uuid.UUID(item_id),
                    batch_job.user_id,
                    params,
                    db
                )
                batch_job.succeeded_items += 1
                batch_job.result_summary[item_id] = {"status": "success", "result": result}
            except Exception as e:
                batch_job.failed_items += 1
                batch_job.result_summary[item_id] = {"status": "error", "error": str(e)}

            batch_job.processed_items += 1

            # Commit progress every 10 items
            if batch_job.processed_items % 10 == 0:
                db.commit()

        # Final status
        if batch_job.failed_items == 0:
            batch_job.status = "completed"
        else:
            batch_job.status = "partial"
        batch_job.completed_at = _utcnow()
        db.commit()

        return {"status": batch_job.status, "processed": batch_job.processed_items}

    except Exception as exc:
        logger.exception("batch_job_failed", extra={"batch_job_id": str(batch_job_id)})
        if 'batch_job' in locals() and batch_job:
            batch_job.status = "failed"
            batch_job.completed_at = _utcnow()
            db.commit()
        raise
    finally:
        db.close()


def enqueue_batch_job(batch_job_id: uuid.UUID) -> None:
    """Dispatch batch job to Celery (sync fallback for tests)."""
    try:
        from app.worker.celery_app import celery_app
        celery_app.send_task(
            "app.worker.tasks.process_batch_job",
            kwargs={"batch_job_id": str(batch_job_id)},
            queue="batch_processing",
        )
        logger.info("batch_job_enqueued", extra={"batch_job_id": str(batch_job_id)})
    except Exception as exc:
        logger.warning(
            "batch_celery_unavailable_running_sync",
            extra={"error": str(exc)},
        )
        _run_batch_job(batch_job_id)