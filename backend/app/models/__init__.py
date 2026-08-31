from app.models.user import User, UserPreference, RefreshToken, DeviceSession
from app.models.job import (
    Job,
    JobApplication,
    JobImport,
    JobAnalysis,
    Resume,
    AuditLog,
    ResumeVersion,
    ApplicationEvent,
    ApplicationNote,
    ApplicationContact,
)
from app.models.cover_letter import CoverLetter
from app.models.profile import (
    Profile,
    Experience,
    Education,
    Skill,
    Project,
    Certification,
)
from app.models.score import JobMatchScore
from app.models.batch import BatchJob
from app.models.notification import Notification
from app.models.analytics import AnalyticsSnapshot

__all__ = [
    # users
    "User",
    "UserPreference",
    "RefreshToken",
    "DeviceSession",
    # jobs
    "Job",
    "JobApplication",
    "JobImport",
    "JobAnalysis",
    "Resume",
    "AuditLog",
    "ResumeVersion",
    "ApplicationEvent",
    "ApplicationNote",
    "ApplicationContact",
    # documents
    "CoverLetter",
    # profile
    "Profile",
    "Experience",
    "Education",
    "Skill",
    "Project",
    "Certification",
    # intelligence
    "JobMatchScore",
    # operations
    "BatchJob",
    # notifications & analytics
    "Notification",
    "AnalyticsSnapshot",
]
