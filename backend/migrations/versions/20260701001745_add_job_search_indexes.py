"""add job search indexes

Revision ID: 20260701001745
Revises: add_remaining_tables
Create Date: 2026-07-01 00:17:45

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260701001745'
down_revision = 'remaining_tables_001'
branch_label = None
depends_on = None


def upgrade():
    # Add indexes for better search and filter performance
    op.create_index('ix_jobs_title', 'jobs', ['title'])
    op.create_index('ix_jobs_company', 'jobs', ['company'])
    op.create_index('ix_jobs_location', 'jobs', ['location'])
    op.create_index('ix_jobs_source', 'jobs', ['source'])
    op.create_index('ix_jobs_created_at', 'jobs', ['created_at'])
    
    # GIN index for tags array (PostgreSQL specific)
    op.execute('CREATE INDEX ix_jobs_tags ON jobs USING GIN (tags)')


def downgrade():
    op.drop_index('ix_jobs_tags', table_name='jobs')
    op.drop_index('ix_jobs_created_at', table_name='jobs')
    op.drop_index('ix_jobs_source', table_name='jobs')
    op.drop_index('ix_jobs_location', table_name='jobs')
    op.drop_index('ix_jobs_company', table_name='jobs')
    op.drop_index('ix_jobs_title', table_name='jobs')
