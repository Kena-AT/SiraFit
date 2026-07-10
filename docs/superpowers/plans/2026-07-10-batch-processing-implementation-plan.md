
# Sprint 10: Batch Processing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable large-scale job operations via a Batch Processing Center that supports analyze, score, tag, and archive operations with progress tracking and per-item error visibility.

**Architecture:** Hybrid batch model (single `BatchJob` table + operation-specific tasks) reusing existing analysis, scoring, and model update logic via Celery background processing.

**Tech Stack:** Python 3.12, SQLAlchemy, Pydantic, FastAPI, Celery, Redis (existing queues), JSON APIs, React/TanStack, TypeScript, Tailwind (existing UI)

---

## Global Constraints

- Use existing Celery + Redis infrastructure (extend batch_processing queue)
- Log all batch actions to AuditLog
- All operations must be idempotent and resumable
- Tests must cover unit, integration, and load scenarios
- Frontend must show real-time progress via polling while pending
- No breaking changes to existing public APIs
- Maintain existing type safety and validation rules

---

## Task 1: Database Migration + BatchJob Model

**Files:**

- Create: `backend/migrations/versions/add_batch_jobs_table.py`
- Create: `backend/app/models/batch.py` (or add to `backend/app/models/job.py`)

**Interfaces:**

- Produces: `BatchJob` SQLAlchemy model with all columns from spec

- [ ] **Step 1.1: Write migration**

```python
# backend/migrations/versions/add_batch_jobs_table.py
"""add batch jobs table

Revision ID: add_batch_jobs_table
Revises: add_application_tracking
Create Date: 2026-07-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_batch_jobs_table"
down_revision = "add_application_tracking"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "batch_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_batch_jobs_user_status", "batch_jobs", ["user_id", "status"])
    op.create_index("ix_batch_jobs_user_type", "batch_jobs", ["user_id", "operation_type"])
    op.create_index("ix_batch_jobs_created", "batch_jobs", ["created_at"])

def downgrade():
    op.drop_index("ix_batch_jobs_created", table_name="batch_jobs")
    op.drop_index("ix_batch_jobs_user_type", table_name="batch_jobs")
    op.drop_index("ix_batch_jobs_user_status", table_name="batch_jobs")
    op.drop_table("batch_jobs")
```

- [ ] **Step 1.2: Run migration to verify**

```bash
cd backend && python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"
```

Expected: Migration completes, tables created.

- [ ] **Step 1.3: Write BatchJob model**

```python
# backend/app/models/batch.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    operation_type = Column(String(30), nullable=False)  # analyze, score, tag, archive
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed, partial, cancelled
    total_items = Column(Integer, nullable=False, default=0)
    processed_items = Column(Integer, nullable=False, default=0)
    succeeded_items = Column(Integer, nullable=False, default=0)
    failed_items = Column(Integer, nullable=False, default=0)
    payload = Column("payload", JSON, nullable=False)  # operation-specific params
    result_summary = Column("result_summary", JSON, nullable=False, default={})  # per-item results/errors
    cancel_requested = Column(Boolean(), nullable=False, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user = relationship("User")
```

- [ ] **Step 1.4: Add import to models __init__**

```python
# backend/app/models/__init__.py
# Add at end:
from app.models.batch import BatchJob
__all__ = [..., "BatchJob"]
```

- [ ] **Step 1.5: Register in conftest.py for tests**

```python
# backend/tests/conftest.py
import app.models.batch  # noqa: F401
```

- [ ] **Step 1.6: Commit**

```bash
git add backend/migrations/versions/add_batch_jobs_table.py backend/app/models/batch.py backend/app/models/__init__.py backend/tests/conftest.py
git commit -m "feat(batch): add BatchJob model and migration"
```

---

## Task 2: Pydantic Schemas for Batch API

**Files:**

- Create: `backend/app/schemas/batch.py`

**Interfaces:**

- Consumes: —
- Produces: `BatchJobCreate`, `BatchJobUpdate`, `BatchJobResponse`, `BatchJobListResponse`

- [ ] **Step 2.1: Write schemas**

```python
# backend/app/schemas/batch.py
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
import uuid
from typing import Literal

class BatchJobCreate(BaseModel):
    operation_type: Literal["analyze", "score", "tag", "archive"]
    job_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=500)
    params: Dict[str, Any] = Field(default_factory=dict)

class BatchJobUpdate(BaseModel):
    cancel_requested: Optional[bool] = None

class BatchJobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    operation_type: str
    status: str
    total_items: int
    processed_items: int
    succeeded_items: int
    failed_items: int
    payload: Dict[str, Any]
    result_summary: Dict[str, Any]
    cancel_requested: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BatchJobListResponse(BaseModel):
    jobs: List[BatchJobResponse]
    total: int
    skip: int
    limit: int
```

- [ ] **Step 2.2: Run quick validation**

```bash
cd backend && python -c "from app.schemas.batch import BatchJobCreate; print(BatchJobCreate(operation_type='analyze', job_ids=['123e4567-e89b-12d3-a456-426614174000']))"
```

Expected: No errors.

- [ ] **Step 2.3: Commit**

```bash
git add backend/app/schemas/batch.py
git commit -m "feat(batch): add Pydantic schemas for batch API"
```

---

## Task 3: Batch Operations Services (Type-Specific Item Handlers)

**Files:**

- Create: `backend/app/services/batch_operations.py`

**Interfaces:**

- Consumes: Existing services (`run_job_analysis`, `calculate_match_score`, Job/Profile/Application models)
- Produces: Four functions with signatures:
  ```python
  async def batch_analyze_item(job_id: uuid.UUID, user_id: uuid.UUID, params: dict, db: Session) -> dict
  def batch_score_item(job_id: uuid.UUID, user_id: uuid.UUID, params: dict, db: Session) -> dict
  def batch_tag_item(job_id: uuid.UUID, user_id: uuid.UUID, params: dict, db: Session) -> dict
  def batch_archive_item(job_id: uuid.UUID, user_id: uuid.UUID, params: dict, db: Session) -> dict
  ```

- [ ] **Step 3.1: Write batch_operations.py**

```python
# backend/app/services/batch_operations.py
"""
Item-level handlers for batch operations.
Each processes a single job_id and returns a result dict.
Reuses existing services where possible.
"""
import uuid
import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.job import Job, JobAnalysis
from app.models.profile import Profile
from app.models.score import JobMatchScore
from app.services.job_analysis import run_job_analysis
from app.services.matching_engine import calculate_match_score

logger = logging.getLogger(__name__)

VALID_OPERATION_TYPES = {"analyze", "score", "tag", "archive"}

async def batch_analyze_item(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    params: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Trigger AI analysis for a single job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    analysis = await run_job_analysis(
        job=job,
        db=db,
        api_key=params.get("api_key"),
        provider=params.get("provider"),
        model=params.get("model"),
        user_id=str(user_id),
    )
    return {"score": analysis.score, "status": analysis.status, "summary": analysis.summary[:200] if analysis.summary else ""}

def batch_score_item(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    params: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Calculate match score for a single job against user profile."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise ValueError(f"Profile for user {user_id} not found")

    score_data = calculate_match_score(profile, job)

    # Upsert JobMatchScore
    existing = db.query(JobMatchScore).filter(
        JobMatchScore.user_id == user_id,
        JobMatchScore.job_id == job_id,
    ).first()

    if existing:
        existing.score = score_data["score"]
        existing.breakdown = score_data["breakdown"]
        existing.explanation = score_data["explanation"]
    else:
        new_score = JobMatchScore(
            user_id=user_id,
            job_id=job_id,
            score=score_data["score"],
            breakdown=score_data["breakdown"],
            explanation=score_data["explanation"],
        )
        db.add(new_score)

    db.commit()
    return {"score": score_data["score"], "breakdown": score_data["breakdown"]}

def batch_tag_item(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    params: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Add or remove tags on a single job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    tags_to_modify = set(params.get("tags", []))
    action = params.get("action", "add")
    current_tags = set(job.tags or [])

    if action == "add":
        current_tags.update(tags_to_modify)
    elif action == "remove":
        current_tags.difference_update(tags_to_modify)
    else:
        raise ValueError(f"Invalid action: {action}")

    job.tags = list(current_tags)
    db.commit()
    return {"tags": job.tags, "action": action}

def batch_archive_item(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    params: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Archive a job or application."""
    target = params.get("target", "jobs")

    if target == "jobs":
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        job.source = "archived"
        db.commit()
        return {"archived": True, "target": "jobs"}
    elif target == "applications":
        from app.models.job import JobApplication
        app = db.query(JobApplication).filter(
            JobApplication.id == job_id,
            JobApplication.user_id == user_id
        ).first()
        if not app:
            raise ValueError(f"Application {job_id} not found")
        app.status = "archived"
        db.commit()
        return {"archived": True, "target": "applications"}
    else:
        raise ValueError(f"Invalid target: {target}")
```

- [ ] **Step 3.2: Add import to services __init__**

```python
# backend/app/services/__init__.py
from app.services.batch_operations import (
    batch_analyze_item,
    batch_score_item,
    batch_tag_item,
    batch_archive_item,
)
__all__ = [..., "batch_analyze_item", "batch_score_item", "batch_tag_item", "batch_archive_item"]
```

- [ ] **Step 3.3: Write unit tests**

```python
# backend/tests/test_batch_operations.py
import uuid
import pytest
from app.services.batch_operations import (
    batch_score_item, batch_tag_item, batch_archive_item
)
from app.models.job import Job
from app.models.profile import Profile

def test_batch_score_item(test_user, db):
    job = Job(external_id="score-job", title="Engineer", company="Co", tags=["python", "react"])
    db.add(job); db.commit()
    profile = Profile(user_id=test_user.id, skills=[...])  # minimal profile
    db.add(profile); db.commit()
    result = batch_score_item(job.id, test_user.id, {}, db)
    assert "score" in result
    assert 0 <= result["score"] <= 100

def test_batch_tag_item_add(test_user, db):
    job = Job(external_id="tag-job", title="Engineer", company="Co", tags=["python"])
    db.add(job); db.commit()
    result = batch_tag_item(job.id, test_user.id, {"tags": ["remote", "senior"], "action": "add"}, db)
    assert "remote" in result["tags"]
    assert "senior" in result["tags"]

def test_batch_tag_item_remove(test_user, db):
    job = Job(external_id="tag-job2", title="Engineer", company="Co", tags=["python", "remote", "senior"])
    db.add(job); db.commit()
    result = batch_tag_item(job.id, test_user.id, {"tags": ["remote"], "action": "remove"}, db)
    assert "remote" not in result["tags"]
    assert "senior" in result["tags"]

def test_batch_archive_job(test_user, db):
    job = Job(external_id="arch-job", title="Engineer", company="Co")
    db.add(job); db.commit()
    result = batch_archive_item(job.id, test_user.id, {"target": "jobs"}, db)
    assert result["archived"] is True
    db.refresh(job)
    assert job.source == "archived"
```

- [ ] **Step 3.4: Run tests**

```bash
cd backend && python -m pytest tests/test_batch_operations.py -v
```

Expected: All tests pass.

- [ ] **Step 3.5: Commit**

```bash
git add backend/app/services/batch_operations.py backend/app/services/__init__.py backend/tests/test_batch_operations.py
git commit -m "feat(batch): add batch operation item handlers"
```

---

## Task 4: Batch API Endpoints

**Files:**

- Create: `backend/app/api/batch.py`
- Modify: `backend/app/api/router.py` (add batch router)

**Interfaces:**

- Consumes: `BatchJob` model, `BatchJobCreate` schema, `enqueue_batch_job` (from Task 5), `get_current_user`
- Produces: REST endpoints per spec

- [ ] **Step 4.1: Write batch API**

```python
# backend/app/api/batch.py
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.batch import BatchJob
from app.schemas.batch import BatchJobCreate, BatchJobUpdate, BatchJobResponse, BatchJobListResponse
from app.services.batch import enqueue_batch_job

router = APIRouter()

@router.post("", response_model=BatchJobResponse, status_code=201)
async def create_batch_job(
    batch_in: BatchJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new batch job and enqueue for processing."""
    # Validate all job_ids exist and user has access
    jobs = db.query(Job).filter(Job.id.in_(batch_in.job_ids)).all()
    if len(jobs) != len(batch_in.job_ids):
        found_ids = {str(j.id) for j in jobs}
        missing = [jid for jid in batch_in.job_ids if str(jid) not in found_ids]
        raise HTTPException(status_code=404, detail=f"Jobs not found: {missing}")

    batch_job = BatchJob(
        user_id=current_user.id,
        operation_type=batch_in.operation_type,
        status="pending",
        total_items=len(batch_in.job_ids),
        payload={"job_ids": [str(jid) for jid in batch_in.job_ids], "params": batch_in.params},
        result_summary={},
    )
    db.add(batch_job)
    db.commit()
    db.refresh(batch_job)

    # Enqueue background task
    background_tasks.add_task(enqueue_batch_job, batch_job.id)

    return batch_job

@router.get("", response_model=BatchJobListResponse)
def list_batch_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    operation_type: Optional[str] = Query(None),
) -> Any:
    """List user's batch jobs with optional filters."""
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
    batch_job = db.query(BatchJob).filter(
        BatchJob.id == batch_id,
        BatchJob.user_id == current_user.id
    ).first()
    if not batch_job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return batch_job

@router.post("/{batch_id}/retry", response_model=BatchJobResponse)
def retry_batch_job(
    batch_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retry only the failed items in a batch job."""
    batch_job = db.query(BatchJob).filter(
        BatchJob.id == batch_id,
        BatchJob.user_id == current_user.id
    ).first()
    if not batch_job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if batch_job.status not in ("completed", "failed", "partial", "cancelled"):
        raise HTTPException(status_code=400, detail="Can only retry completed/failed batches")

    # Extract failed item IDs
    failed_ids = [
        uuid.UUID(item_id) for item_id, result in batch_job.result_summary.items()
        if result.get("status") == "error"
    ]
    if not failed_ids:
        raise HTTPException(status_code=400, detail="No failed items to retry")

    # Create new batch job for retry
    retry_job = BatchJob(
        user_id=current_user.id,
        operation_type=batch_job.operation_type,
        status="pending",
        total_items=len(failed_ids),
        payload={"job_ids": [str(jid) for jid in failed_ids], "params": batch_job.payload.get("params", {})},
        result_summary={},
    )
    db.add(retry_job)
    db.commit()
    db.refresh(retry_job)

    background_tasks.add_task(enqueue_batch_job, retry_job.id)
    return retry_job

@router.post("/{batch_id}/cancel", response_model=BatchJobResponse)
def cancel_batch_job(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Request cancellation of a running/pending batch job."""
    batch_job = db.query(BatchJob).filter(
        BatchJob.id == batch_id,
        BatchJob.user_id == current_user.id
    ).first()
    if not batch_job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if batch_job.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail="Can only cancel pending/running batches")

    batch_job.cancel_requested = True
    db.commit()
    db.refresh(batch_job)
    return batch_job
```

- [ ] **Step 4.2: Register router in api/router.py**

```python
# backend/app/api/router.py
# Add import:
from app.api import batch

# Add line:
api_router.include_router(batch.router, prefix="/batch", tags=["batch"])
```

- [ ] **Step 4.3: Write integration tests**

```python
# backend/tests/test_batch_api.py
import uuid
import pytest

def test_create_batch_analyze(client, auth_headers, test_user, db):
    # Create jobs
    jobs = [Job(external_id=f"batch-job-{i}", title=f"Job {i}", company="Co") for i in range(3)]
    db.add_all(jobs); db.commit()
    job_ids = [str(j.id) for j in jobs]

    response = client.post("/api/v1/batch", json={
        "operation_type": "analyze",
        "job_ids": job_ids,
        "params": {}
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["total_items"] == 3

def test_create_batch_invalid_job_ids(client, auth_headers):
    fake_id = str(uuid.uuid4())
    response = client.post("/api/v1/batch", json={
        "operation_type": "analyze",
        "job_ids": [fake_id],
        "params": {}
    }, headers=auth_headers)
    assert response.status_code == 404

def test_list_batch_jobs(client, auth_headers, test_user, db):
    from app.models.batch import BatchJob
    bj = BatchJob(user_id=test_user.id, operation_type="analyze", status="completed", total_items=1, payload={"job_ids": [], "params": {}})
    db.add(bj); db.commit()

    response = client.get("/api/v1/batch", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

def test_get_batch_job(client, auth_headers, test_user, db):
    from app.models.batch import BatchJob
    bj = BatchJob(user_id=test_user.id, operation_type="analyze", status="completed", total_items=1, payload={"job_ids": [], "params": {}})
    db.add(bj); db.commit(); db.refresh(bj)

    response = client.get(f"/api/v1/batch/{bj.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(bj.id)

def test_cancel_batch_job(client, auth_headers, test_user, db):
    from app.models.batch import BatchJob
    bj = BatchJob(user_id=test_user.id, operation_type="analyze", status="pending", total_items=1, payload={"job_ids": [], "params": {}})
    db.add(bj); db.commit(); db.refresh(bj)

    response = client.post(f"/api/v1/batch/{bj.id}/cancel", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["cancel_requested"] is True
```

- [ ] **Step 4.4: Run tests** (will fail until Task 5 provides enqueue_batch_job)

```bash
cd backend && python -m pytest tests/test_batch_api.py -v
```

Expected: Some pass, some fail (import error for enqueue_batch_job).

- [ ] **Step 4.5: Commit**

```bash
git add backend/app/api/batch.py backend/app/api/router.py backend/tests/test_batch_api.py
git commit -m "feat(batch): add batch API endpoints"
```

---

## Task 5: Celery Worker Task + Enqueue Helper

**Files:**

- Create: `backend/app/worker/tasks/batch.py`
- Modify: `backend/app/worker/celery_app.py` (add batch_processing queue route)
- Create: `backend/app/services/batch.py` (enqueue helper)

**Interfaces:**

- Consumes: `batch_analyze_item`, `batch_score_item`, `batch_tag_item`, `batch_archive_item`
- Produces: `process_batch_job` Celery task, `enqueue_batch_job` function

- [ ] **Step 5.1: Write batch.py task**

```python
# backend/app/worker/tasks/batch.py
"""
Celery task for processing batch jobs.
"""
import logging
import uuid
from typing import Any, Dict
from celery import shared_task

from app.core.database import SessionLocal
from app.models.batch import BatchJob
from app.models.audit import AuditLog  # or AuditLog from models.job

logger = logging.getLogger(__name__)

# Import item handlers
from app.services.batch_operations import (
    batch_analyze_item,
    batch_score_item,
    batch_tag_item,
    batch_archive_item,
)

TASK_MAP = {
    "analyze": batch_analyze_item,
    "score": batch_score_item,
    "tag": batch_tag_item,
    "archive": batch_archive_item,
}

@shared_task(
    name="app.worker.tasks.process_batch_job",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
    time_limit=1800,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_batch_job(self, batch_job_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        batch_job = db.query(BatchJob).filter(BatchJob.id == uuid.UUID(batch_job_id)).first()
        if not batch_job:
            logger.error("batch_job_not_found", extra={"batch_job_id": batch_job_id})
            return {"error": "BatchJob not found"}

        batch_job.status = "running"
        batch_job.started_at = datetime.utcnow()
        batch_job.processed_items = 0
        batch_job.succeeded_items = 0
        batch_job.failed_items = 0
        db.commit()

        task_fn = TASK_MAP.get(batch_job.operation_type)
        if not task_fn:
            raise ValueError(f"Unknown operation_type: {batch_job.operation_type}")

        job_ids = batch_job.payload.get("job_ids", [])
        params = batch_job.payload.get("params", {})
        batch_job.total_items = len(job_ids)

        for item_id_str in job_ids:
            # Check cancel flag
            db.refresh(batch_job)
            if batch_job.cancel_requested:
                batch_job.status = "cancelled"
                batch_job.completed_at = datetime.utcnow()
                db.commit()
                return {"status": "cancelled", "processed": batch_job.processed_items}

            item_id = uuid.UUID(item_id_str)
            try:
                # Pass db session to handlers
                result = task_fn(item_id, batch_job.user_id, params, db)
                batch_job.succeeded_items += 1
                batch_job.result_summary[item_id_str] = {"status": "success", "result": result}
            except Exception as e:
                logger.exception("batch_item_failed", extra={"item_id": item_id_str, "batch_job_id": batch_job_id})
                batch_job.failed_items += 1
                batch_job.result_summary[item_id_str] = {"status": "error", "error": str(e)}

            batch_job.processed_items += 1

            # Commit progress every 10 items
            if batch_job.processed_items % 10 == 0:
                db.commit()

        # Final status
        if batch_job.failed_items == 0:
            batch_job.status = "completed"
        else:
            batch_job.status = "partial"
        batch_job.completed_at = datetime.utcnow()
        db.commit()

        # Audit log
        audit = AuditLog(
            user_id=batch_job.user_id,
            action="batch_job_completed",
            entity_type="batch_job",
            entity_id=batch_job.id,
            details={
                "operation": batch_job.operation_type,
                "total": batch_job.total_items,
                "succeeded": batch_job.succeeded_items,
                "failed": batch_job.failed_items,
            },
        )
        db.add(audit)
        db.commit()

        return {"status": batch_job.status, "processed": batch_job.processed_items}

    except Exception as exc:
        logger.exception("batch_job_failed", extra={"batch_job_id": batch_job_id})
        batch_job = db.query(BatchJob).filter(BatchJob.id == uuid.UUID(batch_job_id)).first()
        if batch_job:
            batch_job.status = "failed"
            batch_job.completed_at = datetime.utcnow()
            db.commit()
        raise
    finally:
        db.close()
```

- [ ] **Step 5.2: Add import to worker tasks __init__**

```python
# backend/app/worker/tasks/__init__.py
from app.worker.tasks.batch import process_batch_job
__all__ = [..., "process_batch_job"]
```

- [ ] **Step 5.3: Update celery_app.py to include batch queue**

```python
# backend/app/worker/celery_app.py
# In task_routes dict, add:
task_routes={
    ...
    "app.worker.tasks.process_batch_job": {"queue": "batch_processing"},
},
```

- [ ] **Step 5.4: Write enqueue helper**

```python
# backend/app/services/batch.py
"""
Enqueue helpers for batch jobs.
"""
import logging
import uuid
from app.core.database import SessionLocal
from app.models.batch import BatchJob

logger = logging.getLogger(__name__)

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
            extra={"batch_job_id": str(batch_job_id), "error": str(exc)},
        )
        # Sync fallback - run directly
        from app.worker.tasks.batch import process_batch_job
        process_batch_job(str(batch_job_id))
```

- [ ] **Step 5.5: Add imports to services __init__**

```python
# backend/app/services/__init__.py
from app.services.batch import enqueue_batch_job
__all__ = [..., "enqueue_batch_job"]
```

- [ ] **Step 5.6: Write tests**

```python
# backend/tests/test_batch_worker.py
import uuid
from unittest.mock import patch, MagicMock
from app.services.batch import enqueue_batch_job

def test_enqueue_batch_job_sync_fallback(db, test_user):
    """When Celery unavailable, falls back to sync execution."""
    from app.models.batch import BatchJob
  
    bj = BatchJob(user_id=test_user.id, operation_type="tag", status="pending", total_items=1, 
                  payload={"job_ids": [], "params": {"tags": ["test"], "action": "add"}})
    db.add(bj); db.commit(); db.refresh(bj)

    with patch('app.worker.celery_app.celery_app.send_task', side_effect=Exception("No Redis")):
        # Should not raise, should run sync
        enqueue_batch_job(bj.id)
  
    # Verify sync execution happened
    db.refresh(bj)
    assert bj.status in ("completed", "partial", "failed")
```

- [ ] **Step 5.7: Run tests**

```bash
cd backend && python -m pytest tests/test_batch_worker.py -v
```

Expected: Tests pass.

- [ ] **Step 5.8: Re-run API tests from Task 4**

```bash
cd backend && python -m pytest tests/test_batch_api.py -v
```

Expected: All pass now.

- [ ] **Step 5.9: Commit**

```bash
git add backend/app/worker/tasks/batch.py backend/app/worker/tasks/__init__.py backend/app/worker/celery_app.py backend/app/services/batch.py backend/app/services/__init__.py backend/tests/test_batch_worker.py
git commit -m "feat(batch): add Celery task and enqueue helper"
```

---

## Task 6: Frontend - Batch List Page ( /batch )

**Files:**

- Create: `frontend/src/routes/_app.batch.tsx` (replace mock with real)
- Create: `frontend/src/lib/api/batch.ts`
- Create: `frontend/src/components/sirafit/batch/BatchJobCard.tsx`
- Create: `frontend/src/components/sirafit/batch/BatchCreateModal.tsx`

**Interfaces:**

- Consumes: Batch API endpoints, TanStack Query
- Produces: Working list page with create modal

- [ ] **Step 6.1: Write API client**

```typescript
// frontend/src/lib/api/batch.ts
import { apiFetch } from "./client";

export interface BatchJob {
  id: string;
  user_id: string;
  operation_type: "analyze" | "score" | "tag" | "archive";
  status: "pending" | "running" | "completed" | "failed" | "partial" | "cancelled";
  total_items: number;
  processed_items: number;
  succeeded_items: number;
  failed_items: number;
  payload: Record<string, any>;
  result_summary: Record<string, { status: "success" | "error"; result?: any; error?: string }>;
  cancel_requested: boolean;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BatchJobCreateInput {
  operation_type: "analyze" | "score" | "tag" | "archive";
  job_ids: string[];
  params?: Record<string, any>;
}

export const getBatchJobs = async (params?: { status?: string; operation_type?: string }): Promise<BatchJob[]> => {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.operation_type) search.set("operation_type", params.operation_type);
  const response = await apiFetch(`/api/v1/batch?${search}`);
  if (!response.ok) throw new Error("Failed to fetch batch jobs");
  return response.json();
};

export const getBatchJob = async (id: string): Promise<BatchJob> => {
  const response = await apiFetch(`/api/v1/batch/${id}`);
  if (!response.ok) throw new Error("Failed to fetch batch job");
  return response.json();
};

export const createBatchJob = async (input: BatchJobCreateInput): Promise<BatchJob> => {
  const response = await apiFetch("/api/v1/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to create batch job" }));
    throw new Error(err.detail || "Failed to create batch job");
  }
  return response.json();
};

export const retryBatchJob = async (id: string): Promise<BatchJob> => {
  const response = await apiFetch(`/api/v1/batch/${id}/retry`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to retry batch job");
  return response.json();
};

export const cancelBatchJob = async (id: string): Promise<BatchJob> => {
  const response = await apiFetch(`/api/v1/batch/${id}/cancel`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to cancel batch job");
  return response.json();
};
```

- [ ] **Step 6.2: Write BatchJobCard component**

```tsx
// frontend/src/components/sirafit/batch/BatchJobCard.tsx
import { StatusPill } from "../bits";
import type { BatchJob } from "@/lib/api/batch";

export function BatchJobCard({ job, onClick }: { job: BatchJob; onClick: () => void }) {
  const progressPct = job.total_items > 0 ? Math.round((job.processed_items / job.total_items) * 100) : 0;
  const getStatus = () => {
    if (job.status === "running") return "info";
    if (job.status === "completed") return "success";
    if (job.status === "failed") return "failed";
    if (job.status === "partial") return "warning";
    if (job.status === "cancelled") return "muted";
    return "muted";
  };

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-4 p-4 text-left rounded-lg bg-card ring-1 ring-border hover:ring-[color:var(--brand)]/40 transition-colors"
    >
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <StatusPill status={job.operation_type} className="shrink-0" />
        <div className="min-w-0">
          <div className="text-sm font-semibold truncate">
            {job.operation_type.charAt(0).toUpperCase() + job.operation_type.slice(1)}
          </div>
          <div className="text-[11px] text-muted-foreground">
            {job.processed_items} / {job.total_items} items
          </div>
        </div>
      </div>
      <div className="w-32 shrink-0">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full bg-[color:var(--brand)]" style={{ width: `${progressPct}%` }} />
        </div>
      </div>
      <StatusPill status={job.status} className="shrink-0" />
    </button>
  );
}
```

- [ ] **Step 6.3: Write BatchCreateModal component**

```tsx
// frontend/src/components/sirafit/batch/BatchCreateModal.tsx
import { useState, type ChangeEvent } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import type { Job } from "@/lib/api/jobs";

interface BatchCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (input: {
    operation_type: "analyze" | "score" | "tag" | "archive";
    job_ids: string[];
    params?: Record<string, any>;
  }) => void;
  availableJobs: Job[];
}

export function BatchCreateModal({ isOpen, onClose, onSubmit, availableJobs }: BatchCreateModalProps) {
  if (!isOpen) return null;

  const [operation, setOperation] = useState<"analyze" | "score" | "tag" | "archive">("analyze");
  const [selectedJobIds, setSelectedJobIds] = useState<string[]>([]);
  const [selectAll, setSelectAll] = useState(false);
  const [tags, setTags] = useState("");
  const [tagAction, setTagAction] = useState<"add" | "remove">("add");
  const [archiveTarget, setArchiveTarget] = useState<"jobs" | "applications">("jobs");

  const handleJobToggle = (id: string) => {
    setSelectedJobIds(prev => prev.includes(id) ? prev.filter(j => j !== id) : [...prev, id]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, any> = {};
    if (operation === "tag") {
      params.tags = tags.split(",").map(t => t.trim()).filter(Boolean);
      params.action = tagAction;
    } else if (operation === "archive") {
      params.target = archiveTarget;
    }
    onSubmit({ operation_type: operation, job_ids: selectedJobIds, params });
    onClose();
  };

  const filteredJobs = availableJobs; // Could add search filter later

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md bg-card rounded-lg ring-1 ring-border p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">New Batch Job</h2>
          <button onClick={onClose} className="p-1 hover:bg-muted rounded"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="block mb-2">Operation</Label>
            <select
              value={operation}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setOperation(e.target.value as any)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="analyze">Batch AI Analysis</option>
              <option value="score">Batch Match Scoring</option>
              <option value="tag">Batch Tagging</option>
              <option value="archive">Batch Archive</option>
            </select>
          </div>

          <div>
            <Label className="block mb-2">Jobs ({selectedJobIds.length} selected)</Label>
            <div className="max-h-48 overflow-y-auto border border-input rounded-md p-2 space-y-1">
              {filteredJobs.map(job => (
                <label key={job.id} className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={selectAll || selectedJobIds.includes(job.id)}
                    onCheckedChange={checked => handleJobToggle(job.id)}
                  />
                  <span className="text-sm">{job.company} – {job.title}</span>
                </label>
              ))}
            </div>
          </div>

          {operation === "tag" && (
            <div className="space-y-2">
              <Label>Tags (comma-separated)</Label>
              <Input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="remote, senior, python"
              />
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input type="radio" value="add" checked={tagAction === "add"} onChange={() => setTagAction("add")} />
                  Add
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" value="remove" checked={tagAction === "remove"} onChange={() => setTagAction("remove")} />
                  Remove
                </label>
              </div>
            </div>
          )}

          {operation === "archive" && (
            <div>
              <Label>Target</Label>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input type="radio" value="jobs" checked={archiveTarget === "jobs"} onChange={() => setArchiveTarget("jobs")} />
                  Jobs
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" value="applications" checked={archiveTarget === "applications"} onChange={() => setArchiveTarget("applications")} />
                  Applications
                </label>
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={selectedJobIds.length === 0}>Create Batch Job</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 6.4: Update batch list page**

```tsx
// frontend/src/routes/_app.batch.tsx
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill, ScoreMeter } from "@/components/sirafit/bits";
import { Plus, RefreshCw, Search, Filter } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getBatchJobs, createBatchJob, cancelBatchJob } from "@/lib/api/batch";
import { getJobs } from "@/lib/api/jobs";
import { BatchJobCard } from "@/components/sirafit/batch/BatchJobCard";
import { BatchCreateModal } from "@/components/sirafit/batch/BatchCreateModal";
import { useState } from "react";

export const Route = createFileRoute("/_app/batch")({
  head: () => ({ meta: [{ title: "Batch processing · SiraFit" }] }),
  component: BatchCenter,
});

function BatchCenter() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);

  const { data: jobs = [] } = useQuery({ queryKey: ["jobs-for-batch"], queryFn: () => getJobs({ limit: 500 }) });
  const { data: batchJobs = [], isLoading } = useQuery({ queryKey: ["batch-jobs"], queryFn: getBatchJobs });

  const createMutation = useMutation({
    mutationFn: createBatchJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batch-jobs"] });
      setModalOpen(false);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: cancelBatchJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["batch-jobs"] }),
  });

  const handleCreate = (input: { operation_type: string; job_ids: string[]; params?: any }) => {
    createMutation.mutate(input);
  };

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Operations" title="Batch processing center" />
        <div className="grid place-items-center py-20">Loading...</div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Operations"
        title="Batch processing center"
        description="Run high-volume operations across your pipeline. Bounded retries, no infinite loops."
        actions={
          <Button onClick={() => setModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" /> New batch job
          </Button>
        }
      />

      <div className="space-y-4">
        <Panel title="Create batch job" className="border-border/50">
          <BatchCreateModal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            onSubmit={handleCreate}
            availableJobs={jobs}
          />
          <Button variant="outline" onClick={() => setModalOpen(true)} className="w-full">
            <Plus className="w-4 h-4 mr-2" /> Start new batch operation
          </Button>
        </Panel>

        <Panel title="Recent batches">
          <div className="mb-4 flex items-center gap-2">
            <Input placeholder="Filter batches..." className="w-64" />
            <Select defaultValue="all" className="w-40">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="partial">Partial</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-3">
            {batchJobs.length === 0 ? (
              <div className="grid h-32 place-items-center rounded-md border border-dashed border-border text-muted-foreground">
                No batch jobs yet. Create one to get started.
              </div>
            ) : (
              batchJobs.map((batchJob: any) => (
                <BatchJobCard
                  key={batchJob.id}
                  job={batchJob}
                  onClick={() => window.location.href = `/batch/${batchJob.id}`}
                />
              ))
            )}
          </div>
        </Panel>
      </div>
    </PageBody>
  );
}
```

- [ ] **Step 6.5: Run frontend build**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: Build succeeds.

- [ ] **Step 6.6: Commit**

```bash
git add frontend/src/lib/api/batch.ts frontend/src/components/sirafit/batch/BatchJobCard.tsx frontend/src/components/sirafit/batch/BatchCreateModal.tsx frontend/src/routes/_app.batch.tsx
git commit -m "feat(batch): add frontend batch list page and create modal"
```

---

## Task 7: Frontend - Batch Detail Page ( /batch/$id )

**Files:**

- Create: `frontend/src/routes/_app.batch.$id.tsx`
- Create: `frontend/src/components/sirafit/batch/BatchDetailView.tsx`
- Create: `frontend/src/components/sirafit/batch/BatchItemRow.tsx`

**Interfaces:**

- Consumes: `getBatchJob`, `retryBatchJob`, `cancelBatchJob` from batch.ts
- Produces: Detail view with polling, progress, per-item results table

- [ ] **Step 7.1: Write BatchItemRow component**

```tsx
// frontend/src/components/sirafit/batch/BatchItemRow.tsx
import { ChevronDown, ChevronUp, AlertCircle, CheckCircle } from "lucide-react";
import { useState } from "react";

interface BatchItemRowProps {
  itemId: string;
  result: { status: "success" | "error"; result?: any; error?: string };
}

export function BatchItemRow({ itemId, result }: BatchItemRowProps) {
  const [expanded, setExpanded] = useState(false);
  const isError = result.status === "error";

  return (
    <tr className={isError ? "bg-destructive/5" : ""}>
      <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground">{itemId.slice(0, 8)}…</td>
      <td className="px-4 py-3">
        {isError ? (
          <span className="inline-flex items-center gap-1.5 text-destructive text-sm">
            <AlertCircle className="w-3 h-3" /> Failed
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-[color:var(--success)] text-sm">
            <CheckCircle className="w-3 h-3" /> Success
          </span>
        )}
      </td>
      <td className="px-4 py-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-muted-foreground hover:text-foreground text-sm underline"
        >
          {expanded ? "Hide" : "Show"} details
        </button>
      </td>
      <td className="px-4 py-3 text-right">
        {isError && (
          <span className="text-xs text-destructive font-mono">{result.error?.slice(0, 80)}…</span>
        )}
      </td>
    </tr>
  );
}
```

- [ ] **Step 7.2: Write BatchDetailView component**

```tsx
// frontend/src/components/sirafit/batch/BatchDetailView.tsx
import { useEffect } from "react";
import { RefreshCw, RotateCcw, XCircle } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader, Panel, StatusPill, ScoreMeter } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getBatchJob, retryBatchJob, cancelBatchJob } from "@/lib/api/batch";
import type { BatchJob } from "@/lib/api/batch";
import { BatchItemRow } from "./BatchItemRow";

interface BatchDetailViewProps {
  batchJob: BatchJob;
  onRefetch: () => void;
}

export function BatchDetailView({ batchJob, onRefetch }: BatchDetailViewProps) {
  const queryClient = useQueryClient();
  const isRunning = ["pending", "running"].includes(batchJob.status);

  // Poll while running
  const { data: liveJob, refetch } = useQuery({
    queryKey: ["batch-job", batchJob.id],
    queryFn: () => getBatchJob(batchJob.id),
    enabled: isRunning,
    refetchInterval: isRunning ? 2000 : false,
  });

  // Update parent when done
  useEffect(() => {
    if (liveJob && !isRunning) {
      onRefetch();
    }
  }, [liveJob, isRunning, onRefetch]);

  const displayJob = liveJob || batchJob;
  const progressPct = displayJob.total_items > 0 ? Math.round((displayJob.processed_items / displayJob.total_items) * 100) : 0;

  const retryMutation = useMutation({
    mutationFn: retryBatchJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batch-job", batchJob.id] });
      queryClient.invalidateQueries({ queryKey: ["batch-jobs"] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: cancelBatchJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batch-job", batchJob.id] });
      queryClient.invalidateQueries({ queryKey: ["batch-jobs"] });
    },
  });

  return (
    <div>
      <PageHeader
        eyebrow="Operations"
        title={`${displayJob.operation_type.charAt(0).toUpperCase() + displayJob.operation_type.slice(1)} batch`}
        description={`${displayJob.processed_items} / ${displayJob.total_items} items processed`}
        actions={
          <div className="flex items-center gap-2">
            {isRunning && (
              <Button variant="ghost" size="sm" onClick={refetch} disabled={cancelMutation.isPending}>
                <RefreshCw className="w-4 h-4 mr-1 animate-spin" /> Refresh
              </Button>
            )}
            {["pending", "running"].includes(displayJob.status) && (
              <Button variant="ghost" size="sm" onClick={() => cancelMutation.mutate(displayJob.id)} disabled={cancelMutation.isPending}>
                <XCircle className="w-4 h-4 mr-1" /> Cancel
              </Button>
            )}
            {["completed", "failed", "partial", "cancelled"].includes(displayJob.status) && displayJob.failed_items > 0 && (
              <Button size="sm" onClick={() => retryMutation.mutate(displayJob.id)} disabled={retryMutation.isPending}>
                <RotateCcw className="w-4 h-4 mr-1" /> Retry failed ({displayJob.failed_items})
              </Button>
            )}
          </div>
        }
      />

      <Panel title="Progress">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full bg-[color:var(--brand)] transition-all duration-300" style={{ width: `${progressPct}%` }} />
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm font-mono tabular-nums">
              <span className="text-[color:var(--success)]">✓ {displayJob.succeeded_items}</span>
              <span className="text-destructive">✗ {displayJob.failed_items}</span>
              <span className="text-muted-foreground">⟳ {displayJob.total_items - displayJob.processed_items}</span>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div><span className="text-muted-foreground">Started:</span> {displayJob.started_at ? new Date(displayJob.started_at).toLocaleString() : "—"}</div>
            <div><span className="text-muted-foreground">Completed:</span> {displayJob.completed_at ? new Date(displayJob.completed_at).toLocaleString() : "—"}</div>
            <div><span className="text-muted-foreground">Status:</span> <StatusPill status={displayJob.status} /></div>
            <div><span className="text-muted-foreground">Cancel requested:</span> {String(displayJob.cancel_requested)}</div>
          </div>
        </div>
      </Panel>

      <Panel title="Items">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="px-4 py-2 font-mono text-[10px] uppercase">Job ID</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase">Status</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase">Details</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase text-right">Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {Object.entries(displayJob.result_summary).map(([itemId, result]) => (
                <BatchItemRow key={itemId} itemId={itemId} result={result} />
              ))}
            </tbody>
          </table>
          {Object.keys(displayJob.result_summary).length === 0 && (
            <div className="p-8 text-center text-muted-foreground">No items processed yet</div>
          )}
        </div>
      </Panel>

      <Panel title="Payload">
        <pre className="p-4 text-[11px] font-mono bg-muted/50 rounded overflow-auto max-h-64">
          {JSON.stringify(displayJob.payload, null, 2)}
        </pre>
      </Panel>
    </div>
  );
}
```

- [ ] **Step 7.3: Write detail page route**

```tsx
// frontend/src/routes/_app.batch.$id.tsx
import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";
import { ArrowLeft } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getBatchJob } from "@/lib/api/batch";
import { BatchDetailView } from "@/components/sirafit/batch/BatchDetailView";

export const Route = createFileRoute("/_app/batch/$id")({
  head: () => ({ meta: [{ title: "Batch job · SiraFit" }] }),
  component: BatchDetailPage,
});

function BatchDetailPage() {
  const { id } = Route.useParams();
  const queryClient = useQueryClient();

  const { data: batchJob, isLoading, refetch } = useQuery({
    queryKey: ["batch-job", id],
    queryFn: () => getBatchJob(id),
  });

  if (isLoading || !batchJob) {
    return (
      <PageBody>
        <PageHeader eyebrow="Operations" title="Loading batch job..." />
        <div className="grid place-items-center py-20">Loading...</div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Operations"
        title={`${batchJob.operation_type.charAt(0).toUpperCase() + batchJob.operation_type.slice(1)} batch`}
        actions={
          <Link to="/batch" className="flex items-center gap-2 rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
        }
      />
      <BatchDetailView batchJob={batchJob} onRefetch={refetch} />
    </PageBody>
  );
}
```

- [ ] **Step 7.4: Run frontend build**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: Build succeeds.

- [ ] **Step 7.5: Commit**

```bash
git add frontend/src/components/sirafit/batch/BatchItemRow.tsx frontend/src/components/sirafit/batch/BatchDetailView.tsx frontend/src/routes/_app.batch.$id.tsx
git commit -m "feat(batch): add frontend batch detail page with polling"
```

---

## Task 8: Comprehensive Tests

**Files:**

- Modify: `backend/tests/test_batch_api.py` (add more tests)
- Create: `backend/tests/test_batch_integration.py`

**Interfaces:**

- Tests full flow: create → process → poll → retry failed

- [ ] **Step 8.1: Write integration test**

```python
# backend/tests/test_batch_integration.py
import uuid
import pytest
from app.models.job import Job
from app.models.profile import Profile
from app.models.batch import BatchJob

def test_batch_tag_full_flow(client, auth_headers, test_user, db):
    """Full flow: create tag batch -> process sync -> verify results."""
    # Create jobs
    jobs = [Job(external_id=f"tag-flow-{i}", title=f"Job {i}", company="Co", tags=["python"]) for i in range(3)]
    db.add_all(jobs); db.commit()
    job_ids = [str(j.id) for j in jobs]

    # Create batch
    response = client.post("/api/v1/batch", json={
        "operation_type": "tag",
        "job_ids": job_ids,
        "params": {"tags": ["remote"], "action": "add"}
    }, headers=auth_headers)
    assert response.status_code == 201
    batch_id = response.json()["id"]

    # Get batch - should be pending
    response = client.get(f"/api/v1/batch/{batch_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

    # In test env, Celery falls back to sync - so process immediately
    # Poll until done
    import time
    for _ in range(10):
        time.sleep(0.5)
        response = client.get(f"/api/v1/batch/{batch_id}", headers=auth_headers)
        if response.json()["status"] in ("completed", "partial", "failed"):
            break

    data = response.json()
    assert data["status"] == "completed"
    assert data["succeeded_items"] == 3
    assert data["failed_items"] == 0

    # Verify tags applied
    for job in jobs:
        db.refresh(job)
        assert "remote" in job.tags

def test_batch_score_full_flow(client, auth_headers, test_user, db):
    """Full flow: create score batch -> process -> verify JobMatchScore created."""
    from app.models.score import JobMatchScore
    from app.models.profile import Profile
    from app.core.security import get_password_hash

    # Create profile with skills
    profile = Profile(user_id=test_user.id, skills=[], experiences=[], educations=[])
    db.add(profile); db.commit()

    # Create jobs
    jobs = [Job(external_id=f"score-flow-{i}", title="Python Engineer", company="Co", tags=["python", "django"]) for i in range(2)]
    db.add_all(jobs); db.commit()
    job_ids = [str(j.id) for j in jobs]

    response = client.post("/api/v1/batch", json={
        "operation_type": "score",
        "job_ids": job_ids,
        "params": {}
    }, headers=auth_headers)
    assert response.status_code == 201
    batch_id = response.json()["id"]

    import time
    for _ in range(10):
        time.sleep(0.5)
        response = client.get(f"/api/v1/batch/{batch_id}", headers=auth_headers)
        if response.json()["status"] in ("completed", "partial", "failed"):
            break

    data = response.json()
    assert data["status"] == "completed"
    assert data["succeeded_items"] == 2

    # Verify JobMatchScore rows created
    scores = db.query(JobMatchScore).filter(
        JobMatchScore.user_id == test_user.id,
        JobMatchScore.job_id.in_([uuid.UUID(jid) for jid in job_ids])
    ).all()
    assert len(scores) == 2
    for s in scores:
        assert 0 <= s.score <= 100
        assert s.breakdown is not None

def test_batch_retry_failed_only(client, auth_headers, test_user, db):
    """Retry only re-queues failed items."""
    # Create a job that will fail analysis (no AI key)
    job = Job(external_id="fail-job", title="Engineer", company="Co")
    db.add(job); db.commit()

    response = client.post("/api/v1/batch", json={
        "operation_type": "analyze",
        "job_ids": [str(job.id)],
        "params": {}
    }, headers=auth_headers)
    assert response.status_code == 201
    batch_id = response.json()["id"]

    import time
    for _ in range(10):
        time.sleep(0.5)
        response = client.get(f"/api/v1/batch/{batch_id}", headers=auth_headers)
        if response.json()["status"] in ("completed", "partial", "failed"):
            break

    data = response.json()
    assert data["status"] in ("failed", "partial")
    assert data["failed_items"] >= 1

    # Retry
    response = client.post(f"/api/v1/batch/{batch_id}/retry", headers=auth_headers)
    assert response.status_code == 201
    retry_batch_id = response.json()["id"]
    retry_data = response.json()
    assert retry_data["total_items"] == data["failed_items"]

    # Wait for retry
    for _ in range(10):
        time.sleep(0.5)
        response = client.get(f"/api/v1/batch/{retry_batch_id}", headers=auth_headers)
        if response.json()["status"] in ("completed", "partial", "failed"):
            break

def test_batch_cancel(client, auth_headers, test_user, db):
    """Cancel sets flag, worker stops."""
    jobs = [Job(external_id=f"cancel-{i}", title=f"Job {i}", company="Co") for i in range(5)]
    db.add_all(jobs); db.commit()
    job_ids = [str(j.id) for j in jobs]

    response = client.post("/api/v1/batch", json={
        "operation_type": "tag",
        "job_ids": job_ids,
        "params": {"tags": ["test"], "action": "add"}
    }, headers=auth_headers)
    batch_id = response.json()["id"]

    # Cancel immediately
    response = client.post(f"/api/v1/batch/{batch_id}/cancel", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["cancel_requested"] is True

    import time
    for _ in range(10):
        time.sleep(0.5)
        response = client.get(f"/api/v1/batch/{batch_id}", headers=auth_headers)
        if response.json()["status"] in ("cancelled", "completed", "partial", "failed"):
            break

    # Status should be cancelled or partial (some items processed before cancel)
    assert response.json()["status"] in ("cancelled", "partial")
```

- [ ] **Step 8.2: Run all batch tests**

```bash
cd backend && python -m pytest tests/test_batch_operations.py tests/test_batch_api.py tests/test_batch_worker.py tests/test_batch_integration.py -v
```

Expected: All tests pass.

- [ ] **Step 8.3: Commit**

```bash
git add backend/tests/test_batch_integration.py backend/tests/test_batch_operations.py
git commit -m "test(batch): add integration and full-flow tests"
```

---

## Task 9: Final Verification & Polish

**Files:**

- Verify all existing tests still pass
- Run frontend build
- Check migration runs cleanly

- [ ] **Step 9.1: Run full backend test suite (batch-related)**

```bash
cd backend && python -m pytest tests/ -k "batch" -v
```

Expected: All batch tests pass.

- [ ] **Step 9.2: Run full frontend build**

```bash
cd frontend && npm run build 2>&1 | tail -30
```

Expected: Build succeeds with no errors.

- [ ] **Step 9.3: Verify migration order**

```bash
cd backend && python -c "
from alembic.config import Config
from alembic import command
cfg = Config('alembic.ini')
command.history(cfg)
"
```

Expected: Shows `add_batch_jobs_table` after `add_application_tracking`.

- [ ] **Step 9.4: Add batch to API tags in router**

```python
# backend/app/api/router.py already updated in Task 4.2
```

- [ ] **Step 9.5: Commit any remaining changes**

```bash
git add -A
git commit -m "feat(batch): final polish and verification"
```

---

## Task 10: Documentation Update (Optional)

**Files:**

- Update any API docs if applicable

- [ ] **Step 10.1: Add batch endpoints to API docs if using OpenAPI** (already auto-generated by FastAPI)
- [ ] **Step 10.2: Commit**

```bash
git commit --allow-empty -m "docs(batch): API docs auto-generated"
```

---

## Execution Order Summary

| Task | Files Created     | Key Deliverable                                |
| ---- | ----------------- | ---------------------------------------------- |
| 1    | Migration + Model | `BatchJob` table & SQLAlchemy model          |
| 2    | Schemas           | `BatchJobCreate`, `BatchJobResponse`, etc. |
| 3    | Services          | 4 item handlers (analyze, score, tag, archive) |
| 4    | API               | `/api/v1/batch` endpoints                    |
| 5    | Worker            | Celery task + enqueue helper                   |
| 6    | Frontend List     | `/batch` page + create modal                 |
| 7    | Frontend Detail   | `/batch/$id` page with polling               |
| 8    | Tests             | Unit + integration tests                       |
| 9    | Verification      | Full test pass, build success                  |
| 10   | Docs              | (Auto-generated)                               |

Each task produces independently testable code. Tasks 1-5 are backend-only and can be verified with `pytest`. Tasks 6-7 are frontend and verified with `npm run build`. Task 8 ties everything together.
