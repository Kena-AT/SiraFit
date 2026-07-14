from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict
import uuid


class NotificationCreate(BaseModel):
    title: str
    body: str
    kind: str = "system_event"


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    body: str
    kind: str
    status: str
    read_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    skip: int
    limit: int


# Analytics schemas


class MetricsResponse(BaseModel):
    total_applications: int
    interview_rate: float
    avg_response_time_days: float
    offer_rate: float
    conversion_funnel: List[Dict[str, Any]]
    rejection_stages: List[Dict[str, Any]]
    skill_coverage: List[Dict[str, Any]]
    market_demand: List[Dict[str, Any]]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyticsSnapshotResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    snapshot_date: datetime
    metrics: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyticsSnapshotListResponse(BaseModel):
    snapshots: List[AnalyticsSnapshotResponse]
    total: int
    skip: int
    limit: int
