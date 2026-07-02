from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
import uuid

class ResumeBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    is_primary: Optional[bool] = False

class ResumeCreate(ResumeBase):
    application_id: Optional[uuid.UUID] = None

class ResumeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_primary: Optional[bool] = None

class ResumeResponse(ResumeBase):
    id: uuid.UUID
    user_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Resume Versions ---

class ResumeVersionCreate(BaseModel):
    content: str
    template: Optional[str] = "minimal"
    job_id: Optional[uuid.UUID] = None
    tailoring_notes: Optional[str] = None
    score: Optional[int] = None
    status: Optional[str] = "completed"

class ResumeVersionResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    version_number: int
    content: str
    template: Optional[str] = None
    job_id: Optional[uuid.UUID] = None
    tailoring_notes: Optional[str] = None
    score: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ResumeVersionListResponse(BaseModel):
    versions: list[ResumeVersionResponse]
    total: int

 # --- Resume Generation ---

class ResumeGenerationRequest(BaseModel):
    job_id: uuid.UUID
    template: str = Field(default="minimal", description="Template name: minimal, technical, modern, corporate, compact")
    provider: Optional[str] = None
    model: Optional[str] = None

class ResumeGenerationResponse(BaseModel):
    version_id: uuid.UUID
    status: str
    message: str
