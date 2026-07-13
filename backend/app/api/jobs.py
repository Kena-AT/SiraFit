from typing import List, Any, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Job, JobImport, JobAnalysis
from app.models.score import JobMatchScore
from app.models.profile import Profile
from app.schemas.job import (
    JobResponse, JobImportCreate, JobListResponse,
    JobImportResponse, ImportResultResponse, JobData,
    JobAnalysisResponse, AnalysisRequest, JobMatchScoreResponse,
    RankedJobResponse, RankedJobListResponse,
)
from app.services.job_import import process_import
from app.services.job_analysis import run_job_analysis
from app.services.matching_engine import calculate_match_score

router = APIRouter()


# ---------------------------------------------------------------------------
# Job listing
# ---------------------------------------------------------------------------

@router.get("/", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    min_salary: Optional[int] = Query(None, ge=0),
    max_salary: Optional[int] = Query(None, ge=0),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
) -> Any:
    """List jobs with search, filtering, sorting, and pagination."""
    query = db.query(Job)

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Job.title.ilike(term),
                Job.company.ilike(term),
                Job.description.ilike(term),
                Job.location.ilike(term),
            )
        )

    if company:
        query = query.filter(Job.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if source:
        query = query.filter(Job.source == source)
    if tags:
        for tag in [t.strip() for t in tags.split(",")]:
            query = query.filter(Job.tags.contains(tag))
    if min_salary is not None:
        query = query.filter(or_(Job.salary_min >= min_salary, Job.salary_max >= min_salary))
    if max_salary is not None:
        query = query.filter(or_(Job.salary_max <= max_salary, Job.salary_min <= max_salary))

    total = query.count()

    sort_col = getattr(Job, sort_by, Job.created_at)
    query = query.order_by(sort_col.asc() if sort_order == "asc" else sort_col.desc())
    jobs = query.offset(skip).limit(limit).all()

    return JobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)


# ---------------------------------------------------------------------------
# Single job
# ---------------------------------------------------------------------------

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/match-score", response_model=JobMatchScoreResponse)
def get_match_score(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Calculate and get match score for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create a profile first.")

    # Calculate score
    score_data = calculate_match_score(profile, job)
    
    # Save/Update score
    existing_score = db.query(JobMatchScore).filter(
        JobMatchScore.user_id == current_user.id,
        JobMatchScore.job_id == job_id
    ).first()
    
    if existing_score:
        existing_score.score = score_data["score"]
        existing_score.breakdown = score_data["breakdown"]
        existing_score.explanation = score_data["explanation"]
        db.commit()
        db.refresh(existing_score)
        return existing_score
    else:
        new_score = JobMatchScore(
            user_id=current_user.id,
            job_id=job_id,
            score=score_data["score"],
            breakdown=score_data["breakdown"],
            explanation=score_data["explanation"]
        )
        db.add(new_score)
        db.commit()
        db.refresh(new_score)
        return new_score


# ---------------------------------------------------------------------------
# AI Analysis
# ---------------------------------------------------------------------------

@router.post("/{job_id}/analyze", response_model=JobAnalysisResponse)
async def trigger_analysis(
    job_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    body: AnalysisRequest = AnalysisRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key"),
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
) -> Any:
    """
    Trigger AI analysis for a job.

    Returns immediately with status=processing (or existing analysis).
    Analysis runs as a background task; poll GET /{job_id}/analysis for results.
    Pass force_refresh=true in the body to re-run even if an analysis exists.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Return existing completed analysis unless force_refresh
    existing = db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
    if existing and existing.status == "done" and not body.force_refresh:
        return existing

    # Create or reset a stub record immediately so the frontend can start polling
    if existing is None:
        stub = JobAnalysis(
            job_id=job_id,
            status="processing",
            score=0,
            summary="",
            pros=[],
            cons=[],
            skills_gap=[],
            key_requirements=[],
        )
        db.add(stub)
        db.commit()
        db.refresh(stub)
    else:
        existing.status = "processing"
        db.commit()
        db.refresh(existing)
        stub = existing

    # Schedule actual analysis in background
    background_tasks.add_task(
        run_job_analysis,
        job=job,
        db=db,
        api_key=x_ai_api_key,
        provider=x_ai_provider,
        model=x_ai_model,
        user_id=str(current_user.id),
    )

    return stub


@router.get("/ranked", response_model=RankedJobListResponse)
def list_ranked_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    """List all jobs with their match scores, ranked by score descending."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    items = []
    for job in jobs:
        score_record = db.query(JobMatchScore).filter(
            JobMatchScore.user_id == current_user.id,
            JobMatchScore.job_id == job.id
        ).first()
        items.append(RankedJobResponse(
            job=JobResponse.model_validate(job),
            match_score=JobMatchScoreResponse.model_validate(score_record) if score_record else None,
        ))
    items.sort(key=lambda r: (r.match_score.score if r.match_score else 0), reverse=True)
    return RankedJobListResponse(jobs=items, total=len(items))


@router.get("/{job_id}/analysis", response_model=JobAnalysisResponse)
def get_job_analysis(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the stored AI analysis for a job (poll this after triggering)."""
    analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this job. Trigger one first.")
    return analysis


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

@router.post("/import", response_model=ImportResultResponse)
def import_jobs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    import_in: JobImportCreate,
) -> Any:
    """Import jobs from a URL or pasted description."""
    import_record, jobs_data, errors = process_import(
        db, current_user.id, import_in.source_type, import_in.data,
    )
    return ImportResultResponse(
        import_record=JobImportResponse.model_validate(import_record),
        jobs=[JobData(**job, is_duplicate=False) for job in jobs_data],
        errors=errors,
    )


@router.get("/import/history", response_model=List[JobImportResponse])
def get_import_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    """Get import history for the current user."""
    return (
        db.query(JobImport)
        .filter(JobImport.user_id == current_user.id)
        .order_by(JobImport.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/import/{import_id}", response_model=ImportResultResponse)
def get_import_detail(
    import_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get details of a specific import."""
    import_record = db.query(JobImport).filter(JobImport.id == import_id).first()
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    if import_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return ImportResultResponse(
        import_record=JobImportResponse.model_validate(import_record),
        jobs=[],
        errors=[],
    )
