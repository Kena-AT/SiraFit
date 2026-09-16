import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from sqlalchemy.exc import OperationalError, TimeoutError as SQLATimeoutError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.router import api_router
from app.core.health import router as health_router
from app.core.logging import configure_logging
from app.core.middleware import RequestTimingMiddleware
from app.core.rate_limiting import RateLimitMiddleware
from app.core.metrics import router as metrics_router, MetricsMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Configure structured logging
configure_logging()
logger = structlog.get_logger("app")


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add rate limit headers if they were set during request processing
        if hasattr(request.state, "rate_limit_remaining"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
            response.headers["X-RateLimit-Remaining"] = str(
                request.state.rate_limit_remaining
            )
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if settings.ENVIRONMENT == "production":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "img-src 'self' data: https://*.sirafit.com; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self' https://*.sirafit.com; "
                "connect-src 'self' https://*.sirafit.com https://api.sirafit.com; "
                "frame-ancestors 'none'; "
                "form-action 'self'; "
                "object-src 'none'"
            )
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        else:
            # Development: permissive CSP so localhost Vite dev server is not blocked
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' http://localhost:* ws://localhost:*; "
                "img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; "
                "connect-src 'self' http://localhost:* ws://localhost:*; "
                "frame-ancestors 'none'; "
                "object-src 'none'"
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    from app.core.redis_client import get_redis_client
    redis_client = get_redis_client()
    if not redis_client:
        if settings.ENVIRONMENT == "production":
            logger.error("redis_connection_required_failed", extra={"redis_url": settings.REDIS_URL})
            raise RuntimeError(f"FATAL: Redis connection could not be established at {settings.REDIS_URL}. Redis is required in production.")
        else:
            logger.warning("redis_unavailable_using_memory_cache", extra={"redis_url": settings.REDIS_URL})
    else:
        try:
            redis_client.ping()
        except Exception as e:
            if settings.ENVIRONMENT == "production":
                logger.error("redis_ping_failed", extra={"error": str(e)})
                raise RuntimeError(f"FATAL: Redis ping failed at {settings.REDIS_URL}: {e}")
            else:
                logger.warning("redis_ping_failed_using_memory_cache", extra={"error": str(e)})

    # Startup: create tables if they don't exist & auto-add missing columns (schema drift healing).
    from app.core.database import Base, engine
    if settings.ENVIRONMENT in ("development", "testing"):
        Base.metadata.create_all(bind=engine)

    # ---------------------------------------------------------------------------
    # Schema drift healing — runs on every startup across all environments.
    # Uses ADD COLUMN IF NOT EXISTS so it is fully idempotent and safe to
    # run repeatedly against a database that is fully, partially, or not at
    # all migrated.  This is the safety net for Neon Postgres and any
    # environment where Alembic hasn't been run yet.
    # ---------------------------------------------------------------------------
    try:
        from sqlalchemy import text

        def _heal(conn, table: str, columns: list) -> None:
            """Add each (col, typedef) to table if it doesn't already exist."""
            for col_name, col_def in columns:
                try:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                    ))
                except Exception:
                    pass  # column already exists or other benign error

        def _run(conn, sql: str) -> None:
            """Execute a raw DDL statement, ignoring errors (already exists etc.)."""
            try:
                conn.execute(text(sql))
            except Exception:
                pass

        with engine.begin() as conn:
            # ── Create missing tables ─────────────────────────────────────────
            # Tables that may not exist at all on a fresh Neon DB or a DB that
            # has never had migrations run.

            _run(conn, """
                CREATE TABLE IF NOT EXISTS device_sessions (
                    id          SERIAL PRIMARY KEY,
                    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    device_name VARCHAR(100) NOT NULL,
                    ip_address  VARCHAR(45),
                    user_agent  TEXT,
                    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
                    last_seen   TIMESTAMP NOT NULL DEFAULT NOW(),
                    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_device_sessions_user_active ON device_sessions (user_id, is_active)")

            _run(conn, """
                CREATE TABLE IF NOT EXISTS job_imports (
                    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    source      VARCHAR(50) NOT NULL,
                    status      VARCHAR(20) DEFAULT 'pending',
                    total_found INTEGER DEFAULT 0,
                    ok_count    INTEGER DEFAULT 0,
                    fail_count  INTEGER DEFAULT 0,
                    errors      JSON DEFAULT '[]',
                    partial     BOOLEAN NOT NULL DEFAULT FALSE,
                    source_data TEXT,
                    created_at  TIMESTAMP,
                    updated_at  TIMESTAMP
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_job_imports_user_id ON job_imports (user_id)")

            _run(conn, """
                CREATE TABLE IF NOT EXISTS job_import_items (
                    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    import_id     UUID NOT NULL REFERENCES job_imports(id) ON DELETE CASCADE,
                    job_id        UUID REFERENCES jobs(id) ON DELETE SET NULL,
                    status        VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    title_guess   VARCHAR(255),
                    created_at    TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_job_import_items_import_id ON job_import_items (import_id)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_job_import_items_job_id ON job_import_items (job_id)")

            _run(conn, """
                CREATE TABLE IF NOT EXISTS application_events (
                    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
                    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    event_type     VARCHAR(30) NOT NULL,
                    title          VARCHAR(255) NOT NULL,
                    description    TEXT,
                    event_metadata JSONB,
                    occurred_at    TIMESTAMP NOT NULL DEFAULT NOW(),
                    created_at     TIMESTAMP
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_application_events_user_id ON application_events (user_id)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_application_events_app_id ON application_events (application_id)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_application_events_occurred_at ON application_events (occurred_at)")

            _run(conn, """
                CREATE TABLE IF NOT EXISTS application_notes (
                    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
                    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    body           TEXT NOT NULL,
                    author         VARCHAR(100),
                    pinned         BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at     TIMESTAMP,
                    updated_at     TIMESTAMP
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_application_notes_user_id ON application_notes (user_id)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_application_notes_app_id ON application_notes (application_id)")

            _run(conn, """
                CREATE TABLE IF NOT EXISTS application_contacts (
                    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
                    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name           VARCHAR(255) NOT NULL,
                    email          VARCHAR(255),
                    phone          VARCHAR(50),
                    role           VARCHAR(50) NOT NULL DEFAULT 'recruiter',
                    company        VARCHAR(255),
                    linkedin       VARCHAR(500),
                    notes          TEXT,
                    is_primary     BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at     TIMESTAMP,
                    updated_at     TIMESTAMP
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_application_contacts_user_id ON application_contacts (user_id)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_application_contacts_app_id ON application_contacts (application_id)")

            _run(conn, """
                CREATE TABLE IF NOT EXISTS analytics_snapshots (
                    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    snapshot_date TIMESTAMPTZ DEFAULT NOW(),
                    metrics       JSONB NOT NULL,
                    created_at    TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_analytics_snapshots_user_id ON analytics_snapshots (user_id)")

            _run(conn, """
                CREATE TABLE IF NOT EXISTS batch_jobs (
                    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    operation_type   VARCHAR(30) NOT NULL,
                    status           VARCHAR(20) NOT NULL DEFAULT 'pending',
                    total_items      INTEGER NOT NULL DEFAULT 0,
                    processed_items  INTEGER NOT NULL DEFAULT 0,
                    succeeded_items  INTEGER NOT NULL DEFAULT 0,
                    failed_items     INTEGER NOT NULL DEFAULT 0,
                    payload          JSONB NOT NULL DEFAULT '{}',
                    result_summary   JSONB NOT NULL DEFAULT '{}',
                    cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
                    started_at       TIMESTAMPTZ,
                    completed_at     TIMESTAMPTZ,
                    created_at       TIMESTAMPTZ DEFAULT NOW(),
                    updated_at       TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_batch_jobs_user_id ON batch_jobs (user_id)")

            _run(conn, """
                CREATE TABLE IF NOT EXISTS notifications (
                    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title      VARCHAR(255) NOT NULL,
                    body       VARCHAR(2000) NOT NULL,
                    kind       VARCHAR(50) NOT NULL,
                    status     VARCHAR(20) NOT NULL DEFAULT 'unread',
                    read_at    TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_notifications_user_status ON notifications (user_id, status)")

            # ── Add missing columns to existing tables ────────────────────────
            _heal(conn, "user_preferences", [
                ("email_job_matches",       "BOOLEAN DEFAULT TRUE"),
                ("email_daily_summary",     "BOOLEAN DEFAULT FALSE"),
                ("push_notifications",      "BOOLEAN DEFAULT TRUE"),
                ("email_new_opportunities", "BOOLEAN DEFAULT TRUE"),
                ("default_template",        "VARCHAR(50) DEFAULT 'modern'"),
                ("auto_tailor_enabled",     "BOOLEAN DEFAULT TRUE"),
                ("export_format",           "VARCHAR(10) DEFAULT 'pdf'"),
                ("encrypted_gemini_key",    "VARCHAR(500)"),
                ("encrypted_openrouter_key","VARCHAR(500)"),
                ("encrypted_anthropic_key", "VARCHAR(500)"),
                ("encrypted_openai_key",    "VARCHAR(500)"),
                ("encrypted_grok_key",      "VARCHAR(500)"),
                ("encrypted_mistral_key",   "VARCHAR(500)"),
                ("encrypted_nvidia_key",    "VARCHAR(500)"),
                ("ai_provider",             "VARCHAR(50) DEFAULT 'gemini'"),
                ("ai_model",                "VARCHAR(255) DEFAULT 'gemini-1.5-flash'"),
                ("ai_fallback_order",       "TEXT"),
            ])

            # Sprint 1: OAuth & 2FA columns on users table
            _heal(conn, "users", [
                ("is_2fa_enabled",  "BOOLEAN NOT NULL DEFAULT FALSE"),
                ("avatar_url",      "VARCHAR(500)"),
                ("auth_provider",   "VARCHAR(20)"),
                ("auth_provider_id","VARCHAR(255)"),
            ])

            # Sprint 1: OAuth accounts table
            _run(conn, """
                CREATE TABLE IF NOT EXISTS oauth_accounts (
                    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    provider         VARCHAR(20) NOT NULL,
                    provider_user_id VARCHAR(255) NOT NULL,
                    access_token     TEXT NOT NULL,
                    refresh_token    TEXT,
                    created_at       TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_oauth_accounts_user_id ON oauth_accounts (user_id)")
            _run(conn, "CREATE UNIQUE INDEX IF NOT EXISTS ix_oauth_accounts_provider ON oauth_accounts (provider, provider_user_id)")

            # Sprint 1: TOTP secrets table
            _run(conn, """
                CREATE TABLE IF NOT EXISTS totp_secrets (
                    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id          UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    encrypted_secret TEXT NOT NULL,
                    created_at       TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Sprint 1: Recovery codes table
            _run(conn, """
                CREATE TABLE IF NOT EXISTS recovery_codes (
                    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    code_hash  VARCHAR(255) NOT NULL,
                    is_used    BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_recovery_codes_user_id ON recovery_codes (user_id)")

            # Sprint 2: Profile versioning table
            _run(conn, """
                CREATE TABLE IF NOT EXISTS profile_versions (
                    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    version    INTEGER NOT NULL,
                    data       JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_profile_versions_user_id ON profile_versions (user_id)")
            _run(conn, "CREATE UNIQUE INDEX IF NOT EXISTS ix_profile_versions_user_version ON profile_versions (user_id, version)")

            # Sprint 2: Skill taxonomy table
            _run(conn, """
                CREATE TABLE IF NOT EXISTS skill_taxonomy (
                    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name     VARCHAR(100) NOT NULL UNIQUE,
                    category VARCHAR(50) NOT NULL,
                    aliases  JSONB DEFAULT '[]'
                )
            """)

            # Sprint 3: Scrape history table
            _run(conn, """
                CREATE TABLE IF NOT EXISTS scrape_history (
                    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    url             TEXT NOT NULL,
                    source_platform VARCHAR(50),
                    method_used     VARCHAR(20) NOT NULL,
                    success         VARCHAR(10) NOT NULL DEFAULT 'true',
                    fields_extracted INTEGER DEFAULT 0,
                    duration_ms     INTEGER,
                    error_message   TEXT,
                    created_at      TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_scrape_history_user_id ON scrape_history (user_id)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_scrape_history_platform ON scrape_history (source_platform)")

            _heal(conn, "jobs", [
                ("is_archived", "BOOLEAN NOT NULL DEFAULT FALSE"),
                ("import_id", "UUID REFERENCES job_imports(id) ON DELETE SET NULL"),
            ])
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_jobs_is_archived ON jobs (is_archived)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_jobs_import_id ON jobs (import_id)")

            _heal(conn, "job_imports", [
                ("errors", "JSON DEFAULT '[]'"),
                ("partial", "BOOLEAN NOT NULL DEFAULT FALSE"),
                ("source_data", "TEXT"),
            ])

            _heal(conn, "job_applications", [
                ("stage",           "INTEGER DEFAULT 0"),
                ("rejection_stage", "VARCHAR(30)"),
                ("general_notes",   "TEXT"),
                ("score",           "INTEGER"),
                ("score_reason",    "TEXT"),
                ("follow_up_at",    "TIMESTAMPTZ"),
                ("follow_up_note",  "VARCHAR(500)"),
            ])
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_job_applications_user_id ON job_applications (user_id)")
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_job_applications_user_status ON job_applications (user_id, status)")

            # Rename legacy "notes" → "general_notes" if the old column still exists
            _run(conn, """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='job_applications' AND column_name='notes'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='job_applications' AND column_name='general_notes'
                    ) THEN
                        ALTER TABLE job_applications RENAME COLUMN notes TO general_notes;
                    END IF;
                END $$
            """)

            _heal(conn, "resumes", [
                ("application_id", "UUID REFERENCES job_applications(id) ON DELETE CASCADE"),
            ])
            _run(conn, "CREATE INDEX IF NOT EXISTS ix_resumes_user_id ON resumes (user_id)")

            _heal(conn, "resume_versions", [
                ("template",        "VARCHAR(100)"),
                ("tailoring_notes", "TEXT"),
                ("score",           "INTEGER"),
                ("status",          "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
            ])

            _heal(conn, "cover_letters", [
                ("resume_id",  "UUID REFERENCES resumes(id) ON DELETE SET NULL"),
                ("job_id",     "UUID REFERENCES jobs(id) ON DELETE SET NULL"),
                ("structured", "JSONB"),
                ("tone",       "VARCHAR(50)"),
                ("template",   "VARCHAR(100)"),
                ("pdf_url",    "TEXT"),
                ("status",     "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
            ])

            _heal(conn, "job_analysis", [
                ("key_requirements", "JSONB"),
                ("seniority",        "VARCHAR(50)"),
                ("analysis_version", "VARCHAR(20) DEFAULT 'v1'"),
                ("status",           "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
                ("pros",             "JSONB NOT NULL DEFAULT '[]'"),
                ("cons",             "JSONB NOT NULL DEFAULT '[]'"),
                ("skills_gap",       "JSONB NOT NULL DEFAULT '[]'"),
            ])

            _heal(conn, "job_match_scores", [
                ("explanation", "TEXT"),
            ])
            _run(conn, "CREATE UNIQUE INDEX IF NOT EXISTS uq_match_scores_user_job ON job_match_scores (user_id, job_id)")

    except Exception as e:
        logger.warning("schema_drift_heal_skipped", extra={"error": str(e)})

    logger.info("app_started", event_type="startup")
    yield
    logger.info("app_stopped", event_type="shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SiraFit API - Career automation platform",
    lifespan=lifespan,
)

# Middleware registration order note:
# Starlette executes middleware in REVERSE registration order — the last
# add_middleware call becomes the outermost wrapper and therefore runs first
# on every incoming request (including OPTIONS preflights).
#
# Desired execution order (outermost → innermost):
#   MetricsMiddleware → CORSMiddleware → SecurityHeadersMiddleware
#   → RateLimitMiddleware → RateLimitHeaderMiddleware
#   → RequestTimingMiddleware → GZipMiddleware → route handler
#
# Register in reverse order below.

# GZip compression middleware for payloads > 1KB (innermost)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request timing middleware
app.add_middleware(RequestTimingMiddleware)

# Rate limit header middleware
app.add_middleware(RateLimitHeaderMiddleware)

# Redis-backed rate limiting (no-op outside production)
app.add_middleware(RateLimitMiddleware)

# Security headers — applied after CORS resolves
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware — handles OPTIONS preflights before security headers can reject them
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics (outermost — counts every request including preflights)
app.add_middleware(MetricsMiddleware)

# Include Prometheus metrics endpoint
app.include_router(metrics_router, tags=["metrics"])

# Health checks at /health/* for Docker/k8s probes (live, ready) and the
# same router also mounted under /api/v1/* via api_router for the SPA
# (which calls /api/v1/health/status). Both prefixes share the same routes.
app.include_router(health_router, prefix="/health", tags=["health"])

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["api"])


@app.exception_handler(OperationalError)
@app.exception_handler(SQLATimeoutError)
async def db_unavailable_handler(request: Request, exc: Exception):
    """Return 503 when the DB pool is exhausted or unreachable.

    Pool exhaustion / connection timeouts are transient and retryable; surfacing
    them as 503 (with Retry-After) lets clients and load balancers back off,
    instead of the generic 500 from the catch-all handler.
    """
    logger.warning("db_unavailable", path=request.url.path, method=request.method, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database temporarily unavailable. Please retry shortly."},
        headers={"Retry-After": "10"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to mask internal errors."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "A system error occurred. Please try again later."},
    )
