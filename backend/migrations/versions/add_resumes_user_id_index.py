"""Add index on user_id in resumes table

Revision ID: add_resumes_user_id_index
Revises: add_job_is_archived_and_indexes
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "add_resumes_user_id_index"
down_revision = "add_job_is_archived_and_indexes"
branch_labels = None
depends_on = None


def upgrade():
    # Index on resumes.user_id to speed up queries filtering by user
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])


def downgrade():
    op.drop_index("ix_resumes_user_id", table_name="resumes")
