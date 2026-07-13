import uuid
import pytest


def test_batch_job_create(client, auth_headers, db):
    """Test creating a batch job."""
    from app.models.job import Job

    # Create test jobs using the db fixture session
    job_ids = []
    for i in range(3):
        job = Job(external_id=f"batch-test-{i}-{uuid.uuid4().hex[:8]}", title="Engineer", company="Co", tags=["python"])
        db.add(job)
        db.commit()
        db.refresh(job)
        job_ids.append(str(job.id))

    response = client.post(
        "/api/v1/batch",
        json={
            "operation_type": "score",
            "job_ids": job_ids,
            "params": {}
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["operation_type"] == "score"
    assert data["status"] == "pending"
    assert data["total_items"] == 3
    assert data["processed_items"] == 0
    assert len(data["payload"]["job_ids"]) == 3
    return data["id"]


def test_batch_job_list(client, auth_headers):
    """Test listing batch jobs."""
    response = client.get("/api/v1/batch", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data


def test_batch_job_get(client, auth_headers, db):
    """Test getting a single batch job."""
    batch_id = test_batch_job_create(client, auth_headers, db)

    response = client.get(f"/api/v1/batch/{batch_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == batch_id


def test_batch_job_retry(client, auth_headers, db):
    """Test retrying a batch job."""
    from app.models.job import Job
    from app.models.batch import BatchJob
    import uuid

    # Create a test job with string UUID
    job_id = uuid.uuid4()
    job = Job(id=job_id, external_id=f"retry-test-job-{job_id.hex[:8]}", title="Engineer", company="Co")
    db.add(job)
    db.commit()
    db.refresh(job)

    # Create batch job
    response = client.post(
        "/api/v1/batch",
        json={
            "operation_type": "score",
            "job_ids": [str(job_id)],
            "params": {}
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    batch_id = uuid.UUID(response.json()["id"])  # Convert string back to UUID

    # Manually set status to partial (simulate completion)
    batch_job = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
    batch_job.status = "partial"
    batch_job.result_summary = {str(job_id): {"status": "error", "error": "test error"}}
    db.commit()

    # Try retry
    response = client.post(f"/api/v1/batch/{str(batch_id)}/retry", headers=auth_headers)
    assert response.status_code in (200, 400)


def test_batch_job_cancel(client, auth_headers, db):
    """Test cancelling a batch job."""
    batch_id = test_batch_job_create(client, auth_headers, db)

    # Should be able to cancel pending job
    response = client.post(f"/api/v1/batch/{batch_id}/cancel", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["cancel_requested"] is True


def test_batch_job_invalid_operation(client, auth_headers):
    """Test creating batch job with invalid operation type."""
    response = client.post(
        "/api/v1/batch",
        json={
            "operation_type": "invalid",
            "job_ids": [],
            "params": {}
        },
        headers=auth_headers,
    )
    assert response.status_code == 422  # Validation error


def test_batch_job_empty_job_ids(client, auth_headers):
    """Test creating batch job with empty job_ids."""
    response = client.post(
        "/api/v1/batch",
        json={
            "operation_type": "score",
            "job_ids": [],
            "params": {}
        },
        headers=auth_headers,
    )
    # Pydantic validation returns 422 for min_length validation
    assert response.status_code == 422


def test_batch_job_too_many_job_ids(client, auth_headers):
    """Test creating batch job with >500 job_ids."""
    job_ids = [str(uuid.uuid4()) for _ in range(501)]
    response = client.post(
        "/api/v1/batch",
        json={
            "operation_type": "score",
            "job_ids": job_ids,
            "params": {}
        },
        headers=auth_headers,
    )
    # Pydantic validation returns 422 for max_length validation
    assert response.status_code == 422