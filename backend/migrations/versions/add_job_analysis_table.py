"""add job analysis table

Revision ID: add_job_analysis_table
Revises: 20260701001745
Create Date: 2026-07-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_job_analysis_table'
down_revision = '20260701001745'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('job_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('pros', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('cons', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('skills_gap', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )

def downgrade():
    op.drop_table('job_analysis')
