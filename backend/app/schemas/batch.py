from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
import uuid
from typing import Literal


class BatchJobCreate(BaseModel):
    operation_type: Literal["analyze", "score", "tag", "archive"]
    job_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=500)
    params: Dict[str, Any] = Field(default_factory=dict)


class BatchJobCreateResponse(BaseModel):
    id: uuid.UUID
    operation_type: str
    status: str
    total_items: int
    processed_items: int
    succeeded_items: int
    failed_items: int
    payload: Dict[str, Any]
    result_summary: Dict[str, Any]
    cancel_requested: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchJobUpdate(BaseModel):
    cancel_requested: Optional[bool] = None


class BatchJobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    operation_type: str
    status: str
    total_items: int
    processed_items: int
    succeeded_items: int
    failed_items: int
    payload: Dict[str, Any]
    result_summary: Dict[str, Any]
    cancel_requested: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchJobListResponse(BaseModel):
    jobs: List[BatchJobResponse]
    total: int
    skip: int
    limit: int