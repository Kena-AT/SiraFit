import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class WSConnectionLog(Base):
    __tablename__ = "ws_connection_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    event = Column(String(20), nullable=False)  # connect, disconnect, error
    reason = Column(String(50), nullable=True)  # normal, timeout, auth_failed, proxy_error
    duration_sec = Column(Integer, nullable=True)  # for disconnect events
    created_at = Column(DateTime, default=_utcnow, nullable=False)
