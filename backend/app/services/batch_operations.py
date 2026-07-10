"""
Item-level handlers for batch operations.
Each processes a single job_id and returns a result dict.
Reuses existing services where possible.
"""
import uuid
import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.job import Job, JobAnalysis
from app.models.profile import Profile
from app.models.score import JobMatchScore
from app.services.job_analysis import run_job_analysis
from app.services.matching_engine import calculate_match_score

logger = logging.getLogger(__name__)

VALID_OPERATION_TYPES = {"analyze", "score", "tag", "archive"}


async def batch_analyze_item(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    params: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Trigger AI analysis for a single job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    analysis = await run_job_analysis(
        job=job,
        db=db,
        api_key=params.get("api_key"),
        provider=params.get("provider"),
        model=params.get("model"),
        user_id=str(user_id),
    )
    return {"score": analysis.score, "status": analysis.status, "summary": analysis.summary[:200] if analysis.summary else ""}


def batch_score_item(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    params: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Calculate match score for a single job against user profile."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise ValueError(f"Profile for user {user_id} not found")

    score_data = calculate_match_score(profile, job)

    # Upsert JobMatchScore
    existing = db.query(JobMatchScore).filter(
        JobMatchScore.user_id == user_id,
        JobMatchScore.job_id == job_id,
    ).first()

    if existing:
        existing.score = score_data["score"]
        existing.breakdown = score_data["breakdown"]
        existing.explanation = score_data["explanation"]
    else:
        new_score = JobMatchScore(
            user_id=user_id,
            job_id=job_id,
            score=score_data["score"],
            breakdown=score_data["breakdown"],
            explanation=score_data["explanation"],
        )
        db.add(new_score)

    db.commit()
    return {"score": score_data["score"], "breakdown": score_data["breakdown"]}


def batch_tag_item(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    params: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Add or remove tags on a single job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    tags_to_modify = set(params.get("tags", []))
    action = params.get("action", "add")
    current_tags = set(job.tags or [])

    if action == "add":
        current_tags.update(tags_to_modify)
    elif action == "remove":
        current_tags.difference_update(tags_to_modify)
    else:
        raise ValueError(f"Invalid action: {action}")

    job.tags = list(current_tags)
    db.commit()
    return {"tags": job.tags, "action": action}


def batch_archive_item(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    params: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Archive a job or application."""
    target = params.get("target", "jobs")

    if target == "jobs":
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        job.source = "archived"
        db.commit()
        return {"archived": True, "target": "jobs"}
    elif target == "applications":
        from app.models.job import JobApplication
        app = db.query(JobApplication).filter(
            JobApplication.id == job_id,
            JobApplication.user_id == user_id
        ).first()
        if not app:
            raise ValueError(f"Application {job_id} not found")
        app.status = "archived"
        db.commit()
        return {"archived": True, "target": "applications"}
    else:
        raise ValueError(f"Invalid target: {target}")