"""AI extraction and resume review service for job imports.

Pipes scraped job content or pasted text directly to the AI model selected
in the user's settings, extracting structured job fields (salary, title, company,
work mode, skills) and generating an executive summary and resume compatibility review.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.job import Job, JobAnalysis
from app.models.profile import Profile
from app.models.user import UserPreference
from app.schemas.ai_output import AIJobAnalysisOutput, AIJobExtractionOutput
from app.services.ai_keys import build_candidates, get_user_fallback_order
from app.services.structured_ai import structured_completion_with_fallback
from app.services.ai import keyword_fallback

logger = logging.getLogger(__name__)


def _serialize_profile_summary(profile: Optional[Profile], db: Session) -> str:
    """Format the candidate profile and skills for AI context."""
    if not profile:
        return "No candidate profile provided."

    parts = []
    if profile.headline:
        parts.append(f"Professional Headline: {profile.headline}")
    if profile.summary:
        parts.append(f"Summary: {profile.summary}")

    if profile.skills:
        skill_names = [s.name for s in profile.skills if s.name]
        if skill_names:
            parts.append(f"Skills: {', '.join(skill_names)}")

    if profile.experiences:
        exp_lines = []
        for exp in profile.experiences[:5]:
            title = exp.title or "Role"
            comp = exp.company or "Company"
            desc = (exp.description or "")[:200]
            exp_lines.append(f"- {title} at {comp}: {desc}")
        if exp_lines:
            parts.append("Recent Experience:\n" + "\n".join(exp_lines))

    if profile.educations:
        edu_lines = []
        for edu in profile.educations[:2]:
            deg = edu.degree or "Degree"
            inst = edu.institution or "Institution"
            edu_lines.append(f"- {deg} from {inst}")
        if edu_lines:
            parts.append("Education:\n" + "\n".join(edu_lines))

    return "\n\n".join(parts) if parts else "Candidate Profile is empty."


async def extract_and_review_job_with_ai(
    raw_text: str,
    db: Session,
    user_id: uuid.UUID,
    url: Optional[str] = None,
    platform: Optional[str] = None,
    job: Optional[Job] = None,
) -> Optional[Dict[str, Any]]:
    """Extract job data and perform an AI resume compatibility review in one pass.

    Uses the user's preferred AI model from Settings (with fallback chain).
    If a ``job`` model instance is supplied, updates missing job attributes and persists
    the resulting ``JobAnalysis`` record directly into the database.
    """
    if not raw_text or len(raw_text.strip()) < 50:
        if job:
            _apply_fallback_analysis(db, job)
        return None

    # Resolve candidate AI models based on user preference and keys
    candidates = build_candidates(
        db=db,
        user_id=str(user_id),
        fallback_order=get_user_fallback_order(db, str(user_id)),
    )
    if not candidates:
        logger.info("No AI candidates configured for user %s; using fallback analysis", user_id)
        if job:
            _apply_fallback_analysis(db, job)
        return None

    # Load candidate profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    candidate_context = _serialize_profile_summary(profile, db)

    # Truncate raw input if excessive to keep latency low
    truncated_input = raw_text[:7000]

    system_prompt = (
        "You are an elite career strategist and technical recruiter. "
        "Analyze the provided job posting and candidate profile. "
        "Extract clean, verified metadata for the job, and perform a deep, honest "
        "compatibility review evaluating the candidate's resume against the role's requirements."
    )

    user_prompt = (
        f"## JOB POSTING TEXT (Source: {platform or url or 'Pasted text'})\n"
        f"{truncated_input}\n\n"
        f"## CANDIDATE PROFILE / RESUME\n"
        f"{candidate_context}\n\n"
        "Please extract all job details accurately (especially salary min/max and currency if mentioned), "
        "write an executive summary of the role, and assess the candidate's compatibility."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        # 1. Structured Job Extraction
        extracted_data, _ = await structured_completion_with_fallback(
            operation="job_import_extraction",
            response_model=AIJobExtractionOutput,
            messages=messages,
            candidates=candidates,
            db=db,
            user_id=user_id,
        )

        # 2. Structured Resume Compatibility Review
        analysis_data, _ = await structured_completion_with_fallback(
            operation="job_import_analysis",
            response_model=AIJobAnalysisOutput,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"## EXTRACTED JOB: {extracted_data.title} at {extracted_data.company}\n"
                        f"Description: {extracted_data.description[:3000]}\n\n"
                        f"## CANDIDATE PROFILE:\n{candidate_context}\n\n"
                        "Evaluate fit, compute compatibility score (0-100), identify matching strengths, "
                        "skill gaps, and provide actionable resume tailoring recommendations."
                    ),
                },
            ],
            candidates=candidates,
            db=db,
            user_id=user_id,
        )

        # If job record provided, update missing/generic fields and save JobAnalysis
        if job:
            if extracted_data.title and job.title in ("Unknown Position", "Unknown Job", ""):
                job.title = extracted_data.title
            if extracted_data.company and job.company in ("Unknown Company", "Unknown Source", ""):
                job.company = extracted_data.company
            if extracted_data.location and not job.location:
                job.location = extracted_data.location
            if extracted_data.salary_min and job.salary_min is None:
                job.salary_min = extracted_data.salary_min
                job.salary_max = extracted_data.salary_max
                job.currency = extracted_data.currency or job.currency or "USD"
            if extracted_data.tags and not job.tags:
                job.tags = extracted_data.tags

            analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).first()
            if not analysis:
                analysis = JobAnalysis(job_id=job.id)
                db.add(analysis)

            analysis.score = analysis_data.score
            analysis.fit_verdict = analysis_data.fit_verdict
            analysis.summary = analysis_data.summary
            analysis.role_overview = analysis_data.role_overview or extracted_data.role_overview
            analysis.core_responsibilities = analysis_data.core_responsibilities
            analysis.required_qualifications = analysis_data.required_qualifications
            analysis.nice_to_have = analysis_data.nice_to_have
            analysis.compensation_notes = analysis_data.compensation_notes
            analysis.pros = analysis_data.pros
            analysis.cons = analysis_data.cons
            analysis.skills_gap = analysis_data.skills_gap
            analysis.key_requirements = analysis_data.key_requirements or extracted_data.key_requirements
            analysis.tailoring_recommendations = analysis_data.tailoring_recommendations
            analysis.seniority = analysis_data.seniority or extracted_data.seniority or "Mid"
            analysis.status = "done"
            db.commit()
            db.refresh(analysis)

        return {
            "title": extracted_data.title,
            "company": extracted_data.company,
            "location": extracted_data.location,
            "work_mode": extracted_data.work_mode,
            "seniority": extracted_data.seniority,
            "salary_min": extracted_data.salary_min,
            "salary_max": extracted_data.salary_max,
            "currency": extracted_data.currency or "USD",
            "tags": extracted_data.tags,
            "description": extracted_data.description,
            "role_overview": extracted_data.role_overview,
            "analysis": {
                "score": analysis_data.score,
                "fit_verdict": analysis_data.fit_verdict,
                "summary": analysis_data.summary,
                "role_overview": analysis_data.role_overview or extracted_data.role_overview,
                "core_responsibilities": analysis_data.core_responsibilities,
                "required_qualifications": analysis_data.required_qualifications,
                "nice_to_have": analysis_data.nice_to_have,
                "compensation_notes": analysis_data.compensation_notes,
                "pros": analysis_data.pros,
                "cons": analysis_data.cons,
                "skills_gap": analysis_data.skills_gap,
                "key_requirements": analysis_data.key_requirements or extracted_data.key_requirements,
                "tailoring_recommendations": analysis_data.tailoring_recommendations,
                "seniority": analysis_data.seniority or extracted_data.seniority or "Mid",
            },
        }

    except Exception as exc:
        logger.warning("AI extraction/review encountered error for user %s: %s", user_id, exc)
        if job:
            _apply_fallback_analysis(db, job)
        return None


def _apply_fallback_analysis(db: Session, job: Job) -> None:
    """Apply keyword-based fallback analysis to job if AI is not configured or fails."""
    try:
        fb = keyword_fallback(job.title, job.description or "")
        analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).first()
        if not analysis:
            analysis = JobAnalysis(job_id=job.id)
            db.add(analysis)

        analysis.score = fb.score
        analysis.fit_verdict = "Potential Match"
        analysis.summary = fb.summary
        analysis.role_overview = (job.description or "")[:300] if job.description else None
        analysis.core_responsibilities = []
        analysis.required_qualifications = []
        analysis.nice_to_have = []
        analysis.compensation_notes = None
        analysis.pros = fb.pros
        analysis.cons = fb.cons
        analysis.skills_gap = fb.skills_gap
        analysis.key_requirements = fb.key_requirements
        analysis.tailoring_recommendations = [
            "Tailor your headline and core skills to match the job requirements directly."
        ]
        analysis.seniority = fb.seniority
        analysis.status = "done"
        db.commit()
    except Exception as err:
        logger.warning("Failed to apply fallback analysis: %s", err)
        db.rollback()


def extract_and_review_job_sync(
    raw_text: str,
    db: Session,
    user_id: uuid.UUID,
    url: Optional[str] = None,
    platform: Optional[str] = None,
    job: Optional[Job] = None,
) -> Optional[Dict[str, Any]]:
    """Synchronous wrapper for extract_and_review_job_with_ai."""
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    asyncio.run,
                    extract_and_review_job_with_ai(raw_text, db, user_id, url, platform, job),
                )
                return future.result()
        else:
            return asyncio.run(
                extract_and_review_job_with_ai(raw_text, db, user_id, url, platform, job)
            )
    except Exception as e:
        logger.warning("extract_and_review_job_sync failed: %s", e)
        if job:
            _apply_fallback_analysis(db, job)
        return None
