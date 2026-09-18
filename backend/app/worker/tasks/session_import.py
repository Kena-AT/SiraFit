import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.job import Job, JobImport, JobImportItem
from app.services.session_management import get_user_session, record_session_audit
from app.services.scraping.session_importer import (
    SavedJobsImporter,
    SessionExpiredError,
    ScraperStructureError,
    ScraperFetchError,
    InvalidSessionConfig,
)
from app.services.scraping.extraction import normalize_url
from app.services.scraping.scrapling_fetcher import fetch_job_html, parse_job_html
from app.services.job_import import parse_job_from_url, normalize_job, check_duplicate

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@shared_task(
    name="app.worker.tasks.import_saved_jobs_task",
    bind=True,
    max_retries=2,
    acks_late=True,
    time_limit=360,
    soft_time_limit=300,
    queue="scraping",
)
def import_saved_jobs_task(
    self,
    user_id: str,
    import_id: str,
    platform: str,
) -> Dict[str, Any]:
    """Orchestrate authenticated saved-job discovery and queue child import tasks.

    Does NOT synchronously scrape 500 jobs inline. Discovers references and
    dispatches individual single-job import tasks.
    """
    db = SessionLocal()
    u_id = uuid.UUID(user_id)
    imp_id = uuid.UUID(import_id)

    try:
        job_import = db.query(JobImport).filter(JobImport.id == imp_id).first()
        if not job_import:
            logger.warning(
                "session_import_record_not_found", extra={"import_id": import_id}
            )
            return {"status": "failed", "error": "JobImport not found"}

        job_import.status = "processing"
        db.commit()

        # 1. Load active session & decrypt in memory
        session_rec, session_data = get_user_session(db, u_id, platform, decrypt=True)

        if not session_rec or not session_rec.is_active:
            job_import.status = "failed"
            job_import.error = "Session unavailable or deleted"
            job_import.processed_at = _utcnow()
            db.commit()
            return {"status": "failed", "error": "Session unavailable or deleted"}

        if not session_data:
            # Expired or decryption failure
            job_import.status = "failed"
            job_import.error = (
                "Session has expired or credentials could not be decrypted"
            )
            job_import.processed_at = _utcnow()
            db.commit()
            return {
                "status": "failed",
                "error": "Session has expired or invalid credentials",
            }

        # 2. Discover saved jobs
        importer = SavedJobsImporter()
        try:
            references, discovery_status = importer.fetch_saved_jobs_list(
                platform, session_data
            )
        except SessionExpiredError:
            job_import.status = "failed"
            job_import.error = "Session expired during saved-job discovery"
            job_import.processed_at = _utcnow()
            db.commit()
            record_session_audit(
                db,
                u_id,
                platform,
                action="expired",
                result="failure",
                error_code="session_expired",
            )
            return {"status": "failed", "error": "Session expired"}
        except (ScraperStructureError, ScraperFetchError, InvalidSessionConfig) as exc:
            job_import.status = "failed"
            job_import.error = f"Discovery failed: {exc}"
            job_import.processed_at = _utcnow()
            db.commit()
            record_session_audit(
                db,
                u_id,
                platform,
                action="failed",
                result="failure",
                error_code=exc.__class__.__name__,
            )
            return {"status": "failed", "error": str(exc)}

        # 3. Handle zero saved jobs
        if discovery_status == "completed_empty" or not references:
            job_import.status = "completed_empty"
            job_import.total_found = 0
            job_import.ok_count = 0
            job_import.fail_count = 0
            job_import.processed_at = _utcnow()
            db.commit()
            return {"status": "completed_empty", "discovered": 0}

        # 4. Queue discovered jobs asynchronously
        job_import.total_found = len(references)
        job_import.status = "queued_batch"
        db.commit()

        for ref in references:
            item = JobImportItem(
                import_id=job_import.id,
                job_id=None,
                status="pending",
                title_guess=ref.title_hint or ref.external_id,
            )
            db.add(item)
            db.commit()
            db.refresh(item)

            import_single_saved_job.delay(
                item_id=str(item.id),
                import_id=str(job_import.id),
                url=ref.url,
                external_id=ref.external_id or ref.url,
                user_id=user_id,
            )

        return {"status": "queued_batch", "discovered": len(references)}

    except SoftTimeLimitExceeded:
        logger.warning(
            "session_discovery_timeout",
            extra={"import_id": import_id, "platform": platform},
        )
        try:
            ji = db.query(JobImport).filter(JobImport.id == imp_id).first()
            if ji and ji.status != "completed":
                ji.status = "failed"
                ji.error = "Saved-jobs discovery timed out (soft limit)"
                ji.processed_at = _utcnow()
                db.commit()
        except Exception:
            db.rollback()
        return {"status": "failed", "error": "Discovery timed out"}
    except Exception as exc:
        logger.exception(
            "session_importer_task_unhandled_error", extra={"import_id": import_id}
        )
        try:
            ji = db.query(JobImport).filter(JobImport.id == imp_id).first()
            if ji and ji.status != "completed":
                ji.status = "failed"
                ji.error = str(exc)[:500]
                ji.processed_at = _utcnow()
                db.commit()
        except Exception:
            db.rollback()
        return {"status": "failed", "error": str(exc)[:500]}
    finally:
        db.close()


@shared_task(
    name="app.worker.tasks.import_single_saved_job",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
    time_limit=90,
    soft_time_limit=75,
    queue="scraping",
)
def import_single_saved_job(
    self,
    item_id: str,
    import_id: str,
    url: str,
    external_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """Import an individual saved job discovered by the session task."""
    db = SessionLocal()
    it_id = uuid.UUID(item_id)
    imp_id = uuid.UUID(import_id)

    try:
        item = db.query(JobImportItem).filter(JobImportItem.id == it_id).first()
        job_import = db.query(JobImport).filter(JobImport.id == imp_id).first()

        if not item or not job_import:
            return {"status": "failed", "error": "Item or import not found"}

        # Check duplicate
        clean_url = normalize_url(url)
        parsed_stub = parse_job_from_url(clean_url)
        parsed_stub["external_id"] = external_id
        normalized = normalize_job(parsed_stub)

        existing_job = check_duplicate(db, normalized)
        if existing_job:
            item.status = "duplicate"
            item.job_id = existing_job.id
            item.title_guess = existing_job.title
            job_import.fail_count += 1
            _check_batch_completion(db, job_import)
            db.commit()
            return {"status": "duplicate", "job_id": str(existing_job.id)}

        # Scrape and parse
        html = None
        try:
            html = fetch_job_html(clean_url)
        except Exception:
            pass

        parsed = parsed_stub
        if html:
            try:
                enriched = parse_job_html(html, clean_url)
                if enriched:
                    for k in (
                        "title",
                        "company",
                        "location",
                        "description",
                        "salary_min",
                        "salary_max",
                        "currency",
                        "tags",
                    ):
                        if enriched.get(k) is not None:
                            parsed[k] = enriched[k]
            except Exception:
                pass

        normalized_final = normalize_job(parsed)
        job = Job(
            external_id=external_id,
            title=normalized_final["title"],
            company=normalized_final["company"],
            location=normalized_final.get("location"),
            description=normalized_final.get("description"),
            salary_min=normalized_final.get("salary_min"),
            salary_max=normalized_final.get("salary_max"),
            currency=normalized_final.get("currency"),
            tags=normalized_final.get("tags", []),
            url=clean_url,
            source=normalized_final.get("source", "saved_import"),
            import_id=job_import.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        item.status = "imported"
        item.job_id = job.id
        item.title_guess = job.title
        job_import.ok_count += 1

        _check_batch_completion(db, job_import)
        db.commit()
        return {"status": "imported", "job_id": str(job.id)}

    except Exception as exc:
        db.rollback()
        db2 = SessionLocal()
        try:
            it = db2.query(JobImportItem).filter(JobImportItem.id == it_id).first()
            ji = db2.query(JobImport).filter(JobImport.id == imp_id).first()
            if it:
                it.status = "failed"
                it.error_message = str(exc)[:500]
            if ji:
                ji.fail_count += 1
                _check_batch_completion(db2, ji)
            db2.commit()
        except Exception:
            db2.rollback()
        finally:
            db2.close()
        return {"status": "failed", "error": str(exc)[:500]}
    finally:
        db.close()


def _check_batch_completion(db: Session, job_import: JobImport) -> None:
    """Check if all items in a batch import have settled into a terminal state."""
    processed = job_import.ok_count + job_import.fail_count
    if job_import.total_found > 0 and processed >= job_import.total_found:
        if job_import.fail_count == 0:
            job_import.status = "completed"
        elif job_import.ok_count > 0:
            job_import.status = "completed_partial"
        else:
            job_import.status = "failed"
        job_import.processed_at = _utcnow()
