import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None
    jti: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    class Config:
        from_attributes = True


class NotificationPreferencesBase(BaseModel):
    email_job_matches: bool = True
    email_daily_summary: bool = False
    push_notifications: bool = True
    email_new_opportunities: bool = True


class NotificationPreferences(NotificationPreferencesBase):
    class Config:
        from_attributes = True


class ResumeDefaultsBase(BaseModel):
    default_template: str = Field(
        default="modern",
        pattern=r"^(modern|classic|minimal|ats)$"
    )
    auto_tailor_enabled: bool = True
    export_format: str = Field(
        default="pdf",
        pattern=r"^(pdf|docx|txt)$"
    )


class ResumeDefaults(ResumeDefaultsBase):
    class Config:
        from_attributes = True


class AIProviderKeysWrite(BaseModel):
    gemini_key: Optional[str] = None
    openrouter_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    openai_key: Optional[str] = None
    grok_key: Optional[str] = None
    mistral_key: Optional[str] = None
    nvidia_key: Optional[str] = None


class AIProviderKeysRead(BaseModel):
    gemini_configured: bool
    openrouter_configured: bool
    anthropic_configured: bool
    openai_configured: bool
    grok_configured: bool
    mistral_configured: bool
    nvidia_configured: bool
