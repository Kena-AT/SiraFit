# SiraFit - Complete Platform Documentation

> High-density job search automation, deterministic match scoring, and structured resume tailoring.

---

## Table of Contents

1. [What is SiraFit?](#1-what-is-sirafit)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Backend Architecture](#4-backend-architecture)
5. [Frontend Architecture](#5-frontend-architecture)
6. [Database Schema](#6-database-schema)
7. [Core Features and How They are Implemented](#7-core-features-and-how-they-are-implemented)
8. [Infrastructure Layer](#8-infrastructure-layer)
9. [End-to-End User Scenario](#9-end-to-end-user-scenario)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Known Limitations &amp; Roadmap](#11-known-limitations--roadmap)

---

## 1. What is SiraFit?

**SiraFit** is a high-density job search automation platform that helps candidates:

- **Import** jobs from URLs or pasted descriptions across 9 ATS platforms (LinkedIn, Indeed, Glassdoor, ZipRecruiter, SimplyHired, Lever, Greenhouse, Ashby, Workday)
- **Score** their fit against each role using a deterministic matching engine (zero AI required for scoring)
- **Analyze** jobs with AI across 7 providers (Gemini, OpenRouter, Anthropic, OpenAI, Grok, Mistral, NVIDIA)
- **Tailor** resumes and cover letters with structured AI output
- **Track** applications through a 10-stage status machine with timeline events, notes, and contacts
- **Get notified** about follow-up reminders, status changes, and new job alerts

The platform uses a **local-first** approach — every user can store their own AI provider keys (encrypted), so the platform works whether or not a server-side key is configured.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Browser)                       │
│  React 19 + TypeScript + TanStack Router + TanStack Query       │
│  SSR via TanStack Start                                         │
└────────────────────┬────────────────────────────────────────────┘
                     │ /api/v1/* (REST + JWT)
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI + Python 3.12)              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐      │
│  │   Routers   │  │  Services   │  │  AI Dispatchers  │      │
│  │  /auth/*    │  │  (business  │  │  7 providers     │      │
│  │  /jobs/*    │──│  logic +    │──│  + keyword       │      │
│  │  /apps/*    │  │  DB ORM)    │  │  fallback        │      │
│  │  /resumes/* │  │             │  │                  │      │
│  └─────┬───────┘  └──────┬──────┘  └──────────────────┘      │
│        │                 │                                     │
│  ┌─────▼─────────────────▼───────────────────────────┐        │
│  │     SQLAlchemy ORM (PostgreSQL / SQLite)          │        │
│  │     Alembic migrations                            │        │
│  └────────────┬──────────────────────────────────────┘        │
└───────────────┼─────────────────────────────────────────────────┘
                │
   ┌────────────┼────────────────┐
   │            │                │
   ▼            ▼                ▼
┌────────┐  ┌─────────┐  ┌────────────────┐
│ Redis  │  │ Celery  │  │ SMTP (Brevo)   │
│ Cache  │  │ Workers │  │ Email delivery │
│ Rate   │  │ + DLQ   │  │                │
│ Limits │  │         │  │                │
└────────┘  └────┬────┘  └────────────────┘
                │
                ▼
         ┌──────────────────────────┐
         │  Background Tasks:        │
         │  • Resume generation     │
         │  • PDF rendering         │
         │  • Cover-letter PDF      │
         │  • Batch processing      │
         │  • Reminder dispatch     │
         └──────────────────────────┘
```

---

## 3. Technology Stack

### Backend

| Component           | Technology                                      |
| ------------------- | ----------------------------------------------- |
| Framework           | FastAPI 0.110+                                  |
| ORM                 | SQLAlchemy 2.0                                  |
| Validation          | Pydantic v2                                     |
| Database            | PostgreSQL 15 (prod) / SQLite (dev)             |
| Migrations          | Alembic                                         |
| Cache + Rate Limits | Redis 7                                         |
| Background workers  | Celery 5                                        |
| Email               | Brevo SMTP (STARTTLS)                           |
| Auth                | JWT (HS256) + refresh tokens                    |
| AI                  | 7 providers via OpenAI-compatible + native SDKs |
| Packaging           | `pyproject.toml` + `requirements.txt`       |
| Docker              | `Dockerfile`, `Dockerfile.celery`           |
| Deployment          | Render (`render.yaml`)                        |

### Frontend

| Component     | Technology                              |
| ------------- | --------------------------------------- |
| Framework     | React 19                                |
| Routing       | TanStack Router (type-safe, file-based) |
| Data fetching | TanStack Query                          |
| Build         | Vite                                    |
| SSR           | TanStack Start                          |
| Styling       | Tailwind CSS 4 + shadcn/ui              |
| Forms         | react-hook-form                         |
| State         | Zustand (where used)                    |
| Language      | TypeScript                              |

### Infrastructure

- **Redis** — caching, rate limiting, Celery broker
- **PostgreSQL** — primary data store
- **Celery** — distributed task queue with 4 specialized queues

---

## 4. Backend Architecture

### Layered Structure

```
backend/app/
├── api/              # FastAPI routers (HTTP layer)
│   ├── auth.py
│   ├── users.py
│   ├── profiles.py
│   ├── jobs.py
│   ├── applications.py
│   ├── resumes.py
│   ├── cover_letters.py
│   ├── batch.py
│   ├── notifications.py
│   ├── analytics.py
│   ├── dashboard.py
│   ├── settings.py
│   ├── stats.py
│   └── router.py     # Aggregates all routes under /api/v1
│
├── core/              # Cross-cutting concerns
│   ├── config.py      # Pydantic Settings (env loading)
│   ├── database.py    # SQLAlchemy engine + SessionLocal
│   ├── security.py    # JWT + bcrypt + Fernet encryption
│   ├── redis_client.py # Lazy Redis connection (ping + fallback)
│   ├── cache.py       # Redis-backed cache with in-memory fallback
│   ├── rate_limiting.py  # Sliding-window limiter (Redis primary, in-memory fallback)
│   ├── middleware.py  # Rate-limit headers + body stream replay
│   ├── logging.py     # structlog config
│   ├── metrics.py     # Prometheus counters
│   └── health.py      # Liveness/readiness endpoints
│
├── models/            # SQLAlchemy ORM models
│   ├── user.py           # User, UserPreference, RefreshToken, DeviceSession
│   ├── profile.py        # Profile + Experience, Education, Skill, Project, Certification
│   ├── job.py            # Job, JobApplication, JobAnalysis, JobImport, Resume, ResumeVersion
│   ├── cover_letter.py   # CoverLetter
│   ├── notification.py   # Notification
│   ├── analytics.py      # AnalyticsSnapshot
│   ├── batch.py          # BatchJob
│   └── score.py          # JobMatchScore
│
├── schemas/          # Pydantic request/response models
│
├── services/          # Business logic
│   ├── ai.py                  # 7-provider AI dispatcher + keyword fallback
│   ├── resume_generation.py   # Tailored resume builder + JSON parsing + ATS scoring
│   ├── cover_letter_generation.py
│   ├── job_analysis.py        # Orchestrates AI vs keyword fallback for jobs
│   ├── job_import.py          # URL/description parsing + normalization + dedup
│   ├── application.py         # Status state machine, timeline events, notes, contacts
│   ├── matching_engine.py     # Deterministic scoring (skills/title/salary heuristics)
│   ├── scoring.py             # AI match scoring (calls AI providers)
│   ├── notification.py        # In-app notification logic
│   ├── notification_service.py # Email dispatch + reminder cron-like routine
│   ├── pdf_rendering.py       # HTML → PDF via weasyprint
│   ├── resume_export.py       # Generate HTML for resumes
│   ├── batch.py               # Batch job orchestration
│   ├── batch_operations.py    # Item handlers (analyze/score/tag/archive)
│   ├── email.py               # SMTP wrapper (Brevo, with graceful fallback)
│   ├── agent_api.py           # Local-agent connectivity check for the landing page
│   └── analytics.py           # Metrics computation + snapshot persistence
│
├── worker/            # Celery worker definitions
│   ├── celery_app.py          # Celery factory + 4 queue routes + DLQ
│   └── tasks.py               # generate_resume, render_*, batch, notifications
│
└── main.py            # FastAPI app instance + middleware wiring + Alembic auto-upgrade
```

### Key Architectural Decisions

1. **Single backend, versioned REST API** — `/api/v1/*`. All routers aggregate under a single `api_router` in `router.py`.
2. **Lazy Redis** — `get_redis_client()` is called fresh each request and memoized after the first successful ping. If Redis is unreachable (development), it returns `None` and the caller falls back to in-memory.
3. **Background jobs with graceful degradation** — Every Celery `enqueue_*` helper wraps the dispatch in a `try/except`. If Redis/Celery is unavailable, it falls back to a threading-based synchronous run.
4. **Dead-letter queue** — All Celery tasks inherit a base `BaseRetryTask` with `max_retries=3`. After exhaustion, the task is re-dispatched to a DLQ for inspection via `send_task("app.worker.tasks.handle_dead_letter", ...)`.
5. **Encrypted per-user AI keys** — Users can paste provider API keys in `/settings/ai`. Keys are encrypted with Fernet (`DATA_ENCRYPTION_KEY` env or `SECRET_KEY` fallback) before persistence, and decrypted on each AI call.
6. **Status machine** — Application status transitions are enforced by `app.services.application.validate_transition()` which uses a static adjacency map; only legal status moves are allowed.

---

## 5. Frontend Architecture

### Folder Layout (key folders)

```
frontend/src/
├── routes/             # File-based routes, generated by TanStack Router
│   ├── __root.tsx
│   ├── _app/           # Auth-protected routes (layout group)
│   │   ├── dashboard.tsx
│   │   ├── jobs/              # list, $jobId, history, import
│   │   ├── applications/      # list, $id, followups, timeline
│   │   ├── resumes/           # list, $id, $id/editor, builder, profiles, profile-editor
│   │   ├── cover-letters/     # list, builder
│   │   ├── batch/             # list, $id
│   │   ├── analytics/         # index, market, skills
│   │   ├── settings/          # index, ai, notifications, privacy, resume
│   │   ├── notifications.tsx
│   │   ├── match.tsx          # /match
│   │   └── ranking.tsx        # /ranking
│   ├── docs/           # 6 in-product doc pages
│   ├── login.tsx, register.tsx, forgot-password.tsx, reset-password.tsx,
│   ├── verify-email.tsx, logout.tsx
│   ├── help.tsx, terms.tsx, privacy.tsx
│   └── index.tsx       # landing page
│
├── lib/
│   ├── api/            # Typed API clients
│   │   ├── client.ts            # apiFetch wrapper (JWT injection, 401 refresh)
│   │   ├── auth.ts
│   │   ├── profiles.ts
│   │   ├── jobs.ts              # jobs/import/analysis/match-scores
│   │   ├── applications.ts      # CRUD + events + notes + contacts + timelines + followups
│   │   ├── resumes.ts
│   │   ├── cover-letters.ts
│   │   ├── batch.ts
│   │   ├── notifications.ts
│   │   ├── analytics.ts
│   │   ├── dashboard.ts
│   │   ├── stats.ts             # landing stats
│   │   ├── headers.ts           # X-AI-API-Key / X-AI-Provider / X-AI-Model augmentation
│   │   └── users.ts
│   ├── validation/
│   ├── error-capture.ts / error-page.ts
│   └── mock-jobs.ts (dev)
│
├── components/
│   ├── ui/             # shadcn primitives (button, card, dialog, etc.)
│   ├── custom/         # SiraFit-specific wrappers (Input, Textarea, ValidationDisplay)
│   └── sirafit/        # Feature components
│
├── types/              # Shared TS types (job.ts, resume.ts, cover-letter.ts, profile.ts)
│
├── hooks/
│   └── use-mobile.tsx
│
├── router.tsx          # TanStack Router instance
├── start.ts            # SSR entry
├── server.ts           # SSR server entry
└── routeTree.gen.ts    # AUTO-GENERATED by TanStack Router plugin
```

### Routing

TanStack Router generates `routeTree.gen.ts` from files in `routes/`. The pattern `_app.<segment>.tsx` is a child of the `_app` layout (auth-gated). The router has automatic type inference — every link, navigate, and prefetch is type-safe.

### Data Fetching Strategy

- **Server state**: TanStack Query (`staleTime: 0` so refetches happen immediately after mutations).
- **Mutations**: Always `retry: false`, but auto-refetch all dependent queries on success.
- **JWT lifecycle**: `apiFetch()` in `client.ts` transparently attaches `Authorization: Bearer <token>` and on 401 attempts a refresh-once-then-retry.

### SSR

TanStack Start provides SSR. The frontend can pre-render pages server-side and stream a hydration payload to the client.

---

## 6. Database Schema

The data model has 25+ tables. Below are the most important relationships:

```
                            ┌─────────────┐
                            │   users     │
                            └──────┬──────┘
                                   │ 1:1
                                   ▼
        ┌────────────────────┐  ┌──────────────┐   1:N   ┌──────────────────┐
        │ user_preferences   │  │   profiles   │──────────│ experiences/     │
        │ (AI keys enum)     │  │              │          │ educations/      │
        └────────────────────┘  └──────────────┘          │ skills/projects/ │
                                   ▲                     │ certifications   │
                                   │                     └──────────────────┘
                                   │
        ┌────────────────────┐    │ 1:N     ┌─────────────────────────────────┐
        │   jobs             │◄───┘         │  job_applications               │
        │   (external_id     │◄─────────────│  (user_id, job_id, status,      │
        │    unique)         │      1/N     │   score, follow_up_at)          │
        └────────┬───────────┘              └──────┬──────────────────────────┘
                 │                                  │
                 │ 1:1                              │ 1:N
                 ▼                                  ▼
        ┌────────────────────┐         ┌──────────────────────────────────────┐
        │  job_analysis      │         │  application_events  (timeline)     │
        │  (AI verdict +     │         │  application_notes   (user-editable)│
        │   pros/cons/       │         │  application_contacts (recruiter)   │
        │   skills_gap)      │         │  job_match_scores     (deterministic)│
        └────────────────────┘         └──────────────────────────────────────┘

        ┌────────────────────┐         ┌──────────────────────────────────────┐
        │  resumes           │         │  cover_letters                      │
        │   1:N resume_      │         │  (body, template, tone, status)     │
        │   versions         │         └──────────────────────────────────────┘
        └────────────────────┘
        ┌────────────────────┐         ┌──────────────────────────────────────┐
        │  notifications     │         │  analytics_snapshots (daily rollup) │
        │  (kind, status,    │         └──────────────────────────────────────┘
        │   read_at)         │         ┌──────────────────────────────────────┐
        └────────────────────┘         │  batch_jobs + items                 │
        ┌────────────────────┐         └──────────────────────────────────────┘
        │  refresh_tokens    │         ┌──────────────────────────────────────┐
        │  device_sessions   │         │  job_imports (URL/desc/CSV)         │
        │  audit_logs        │         └──────────────────────────────────────┘
        └────────────────────┘
```

Indexes of note:

- `ix_job_applications_user_status` (Kanban-speed)
- `ix_job_applications_user_job` UNIQUE (one application per job per user)
- `ix_jobs_title/company` (LIKE search via trigram-style ILIKE)
- `application_events_(user_id, application_id)` composite
- `ix_resumes_user_id` (Sprint 9)

---

## 7. Core Features and How They are Implemented

### 7.1 Authentication

- **JWT** signed with HS256 using `SECRET_KEY`. Short-lived access tokens (15 min default), long-lived refresh tokens (7 days).
- Refresh tokens stored in `refresh_tokens` table (hash only, never the raw token).
- **Devices** tracked in `device_sessions`. Users can view/revoke active sessions.
- **Email verification** via signed token in `/verify-email?token=...`.
- **Password reset** mirrors the same pattern (signed token + 24-hour exp).
- **Logout** revokes the refresh token (server-side).

### 7.2 Profile & Skills

- The `Profile` model holds top-level fields; inline nested arrays (`experiences`, `educations`, `skills`, `projects`, `certifications`) are persisted on every `PUT /profiles/me` request as a **full-replacement** strategy (no PATCH; saves editing complexity).
- Alembic migration `4f0218ad2e0c_initial_migration.py` plus `add_profile_tables.py` covers this.

### 7.3 Job Import

- `app/services/job_import.py` exposes three parser functions: `parse_job_from_url`, `parse_job_from_description`, future `parse_job_csv`.
- URL parsing detects 9 platforms and extracts their canonical ID regex; description parsing does title-keyword detection + salary-number extraction + tech-tag extraction.
- **Deduplication** (`check_duplicate`) uses `WHERE title ILIKE ? AND company ILIKE ? AND location ILIKE ?` with `.limit(1).first()` — indexed lookup, not a full scan.
- After import, the job is saved with `external_id = uuid4()` (idempotency happens via dedup).

### 7.4 Job Analysis (AI)

- Endpoint: `POST /jobs/{id}/analyze`.
- Flow:
  1. Find-or-create a `JobAnalysis` row with `status="processing"`.
  2. Schedule `run_job_analysis` in `BackgroundTasks` (FastAPI).
  3. The background task resolves API keys with priority: **client header → user-encrypted key → server env**. Key resolution uses `config.PROVIDER_KEY_FIELDS` dict.
  4. Calls the relevant AI provider (or `keyword_fallback` if none).
  5. Persists `score`, `summary`, `pros`, `cons`, `skills_gap`, `key_requirements`, `seniority`.

### 7.5 Match Scoring (Deterministic + AI Hybrid)

- **Deterministic** path: `services/matching_engine.calculate_match_score(profile, job)` produces a 0–100 score via weighted overlap of skills, title keywords, and salary band. This is the **SOTA** path used for the top-matches ranking and is computed locally.
- **AI** path: `services/scoring.analyze_match_score(profile, job, ...)` calls an LLM. Used opportunistically on `/apply`-style flows.
- **Cache layer**: `/jobs/{id}/match-score/cached` returns just the stored score (read-only), `/jobs/{id}/match-score` calculates and persists.

### 7.6 Resume Generation

- Endpoint: `POST /resumes/{id}/generate`.
- Flow:
  1. Create a `ResumeVersion` row (`status=pending`).
  2. **Dispatch to Celery** `generate_resume_task` with user/profile/job/template args.
  3. Inside the task: AI returns JSON conforming to `TailoredResume` Pydantic schema. **Auto-clamping** of array lengths (max 5 bullets per role, max 30 skills, etc.).
  4. Validate via `validate_resume_json` + `_calculate_ats_score(job)`. If `is_valid=False`, status flips to `"failed"`.
  5. Persist `version.content` (JSON), `version.score` (ATS score 0–100), `version.tailoring_notes` (issues if invalid).

### 7.7 Resume PDF Export

- Endpoint: `GET /resumes/{id}/versions/{version_id}/export`.
- Path A (sync): Render HTML via `services/resume_export.export_resume_pdf()` → `weasyprint` → bytes → stream.
- Path B (async): `query=async_export=true` flips `status="processing"` and dispatches `render_resume_pdf_task`. Returns 202 with a poll URL.

### 7.8 Cover Letters

- Three templates (`classic`, `modern`, `compact`) and three tones (`matching`, `conversational`, `formal`).
- Same Celery-backed async export flow as resumes.
- Regeneration: the legacy path creates a new cover letter on every regen; the modern path updates an existing one (line `[{letter_id}/generate]`).

### 7.9 Applications & Status Tracking (Sprint 9)

- **Deterministic status machine** with 10 statuses (`saved → preparing → applied → screening → interview → final_round → offer`), plus side states (`rejected`, `withdrawn`, `archived`).
- Adjacency map (`VALID_NEXT`) forbids illegal transitions (e.g. `interview → saved` requires a re-open path through `withdrawn`).
- Every transition writes an `ApplicationEvent` (`event_type="status_change"`) plus an `AuditLog` row.
- Notes and Contacts share the same `application_id` FK and cascade-delete with the parent application.
- **Follow-ups** stored on the parent (`JobApplication.follow_up_at`, `follow_up_note`). The list endpoint `GET /applications/followups` is registered **before** `/{app_id}` so FastAPI route matching doesn't capture `"followups"` as a UUID.

### 7.10 Notifications

- In-app `Notification` rows; user-facing UI polls every 5 s.
- **Email reminders** dispatched by `check_and_send_reminders()` (Celery schedule`check_reminders_task`). Uses body-pattern matching (`body LIKE "application for {title} at%"`) to prevent duplicate reminders within 24 h.
- User preference toggles (`email_notifications`) in `UserPreference`.

### 7.11 Analytics

- `MetricsResponse` carries: conversion funnel, rejection stages, skill coverage, market demand, top technologies, salary medians, skill gaps.
- Computed via `services/analytics.generate_analytics_metrics(db, user_id)`.
- Cached at the API level (`cache.py`) for 60 s per user.

### 7.12 Settings / AI Keys

- `PUT /users/me/preferences/ai-keys` accepts 7 keys (`openrouter_key`, `gemini_key`, `anthropic_key`, `openai_key`, `grok_key`, `mistral_key`, `nvidia_key`). Encrypted via Fernet before storage.
- On every AI call the key lookup chain is client-header → user-encrypted → server-env.

### 7.13 Batch Operations

- One `BatchJob` row + N items (one per action target).
- Actions: `analyze`, `score`, `tag`, `archive`. Each item handler runs in the `process_batch_task` Celery worker with its own retries.
- Frontend polls `/batch/{id}` for progress.

### 7.14 Rate Limiting

- Sliding-window token bucket per `user-id` or `client-ip`.
- Limits defined in `RATE_LIMITS`. Specific routes (`/auth/login`) have stricter limits.
- **Redis-backed when available**, in-memory fallback otherwise.
- Disabled in `testing`/`development` environments to keep dev frictionless.
- Returns 429 with `Retry-After` and `X-RateLimit-*` headers.

### 7.15 Pagination, Filtering, Sorting

- All list endpoints accept `skip`, `limit`, optional filters (e.g. `min_salary`, `source`), and `sort_by`, `sort_order`. The constructed query uses `getattr(Job, sort_by, ...)` to avoid SQL injection.
- Jobs supports name/comma-tag filtering with `cast(tags as String) LIKE '%"tag"%'` — works on both SQLite (text JSON) and PostgreSQL (JSONB cast).

---

## 8. Infrastructure Layer

### Redis

- Stores: cache (`cache.py`), rate-limit counters (`rate_limiting.py`), Celery broker, Celery result backend.
- Lazy probe (2 s `socket_connect_timeout`, `socket_timeout`). On failure the entire app continues with in-memory fallbacks.

### Celery

- 4 routes:
  - `resume_generation` queue
  - `pdf_rendering` queue
  - `batch_processing` queue
  - `notifications` queue
  - `sirafit_dlq` for permanently failed tasks
- `worker_prefetch_multiplier=1` to avoid monopolizing workers.
- `task_acks_late=True` + `task_reject_on_worker_lost=True` for durability.

### Email (SMTP)

- Brevo SMTP via STARTTLS, port 587.
- Graceful no-op when SMTP not configured (no exceptions thrown in local dev).
- All email templates inlined in `email.py` (no template files).

### Logging

- `structlog` carries structured fields (`"event": "email_failed", "to": ..., "error": ...`).
- Standard logging in core modules.
- All Celery tasks log `extra={...}` for structured export.

### Auditing

- Every status change, login, password change, profile update, and AI generation writes an `AuditLog` row.
- Surfaces in `/dashboard` and admin views.

---

## 9. End-to-End User Scenario

Below is the full journey of a user named **Maya** who has just signed up for SiraFit.

### 9.1 Onboarding (Day 1)

Maya visits **sirafit.com**. The landing page (`/`) calls `GET /stats/landing` and shows:

- "12,438 jobs indexed in the last 24 hours"
- A "Top Match Queue" — empty (anonymous user).

She clicks **Sign Up**:

1. `POST /auth/register` — server creates the `User`, `UserProfile`, sends a verification email via Brevo.
2. She verifies her email at `/verify-email?token=...` → server marks `is_verified=true`.
3. She's redirected to **/settings/ai** where she pastes her **OpenRouter key**. Server encrypts it with Fernet and stores it in `UserPreference.encrypted_openrouter_key`.

She opens **/resumes/profile-editor** and fills out her profile:

- 2 experiences, 1 education, 12 skills, 1 project
- The PUT request replaces the entire nested structure atomically.

### 9.2 First Import (Day 1)

Maya finds a LinkedIn job for "Staff Engineer at Anthropic":

1. She opens **/jobs/import**, pastes the LinkedIn URL.
2. `POST /jobs/import` → `parse_job_from_url("linkedin", "https://linkedin.com/jobs/view/12345")` extracts the ID `12345`, company hint "LinkedIn", title by reverse-walking path segments.
3. Server normalizes (`"Staff Engineer"`), checks dedup (no match), saves with `external_id="12345"` and `is_archived=false`.
4. UI shows the imported job with a skeleton card.

She pastes 4 more jobs from Greenhouse and Lever into the bulk description box:

- `parse_job_from_description` runs for each, tags extracted from `SKILL_KEYWORDS`, regex-pulled salary range, title detection via first-line keyword.
- Two are flagged as duplicates (same company + title) and skipped with errors listed in `process_import.errors`.

### 9.3 Job Analysis (Day 1)

On the new Anthropic job, Maya clicks **Analyze**. The frontend:

1. `POST /jobs/{id}/analyze { force_refresh: false }`
   - Server creates `JobAnalysis` row, returns `status="processing"`. The frontend immediately starts polling `/jobs/{id}/analysis`.
2. Background task `run_job_analysis`:
   - Looks up encrypted OpenRouter key, calls the model.
   - Returns structured JSON → parsed into `AnalysisOutput(score=87, summary="…", pros=[…], cons=[…], skills_gap=["kubernetes"], seniority="Staff")`.
3. The polling resolves with full pros/cons and an ATS-style summary.

Maya clicks **Match Score** → `GET /jobs/{id}/match-score`

- `calculate_match_score(profile, job)` returns 92.
- Stored in `job_match_scores`. Her dashboard now shows 87 (AI) and 92 (deterministic).

### 9.4 Resume Tailoring (Day 2)

Maya clicks **Generate Tailored Resume** on the Anthropic job.

1. Frontend calls `POST /resumes/{resume_id}/generate { job_id, template: "technical" }`.
2. Backend creates a new `ResumeVersion` row with `status="pending"`, dispatches `generate_resume_task` to Celery.
3. Worker calls OpenRouter, returns JSON validated against `TailoredResume`. ATS score: 84 (good code, skills match).
4. Maya polls `/resumes/{resume_id}/versions` — sees status flip from `pending → processing → completed`.

She clicks **Export PDF** → the page supports sync (immediate) or async. She picks async → status flips to processing → workers render `resume-<uuid>.pdf` with `weasyprint` → path written back to `resume.pdf_url`.

### 9.5 Applying & Tracking (Day 2)

She clicks **Apply**:

1. Frontend: `POST /applications { job_id, status: "preparing" }` → server creates `JobApplication`, computes initial `score=92`, writes `AuditLog` and an `ApplicationEvent (event_type="application_created")`.

Two days later she submits the application:

1. `POST /applications/{app_id}/status { to_status: "applied" }` — the status machine accepts this transition and writes an event.
2. She adds the Anthropic recruiter's email via `POST /applications/{app_id}/contacts`.
3. She pins a note: "Submitted via referrals portal. Following up next Tuesday." → `POST /applications/{app_id}/notes` → the note sits in `application_notes` and surfaces at the top of the application detail page because `pinned=true`.

A week later she sets a follow-up:

1. `PUT /applications/{app_id}/followup { follow_up_at: "2026-08-22T14:00Z", note: "Email recruiter if no reply" }`.

### 9.6 Reminders Fire (Day 14)

The Celery schedule runs `check_reminders_task` daily at 09:00 UTC.

1. Worker queries `job_applications WHERE follow_up_at BETWEEN now() AND now() + 24h AND status NOT IN ('offer','rejected',…)`.
2. For each, a body-pattern check (`Notification.body LIKE "application for %{title} at%"`) confirms no duplicate.
3. A new `Notification(kind="reminder")` is created, an email is sent via Brevo, and Maya sees a bell badge in the navbar.

### 9.7 Interview Round (Day 18)

Maya updates her status to `screening` after passing the recruiter screen.

1. Frontend optimistically updates the kanban; server writes `ApplicationEvent(event_type="status_transition", from_status="screening", to_status="interview")`.
2. She reorders her notes to surface the interview prep question at the top by pinning it.
3. She adds the hiring manager as a contact role=`hiring_manager`.

Two weeks later — final round:

- `POST /applications/{app_id}/status { to_status: "final_round" }` (valid transition from `interview`).
- Dashboard updates in real time via the global timeline endpoint `/applications/timeline`.

### 9.8 Offer (Day 28)

She gets the offer! `POST /status { to_status: "offer" }` → her dashboard's conversion funnel "applied → offer" stat ticks up by 1. Her analytics snapshot (computed lazily on `/analytics/metrics`) shows her `offer_rate = 33%` over the last 30 days.

### 9.9 Analytics Snapshot (Day 30)

She clicks **Create Snapshot** on `/analytics`:

1. `POST /analytics/snapshots` persists the current metrics; the cache is invalidated.
2. Future `/analytics/metrics` calls recompute from scratch (the cached path was 60 s old).

### 9.10 Batch Tracking v2 (Day 35)

Now comfortable, Maya uses **/batch** to score 50 jobs at once:

1. `POST /batch { action: "score", job_ids: [...] }`.
2. Server enqueues `process_batch_job` with item handlers that call the deterministic matcher for each (cheap, no AI needed).
3. She watches progress in `/batch/{id}`.

### 9.11 Logout & Sessions

Before logging out she visits **/settings** → sees 2 active devices (laptop + phone). She kills the phone session with `DELETE /users/me/devices/{device_id}`.

`POST /auth/logout` revokes her refresh token.

---

## 10. Deployment Architecture

- **Production**: Render with `render.yaml` defining two services:
  - Web: `Dockerfile` (FastAPI + Uvicorn)
  - Worker: `Dockerfile.celery` (Celery worker)
- **Backing services**: Managed Redis + Managed PostgreSQL.
- **CI/CD**: GitHub Actions (test suite + Docker build + render deploy hook).
- **Migrations**: `alembic upgrade head` runs on API container start (`main.py` calls `command.upgrade(...)` in the lifespan handler).

---

## 11. Known Limitations & Roadmap

### Currently Implemented

- Email/password auth with JWT + refresh
- 7 AI providers with auto-key-resolution
- Deterministic + AI hybrid matching
- Async resume/cover-letter PDF rendering
- 5 resume templates, 3 cover-letter templates
- Full Sprint 9 application tracking (status machine, events, notes, contacts, follow-ups)
- Batch processing with retries + DLQ
- Per-user encrypted AI key storage
- Multi-device session management

### Known Limitations

1. **CSV import** is referenced in the enum (`source_type` includes `"csv"`) but not implemented.
2. **Real-time notifications** are polled (5 s) — no WebSocket/SSE.
3. **2FA / OAuth** not implemented.
4. **Webhook ingestion** from Greenhouse/Lever/Workday not implemented (only URL parsing).
5. **Calendar sync** for interviews not implemented.
6. **Application search** lacks full-text search (currently pagination + per-field filters).
7. **Resume scoring breakdown UI** exists in the data model but the chrome frontend only shows the top-line score.

### Roadmap

- CSV import (`parse_job_csv`)
- Real-time notifications via SSE
- LinkedIn/Google/GitHub OAuth
- Webhook ingress endpoint for ATS platforms
- Calendar integrations (Google, Outlook)
- Full-text search (`PG_TRGM` extensions)
- Insights page showing where applications stall
- Multi-language support

---

## Appendix A — File Layout Quick Reference

### Backend API Endpoints

| Path                                           | Methods        | Description             |
| ---------------------------------------------- | -------------- | ----------------------- |
| `/api/v1/auth/register`                      | POST           | Register new user       |
| `/api/v1/auth/login`                         | POST           | Login (returns JWT)     |
| `/api/v1/auth/refresh-token`                 | POST           | Refresh JWT             |
| `/api/v1/auth/logout`                        | POST           | Logout (revoke refresh) |
| `/api/v1/auth/verify-email`                  | POST           | Verify email            |
| `/api/v1/auth/resend-verification`           | POST           | Resend verification     |
| `/api/v1/auth/forgot-password`               | POST           | Forgot flow             |
| `/api/v1/auth/reset-password`                | POST           | Reset with token        |
| `/api/v1/users/me`                           | GET/PUT/DELETE | Profile / delete        |
| `/api/v1/users/me/password`                  | PUT            | Change password         |
| `/api/v1/users/me/export`                    | GET            | GDPR export             |
| `/api/v1/users/me/preferences/ai-keys`       | GET/PUT        | Encrypted API keys      |
| `/api/v1/users/me/preferences/notifications` | GET/PUT        | Email toggles           |
| `/api/v1/users/me/preferences/resume`        | GET/PUT        | Resume defaults         |
| `/api/v1/users/me/devices`                   | GET            | List active devices     |
| `/api/v1/users/me/devices/{id}`              | DELETE         | Revoke session          |
| `/api/v1/profiles/me`                        | GET/PUT        | Master profile          |
| `/api/v1/jobs`                               | GET            | Search/filter           |
| `/api/v1/jobs/ranked`                        | GET            | Ranked list             |
| `/api/v1/jobs/top-matches`                   | GET            | Top matches for user    |
| `/api/v1/jobs/{id}`                          | GET            | Single job              |
| `/api/v1/jobs/{id}/analyze`                  | POST           | Trigger AI analysis     |
| `/api/v1/jobs/{id}/analysis`                 | GET            | Poll analysis           |
| `/api/v1/jobs/{id}/match-score`              | GET            | Calculate+store         |
| `/api/v1/jobs/{id}/match-score/cached`       | GET            | Read-only               |
| `/api/v1/jobs/import`                        | POST           | URL/desc import         |
| `/api/v1/jobs/import/history`                | GET            | Import history          |
| `/api/v1/jobs/import/{id}`                   | GET            | Single import           |
| `/api/v1/applications`                       | GET/POST       | List / create           |
| `/api/v1/applications/timeline`              | GET            | Global events           |
| `/api/v1/applications/followups`             | GET            | Follow-up list          |
| `/api/v1/applications/{id}`                  | GET/PUT        | Single app              |
| `/api/v1/applications/{id}/status`           | POST           | Status transition       |
| `/api/v1/applications/{id}/events`           | GET            | Timeline                |
| `/api/v1/applications/{id}/followup`         | PUT            | Set follow-up           |
| `/api/v1/applications/{id}/notes`            | GET/POST       | Notes                   |
| `/api/v1/applications/notes/{id}`            | PUT/DELETE     | Single note             |
| `/api/v1/applications/{id}/contacts`         | GET/POST       | Contacts                |
| `/api/v1/applications/contacts/{id}`         | PUT/DELETE     | Single contact          |
| `/api/v1/resumes`                            | GET/POST       | List / create           |
| `/api/v1/resumes/{id}`                       | GET/PUT/DELETE | Single resume           |
| `/api/v1/resumes/{id}/versions`              | GET            | Versions                |
| `/api/v1/resumes/{id}/versions`              | POST           | New version             |
| `/api/v1/resumes/{id}/generate`              | POST           | Tailor via AI           |
| `/api/v1/resumes/{id}/versions/{v}/export`   | GET            | PDF export              |
| `/api/v1/cover-letters`                      | GET/POST       | List / create           |
| `/api/v1/cover-letters/{id}`                 | GET/PUT/DELETE | Single letter           |
| `/api/v1/cover-letters/generate`             | POST           | AI generate             |
| `/api/v1/cover-letters/{id}/generate`        | POST           | AI regenerate           |
| `/api/v1/cover-letters/{id}/export`          | GET            | HTML/PDF export         |
| `/api/v1/batch`                              | GET/POST       | List / create           |
| `/api/v1/batch/{id}`                         | GET            | Single batch            |
| `/api/v1/batch/{id}/retry`                   | POST           | Retry failed            |
| `/api/v1/batch/{id}/cancel`                  | POST           | Cancel                  |
| `/api/v1/notifications`                      | GET            | List                    |
| `/api/v1/notifications/unread-count`         | GET            | Unread badge            |
| `/api/v1/notifications/{id}/read`            | POST           | Mark read               |
| `/api/v1/notifications/mark-all-read`        | POST           | Mark all                |
| `/api/v1/notifications/{id}`                 | DELETE         | Delete                  |
| `/api/v1/analytics/metrics`                  | GET            | Current metrics         |
| `/api/v1/analytics/snapshots`                | GET/POST       | Snapshots               |
| `/api/v1/analytics/snapshots/latest`         | GET            | Latest snapshot         |
| `/api/v1/dashboard/stats`                    | GET            | Dashboard numbers       |
| `/api/v1/stats/landing`                      | GET            | Landing stats           |
| `/api/v1/health`                             | GET            | Healthcheck             |

---

## Appendix B — Database Tables

| Table                    | Purpose                               |
| ------------------------ | ------------------------------------- |
| `users`                | Account records                       |
| `user_preferences`     | AI keys, email prefs, resume defaults |
| `device_sessions`      | Multi-device session tracking         |
| `refresh_tokens`       | JWT refresh tokens (hash only)        |
| `profiles`             | Master candidate profile              |
| `experiences`          | Work history (FK → profiles)         |
| `education`            | Education history                     |
| `skills`               | Candidate skills                      |
| `projects`             | Portfolio projects                    |
| `certifications`       | Certifications                        |
| `jobs`                 | Imported jobs                         |
| `job_imports`          | Import batches                        |
| `job_applications`     | User applications for jobs            |
| `job_analysis`         | AI analysis (1:1 with jobs)           |
| `job_match_scores`     | Per-user match scores                 |
| `resumes`              | Master resume docs                    |
| `resume_versions`      | Tailored versions (N per resume)      |
| `cover_letters`        | Cover letters                         |
| `application_events`   | Timeline events (append-only)         |
| `application_notes`    | User notes                            |
| `application_contacts` | Recruiters / HR contacts              |
| `notifications`        | In-app + email reminders              |
| `audit_logs`           | System audit trail                    |
| `analytics_snapshots`  | Daily analytics rollups               |
| `batch_jobs`           | Batch operation metadata              |

---

*Generated as part of the SiraFit codebase audit. Last reviewed against `main` branch.*
