"""
Job analysis orchestration.
Builds the prompt context from job data and dispatches to the correct AI
provider (Gemini or OpenRouter). Falls back to keyword analysis on failure.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.job import Job, JobAnalysis
from app.services.ai import (
    analyze_job_with_fallback,
    keyword_fallback,
    CURRENT_PROMPT_VERSION,
    AnalysisOutput,
)
from app.services.ai_keys import build_candidates, get_user_fallback_order

logger = logging.getLogger(__name__)


def _build_context(job: Job) -> str:
    """Build the prompt context string from a Job ORM object."""
    parts = [
        f"Job Title: {job.title}",
        f"Company: {job.company}",
    ]
    if job.location:
        parts.append(f"Location: {job.location}")
    if job.salary_min or job.salary_max:
        salary = f"Salary: {job.currency or '$'}"
        if job.salary_min:
            salary += f"{job.salary_min:,}"
        if job.salary_min and job.salary_max:
            salary += f" – {job.currency or '$'}{job.salary_max:,}"
        elif job.salary_max:
            salary += f" up to {job.currency or '$'}{job.salary_max:,}"
        parts.append(salary)
    if job.tags:
        parts.append(f"Tags/Technologies: {', '.join(job.tags)}")
    if job.description:
        # Truncate very long descriptions to stay within token limits
        desc = job.description[:6000]
        parts.append(f"\nJob Description:\n{desc}")
    return "\n".join(parts)


async def run_job_analysis(
    job: Job,
    db: Session,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    user_id: Optional[str] = None,
) -> JobAnalysis:
    """
    Orchestrate AI analysis for a job.

    1. Finds or creates a JobAnalysis row (sets status=processing)
    2. Looks up user-stored encrypted API key (if user_id provided)
    3. Calls the correct AI provider
    4. Saves results (status=done) or marks failed
    5. Returns the updated JobAnalysis row

    Key resolution order (first match wins):
      1. api_key parameter (passed via header — client override)
      2. User-stored encrypted key (from UserPreference)
      3. Server environment variable (settings.GEMINI_API / OPENROUTER_API)
    """
    # Fetch or create the analysis record
    analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).first()
    if analysis is None:
        analysis = JobAnalysis(
            job_id=job.id,
            status="processing",
            score=0,
            summary="",
            pros=[],
            cons=[],
            skills_gap=[],
            key_requirements=[],
            analysis_version=CURRENT_PROMPT_VERSION,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
    else:
        analysis.status = "processing"
        analysis.analysis_version = CURRENT_PROMPT_VERSION
        db.commit()

    context = _build_context(job)
    result: AnalysisOutput

    try:
        actual_provider = (provider or "").lower() or None
        actual_model = model or None

        # Resolve the ordered candidate list (header -> user UI key -> env ->
        # fallback providers). See app.services.ai_keys for the full policy.
        fallback_order = get_user_fallback_order(db, user_id) if user_id else None
        candidates = build_candidates(
            db=db,
            user_id=user_id,
            provider=actual_provider,
            model=actual_model,
            request_api_key=api_key,
            fallback_order=fallback_order,
        )

        if candidates:
            logger.info(
                "Job %s analysis trying %d candidate(s): %s",
                job.id,
                len(candidates),
                ", ".join(f"{p}/{m}" for p, m, _ in candidates),
            )
            result = await analyze_job_with_fallback(context, candidates)
        else:
            logger.info(f"No AI key configured for job {job.id}, using fallback")
            result = keyword_fallback(job.title, job.description or "")

        # Persist results
        analysis.score = result.score
        analysis.summary = result.summary
        analysis.pros = result.pros
        analysis.cons = result.cons
        analysis.skills_gap = result.skills_gap
        analysis.key_requirements = result.key_requirements
        analysis.seniority = result.seniority
        analysis.status = "done"

    except Exception as e:
        logger.error(f"Job analysis failed for job {job.id}: {e}")
        analysis.status = "failed"
        analysis.summary = f"Analysis failed: {str(e)[:200]}"

    db.commit()
    db.refresh(analysis)
    return analysis
