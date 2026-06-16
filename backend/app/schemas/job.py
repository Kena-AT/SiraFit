from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
import uuid

# --- Job ---
class JobBase(BaseModel):
    title: str = Field(..., max_length=255)
    company: str = Field(..., max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = Field(None, max_length=3)
    tags: Optional[List[str]] = []
    url: Optional[str] = None
    source: Optional[str] = "manual"

class JobCreate(JobBase):
    external_id: str = Field(..., max_length=255)

class JobResponse(JobBase):
    id: uuid.UUID
    external_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Job Application ---
class JobApplicationBase(BaseModel):
    status: Optional[str] = "applied"
    stage: Optional[int] = 0
    notes: Optional[str] = None

class JobApplicationCreate(JobApplicationBase):
    job_id: uuid.UUID

class JobApplicationUpdate(JobApplicationBase):
    pass

class JobApplicationResponse(JobApplicationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    score: Optional[int] = None
    score_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    job: Optional[JobResponse] = None

    model_config = ConfigDict(from_attributes=True)
