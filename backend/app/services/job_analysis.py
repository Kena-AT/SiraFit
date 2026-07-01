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
    analyze_job_gemini,
    analyze_job_openrouter,
    keyword_fallback,
    CURRENT_PROMPT_VERSION,
    AnalysisOutput,
)

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
) -> JobAnalysis:
    """
    Orchestrate AI analysis for a job.

    1. Finds or creates a JobAnalysis row (sets status=processing)
    2. Calls the correct AI provider
    3. Saves results (status=done) or marks failed
    4. Returns the updated JobAnalysis row
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
        actual_provider = (provider or "").lower()
        actual_model = model or ""

        # Resolve API key from server env if not passed from client
        if not api_key:
            from app.core.config import settings
            if actual_provider == "openrouter":
                api_key = getattr(settings, "OPENROUTER_API_KEY", None)
            else:
                api_key = getattr(settings, "GEMINI_API_KEY", None)
                if not actual_provider:
                    actual_provider = "gemini"

        if api_key and actual_provider == "openrouter":
            result = await analyze_job_openrouter(
                context, api_key, model=actual_model or "openai/gpt-4o-mini"
            )
        elif api_key:
            result = await analyze_job_gemini(
                context, api_key, model=actual_model or "gemini-1.5-flash"
            )
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
