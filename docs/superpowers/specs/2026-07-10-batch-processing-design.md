# Sprint 10: Batch Processing — Design Specification

**Date:** 2026-07-10  
**Status:** Approved  
**Sprint Goal:** Enable large-scale job operations (batch analyze, score, tag, archive)

---

## 1. Overview

Batch Processing adds a "Batch Processing Center" where users can run high-volume operations across their job pipeline with bounded retries, progress tracking, and per-item error visibility.

**Operations in scope (v1):**
- **Batch AI Analysis** — trigger AI analysis for 50-500 selected jobs
- **Batch Match Scoring** — recalculate match scores against user profile
- **Batch Tagging** — add/remove tags on multiple jobs
- **Batch Archive/Delete** — bulk archive or soft-delete jobs/applications

**Scale target:** Medium (50-500 items per batch), async via Celery with progress polling.

---

## 2. Data Model

### 2.1 `BatchJob` Table

```sql
CREATE TABLE batch_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    operation_type  VARCHAR(30) NOT NULL,  -- 'analyze' | 'score' | 'tag' | 'archive'
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending | running | completed | failed | partial | cancelled
    total_items     INTEGER NOT NULL DEFAULT 0,
    processed_items INTEGER NOT NULL DEFAULT 0,
    succeeded_items INTEGER NOT NULL DEFAULT 0,
    failed_items    INTEGER NOT NULL DEFAULT 0,
    payload         JSONB NOT NULL,        -- operation-specific params
    result_summary  JSONB DEFAULT '{}',    -- per-item results/errors
    cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX ix_batch_jobs_user_status ON batch_jobs(user_id, status);
CREATE INDEX ix_batch_jobs_user_type ON batch_jobs(user_id, operation_type);
CREATE INDEX ix_batch_jobs_created ON batch_jobs(created_at DESC);
```

### 2.2 `payload` Schema by Operation Type

| operation_type | payload keys |
|----------------|--------------|
| `analyze` | `job_ids: string[], provider?: string, model?: string, force_refresh?: boolean` |
| `score` | `job_ids: string[]` |
| `tag` | `job_ids: string[], tags: string[], action: 'add' | 'remove'` |
| `archive` | `job_ids: string[], target: 'jobs' | 'applications'` |

### 2.3 `result_summary` Structure

```json
{
  "job_id_1": { "status": "success", "result": {...} },
  "job_id_2": { "status": "error", "error": "Analysis failed: timeout" }
}
```

---

## 3. API Layer

### 3.1 Endpoints (`backend/app/api/batch.py`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/batch` | Create batch job, returns `BatchJobResponse` with `status=pending` |
| `GET` | `/api/v1/batch` | List batch jobs (query: `status`, `operation_type`, `skip`, `limit`) |
| `GET` | `/api/v1/batch/{id}` | Get batch job with full `result_summary` |
| `POST` | `/api/v1/batch/{id}/retry` | Re-queue only failed items, returns updated batch job |
| `POST` | `/api/v1/batch/{id}/cancel` | Set `cancel_requested=true`, worker checks flag each iteration |

### 3.2 Request/Response Schemas (`backend/app/schemas/batch.py`)

```python
class BatchJobCreate(BaseModel):
    operation_type: Literal["analyze", "score", "tag", "archive"]
    job_ids: List[UUID]
    params: Optional[Dict[str, Any]] = {}

class BatchJobResponse(BaseModel):
    id: UUID
    user_id: UUID
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

class BatchJobListResponse(BaseModel):
    jobs: List[BatchJobResponse]
    total: int
    skip: int
    limit: int
```

### 3.3 Validation Rules

- `job_ids` must not be empty, max 500 items
- All `job_ids` must exist and belong to current user
- `operation_type` must be one of the four supported types
- `params` validated per operation (Pydantic validators)

---

## 4. Worker Layer

### 4.1 Type-Specific Task Functions (in `app/services/batch_operations.py`)

Each reuses existing services where possible:

```python
# Analyze - reuses run_job_analysis()
async def batch_analyze_item(job_id: UUID, user_id: UUID, params: dict) -> dict:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    analysis = await run_job_analysis(job, db, provider=params.get("provider"), ...)
    return {"score": analysis.score, "status": analysis.status}

# Score - reuses calculate_match_score()
def batch_score_item(job_id: UUID, user_id: UUID, params: dict) -> dict:
    job = db.query(Job).filter(Job.id == job_id).first()
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    score_data = calculate_match_score(profile, job)
    # upsert JobMatchScore
    return {"score": score_data["score"], "breakdown": score_data["breakdown"]}

# Tag - direct model update
def batch_tag_item(job_id: UUID, user_id: UUID, params: dict) -> dict:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    tags = set(job.tags or [])
    if params["action"] == "add":
        tags.update(params["tags"])
    else:
        tags.difference_update(params["tags"])
    job.tags = list(tags)
    db.commit()
    return {"tags": job.tags}

# Archive - direct model update
def batch_archive_item(job_id: UUID, user_id: UUID, params: dict) -> dict:
    if params["target"] == "jobs":
        job = db.query(Job).filter(Job.id == job_id).first()
        job.source = "archived"  # soft archive
    else:
        app = db.query(JobApplication).filter(JobApplication.id == job_id, JobApplication.user_id == user_id).first()
        app.status = "archived"
    db.commit()
    return {"archived": True}
```

### 4.2 Orchestrator Task (`app/worker/tasks/batch.py`)

```python
@celery_app.task(
    name="app.worker.tasks.process_batch_job",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
    time_limit=1800,  # 30 min hard limit
)
def process_batch_job(self, batch_job_id: str) -> dict:
    db = SessionLocal()
    try:
        batch_job = db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        if not batch_job:
            return {"error": "BatchJob not found"}

        batch_job.status = "running"
        batch_job.started_at = utcnow()
        batch_job.total_items = len(batch_job.payload["job_ids"])
        db.commit()

        task_map = {
            "analyze": batch_analyze_item,
            "score": batch_score_item,
            "tag": batch_tag_item,
            "archive": batch_archive_item,
        }
        task_fn = task_map[batch_job.operation_type]

        for item_id in batch_job.payload["job_ids"]:
            # Check cancel flag
            db.refresh(batch_job)
            if batch_job.cancel_requested:
                batch_job.status = "cancelled"
                batch_job.completed_at = utcnow()
                db.commit()
                return {"status": "cancelled", "processed": batch_job.processed_items}

            try:
                result = task_fn(UUID(item_id), batch_job.user_id, batch_job.payload.get("params", {}))
                batch_job.succeeded_items += 1
                batch_job.result_summary[item_id] = {"status": "success", "result": result}
            except Exception as e:
                batch_job.failed_items += 1
                batch_job.result_summary[item_id] = {"status": "error", "error": str(e)}

            batch_job.processed_items += 1
            
            # Commit progress every 10 items to reduce DB load
            if batch_job.processed_items % 10 == 0:
                db.commit()

        # Final status
        if batch_job.failed_items == 0:
            batch_job.status = "completed"
        else:
            batch_job.status = "partial"
        batch_job.completed_at = utcnow()
        db.commit()

        return {"status": batch_job.status, "processed": batch_job.processed_items}

    except Exception as exc:
        logger.exception("batch_job_failed", extra={"batch_job_id": batch_job_id})
        batch_job = db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        if batch_job:
            batch_job.status = "failed"
            batch_job.completed_at = utcnow()
            db.commit()
        raise
    finally:
        db.close()
```

### 4.3 Enqueue Helper (`app/services/batch.py`)

```python
def enqueue_batch_job(batch_job_id: UUID) -> None:
    """Dispatch batch job to Celery (sync fallback for tests)."""
    try:
        from app.worker.celery_app import celery_app
        celery_app.send_task(
            "app.worker.tasks.process_batch_job",
            kwargs={"batch_job_id": str(batch_job_id)},
            queue="batch_processing",
        )
    except Exception as exc:
        logger.warning("batch_celery_unavailable_running_sync", extra={"error": str(exc)})
        # Sync fallback - run directly
        process_batch_job(str(batch_job_id))
```

---

## 5. Frontend Architecture

### 5.1 Routes

| Route | File | Purpose |
|-------|------|---------|
| `/batch` | `_app.batch.tsx` | Batch Processing Center (list + create) |
| `/batch/$id` | `_app.batch.$id.tsx` | Batch Detail (progress + results) |

### 5.2 Components

```
src/components/sirafit/
├── batch/
│   ├── BatchJobCard.tsx        # List row: status pill, progress bar, counts
│   ├── BatchCreateModal.tsx    # Operation picker, job multi-select, params form
│   ├── BatchDetailView.tsx     # Progress header, per-item table, retry button
│   └── BatchItemRow.tsx        # Expandable row in detail view (show error on failure)
```

### 5.3 TanStack Query Hooks (`src/lib/api/batch.ts`)

```typescript
export interface BatchJob {
  id: string;
  operation_type: string;
  status: "pending" | "running" | "completed" | "failed" | "partial" | "cancelled";
  total_items: number;
  processed_items: number;
  succeeded_items: number;
  failed_items: number;
  payload: Record<string, any>;
  result_summary: Record<string, { status: "success" | "error"; result?: any; error?: string }>;
  // ... timestamps
}

export const getBatchJobs = async (params?: { status?: string; type?: string }): Promise<BatchJob[]>;
export const getBatchJob = async (id: string): Promise<BatchJob>;
export const createBatchJob = async (input: { operation_type: string; job_ids: string[]; params?: {} }): Promise<BatchJob>;
export const retryBatchJob = async (id: string): Promise<BatchJob>;
export const cancelBatchJob = async (id: string): Promise<BatchJob>;
```

### 5.4 Polling Strategy

- **List page**: no auto-poll (user refreshes)
- **Detail page**: poll every 2s while `status in ("pending", "running")`
- Stop polling on `completed`, `failed`, `partial`, `cancelled`

---

## 6. Database Migration

File: `backend/migrations/versions/add_batch_jobs_table.py`

```python
def upgrade():
    op.create_table(
        "batch_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
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
```

---

## 7. QA / Tests

### 7.1 Unit Tests (`tests/test_batch_processing.py`)

- `test_batch_job_create_validation()` — payload validation per operation
- `test_batch_job_status_transitions()` — pending → running → completed/partial/failed/cancelled
- `test_batch_analyze_operation()` — mocks `run_job_analysis`, verifies result_summary
- `test_batch_score_operation()` — verifies JobMatchScore upsert
- `test_batch_tag_operation()` — add/remove tags idempotently
- `test_batch_archive_operation()` — soft archive jobs/applications
- `test_retry_failed_only()` — retry endpoint only re-queues failed items
- `test_cancel_sets_flag()` — cancel endpoint sets `cancel_requested`

### 7.2 Integration Tests

- Full flow: create batch → poll detail → verify progress → retry failed
- Concurrent batches for same user (isolation)

### 7.3 Load Test (manual)

- Create batch with 500 job_ids
- Verify completes within 5 min, memory stable, DB connections managed

---

## 8. Error Handling Summary

| Scenario | Behavior |
|----------|----------|
| Single item fails | Logged in `result_summary`, batch continues |
| All items fail | `status=failed`, `failed_items=total_items` |
| Partial success | `status=partial`, `succeeded_items > 0`, `failed_items > 0` |
| Cancel requested | `status=cancelled`, stops at next iteration |
| Celery broker down | Sync fallback executes in request thread (logged WARNING) |
| Worker crash mid-batch | `acks_late=True` + `max_retries=3` → re-queues entire batch (idempotent per-item) |
| Task timeout (30 min) | Celery kills task, batch stays `running`; manual retry or admin intervention |

---

## 9. Implementation Order

1. **Migration + Model** — `BatchJob` table, SQLAlchemy model
2. **Schemas + API** — Pydantic schemas, `/api/v1/batch` endpoints
3. **Services** — `batch_operations.py` (type-specific item handlers)
4. **Worker** — `process_batch_job` task, enqueue helper, Celery queue config
5. **Frontend List** — `/batch` page with create modal, job multi-select
6. **Frontend Detail** — `/batch/$id` with polling, per-item table, retry
6. **Tests** — Unit + integration
7. **Docs** — Update API docs if applicable

---

## 10. Out of Scope (Future)

- Scheduled/recurring batches
- Cross-user batch operations (admin)
- WebSocket/SSE for real-time progress (polling is sufficient for v1)
- Batch export (CSV/JSON of results)
- Operation chaining (analyze → score → tag in one batch)