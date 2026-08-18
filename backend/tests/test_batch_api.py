"""
Tests for batch API endpoints.
"""
import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.api.users import get_current_user
from app.models.batch import BatchJob
from app.models.job import Job
from app.models.user import User

client = TestClient(app)

TEST_USER_ID = uuid.uuid4()

@pytest.fixture(autouse=True)
def override_dependencies(db):
    app.dependency_overrides[get_db] = lambda: db
    mock_user = User(
        id=TEST_USER_ID,
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_job(db) -> Job:
    job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Test Company",
        source="linkedin",
        external_id="123",
    )
    db.add(job)
    db.commit()
    return job


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test_token"}


def test_create_batch_job_success(db, mock_job, auth_headers):
    with patch("app.api.batch.enqueue_batch_job") as mock_enqueue:
        response = client.post(
            "/api/v1/batch",
            json={
                "operation_type": "analyze",
                "job_ids": [str(mock_job.id)],
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["operation_type"] == "analyze"
        assert data["status"] == "pending"
        assert data["total_items"] == 1
        
        # Verify the batch job was created
        batch_job = db.query(BatchJob).filter(BatchJob.id == uuid.UUID(data["id"])).first()
        assert batch_job is not None
        
        mock_enqueue.assert_called_once_with(batch_job.id)


def test_create_batch_job_invalid_job_id(db, auth_headers):
    response = client.post(
        "/api/v1/batch",
        json={
            "operation_type": "analyze",
            "job_ids": [str(uuid.uuid4())],  # Invalid job ID
        },
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "Jobs not found" in response.json()["detail"]


def test_list_batch_jobs(db, auth_headers):
    # Create a batch job for TEST_USER_ID
    batch_job = BatchJob(
        id=uuid.uuid4(),
        user_id=TEST_USER_ID,
        operation_type="analyze",
        status="completed",
        total_items=1,
        processed_items=1,
        succeeded_items=1,
        failed_items=0,
        payload={"job_ids": [str(uuid.uuid4())], "params": {}},
        result_summary={"test": {"status": "success"}},
    )
    db.add(batch_job)
    db.commit()
    
    response = client.get("/api/v1/batch", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["jobs"]) >= 1
    assert data["jobs"][0]["operation_type"] == "analyze"


def test_get_batch_job(db, auth_headers):
    # Create a batch job for TEST_USER_ID
    batch_job = BatchJob(
        id=uuid.uuid4(),
        user_id=TEST_USER_ID,
        operation_type="analyze",
        status="completed",
        total_items=1,
        processed_items=1,
        succeeded_items=1,
        failed_items=0,
        payload={"job_ids": [str(uuid.uuid4())], "params": {}},
        result_summary={"test": {"status": "success"}},
    )
    db.add(batch_job)
    db.commit()
    
    response = client.get(f"/api/v1/batch/{batch_job.id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(batch_job.id)
    assert data["operation_type"] == "analyze"
    assert data["status"] == "completed"


def test_retry_batch_job(db, auth_headers):
    # Create a batch job with failed items for TEST_USER_ID
    batch_job = BatchJob(
        id=uuid.uuid4(),
        user_id=TEST_USER_ID,
        operation_type="analyze",
        status="partial",
        total_items=2,
        processed_items=2,
        succeeded_items=1,
        failed_items=1,
        payload={"job_ids": [str(uuid.uuid4()), str(uuid.uuid4())], "params": {}},
        result_summary={
            str(uuid.uuid4()): {"status": "success"},
            str(uuid.uuid4()): {"status": "error", "error": "Failed"},
        },
    )
    db.add(batch_job)
    db.commit()
    
    with patch("app.api.batch.enqueue_batch_job") as mock_enqueue:
        response = client.post(f"/api/v1/batch/{batch_job.id}/retry", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["operation_type"] == "analyze"
        assert data["status"] == "pending"
        assert data["total_items"] == 1  # Only the failed item
        
        mock_enqueue.assert_called_once()


def test_cancel_batch_job(db, auth_headers):
    # Create a batch job for TEST_USER_ID
    batch_job = BatchJob(
        id=uuid.uuid4(),
        user_id=TEST_USER_ID,
        operation_type="analyze",
        status="running",
        total_items=1,
        processed_items=0,
        succeeded_items=0,
        failed_items=0,
        payload={"job_ids": [str(uuid.uuid4())], "params": {}},
        result_summary={},
    )
    db.add(batch_job)
    db.commit()
    
    response = client.post(f"/api/v1/batch/{batch_job.id}/cancel", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(batch_job.id)
    assert data["cancel_requested"] is True
    
    # Verify the batch job was updated
    db.refresh(batch_job)
    assert batch_job.cancel_requested is True