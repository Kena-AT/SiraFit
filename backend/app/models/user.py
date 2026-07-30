import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    profile = relationship(
        "Profile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    applications = relationship(
        "JobApplication", back_populates="user", cascade="all, delete-orphan"
    )
    resumes = relationship(
        "Resume", back_populates="user", cascade="all, delete-orphan"
    )
    cover_letters = relationship(
        "CoverLetter", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship("AuditLog", back_populates="user")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )

    # Store generic JSON preferences or specific columns
    theme = Column(String(50), default="light")
    notifications_enabled = Column(Boolean, default=True)

    # Notification preference fields
    email_job_matches = Column(Boolean, default=True, nullable=False)
    email_daily_summary = Column(Boolean, default=False, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)
    email_new_opportunities = Column(Boolean, default=True, nullable=False)

    # Resume defaults
    default_template = Column(String(50), default="modern", nullable=False)
    auto_tailor_enabled = Column(Boolean, default=True, nullable=False)
    export_format = Column(String(10), default="pdf", nullable=False)

    # Encrypted AI API keys (AES-128-CBC via Fernet)
    encrypted_gemini_key = Column(String(500), nullable=True)
    encrypted_openrouter_key = Column(String(500), nullable=True)
    encrypted_anthropic_key = Column(String(500), nullable=True)
    encrypted_openai_key = Column(String(500), nullable=True)
    encrypted_grok_key = Column(String(500), nullable=True)
    encrypted_mistral_key = Column(String(500), nullable=True)
    encrypted_nvidia_key = Column(String(500), nullable=True)

    # Provider and model preferences (plain text, no sensitive data)
    ai_provider = Column(String(50), nullable=True, default="gemini")
    ai_model = Column(String(255), nullable=True, default="gemini-1.5-flash")

    user = relationship("User", back_populates="preferences")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")
