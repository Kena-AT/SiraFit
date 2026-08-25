# SiraFit — Implementation Status

*Captured 2026-08-22. Purpose: reconcile the `docs/` folder against the actual codebase so
onboarding and planning start from reality, not from stale specs.*

## 0. Read this first — the docs describe three different products

The `docs/` folder is internally inconsistent. Treat the three tiers as follows:

1. **`SIRAFIT_OVERVIEW.md`** — the *as-built* source of truth. Describes the shipped web app
   (FastAPI backend, TanStack Router/Query frontend, jobs/resumes/cover-letters/applications/
   analytics/batch, Celery worker). **Matches the code.**
2. **`.docx` set (PRD, API Architecture, Technical Design, Frontend Design, etc.)** — describes a
   much larger *"local-first agentic platform"*: a desktop Local Agent running Playwright, a sync
   engine with append-only event logs, S3 storage, webhooks, OpenTelemetry, WebSockets/SSE, 2FA/OAuth.
   **Mostly NOT built.** Several of these docs also contradict the code (see §4–§5).
3. **`backend_arch.txt`** — proposes an `apps/ modules/ shared/` layout that **does not match** the
   real `backend/app/` package. It is an unrealized design; see the note now pinned to the top of
   that file.

**Bottom line:** the MVP web app (tier 1) is ~85–90% complete and regression-tested (270-test suite
green). The agentic/local-first vision (tier 2) is ~15–25% complete (core API exists; the agent
runtime, sync, scraping, and object storage do not).

## 1. Verified done (confirmed in code this session)

- **Jobs**: list / ranked / with-scores, search + filter + sort, import (URL + pasted description),
  AI analysis, match-score caching. `list_ranked_jobs` is N+1-free (2 bounded queries); `/jobs`
  uses singleflight dedup; 30s cache.
- **Match page**: 1 batched `getJobsWithScores` call instead of 200+.
- **Resumes & Cover Letters list pages**: global 60s `staleTime`, no per-query override → cache hits.
- **Dashboard**: cached 30s, invalidated on import.
- **Rate limiting**: returns **429** + `Retry-After` / `X-RateLimit-*`.
- **Caching / Redis**: lazy client, `allkeys-lru`, in-memory fallback.
- **DB pool**: `pool_size=20`, `max_overflow=10`, `pool_timeout=10`; **503 handler** for pool
  exhaustion (added 2026-08-22).
- **Security headers** (`SecurityHeadersMiddleware`: CSP, HSTS-in-prod, X-Frame-Options, etc.) + CSRF
  protection — both in `main.py`.
- **Worker**: `celery_worker` + `celery_beat` in both compose files; `Dockerfile.celery`; DLQ wired.
- **Health / metrics**: `/health/live`, `/health/ready`, `/metrics` (Prometheus), `worker_healthy`.
- **Analytics**: frontend renders real computed data (contract verified).
- **Batch**: `batch.py`, `services/batch.py`, `batch_operations.py`, `_app.batch.*` routes, retry/cancel.

## 2. Done per the docs' own "Currently Implemented" list

(routes/services/files exist; not re-read line-by-line this session)

JWT + refresh, email verification, password reset, device sessions, 7-provider AI with encrypted
per-user keys, deterministic + AI hybrid matching, async resume/cover-letter PDF (WeasyPrint),
application status machine + events + notes + contacts + follow-ups, in-app notifications + Brevo
email reminders, multi-device sessions.

## 3. Partially done / known limitations (admitted in `SIRAFIT_OVERVIEW.md` §11)

- CSV import — referenced in enum, not implemented.
- Real-time notifications — polled (5s), no WS/SSE.
- 2FA / OAuth — not implemented.
- Webhook ingestion — not implemented.
- Calendar sync — not implemented.
- Full-text job search — pagination + per-field filters only (no PG_TRGM).
- Resume scoring breakdown UI — data model has it; frontend shows top-line only.

## 4. NOT built (the tier-2 docx vision — grep-confirmed absent in backend)

- Playwright scraping runtime / Local Agent scraping — `grep playwright|selenium|scraping` → nothing.
  (An `agent_api.py` *connectivity check* exists and is surfaced in `/health/status`, but there is no
  scraping/sync engine code.)
- Sync engine / event-sourced sync / `event_log` / webhooks — absent.
- S3 / object storage / ClamAV — `grep boto3|s3` → nothing; PDFs rendered locally.
- OpenTelemetry tracing — absent (code uses structlog + Prometheus only).
- WebSockets / SSE — absent.
- 2FA / TOTP / WebAuthn — `grep totp|otp|2fa|mfa` → nothing.

## 5. Implemented DIFFERENT than the docs (doc-vs-code)

| Area | Docs say | Code actually does | Verdict |
|------|----------|--------------------|---------|
| Frontend framework | API/docx FE: **Next.js App Router** | **TanStack Router/Start + Vite** (matches overview) | docx FE stale; code correct |
| Backend layout | `backend_arch.txt`: `apps/ modules/ shared/` | flat `backend/app/{api,core,models,schemas,services,worker}` | txt is unrealized design |
| Pagination | API docx: **cursor** | **`skip`/`limit`** offset (matches overview) | docx wrong |
| Endpoint paths | API docx: `/api/v1/batches/jobs/analyze`, `/generations`, `/sync` | `/api/v1/batch`, `/resumes`, `/cover-letters` (no `/sync`) | docx wrong |
| Batch cap | API docx: **100**/request | **500** (`schemas/batch.py` `max_length=500`) | docx wrong; code matches spec |
| Rate limits | API docx: generation 20/hr, sync 120/min, imports 30/hr | `ai_generate` 10/hr, `api_import` 10/hr, no `/sync` | docx aspirational |
| Response envelope | API docx + `backend_arch.txt`: `{data,meta,errors}` / `{error:{code,message,request_id}}` | FastAPI `{"detail": ...}` | API consumers won't see the envelope |
| Resume templates | overview/docx: 5 | **5** (`minimal, technical, modern, corporate, compact`) | matches ✅ |
| Cover-letter templates | overview/docx: 3 | **3** (`classic, modern, compact`) | matches ✅ |

## 6. Where the code is BETTER than the docs

- Security headers (CSP/HSTS/CSRF) are implemented though no doc specified them.
- 503 on DB pool exhaustion — added; no doc required it.
- AI kept out of scoring (`matching_engine.py` deterministic-only) — honors the Technical Design
  constraint "AI never controls scoring," the safer reading of the PRD's looser wording.
- Singleflight + bounded queries for `/jobs` and ranked listings exceed the docs' "avoid N+1" ask.

## 7. What's left

The unbuilt tier-2 vision: desktop scraping agent, sync engine, S3, webhooks, real-time
notifications, 2FA, OpenTelemetry, calendar sync, full-text search, resume-breakdown UI, insights/stall
page. Plus the smaller known limitations in §3.

## 8. Risk / recommendation

The doc set is internally contradictory (Next.js vs TanStack, cursor vs offset, `/batch` vs
`/batches`, divergent rate limits, divergent batch cap). Anyone onboarding from the `.docx` API
Architecture will be misled about both the stack and the API contract. **`SIRAFIT_OVERVIEW.md` is the
only doc that tracks the code; the API Architecture docx and `backend_arch.txt` have been flagged for
reconciliation** (see notes pinned in those files).
