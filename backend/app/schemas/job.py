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

class JobListResponse(BaseModel):
    """Paginated list of jobs with metadata."""
    jobs: List[JobResponse]
    total: int
    skip: int
    limit: int


# --- Job Data (extracted/normalized, not yet saved) ---
class JobData(BaseModel):
    external_id: str
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    tags: List[str] = []
    url: Optional[str] = None
    source: str = "manual"
    is_duplicate: bool = False


# --- Job Import ---
class JobImportCreate(BaseModel):
    source_type: str  # "url", "description", "csv"
    data: str  # The URL or the full description text

class JobImportResponse(BaseModel):
    id: uuid.UUID
    source: str
    status: str
    total_found: int
    ok_count: int
    fail_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ImportResultResponse(BaseModel):
    import_record: JobImportResponse
    jobs: List[JobData] = []
    errors: List[str] = []


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

class JobAnalysisResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    score: int
    summary: str
    pros: List[str]
    cons: List[str]
    skills_gap: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
