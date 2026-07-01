import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Integer, Text, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class JobMatchScore(Base):
    __tablename__ = "job_match_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    score = Column(Integer, nullable=False)  # Overall match score (0-100)
    breakdown = Column(JSON, nullable=False)  # e.g. {"skills": 80, "experience": 90, "education": 70}
    explanation = Column(Text, nullable=True)  # Detailed explanation

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User")
    job = relationship("Job")
