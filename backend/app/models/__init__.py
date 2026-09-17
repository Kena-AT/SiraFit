from app.models.user import User, UserPreference, RefreshToken, DeviceSession
from app.models.oauth import OAuthAccount
from app.models.totp import TOTPSecret, RecoveryCode
from app.models.job import (
    Job,
    JobApplication,
    JobImport,
    JobImportItem,
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
from app.models.profile_version import ProfileVersion
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.scrape_history import ScrapeHistory
from app.models.score import JobMatchScore
from app.models.batch import BatchJob
from app.models.user_session import UserSession
from app.models.session_access_log import SessionAccessLog
from app.models.notification import Notification
from app.models.analytics import AnalyticsSnapshot
from app.models.extension_token import ExtensionToken

__all__ = [
    # users
    "User",
    "UserPreference",
    "RefreshToken",
    "DeviceSession",
    "UserSession",
    "SessionAccessLog",
    "ExtensionToken",
    # auth
    "OAuthAccount",
    "TOTPSecret",
    "RecoveryCode",
    # jobs
    "Job",
    "JobApplication",
    "JobImport",
    "JobImportItem",
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
    "ProfileVersion",
    "SkillTaxonomy",
    "ScrapeHistory",
    # intelligence
    "JobMatchScore",
    # operations
    "BatchJob",
    # notifications & analytics
    "Notification",
    "AnalyticsSnapshot",
]
