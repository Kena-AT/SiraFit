from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel
import uuid


class AuditLogItem(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: Optional[str] = None
    created_at: datetime
    details: Optional[Dict[str, Any]] = None


class DashboardStats(BaseModel):
    active_applications: int
    resumes_generated: int
    jobs_scored: int
    recent_activity: List[AuditLogItem]
    # v2 additions (defaults keep old cached entries deserializable)
    total_jobs: int = 0
    upcoming_followups_count: int = 0


class MarketPulseTag(BaseModel):
    tag: str
    count: int
    pct: int  # percent of analyzed jobs carrying this tag


class MarketPulseResponse(BaseModel):
    total_jobs_analyzed: int
    top_tags: List[MarketPulseTag]


class BriefingResponse(BaseModel):
    briefing: str
    date: str  # YYYY-MM-DD the briefing was generated for
