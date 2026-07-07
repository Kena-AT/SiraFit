"""add cover_letters table

Revision ID: add_cover_letters_table
Revises: add_resume_versions_table
Create Date: 2026-07-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_cover_letters_table'
down_revision = 'add_resume_versions_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cover_letters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('structured', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tone', sa.String(50), nullable=True),
        sa.Column('template', sa.String(100), nullable=True),
        sa.Column('pdf_url', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_cover_letters_user_id', 'cover_letters', ['user_id'])
    op.create_index('ix_cover_letters_job_id', 'cover_letters', ['job_id'])
    op.create_index('ix_cover_letters_resume_id', 'cover_letters', ['resume_id'])


def downgrade():
    op.drop_index('ix_cover_letters_resume_id', table_name='cover_letters')
    op.drop_index('ix_cover_letters_job_id', table_name='cover_letters')
    op.drop_index('ix_cover_letters_user_id', table_name='cover_letters')
    op.drop_table('cover_letters')
