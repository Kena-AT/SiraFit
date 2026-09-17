import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class OAuthAccount(Base):
    """Stores linked OAuth provider accounts for a user."""

    __tablename__ = "oauth_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider = Column(String(20), nullable=False)  # google, github, linkedin
    provider_user_id = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)  # Fernet encrypted
    refresh_token = Column(Text, nullable=True)  # Fernet encrypted
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_uid"),
        UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),
        {"extend_existing": True},
    )
