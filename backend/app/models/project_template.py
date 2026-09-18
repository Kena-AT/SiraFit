import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class ProjectTemplate(Base):
    __tablename__ = "project_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(50), nullable=False)
    estimated_minutes = Column(Integer, nullable=True)
    prerequisites = Column(JSON, nullable=False, default=list)
    steps = Column(JSON, nullable=False, default=list)
    acceptance_criteria = Column(JSON, nullable=False, default=list)
    evidence_artifacts = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    skill_ids = Column(JSON, nullable=False, default=list) # List of SkillTaxonomy.canonical_key
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
