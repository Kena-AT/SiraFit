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
    status: Optional[str] = "saved"
    stage: Optional[int] = 0
    general_notes: Optional[str] = None
    follow_up_at: Optional[datetime] = None
    follow_up_note: Optional[str] = None


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


# --- Follow-up / Reminder ---


class FollowUpSet(BaseModel):
    """Payload to set or clear a follow-up on an application."""

    follow_up_at: Optional[datetime] = Field(
        None, description="UTC datetime when the follow-up is due; null to clear"
    )
    follow_up_note: Optional[str] = Field(
        None, max_length=500, description="Short reminder label"
    )


class FollowUpItem(BaseModel):
    """A single follow-up item for the Follow-up Center."""

    application_id: uuid.UUID
    job_title: str
    company: str
    status: str
    follow_up_at: datetime
    follow_up_note: Optional[str] = None
    score: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class JobAnalysisResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    score: int
    summary: str
    pros: List[str]
    cons: List[str]
    skills_gap: List[str]
    key_requirements: Optional[List[str]] = None
    seniority: Optional[str] = None
    analysis_version: Optional[str] = None
    status: str = "done"
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobMatchScoreResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    user_id: uuid.UUID
    score: int
    breakdown: Dict[str, Any]
    explanation: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RankedJobResponse(BaseModel):
    job: JobResponse
    match_score: Optional[JobMatchScoreResponse] = None


class RankedJobListResponse(BaseModel):
    jobs: List[RankedJobResponse]
    total: int


class AnalysisRequest(BaseModel):
    force_refresh: bool = False


# --- Sprint 9 Application Tracking ---


class ApplicationEventResponse(BaseModel):
    """Timeline event for an application."""

    id: uuid.UUID
    application_id: uuid.UUID
    event_type: str
    title: str
    description: Optional[str] = None
    event_metadata: Optional[dict] = None
    occurred_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationNoteBase(BaseModel):
    body: str
    author: Optional[str] = None
    pinned: bool = False


class ApplicationNoteCreate(ApplicationNoteBase):
    pass


class ApplicationNoteUpdate(BaseModel):
    body: Optional[str] = None
    author: Optional[str] = None
    pinned: Optional[bool] = None


class ApplicationNoteResponse(ApplicationNoteBase):
    id: uuid.UUID
    application_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationContactBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = "recruiter"
    company: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None
    is_primary: bool = False


class ApplicationContactCreate(ApplicationContactBase):
    pass


class ApplicationContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None
    is_primary: Optional[bool] = None


class ApplicationContactResponse(ApplicationContactBase):
    id: uuid.UUID
    application_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatusTransitionRequest(BaseModel):
    to_status: str
