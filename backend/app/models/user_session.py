import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class UserSession(Base):
    """Stores user session credentials encrypted at rest.

    Never stores raw plaintext cookies/headers. Raw credentials are encrypted
    using AES-128-CBC via Fernet in ``app.services.session_management``.
    """

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform = Column(
        String(50), nullable=False, index=True
    )  # e.g., "linkedin", "indeed"
    encrypted_session_data = Column(Text, nullable=False)
    stored_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user = relationship("User", back_populates="user_sessions")

    __table_args__ = (
        Index(
            "ix_user_sessions_user_platform_active", "user_id", "platform", "is_active"
        ),
    )
