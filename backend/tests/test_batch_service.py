"""
Tests for batch job service.
"""
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from sqlalchemy.orm import Session
from app.models.batch import BatchJob
from app.models.job import Job
from app.services.batch import _run_batch_job, enqueue_batch_job


@pytest.fixture
def mock_batch_job(db: Session) -> BatchJob:
    job1 = Job(id=uuid.uuid4(), title="Job 1", company="Company 1", source="linkedin", external_id="1")
    job2 = Job(id=uuid.uuid4(), title="Job 2", company="Company 2", source="linkedin", external_id="2")
    db.add_all([job1, job2])
    db.commit()

    batch_job = BatchJob(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        operation_type="analyze",
        status="pending",
        total_items=2,
        processed_items=0,
        succeeded_items=0,
        failed_items=0,
        payload={"job_ids": [str(job1.id), str(job2.id)], "params": {}},
        result_summary={},
        cancel_requested=False,
    )
    db.add(batch_job)
    db.commit()
    return batch_job


def test_run_batch_job_success(db: Session, mock_batch_job: BatchJob):
    batch_job_id = mock_batch_job.id
    
    async def mock_analyze(*args, **kwargs):
        return {"score": 85, "status": "done"}

    with patch("app.core.database.SessionLocal", return_value=db), \
         patch("app.services.batch_operations.batch_analyze_item", side_effect=mock_analyze):
        
        result = _run_batch_job(batch_job_id)
        
        assert result["status"] == "completed"
        assert result["processed"] == 2
        
        # Verify the batch job was updated (query fresh)
        updated_job = db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        assert updated_job is not None
        assert updated_job.status == "completed"
        assert updated_job.processed_items == 2
        assert updated_job.succeeded_items == 2
        assert updated_job.failed_items == 0


def test_run_batch_job_partial_failure(db: Session, mock_batch_job: BatchJob):
    batch_job_id = mock_batch_job.id
    
    async def mock_analyze(*args, **kwargs):
        # Fail on second call
        if mock_analyze.calls == 1:
            mock_analyze.calls += 1
            raise Exception("Failed")
        mock_analyze.calls += 1
        return {"score": 85}
    mock_analyze.calls = 0

    with patch("app.core.database.SessionLocal", return_value=db), \
         patch("app.services.batch_operations.batch_analyze_item", side_effect=mock_analyze):
        
        result = _run_batch_job(batch_job_id)
        
        assert result["status"] == "partial"
        assert result["processed"] == 2
        
        # Verify the batch job was updated (query fresh)
        updated_job = db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        assert updated_job is not None
        assert updated_job.status == "partial"
        assert updated_job.processed_items == 2
        assert updated_job.succeeded_items == 1
        assert updated_job.failed_items == 1


def test_run_batch_job_cancelled(db: Session, mock_batch_job: BatchJob):
    batch_job_id = mock_batch_job.id
    
    # Set cancel_requested to True
    mock_batch_job.cancel_requested = True
    db.commit()
    
    with patch("app.core.database.SessionLocal", return_value=db):
        result = _run_batch_job(batch_job_id)
    
    assert result["status"] == "cancelled"
    assert result["processed"] == 0


def test_enqueue_batch_job_success(db: Session, mock_batch_job: BatchJob):
    with patch("app.worker.celery_app.celery_app") as mock_celery:
        mock_send_task = MagicMock()
        mock_celery.send_task = mock_send_task
        
        enqueue_batch_job(mock_batch_job.id)
        
        mock_send_task.assert_called_once_with(
            "app.worker.tasks.process_batch_job",
            kwargs={"batch_job_id": str(mock_batch_job.id)},
            queue="batch_processing",
        )


def test_enqueue_batch_job_fallback(db: Session, mock_batch_job: BatchJob):
    with patch("app.worker.celery_app.celery_app.send_task", side_effect=Exception("Celery unavailable")), \
         patch("app.core.database.SessionLocal", return_value=db), \
         patch("app.services.batch._run_batch_job") as mock_run:
        
        enqueue_batch_job(mock_batch_job.id)
        
        mock_run.assert_called_once_with(mock_batch_job.id)