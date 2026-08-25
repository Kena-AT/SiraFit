# SiraFit — Product & Engineering Direction

*Suggestions for what to build next, how the app should work differently, and where the
competitive moat is. Grounded in the actual codebase as of 2026-08-22.*

**How to read this:** every suggestion cites a real module or gap in the current code. Items are
split into "reprioritize from existing docs" (already envisioned, I'd reorder) and "new" (not in the
docs). The last section lists what I'd explicitly *not* do.

---

## TL;DR

1. The deterministic, explainable scoring engine (`matching_engine.py`) is the real differentiator —
   productize it as a free top-of-funnel tool and a public API.
2. The missing acquisition channel is a **browser-extension capture + autofill layer** backed by
   **Scrapling** as the server-side scraping engine — not the heavy Playwright desktop "Local Agent"
   the docs describe.
3. Analytics, resume scoring, application follow-ups, and notifications all exist but are undercooked.
4. Moat = **BYOK + 7 providers + per-user encrypted keys** (near-zero AI cost, privacy-defensible)
   plus **explainable scoring**.
5. Do **not** build auto-apply, a premature distributed sync engine, or mass auto-crawling (Scrapling
   powers *user-initiated* import, not bulk scraping).

---

## Priority snapshot

| # | Suggestion | Effort | Impact | Phase |
|---|------------|--------|--------|-------|
| 1 | Public "Resume Match Score" free tool (PLG) | Low | High | Now |
| 2 | Resume Health Score (gap in docs) | Low | High | Now |
| 3 | Browser-extension job capture + autofill | Med | High | Now–Next |
| 3b | Scrapling backend scraping engine (URL + saved-jobs import) | Med | High | Now |
| 4 | WS/SSE instead of 5s polling | Low | Med | Now |
| 5 | Analytics → salary benchmark + skills-gap | Med | High | Next |
| 6 | Per-job resume variants + diff/revert | Med | Med | Next |
| 7 | Gap-to-plan + interview-prep coach | Med | High | Next |
| 8 | Full-text job search (pg_trgm) | Low | Med | Next |
| 9 | API contract tests (stop doc drift) | Low | High | Now |
| 10 | 2FA | Med | Med (trust) | Next |
| 11 | Local/on-device tailoring provider | Med | Med | Later |
| 12 | Career-cohort / coaching licenses (B2B2C) | Med | High | Later |

---

## 1. Weaponize the deterministic scoring engine (crown jewel)

`matching_engine.py` is **deterministic and explainable** — rare in this space (Teal, Jobscan,
Kickresume hide behind opaque "AI match %"). Right now it's an internal ranking signal. Turn it into
the product's identity.

- **Free top-of-funnel tool (PLG):** paste a job + resume → transparent match breakdown. This is
  Jobscan's whole business; win on explainability + let users bring their own AI key for writing.
  Free, no login, shareable. It's the customer-acquisition engine.
- **Resume Health Score** — currently a *known limitation* (`SIRAFIT_OVERVIEW.md` §11). ATS readiness,
  keyword density, action-verb usage, quantified-achievement ratio, section completeness. Job seekers
  pay specifically for this.
- **Public, documented scoring API** on top of the engine. `batch.py` already scores up to 500 jobs
  per call — expose "score my resume against N jobs." Developers + career coaches become a
  distribution channel.

## 2. The #1 missing piece: browser-extension capture + autofill

The docs describe a **Playwright desktop "Local Agent"** that scrapes jobs. Reframe: a heavy desktop
scraping runtime is a ToS minefield, a maintenance burden across site changes, and easy to block. The
higher-ROI, lower-risk version is a **browser extension** (Teal/Simplify style) that captures a job
with one click as the user browses LinkedIn / Indeed / Greenhouse / Lever, importing via the existing
`/jobs/import`. Repoint `agent_api.py` (currently a health stub) + the "scraping runtime" language in
`backend_arch.txt` at an extension, not a phantom desktop agent.

 - Extension also unlocks **autofill**: pre-fill application forms from stored profile/resume. Users
   pay for this and it stays within site ToS (user-initiated).

### Scrapling as the backend scraping engine

Rather than a hand-rolled Playwright scraper, use [Scrapling](https://github.com/D4Vinci/Scrapling)
(actively maintained, Python 3.10+, compatible with this backend's 3.12) as the server-side
fetch + parse layer. Its **adaptive parsing** — selectors auto-relocate when a site's layout changes —
directly removes the maintenance tax that makes job-board scrapers brittle, which is why a scraping
runtime was risky before. The extension captures DOM client-side; Scrapling handles URL
fetching/parsing server-side.

- **Integration point:** swap the current fetch/parse in `services/job_import.py` (used by `jobs.py`
  import) for a Scrapling fetcher + adaptive selectors. This upgrades the URL-import feature you
  already ship. The lightweight stealth-HTTP fetcher covers mostly-static boards (Greenhouse/Lever);
  the browser-automation fetchers cover JS-heavy / anti-bot boards (LinkedIn).
- **Run it in the Celery worker, not the request path.** Browser fetchers are heavy; the existing
  `worker/` + `celery_beat` infra is the natural home (same pattern as `batch.py`). Add
  `scrapling[fetchers]` + the `scrapling install` browser deps to the backend/celery Docker images.
- **Scope:** user-provided URLs and the user's own authenticated saved-jobs (via session), with rate
  limits — not mass auto-crawling (same ToS/quality line as auto-apply).
- It also ships an MCP server + a Claude/OpenClaw agent skill, which dovetails with the local-agent
  vision later.

- **Do NOT build auto-apply** (see §7).

## 3. Features that exist but are crowded out

- **Analytics** (`frontend` analytics routes render real computed data, verified) is a roof over an
  empty room. Expand to: salary benchmarking from imported jobs (role/level/location); personal
  **skills-gap report** (skills most common in imported JDs the user lacks); "you're an X% match for
  Senior Backend in Berlin; here are the 3 skills blocking you."
- **Resume templates (5) + cover letters (3)** exist; tailoring is one-shot. Add **per-job variant
  management**: base resume + N tailored versions, diff, revert. `resume_generation.py` already renders
  per-template — add versioning.
- **Applications status machine + follow-ups** exist; follow-up *content* is generic. Use AI providers
  to draft a personalized follow-up per stage, pre-filled for edit. `check_reminders_task` (Celery
  beat) already fires reminders — attach a drafted message.
- **Notifications polled every 5s** → swap to WebSockets/SSE. Cheap, high-ROI, unlocks live "new
  match" alerts the moment a batch imports.
- **Full-text job search** (known limitation) → add Postgres `pg_trgm`/FTS. Trivial given existing
  `skip/limit` queries; makes a 200-job list actually searchable.

## 4. Bold, differentiated (not in the docs)

- **Gap-to-plan engine:** resume → target role → prioritized learning/action plan ("weak on Kubernetes
  — here's a project that demonstrates it"). Deterministic score already knows the gap; close loop
  diagnosis → action. Human-in-the-loop; **never fabricate experience** (ethical guardrail the
  generation path needs explicitly).
- **Interview-prep mode:** given job + resume, generate likely questions, technical deep-dives, study
  plan over existing generation infra. High willingness-to-pay, low cost.
- **Semantic "similar jobs / relevant achievements" search:** embeddings over imported jobs + resume
  bullets → "which past achievement best fits this JD", "find jobs like the one I aced." Provider
  abstraction can call an embedding model.
- **Career-cohort / coaching licenses:** multi-device sessions + per-user keys already support "one
  account manages many clients." Sell to university career centers + independent coaches (B2B2C).
- **Local / on-device tailoring:** 7-provider abstraction means a local model (Ollama/LM Studio) is
  mostly a new provider entry. Privacy-first users pay a premium for "my resume never leaves my
  machine."

## 5. How the architecture should work differently

- **Kill the premature "sync engine / event-sourced sync"** from the spec. Distributed-systems
  gold-plating for a multi-device-conflict problem you don't have yet. Stay server-authoritative with
  polling/SSE; build real sync only when telemetry shows conflicts.
- **Extension > desktop agent** (§2) — simpler, ToS-safe, shippable in weeks. Scrapling is the
  server-side engine behind it; run its browser fetchers in Celery, not the request path.
- **API contract tests.** Docs drifted so far the API docx specified a different envelope, pagination,
  and paths than the code. Contract tests (response shape + doc-matching assertions) make that
  impossible. 270 unit tests pass; apparently none are contract tests.
- **Stale-while-revalidate on the match page.** Already have 30s cache + singleflight — extend to SWR
  for instant-feeling UI with background refresh.
- **Prioritize 2FA.** Listed gap; for a tool holding resumes + job history + AI keys, trust signals
  drive conversion. Do it before more features.

## 6. The actual moat (sharpen it)

- **BYOK + 7 providers + per-user Fernet-encrypted keys** (`core/security.py` encrypt_value).
  Competitors can't easily copy: *AI cost approaches zero* because users bring the key, and it's
  privacy-defensible ("your data never trains models"). Market loudly.
- **Explainable scoring** (§1) is the second pillar: "we show you *why* you're a 72% match" beats
  "our AI says 72%."
- **Privacy-first, local-optional, portable.** `/me/export` exists — expand to one-click full
  workspace export. Data-ownership is a rising consumer demand; own that position.

## 7. Explicitly do NOT

- **Auto-apply / auto-submit** — ToS, spam reputation, low quality that hurts the user.
- **Mass / auto-crawling** — ToS, spam reputation, low quality. Scrapling is fine for *user-initiated*
  URL + own-saved-jobs import, but not bulk scraping of boards.
- **Premature distributed sync engine** — solve the real problem when it appears.
- **Fabricate resume content in generation** — add a "verified facts only" guardrail; fabrication is
  unethical and a liability when a recruiter catches it.

---

## 8. Scrapling implementation plan

Detailed engineering plan for making Scrapling the app's scraping engine. Phase 0 is **done**;
Phases 1–4 are the roadmap. All scraping is **server-side** (Python); the browser extension (§2/§3)
is a separate client-side capture path that complements it.

### 8.1 Current state
- **Before:** `services/job_import.py::parse_job_from_url` did **not** fetch the page — it guessed a
  title from the URL path and returned `description: None`. URL import stored almost no real data.
- **Phase 0 (done):** added `fetch_job_html` (Scrapling `Fetcher` stealthy engine) and
  `parse_job_html` (`Selector(adaptive=True)`; JSON-LD `JobPosting` → Open-Graph/meta → DOM
  heuristics), wired into `process_import`'s URL branch with a **non-fatal fallback** to the old
  heuristic. Added `scrapling[fetchers]==0.4.14` to `requirements.txt` and commented-out optional
  `RUN scrapling install` steps in `Dockerfile` + `Dockerfile.celery`.
- **Still heuristic/limited:** salary via regex, company for non-JSON-LD pages, no import rate limit,
  synchronous (blocks the request), no saved-jobs import, no browser-extension wiring.

### 8.2 Goals
- Robust, low-maintenance ingestion from **user-provided URLs** and later the **user's own saved
  jobs**.
- Stay ToS-safe: user-initiated, user's-own-data only, no mass crawl.
- Keep infra/cost low: stealthy HTTP first; browser engines optional and offloaded.

### 8.3 Non-goals
- Auto-apply / auto-submit (see §7).
- Mass crawling or competitor indexing of boards.
- A heavy desktop "Local Agent" (replaced by extension + server-side Scrapling).

### 8.4 Architecture
- **Server-side only.** Scrapling is Python; it never runs in the browser extension.
- **Two engine tiers:**
  - *Tier A (default):* `Fetcher.configure(stealthy=True)` — curl_cffi TLS-impersonation, **no
    browser binary**. Covers Greenhouse, Lever, Ashby, and most ATS/boards that serve HTML.
  - *Tier B (optional):* `Fetcher.configure(adaptive=True, stealthy=True)` — adds a Playwright/
    patchright browser fallback for JS-heavy / anti-bot boards (LinkedIn, Indeed). Requires
    `scrapling install` (Chromium download) + uncommenting the Docker step. Heavy → Celery only.
- **Parsing:** `Selector(adaptive=True)` so selectors auto-relocate when a site's layout changes —
  this is the maintenance-tax removal that makes scraping viable.
- **Async boundary:** move fetching off the request path into `app/worker/tasks.py`
  (`@celery_app.task`, mirroring the existing resume/pdf/batch tasks) so the import endpoint returns
  `status=processing` immediately and the existing `JobImport` record is updated on completion. The
  `sirafit` queue already exists in `Dockerfile.celery`; add a `scraping` queue for Tier B.
- **Rate limiting:** reuse `app/core/rate_limiting.py::check_rate_limit` (the same `RateLimiter`
  behind `RateLimitMiddleware` in `main.py`) to bound imports per user, within the existing per-user
  envelope used for AI generation.

### 8.5 Phase 0 — URL import enrichment (DONE)
- Files: `services/job_import.py`, `requirements.txt`, `Dockerfile`, `Dockerfile.celery`.
- Verified: JSON-LD extraction, DOM-only fallback, and stable-`external_id` merge all pass unit checks.

### 8.6 Phase 1 — Harden & productionize (next)
1. **Offload to Celery.** Add `scrape_and_import_job.delay(user_id, url, import_id)` in
   `worker/tasks.py`; `process_import` becomes a thin orchestrator that creates
   `JobImport(status="processing")` and enqueues. The endpoint returns status immediately (client
   polls) instead of blocking on the fetch. Minimal alternative for Tier A MVP: wrap the fetch in
   `run_in_threadpool` (as `list_jobs` already does) with a hard timeout, keeping the sync contract.
2. **Timeouts / retries.** Scrapling `timeout=15`, `retries=2`, plus a Celery `soft_time_limit`.
   Tier B browser fetches get a longer limit and run on the `scraping` queue only.
3. **Rate limit imports.** Call `check_rate_limit(request, "import", user_id)` at the endpoint
   (service-layer equivalent inside the task), reusing the Redis-backed `RateLimiter`.
4. **Cache fetched HTML.** Redis-cache parsed HTML keyed by URL hash with a short TTL to avoid
   re-fetching the same URL in one session (matches the stale-while-revalidate spirit in §5).
5. **Structured degradation.** On full fetch/parse failure, keep the heuristic record but annotate
   `JobImport` so the UI can show "imported from URL (limited metadata)."
6. **Tests.** Unit tests for `parse_job_html` with fixtures: JSON-LD, DOM-only, empty body, malformed
   JSON-LD, and an anti-bot challenge page. Mock the network so tests never hit live sites.

### 8.7 Phase 2 — Saved-jobs importer (authenticated)
- The legitimate core of the "Local Agent" idea: pull the user's **own** saved jobs, not crawl the web.
- New `source_type` (e.g. `session` / per-board) where the user supplies an authenticated
  session cookie/token, stored encrypted via `core/security.py::encrypt_value` (same as AI keys);
  never log or expose it. Add a new `JobImport.source` value (e.g. `linkedin_session`).
- Per-board connector modules `services/scraping/<board>.py` (LinkedIn/Indeed/Greenhouse) layered on
  top of `fetch_job_html` + `parse_job_html` with board-specific selectors.
- Enqueue a Celery **batch** (respect `batch.py`'s 500-item ceiling) that fetches each saved URL and
  imports via the same `process_import` path. Use a stable `external_id` per board to avoid dupes
  (the `Job.external_id` column is unique-indexed).
- ToS: only the user's own saved items, explicit consent, rate-limited and queued.

### 8.8 Phase 3 — Browser-extension capture (client side)
- A Teal/Simplify-style extension captures the job DOM and applies autofill, then sends **structured
  JSON** (not raw HTML) to a lightweight endpoint (reuse `/jobs/import` with a new `source_type=
  "extension"`), bypassing server-side fetch for those jobs.
- Scrapling's role here is the resilient **server-side fallback** for URLs the extension can't reach,
  plus powering the saved-jobs importer (Phase 2). Repoint `agent_api.py` (currently a health stub)
  to document/serve the extension handshake.

### 8.9 Phase 4 — Local-agent vision (deferred)
- Scrapling already ships an MCP server + a Claude/OpenClaw agent skill. The Phase-2 saved-jobs
  importer is the natural on-ramp to a local agent that periodically refreshes the user's saved roles.
  Defer until Phase 2 proves value and the ToS posture is settled.

### 8.10 ToS / ethical guardrails (cross-cutting)
- User-initiated only; never auto-crawl boards.
- Only fetch URLs the user provides or their own authenticated saved jobs.
- Respect `robots.txt` and rate limits; send a clear, identifiable User-Agent.
- Never store raw session secrets in logs; encrypt at rest via `encrypt_value`.
- Never fabricate metadata — if a field can't be extracted, leave it `null` (the benign
  title/company URL heuristic stays only as a last-resort fallback).

### 8.11 Deployment / Docker
- Base image: `scrapling[fetchers]` is already in `requirements.txt`, so Tier A works out of the box.
- Browser tier: uncomment `RUN scrapling install` in `Dockerfile` + `Dockerfile.celery`; add the
  system libraries Playwright needs (the base is `python:3.12-slim`). Keep browser binaries in the
  **celery** image only — the API container stays small and browser-free.

### 8.12 Testing & acceptance
- **Unit:** `parse_job_html` fixtures (JSON-LD, DOM, anti-bot, empty); `fetch_job_html` network
  mocked.
- **Integration (staging only):** one real fetch per supported board behind a flag.
- **Acceptance:** a Greenhouse/Lever URL yields a real description + parsed salary; a fetch failure
  degrades to the heuristic without a 5xx; import endpoint stays responsive after Celery offload;
  exceeding the rate limit returns 429 with `X-RateLimit-*` headers (reusing the existing middleware).

### 8.13 Open decisions (need your call)
- Scope of Phase 2 now, or stay URL-only for the moment?
- Enable the browser tier (Tier B) now or later (adds image size + `scrapling install` in CI)?
- Import rate-limit number/window — reuse the AI-generation envelope or a dedicated one?
- Session-secret storage slot for saved-jobs (new `encrypt_value` key vs. reusing the AI-key slot)?

---

## Suggested first build

Highest leverage, shippable fast:

- **(0) Scrapling URL-import upgrade** *(implemented)* — `services/job_import.py` now fetches the
  page via Scrapling (`Fetcher` stealthy engine) and parses with `Selector(adaptive=True)`:
  JSON-LD `JobPosting` → OG/meta → DOM heuristics. Falls back to the prior heuristic if Scrapling
  is absent or the fetch fails, so the endpoint can never break.
- **(a) the public Resume Match Score tool** (reuses `matching_engine.py` + existing generation).
- **(b) the browser-extension capture layer** (reuses `/jobs/import` + `agent_api.py`; Scrapling is
  the server-side engine).
- **(c) API contract tests** so the docs can never drift again.

Steps (0)–(a)–(c) feed the core loop and the PLG funnel; (b) is the acquisition channel.

---

## 9. Recommended free tooling (the "Scrapling-equivalent" stack)

All tools below are **open-source and free to self-host** — no per-seat or per-call cost. Each targets
one brittle, hand-rolled, or paid-dependent part of SiraFit, the same way Scrapling targets scraping.
Together they reinforce the BYOK + privacy + lean-architecture moat (§6).

### Summary

| Tool | License | App aspect | What it replaces / improves |
|------|---------|-----------|----------------------------|
| Docling | Apache-2.0 | Resume/JD ingestion | basic PDF text extraction (loses layout/tables) |
| pdfplumber | MIT | Resume/JD ingestion | ad-hoc text/table scraping |
| unstructured | Apache-2.0 | Resume/JD ingestion | manual element partitioning |
| Instructor | MIT | AI reliability (7 providers) | fragile JSON parsing + retry glue |
| sentence-transformers | Apache-2.0 | Embeddings | paid embedding APIs |
| ChromaDB | Apache-2.0 | Vector search | external vector service |
| pgvector | Free OSS | Vector search (Postgres-native) | external vector service |
| DuckDB | MIT | Analytics + vector | slow/heavy analytics path |
| promptfoo | MIT | LLM evals / regression | manual prompt testing |
| deepeval | Apache-2.0 | LLM unit tests | none |
| ruff | MIT | Code quality | slow/legacy linters |
| bandit | Apache-2.0 | Security lint | none |
| pip-audit | MIT | Dependency security | none |
| Plasmo | MIT | Browser extension | raw Manifest V3 plumbing |
| Ollama | MIT | Local / private AI | cloud-only providers |
| llama-cpp-python | MIT | Local / private AI | cloud-only providers |
| WeasyPrint | Free OSS | Resume PDF generation | paid/limited PDF render |

### 9.1 Document & resume ingestion
- **Docling (Apache-2.0, IBM).** Converts multi-column PDFs and Word docs into structured markdown and
  JSON with high layout fidelity (headings, tables, bullet groups preserved), and can OCR scanned
  resumes via Tesseract. Replaces the current basic extractor so the profile builder and matching
  engine receive clean structured data. Integration: swap the PDF/DOCX parsing step in the resume and
  JD import pipelines.
- **pdfplumber (MIT).** Precise, surgical text and table extraction when you need character-level
  control over specific resume regions. Good companion to Docling for edge cases.
- **unstructured (Apache-2.0).** Partitions documents into typed elements (title, list, table) that
  map directly onto the `Job` / `Profile` models. Note: the OSS library is free; their hosted API is
  paid — self-host the library only.

### 9.2 AI reliability across 7 BYOK providers
- **Instructor (MIT).** Patches any OpenAI-compatible client to enforce **Pydantic v2** schemas and
  auto-retries on validation failure (self-correction loop). Eliminates malformed-JSON crashes and
  retry sprawl in resume tailoring, cover-letter generation, and JD parsing. Integration: wrap the
  existing provider abstraction (`services/*_generation.py`) so every AI call returns a validated
  object instead of raw text.

### 9.3 Embeddings & semantic search
- **sentence-transformers (Apache-2.0).** Generate local embeddings with **no API spend**, powering
  semantic match, similar-achievement lookup, and "jobs like the one I aced" (§4).
- **ChromaDB (Apache-2.0).** Free embedded vector store; zero separate service to run.
- **pgvector (free OSS Postgres extension).** If staying on Postgres, adds vector similarity with no
  new infrastructure — natural fit for the existing DB.
- **DuckDB (MIT).** Also ships a vector engine for in-process similarity when you want analytics +
  search in one embedded engine.

### 9.4 Analytics & benchmarking
- **DuckDB (MIT).** Embedded columnar engine that turns hundreds of imported jobs into instant salary
  benchmarks and skills-gap reports inside the existing Python worker, with no warehouse. Doubles as
  the vector engine noted above.

### 9.5 Testing, LLM evals & code health
- **promptfoo (MIT).** Free eval framework that runs prompts against every provider at once and catches
  regressions before ship — essential for a multi-provider app.
- **deepeval (Apache-2.0).** Unit tests for LLM outputs (faithfulness, schema, quality gates).
- **ruff (MIT).** Extremely fast all-in-one linter + formatter; replaces slower legacy tooling in CI.
- **bandit (Apache-2.0).** Static security analysis for Python; surfaces injection/secret risks.
- **pip-audit (MIT).** Scans dependencies for known vulnerabilities; wire into CI for supply-chain safety.

### 9.6 Frontend & browser extension
- **Plasmo (MIT).** Free, open-source framework for cross-browser extensions with a React/TanStack-friendly
  DX. Makes the capture + autofill extension (§2/§3) far faster than hand-rolling Manifest V3.

### 9.7 Local / private AI (privacy moat)
- **Ollama (MIT).** Run local models on the user's machine; a real, cost-free provider behind the
  existing abstraction, realizing the "local/on-device tailoring" idea (§4).
- **llama-cpp-python (MIT).** Run GGUF models locally with broad hardware support; another local
  provider option.

### 9.8 Resume PDF generation
- **WeasyPrint (free, open-source).** Render styled, print-quality resume PDFs from HTML/CSS with no
  paid service. Integration: replace or augment the current PDF renderer for tailored resume variants.

### 9.9 Why this stack
Every tool is free and self-hostable, so adopting them costs nothing but engineering time and directly
extends the moat: BYOK keeps AI spend near zero, local options (Ollama, sentence-transformers,
WeasyPrint) keep user data on-machine, and each removes a category of brittle custom code — the same
lever Scrapling pulls for scraping.

---

## 10. Expanded free tooling, architectures & pipelines (the rest of the stack)

Beyond the curated §9 set, here are additional **free / open-source** tools, architectural patterns,
and pipeline designs that close gaps across search, CV writing, retrieval, frontend/design,
observability, security, and ops. Licenses range from permissive (MIT/Apache/BSD) to copyleft (AGPL
for a few like MinIO, Grafana, Plausible) — all are free to self-host; review copyleft terms only if
you ever ship a closed-source hosted offering.

### 10.1 Search & retrieval (upgrade from ILIKE)
- **Meilisearch (MIT)** / **Typesense (Apache-2.0)** — free OSS instant search engines with typo
  tolerance and ranked results, far better than Postgres `ILIKE` for job search. Self-host alongside
  the DB.
- **Whoosh (BSD)** — pure-Python index if you want zero extra infrastructure.
- **Cross-encoder reranking** via `sentence-transformers` (free) — re-rank keyword/vector hits by true
  relevance; a free stand-in for paid rerank APIs.

### 10.2 CV / resume writing & optimization (the "CV writers")
NLP and quality tooling that makes generated resumes genuinely better, not just longer:
- **spaCy (MIT)** — skill/entity extraction, rewriting suggestions, semantic similarity to the JD.
- **KeyBERT (MIT)** — extract ATS keywords from a JD so the resume targets the right terms.
- **textstat (MIT)** — readability scores per bullet/section.
- **LanguageTool (LGPL, free OSS)** via `language-tool-python` — grammar/style checking of resume text.
- **PyTextRank (MIT)** — key-phrase extraction and JD summarization to align bullets with the role.
- **scikit-learn / numpy / pandas (BSD)** — ML features, a learnable ATS-scoring model, skills-gap
  quantification.
- **Argos Translate / LibreTranslate (free OSS)** — offline multilingual resume translation.
- **Tesseract + pytesseract / EasyOCR (Apache-2.0)** — OCR for scanned resumes (Docling uses Tesseract).
- **python-docx / PyLaTeX** — export to Word and LaTeX CVs; **WeasyPrint** for PDF (§9.8).
- **difflib / embeddings** — detect duplication across tailored variants to keep them original.

### 10.3 Workflow & pipeline orchestration
- **Prefect (Apache-2.0) / Dagster (Apache-2.0) / Temporal (MIT)** — durable, observable pipelines for
  import → parse → score → tailor → review → export, with retries, branching, and a visual UI. Use
  these for the multi-step "job applied" flow instead of ad-hoc chaining inside Celery.
- **arq / dramatiq (free)** — lighter Celery alternatives for simple async tasks.
- Validate data passed between steps with **Pydantic** contracts.

### 10.4 Frontend, design systems & mechanisms
- **shadcn/ui (free OSS) + Radix UI (MIT) + Tailwind (free)** — accessible, themeable components.
- **Zod (MIT)** — frontend validation mirroring Pydantic; **TanStack Query/Table/Form** already in stack.
- **lucide-react (free)** icons; **react-pdf (MIT)** resume preview; **Framer Motion (free)** motion.
- **Storybook (free OSS)** — component docs/visual testing; **lost-pixel (free OSS)** visual regression
  (vs the paid Chromatic).
- **Style Dictionary (Apache-2.0, Amazon)** — manage design tokens across platforms for consistency.
- **axe-core / pa11y (free OSS)** — automated accessibility checks in CI.

### 10.5 Product analytics & experimentation (privacy-first)
- **Plausible / Umami / OpenReplay (free OSS)** — privacy-friendly analytics & session replay, matching
  the no-Google-Analytics privacy moat.
- **PostHog (OSS self-host free) / Unleash (Apache-2.0) / Flagsmith (BSD)** — feature flags + A/B tests.

### 10.6 Observability & ops
- **OpenTelemetry (CNCF, free)** — tracing across ingestion → AI → scoring.
- **Grafana (free OSS) + Prometheus (used)** dashboards; **Pyroscope (Apache-2.0)** continuous profiling.
- **GlitchTip (free OSS)** — Sentry-compatible error tracking without the paid tier.
- **pre-commit (free)** with ruff/bandit/pip-audit; **Renovate (free OSS)** auto dependency updates.

### 10.7 Security scanning
- **Semgrep (free OSS) + Trivy (Apache-2.0)** — SAST + container image scanning in CI.
- **sops (Mozilla, free OSS)** — encrypted secrets in git (avoids the BSL-licensed Vault).

### 10.8 Storage, files & infra
- **MinIO (AGPL, self-host free)** or plain disk + presigned URLs — S3-compatible object storage for
  resume PDFs (the app already stores `pdf_url`); note AGPL if a closed commercial offering is planned.
- **nginx / Traefik (free OSS)** reverse proxy; **Podman (Apache-2.0)** as a Docker alternative.
- **uv (Astral, MIT) / pip-tools** — fast, reproducible Python dependency management.

### 10.9 API & developer experience
- **Scalar (free OSS) / Redoc** — nicer FastAPI docs UI than default Swagger.
- **slowapi / limits (free)** — drop-in rate limiting if you outgrow the custom limiter.
- **respx / responses / vcrpy (free)** — HTTP mocking; **factory_boy + faker** fixtures;
  **hypothesis (MPL, free)** property-based testing.

### 10.10 Architectural patterns worth adopting
- **Retrieval-augmented tailoring:** embed JD + resume, retrieve only relevant achievements
  (sentence-transformers + ChromaDB), feed those to the LLM → cheaper, grounded, higher-quality resumes.
- **Event-driven import pipeline:** status events (imported → parsed → scored → tailored) over
  Celery/Redis streams so the UI updates live (ties to WS/SSE in §3).
- **Multi-provider tiers:** keep the existing abstraction, add a local provider (Ollama) and a
  "cheap vs quality" selector.
- **ATS feedback loop:** run KeyBERT + spaCy to score the generated resume against the JD before
  returning, auto-suggesting fixes.
- **Design tokens + Storybook** to keep the UI consistent as features grow.
- **Privacy-by-design:** all PII (resume, keys, session secrets) encrypted at rest (`encrypt_value`),
  local-model option, no third-party analytics.

### 10.11 Concrete "work pipeline" (fully buildable with the free tools above)
A single job import → tailored resume:
1. Scrape/import JD — **Scrapling** (§8).
2. Parse + structure — **Docling / unstructured** (§9.1).
3. Extract target keywords + summarize — **KeyBERT / PyTextRank / spaCy**.
4. Score match — deterministic engine + embedding similarity.
5. Retrieve relevant past achievements — **ChromaDB**.
6. Generate tailored resume via **Instructor**-enforced schema + local or BYOK model.
7. ATS pre-check (**KeyBERT / spaCy**) + grammar (**LanguageTool**) + readability (**textstat**); loop
   if below threshold.
8. Render PDF (**WeasyPrint**) / DOCX (**python-docx**) / LaTeX (**PyLaTeX**).
9. Store in object storage (**MinIO**) + cache invalidation.
10. Notify user (**Celery beat / apprise**) + live update (**WS/SSE**).

Every step uses a free, self-hostable tool from §9–§10, so the whole pipeline costs nothing but compute
and keeps user data on-machine.
