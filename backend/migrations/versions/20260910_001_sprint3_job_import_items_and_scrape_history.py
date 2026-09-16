"""Add job_import_items, scrape_history, and import_id linkage (Sprint 3)

Revision ID: 20260910_001
Revises: 20260901_001, 20260909_import_status
Create Date: 2026-09-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '20260910_001'
down_revision: Union[str, Sequence[str], None] = ('20260901_001', '20260909_import_status')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add import_id and is_archived to jobs if not present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    jobs_cols = [c['name'] for c in inspector.get_columns('jobs')]

    if 'import_id' not in jobs_cols:
        op.add_column(
            'jobs',
            sa.Column(
                'import_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('job_imports.id', ondelete='SET NULL'),
                nullable=True,
            )
        )
        op.create_index('ix_jobs_import_id', 'jobs', ['import_id'])

    if 'is_archived' not in jobs_cols:
        op.add_column(
            'jobs',
            sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False)
        )
        op.create_index('ix_jobs_is_archived', 'jobs', ['is_archived'])

    # 2. Add partial, errors, source_data to job_imports if missing
    imports_cols = [c['name'] for c in inspector.get_columns('job_imports')]
    if 'partial' not in imports_cols:
        op.add_column(
            'job_imports',
            sa.Column('partial', sa.Boolean(), server_default='false', nullable=False)
        )
    if 'errors' not in imports_cols:
        op.add_column(
            'job_imports',
            sa.Column('errors', sa.JSON(), server_default='[]', nullable=True)
        )
    if 'source_data' not in imports_cols:
        op.add_column(
            'job_imports',
            sa.Column('source_data', sa.Text(), nullable=True)
        )

    # 3. Create job_import_items table
    tables = inspector.get_table_names()
    if 'job_import_items' not in tables:
        op.create_table(
            'job_import_items',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                'import_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('job_imports.id', ondelete='CASCADE'),
                nullable=False,
            ),
            sa.Column(
                'job_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('jobs.id', ondelete='SET NULL'),
                nullable=True,
            ),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('title_guess', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )
        op.create_index('ix_job_import_items_import_id', 'job_import_items', ['import_id'])
        op.create_index('ix_job_import_items_job_id', 'job_import_items', ['job_id'])

    # 4. Create scrape_history table
    if 'scrape_history' not in tables:
        op.create_table(
            'scrape_history',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                'user_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('users.id', ondelete='CASCADE'),
                nullable=False,
            ),
            sa.Column('url', sa.Text(), nullable=False),
            sa.Column('source_platform', sa.String(length=50), nullable=True),
            sa.Column('method_used', sa.String(length=20), nullable=False),
            sa.Column('success', sa.String(length=10), server_default='true', nullable=False),
            sa.Column('fields_extracted', sa.Integer(), server_default='0', nullable=True),
            sa.Column('duration_ms', sa.Integer(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        )
        op.create_index('ix_scrape_history_user_id', 'scrape_history', ['user_id'])
        op.create_index('ix_scrape_history_platform', 'scrape_history', ['source_platform'])


def downgrade() -> None:
    op.drop_table('scrape_history')
    op.drop_table('job_import_items')
    op.drop_column('job_imports', 'source_data')
    op.drop_column('job_imports', 'errors')
    op.drop_column('job_imports', 'partial')
    op.drop_index('ix_jobs_is_archived', table_name='jobs')
    op.drop_column('jobs', 'is_archived')
    op.drop_index('ix_jobs_import_id', table_name='jobs')
    op.drop_column('jobs', 'import_id')
