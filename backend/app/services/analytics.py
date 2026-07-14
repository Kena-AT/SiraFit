"""
Analytics service for generating metrics and snapshots.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.job import Job, JobApplication
from app.models.profile import Profile
from app.models.analytics import AnalyticsSnapshot


def _utcnow():
    return datetime.now(timezone.utc)


def generate_analytics_metrics(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
    """
    Generate comprehensive analytics metrics for a user.
    """
    # 1. Application metrics
    applications = db.query(JobApplication).filter(JobApplication.user_id == user_id).all()
    total_applications = len(applications)
    
    # Interview stages
    interview_stages = ["screening", "interview", "final_round"]
    interviewed = sum(1 for a in applications if a.status in interview_stages)
    interview_rate = (interviewed / total_applications * 100) if total_applications > 0 else 0
    
    # Offer rate
    offers = sum(1 for a in applications if a.status == "offer")
    offer_rate = (offers / total_applications * 100) if total_applications > 0 else 0
    
    # Average response time (for applications that got a response)
    response_times = []
    for app in applications:
        if app.updated_at and app.created_at:
            diff = app.updated_at - app.created_at
            response_times.append(diff.total_seconds() / 86400)  # days
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
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
        count = sum(1 for a in applications if a.status == status or (status == "applied" and a.status == "applied"))
        funnel.append([label, count])
    
    # 3. Rejection stages
    rejection_stages = [
        ("Resume screen", "rejected"),
        ("Recruiter call", "rejected"),
        ("Tech screen", "rejected"),
        ("Onsite", "rejected"),
    ]
    rejections = []
    for label, status in rejection_stages:
        count = sum(1 for a in applications if a.status == status)
        rejections.append([label, count])
    
    # 4. Skill coverage vs market demand
    # Get user skills
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    user_skills = set(s.name.lower() for s in profile.skills) if profile else set()
    
    # Get all skills from jobs the user has applied to
    job_ids = [a.job_id for a in applications]
    all_job_skills = set()
    if job_ids:
        jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
        for job in jobs:
            if job.tags:
                all_job_skills.update(s.lower() for s in job.tags)
    
    skill_coverage = []
    for skill in all_job_skills:
        you = 100 if skill in user_skills else 0
        market = 100  # placeholder - could be calculated from all jobs
        skill_coverage.append({
            "skill": skill.title(),
            "you": you,
            "market": market,
        })
    
    # 5. Market roles — aggregated from the actual jobs imported by this user
    # Count applications per job title (normalised), take the top 10
    from collections import Counter
    title_counter: Counter = Counter()
    all_imported_jobs = db.query(Job).all()
    for job in all_imported_jobs:
        # Normalise: strip seniority words and lowercase
        import re
        normalised = re.sub(
            r"\b(senior|junior|staff|principal|lead|mid|associate|sr\.|jr\.)\b",
            "",
            job.title,
            flags=re.IGNORECASE,
        ).strip().title()
        if normalised:
            title_counter[normalised] += 1

    top_roles = title_counter.most_common(8)
    market_roles = []
    for rank, (role, count) in enumerate(top_roles):
        demand = max(10, 100 - rank * 10)
        market_roles.append({
            "role": role,
            "demand": demand,
            "postings": count,
            "change": "+0%",  # would need historical data
        })

    # 6. Top technologies — frequency count from all job tags
    tag_counter: Counter = Counter()
    for job in all_imported_jobs:
        if job.tags:
            for tag in job.tags:
                tag_counter[tag.lower()] += 1

    total_tags = sum(tag_counter.values()) or 1
    top_technologies = [
        [tag.title(), round(count / total_tags * 100)]
        for tag, count in tag_counter.most_common(10)
    ] or [
        ["Python", 0], ["JavaScript", 0], ["React", 0], ["AWS", 0], ["Docker", 0]
    ]

    # 7. Salary medians — derived from imported jobs that have salary data
    salary_data = [
        (job.salary_min, job.salary_max, job.currency or "USD")
        for job in all_imported_jobs
        if job.salary_min or job.salary_max
    ]

    if salary_data:
        import statistics
        midpoints = [
            ((s_min or 0) + (s_max or 0)) / (2 if s_min and s_max else 1)
            for s_min, s_max, _ in salary_data
            if (s_min or 0) + (s_max or 0) > 0
        ]
        if midpoints:
            median_val = statistics.median(midpoints)
            currency = salary_data[0][2]
            salary_medians = [
                ["Median (your imports)", f"{currency}{int(median_val / 1000)}k"],
                ["25th percentile", f"{currency}{int(sorted(midpoints)[len(midpoints) // 4] / 1000)}k"],
                ["75th percentile", f"{currency}{int(sorted(midpoints)[3 * len(midpoints) // 4] / 1000)}k"],
            ]
        else:
            salary_medians = [["No salary data", "—"]]
    else:
        salary_medians = [["No salary data", "—"]]
    
    return {
        "total_applications": total_applications,
        "interview_rate": round(interview_rate, 1),
        "avg_response_time_days": round(avg_response_time, 1),
        "offer_rate": round(offer_rate, 1),
        "conversion_funnel": funnel,
        "rejection_stages": rejections,
        "skill_coverage": skill_coverage,
        "market_roles": market_roles,
        "top_technologies": top_technologies,
        "salary_medians": salary_medians,
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
    return db.query(AnalyticsSnapshot).filter(
        AnalyticsSnapshot.user_id == user_id
    ).order_by(AnalyticsSnapshot.snapshot_date.desc()).first()


def get_snapshots(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
    """
    Get paginated analytics snapshots for a user.
    """
    query = db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.user_id == user_id)
    total = query.count()
    snapshots = query.order_by(AnalyticsSnapshot.snapshot_date.desc()).offset(skip).limit(limit).all()
    return snapshots, total