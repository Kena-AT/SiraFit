from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ExtensionTokenCreate(BaseModel):
    name: Optional[str] = Field(
        default="Browser Extension", max_length=100, description="Device/Browser name"
    )
    expires_days: Optional[int] = Field(
        default=30, ge=1, le=365, description="Token validity in days"
    )


class ExtensionTokenOut(BaseModel):
    token: str
    token_type: str = "Bearer"
    name: str
    expires_at: datetime


class ExtensionStatusOut(BaseModel):
    connected: bool = True
    user_id: str
    user_email: str
    user_name: Optional[str] = None
    version: str = "1.0.0"


class ExtensionProfileOut(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    skills: List[str] = Field(default_factory=list)


class ExtensionJobCaptureIn(BaseModel):
    capture_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Client capture UUID for idempotency",
    )
    page_url: str = Field(..., min_length=1, max_length=2048)
    apply_url: Optional[str] = Field(None, max_length=2048)
    platform: str = Field(default="generic", max_length=50)
    title: str = Field(..., min_length=1, max_length=300)
    company: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    description: str = Field(..., min_length=1, max_length=50000)
    salary_raw: Optional[str] = Field(None, max_length=100)
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = Field("USD", max_length=10)
    tags: Optional[List[str]] = Field(default_factory=list)
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    extracted_via: Optional[str] = Field("dom_adapter", max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("page_url", "apply_url")
    @classmethod
    def validate_urls(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("title", "company", "description")
    @classmethod
    def strip_and_clean_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace only")
        return cleaned


class ExtensionJobCaptureOut(BaseModel):
    success: bool
    status: str  # "imported" | "duplicate" | "failed"
    job_id: Optional[str] = None
    import_id: str
    capture_id: str
    title: str
    company: str
    message: str
