from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.batch import BatchJob
from app.models.job import Job
from app.schemas.batch import BatchJobCreate, BatchJobResponse, BatchJobListResponse
from app.services.batch import enqueue_batch_job

router = APIRouter()


def _validate_job_ids(
    db: Session, user_id: uuid.UUID, job_ids: List[uuid.UUID]
) -> List[Job]:
    """Validate that all job IDs exist and belong to the user's jobs."""
    # For batch operations, we allow jobs from any source (user's own + imported)
    # but we verify they exist in the database
    jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
    found_ids = {job.id for job in jobs}
    missing = set(job_ids) - found_ids
    if missing:
        raise HTTPException(status_code=404, detail=f"Jobs not found: {missing}")
    return jobs


@router.post("", response_model=BatchJobResponse)
def create_batch_job(
    batch_in: BatchJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new batch job and enqueue it for processing."""
    # Validate job_ids exist
    _validate_job_ids(db, current_user.id, batch_in.job_ids)

    # Build payload
    payload = {"job_ids": [str(j) for j in batch_in.job_ids], "params": batch_in.params}

    # Create batch job record
    batch_job = BatchJob(
        user_id=current_user.id,
        operation_type=batch_in.operation_type,
        status="pending",
        total_items=len(batch_in.job_ids),
        processed_items=0,
        succeeded_items=0,
        failed_items=0,
        payload=payload,
        result_summary={},
        cancel_requested=False,
    )
    db.add(batch_job)
    db.commit()
    db.refresh(batch_job)

    # Enqueue for processing
    enqueue_batch_job(batch_job.id)

    return batch_job


@router.get("", response_model=BatchJobListResponse)
def list_batch_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
    operation_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    """List batch jobs for the current user."""
    query = db.query(BatchJob).filter(BatchJob.user_id == current_user.id)

    if status:
        query = query.filter(BatchJob.status == status)
    if operation_type:
        query = query.filter(BatchJob.operation_type == operation_type)

    total = query.count()
    jobs = query.order_by(BatchJob.created_at.desc()).offset(skip).limit(limit).all()

    return BatchJobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)


@router.get("/{batch_id}", response_model=BatchJobResponse)
def get_batch_job(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single batch job with full result summary."""
    batch_job = (
        db.query(BatchJob)
        .filter(BatchJob.id == batch_id, BatchJob.user_id == current_user.id)
        .first()
    )
    if not batch_job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return batch_job


@router.post("/{batch_id}/retry", response_model=BatchJobResponse)
def retry_batch_job(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retry failed items in a batch job by creating a new batch job."""
    original = (
        db.query(BatchJob)
        .filter(BatchJob.id == batch_id, BatchJob.user_id == current_user.id)
        .first()
    )
    if not original:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if original.status not in ("failed", "partial"):
        raise HTTPException(
            status_code=400,
            detail="Can only retry failed or partially completed batch jobs",
        )

    # Extract failed job_ids from result_summary
    failed_ids = [
        uuid.UUID(job_id)
        for job_id, result in original.result_summary.items()
        if result.get("status") == "error"
    ]

    if not failed_ids:
        raise HTTPException(status_code=400, detail="No failed items to retry")

    # Create new batch job with only failed items
    retry_job = BatchJob(
        user_id=current_user.id,
        operation_type=original.operation_type,
        status="pending",
        total_items=len(failed_ids),
        processed_items=0,
        succeeded_items=0,
        failed_items=0,
        payload={
            "job_ids": [str(j) for j in failed_ids],
            "params": original.payload.get("params", {}),
        },
        result_summary={},
        cancel_requested=False,
    )
    db.add(retry_job)
    db.commit()
    db.refresh(retry_job)

    # Enqueue for processing
    enqueue_batch_job(retry_job.id)

    return retry_job


@router.post("/{batch_id}/cancel", response_model=BatchJobResponse)
def cancel_batch_job(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Request cancellation of a running batch job."""
    batch_job = (
        db.query(BatchJob)
        .filter(BatchJob.id == batch_id, BatchJob.user_id == current_user.id)
        .first()
    )
    if not batch_job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if batch_job.status not in ("pending", "running"):
        raise HTTPException(
            status_code=400, detail=f"Cannot cancel job with status: {batch_job.status}"
        )

    batch_job.cancel_requested = True
    db.commit()
    db.refresh(batch_job)

    return batch_job
