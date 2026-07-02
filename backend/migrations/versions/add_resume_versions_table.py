"""add resume_versions table

Revision ID: add_resume_versions_table
Revises: add_job_match_scores
Create Date: 2026-07-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_resume_versions_table'
down_revision = 'add_job_match_scores'
branch_labels = None
depends_on = None


def upgrade():
    # Create resume_versions table
    op.create_table(
        'resume_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('template', sa.String(100), nullable=True),  # "minimal", "technical", "modern", "corporate", "compact"
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column(' tailoring_notes', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),  # ATS readiness score
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # pending, processing, completed, failed
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', 'version_number', name='uq_resume_version')
    )

    # Add indexes for common queries
    op.create_index('ix_resume_versions_resume_id', 'resume_versions', ['resume_id'])
    op.create_index('ix_resume_versions_job_id', 'resume_versions', ['job_id'])


    # Add columns to resumes table for generation state
    op.add_column('resumes', sa.Column('generation_status', sa.String(20), nullable=True, server_default='idle'))
    op.add_column('resumes', sa.Column('generation_log', sa.Text(), nullable=True))


def downgrade():
    op.drop_index('ix_resume_versions_job_id', table_name='resume_versions')
    op.drop_index('ix_resume_versions_resume_id', table_name='resume_versions')
    op.drop_table('resume_versions')
    op.drop_column('resumes', 'generation_status')
    op.drop_column('resumes', 'generation_log')