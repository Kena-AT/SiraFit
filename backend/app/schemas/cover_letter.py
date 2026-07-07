"""Cover letter Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class CoverLetterBase(BaseModel):
    title: str = Field(..., max_length=255)
    body: str = Field(..., min_length=1)
    tone: Optional[str] = Field(default="matching", description="matching | conversational | formal")
    template: Optional[str] = Field(default="classic", description="classic | modern | compact")


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class CoverLetterCreate(CoverLetterBase):
    resume_id: Optional[uuid.UUID] = None
    job_id: Optional[uuid.UUID] = None


class CoverLetterUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tone: Optional[str] = None
    template: Optional[str] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class CoverLetterResponse(CoverLetterBase):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: Optional[uuid.UUID] = None
    job_id: Optional[uuid.UUID] = None
    pdf_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

class CoverLetterGenerateRequest(BaseModel):
    job_id: uuid.UUID
    resume_id: Optional[uuid.UUID] = None
    tone: str = Field(default="matching", description="matching | conversational | formal")
    template: Optional[str] = Field(default="classic", description="classic | modern | compact")


class CoverLetterGenerateResponse(BaseModel):
    cover_letter_id: uuid.UUID
    status: str
    message: str
