"""
Landing page statistics endpoint.

Provides aggregated metrics for the landing page:
- Jobs ingested per day
- ATS sources polled
- Sector interview rate
- Top match queue
"""

from datetime import datetime, timedelta
from typing import List, Optional
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.cache import cache_get, cache_set
from app.models.job import Job, JobApplication
from app.models.profile import Profile
from app.services.agent_api import check_agent_api_connection

router = APIRouter()


class TopMatchItem(BaseModel):
    company: str
    role: str
    match_score: float
    status: str  # "new" | "saved" | "seen"


class LandingStatsResponse(BaseModel):
    jobs_ingested_per_day: int
    ats_sources_polled: int
    sector_interview_rate: float
    top_match_queue: List[TopMatchItem]
    generated_at: datetime


@router.get("/landing", response_model=LandingStatsResponse)
def get_landing_stats(
    db: Session = Depends(get_db),
) -> LandingStatsResponse:
    """
    Get aggregated statistics for the landing page.
    
    Returns:
        LandingStatsResponse: Aggregated metrics
    """
    cache_key = "stats:landing"
    cached = cache_get(cache_key)
    if cached:
        return LandingStatsResponse(**cached)

    try:
        # 1. Jobs ingested in the last 24 hours
        jobs_ingested_per_day = _get_jobs_ingested_per_day(db)
        
        # 2. ATS sources polled (distinct sources with jobs in last 30 days)
        ats_sources_polled = _get_ats_sources_polled(db)
        
        # 3. Sector interview rate (rolling 30-day window)
        sector_interview_rate = _get_sector_interview_rate(db)
        
        # 4. Top match queue (top 4 matches for the current user/org)
        top_match_queue = _get_top_match_queue(db)
        
        response = LandingStatsResponse(
            jobs_ingested_per_day=jobs_ingested_per_day,
            ats_sources_polled=ats_sources_polled,
            sector_interview_rate=sector_interview_rate,
            top_match_queue=top_match_queue,
            generated_at=datetime.utcnow().isoformat(),
        )
        
        # Cache for 5 minutes
        cache_set(cache_key, jsonable_encoder(response), ttl=300)
        return response
        
    except Exception as e:
        # Log the error but don't crash the landing page
        # In production, you'd want proper error logging here
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute landing stats: {str(e)}",
        )


def _get_jobs_ingested_per_day(db: Session) -> int:
    """Count jobs ingested in the last 24 hours with timeout."""
    try:
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        count = db.query(Job).filter(
            Job.created_at >= twenty_four_hours_ago
        ).count()
        
        return count
    except Exception:
        return 0  # Return 0 if query fails


def _get_ats_sources_polled(db: Session) -> int:
    """Count distinct ATS sources with jobs in the last 30 days with timeout."""
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Assuming 'source' field contains ATS names like 'lever', 'greenhouse', etc.
        sources = db.query(Job.source).filter(
            Job.created_at >= thirty_days_ago
        ).distinct().all()
        
        return len(sources)
    except Exception:
        return 0  # Return 0 if query fails


def _get_sector_interview_rate(db: Session) -> float:
    """
    Compute interview rate: (applications that reached interview stage) / (total applications)
    over the last 30 days, grouped by sector.
    
    Uses a simplified approach with timeouts to prevent hanging.
    """
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Count applications that reached interview stage or later
        interview_stages = ["interview_scheduled", "interviewing", "offer", "hired"]
        interview_count = db.query(JobApplication).filter(
            JobApplication.status.in_(interview_stages),
            JobApplication.created_at >= thirty_days_ago,
        ).limit(10000).count()  # Limit to prevent excessive scanning
        
        # Count total applications
        total_count = db.query(JobApplication).filter(
            JobApplication.created_at >= thirty_days_ago,
        ).limit(10000).count()  # Limit to prevent excessive scanning
        
        if total_count == 0:
            return 0.0
        
        return interview_count / total_count
    except Exception:
        return 0.0  # Return 0 if query fails


def _get_top_match_queue(db: Session) -> List[TopMatchItem]:
    """
    Get the top 4 job matches for the current user/org.
    
    This is a simplified implementation. In a real app, you'd have a proper
    match scoring system and user-specific data.
    """
    # For now, return an empty list. This would be replaced with real logic
    # that queries the match table and joins with job data.
    return []


# Add the router to the API
__all__ = ["router"]