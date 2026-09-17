import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
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
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    auth_provider = Column(String(20), nullable=True)  # google, github, linkedin
    auth_provider_id = Column(String(255), nullable=True)
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
    oauth_accounts = relationship("OAuthAccount", back_populates="user")
    totp_secret = relationship("TOTPSecret", back_populates="user", uselist=False)
    recovery_codes = relationship("RecoveryCode", back_populates="user")
    user_sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    extension_tokens = relationship(
        "ExtensionToken", back_populates="user", cascade="all, delete-orphan"
    )


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
    # Ordered list of providers to try when the chosen one is unavailable.
    # Stored as a JSON array (e.g. '["gemini","openai","anthropic"]') or NULL
    # to use the built-in DEFAULT_FALLBACK_ORDER.
    ai_fallback_order = Column(Text, nullable=True)

    user = relationship("User", back_populates="preferences")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")


class DeviceSession(Base):
    """Track user device sessions for security monitoring."""

    __tablename__ = "device_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    device_name = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen = Column(DateTime, default=_utcnow, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    user = relationship("User")
