"""Add composite indexes and pg_trgm for ILIKE performance

Revision ID: 20260820_001
Revises: 20260812_001
Create Date: 2026-08-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260820_001"
down_revision = "6f076c0ee183"
branch_labels = None
depends_on = None


def upgrade():
    # Enable pg_trgm extension for trigram-based ILIKE acceleration
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Composite index for common filter combination: is_archived + created_at
    # Used in list_jobs with default sorting by created_at
    op.create_index(
        "ix_jobs_archived_created",
        "jobs",
        ["is_archived", "created_at"],
    )

    # Composite index for source + is_archived
    # Used when filtering by source
    op.create_index(
        "ix_jobs_source_archived",
        "jobs",
        ["source", "is_archived"],
    )

    # Composite index for company + is_archived
    # Used when filtering by company
    op.create_index(
        "ix_jobs_company_archived",
        "jobs",
        ["company", "is_archived"],
    )

    # Composite index for location + is_archived
    # Used when filtering by location
    op.create_index(
        "ix_jobs_location_archived",
        "jobs",
        ["location", "is_archived"],
    )

    # GIN indexes using pg_trgm for ILIKE queries on text columns
    # These accelerate substring/pattern searches (ILIKE '%term%')
    op.execute("CREATE INDEX ix_jobs_title_trgm ON jobs USING GIN (title gin_trgm_ops)")
    op.execute("CREATE INDEX ix_jobs_company_trgm ON jobs USING GIN (company gin_trgm_ops)")
    op.execute("CREATE INDEX ix_jobs_description_trgm ON jobs USING GIN (description gin_trgm_ops)")
    op.execute("CREATE INDEX ix_jobs_location_trgm ON jobs USING GIN (location gin_trgm_ops)")


def downgrade():
    # Drop GIN trigram indexes
    op.execute("DROP INDEX IF EXISTS ix_jobs_location_trgm")
    op.execute("DROP INDEX IF EXISTS ix_jobs_description_trgm")
    op.execute("DROP INDEX IF EXISTS ix_jobs_company_trgm")
    op.execute("DROP INDEX IF EXISTS ix_jobs_title_trgm")

    # Drop composite indexes
    op.drop_index("ix_jobs_location_archived", table_name="jobs")
    op.drop_index("ix_jobs_company_archived", table_name="jobs")
    op.drop_index("ix_jobs_source_archived", table_name="jobs")
    op.drop_index("ix_jobs_archived_created", table_name="jobs")

    # Note: We don't drop pg_trgm extension as it may be used elsewhere