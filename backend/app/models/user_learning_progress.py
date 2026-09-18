import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class UserLearningProgress(Base):
    __tablename__ = "user_learning_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_resources.id", ondelete="CASCADE"),
        nullable=True,
    )
    project_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("project_templates.id", ondelete="CASCADE"),
        nullable=True,
    )

    status = Column(
        String(50), nullable=False, default="not_started"
    )  # not_started, in_progress, completed, skipped
    minutes_spent = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        CheckConstraint(
            "(resource_id IS NOT NULL AND project_template_id IS NULL) OR (resource_id IS NULL AND project_template_id IS NOT NULL)",
            name="check_resource_or_project",
        ),
    )

    user = relationship("User")
    learning_resource = relationship("LearningResource")
    project_template = relationship("ProjectTemplate")
