"""Cover letter ORM models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)            # The letter body (plain text or markdown)
    structured = Column(JSON, nullable=True)       # Optional structured form (paragraphs[], greeting, sign_off)

    tone = Column(String(50), nullable=True)       # "matching", "conversational", "formal"
    template = Column(String(100), nullable=True)  # "classic", "modern", "compact"

    pdf_url = Column(Text, nullable=True)          # Local path or URL to generated PDF
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="cover_letters")
    resume = relationship("Resume", backref="cover_letters")
    job = relationship("Job", backref="cover_letters")
