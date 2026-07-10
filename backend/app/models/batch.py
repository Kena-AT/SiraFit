import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

def _utcnow():
    return datetime.now(timezone.utc)


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    operation_type = Column(String(30), nullable=False)  # analyze, score, tag, archive
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed, partial, cancelled
    total_items = Column(Integer, nullable=False, default=0)
    processed_items = Column(Integer, nullable=False, default=0)
    succeeded_items = Column(Integer, nullable=False, default=0)
    failed_items = Column(Integer, nullable=False, default=0)
    payload = Column("payload", JSON, nullable=False)  # operation-specific params
    result_summary = Column("result_summary", JSON, nullable=False, default={})  # per-item results/errors
    cancel_requested = Column(Boolean(), nullable=False, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user = relationship("User")