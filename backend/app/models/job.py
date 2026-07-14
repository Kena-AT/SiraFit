import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Integer,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String(3), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    url = Column(Text, nullable=True)
    source = Column(String(50), default="manual")  # manual, linkedin, indeed, etc.

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    applications = relationship(
        "JobApplication", back_populates="job", cascade="all, delete-orphan"
    )


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )

    status = Column(
        String(50), default="saved"
    )  # saved, preparing, applied, screening, interview, final_round, offer, rejected, withdrawn, archived
    stage = Column(Integer, default=0)  # Application stage number
    general_notes = Column(
        Text, nullable=True
    )  # General notes (legacy field, use ApplicationNote for rich notes)
    score = Column(Integer, nullable=True)  # AI-generated match score (0-100)
    score_reason = Column(Text, nullable=True)  # AI explanation for score
    follow_up_at = Column(DateTime, nullable=True)  # Optional follow-up reminder date
    follow_up_note = Column(String(500), nullable=True)  # Brief label for the reminder

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resumes = relationship(
        "Resume", back_populates="application", cascade="all, delete-orphan"
    )


class JobAnalysis(Base):
    __tablename__ = "job_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Core analysis fields
    score = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=False, default="")
    pros = Column(JSON, nullable=False, default=list)
    cons = Column(JSON, nullable=False, default=list)
    skills_gap = Column(JSON, nullable=False, default=list)
    key_requirements = Column(JSON, nullable=True)  # List[str]
    seniority = Column(String(50), nullable=True)  # e.g. "Senior", "Junior", "Mid"

    # Versioning & async state
    analysis_version = Column(String(20), nullable=True, default="v1")
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending | processing | done | failed

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    job = relationship("Job", backref="analysis")


class JobImport(Base):
    __tablename__ = "job_imports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source = Column(String(50), nullable=False)  # url, description, csv
    status = Column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    total_found = Column(Integer, default=0)
    ok_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=True,
    )

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Markdown or HTML content
    pdf_url = Column(Text, nullable=True)  # URL to generated PDF
    is_primary = Column(Boolean, default=False)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="resumes")
    application = relationship("JobApplication", back_populates="resumes")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action = Column(
        String(100), nullable=False
    )  # login, password_change, profile_update, resume_generation, application_status_change
    entity_type = Column(String(50), nullable=True)  # user, resume, application, job
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSON, nullable=True)  # Additional context as JSON
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="audit_logs")


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # Full generated resume content (JSON)
    template = Column(
        String(100), nullable=True
    )  # "minimal", "technical", "modern", "corporate", "compact"
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    tailoring_notes = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)  # ATS readiness score
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, processing, completed, failed

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    resume = relationship("Resume", backref="versions")
    job = relationship("Job")


# ---------------------------------------------------------------------------
# Sprint 9 — Application tracking
# ---------------------------------------------------------------------------


class ApplicationEvent(Base):
    """Chronological event in a JobApplication's timeline.

    Mirrors application activity: status transitions, notes (when posted to
    timeline), emails, interviews, offers, reminders, and arbitrary markers.

    One row per event. The ``application_events`` table is append-only —
    events are never updated (a correction is itself a new event).
    """

    __tablename__ = "application_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Validated on the service layer, not at the DB level.
    event_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Free-form per-event data (e.g. from_status/to_status, email_subject).
    event_metadata = Column("event_metadata", JSON, nullable=True)

    occurred_at = Column(DateTime, default=_utcnow, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    application = relationship("JobApplication", backref="events")
    user = relationship("User")


class ApplicationNote(Base):
    """Free-form note attached to a JobApplication.

    Notes are user-editable mutable rows (unlike events). The user can
    pin important notes to surface them first.
    """

    __tablename__ = "application_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    body = Column(Text, nullable=False)
    author = Column(String(100), nullable=True)  # Optional display name
    pinned = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    application = relationship("JobApplication", backref="note_items")
    user = relationship("User")


class ApplicationContact(Base):
    """Recruiter / hiring-manager / HR contact associated with one application.

    One application typically has a small set of contacts (recruiter, hiring
    manager, referrer). They are surfaced on the application detail page and
    can be reused across applications when names/emails repeat.
    """

    __tablename__ = "application_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    # recruiter | hiring_manager | hr | referrer | interviewer | other
    role = Column(String(50), nullable=False, default="recruiter")
    company = Column(String(255), nullable=True)
    linkedin = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    application = relationship("JobApplication", backref="contacts")
    user = relationship("User")
