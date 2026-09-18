import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(
        String(100), nullable=False, index=True
    )  # References SkillTaxonomy.canonical_key
    title = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    provider = Column(String(100), nullable=False)
    resource_type = Column(
        String(50), nullable=False
    )  # documentation, course, tutorial, video, certification
    access_type = Column(String(50), nullable=False)  # free, free_audit, paid, unknown
    difficulty = Column(String(50), nullable=False)  # basic, intermediate, advanced
    estimated_minutes = Column(Integer, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
