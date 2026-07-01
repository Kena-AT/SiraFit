"""add job_match_scores table

Revision ID: add_job_match_scores
Revises: add_job_analysis_table
Create Date: 2026-07-01 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_job_match_scores'
down_revision = 'add_job_analysis_table'
branch_labels = None
depends_on = None

def upgrade():
    op.execute('CREATE TABLE IF NOT EXISTS job_match_scores ('
        'id UUID NOT NULL, '
        'user_id UUID NOT NULL, '
        'job_id UUID NOT NULL, '
        'score INTEGER NOT NULL, '
        'breakdown JSON NOT NULL, '
        'explanation TEXT, '
        'created_at TIMESTAMP WITHOUT TIME ZONE, '
        'updated_at TIMESTAMP WITHOUT TIME ZONE, '
        'PRIMARY KEY (id), '
        'FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, '
        'FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE'
    ')')

def downgrade():
    op.drop_table('job_match_scores')
