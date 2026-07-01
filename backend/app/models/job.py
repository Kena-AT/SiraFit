import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(String(50), default="applied")  # applied, screening, interview, offer, rejected, withdrawn
    stage = Column(Integer, default=0)  # Application stage number
    notes = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)  # AI-generated match score (0-100)
    score_reason = Column(Text, nullable=True)  # AI explanation for score
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resumes = relationship("Resume", back_populates="application", cascade="all, delete-orphan")


class JobAnalysis(Base):
    __tablename__ = "job_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Core analysis fields
    score = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=False, default="")
    pros = Column(JSON, nullable=False, default=list)
    cons = Column(JSON, nullable=False, default=list)
    skills_gap = Column(JSON, nullable=False, default=list)
    key_requirements = Column(JSON, nullable=True)   # List[str]
    seniority = Column(String(50), nullable=True)    # e.g. "Senior", "Junior", "Mid"

    # Versioning & async state
    analysis_version = Column(String(20), nullable=True, default="v1")
    status = Column(String(20), nullable=False, default="pending")  # pending | processing | done | failed

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("Job", backref="analysis")




class JobImport(Base):
    __tablename__ = "job_imports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(50), nullable=False)  # url, description, csv
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    total_found = Column(Integer, default=0)
    ok_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=True)
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Markdown or HTML content
    pdf_url = Column(Text, nullable=True)  # URL to generated PDF
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="resumes")
    application = relationship("JobApplication", back_populates="resumes")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # login, password_change, profile_update, resume_generation, application_status_change
    entity_type = Column(String(50), nullable=True)  # user, resume, application, job
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSON, nullable=True)  # Additional context as JSON
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")
