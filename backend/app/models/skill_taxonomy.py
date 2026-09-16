import uuid
from sqlalchemy import Column, String, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class SkillTaxonomy(Base):
    __tablename__ = "skill_taxonomy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)  # e.g., "Programming", "Framework", "Soft Skill"
    aliases = Column(JSON, default=[])  # alternative names, e.g., ["JS"] for "JavaScript"
