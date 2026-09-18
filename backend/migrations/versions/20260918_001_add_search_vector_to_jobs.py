"""add search_vector to jobs

Revision ID: 20260918_001
Revises: 20260917_009
Create Date: 2026-09-18 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260918_001'
down_revision = '20260917_009'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # Add generated TSVECTOR column with weights
        op.execute("""
            ALTER TABLE jobs ADD COLUMN search_vector tsvector
                GENERATED ALWAYS AS (
                    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(cast(tags as text), '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(company, '')), 'B') ||
                    setweight(to_tsvector('english', coalesce(description, '')), 'C') ||
                    setweight(to_tsvector('english', coalesce(location, '')), 'D')
                ) STORED;
        """)
        # Create GIN index for full-text search
        op.execute("CREATE INDEX ix_jobs_search_vector ON jobs USING GIN (search_vector);")


def downgrade():
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute("DROP INDEX IF EXISTS ix_jobs_search_vector;")
        op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS search_vector;")
