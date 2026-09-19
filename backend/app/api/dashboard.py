from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User, UserPreference
from app.models.job import Job, JobApplication, Resume, AuditLog, JobImport
from app.models.score import JobMatchScore
from app.schemas.dashboard import (
    DashboardStats,
    AuditLogItem,
    MarketPulseResponse,
    MarketPulseTag,
    BriefingResponse,
)
from app.core.cache import cache_get, cache_set

router = APIRouter()

_DASHBOARD_TTL = 30  # seconds; keep frontend staleTime in sync


def _compute_stats(db: Session, user: User) -> DashboardStats:
    """Compute all dashboard aggregates for a user. Shared by GET /stats and /briefing."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    active_apps = (
        db.query(func.count(JobApplication.id))
        .filter(
            JobApplication.user_id == user.id,
            JobApplication.status.notin_(["rejected", "withdrawn"]),
        )
        .scalar()
        or 0
    )

    resumes_generated = (
        db.query(func.count(Resume.id)).filter(Resume.user_id == user.id).scalar() or 0
    )

    match_scores_count = (
        db.query(func.count(JobMatchScore.id))
        .filter(JobMatchScore.user_id == user.id)
        .scalar()
        or 0
    )
    app_scores_count = (
        db.query(func.count(JobApplication.id))
        .filter(JobApplication.user_id == user.id, JobApplication.score.isnot(None))
        .scalar()
        or 0
    )
    jobs_scored = max(match_scores_count, app_scores_count)

    total_jobs = db.query(func.count(Job.id)).scalar() or 0

    upcoming_followups_count = (
        db.query(func.count(JobApplication.id))
        .filter(
            JobApplication.user_id == user.id,
            JobApplication.follow_up_at.isnot(None),
            JobApplication.follow_up_at >= now,
            JobApplication.follow_up_at <= now + timedelta(days=7),
            JobApplication.status.notin_(["rejected", "withdrawn"]),
        )
        .scalar()
        or 0
    )

    recent_activity_records = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(8)
        .all()
    )
    recent_activity = [
        AuditLogItem(
            id=r.id,
            action=r.action,
            entity_type=r.entity_type,
            created_at=r.created_at,
            details=r.details,
        )
        for r in recent_activity_records
    ]

    return DashboardStats(
        active_applications=active_apps,
        resumes_generated=resumes_generated,
        jobs_scored=jobs_scored,
        recent_activity=recent_activity,
        total_jobs=total_jobs,
        upcoming_followups_count=upcoming_followups_count,
    )


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve dashboard statistics for the current user (cached for 30s)."""
    cache_key = f"dashboard:stats:v2:{current_user.id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    result = _compute_stats(db, current_user)
    cache_set(cache_key, result.model_dump(mode="json"), ttl=_DASHBOARD_TTL)
    return result


@router.get("/market-pulse", response_model=MarketPulseResponse)
def get_market_pulse(
    limit_jobs: int = 500,
    top_n: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Tag-frequency analysis across the job pool — powers the "Market pulse"
    widget. The frontend diffs these tags against the user's profile skills.
    Cached for 10 minutes (tag distribution changes slowly).
    """
    cache_key = f"dashboard:pulse:{limit_jobs}:{top_n}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    jobs = (
        db.query(Job.id, Job.tags)
        .order_by(Job.created_at.desc())
        .limit(max(1, min(limit_jobs, 2000)))
        .all()
    )

    counts: dict[str, int] = {}
    analyzed = 0
    for _, tags in jobs:
        if not tags:
            continue
        analyzed += 1
        for tag in tags:
            if not isinstance(tag, str):
                continue
            t = tag.strip()
            if t:
                counts[t] = counts.get(t, 0) + 1

    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[
        : max(1, min(top_n, 30))
    ]
    pct_base = analyzed or 1
    result = MarketPulseResponse(
        total_jobs_analyzed=analyzed,
        top_tags=[
            MarketPulseTag(tag=t, count=c, pct=round(c * 100 / pct_base))
            for t, c in top
        ],
    )
    cache_set(cache_key, result.model_dump(mode="json"), ttl=600)
    return result


@router.post("/briefing", response_model=BriefingResponse)
async def get_daily_briefing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    AI-generated daily briefing (3 short bullets) built from the user's live
    dashboard data via their own configured provider key (BYOK with automatic
    multi-provider fallback). One generation per user per day.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache_key = f"dashboard:briefing:{current_user.id}:{today}"
    cached = cache_get(cache_key)
    if cached is not None:
        return BriefingResponse(**cached)

    from app.services.ai_keys import build_candidates
    from app.services.ai import complete_with_fallback

    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    candidates = build_candidates(
        db=db,
        user_id=current_user.id,
        provider=(prefs.ai_provider if prefs else None) or None,
        model=(prefs.ai_model if prefs else None) or None,
    )
    if not candidates:
        raise HTTPException(
            status_code=503,
            detail="No AI provider key configured — configure one in Settings → AI.",
        )

    stats = _compute_stats(db, current_user)

    # Follow-up context for the prompt.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    overdue = (
        db.query(func.count(JobApplication.id))
        .filter(
            JobApplication.user_id == current_user.id,
            JobApplication.follow_up_at.isnot(None),
            JobApplication.follow_up_at < now,
            JobApplication.status.notin_(["rejected", "withdrawn"]),
        )
        .scalar()
        or 0
    )

    week_ago = now - timedelta(days=7)
    imports_last_7d = (
        db.query(func.count(JobImport.id))
        .filter(JobImport.user_id == current_user.id, JobImport.created_at >= week_ago)
        .scalar()
        or 0
    )

    context = (
        f"Active applications: {stats.active_applications}. "
        f"Total jobs in pool: {stats.total_jobs}. "
        f"Resumes generated: {stats.resumes_generated}. "
        f"Applications scored: {stats.jobs_scored}. "
        f"Follow-ups scheduled within 7 days: {stats.upcoming_followups_count}. "
        f"Overdue follow-ups: {overdue}. "
        f"Imports in last 7 days: {imports_last_7d}."
    )

    system_prompt = (
        "You are a concise career coach. Using ONLY the candidate's job-search data "
        "provided below, write a daily briefing of EXACTLY 3 bullet points, each on its "
        "own line starting with '• '. Bullet 1: the most urgent action (follow-ups/overdue). "
        "Bullet 2: pipeline observation with one number. Bullet 3: one concrete suggestion "
        "to improve momentum this week. Max 20 words per bullet. No preamble, no markdown."
    )

    try:
        briefing_text = await complete_with_fallback(
            context, candidates, system=system_prompt, max_tokens=220
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"All AI providers failed: {exc}")

    result = BriefingResponse(briefing=briefing_text.strip(), date=today)
    cache_set(cache_key, result.model_dump(mode="json"), ttl=3600 * 12)
    return result
