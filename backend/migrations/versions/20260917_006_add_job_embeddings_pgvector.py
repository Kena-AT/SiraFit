"""Add job embeddings and pgvector support (Sprint 8)

Revision ID: 20260917_006
Revises: 20260917_005
Create Date: 2026-09-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "20260917_006"
down_revision: Union[str, Sequence[str], None] = "20260917_005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    is_postgres = conn.dialect.name == "postgresql"

    # 1. Enable pgvector extension in PostgreSQL
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "jobs" in existing_tables:
        job_cols = {c["name"] for c in inspector.get_columns("jobs")}

        # 2. Add embedding column (VECTOR(384) in postgres, JSON or TEXT elsewhere)
        if "embedding" not in job_cols:
            if is_postgres:
                from pgvector.sqlalchemy import Vector
                op.add_column("jobs", sa.Column("embedding", Vector(384), nullable=True))
            else:
                op.add_column("jobs", sa.Column("embedding", sa.JSON(), nullable=True))

        # 3. Add embedding metadata fields
        if "embedding_model" not in job_cols:
            op.add_column("jobs", sa.Column("embedding_model", sa.String(100), nullable=True))
        if "embedding_version" not in job_cols:
            op.add_column("jobs", sa.Column("embedding_version", sa.String(20), nullable=True))
        if "embedding_source_hash" not in job_cols:
            op.add_column("jobs", sa.Column("embedding_source_hash", sa.String(64), nullable=True))
            op.create_index("ix_jobs_embedding_source_hash", "jobs", ["embedding_source_hash"])
        if "embedding_status" not in job_cols:
            op.add_column(
                "jobs",
                sa.Column("embedding_status", sa.String(20), nullable=False, server_default="pending"),
            )
            op.create_index("ix_jobs_embedding_status", "jobs", ["embedding_status"])
        if "embedding_updated_at" not in job_cols:
            op.add_column("jobs", sa.Column("embedding_updated_at", sa.DateTime(), nullable=True))

        # 4. Create HNSW index for cosine distance in PostgreSQL
        if is_postgres:
            op.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_embedding_hnsw ON jobs USING hnsw (embedding vector_cosine_ops)"
            )


def downgrade() -> None:
    conn = op.get_bind()
    is_postgres = conn.dialect.name == "postgresql"

    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "jobs" in existing_tables:
        job_cols = {c["name"] for c in inspector.get_columns("jobs")}

        if is_postgres:
            op.execute("DROP INDEX IF EXISTS idx_jobs_embedding_hnsw")

        if "embedding_source_hash" in job_cols:
            op.drop_index("ix_jobs_embedding_source_hash", table_name="jobs")
        if "embedding_status" in job_cols:
            op.drop_index("ix_jobs_embedding_status", table_name="jobs")

        for col in [
            "embedding_updated_at",
            "embedding_status",
            "embedding_source_hash",
            "embedding_version",
            "embedding_model",
            "embedding",
        ]:
            if col in job_cols:
                op.drop_column("jobs", col)
