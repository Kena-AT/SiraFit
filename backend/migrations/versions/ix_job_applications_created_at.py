"""add index on job_applications.created_at for landing stats query"""
from alembic import op
import sqlalchemy as sa

revision = "ix_job_applications_created_at"
down_revision = "add_cover_letters_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_job_applications_created_at", "job_applications", ["created_at"])


def downgrade():
    op.drop_index("ix_job_applications_created_at", table_name="job_applications")