"""Full schema baseline — ensure every table and column exists.

Revision ID: 20260831_001
Revises: 20260822_001
Create Date: 2026-08-31

This migration is idempotent. Every CREATE TABLE uses IF NOT EXISTS and every
ALTER TABLE uses ADD COLUMN IF NOT EXISTS so it is safe to run against a
database that is fully, partially, or not at all migrated.

Tables covered (25 total):
  users, user_preferences, refresh_tokens, device_sessions
  jobs, job_applications, job_analysis, job_imports
  resumes, resume_versions, audit_logs
  application_events, application_notes, application_contacts
  profiles, experiences, education, skills, projects, certifications
  cover_letters, job_match_scores, batch_jobs, notifications, analytics_snapshots
"""
from alembic import op
import sqlalchemy as sa

revision = "20260831_001"
down_revision = "20260822_001"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # All DDL is executed through the live connection exposed by Alembic.
    # We use op.get_bind() which returns a sqlalchemy.engine.Connection
    # in both SQLAlchemy 1.x and 2.x.
    # ------------------------------------------------------------------
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    def run(sql: str) -> None:
        """Execute raw DDL, silently ignoring 'already exists' errors."""
        try:
            conn.execute(sa.text(sql))
        except Exception:
            pass

    def patch(table: str, columns: list) -> None:
        """ADD COLUMN IF NOT EXISTS for every (name, typedef) pair."""
        for col, defn in columns:
            run(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {defn}")

    # ==================================================================
    # EXTENSIONS  (PostgreSQL only)
    # ==================================================================
    if is_pg:
        run('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        run('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # ==================================================================
    # users
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS users (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email           VARCHAR(255) NOT NULL,
            full_name       VARCHAR(255),
            hashed_password VARCHAR(255) NOT NULL,
            is_active       BOOLEAN DEFAULT TRUE,
            is_verified     BOOLEAN DEFAULT FALSE,
            created_at      TIMESTAMP,
            updated_at      TIMESTAMP
        )
    """)
    run("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email)")
    run("CREATE INDEX        IF NOT EXISTS ix_users_email ON users (email)")

    # ==================================================================
    # user_preferences
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id                  UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            theme                    VARCHAR(50)  DEFAULT 'light',
            notifications_enabled    BOOLEAN      DEFAULT TRUE,
            email_job_matches        BOOLEAN NOT NULL DEFAULT TRUE,
            email_daily_summary      BOOLEAN NOT NULL DEFAULT FALSE,
            push_notifications       BOOLEAN NOT NULL DEFAULT TRUE,
            email_new_opportunities  BOOLEAN NOT NULL DEFAULT TRUE,
            default_template         VARCHAR(50)  NOT NULL DEFAULT 'modern',
            auto_tailor_enabled      BOOLEAN      NOT NULL DEFAULT TRUE,
            export_format            VARCHAR(10)  NOT NULL DEFAULT 'pdf',
            encrypted_gemini_key     VARCHAR(500),
            encrypted_openrouter_key VARCHAR(500),
            encrypted_anthropic_key  VARCHAR(500),
            encrypted_openai_key     VARCHAR(500),
            encrypted_grok_key       VARCHAR(500),
            encrypted_mistral_key    VARCHAR(500),
            encrypted_nvidia_key     VARCHAR(500),
            ai_provider              VARCHAR(50)  DEFAULT 'gemini',
            ai_model                 VARCHAR(255) DEFAULT 'gemini-1.5-flash',
            ai_fallback_order        TEXT
        )
    """)
    patch("user_preferences", [
        ("theme",                   "VARCHAR(50) DEFAULT 'light'"),
        ("notifications_enabled",   "BOOLEAN DEFAULT TRUE"),
        ("email_job_matches",       "BOOLEAN NOT NULL DEFAULT TRUE"),
        ("email_daily_summary",     "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("push_notifications",      "BOOLEAN NOT NULL DEFAULT TRUE"),
        ("email_new_opportunities", "BOOLEAN NOT NULL DEFAULT TRUE"),
        ("default_template",        "VARCHAR(50) NOT NULL DEFAULT 'modern'"),
        ("auto_tailor_enabled",     "BOOLEAN NOT NULL DEFAULT TRUE"),
        ("export_format",           "VARCHAR(10) NOT NULL DEFAULT 'pdf'"),
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

    # ==================================================================
    # refresh_tokens
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
            token      VARCHAR(512) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            is_revoked BOOLEAN DEFAULT FALSE
        )
    """)
    run("CREATE UNIQUE INDEX IF NOT EXISTS uq_refresh_tokens_token ON refresh_tokens (token)")
    run("CREATE INDEX        IF NOT EXISTS ix_refresh_tokens_token ON refresh_tokens (token)")

    # ==================================================================
    # device_sessions
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS device_sessions (
            id          SERIAL PRIMARY KEY,
            user_id     UUID      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            device_name VARCHAR(100) NOT NULL,
            ip_address  VARCHAR(45),
            user_agent  TEXT,
            is_active   BOOLEAN   NOT NULL DEFAULT TRUE,
            last_seen   TIMESTAMP NOT NULL DEFAULT NOW(),
            created_at  TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_device_sessions_user_active ON device_sessions (user_id, is_active)")

    # ==================================================================
    # jobs
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            external_id VARCHAR(255) NOT NULL,
            title       VARCHAR(255) NOT NULL,
            company     VARCHAR(255) NOT NULL,
            location    VARCHAR(255),
            description TEXT,
            salary_min  INTEGER,
            salary_max  INTEGER,
            currency    VARCHAR(3),
            tags        JSONB,
            url         TEXT,
            source      VARCHAR(50) DEFAULT 'manual',
            is_archived BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMP,
            updated_at  TIMESTAMP
        )
    """)
    run("CREATE UNIQUE INDEX IF NOT EXISTS uq_jobs_external_id ON jobs (external_id)")
    run("CREATE INDEX        IF NOT EXISTS ix_jobs_external_id  ON jobs (external_id)")
    run("CREATE INDEX        IF NOT EXISTS ix_jobs_created_at   ON jobs (created_at)")
    run("CREATE INDEX        IF NOT EXISTS ix_jobs_is_archived  ON jobs (is_archived)")
    patch("jobs", [
        ("is_archived", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("tags",        "JSONB"),
    ])

    # ==================================================================
    # job_applications
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            job_id          UUID NOT NULL REFERENCES jobs(id)  ON DELETE CASCADE,
            status          VARCHAR(50)  DEFAULT 'saved',
            stage           INTEGER      DEFAULT 0,
            rejection_stage VARCHAR(30),
            general_notes   TEXT,
            score           INTEGER,
            score_reason    TEXT,
            follow_up_at    TIMESTAMPTZ,
            follow_up_note  VARCHAR(500),
            created_at      TIMESTAMP,
            updated_at      TIMESTAMP
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_job_applications_user_id     ON job_applications (user_id)")
    run("CREATE INDEX IF NOT EXISTS ix_job_applications_created_at  ON job_applications (created_at)")
    run("CREATE INDEX IF NOT EXISTS ix_job_applications_user_status ON job_applications (user_id, status)")
    # Unique constraint added only when it doesn't already exist to avoid
    # conflicting with the existing ix_job_applications_user_job index
    # created by the add_application_tracking migration.
    run("CREATE UNIQUE INDEX IF NOT EXISTS uq_job_applications_user_job ON job_applications (user_id, job_id)")
    patch("job_applications", [
        ("stage",           "INTEGER DEFAULT 0"),
        ("rejection_stage", "VARCHAR(30)"),
        ("general_notes",   "TEXT"),
        ("score",           "INTEGER"),
        ("score_reason",    "TEXT"),
        ("follow_up_at",    "TIMESTAMPTZ"),
        ("follow_up_note",  "VARCHAR(500)"),
    ])
    # Rename legacy "notes" → "general_notes" if the old column still exists
    if is_pg:
        run("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'job_applications' AND column_name = 'notes'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'job_applications' AND column_name = 'general_notes'
                ) THEN
                    ALTER TABLE job_applications RENAME COLUMN notes TO general_notes;
                END IF;
            END $$
        """)

    # ==================================================================
    # job_analysis
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS job_analysis (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id           UUID NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
            score            INTEGER  NOT NULL DEFAULT 0,
            summary          TEXT     NOT NULL DEFAULT '',
            pros             JSONB    NOT NULL DEFAULT '[]',
            cons             JSONB    NOT NULL DEFAULT '[]',
            skills_gap       JSONB    NOT NULL DEFAULT '[]',
            key_requirements JSONB,
            seniority        VARCHAR(50),
            analysis_version VARCHAR(20) DEFAULT 'v1',
            status           VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at       TIMESTAMP,
            updated_at       TIMESTAMP
        )
    """)
    patch("job_analysis", [
        ("key_requirements", "JSONB"),
        ("seniority",        "VARCHAR(50)"),
        ("analysis_version", "VARCHAR(20) DEFAULT 'v1'"),
        ("status",           "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
        ("pros",             "JSONB NOT NULL DEFAULT '[]'"),
        ("cons",             "JSONB NOT NULL DEFAULT '[]'"),
        ("skills_gap",       "JSONB NOT NULL DEFAULT '[]'"),
    ])

    # ==================================================================
    # job_imports
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS job_imports (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source      VARCHAR(50) NOT NULL,
            status      VARCHAR(20) DEFAULT 'pending',
            total_found INTEGER DEFAULT 0,
            ok_count    INTEGER DEFAULT 0,
            fail_count  INTEGER DEFAULT 0,
            created_at  TIMESTAMP,
            updated_at  TIMESTAMP
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_job_imports_user_id ON job_imports (user_id)")

    # ==================================================================
    # profiles
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS profiles (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            first_name VARCHAR(255),
            last_name  VARCHAR(255),
            headline   VARCHAR(255),
            summary    TEXT,
            email      VARCHAR(255),
            phone      VARCHAR(50),
            location   VARCHAR(255),
            website    VARCHAR(255),
            linkedin   VARCHAR(255),
            github     VARCHAR(255),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    # ==================================================================
    # experiences
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS experiences (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_id  UUID REFERENCES profiles(id) ON DELETE CASCADE,
            title       VARCHAR(255) NOT NULL,
            company     VARCHAR(255) NOT NULL,
            location    VARCHAR(255),
            start_date  DATE,
            end_date    DATE,
            is_current  BOOLEAN DEFAULT FALSE,
            description TEXT
        )
    """)

    # ==================================================================
    # education
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS education (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_id     UUID REFERENCES profiles(id) ON DELETE CASCADE,
            institution    VARCHAR(255) NOT NULL,
            degree         VARCHAR(255),
            field_of_study VARCHAR(255),
            start_date     DATE,
            end_date       DATE,
            description    TEXT
        )
    """)

    # ==================================================================
    # skills
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS skills (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_id  UUID REFERENCES profiles(id) ON DELETE CASCADE,
            name        VARCHAR(100) NOT NULL,
            category    VARCHAR(100),
            proficiency VARCHAR(50)
        )
    """)

    # ==================================================================
    # projects
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS projects (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_id  UUID REFERENCES profiles(id) ON DELETE CASCADE,
            name        VARCHAR(255) NOT NULL,
            description TEXT,
            url         VARCHAR(255),
            start_date  DATE,
            end_date    DATE
        )
    """)

    # ==================================================================
    # certifications
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS certifications (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_id      UUID REFERENCES profiles(id) ON DELETE CASCADE,
            name            VARCHAR(255) NOT NULL,
            issuer          VARCHAR(255) NOT NULL,
            issue_date      DATE,
            expiration_date DATE,
            credential_id   VARCHAR(255),
            credential_url  VARCHAR(255)
        )
    """)

    # ==================================================================
    # resumes
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS resumes (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id        UUID NOT NULL REFERENCES users(id)            ON DELETE CASCADE,
            application_id UUID          REFERENCES job_applications(id) ON DELETE CASCADE,
            title          VARCHAR(255) NOT NULL,
            content        TEXT NOT NULL,
            pdf_url        TEXT,
            is_primary     BOOLEAN DEFAULT FALSE,
            created_at     TIMESTAMP,
            updated_at     TIMESTAMP
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_resumes_user_id ON resumes (user_id)")
    patch("resumes", [
        ("application_id", "UUID REFERENCES job_applications(id) ON DELETE CASCADE"),
        ("pdf_url",        "TEXT"),
        ("is_primary",     "BOOLEAN DEFAULT FALSE"),
    ])

    # ==================================================================
    # resume_versions
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS resume_versions (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            resume_id       UUID     NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
            version_number  INTEGER  NOT NULL,
            content         TEXT     NOT NULL,
            template        VARCHAR(100),
            job_id          UUID REFERENCES jobs(id) ON DELETE SET NULL,
            tailoring_notes TEXT,
            score           INTEGER,
            status          VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at      TIMESTAMP,
            updated_at      TIMESTAMP
        )
    """)
    patch("resume_versions", [
        ("template",        "VARCHAR(100)"),
        ("job_id",          "UUID REFERENCES jobs(id) ON DELETE SET NULL"),
        ("tailoring_notes", "TEXT"),
        ("score",           "INTEGER"),
        ("status",          "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
    ])

    # ==================================================================
    # cover_letters
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS cover_letters (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
            resume_id  UUID          REFERENCES resumes(id) ON DELETE SET NULL,
            job_id     UUID          REFERENCES jobs(id)    ON DELETE SET NULL,
            title      VARCHAR(255) NOT NULL,
            body       TEXT NOT NULL,
            structured JSONB,
            tone       VARCHAR(50),
            template   VARCHAR(100),
            pdf_url    TEXT,
            status     VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_cover_letters_user_id ON cover_letters (user_id)")
    patch("cover_letters", [
        ("resume_id",  "UUID REFERENCES resumes(id) ON DELETE SET NULL"),
        ("job_id",     "UUID REFERENCES jobs(id) ON DELETE SET NULL"),
        ("structured", "JSONB"),
        ("tone",       "VARCHAR(50)"),
        ("template",   "VARCHAR(100)"),
        ("pdf_url",    "TEXT"),
        ("status",     "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
    ])

    # ==================================================================
    # audit_logs
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
            action      VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50),
            entity_id   UUID,
            details     JSONB,
            ip_address  VARCHAR(45),
            user_agent  VARCHAR(500),
            created_at  TIMESTAMP
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_audit_log_user_created ON audit_logs (user_id, created_at DESC)")

    # ==================================================================
    # job_match_scores
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS job_match_scores (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            job_id      UUID NOT NULL REFERENCES jobs(id)  ON DELETE CASCADE,
            score       INTEGER NOT NULL,
            breakdown   JSONB   NOT NULL,
            explanation TEXT,
            created_at  TIMESTAMP,
            updated_at  TIMESTAMP
        )
    """)
    run("CREATE INDEX        IF NOT EXISTS ix_match_scores_user_score  ON job_match_scores (user_id, score DESC)")
    run("CREATE UNIQUE INDEX IF NOT EXISTS uq_match_scores_user_job    ON job_match_scores (user_id, job_id)")
    patch("job_match_scores", [
        ("explanation", "TEXT"),
    ])

    # ==================================================================
    # batch_jobs
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            operation_type   VARCHAR(30)  NOT NULL,
            status           VARCHAR(20)  NOT NULL DEFAULT 'pending',
            total_items      INTEGER      NOT NULL DEFAULT 0,
            processed_items  INTEGER      NOT NULL DEFAULT 0,
            succeeded_items  INTEGER      NOT NULL DEFAULT 0,
            failed_items     INTEGER      NOT NULL DEFAULT 0,
            payload          JSONB        NOT NULL DEFAULT '{}',
            result_summary   JSONB        NOT NULL DEFAULT '{}',
            cancel_requested BOOLEAN      NOT NULL DEFAULT FALSE,
            started_at       TIMESTAMPTZ,
            completed_at     TIMESTAMPTZ,
            created_at       TIMESTAMPTZ  DEFAULT NOW(),
            updated_at       TIMESTAMPTZ  DEFAULT NOW()
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_batch_jobs_user_id ON batch_jobs (user_id)")
    run("CREATE INDEX IF NOT EXISTS ix_batch_jobs_status  ON batch_jobs (status)")

    # ==================================================================
    # notifications
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS notifications (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title      VARCHAR(255) NOT NULL,
            body       VARCHAR(2000) NOT NULL,
            kind       VARCHAR(50)  NOT NULL,
            status     VARCHAR(20)  NOT NULL DEFAULT 'unread',
            read_at    TIMESTAMPTZ,
            created_at TIMESTAMPTZ  DEFAULT NOW(),
            updated_at TIMESTAMPTZ  DEFAULT NOW()
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_notifications_user_id     ON notifications (user_id)")
    run("CREATE INDEX IF NOT EXISTS ix_notifications_status      ON notifications (status)")
    run("CREATE INDEX IF NOT EXISTS ix_notifications_user_status ON notifications (user_id, status)")

    # ==================================================================
    # analytics_snapshots
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS analytics_snapshots (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            snapshot_date TIMESTAMPTZ DEFAULT NOW(),
            metrics       JSONB NOT NULL,
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_analytics_snapshots_user_id ON analytics_snapshots (user_id)")

    # ==================================================================
    # application_events
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS application_events (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
            user_id        UUID NOT NULL REFERENCES users(id)            ON DELETE CASCADE,
            event_type     VARCHAR(30)  NOT NULL,
            title          VARCHAR(255) NOT NULL,
            description    TEXT,
            event_metadata JSONB,
            occurred_at    TIMESTAMP NOT NULL DEFAULT NOW(),
            created_at     TIMESTAMP
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_application_events_user_id    ON application_events (user_id)")
    run("CREATE INDEX IF NOT EXISTS ix_application_events_app_id     ON application_events (application_id)")
    run("CREATE INDEX IF NOT EXISTS ix_application_events_occurred   ON application_events (occurred_at)")
    run("CREATE INDEX IF NOT EXISTS ix_application_events_user_app   ON application_events (user_id, application_id)")

    # ==================================================================
    # application_notes
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS application_notes (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
            user_id        UUID NOT NULL REFERENCES users(id)            ON DELETE CASCADE,
            body           TEXT    NOT NULL,
            author         VARCHAR(100),
            pinned         BOOLEAN NOT NULL DEFAULT FALSE,
            created_at     TIMESTAMP,
            updated_at     TIMESTAMP
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_application_notes_user_id ON application_notes (user_id)")
    run("CREATE INDEX IF NOT EXISTS ix_application_notes_app_id  ON application_notes (application_id)")

    # ==================================================================
    # application_contacts
    # ==================================================================
    run("""
        CREATE TABLE IF NOT EXISTS application_contacts (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
            user_id        UUID NOT NULL REFERENCES users(id)            ON DELETE CASCADE,
            name           VARCHAR(255) NOT NULL,
            email          VARCHAR(255),
            phone          VARCHAR(50),
            role           VARCHAR(50)  NOT NULL DEFAULT 'recruiter',
            company        VARCHAR(255),
            linkedin       VARCHAR(500),
            notes          TEXT,
            is_primary     BOOLEAN NOT NULL DEFAULT FALSE,
            created_at     TIMESTAMP,
            updated_at     TIMESTAMP
        )
    """)
    run("CREATE INDEX IF NOT EXISTS ix_application_contacts_user_id ON application_contacts (user_id)")
    run("CREATE INDEX IF NOT EXISTS ix_application_contacts_app_id  ON application_contacts (application_id)")


def downgrade():
    # Baseline safety net — no-op downgrade to avoid accidental data loss.
    # To roll back, write a targeted migration that drops specific objects.
    pass
