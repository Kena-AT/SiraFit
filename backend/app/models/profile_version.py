import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class ProfileVersion(Base):
    __tablename__ = "profile_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)  # Snapshot of full profile at this version
    created_at = Column(DateTime(timezone=True), default=_utcnow)
