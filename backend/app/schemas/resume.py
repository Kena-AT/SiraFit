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
    versions_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Resume Versions ---


class ResumeVersionCreate(BaseModel):
    content: str
    template: Optional[str] = "minimal"
    job_id: Optional[uuid.UUID] = None
    parent_version_id: Optional[uuid.UUID] = None
    source_type: Optional[str] = "base"
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
    parent_version_id: Optional[uuid.UUID] = None
    source_type: str = "base"
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    tailoring_notes: Optional[str] = None
    score: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeVersionListResponse(BaseModel):
    versions: list[ResumeVersionResponse]
    total: int


# --- Resume Diff ---


class DiffSummary(BaseModel):
    added: int = 0
    removed: int = 0
    changed: int = 0


class StringListDiff(BaseModel):
    added: list[str] = []
    removed: list[str] = []
    preserved: list[str] = []


class TextDiff(BaseModel):
    from_text: Optional[str] = None
    to_text: Optional[str] = None
    changed: bool = False


class ExperienceItemDiff(BaseModel):
    key: str
    status: str  # "added", "removed", "modified", "unchanged"
    company: str
    title: str
    period_from: Optional[str] = None
    period_to: Optional[str] = None
    location_from: Optional[str] = None
    location_to: Optional[str] = None
    bullets_added: list[str] = []
    bullets_removed: list[str] = []
    bullets_preserved: list[str] = []


class ProjectItemDiff(BaseModel):
    name: str
    status: str  # "added", "removed", "modified", "unchanged"
    description_from: Optional[str] = None
    description_to: Optional[str] = None
    url_from: Optional[str] = None
    url_to: Optional[str] = None


class EducationItemDiff(BaseModel):
    key: str
    status: str  # "added", "removed", "modified", "unchanged"
    institution: str
    degree: str
    field_of_study_from: Optional[str] = None
    field_of_study_to: Optional[str] = None
    period_from: Optional[str] = None
    period_to: Optional[str] = None


class ResumeDiffSections(BaseModel):
    summary: TextDiff
    skills: StringListDiff
    experience: list[ExperienceItemDiff] = []
    projects: list[ProjectItemDiff] = []
    education: list[EducationItemDiff] = []


class ResumeDiffResponse(BaseModel):
    from_version_id: uuid.UUID
    to_version_id: uuid.UUID
    from_version_number: int
    to_version_number: int
    has_changes: bool
    summary: DiffSummary
    sections: ResumeDiffSections


# --- Resume Generation ---


class ResumeGenerationRequest(BaseModel):
    job_id: uuid.UUID
    parent_version_id: Optional[uuid.UUID] = None
    template: str = Field(
        default="minimal",
        description="Template name: minimal, technical, modern, corporate, compact",
    )
    provider: Optional[str] = None
    model: Optional[str] = None


class ResumeGenerationResponse(BaseModel):
    version_id: uuid.UUID
    status: str
    message: str

