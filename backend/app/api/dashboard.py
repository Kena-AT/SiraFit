from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import JobApplication, Resume, AuditLog
from app.schemas.dashboard import DashboardStats
from app.core.cache import cache_get, cache_set

router = APIRouter()

_DASHBOARD_TTL = 30


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve dashboard statistics for the current user (cached for 30s)."""
    cache_key = f"dashboard:stats:{current_user.id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # 1. Count active applications
    active_apps = (
        db.query(func.count(JobApplication.id))
        .filter(
            JobApplication.user_id == current_user.id,
            JobApplication.status.notin_(["rejected", "withdrawn"]),
        )
        .scalar()
        or 0
    )

    # 2. Count resumes generated
    resumes_generated = (
        db.query(func.count(Resume.id))
        .filter(Resume.user_id == current_user.id)
        .scalar()
        or 0
    )

    # 3. Count jobs scored (applications with a score)
    jobs_scored = (
        db.query(func.count(JobApplication.id))
        .filter(
            JobApplication.user_id == current_user.id, JobApplication.score.isnot(None)
        )
        .scalar()
        or 0
    )

    # 4. Recent activity
    recent_activity = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(5)
        .all()
    )

    result = DashboardStats(
        active_applications=active_apps,
        resumes_generated=resumes_generated,
        jobs_scored=jobs_scored,
        recent_activity=recent_activity,
    )
    cache_set(cache_key, result.model_dump(mode="json"), ttl=_DASHBOARD_TTL)
    return result
