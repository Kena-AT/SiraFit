import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON, UniqueConstraint, Index
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
    source = Column(String(50), default="update", nullable=False)  # update, revert, baseline
    reverted_from_version_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_profile_versions_user_version"),
        Index("ix_profile_versions_user_id_version", "user_id", "version"),
    )
