# SiraFit — Bug Verification & Implementation Plan

## Executive Summary

After systematically auditing all 15 reported issues across the frontend and backend, the findings are:

| Severity | Issues Reported | Status | Remaining |
|----------|----------------|--------|-----------|
| **High** | 4 | **All 4 FIXED** | 0 |
| **Medium** | 5 | 3 FIXED, 2 PRESENT | 2 |
| **Low** | 6 | 3 FIXED, 3 PRESENT | 3 |
| **Total** | 15 | 10 fixed, 5 present | **5** |

All four **High Severity** issues — the ones that broke core functionality (password change, data export/deletion, Celery worker crash, dead ranked-jobs endpoint) — have already been resolved in the current codebase. The remaining 5 open issues are Medium and Low severity but would cause silent data-format bugs, dead links, or missing landing-page features.

---

## Already Fixed (No Action Required)

### High Severity — All 4 Fixed ✅

**1. Password Change endpoint**
- **Was:** Settings page faked a 500ms delay; `PUT /users/me/password` didn't exist; `PUT /users/me` stripped the password field.
- **Now:** `backend/app/api/users.py` (line 106) has a full `PUT /users/me/password` endpoint with current-password verification, 12-character minimum, uppercase/lowercase/digit complexity checks, audit logging via `AuditLog`, and refresh-token invalidation. The frontend (`_app.settings.index.tsx`) calls `changePassword()` from `@/lib/api:users.ts` (line 62) with matching client-side validation. No mocks.

**2. Data Export & Account Deletion**
- **Was:** "Generate export" and "Delete account" buttons used `setTimeout` mocks. No backend endpoints existed.
- **Now:** Backend has `GET /users/me/export` (line 205) returning real user data (profile, applications, resumes, cover letters, preferences) and `DELETE /users/me` (line 262) for full account deletion. The frontend (`_app.settings.privacy.tsx`) calls `exportUserData()` and `deleteAccount()` from the real API client. No `setTimeout`.

**3. notification_service.py broken import**
- **Was:** `from app.services.email import send_email` failed because `email.py` only exported `email_service` and `EmailService` class.
- **Now:** `email.py` (line 283) defines a module-level `send_email()` convenience function. The import in `notification_service.py` (line 14) works correctly. Celery tasks in `tasks.py` (lines 469-503) defer the import inside the task function body, so workers don't crash at import time.

**4. GET /jobs/ranked — Unreachable**
- **Was:** Endpoint registered after `/{job_id}`, causing FastAPI to match `/ranked` against the UUID path parameter (422 error).
- **Now:** In `backend/app/api/jobs.py`, the `/ranked` route (line 40) is defined **before** `/{job_id}` (line 195). FastAPI matches routes in registration order, so `/ranked` is now reachable. The frontend `_app.ranking.tsx` successfully calls `getRankedJobs()` which hits `/api/v1/jobs/ranked`.

### Medium Severity — 3 of 5 Fixed ✅

**5. Notification Preferences save mutation**
- **Was:** Mutated local state only; no backend endpoint.
- **Now:** Backend has `GET/PUT /users/me/preferences/notifications` (users.py lines 299-322). Frontend (`_app.settings.notifications.tsx`) uses `useQuery`/`useMutation` calling `getNotificationPreferences`/`updateNotificationPreferences` from the real API client. Persists to `UserPreference` model columns (`email_job_matches`, `email_daily_summary`, `push_notifications`, `email_new_opportunities`).

**6. Analytics — Rejection Stages identical counts**
- **Was:** All four rejection stages queried `status == "rejected"` with no stage distinction; `JobApplication` had no `rejection_stage` column.
- **Now:** `backend/app/models/job.py` (line 61) has a `rejection_stage` column. `backend/app/services/analytics.py` (lines 75-90) queries `a.status == "rejected" and a.rejection_stage == stage` with proper stage values: `"resume_screen"`, `"recruiter_call"`, `"tech_screen"`, `"onsite"`, `"offer_declined"`.

**7. UserPreference — AI Provider key fields missing**
- **Was:** `encrypted_anthropic_key`, `encrypted_openai_key`, `encrypted_grok_key`, `encrypted_mistral_key`, `encrypted_nvidia_key` didn't exist in the model.
- **Now:** `backend/app/models/user.py` (lines 66-72) defines all 7 encrypted key columns. Backend `users.py` (lines 351-422) has `GET/PUT /me/preferences/ai-keys` handling all 7. Frontend `_app.settings.ai.tsx` renders all 7 provider key inputs with status indicators. `job_analysis.py` (lines 117-129) maps provider → encrypted column and uses `hasattr` guard.

**8. Analytics — Market Trend always "+0%"**
- **Was:** Trend hardcoded to "+0%" with comment "would need historical data."
- **Now:** `backend/app/services/analytics.py` (lines 144-172) computes actual trend: queries job count in the last 30 days vs the previous 30-day window and calculates `trend_pct`.

**9. Import History Detail always empty**
- **Was:** `GET /jobs/import/{import_id}` returned `jobs=[]` and `errors=[]`.
- **Now:** `backend/app/api/jobs.py` (lines 384-432) fetches associated `JobApplication` records joined with `Job` from the database and returns populated `jobs_data` array.

### Low Severity — 3 of 6 Fixed ✅

**10. Devices Panel — Hardcoded fake data**
- **Was:** Rendered a hardcoded "MacBook Pro · alex-mbp" entry.
- **Now:** Frontend `_app.settings.index.tsx` (line 224) `DeviceList` component calls `getDevices()` API. Backend `users.py` (lines 513-545) queries `DeviceSession` records from the database, and `DeviceSession` model is created on login via `_create_device_session()`.

---

## Remaining Issues (Need Implementation)

### Medium Severity — 2 Issues

---

#### M1. Analytics — Frontend/Backend Data Format Mismatch

**Severity:** Medium (silently broken, fallback data always shows instead of real data)

**Location:**
- `frontend/src/lib/api/notifications.ts` — `MetricsResponse` type (lines 26-39)
- `frontend/src/routes/_app.analytics.market.tsx` — component (lines 40-53, 122-137)
- `frontend/src/routes/_app.analytics.skills.tsx` — component (lines 87-94)
- `backend/app/schemas/notification.py` — `MetricsResponse` Pydantic schema (lines 37-51)
- `backend/app/services/analytics.py` — `generate_analytics_metrics()` (lines 238-251)

**Root Cause:**

The backend's `MetricsResponse` schema returns data in object/dict formats, but the frontend TypeScript types expect tuple arrays:

| Field | Backend format (Pydantic) | Frontend type (TS) | Frontend usage |
|-------|--------------------------|--------------------|-----------------|
| `top_technologies` | `List[Dict[str, Any]]` → `[{"skill": "Python", "count": 5}]` | `Array<[string, number]>` → `[["Python", 5]]` | `r[0]` (name), `r[1]` (count %) |
| `salary_medians` | `Dict[str, float]` → `{"Google": 120000.0}` | `Array<[string, string]>` → `[["SF Bay Area", "$165k"]]` | `r[0]` (location), `r[1]` (salary) |
| `skill_gaps` | `List[Dict[str, Any]>` → `[{"skill": "K8s", "demand_frequency": 3, "impact_score": 30}]` | `string[]` → `["Kubernetes"]` | `{s}` (skill name rendered as string) |

**Impact:**

1. **`top_technologies`**: When the backend returns data (non-empty array of objects), the frontend's tuple-access `r[0]`/`r[1]` returns `undefined` — the list renders with blank names and "undefined%" counts.
2. **`salary_medians`**: When the backend returns a non-empty object, `.map()` will throw a `TypeError: salaryMedians.map is not a function` at runtime because JavaScript objects lack `.map()`. This would crash the Market Insights page.
3. **`skill_gaps`**: When the backend returns objects, `{s}` renders `[object Object]` in the DOM.

The hardcoded fallbacks in the components are intended as safety nets, but because non-empty backend data is truthy in JavaScript, the fallbacks are **never reached** when real data exists — the real (mis-formatted) data is used instead, producing broken output.

**Implementation Plan:**

**Step 1 — Fix frontend TypeScript types** (`frontend/src/lib/api/notifications.ts`, lines 26-39)

Update `MetricsResponse` to match the actual backend response shapes:

```typescript
export interface MetricsResponse {
  total_applications: number;
  interview_rate: number;
  avg_response_time_days: number;
  offer_rate: number;
  conversion_funnel: Array<[string, number]>;  // OK — backend returns list of dicts
  rejection_stages: Array<[string, number]>;   // OK — backend returns list of dicts
  skill_coverage: Array<{ skill: string; you: number; market: number }>;  // OK
  market_demand: Array<{ role: string; demand: number; postings: number; change: string }>;  // OK
  top_technologies: Array<{ skill: string; count: number }>;  // FIX: was Array<[string, number]>
  salary_medians: Record<string, number>;  // FIX: was Array<[string, string]>
  skill_gaps: Array<{ skill: string; demand_frequency: number; impact_score: number }>;  // FIX: was string[]
  generated_at: string;
}
```

Note: `conversion_funnel` and `rejection_stages` use `[string, number]` which happens to work because `Dict[str, Any]` with keys "stage" and "count" renders as `{stage: "...", count: N}` — objects without numeric indices, so this is also technically broken. Verify and fix similarly if needed.

**Step 2 — Fix market.tsx component** (`frontend/src/routes/_app.analytics.market.tsx`)

- Update `TechStat` interface to `{ skill: string; count: number }` and render `r.skill` and `r.count` instead of `r[0]` and `r[1]`.
- Change `salaryMedians` from array mapping to object iteration: convert `metrics?.salary_medians` (now `Record<string, number>`) to an array of `[location, formattedSalary]` entries for rendering.
- Update `SalaryStat` interface or remove it in favor of inline typing.
- Replace hardcoded fallback arrays with empty-array fallbacks (the format match makes the fallbacks correct if data simply isn't available).

**Step 3 — Fix skills.tsx component** (`frontend/src/routes/_app.analytics.skills.tsx`)

- Update the `skill_gaps` rendering: the backend provides `{skill, demand_frequency, impact_score}` objects. Change `{s}` to `{s.skill}` and use `s.demand_frequency` instead of `Math.random()`.

**Step 4 — Verify backend returns data in the correct shape**

Confirm that the backend's `generate_analytics_metrics()` returns objects with the expected keys:
- `top_technologies`: `[{"skill": "python", "count": 5}, ...]` — ✅ matches new frontend type
- `salary_medians`: `{"Google": 120000.0, ...}` — ✅ matches new frontend type (Record<string, number>)
- `skill_gaps`: `[{"skill": "kubernetes", "demand_frequency": 3, "impact_score": 30}, ...]` — ✅ matches new frontend type

**Step 5 — Add tests**

Write frontend component tests or at minimum manual verification:
1. Render market page with mocked API data matching backend format — verify no crashes, data displays correctly.
2. Render skills page with mocked API data — verify skill gaps display with real `demand_frequency` values.

**Effort:** 2-3 hours (frontend type and component updates).

---

#### M2. Math.random() Placeholder in skills.tsx

**Severity:** Low (visible bug — non-deterministic UI text)

**Location:** `frontend/src/routes/_app.analytics.skills.tsx`, line 91

```tsx
<span className="text-[11px] text-muted-foreground">
  Improves match on {Math.floor(Math.random() * 10 + 5)} jobs
</span>
```

**Root Cause:**

The "Improves match on N jobs" value is generated with `Math.random()` instead of using the actual `demand_frequency` field from the backend's `skill_gaps` data. This causes:
1. Non-deterministic text — refreshing the page shows different numbers.
2. Misleading data — the count doesn't reflect actual market demand frequency.

**Implementation Plan:**

**Step 1 — Replace Math.random() with real data**

After fixing M1 (data format mismatch), update the skill gaps rendering:

```tsx
{metrics?.skill_gaps?.map((s: SkillGapItem) => (
  <li key={s.skill} className="flex items-center justify-between px-4 py-3">
    <span className="font-semibold">{s.skill}</span>
    <span className="text-[11px] text-muted-foreground">
      Closing this gap improves match on {s.demand_frequency} jobs
    </span>
  </li>
))} || (
  // fallback hardcoded items
)
```

**Step 2 — Add SkillGapItem type** to the frontend types in `notifications.ts`:

```typescript
export interface SkillGapItem {
  skill: string;
  demand_frequency: number;
  impact_score: number;
}
```

**Effort:** 30 minutes.

---

### Low Severity — 3 Issues

---

#### L1. Top Match Queue Always Empty

**Severity:** Low (missing feature on landing page)

**Location:** `backend/app/api/stats.py`, lines 155-164

```python
def _get_top_match_queue(db: Session) -> List[TopMatchItem]:
    """..."""
    # For now, return an empty list.
    return []
```

**Root Cause:**

The function is a stub. It returns an empty list instead of querying for actual top job matches. The `GET /stats/landing` endpoint therefore always returns `top_match_queue: []`.

**Implementation Plan:**

**Step 1 — Implement the match queue query**

Replace the stub with a real database query. The function should:
1. Find jobs that match the current user's profile based on match score (leveraging the existing `calculate_match_score` from `app.services.matching_engine`).
2. Return the top 4 matches with `company`, `role`, `match_score`, and `status`.

However, `stats.py`'s `get_landing_stats` endpoint is not user-scoped (no `get_current_user` dependency). Implement one of two approaches:

**Option A (simple):** If the landing stats endpoint is meant to be org-level/anonymous (no user context), compute matches against a default or sample profile. This is limited value.

**Option B (correct):** Add `get_current_user` dependency to `get_landing_stats` and call `_get_top_match_queue(db, current_user)`. This matches how the jobs API `GET /jobs/top-matches` (jobs.py line 139) already works — it queries `calculate_match_score` and filters `score >= 30`.

Recommended: **Option B**, mirroring the existing `get_top_matches` implementation in `jobs.py`:

```python
def _get_top_match_queue(db: Session, user_id: uuid.UUID, limit: int = 4) -> List[TopMatchItem]:
    from app.models.profile import Profile
    from app.models.job import JobApplication
    from app.services.matching_engine import calculate_match_score

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        return []

    applied_job_ids = (
        db.query(JobApplication.job_id)
        .filter(JobApplication.user_id == user_id)
        .subquery()
    )

    candidate_jobs = (
        db.query(Job)
        .filter(Job.id.notin_(applied_job_ids))
        .order_by(Job.created_at.desc())
        .limit(50)
        .all()
    )

    scored = []
    for job in candidate_jobs:
        score_data = calculate_match_score(profile, job)
        if score_data["score"] >= 30:
            scored.append(TopMatchItem(
                company=job.company,
                role=job.title,
                match_score=score_data["score"],
                status="new",
            ))

    scored.sort(key=lambda x: x.match_score, reverse=True)
    return scored[:limit]
```

**Step 2 — Update `get_landing_stats` signature** to accept `current_user` and pass `user_id` to `_get_top_match_queue`.

**Step 3 — Update the frontend** if it consumes the landing stats API (check `frontend/src/lib/api/stats.ts`).

**Effort:** 3-4 hours.

---

#### L2. Orphaned notification.py Service File

**Severity:** Low (dead code, maintenance hazard)

**Location:**
- `backend/app/services/notification.py` — orphaned service with 6 functions
- `backend/app/services/__init__.py` — line 15 imports from it
- `backend/app/api/notifications.py` — has its own inline implementations
- `backend/app/services/notification_service.py` — active service used by Celery workers

**Root Cause:**

There are two notification service files:
1. `app/services/notification.py` — defines `create_notification`, `create_notifications_bulk`, `get_notifications`, `mark_as_read`, `mark_all_as_read`, `get_unread_count`, `create_job_alert_notification`, `create_application_update_notification`, `create_follow_up_reminder`, `create_system_event_notification`. It's imported in `__init__.py` but **never called** by any API route or service function.
2. `app/services/notification_service.py` — defines `send_notification_email`, `check_and_send_reminders`, `create_job_alert_notification`, `create_application_update_notification`, `create_system_event_notification`. Used by Celery `tasks.py`.

The `app/api/notifications.py` router has **inline** implementations of list, unread-count, mark-read, mark-all-read, and delete — it does NOT delegate to either service file.

This creates:
- **Code duplication**: `create_notification`, `create_job_alert_notification`, `create_application_update_notification`, `create_system_event_notification` exist in both service files with different signatures and behaviors.
- **Dead code**: `notification.py` is never called.
- **Confusion**: Two files with nearly identical names (`notification.py` vs `notification_service.py`).

**Implementation Plan:**

**Step 1 — Audit usage (confirm truly orphaned)**

Grep shows `app.services.notification` is only imported in `__init__.py`. No other file imports it. Confirmed dead code.

**Step 2 — Remove the orphaned service**

Delete `backend/app/services/notification.py` and remove the import block from `__init__.py` (lines 15-26). The functions it provided (`create_notification`, etc.) are either:
- Inline-implemented in `app/api/notifications.py` (list, unread-count, mark-read, mark-all-read, delete)
- Duplicated in `notification_service.py` (create_job_alert_notification, create_application_update_notification, create_system_event_notification)

**Step 3 — Consolidate (optional but recommended)**

Migrate any remaining inline implementations in `app/api/notifications.py` to use functions from `notification_service.py` (or keep inline if they're trivial). The `create_notification` helper in `notification.py` could be moved to `notification_service.py` if needed by the API router.

**Step 4 — Clean up `__all__`** in `__init__.py` to remove the deleted exports.

**Effort:** 2-3 hours (including testing that nothing breaks).

---

#### L3. Help Page Dead Links

**Severity:** Low (broken UI — clicking links does nothing or 404s)

**Location:** `frontend/src/routes/help.tsx`, lines 14, 20, 26, 32, 38, 44

```typescript
href: "/docs/agent-install",
href: "/docs/gemini-key",
href: "/docs/import-jobs",
href: "/docs/resume-profile",
href: "/docs/match-scores",
href: "/docs/track-applications",
```

**Root Cause:**

The help page renders 6 article cards with `href` values pointing to `/docs/*` routes, but no corresponding route files exist in `frontend/src/routes/` (verified: no files with `*docs*` in the routes directory). Clicking these links via `<Link to={article.href}>` will result in a TanStack Router "not found" error or a blank page.

**Implementation Plan:**

**Step 1 — Decide on approach.** Two options:

**Option A (Minimal — redirect to README):** Point the links to external documentation (e.g., the project's README or GitHub wiki). Update `href` values to `#` or a documentation URL.

**Option B (Full — create doc routes):** Create lightweight documentation pages under `frontend/src/routes/docs/` with the same file naming convention as the existing route structure (e.g., `_docs.agent-install.tsx`, etc.). Each page would be a simple content page using the existing `MarketingShell` component.

**Step 2 — For Option A (recommended as MVP):** Update `help.tsx` to wrap card clicks in a handler that opens a GitHub docs URL or displays a toast:

```tsx
const handleDocsClick = (docId: string) => {
  // Fallback: link to GitHub wiki or README
  window.open(
    `https://github.com/sirafit/sirafit/blob/main/docs/SiraFit%20Documentation.docx`,
    "_blank"
  );
};
```

Or, if documentation pages will be created:
Replace `<Link to={article.href}>` with `<Link to={article.href}>` and create the actual route files.

**Step 3 — Create documentation route files** (if choosing Option B). Create 6 minimal route files:
- `frontend/src/routes/docs/agent-install.tsx`
- `frontend/src/routes/docs/gemini-key.tsx`
- `frontend/src/routes/docs/import-jobs.tsx`
- `frontend/src/routes/docs/resume-profile.tsx`
- `frontend/src/routes/docs/match-scores.tsx`
- `frontend/src/routes/docs/track-applications.tsx`

Each should be a simple content page with a heading, description, and relevant steps.

**Step 4 — Verify routing.** Ensure the TanStack Router config picks up the new routes (check `frontend/src/routeTree.gen.ts` or run the route generation command).

**Effort:** 1-2 hours for Option A; 4-6 hours for Option B.

---

## Implementation Priority

| Priority | Issue | Why |
|----------|-------|-----|
| **P1** | M1 — Analytics data format mismatch | Causes runtime crash (`TypeError: .map is not a function`) on salary_medians; silently shows wrong/empty data on top_technologies and skill_gaps. Affects both market and skills insights pages. |
| **P2** | M2 — Math.random() placeholder | Produces non-deterministic, misleading UI data. Simple fix once M1 is done. |
| **P3** | L1 — Top match queue empty | Missing landing page feature; requires DB query implementation. |
| **P4** | L3 — Help page dead links | Broken links; affects UX but not core functionality. |
| **P5** | L2 — Orphaned notification.py | Dead code; maintenance hazard but no runtime impact. |

## Notes

- All **High Severity** issues have been fixed in the current codebase. The fixes appear comprehensive: real endpoints exist, frontend properly calls them, and no mocks remain.
- The `RefreshToken` model referenced in `users.py` line 184 is used in the password change flow but I did not verify its definition in the models. It's imported from `app.models.job` at line 123. This is a pre-existing pattern and not part of the reported issues.
- The `AnalyticsSnapshot` model in `backend/app/models/analytics.py` was used by the analytics service but not examined in detail — it's not part of any reported issue.
- The `docs` directory at the project root contains `.docx` and `.txt` files but no web-routable documentation that would satisfy the `/docs/*` links.
