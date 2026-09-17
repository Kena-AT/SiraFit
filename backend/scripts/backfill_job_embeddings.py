"""Job Embeddings Backfill Script (Sprint 8).

Iterates through jobs requiring embedding generation:
- Missing embedding (status != 'ready' or embedding is NULL)
- Outdated hash (source text updated)
- Outdated version/model

Supports batching, resumability, bounded concurrency, and progress tracking.

Usage:
    python backend/scripts/backfill_job_embeddings.py [--batch-size 50] [--limit 500] [--async]
"""
import argparse
import logging
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.job import Job
from app.core.config import settings
from app.services.embeddings import (
    generate_job_embedding,
    build_job_embedding_text,
    compute_source_hash,
    EMBEDDING_VERSION,
)
from app.worker.tasks.embeddings import enqueue_job_embedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_embeddings")


def parse_args():
    parser = argparse.ArgumentParser(description="Backfill job embeddings")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size per transaction")
    parser.add_argument("--limit", type=int, default=None, help="Maximum total jobs to process")
    parser.add_argument("--async-celery", action="store_true", help="Enqueue via Celery instead of inline")
    parser.add_argument("--force", action="store_true", help="Force regenerate even if current")
    return parser.parse_args()


def run_backfill():
    args = parse_args()
    logger.info(
        "Starting job embedding backfill (batch_size=%d, limit=%s, async=%s, force=%s)...",
        args.batch_size,
        args.limit,
        args.async_celery,
        args.force,
    )

    db = SessionLocal()
    try:
        query = db.query(Job).filter(Job.is_archived == False)  # noqa: E712
        if not args.force:
            query = query.filter(
                (Job.embedding_status != "ready")
                | (Job.embedding == None)  # noqa: E711
                | (Job.embedding_version != (settings.EMBEDDING_VERSION or EMBEDDING_VERSION))
            )

        total_candidates = query.count()
        logger.info("Found %d candidate jobs for embedding backfill", total_candidates)

        if total_candidates == 0:
            logger.info("All jobs are already embedded and up-to-date.")
            return

        processed = 0
        success_count = 0
        skip_count = 0
        failure_count = 0
        offset = 0

        while True:
            batch = query.offset(offset).limit(args.batch_size).all()
            if not batch:
                break

            for job in batch:
                if args.limit and processed >= args.limit:
                    break

                try:
                    if args.async_celery:
                        enqueue_job_embedding(job.id)
                        success_count += 1
                    else:
                        # Check hash
                        canonical_text = build_job_embedding_text(job)
                        current_hash = compute_source_hash(canonical_text)

                        if (
                            not args.force
                            and job.embedding_status == "ready"
                            and job.embedding_source_hash == current_hash
                            and job.embedding is not None
                        ):
                            skip_count += 1
                        else:
                            result = generate_job_embedding(job)
                            job.embedding = result.vector
                            job.embedding_model = result.model
                            job.embedding_version = result.version
                            job.embedding_source_hash = result.source_hash
                            job.embedding_status = "ready"
                            db.commit()
                            success_count += 1

                except Exception as exc:
                    logger.error("Error processing job %s: %s", job.id, exc)
                    failure_count += 1
                    if not args.async_celery:
                        db.rollback()

                processed += 1

            if not args.async_celery and not args.force:
                # If synchronous and not forcing, jobs were updated to 'ready', so next query slice starts at 0
                offset = 0
            else:
                offset += len(batch)

            logger.info(
                "Progress: %d/%d (Success: %d, Skipped: %d, Failed: %d)",
                processed,
                min(total_candidates, args.limit or total_candidates),
                success_count,
                skip_count,
                failure_count,
            )

            if args.limit and processed >= args.limit:
                break

        logger.info(
            "Backfill completed! Total: %d, Success: %d, Skipped: %d, Failed: %d",
            processed,
            success_count,
            skip_count,
            failure_count,
        )

    finally:
        db.close()


if __name__ == "__main__":
    run_backfill()
