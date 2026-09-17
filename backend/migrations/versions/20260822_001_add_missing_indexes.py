"""Add missing indexes for the rankings / follow-ups / notifications hot paths.

Revision ID: 20260822_001
Revises: 20260820_001
Create Date: 2026-08-22

Targets the query patterns flagged in the audit:
  - dashboard stats: job_applications (user_id, status) and (user_id, follow_up_at)
  - ranked/match listings: job_match_scores (user_id, score DESC)
  - audit log feed: audit_logs (user_id, created_at DESC)
  - notifications list: notifications (user_id, status)

Indexes are built CONCURRENTLY so they don't lock the underlying tables in
production. CREATE INDEX CONCURRENTLY must run outside a transaction block,
hence the autocommit_block() wrapper. Postgres-only — other dialects (e.g.
SQLite used by the test suite, which builds schema via metadata.create_all)
are intentionally skipped.
"""
from alembic import op
import sqlalchemy as sa


revision = "20260822_001"
down_revision = "20260820_001"
branch_labels = None
depends_on = None


# (index_name, table, postgres_ddl)
_INDEXES = [
    (
        "ix_job_apps_user_status",
        "job_applications",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_job_apps_user_status "
        "ON job_applications (user_id, status)",
    ),
    (
        "ix_job_apps_user_followup",
        "job_applications",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_job_apps_user_followup "
        "ON job_applications (user_id, follow_up_at) "
        "WHERE follow_up_at IS NOT NULL",
    ),
    (
        "ix_match_scores_user_score",
        "job_match_scores",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_match_scores_user_score "
        "ON job_match_scores (user_id, score DESC)",
    ),
    (
        "ix_audit_log_user_created",
        "audit_logs",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_audit_log_user_created "
        "ON audit_logs (user_id, created_at DESC)",
    ),
    (
        "ix_notifications_user_status",
        "notifications",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_notifications_user_status "
        "ON notifications (user_id, status)",
    ),
]


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # CONCURRENTLY is Postgres-only; the test suite builds its schema via
        # SQLAlchemy metadata.create_all and never runs Alembic.
        return
    with op.get_context().autocommit_block():
        for _name, _table, ddl in _INDEXES:
            op.execute(sa.text(ddl))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    with op.get_context().autocommit_block():
        for name, _table, _ddl in _INDEXES:
            op.execute(sa.text(f"DROP INDEX CONCURRENTLY IF EXISTS {name}"))
