"""add resume version lineage and application tracking

Revision ID: 20260917_007
Revises: 20260917_006
Create Date: 2026-09-17 19:45:00.000000

Sprint 9:
- Add parent_version_id, source_type to resume_versions
- Add resume_version_id to job_applications
- Backfill source_type on resume_versions (lowest version or NULL job_id as 'base', others as 'tailored')
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260917_007"
down_revision = "20260917_006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add parent_version_id and source_type to resume_versions
    op.add_column(
        "resume_versions",
        sa.Column(
            "parent_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resume_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_resume_versions_parent_version_id",
        "resume_versions",
        ["parent_version_id"],
    )

    op.add_column(
        "resume_versions",
        sa.Column(
            "source_type",
            sa.String(length=20),
            nullable=True,
        ),
    )

    # 2. Backfill source_type:
    # Existing versions with job_id are tailored; versions without job_id (or first version) are base
    op.execute(
        """
        UPDATE resume_versions
        SET source_type = CASE
            WHEN job_id IS NOT NULL THEN 'tailored'
            ELSE 'base'
        END
        WHERE source_type IS NULL
        """
    )
    # Ensure at least one base per resume if any versions exist
    op.execute(
        """
        UPDATE resume_versions
        SET source_type = 'base'
        WHERE id IN (
            SELECT rv.id FROM resume_versions rv
            INNER JOIN (
                SELECT resume_id, MIN(version_number) as min_v
                FROM resume_versions
                GROUP BY resume_id
            ) first_v ON rv.resume_id = first_v.resume_id AND rv.version_number = first_v.min_v
            WHERE NOT EXISTS (
                SELECT 1 FROM resume_versions b WHERE b.resume_id = rv.resume_id AND b.source_type = 'base'
            )
        )
        """
    )
    # Default any remaining to 'tailored'
    op.execute("UPDATE resume_versions SET source_type = 'tailored' WHERE source_type IS NULL")

    op.alter_column("resume_versions", "source_type", nullable=False, server_default="base")

    # 3. Add resume_version_id to job_applications
    op.add_column(
        "job_applications",
        sa.Column(
            "resume_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resume_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_job_applications_resume_version_id",
        "job_applications",
        ["resume_version_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_job_applications_resume_version_id", table_name="job_applications")
    op.drop_column("job_applications", "resume_version_id")

    op.drop_index("ix_resume_versions_parent_version_id", table_name="resume_versions")
    op.drop_column("resume_versions", "source_type")
    op.drop_column("resume_versions", "parent_version_id")
