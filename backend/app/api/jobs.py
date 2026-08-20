from typing import List, Any, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, func
import uuid
import json
import hashlib

from app.core.database import get_db
from app.core.cache import cache_get, cache_set
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Job, JobApplication, JobImport, JobAnalysis
from app.models.score import JobMatchScore
from app.models.profile import Profile
from app.schemas.job import (
    JobResponse,
    JobImportCreate,
    JobListResponse,
    JobImportResponse,
    ImportResultResponse,
    JobData,
    JobAnalysisResponse,
    AnalysisRequest,
    JobMatchScoreResponse,
    RankedJobResponse,
    RankedJobListResponse,
    TopMatchItem,
    TopMatchListResponse,
)
from app.services.job_import import process_import
from app.services.job_analysis import run_job_analysis
from app.services.matching_engine import calculate_match_score

router = APIRouter()


# ---------------------------------------------------------------------------
# Job listing
# ---------------------------------------------------------------------------


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
        score_record = (
            db.query(JobMatchScore)
            .filter(
                JobMatchScore.user_id == current_user.id, JobMatchScore.job_id == job.id
            )
            .first()
        )
        items.append(
            RankedJobResponse(
                job=JobResponse.model_validate(job),
                match_score=JobMatchScoreResponse.model_validate(score_record)
                if score_record
                else None,
            )
        )
    items.sort(key=lambda r: r.match_score.score if r.match_score else 0, reverse=True)
    return RankedJobListResponse(jobs=items, total=len(items))


# ---------------------------------------------------------------------------
# Job listing
# ---------------------------------------------------------------------------


def _build_cache_key(user_id: str, **params) -> str:
    """Build a deterministic cache key from filter parameters."""
    # Sort params for determinism, exclude skip/limit (they don't affect total)
    cache_params = {k: v for k, v in params.items() if k not in ("skip", "limit") and v is not None}
    param_str = json.dumps(cache_params, sort_keys=True)
    return f"jobs:list:{user_id}:{hashlib.md5(param_str.encode()).hexdigest()}"


def _invalidate_job_cache(user_id: str) -> None:
    """Invalidate all job list caches for a user."""
    cache_delete_prefix(f"jobs:list:{user_id}:")


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
    include_archived: bool = Query(False, description="Include archived jobs"),
) -> Any:
    """List jobs with search, filtering, sorting, and pagination."""
    # Ponytail: 30s Redis cache for job listings. Invalidate on import/analysis.
    # Caches the total + jobs for a given filter set. skip/limit intentionally
    # excluded from key so we can serve any page from the same cached response.
    cache_key = _build_cache_key(
        str(current_user.id),
        search=search,
        company=company,
        location=location,
        source=source,
        tags=tags,
        min_salary=min_salary,
        max_salary=max_salary,
        sort_by=sort_by,
        sort_order=sort_order,
        include_archived=include_archived,
    )

    cached = cache_get(cache_key)
    if cached:
        total = cached["total"]
        # Slice the cached jobs for the requested page
        cached_jobs = cached["jobs"]
        page_jobs = cached_jobs[skip : skip + limit]
        return JobListResponse(
            jobs=[JobResponse.model_validate(j) for j in page_jobs],
            total=total,
            skip=skip,
            limit=limit,
        )

    query = db.query(Job)

    if not include_archived:
        query = query.filter(Job.is_archived == False)  # noqa: E712

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
            # Cast to text so the match works on both SQLite (JSON-as-text)
            # and PostgreSQL (JSONB); `"tag"` matches the JSON-encoded element.
            query = query.filter(cast(Job.tags, String).like(f'%"{tag}"%'))
    if min_salary is not None:
        query = query.filter(
            or_(Job.salary_min >= min_salary, Job.salary_max >= min_salary)
        )
    if max_salary is not None:
        query = query.filter(
            or_(Job.salary_max <= max_salary, Job.salary_min <= max_salary)
        )

    total = query.with_entities(func.count(Job.id)).order_by(None).scalar() or 0

    sort_col = getattr(Job, sort_by, Job.created_at)
    query = query.order_by(sort_col.asc() if sort_order == "asc" else sort_col.desc())
    jobs = query.offset(skip).limit(limit).all()

    # Store full result set in cache (not just the paged subset)
    # Re-use the same query with all filters — only remove skip/limit
    full_query = db.query(Job)
    if not include_archived:
        full_query = full_query.filter(Job.is_archived == False)
    if search:
        term = f"%{search}%"
        full_query = full_query.filter(
            or_(
                Job.title.ilike(term),
                Job.company.ilike(term),
                Job.description.ilike(term),
                Job.location.ilike(term),
            )
        )
    if company:
        full_query = full_query.filter(Job.company.ilike(f"%{company}%"))
    if location:
        full_query = full_query.filter(Job.location.ilike(f"%{location}%"))
    if source:
        full_query = full_query.filter(Job.source == source)
    if tags:
        for tag in [t.strip() for t in tags.split(",")]:
            full_query = full_query.filter(cast(Job.tags, String).like(f'%"{tag}"%'))
    if min_salary is not None:
        full_query = full_query.filter(
            or_(Job.salary_min >= min_salary, Job.salary_max >= min_salary)
        )
    if max_salary is not None:
        full_query = full_query.filter(
            or_(Job.salary_max <= max_salary, Job.salary_min <= max_salary)
        )

    all_jobs = full_query.order_by(sort_col.asc() if sort_order == "asc" else sort_col.desc()).all()

    cache_data = {
        "total": total,
        "jobs": [JobResponse.model_validate(j).model_dump(mode="json") for j in all_jobs],
    }
    cache_set(cache_key, cache_data, ttl=30)

    return JobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)


# ---------------------------------------------------------------------------
# Top Matches (personalized match queue)
# ---------------------------------------------------------------------------


@router.get("/top-matches", response_model=TopMatchListResponse)
def get_top_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(4, ge=1, le=10),
) -> Any:
    """Get the user's top job matches based on profile scoring."""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=404, detail="Profile not found. Create a profile first."
        )

    # Get job IDs the user has already applied to or saved
    applied_job_ids = (
        db.query(JobApplication.job_id)
        .filter(JobApplication.user_id == current_user.id)
        .subquery()
    )

    # Get candidate jobs not yet applied to
    candidate_jobs = (
        db.query(Job)
        .filter(Job.id.notin_(applied_job_ids))
        .order_by(Job.created_at.desc())
        .limit(50)
        .all()
    )

    # Score each job and filter by threshold
    scored_matches = []
    for job in candidate_jobs:
        score_data = calculate_match_score(profile, job)
        if score_data["score"] >= 30:  # minimum threshold
            scored_matches.append(
                TopMatchItem(
                    job_id=job.id,
                    company=job.company,
                    role=job.title,
                    match_score=score_data["score"],
                    status="new",
                )
            )

    # Sort by score descending and limit
    scored_matches.sort(key=lambda x: x.match_score, reverse=True)
    top_matches = scored_matches[:limit]

    return TopMatchListResponse(matches=top_matches, total=len(top_matches))


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


def _match_score_cache_key(user_id: str, job_id: str) -> str:
    return f"match_score:{user_id}:{job_id}"


@router.get("/{job_id}/match-score", response_model=JobMatchScoreResponse)
def get_match_score(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Calculate and get match score for a job."""
    # Ponytail: 5min cache for match scores.
    cache_key = _match_score_cache_key(str(current_user.id), str(job_id))
    cached = cache_get(cache_key)
    if cached:
        return JobMatchScoreResponse.model_validate(cached)

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=404, detail="Profile not found. Create a profile first."
        )

    # Calculate score
    score_data = calculate_match_score(profile, job)

    # Save/Update score
    existing_score = (
        db.query(JobMatchScore)
        .filter(
            JobMatchScore.user_id == current_user.id, JobMatchScore.job_id == job_id
        )
        .first()
    )

    if existing_score:
        existing_score.score = score_data["score"]
        existing_score.breakdown = score_data["breakdown"]
        existing_score.explanation = score_data["explanation"]
        db.commit()
        db.refresh(existing_score)
        cache_set(cache_key, JobMatchScoreResponse.model_validate(existing_score).model_dump(mode="json"), ttl=300)
        return existing_score
    else:
        new_score = JobMatchScore(
            user_id=current_user.id,
            job_id=job_id,
            score=score_data["score"],
            breakdown=score_data["breakdown"],
            explanation=score_data["explanation"],
        )
        db.add(new_score)
        db.commit()
        db.refresh(new_score)
        cache_set(cache_key, JobMatchScoreResponse.model_validate(new_score).model_dump(mode="json"), ttl=300)
        return new_score


@router.get("/{job_id}/match-score/cached", response_model=JobMatchScoreResponse)
def get_cached_match_score(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the stored match score for a job without recalculating.

    Returns 404 if no score has been calculated yet. Use GET /{job_id}/match-score
    to calculate and store a score on demand.
    """
    # Check cache first
    cache_key = _match_score_cache_key(str(current_user.id), str(job_id))
    cached = cache_get(cache_key)
    if cached:
        return JobMatchScoreResponse.model_validate(cached)

    score = (
        db.query(JobMatchScore)
        .filter(
            JobMatchScore.user_id == current_user.id,
            JobMatchScore.job_id == job_id,
        )
        .first()
    )
    if not score:
        raise HTTPException(
            status_code=404,
            detail="No match score found for this job. Trigger one via GET /{job_id}/match-score.",
        )
    # Populate cache for next time
    cache_set(cache_key, JobMatchScoreResponse.model_validate(score).model_dump(mode="json"), ttl=300)
    return score


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


@router.get("/{job_id}/analysis", response_model=JobAnalysisResponse)
def get_job_analysis(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the stored AI analysis for a job (poll this after triggering)."""
    analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
    if not analysis:
        raise HTTPException(
            status_code=404, detail="No analysis found for this job. Trigger one first."
        )
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
        db,
        current_user.id,
        import_in.source_type,
        import_in.data,
    )
    # Invalidate job cache since new jobs were added
    _invalidate_job_cache(str(current_user.id))
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

    # Query jobs associated with this import batch
    from app.models.job import JobApplication
    applied_jobs = (
        db.query(JobApplication)
        .filter(
            JobApplication.user_id == current_user.id,
            JobApplication.created_at >= import_record.created_at,
        )
        .join(Job)
        .all()
    )

    jobs_data = []
    for app in applied_jobs:
        job = app.job
        if job:
            jobs_data.append({
                "id": str(job.id),
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "currency": job.currency,
                "tags": job.tags,
                "url": job.url,
                "source": job.source,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "is_duplicate": False,
            })

    return ImportResultResponse(
        import_record=JobImportResponse.model_validate(import_record),
        jobs=[JobData(**job) for job in jobs_data],
        errors=[],
    )
