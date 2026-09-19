"""Add is_archived column to jobs table

Revision ID: 20260812_001
Revises: 20260730_100700
Create Date: 2026-08-12

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260812_001"
down_revision = "20260730_100700"
branch_labels = None
depends_on = None


def upgrade():
    # is_archived and ix_jobs_is_archived are already introduced in
    # add_job_is_archived_and_indexes on the parallel branch merging into 6f076c0ee183.
    pass


def downgrade():
    pass
