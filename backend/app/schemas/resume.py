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
