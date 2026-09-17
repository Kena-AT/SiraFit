import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class SkillTaxonomy(Base):
    __tablename__ = "skill_taxonomy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_key = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)  # e.g., "Languages", "Frameworks", "Databases", "DevOps", "Soft Skills"
    aliases = Column(JSON, default=list)  # alternative names, e.g., ["JS"] for "JavaScript"
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
