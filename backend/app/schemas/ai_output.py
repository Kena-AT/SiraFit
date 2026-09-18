"""Pydantic schemas for structured AI generation via Instructor (Sprint 7)."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Job Analysis Schemas
# ---------------------------------------------------------------------------


class AIJobAnalysisOutput(BaseModel):
    """Structured output for job analysis operations."""

    score: int = Field(default=0, description="Match score between 0 and 100")
    summary: str = Field(
        ..., min_length=10, description="2-3 sentence summary of role and candidate fit"
    )
    pros: List[str] = Field(
        default_factory=list, description="Strengths and strong alignment points"
    )
    cons: List[str] = Field(
        default_factory=list, description="Weaknesses or potential mismatch points"
    )
    skills_gap: List[str] = Field(
        default_factory=list, description="Missing required or preferred skills"
    )
    key_requirements: List[str] = Field(
        default_factory=list, description="Top requirements of the position"
    )
    seniority: str = Field(
        default="Mid",
        description="Seniority level: Junior, Mid, Senior, Staff, Lead, Director",
    )

    @field_validator("score", mode="before")
    @classmethod
    def _clamp_score(cls, v):
        try:
            return max(0, min(100, int(v)))
        except Exception:
            return 0

    def model_post_init(self, __context):
        self.score = max(0, min(100, self.score))
        self.pros = self.pros[:6]
        self.cons = self.cons[:6]
        self.skills_gap = self.skills_gap[:6]
        self.key_requirements = self.key_requirements[:6]


# ---------------------------------------------------------------------------
# Resume Generation Schemas
# ---------------------------------------------------------------------------


class AIResumeExperienceItem(BaseModel):
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company or organization name")
    location: Optional[str] = Field(
        default=None, description="City, State, Country or Remote"
    )
    period: str = Field(..., description="Date range, e.g. 'Jan 2022 - Present'")
    bullets: List[str] = Field(
        default_factory=list,
        description="Bullet points detailing achievements and metrics",
    )

    def model_post_init(self, __context):
        self.bullets = self.bullets[:6]


class AIResumeProjectItem(BaseModel):
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project summary and impact")
    url: Optional[str] = Field(default=None, description="URL or repository link")


class AIResumeEducationItem(BaseModel):
    institution: str = Field(..., description="School or university name")
    degree: str = Field(..., description="Degree or certificate title")
    field_of_study: Optional[str] = Field(
        default=None, description="Field of study or major"
    )
    period: str = Field(..., description="Years attended, e.g. '2018 - 2022'")


class AIResumeOutput(BaseModel):
    """Structured output for tailored resume generation."""

    name: str = Field(..., description="Candidate full name")
    email: str = Field(..., description="Candidate email address")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    location: Optional[str] = Field(default=None, description="City/Location")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    github: Optional[str] = Field(default=None, description="GitHub profile URL")
    website: Optional[str] = Field(default=None, description="Portfolio or website URL")
    summary: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="ATS-optimized professional summary",
    )
    experience: List[AIResumeExperienceItem] = Field(
        default_factory=list, description="Tailored experience items"
    )
    projects: List[AIResumeProjectItem] = Field(
        default_factory=list, description="Highlighted projects"
    )
    skills: List[str] = Field(
        default_factory=list, description="Relevant skills for target job"
    )
    education: List[AIResumeEducationItem] = Field(
        default_factory=list, description="Education records"
    )

    def model_post_init(self, __context):
        self.experience = self.experience[:10]
        self.projects = self.projects[:6]
        self.skills = list(dict.fromkeys(self.skills))[:30]
        self.education = self.education[:5]


# ---------------------------------------------------------------------------
# Cover Letter Generation Schemas
# ---------------------------------------------------------------------------


class AICoverLetterOutput(BaseModel):
    """Structured output for tailored cover letter generation."""

    salutation: Optional[str] = Field(
        default="Dear Hiring Manager,", description="Professional salutation"
    )
    body: str = Field(
        ..., min_length=50, description="The complete cover letter body (paragraphs)"
    )
    sign_off: Optional[str] = Field(
        default="Sincerely,", description="Closing sign-off, e.g. Sincerely,"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Key highlighted selling points used in the letter",
    )
