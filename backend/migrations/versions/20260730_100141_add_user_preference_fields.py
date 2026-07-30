"""Add notification prefs, resume defaults, and AI provider keys to UserPreference

Revision ID: 20260730_100141
Revises: ix_job_applications_created_at
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260730_100141"
down_revision = "ix_job_applications_created_at"
branch_labels = None
depends_on = None


def upgrade():
    # Notification preference fields
    with op.batch_alter_table("user_preferences") as batch:
        batch.add_column(sa.Column("email_job_matches", sa.Boolean, nullable=False, server_default="1"))
        batch.add_column(sa.Column("email_daily_summary", sa.Boolean, nullable=False, server_default="0"))
        batch.add_column(sa.Column("push_notifications", sa.Boolean, nullable=False, server_default="1"))
        batch.add_column(sa.Column("email_new_opportunities", sa.Boolean, nullable=False, server_default="1"))

        # Resume defaults
        batch.add_column(sa.Column("default_template", sa.String(50), nullable=False, server_default="modern"))
        batch.add_column(sa.Column("auto_tailor_enabled", sa.Boolean, nullable=False, server_default="1"))
        batch.add_column(sa.Column("export_format", sa.String(10), nullable=False, server_default="pdf"))

        # AI provider keys (encrypted)
        batch.add_column(sa.Column("encrypted_anthropic_key", sa.Text, nullable=True))
        batch.add_column(sa.Column("encrypted_openai_key", sa.Text, nullable=True))
        batch.add_column(sa.Column("encrypted_grok_key", sa.Text, nullable=True))
        batch.add_column(sa.Column("encrypted_mistral_key", sa.Text, nullable=True))
        batch.add_column(sa.Column("encrypted_nvidia_key", sa.Text, nullable=True))


def downgrade():
    with op.batch_alter_table("user_preferences") as batch:
        # Notification prefs
        batch.drop_column("email_job_matches")
        batch.drop_column("email_daily_summary")
        batch.drop_column("push_notifications")
        batch.drop_column("email_new_opportunities")

        # Resume defaults
        batch.drop_column("default_template")
        batch.drop_column("auto_tailor_enabled")
        batch.drop_column("export_format")

        # AI provider keys
        batch.drop_column("encrypted_anthropic_key")
        batch.drop_column("encrypted_openai_key")
        batch.drop_column("encrypted_grok_key")
        batch.drop_column("encrypted_mistral_key")
        batch.drop_column("encrypted_nvidia_key")
