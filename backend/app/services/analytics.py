"""
Analytics service for generating metrics and snapshots.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.models.job import Job, JobApplication
from app.models.profile import Profile, Skill
from app.models.analytics import AnalyticsSnapshot
from app.models.score import JobMatchScore


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
    
    # 5. Market roles (mock data for now - could be from external API)
    market_roles = [
        {"role": "Software Engineer", "demand": 95, "postings": 12500, "change": "+12%"},
        {"role": "Backend Engineer", "demand": 88, "postings": 8200, "change": "+8%"},
        {"role": "Full Stack Engineer", "demand": 82, "postings": 7100, "change": "+5%"},
        {"role": "DevOps Engineer", "demand": 78, "postings": 5400, "change": "+15%"},
        {"role": "Frontend Engineer", "demand": 75, "postings": 4800, "change": "+3%"},
    ]
    
    # 6. Top technologies
    top_technologies = [
        ["TypeScript", 71],
        ["Python", 64],
        ["React", 58],
        ["AWS", 56],
        ["Kubernetes", 41],
    ]
    
    # 7. Salary medians
    salary_medians = [
        ["SF Bay Area", "$165k"],
        ["NYC", "$155k"],
        ["Remote (US)", "$145k"],
        ["Berlin", "€68k"],
        ["London", "£72k"],
    ]
    
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