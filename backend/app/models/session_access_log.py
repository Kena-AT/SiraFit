import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class SessionAccessLog(Base):
    """Audit log for session access, usage, and validation events.

    Strict security rule: NEVER store cookies, headers, or tokens in this table.
    Only store safe metadata such as action, result, and failure codes.
    """

    __tablename__ = "session_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # stored, validated, used, deleted, expired, failed
    result = Column(String(50), nullable=False)  # success, failure
    error_code = Column(String(100), nullable=True)  # safe code: session_expired, invalid_cookies, etc.
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)

    user = relationship("User")
