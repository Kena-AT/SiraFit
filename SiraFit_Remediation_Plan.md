# SiraFit Performance & Code Quality Remediation Plan

**Date:** 2026-08-21
**Based on:** Codebase Audit Reports (2026-08-20, 2026-08-21)
**Owner:** Engineering Team
**Objective:** Eliminate the root causes of slow page loads and close code-completeness/security gaps identified in the audit, in a sequenced, low-risk rollout.

---

## 1. Summary of Findings

| #  | Issue                                                                               | Severity    | Area               |
| -- | ----------------------------------------------------------------------------------- | ----------- | ------------------ |
| 1  | N+1 query in`list_ranked_jobs`                                                    | 🔴 Critical | Backend            |
| 2  | No request deduplication (singleflight)                                             | 🔴 Critical | Backend            |
| 3  | Unstable React Query keys in Jobs Explorer                                          | 🔴 Critical | Frontend           |
| 4  | Match page fires 200 HTTP requests for match scores                                 | 🔴 Critical | Frontend + Backend |
| 5  | Manual`setInterval` polling bypasses cache                                        | 🟡 High     | Frontend           |
| 6  | Incomplete cache invalidation (job list, match score, user)                         | 🟡 High     | Backend            |
| 7  | Dashboard cache never invalidated                                                   | 🟡 High     | Backend            |
| 8  | Missing DB indexes (applications, follow-ups, notifications, audit log)             | 🟡 High     | Database           |
| 9  | `pool_timeout=30s` too high; no pool exhaustion monitoring                        | 🟡 High     | Backend            |
| 10 | List pages using`useEffect` instead of `useQuery` (Resumes, Cover Letters only) | 🟡 High     | Frontend           |
| 11 | Redis cold-start probe (~200ms)                                                     | 🟢 Medium   | Backend            |
| 12 | Redis connection pool not configured (`max_connections`)                          | 🟢 Medium   | Backend            |
| 13 | No rate limiting on AI endpoints (analyze/generate)                                 | 🟢 Medium   | Backend            |
| 14 | No payload size validation (import, batch)                                          | 🟢 Medium   | Backend            |
| 15 | Duplicate`Profile` queries per request                                            | 🟢 Medium   | Backend            |
| 16 | Landing stats re-runs match scoring instead of reading persisted scores             | 🟢 Medium   | Backend            |
| 17 | Background worker liveness check missing                                            | 🟢 Medium   | Backend            |
| 18 | `batch.test.ts` has no test runner script                                         | 🟢 Medium   | Frontend           |
| 19 | Dead code / stale TODOs / abandoned routes                                          | 🔵 Low      | Both               |
| 20 | No error boundaries / Suspense fallbacks                                            | 🔵 Low      | Frontend           |
| 21 | Redis key growth / no eviction policy                                               | 🔵 Low      | Infra              |

---

## 2. Guiding Principles for the Rollout

1. **Fix correctness before speed.** Cache invalidation bugs (stale data) are worse than latency — sequence Phase 2 (cache correctness) tightly after Phase 1 (raw latency).
2. **Ship behind feature flags where risk is non-trivial** — specifically request deduplication and the N+1 query rewrite, since both touch high-traffic read paths.
3. **One PR per numbered issue** where possible, to keep review small and rollback trivial.
4. **Add a regression test before each fix**, not after — this audit found the bugs because there was no test coverage catching them (e.g., no test asserts `list_ranked_jobs` issues a single query).
5. **Measure before/after** using `pg_stat_statements` and browser Network tab timings — the verification checklist in Section 7 is not optional.

---

## 3. Phase 1 - Critical Fixes

**Goal:** Directly address the reported "pages load slowly" symptom. These four fixes should collectively cut `/app/jobs` and `/app/match` load times from ~2–3s to under 500ms.

### 3.1 Fix N+1 Query in `list_ranked_jobs`

**File:** `backend/app/api/jobs.py:43-70`

**Note:** Do not add a `viewonly` relationship to the `Job` model for this — `current_user.id` is only available at query time, not at model-definition time, making a correlated relationship definition fragile and misleading. The query-only approach below is simpler and correct.

**Steps:**

1. Replace the per-job loop with a single `outerjoin` against a user-scoped `JobMatchScore` subquery.
2. Use `contains_eager` with an explicit alias to instruct SQLAlchemy to populate match score data from the join result without a separate SELECT.
3. Add a unit test asserting exactly 1 SQL statement is issued for N jobs (use `sqlalchemy.event` query counter).

```python
# backend/app/api/jobs.py
from sqlalchemy.orm import contains_eager

@router.get("/ranked", response_model=RankedJobListResponse)
def list_ranked_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    score_subq = (
        db.query(JobMatchScore)
        .filter(JobMatchScore.user_id == current_user.id)
        .subquery()
    )
    jobs = (
        db.query(Job)
        .outerjoin(score_subq, Job.id == score_subq.c.job_id)
        .add_columns(
            score_subq.c.score,
            score_subq.c.match_reason,
        )
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return RankedJobListResponse(items=[
        RankedJobResponse(job=job, match_score=score, match_reason=reason)
        for job, score, reason in jobs
    ])
```

**Verification:** `pg_stat_statements` shows 1 query for `/jobs/ranked` regardless of page size; response time drops proportionally to `(N-1) × query_latency`.

**Rollback:** Revert to loop-based version — no data migration involved, so rollback is a simple code revert.

---

### 3.2 Add Request Deduplication (Singleflight)

**File:** `backend/app/core/cache.py` (new function), `backend/app/api/jobs.py` (adopt in `list_jobs`)

**Steps:**

1. Implement `cache_get_or_compute()` with an `asyncio.Lock` per cache key, double-checked locking pattern.
2. Use `cachetools.TTLCache` to cap the in-process lock dict — `jobs:list:{user_id}:{hash}` has high cardinality (one entry per unique filter combination per user) and a plain `dict` would grow unboundedly. A TTL-capped LRU evicts stale entries automatically. Install via `pip install cachetools`.
3. Convert `list_jobs` to `async def` and route its query logic through a nested `fetch()` coroutine.
4. **Caveat:** `asyncio.Lock` dedupes within a single process/worker only. If running multiple Uvicorn/Gunicorn workers, cross-process duplication still occurs. If that matters at current scale, consider a Redis-based distributed lock (`SET NX PX`) instead — flag as a follow-up, not a Phase 1 blocker.
5. Add a load test (e.g., `asyncio.gather` of 20 concurrent identical requests) asserting DB query count stays near 1, not 20.

```python
# backend/app/core/cache.py
import asyncio
from cachetools import TTLCache
from threading import Lock as ThreadLock

# Cap at 1000 unique in-flight keys; auto-evict after 60s
_flight: TTLCache = TTLCache(maxsize=1000, ttl=60)
_flight_lock = ThreadLock()  # guards mutations to _flight itself

async def cache_get_or_compute(key: str, ttl: int, func, *args, **kwargs):
    val = cache_get(key)
    if val is not None:
        return val

    with _flight_lock:
        if key not in _flight:
            _flight[key] = asyncio.Lock()
        lock = _flight[key]

    async with lock:
        val = cache_get(key)  # double-check after acquiring lock
        if val is not None:
            return val
        val = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        cache_set(key, val, ttl)
        return val
```

```python
# backend/app/api/jobs.py
@router.get("/", response_model=JobListResponse)
async def list_jobs(...):
    cache_key = _build_cache_key(...)
    async def fetch():
        # existing query logic, unchanged
        return JobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)
    return await cache_get_or_compute(cache_key, 30, fetch)
```

**Verification:** Concurrent identical requests result in 1 DB query + 1 Redis write, confirmed via query logs during a burst test.

**Rollback:** Feature-flag the dedup wrapper (`if settings.ENABLE_REQUEST_DEDUP: ...`) so it can be disabled without a redeploy if it introduces lock contention issues.

---

### 3.3 Fix Unstable React Query Keys in Jobs Explorer

**File:** `frontend/src/routes/_app.jobs.index.tsx:48-66`

**Steps:**

1. Replace the object-based query key with a memoized array of primitives.
2. Add an eslint rule or code-review checklist item: *no object/array literals directly in `queryKey` without `useMemo`.*
3. Manually verify in React Query Devtools that navigating/filtering no longer shows a new query entry on every keystroke.

```typescript
const queryKey = useMemo(() => [
  "jobs",
  page,
  limit,
  sortBy,
  sortOrder,
  activeSearch,
  companyFilter,
  locationFilter,
  sourceFilter,
], [page, limit, sortBy, sortOrder, activeSearch, companyFilter, locationFilter, sourceFilter]);

const { data, isLoading, error, refetch } = useQuery({
  queryKey,
  queryFn: () => getJobs({
    skip: page * limit,
    limit,
    sort_by: sortBy,
    sort_order: sortOrder,
    search: activeSearch || undefined,
    company: companyFilter || undefined,
    location: locationFilter || undefined,
    source: sourceFilter || undefined,
  }),
});
```

**Verification:** Typing in the search box no longer triggers a network request per keystroke (only after debounce/submit); React Query cache hit rate visibly improves in Devtools.

**Rollback:** Trivial — single-file revert.

---

### 3.4 Fix Match Page 200-Request N+1

**Files:** `frontend/src/routes/_app.match.tsx:33-37`, `backend/app/api/jobs.py` (new endpoint)

**Problem:** `_app.match.tsx` currently loads a job list and then fires a `getCachedMatchScore(job.id)` call per job via `Promise.all`, resulting in up to 200 simultaneous HTTP requests to the backend. This is the single largest frontend performance issue in the codebase and is not addressed by the Jobs Explorer query key fix (3.3), which is a different page.

```typescript
// _app.match.tsx:33-37 — CURRENT (200 requests)
const withScores = await Promise.all(
  list.jobs.map(async (job) => {
    const score = await getCachedMatchScore(job.id);  // one request per job
    return { ...job, score };
  })
);
```

**Do not naively convert this to `useQuery`** — splitting into two queries (`getJobs` then N score fetches) would cause UI flicker and doesn't remove the N+1 pattern.

**Fix:** Add a dedicated backend endpoint that returns jobs pre-joined with their match scores in a single query, then replace the two-step client pattern with a single `useQuery` call.

```python
# backend/app/api/jobs.py — new endpoint
@router.get("/with-scores", response_model=JobWithScoreListResponse)
def list_jobs_with_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    score_subq = (
        db.query(JobMatchScore)
        .filter(JobMatchScore.user_id == current_user.id)
        .subquery()
    )
    rows = (
        db.query(Job, score_subq.c.score)
        .outerjoin(score_subq, Job.id == score_subq.c.job_id)
        .order_by(score_subq.c.score.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return JobWithScoreListResponse(
        items=[JobWithScore(job=job, score=score) for job, score in rows]
    )
```

```typescript
// _app.match.tsx — AFTER
const { data, isLoading } = useQuery({
  queryKey: ["jobs-with-scores", page, limit],
  queryFn: () => getJobsWithScores({ skip: page * limit, limit }),
});
```

**Steps:**

1. Add the `GET /jobs/with-scores` endpoint and `JobWithScoreListResponse` / `JobWithScore` schemas to the backend.
2. Add `getJobsWithScores` to `frontend/src/lib/api/jobs.ts`.
3. Refactor `_app.match.tsx` to use a single `useQuery` with the new endpoint — remove the `Promise.all` loop entirely.
4. Add `JobWithScore` type to the frontend type definitions.

**Verification:** Network tab on `/app/match` shows 1 API call instead of 200+; page load time drops from several seconds to <500ms.

**Rollback:** The old `getCachedMatchScore` loop can be restored independently; the new endpoint is additive and doesn't remove anything from the backend.

---

## 4. Phase 2 — High Priority

**Goal:** Eliminate stale-data bugs and extend the caching pattern consistently across the app.

### 4.1 Complete Cache Invalidation Coverage

**Files:** `applications.py`, `batch.py` / `batch_operations.py`, `users.py`, `resumes.py`, `cover_letters.py`

**Steps:**

1. Build a small helper that centralizes "what to invalidate on mutation of X":
   ```python
   # backend/app/core/cache.py
   def invalidate_job_related(user_id: int):
       cache_delete_prefix(f"jobs:list:{user_id}:")
       cache_delete(f"dashboard:stats:{user_id}")

   def invalidate_match_score(user_id: int, job_id: int):
       cache_delete(f"match_score:{user_id}:{job_id}")
       cache_delete(f"dashboard:stats:{user_id}")

   def invalidate_user_profile(user_id: int):
       cache_delete(f"user:me:{user_id}")
   ```
2. Call the appropriate helper from every mutation endpoint identified in the audit:
   - `batch_tag_item`, `batch_archive_item` → `invalidate_job_related`
   - `create_application`, `transition_status` → `invalidate_job_related` + `invalidate_match_score`
   - `update_notification_preferences`, `update_ai_provider_keys`, `update_resume_defaults` → `invalidate_user_profile`
3. Add an integration test per mutation: call the mutation, then assert the relevant cache key is empty (`cache_get(key) is None`).

**Verification:** Manually reproduce the audit's example bug (batch tag → stale list) and confirm the list reflects the change immediately, not after 30s.

---

### 4.2 Fix Dashboard Cache (Never Invalidated)

**File:** `backend/app/api/dashboard.py`, plus all mutation endpoints touching dashboard-visible data.

**Steps:**

1. Add `cache_delete(f"dashboard:stats:{user_id}")` to:
   - `create_application`, `transition_status` (applications.py)
   - `batch` operations affecting applications
   - `create_resume`, `update_resume`, `delete_resume` (resumes.py)
   - `create_cover_letter` / regenerate (cover_letters.py)
2. Since this touches many call sites, prefer wiring it through the `invalidate_job_related` / a new `invalidate_dashboard` helper from 4.1 rather than duplicating `cache_delete` calls inline.

**Verification:** Create an application in the UI, navigate to dashboard — count updates immediately, no 30s lag.

---

### 4.3 Replace Manual Polling with `useQuery` + `refetchInterval`

**File:** `frontend/src/routes/_app.jobs.$jobId.tsx:93-113`

```typescript
const { data: analysis } = useQuery({
  queryKey: ["job-analysis", jobId],
  queryFn: () => getJobAnalysis(jobId),
  refetchInterval: (query) => query.state.data?.status === "processing" ? 2500 : false,
  refetchIntervalInBackground: false,
});
```

**Steps:**

1. Remove `pollRef`, `setInterval`, and manual cleanup logic entirely.
2. Confirm the `refetchInterval` callback signature matches the installed React Query major version (v4 passes `data` directly to the callback; v5 passes the full `query` object — verify against `package.json` before implementing).
3. Add exponential-backoff-on-failure via React Query's built-in `retry`/`retryDelay` options rather than hand-rolling it.

**Verification:** Job analysis panel still updates every ~2.5s while processing, stops polling on completion/failure, and shows up correctly in React Query Devtools (no orphaned intervals on unmount).

---

### 4.4 Add Missing Database Indexes

**File:** New Alembic migration, e.g. `backend/migrations/versions/20260822_001_add_missing_indexes.py`

```sql
CREATE INDEX CONCURRENTLY ix_job_apps_user_status ON job_applications (user_id, status);
CREATE INDEX CONCURRENTLY ix_job_apps_user_followup ON job_applications (user_id, follow_up_at)
    WHERE follow_up_at IS NOT NULL;
CREATE INDEX CONCURRENTLY ix_match_scores_user_score ON job_match_scores (user_id, score DESC);
CREATE INDEX CONCURRENTLY ix_audit_log_user_created ON audit_logs (user_id, created_at DESC);
CREATE INDEX CONCURRENTLY ix_notifications_user_status ON notifications (user_id, status);
```

**Steps:**

1. Use `CREATE INDEX CONCURRENTLY` to avoid locking tables in production (requires running outside a transaction block — configure the Alembic migration with `autocommit_block()` or set `op.execute` outside a transaction).
2. Run `EXPLAIN ANALYZE` on the dashboard stats query and follow-ups query before/after to confirm the planner picks up the new indexes.
3. Deploy migration during low-traffic window even though `CONCURRENTLY` avoids full locks — building indexes still consumes I/O.

**Verification:** `EXPLAIN ANALYZE` shows Index Scan instead of Seq Scan on the four affected query patterns.

---

### 4.5 Reduce `pool_timeout` and Add Pool Exhaustion Monitoring

**File:** `backend/app/core/database.py:12-20`

```python
engine_kwargs["pool_timeout"] = 10   # was 30 — fail fast under exhaustion
engine_kwargs["pool_size"] = 20      # unchanged — but review before increasing
engine_kwargs["max_overflow"] = 10   # unchanged — burst ceiling of 30 total
```

**Steps:**

1. Reduce `pool_timeout` from 30s to 10s so exhausted-pool requests return a 503 promptly rather than hanging. This alone does not prevent exhaustion — it just makes the failure mode faster and observable.
2. **Critically:** Add monitoring on pool exhaustion before raising `pool_size`. If real traffic regularly exceeds 30 concurrent DB connections (`pool_size + max_overflow`), the underlying issue is probably slow queries (fix those first via 3.1 and 4.4) rather than an undersized pool. Raising `pool_size` without addressing slow queries just delays exhaustion.
3. Expose pool stats via the health endpoint:
   ```python
   # backend/app/api/stats.py or main.py health check
   from app.core.database import engine
   pool = engine.pool
   stats = {
       "pool_size": pool.size(),
       "checked_in": pool.checkedin(),
       "checked_out": pool.checkedout(),
       "overflow": pool.overflow(),
   }
   ```
4. Alert when `checked_out / (pool_size + max_overflow) > 0.8` (80% utilisation) — that's the signal to investigate, not to blindly raise pool size.

**Verification:** Under a simulated pool-exhaustion load test, requests fail fast (~10s) with a 503 instead of hanging up to 30s. Pool stats endpoint returns current utilisation.

---

### 4.6 Migrate Manual `useEffect` Fetches to `useQuery` (Resumes & Cover Letters)

**Files:** `_app.resumes.index.tsx:18`, `_app.cover-letters.index.tsx:18`

**Scope note:** Applications is already migrated (`_app.applications.index.tsx:48` uses `useQuery` with a stable key). Match is handled separately in 3.4 — it requires a new backend endpoint and cannot be converted with the standard pattern below. This item covers only the two remaining simple list pages.

**Steps:**

1. Treat each page as its own PR.
2. Standard conversion pattern:
   ```typescript
   // Before: useState + useEffect + fetch
   // After:
   const { data, isLoading, error } = useQuery({
     queryKey: ["resumes"],           // or ["cover-letters"]
     queryFn: () => getResumes(),     // or getCoverLetters()
   });
   ```
3. Confirm loading/error UI states are preserved — map existing bespoke loading spinners to `isLoading`/`isError` from `useQuery`.
4. Do **not** pass an explicit `staleTime` — omit it to inherit `staleTime: 60_000` from the global `queryClient` config in `router.tsx`. Any per-query override breaks consistent caching behaviour. Add this as a required code-review checklist item for each PR.

**Verification:** Navigating away from and back to Resumes or Cover Letters within 60s shows instant render with no network request (served from cache). Confirm in React Query Devtools that each query shows `staleTime: 60000` with no per-query override.

---

## 5. Phase 3 — Medium Priority

### 5.1 Redis Warm-Up on Startup

**File:** `backend/app/main.py`, `backend/app/core/redis_client.py`

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(warm_redis())
    yield

async def warm_redis():
    try:
        client = get_redis_client()
        if client:
            await asyncio.to_thread(client.ping)
    except Exception:
        pass  # non-fatal; app should still boot if Redis is briefly unavailable
```

**Verification:** First request after a fresh deploy no longer shows the ~200ms Redis-connect spike in APM traces.

### 5.2 Rate Limit AI Endpoints

**Files:** `jobs.py` (`/analyze`), `resumes.py` (`/generate`), `cover_letters.py` (`/generate`)

**Steps:** Reuse the existing sliding-window token bucket already implemented for auth (per the security review, this pattern exists) rather than building a new mechanism. Apply per-user limits (e.g., 10 analyses/hour) sized against actual AI provider cost budgets.

### 5.3 Validate Payload Sizes

**Files:** `jobs.py` (`/import`), `batch.py` (`/batch`)

**Steps:** Add Pydantic `Field(max_length=...)` / explicit length checks on `import_in.data` and `job_ids`. Return `422` with a clear message rather than letting oversized payloads reach the DB layer.

### 5.4 Request-Scoped Profile Dependency

**Files:** `applications.py`, `jobs.py`, `resumes.py`, `stats.py`

```python
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile
```

**Before implementing:** Verify that `get_current_user` or any other shared dependency does not already load the `Profile` as part of its own query — if it does, this dependency would add a second query rather than removing one. Check `auth.py` and `dependencies.py` for any `joinedload(User.profile)` or similar. If the profile is already attached to the `User` object, access it via `current_user.profile` rather than adding a new dependency.

If the profile is not already loaded, replace ad-hoc `Profile` queries in `applications.py`, `jobs.py`, `resumes.py`, and `stats.py` with `profile: Profile = Depends(get_user_profile)`. This eliminates redundant queries *within* a single request when multiple internal functions each fetch the profile independently, but each HTTP request will still issue one profile query.

### 5.5 Fix Landing Stats to Read Persisted Match Scores

**File:** `backend/app/api/stats.py:210-264`

**Problem:** `_get_top_match_queue` currently calls `calculate_match_score` in a loop for up to 50 jobs on every landing page hit — recomputing scores that the batch scoring pipeline has already calculated and persisted to `JobMatchScore`. Caching this recomputation (the previous plan's option b) is a band-aid that still wastes CPU and drifts from the persisted values. The correct fix is option a: read from the table directly.

**Steps:**

1. Replace the scoring loop in `_get_top_match_queue` with a direct query against `JobMatchScore`, ordered by score descending, joined to `Job` for the job details.
2. Fall back gracefully (empty list) if no scores exist yet for the user — batch scoring may not have run.
3. This also means the landing stats endpoint becomes a simple DB read, fast enough to not need caching at all.

```python
# backend/app/api/stats.py
def _get_top_match_queue(db: Session, current_user) -> list:
    rows = (
        db.query(Job, JobMatchScore)
        .join(JobMatchScore, (JobMatchScore.job_id == Job.id) & (JobMatchScore.user_id == current_user.id))
        .order_by(JobMatchScore.score.desc())
        .limit(10)
        .all()
    )
    return [{"job": job, "score": score.score} for job, score in rows]
```

**Verification:** Landing page stats endpoint no longer shows `calculate_match_score` in profiling traces; returns pre-computed scores from the table.

### 5.6 Configure Redis Connection Pool

**File:** `backend/app/core/redis_client.py`

**Problem:** The current `redis.Redis()` client uses a single implicit connection with no pool. Under concurrent request load, connections queue behind each other.

**Steps:** Add explicit connection pool config:

```python
# backend/app/core/redis_client.py
from redis import ConnectionPool, Redis

pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=20,
    socket_connect_timeout=0.2,
    socket_timeout=0.5,
)

def get_redis_client() -> Redis:
    return Redis(connection_pool=pool)
```

Size `max_connections` to match the DB pool size (`pool_size=20`) so both resources scale together.

**Verification:** Under burst load, Redis commands no longer queue; `redis-cli info clients` shows `connected_clients` stable rather than spiking.

### 5.7 Add Worker Liveness Check

**File:** `backend/app/main.py:70-86`

**Problem:** The startup health check pings Redis but does not verify the Celery broker. If the worker process is down, resume generation, batch processing, and PDF rendering silently queue jobs that never complete — with no observable signal at the API layer.

**Steps:**

1. Add a Celery inspect call to the `/health/status` endpoint:
   ```python
   from app.worker.celery_app import celery_app

   def check_worker_health() -> bool:
       try:
           inspect = celery_app.control.inspect(timeout=1.0)
           active = inspect.active()
           return active is not None  # None means no workers responded
       except Exception:
           return False
   ```
2. Include `worker_healthy: bool` in the health status response so monitoring systems can alert on it separately from Redis/DB health.
3. Do not make worker health a hard startup dependency — the API should still boot if Celery is temporarily unavailable.

**Verification:** Stopping the Celery worker and hitting `/health/status` returns `worker_healthy: false` within ~1s; alerting fires appropriately.

---

## 6. Phase 4 — Low Priority / Cleanup

| Task                                                          | Action                                                                                                                                                                                                                          |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stale 2FA TODO (`AuthContext.tsx:49`)                       | Remove comment, or file a ticket and reference the ticket ID in the comment                                                                                                                                                     |
| `frontend/src/lib/api/batch.test.ts`                        | File has 20 tests but`package.json` has no `test` or `test:unit` script — tests are currently dead weight. Either add a Jest/Vitest runner script or remove the file.                                                    |
| `_app.match.tsx` / `_app.ranking.tsx`                     | Product decision needed: consolidate into`/jobs?ranked=true` or confirm they're intentionally separate; don't silently delete                                                                                                 |
| `_app.analytics.market.tsx` / `_app.analytics.skills.tsx` | Placeholders with no data fetching — implement or remove before next release to avoid shipping dead UI                                                                                                                         |
| `backend/app/worker/`                                       | Worker is wired (`tasks.py` defines 7 tasks across resume_generation, pdf_rendering, batch_processing, notifications queues) — verify it is included in the production deployment manifest (Procfile / Docker Compose / k8s) |
| Error boundaries / Suspense                                   | Add a top-level error boundary per route layout (`_app.tsx`, `_app.jobs.tsx`, etc.) so a single component crash doesn't blank the whole page                                                                                |
| Redis key growth                                              | Set`maxmemory-policy allkeys-lru` in Redis config, or add a scheduled job to audit key counts                                                                                                                                 |

---

## 7. Verification Checklist (Run After Each Phase)

- [ ] `/app/jobs` loads in <500ms (baseline: ~2–3s)
- [ ] `/app/jobs?search=x` does not issue a network request on every keystroke
- [ ] `/app/jobs/$jobId` analysis panel uses React Query, no manual `setInterval` in DevTools
- [ ] Batch tag/archive operations invalidate the job list cache immediately (no 30s stale window)
- [ ] Dashboard stats update immediately after creating an application
- [ ] `list_ranked_jobs` executes exactly 1 SQL query regardless of result size (verify via `pg_stat_statements`)
- [ ] Concurrent identical `/jobs` requests are deduplicated (Redis write count ≈ 1, not N, under burst test)
- [ ] Cold start after deploy adds <50ms (Redis warm-up confirmed via APM)
- [ ] `/app/match` fires exactly 1 API request instead of 200+ `getCachedMatchScore` calls (confirmed via Network tab)
- [ ] Resumes and Cover Letters list pages show cache hits in React Query Devtools on repeat navigation within 60s; no per-query `staleTime` override present
- [ ] Job detail analysis `refetchInterval` callback uses React Query v5 signature (`(query) => query.state.data?.status === "processing" ? 2500 : false`) — confirmed against installed `@tanstack/react-query` version in `package.json`
- [ ] `EXPLAIN ANALYZE` confirms new indexes are used for dashboard, follow-ups, and notifications queries
- [ ] Pool exhaustion test returns 503 within ~10s, not 30s
- [ ] AI endpoints reject requests beyond the configured rate limit with a clear error
- [ ] Oversized import/batch payloads are rejected with 422, not processed

---

## 8. Risk Notes & Rollback Strategy

- **Request deduplication (3.2)** is the riskiest change — it introduces async locking into a previously synchronous code path. Ship behind a feature flag (`ENABLE_REQUEST_DEDUP`), monitor for lock contention or deadlock symptoms (elevated p99 latency, not reduced), and have a one-line flag flip as the rollback path.
- **Index creation (4.4)** should always use `CONCURRENTLY` in production to avoid table locks; if a migration fails partway, `DROP INDEX CONCURRENTLY IF EXISTS` before retrying, since a failed concurrent index build can leave an invalid index behind.
- **N+1 fix (3.1)** changes query structure but not the API response shape — low risk, but add a contract test comparing old vs. new endpoint output on a fixed dataset before deploying.
- All Phase 2 frontend migrations (4.6) should be shipped one page at a time, not as a single large PR, so a regression in one list page doesn't block or entangle with the others.
- The `cachetools` dependency introduced in 3.2 must be added to `requirements.txt` / `pyproject.toml` and pinned to a specific version before deploying - a missing dependency on a hot code path causes an immediate 500.

---

## Appendix: File Reference Map

| Area                               | Key Files                                                                                                 |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Job listing & caching              | `backend/app/api/jobs.py:91-222`                                                                        |
| Match scoring & N+1                | `backend/app/api/jobs.py:43-70`, `backend/app/services/matching_engine.py`                            |
| Match page 200-request N+1         | `frontend/src/routes/_app.match.tsx:33-37`, `backend/app/api/jobs.py` (new `/with-scores` endpoint) |
| Batch operations                   | `backend/app/services/batch.py`, `backend/app/services/batch_operations.py`                           |
| Redis client                       | `backend/app/core/redis_client.py`                                                                      |
| Cache layer                        | `backend/app/core/cache.py`                                                                             |
| DB pool config                     | `backend/app/core/database.py`                                                                          |
| Jobs Explorer (FE)                 | `frontend/src/routes/_app.jobs.index.tsx`                                                               |
| Job Detail (FE)                    | `frontend/src/routes/_app.jobs.$jobId.tsx`                                                              |
| API client                         | `frontend/src/lib/api/client.ts`                                                                        |
| Auth context                       | `frontend/src/contexts/AuthContext.tsx`                                                                 |
| Router/Query config                | `frontend/src/router.tsx`                                                                               |
| Indexes migration (existing)       | `backend/migrations/versions/20260820_001_add_composite_indexes_and_pgtrgm.py`                          |
| Indexes migration (new, this plan) | `backend/migrations/versions/20260822_001_add_missing_indexes.py`                                       |
| Dashboard                          | `backend/app/api/dashboard.py`                                                                          |
| Applications                       | `backend/app/api/applications.py`                                                                       |
| Stats / landing page               | `backend/app/api/stats.py`                                                                              |
| All routes registration            | `backend/app/api/router.py`                                                                             |
