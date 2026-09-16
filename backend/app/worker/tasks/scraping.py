import uuid
from datetime import datetime, timezone
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from app.services.job_import import _scrape_and_import_job_sync
import logging

logger = logging.getLogger(__name__)

@shared_task(
    name="app.worker.tasks.scrape_and_import_job",
    bind=True,
    max_retries=2,
    default_retry_delay=15,
    acks_late=True,
    time_limit=90,  # Hard limit
    soft_time_limit=75,
    queue="scraping"
)
def scrape_and_import_job(self, import_id: str, url: str, source: str, user_id: str):
    try:
        return _scrape_and_import_job_sync(import_id, url, source, user_id)
    except SoftTimeLimitExceeded:
        logger.warning("scraping_timeout", extra={"import_id": import_id})
        return {"status": "failed", "error": "Scraping timed out"}
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15)
        return {"status": "failed", "error": str(exc)[:500]}
