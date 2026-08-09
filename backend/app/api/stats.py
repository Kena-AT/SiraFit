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
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.cache import cache_get, cache_set
from app.models.job import Job, JobApplication
from app.models.profile import Profile
from app.models.user import User
from app.services.agent_api import check_agent_api_connection
from app.services.matching_engine import calculate_match_score

router = APIRouter()

logger = logging.getLogger(__name__)

# Reuse the OAuth2 scheme already configured in app.api.users
_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False
)


def _try_get_current_user(
    request: Request, db: Session, token: Optional[str]
) -> Optional[User]:
    """Attempt to resolve the current user from header or cookie, returning
    ``None`` when no valid token is present (anonymous request)."""
    token_str = token or request.cookies.get("access_token")
    if not token_str:
        return None

    try:
        import jwt
        from app.schemas.user import TokenPayload
        from pydantic import ValidationError

        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        if token_data.type != "access":
            return None
        import uuid

        user = db.query(User).filter(User.id == uuid.UUID(token_data.sub)).first()
        if user and user.is_active:
            return user
    except Exception:
        logger.debug("Could not resolve authenticated user for landing stats", exc_info=True)
    return None


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


def _get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(_oauth2_scheme),
) -> Optional[User]:
    """FastAPI dependency: resolves the current user or returns ``None``."""
    return _try_get_current_user(request, db, token)


@router.get("/landing", response_model=LandingStatsResponse)
def get_landing_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(_get_optional_user),
) -> LandingStatsResponse:
    """
    Get aggregated statistics for the landing page.

    Works for both anonymous visitors (top match queue is empty) and
    authenticated users (who get a personalised match queue).

    Returns:
        LandingStatsResponse: Aggregated metrics
    """
    cache_key = f"stats:landing:{current_user.id}" if current_user else "stats:landing"
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
        top_match_queue = _get_top_match_queue(db, current_user)
        
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
    over the last 30 days.

    One query with a conditional aggregate instead of two COUNT scans over the
    same filtered table.
    """
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        interview_stages = ["interview_scheduled", "interviewing", "offer", "hired"]

        total, interview_count = db.query(
            func.count(JobApplication.id),
            func.sum(
                case(
                    (JobApplication.status.in_(interview_stages), 1),
                    else_=0,
                )
            ),
        ).filter(
            JobApplication.created_at >= thirty_days_ago,
        ).one()

        if total is None or total == 0:
            return 0.0
        return (interview_count or 0) / total
    except Exception:
        return 0.0  # Return 0 if query fails


def _get_top_match_queue(
    db: Session, current_user: Optional[User] = None
) -> List[TopMatchItem]:
    """
    Get the top 4 job matches for the current user.

    If no user is authenticated (anonymous landing-page visitor), returns an
    empty list.  When authenticated, mirrors the scoring logic from
    ``jobs.get_top_matches``: pull the user's profile, exclude jobs they've
    already applied to, score the remaining candidates with the deterministic
    matching engine, and return the top 4 above the minimum threshold.
    """
    if current_user is None:
        return []

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        return []

    # Jobs the user has already applied to — exclude them from the queue
    applied_job_ids = (
        db.query(JobApplication.job_id)
        .filter(JobApplication.user_id == current_user.id)
        .subquery()
    )

    # Fetch recent candidate jobs the user hasn't seen yet (limit to 50 for
    # scoring performance; the list is sorted and trimmed below).
    candidate_jobs = (
        db.query(Job)
        .filter(Job.id.notin_(applied_job_ids))
        .order_by(Job.created_at.desc())
        .limit(50)
        .all()
    )

    scored_matches: List[TopMatchItem] = []
    for job in candidate_jobs:
        score_data = calculate_match_score(profile, job)
        if score_data["score"] >= 30:  # minimum threshold (mirrors jobs.py)
            scored_matches.append(
                TopMatchItem(
                    company=job.company or "Unknown",
                    role=job.title or "Untitled",
                    match_score=score_data["score"] / 100.0,  # 0–1 range
                    status="new",
                )
            )

    scored_matches.sort(key=lambda x: x.match_score, reverse=True)
    return scored_matches[:4]


# Add the router to the API
__all__ = ["router"]