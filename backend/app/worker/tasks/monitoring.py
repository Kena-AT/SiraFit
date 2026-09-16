from datetime import datetime, timedelta, timezone
from celery import shared_task
from app.core.database import SessionLocal
from app.models.job import JobImport
import logging

logger = logging.getLogger(__name__)

@shared_task(name="app.worker.tasks.detect_stuck_imports")
def detect_stuck_imports():
    db = SessionLocal()
    try:
        stuck_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        stuck_imports = db.query(JobImport).filter(
            JobImport.status == "processing",
            JobImport.created_at < stuck_threshold,
        ).all()
        
        for job_import in stuck_imports:
            job_import.status = "failed"
            job_import.error = "Scraping job lost (worker timeout or crash)"
            job_import.processed_at = datetime.now(timezone.utc)
            logger.warning("stuck_import_detected_and_marked_failed", extra={"import_id": str(job_import.id)})
        
        db.commit()
        return {"stuck_jobs_fixed": len(stuck_imports)}
    except Exception as exc:
        logger.exception("detect_stuck_imports_failed")
        db.rollback()
    finally:
        db.close()
