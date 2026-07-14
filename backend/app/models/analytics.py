import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(DateTime(timezone=True), default=_utcnow)
    metrics = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User")