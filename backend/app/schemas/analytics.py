import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SalaryBenchmark(BaseModel):
    role: str
    currency: str
    period: str
    sample_size: int
    min_p50: Optional[float] = None
    max_p50: Optional[float] = None
    min_p25: Optional[float] = None
    max_p75: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class SkillGapItem(BaseModel):
    skill_id: Optional[uuid.UUID] = None
    skill: str
    frequency: int
    percentage: float
    priority: bool

    model_config = ConfigDict(from_attributes=True)


class SkillsGapResponse(BaseModel):
    analyzed_jobs: int
    current_skill_count: int
    skills: List[SkillGapItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class StageInsight(BaseModel):
    stage: str
    entered_count: int
    progressed_count: int
    dropped_count: int
    drop_off_rate: Optional[float] = None
    median_duration_hours: Optional[float] = None
    duration_sample_size: int

    model_config = ConfigDict(from_attributes=True)


class StallInsightsResponse(BaseModel):
    total_applications: int
    stages: List[StageInsight] = Field(default_factory=list)
    longest_median_stage: Optional[str] = None
    highest_drop_off_stage: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MetricsResponse(BaseModel):
    total_applications: int
    interview_rate: float
    avg_response_time_days: float
    offer_rate: float
    conversion_funnel: List[Dict[str, Any]]
    rejection_stages: List[Dict[str, Any]]
    skill_coverage: List[Dict[str, Any]]
    market_demand: List[Dict[str, Any]]
    top_technologies: List[Dict[str, Any]] = Field(default_factory=list)
    salary_medians: Dict[str, float] = Field(default_factory=dict)
    skill_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    # Sprint 10 expansion fields
    salary_benchmarks: List[SalaryBenchmark] = Field(default_factory=list)
    skills_gap_analysis: Optional[SkillsGapResponse] = None
    stall_insights: Optional[StallInsightsResponse] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
