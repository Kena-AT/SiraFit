"""Add is_archived to jobs and user_id index to job_applications

Revision ID: add_job_is_archived_and_indexes
Revises: ix_job_applications_created_at
Create Date: 2026-08-13

"""
from alembic import op
import sqlalchemy as sa

revision = "add_job_is_archived_and_indexes"
down_revision = "ix_job_applications_created_at"
branch_labels = None
depends_on = None


def upgrade():
    # Add soft-delete flag to jobs
    op.add_column(
        "jobs",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_jobs_is_archived", "jobs", ["is_archived"])

    # Index on job_applications.user_id to speed up board & follow-up queries
    op.create_index("ix_job_applications_user_id", "job_applications", ["user_id"])


def downgrade():
    op.drop_index("ix_job_applications_user_id", table_name="job_applications")
    op.drop_index("ix_jobs_is_archived", table_name="jobs")
    op.drop_column("jobs", "is_archived")
