add job_applications created_at index

Revision ID: add_job_applications_created_at_index
Revises: add_cover_letters_table
Create Date: 2026-07-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_job_applications_created_at_index'
down_revision = 'add_cover_letters_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_job_applications_created_at', 'job_applications', ['created_at'])


def downgrade():
    op.drop_index('ix_job_applications_created_at', table_name='job_applications')