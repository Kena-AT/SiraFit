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
    op.add_column(
        "jobs",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_jobs_is_archived", "jobs", ["is_archived"])


def downgrade():
    op.drop_index("ix_jobs_is_archived", table_name="jobs")
    op.drop_column("jobs", "is_archived")
