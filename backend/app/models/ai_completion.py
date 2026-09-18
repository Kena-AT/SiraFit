"""AI Completion and Attempt audit ORM models (Sprint 7)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class AICompletion(Base):
    __tablename__ = "ai_completions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generation_id = Column(String(64), nullable=False, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    operation = Column(String(64), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    response_model = Column(String(128), nullable=False)
    status = Column(
        String(32), nullable=False, default="success"
    )  # success, failed, fallback
    attempt_count = Column(Integer, nullable=False, default=1)
    duration_ms = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    attempts = relationship(
        "AICompletionAttempt",
        back_populates="completion",
        cascade="all, delete-orphan",
        order_by="AICompletionAttempt.attempt_number",
    )
    user = relationship("User", backref="ai_completions")


class AICompletionAttempt(Base):
    __tablename__ = "ai_completion_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    completion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_completions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number = Column(Integer, nullable=False, default=1)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)  # success, failed
    failure_code = Column(
        String(64), nullable=True
    )  # validation_error, rate_limit, timeout, auth_error, schema_error, unknown
    validation_errors = Column(JSON, nullable=True)
    duration_ms = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=_utcnow, nullable=False)

    completion = relationship("AICompletion", back_populates="attempts")
