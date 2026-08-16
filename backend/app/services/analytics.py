"""
Analytics service for generating metrics and snapshots.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy.orm import Session, joinedload

from app.models.job import Job, JobApplication
from app.models.profile import Profile
from app.models.analytics import AnalyticsSnapshot


def _utcnow():
    return datetime.now(timezone.utc)


def generate_analytics_metrics(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
    """
    Generate comprehensive analytics metrics for a user.

    Performance considerations:
    - Uses joinedload to eagerly load related Job objects to avoid N+1
      query issues when iterating over applications
    - Database-level aggregations used where possible
    """
    # 1. Application metrics - eager load Job relationship to avoid N+1
    applications = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == user_id)
        .options(joinedload(JobApplication.job))
        .all()
    )
    total_applications = len(applications)

    # Interview stages
    interview_stages = ["screening", "interview", "final_round"]
    interviewed = sum(1 for a in applications if a.status in interview_stages)
    interview_rate = (
        (interviewed / total_applications * 100) if total_applications > 0 else 0
    )

    # Offer rate
    offers = sum(1 for a in applications if a.status == "offer")
    offer_rate = (offers / total_applications * 100) if total_applications > 0 else 0

    # Average response time (for applications that got a response)
    response_times = []
    for app in applications:
        if app.updated_at and app.created_at:
            diff = app.updated_at - app.created_at
            response_times.append(diff.total_seconds() / 86400)  # days
    avg_response_time = (
        sum(response_times) / len(response_times) if response_times else 0
    )

    # 2. Conversion funnel
    funnel_stages = [
        ("Applied", "applied"),
        ("Recruiter screen", "screening"),
        ("Tech screen", "interview"),
        ("Onsite / final", "final_round"),
        ("Offer", "offer"),
    ]
    funnel = []
    for label, status in funnel_stages:
        count = sum(
            1
            for a in applications
            if a.status == status or (status == "applied" and a.status == "applied")
        )
        funnel.append({"stage": label, "count": count})

    # 3. Rejection stages (now using rejection_stage column for accurate tracking)
    rejection_stages = [
        ("Resume screen", "resume_screen"),
        ("Recruiter call", "recruiter_call"),
        ("Tech screen", "tech_screen"),
        ("Onsite", "onsite"),
        ("Offer declined", "offer_declined"),
    ]
    rejections = []
    for label, stage in rejection_stages:
        count = sum(
            1
            for a in applications
            if a.status == "rejected" and a.rejection_stage == stage
        )
        rejections.append({"stage": label, "count": count})

    # 4. Skill coverage vs market demand
    # Get user skills
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    user_skills = set(s.name.lower() for s in profile.skills) if profile else set()

    # Get all skills from jobs the user has applied to
    job_ids = [a.job_id for a in applications]
    all_job_skills = set()
    skill_job_counts: Dict[str, int] = {}
    if job_ids:
        jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
        for job in jobs:
            if job.tags:
                for tag in job.tags:
                    tag_lower = tag.lower()
                    all_job_skills.add(tag_lower)
                    skill_job_counts[tag_lower] = skill_job_counts.get(tag_lower, 0) + 1

    total_applied_with_skills = len(jobs) if job_ids else 0
    skill_coverage = []
    for skill in all_job_skills:
        you = 100 if skill in user_skills else 0
        # Market = proportion of applied jobs that have this skill, as a percentage
        market = int(skill_job_counts.get(skill, 0) / max(1, total_applied_with_skills) * 100)
        skill_coverage.append(
            {
                "skill": skill.title(),
                "you": you,
                "market": market,
            }
        )

    # 5. Market demand — aggregated from the actual jobs imported by this user.
    # Count applications per job title (normalised), take the top 8.
    from collections import Counter

    # Get jobs the user has applied to (not all jobs globally)
    applied_job_ids = [a.job_id for a in applications]
    title_counter: Counter = Counter()
    if applied_job_ids:
        jobs = db.query(Job).filter(Job.id.in_(applied_job_ids)).all()
        for job in jobs:
            # Normalise: strip seniority words and lowercase
            import re

            normalised = (
                re.sub(
                    r"\b(senior|junior|staff|principal|lead|mid|associate|sr\.|jr\.)\b",
                    "",
                    job.title,
                    flags=re.IGNORECASE,
                )
                .strip()
                .title()
            )
            if normalised:
                title_counter[normalised] += 1

    top_roles = title_counter.most_common(8)
    market_demand = []

    # Calculate market trend using historical snapshots (user-specific)
    from app.models.analytics import AnalyticsSnapshot
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    current_period_start = now - timedelta(days=30)
    previous_period_start = now - timedelta(days=60)

    # Count jobs applied to by this user in current/previous periods
    current_count = (
        db.query(Job)
        .join(JobApplication, JobApplication.job_id == Job.id)
        .filter(
            JobApplication.user_id == user_id,
            Job.created_at >= current_period_start,
        )
        .count()
    )
    previous_count = (
        db.query(Job)
        .join(JobApplication, JobApplication.job_id == Job.id)
        .filter(
            JobApplication.user_id == user_id,
            Job.created_at >= previous_period_start,
            Job.created_at < current_period_start,
        )
        .count()
    )

    if previous_count > 0:
        trend_pct = ((current_count - previous_count) / previous_count) * 100
    else:
        trend_pct = 0.0

    trend_str = f"{'+' if trend_pct >= 0 else ''}{trend_pct:.1f}%"

    for rank, (role, count) in enumerate(top_roles):
        # Scale demand from postings count: each posting contributes ~10%, capped at 100%
        demand = min(100, count * 10)
        market_demand.append(
            {
                "role": role,
                "demand": demand,
                "postings": count,
                "change": trend_str,
            }
        )

    # 6. Top technologies (skills from applied jobs)
    from collections import Counter as SkillCounter

    skill_counter: SkillCounter = SkillCounter()
    for app in applications:
        if app.job and app.job.tags:
            for tag in app.job.tags:
                skill_counter[tag.lower()] += 1

    top_technologies = [
        {"skill": skill.title(), "count": count}
        for skill, count in skill_counter.most_common(10)
    ]

    # 7. Salary medians by sector
    from sqlalchemy import func as sql_func

    salary_data = (
        db.query(
            Job.company,
            sql_func.avg((Job.salary_min + Job.salary_max) / 2).label("median"),
        )
        .join(JobApplication)
        .filter(
            JobApplication.user_id == user_id,
            Job.salary_min.isnot(None),
            Job.salary_max.isnot(None),
        )
        .group_by(Job.company)
        .all()
    )

    salary_medians = {company: float(median) for company, median in salary_data}

    # 8. Skill gaps (user skills vs job requirements)
    user_skills_set = set(s.name.lower() for s in profile.skills) if profile else set()
    required_skills: SkillCounter = SkillCounter()
    for app in applications:
        if app.job and app.job.tags:
            for tag in app.job.tags:
                required_skills[tag.lower()] += 1

    skill_gaps = []
    for skill, freq in required_skills.most_common(10):
        if skill not in user_skills_set:
            skill_gaps.append(
                {
                    "skill": skill.title(),
                    "demand_frequency": freq,
                    "impact_score": min(freq * 10, 100),
                }
            )

    return {
        "total_applications": total_applications,
        "interview_rate": round(interview_rate, 1),
        "avg_response_time_days": round(avg_response_time, 1),
        "offer_rate": round(offer_rate, 1),
        "conversion_funnel": funnel,
        "rejection_stages": rejections,
        "skill_coverage": skill_coverage,
        "market_demand": market_demand,
        "top_technologies": top_technologies,
        "salary_medians": salary_medians,
        "skill_gaps": skill_gaps,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def create_analytics_snapshot(db: Session, user_id: uuid.UUID) -> AnalyticsSnapshot:
    """
    Create a new analytics snapshot for the user.
    """
    metrics = generate_analytics_metrics(db, user_id)

    snapshot = AnalyticsSnapshot(
        user_id=user_id,
        snapshot_date=_utcnow(),
        metrics=metrics,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_latest_snapshot(db: Session, user_id: uuid.UUID) -> AnalyticsSnapshot | None:
    """
    Get the most recent analytics snapshot for a user.
    """
    return (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.user_id == user_id)
        .order_by(AnalyticsSnapshot.snapshot_date.desc())
        .first()
    )


def get_snapshots(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
    """
    Get paginated analytics snapshots for a user.
    """
    query = db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.user_id == user_id)
    total = query.count()
    snapshots = (
        query.order_by(AnalyticsSnapshot.snapshot_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return snapshots, total
