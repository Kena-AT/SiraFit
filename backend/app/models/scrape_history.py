"""ScrapeHistory — tracks every scrape attempt for observability."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class ScrapeHistory(Base):
    __tablename__ = "scrape_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url = Column(Text, nullable=False)
    source_platform = Column(
        String(50), index=True
    )  # linkedin, greenhouse, lever, indeed
    method_used = Column(String(20), nullable=False)  # scrapling, heuristic, fallback
    success = Column(
        String(10), nullable=False, default="true"
    )  # true / false / partial
    fields_extracted = Column(Integer, default=0)
    duration_ms = Column(Integer)  # total fetch+parse time in milliseconds
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
