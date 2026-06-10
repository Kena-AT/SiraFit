from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
import uuid

# --- Shared Config ---
class ProfileBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# --- Experience ---
class ExperienceBase(ProfileBaseModel):
    title: str = Field(..., max_length=255)
    company: str = Field(..., max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceUpdate(ExperienceBase):
    pass

class ExperienceResponse(ExperienceBase):
    id: uuid.UUID

# --- Education ---
class EducationBase(ProfileBaseModel):
    institution: str = Field(..., max_length=255)
    degree: Optional[str] = Field(None, max_length=255)
    field_of_study: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

class EducationCreate(EducationBase):
    pass

class EducationUpdate(EducationBase):
    pass

class EducationResponse(EducationBase):
    id: uuid.UUID

# --- Skill ---
class SkillBase(ProfileBaseModel):
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    proficiency: Optional[str] = Field(None, max_length=50)

class SkillCreate(SkillBase):
    pass

class SkillUpdate(SkillBase):
    pass

class SkillResponse(SkillBase):
    id: uuid.UUID

# --- Project ---
class ProjectBase(ProfileBaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    url: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: uuid.UUID

# --- Certification ---
class CertificationBase(ProfileBaseModel):
    name: str = Field(..., max_length=255)
    issuer: str = Field(..., max_length=255)
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    credential_id: Optional[str] = Field(None, max_length=255)
    credential_url: Optional[str] = Field(None, max_length=255)

class CertificationCreate(CertificationBase):
    pass

class CertificationUpdate(CertificationBase):
    pass

class CertificationResponse(CertificationBase):
    id: uuid.UUID

# --- Profile ---
class ProfileBase(ProfileBaseModel):
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    headline: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    linkedin: Optional[str] = Field(None, max_length=255)
    github: Optional[str] = Field(None, max_length=255)

class ProfileCreate(ProfileBase):
    # Using monolithic creation/update for autosave ease
    experiences: Optional[List[ExperienceCreate]] = []
    educations: Optional[List[EducationCreate]] = []
    skills: Optional[List[SkillCreate]] = []
    projects: Optional[List[ProjectCreate]] = []
    certifications: Optional[List[CertificationCreate]] = []

class ProfileUpdate(ProfileBase):
    # Monolithic update accepts lists of items to fully replace the existing ones
    experiences: Optional[List[ExperienceCreate]] = None
    educations: Optional[List[EducationCreate]] = None
    skills: Optional[List[SkillCreate]] = None
    projects: Optional[List[ProjectCreate]] = None
    certifications: Optional[List[CertificationCreate]] = None

class ProfileResponse(ProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    experiences: List[ExperienceResponse] = []
    educations: List[EducationResponse] = []
    skills: List[SkillResponse] = []
    projects: List[ProjectResponse] = []
    certifications: List[CertificationResponse] = []
