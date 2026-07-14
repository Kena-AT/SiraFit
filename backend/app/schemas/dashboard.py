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
