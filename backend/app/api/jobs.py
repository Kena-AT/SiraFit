from typing import List, Any, Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Header,
    Request,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, cast, String, func
import uuid
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.rate_limiting import check_rate_limit
from app.core.cache import (
    cache_get,
    cache_set,
    cache_get_or_compute,
    invalidate_job_related,
)
from app.api.users import get_current_user
from app.api.dependencies import get_user_profile
from app.models.user import User
from app.models.job import Job, JobApplication, JobImport, JobImportItem, JobAnalysis
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
    JobArchiveRequest,
    SessionImportIn,
    SessionValidationResponse,
    SupportedPlatformsResponse,
)
from app.services.job_import import process_import
from app.services.job_analysis import run_job_analysis
from app.services.matching_engine import calculate_match_score
from app.services.session_management import (
    store_user_session,
    delete_user_session,
    enqueue_session_import,
)
from app.services.scraping.session_importer import (
    SUPPORTED_PLATFORMS,
    SavedJobsImporter,
)
from app.core.config import settings
from app.core import metrics
from app.repositories.job_search import (
    keyword_search_jobs,
    semantic_search_jobs,
    hybrid_search_jobs,
    find_similar_jobs,
)
from app.services.embeddings import generate_query_embedding

router = APIRouter()


# ---------------------------------------------------------------------------
# Job listing
# ---------------------------------------------------------------------------


@router.get("/ranked", response_model=RankedJobListResponse)
def list_ranked_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> Any:
    """List all jobs with their match scores, ranked by score descending using a SQL join."""
    total = db.query(func.count(Job.id)).scalar() or 0
    query = (
        db.query(Job, JobMatchScore)
        .outerjoin(
            JobMatchScore,
            and_(
                JobMatchScore.job_id == Job.id, JobMatchScore.user_id == current_user.id
            ),
        )
        .order_by(JobMatchScore.score.desc().nullslast(), Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    results = query.all()

    items = [
        RankedJobResponse(
            job=JobResponse.model_validate(job),
            match_score=JobMatchScoreResponse.model_validate(score) if score else None,
        )
        for job, score in results
    ]
    return RankedJobListResponse(jobs=items, total=total)


@router.get("/search", response_model=JobListResponse)
def job_search(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    q: str = Query(..., min_length=1, description="Search query"),
    mode: str = Query(
        "keyword",
        regex="^(keyword|semantic|hybrid)$",
        description="Search mode: keyword, semantic, or hybrid",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> Any:
    """Search jobs using keyword, semantic (pgvector), or hybrid (RRF) retrieval."""
    import time

    start_time = time.perf_counter()

    # If semantic/hybrid requested but embeddings disabled, fall back to keyword
    effective_mode = mode
    if effective_mode in ("semantic", "hybrid") and not settings.ENABLE_SEMANTIC_SEARCH:
        effective_mode = "keyword"

    try:
        if effective_mode == "semantic":
            query_vector = generate_query_embedding(q)
            jobs, total = semantic_search_jobs(
                db, query_vector=query_vector, skip=skip, limit=limit
            )
        elif effective_mode == "hybrid":
            query_vector = generate_query_embedding(q)
            jobs, total = hybrid_search_jobs(
                db, query_text=q, query_vector=query_vector, skip=skip, limit=limit
            )
        else:
            jobs, total = keyword_search_jobs(db, query_text=q, skip=skip, limit=limit)

        duration = time.perf_counter() - start_time
        metrics.SEMANTIC_SEARCH_TOTAL.labels(
            mode=effective_mode, status="success"
        ).inc()
        metrics.SEMANTIC_SEARCH_DURATION_SECONDS.labels(mode=effective_mode).observe(
            duration
        )
        return JobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)

    except Exception as exc:
        metrics.SEMANTIC_SEARCH_TOTAL.labels(
            mode=effective_mode, status="failure"
        ).inc()
        logger.exception("Search failure in mode %s: %s", effective_mode, exc)
        # Graceful fallback to keyword search if semantic model fails
        jobs, total = keyword_search_jobs(db, query_text=q, skip=skip, limit=limit)
        return JobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)


@router.get("/with-scores", response_model=RankedJobListResponse)
def list_jobs_with_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    """List jobs with their match scores in a single batched call.

    Returns each job pre-joined with its stored match score (or null) so the
    Match page can render without firing a per-job score request (the previous
    N+1 pattern). Scores are fetched in one IN()-query rather than one per job.
    """
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    job_ids = [j.id for j in jobs]
    scores = (
        db.query(JobMatchScore)
        .filter(
            JobMatchScore.user_id == current_user.id,
            JobMatchScore.job_id.in_(job_ids),
        )
        .all()
    )
    score_map = {s.job_id: s for s in scores}

    items = [
        RankedJobResponse(
            job=JobResponse.model_validate(job),
            match_score=JobMatchScoreResponse.model_validate(score_map[job.id])
            if job.id in score_map
            else None,
        )
        for job in jobs
    ]
    items.sort(key=lambda r: r.match_score.score if r.match_score else 0, reverse=True)
    return RankedJobListResponse(jobs=items, total=len(items))


# ---------------------------------------------------------------------------
# Job listing
# ---------------------------------------------------------------------------


def _build_cache_key(user_id: str, **params) -> str:
    """Build a deterministic cache key from filter parameters."""
    # Sort params for determinism, exclude skip/limit (they don't affect total)
    cache_params = {
        k: v for k, v in params.items() if k not in ("skip", "limit") and v is not None
    }
    param_str = json.dumps(cache_params, sort_keys=True)
    return f"jobs:list:{user_id}:{hashlib.md5(param_str.encode()).hexdigest()}"


def _list_jobs_query(
    db: Session,
    current_user: User,
    skip: int,
    limit: int,
    search: Optional[str],
    company: Optional[str],
    location: Optional[str],
    source: Optional[str],
    tags: Optional[str],
    min_salary: Optional[int],
    max_salary: Optional[int],
    sort_by: Optional[str],
    sort_order: Optional[str],
    include_archived: bool,
    skill_keywords: list[str] | None = None,
    mode: str = "keyword",
) -> JobListResponse:
    """Core job-listing query logic with support for keyword, semantic, and hybrid retrieval."""
    effective_mode = mode
    if effective_mode in ("semantic", "hybrid") and not settings.ENABLE_SEMANTIC_SEARCH:
        effective_mode = "keyword"

    if search and search.strip() and effective_mode in ("semantic", "hybrid"):
        try:
            query_vector = generate_query_embedding(search.strip())
            if effective_mode == "semantic":
                jobs, total = semantic_search_jobs(
                    db,
                    query_vector=query_vector,
                    skip=skip,
                    limit=limit,
                    company=company,
                    location=location,
                    source=source,
                    tags=tags,
                    min_salary=min_salary,
                    max_salary=max_salary,
                    include_archived=include_archived,
                )
            else:
                jobs, total = hybrid_search_jobs(
                    db,
                    query_text=search.strip(),
                    query_vector=query_vector,
                    skip=skip,
                    limit=limit,
                    company=company,
                    location=location,
                    source=source,
                    tags=tags,
                    min_salary=min_salary,
                    max_salary=max_salary,
                    include_archived=include_archived,
                )
            return JobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)
        except Exception as exc:
            logger.warning(
                "Semantic/hybrid retrieval failed in list_jobs, falling back to keyword: %s",
                exc,
            )

    query = db.query(Job)

    if not include_archived:
        query = query.filter(Job.is_archived == False)  # noqa: E712

    relevance_col = None
    if search:
        term_clean = search.strip()
        from app.repositories.job_search import is_postgres

        if is_postgres(db):
            from sqlalchemy import text

            fts_cond = text("search_vector @@ websearch_to_tsquery('english', :query)")
            trgm_cond = or_(
                Job.title.op("%")(term_clean), Job.company.op("%")(term_clean)
            )
            query = query.filter(or_(fts_cond, trgm_cond)).params(query=term_clean)

            fts_rank = text(
                "ts_rank_cd(search_vector, websearch_to_tsquery('english', :query))"
            )
            trgm_rank = text(
                "GREATEST(word_similarity(:query, title), word_similarity(:query, company))"
            )
            relevance_col = (fts_rank + trgm_rank).desc()
        else:
            term = f"%{term_clean}%"
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

    # Optional best-effort skill-keyword filter on the job.tags JSON field.
    if skill_keywords:
        # Build an OR clause: tags LIKE '%keyword1%' OR tags LIKE '%keyword2%' ...
        # We wrap each in cast(...) so it works on both SQLite and PostgreSQL.
        keyword_conditions = []
        for kw in skill_keywords:
            keyword_conditions.append(cast(Job.tags, String).ilike(f'%"{kw}"%'))
        # Combine with OR — if multiple keywords, match any one of them.
        from sqlalchemy import or_ as _or

        query = query.filter(_or(*keyword_conditions))

    total = query.with_entities(func.count(Job.id)).order_by(None).scalar() or 0

    sort_col = getattr(Job, sort_by, Job.created_at)
    primary_sort = sort_col.asc() if sort_order == "asc" else sort_col.desc()
    if relevance_col is not None:
        query = query.order_by(relevance_col, primary_sort)
    else:
        query = query.order_by(primary_sort)
    jobs = query.offset(skip).limit(limit).all()

    return JobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
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
    mode: str = Query(
        "keyword", regex="^(keyword|semantic|hybrid)$", description="Search mode"
    ),
    # Profiling: if a user profile exists, we pre-filter jobs by skill overlap
    # so the returned list is immediately relevant. This is a best-effort filter —
    # if no profile is found we fall back to the full list unchanged.
    profile_id: Optional[uuid.UUID] = Query(
        None, description="Filter by user profile ID"
    ),
) -> Any:
    """List jobs with search, filtering, sorting, and pagination.

    Ponytail: 30s Redis cache behind singleflight dedup. Concurrent
    identical requests coalesce to a single DB round-trip on cache miss,
    preventing thundering-herd load.
    """
    # Resolve profile once and build a skill-filter if a profile_id was given.
    skill_keywords: list[str] = []
    if profile_id is not None:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if profile and profile.skills:
            # Use the first 3 skill keywords as a lightweight relevance filter.
            # Each Skill.name is a free-text tag; we'll ILIKE-search against job.tags.
            skill_keywords = [s.name for s in profile.skills[:3]]

    cache_key = _build_cache_key(
        str(current_user.id),
        search=search,
        mode=mode,
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

    async def fetch() -> JobListResponse:
        result = await run_in_threadpool(
            _list_jobs_query,
            db,
            current_user,
            skip,
            limit,
            search,
            company,
            location,
            source,
            tags,
            min_salary,
            max_salary,
            sort_by,
            sort_order,
            include_archived,
            skill_keywords,
            mode,
        )
        return result

    # Singleflight: dedupe concurrent fetches for the same cache key.
    # On cache hit, the cached dict is re-hydrated into a JobListResponse.
    cached = cache_get(cache_key)
    if cached:
        return JobListResponse(
            jobs=[JobResponse(**j) for j in cached["jobs"]],
            total=cached["total"],
            skip=cached["skip"],
            limit=cached["limit"],
        )

    result = await cache_get_or_compute(cache_key, 30, fetch)
    return result


# ---------------------------------------------------------------------------
# Top Matches (personalized match queue)
# ---------------------------------------------------------------------------


@router.get("/top-matches", response_model=TopMatchListResponse)
def get_top_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: Profile = Depends(get_user_profile),
    limit: int = Query(4, ge=1, le=10),
) -> Any:
    """Get the user's top job matches based on profile scoring."""

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


@router.delete("/{job_id}", status_code=204)
def delete_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.import_id:
        import_record = (
            db.query(JobImport).filter(JobImport.id == job.import_id).first()
        )
        if import_record and import_record.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    # Clean up related records explicitly to prevent FK constraint errors
    db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).delete()
    db.query(JobMatchScore).filter(JobMatchScore.job_id == job_id).delete()
    db.query(JobImportItem).filter(JobImportItem.job_id == job_id).update(
        {JobImportItem.job_id: None}
    )

    db.delete(job)
    db.commit()
    return None


@router.post("/{job_id}/archive")
def archive_job(
    job_id: uuid.UUID,
    body: JobArchiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Archive or unarchive a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.import_id:
        import_record = (
            db.query(JobImport).filter(JobImport.id == job.import_id).first()
        )
        if import_record and import_record.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    job.is_archived = body.archived
    db.commit()
    db.refresh(job)
    return {"message": "Job archived" if body.archived else "Job unarchived"}


def _match_score_cache_key(user_id: str, job_id: str) -> str:
    return f"match_score:{user_id}:{job_id}"


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

    # Ponytail: 5min cache for match scores.
    cache_key = _match_score_cache_key(str(current_user.id), str(job_id))
    cached = cache_get(cache_key)
    if cached:
        if "status" not in cached:
            cached["status"] = "done"
        return JobMatchScoreResponse.model_validate(cached)

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        return {
            "job_id": job_id,
            "user_id": current_user.id,
            "score": 0,
            "breakdown": {},
            "explanation": "Profile not created yet.",
            "status": "not_started",
        }

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
        resp_data = JobMatchScoreResponse.model_validate(existing_score).model_dump(
            mode="json"
        )
        resp_data["status"] = "done"
        cache_set(cache_key, resp_data, ttl=300)
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
        resp_data = JobMatchScoreResponse.model_validate(new_score).model_dump(
            mode="json"
        )
        resp_data["status"] = "done"
        cache_set(cache_key, resp_data, ttl=300)
        return new_score


@router.get("/{job_id}/match-score/cached", response_model=JobMatchScoreResponse)
def get_cached_match_score(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the stored match score for a job without recalculating.

    Returns status="not_started" if no score has been calculated yet. Use GET /{job_id}/match-score
    to calculate and store a score on demand.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check cache first
    cache_key = _match_score_cache_key(str(current_user.id), str(job_id))
    cached = cache_get(cache_key)
    if cached:
        if "status" not in cached:
            cached["status"] = "done"
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
        return {
            "job_id": job_id,
            "user_id": current_user.id,
            "score": 0,
            "breakdown": {},
            "explanation": "No match score found for this job. Trigger one via GET /{job_id}/match-score.",
            "status": "not_started",
        }
    # Populate cache for next time
    resp_data = JobMatchScoreResponse.model_validate(score).model_dump(mode="json")
    resp_data["status"] = "done"
    cache_set(cache_key, resp_data, ttl=300)
    return score


@router.get("/{job_id}/similar", response_model=JobListResponse)
def get_similar_jobs(
    job_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50, description="Max similar jobs to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve semantically similar jobs using pgvector cosine distance.

    Excludes the source job, jobs without ready embeddings, and archived jobs.
    """
    source_job = (
        db.query(Job).filter(Job.id == job_id, Job.is_archived == False).first()
    )  # noqa: E712
    if not source_job:
        raise HTTPException(status_code=404, detail="Job not found")

    similar = find_similar_jobs(db, source_job_id=job_id, limit=limit)
    return JobListResponse(jobs=similar, total=len(similar), skip=0, limit=limit)


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
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
    if not analysis:
        return {
            "job_id": job_id,
            "score": 0,
            "summary": "No analysis found for this job. Trigger one first.",
            "pros": [],
            "cons": [],
            "skills_gap": [],
            "status": "not_started",
        }
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
    """Import jobs from a URL (async via Celery) or pasted description/CSV (sync)."""
    # Description / CSV imports are fast and stay synchronous on the request path.
    if import_in.source_type != "url":
        import_record, jobs_data, errors, scrape_meta = process_import(
            db,
            current_user.id,
            import_in.source_type,
            import_in.data,
        )
        invalidate_job_related(str(current_user.id))
        return ImportResultResponse(
            import_record=JobImportResponse.model_validate(import_record),
            jobs=[JobData(**job, is_duplicate=False) for job in jobs_data],
            errors=errors,
            scrape_method=scrape_meta.get("method_used"),
            scrape_duration_ms=scrape_meta.get("duration_ms"),
            fields_extracted=scrape_meta.get("fields_extracted"),
            source_platform=scrape_meta.get("source_platform"),
        )

    # URL import: create a tracking record, then offload to the scraping queue.
    from app.services.job_import import enqueue_job_import

    job_import = JobImport(
        user_id=current_user.id,
        source="url",
        status="processing",
        source_data=import_in.data[:2000],
    )
    db.add(job_import)
    db.commit()
    db.refresh(job_import)

    outcome = enqueue_job_import(
        str(job_import.id), import_in.data, "url", str(current_user.id)
    )

    if outcome.get("queued"):
        # Accepted for async processing; the worker will update status.
        return JSONResponse(
            status_code=202,
            content=ImportResultResponse(
                import_record=JobImportResponse.model_validate(job_import),
                jobs=[],
                errors=[],
                scrape_method="async",
            ).model_dump(mode="json"),
        )

    # Broker unavailable -> sync fallback in background task to avoid holding HTTP DB session!
    from app.services.job_import import _scrape_and_import_job_sync
    background_tasks.add_task(
        _scrape_and_import_job_sync,
        str(job_import.id),
        import_in.data,
        "url",
        str(current_user.id)
    )

    return JSONResponse(
        status_code=202,
        content=ImportResultResponse(
            import_record=JobImportResponse.model_validate(job_import),
            jobs=[],
            errors=[],
            scrape_method="async_fallback",
        ).model_dump(mode="json"),
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


@router.delete("/import/{import_id}", status_code=204)
def delete_import(
    import_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an import record."""
    import_record = db.query(JobImport).filter(JobImport.id == import_id).first()
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    if import_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(import_record)
    db.commit()


# ---------------------------------------------------------------------------
# Authenticated Session Import (Sprint 5)
# ---------------------------------------------------------------------------


@router.get("/import/session/platforms", response_model=SupportedPlatformsResponse)
def get_supported_session_platforms() -> Any:
    """List platforms approved and supported for authenticated session import."""
    return SupportedPlatformsResponse(platforms=sorted(list(SUPPORTED_PLATFORMS)))


@router.post(
    "/import/session/{platform}/validate", response_model=SessionValidationResponse
)
def validate_platform_session(
    platform: str,
    body: SessionImportIn,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Validate user-supplied session credentials against the platform.

    Does NOT persist credentials or import jobs.
    """
    check_rate_limit(request, "session_validate", str(current_user.id))

    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=400, detail=f"Platform '{platform}' is not supported"
        )

    importer = SavedJobsImporter()
    valid, message = importer.validate_session(platform, body.model_dump())
    return SessionValidationResponse(valid=valid, platform=platform, message=message)


@router.post("/import/session/{platform}", response_model=ImportResultResponse)
def import_saved_jobs_from_session(
    platform: str,
    body: SessionImportIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Store encrypted session credentials and initiate async saved-job import.

    Returns HTTP 202 immediately; discovery runs in the Celery worker.
    """
    check_rate_limit(request, "session_import", str(current_user.id))

    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=400, detail=f"Platform '{platform}' is not supported"
        )

    if not body.consent_confirmed:
        raise HTTPException(
            status_code=422, detail="Consent must be confirmed to import saved jobs"
        )

    # 1. Validate & store encrypted session
    try:
        store_user_session(
            db=db,
            user_id=current_user.id,
            platform=platform,
            session_data=body.model_dump(),
            expires_at=body.expires_at,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to securely store session credentials"
        )

    # 2. Create JobImport tracking record
    job_import = JobImport(
        user_id=current_user.id,
        source=f"session_{platform}",
        status="processing",
        source_data=f"Authenticated saved jobs import ({platform})",
    )
    db.add(job_import)
    db.commit()
    db.refresh(job_import)

    # 3. Offload discovery to Celery queue
    enqueue_session_import(
        import_id=str(job_import.id),
        platform=platform,
        user_id=str(current_user.id),
    )

    invalidate_job_related(str(current_user.id))

    return JSONResponse(
        status_code=202,
        content=ImportResultResponse(
            import_record=JobImportResponse.model_validate(job_import),
            jobs=[],
            errors=[],
            scrape_method="session_async",
            source_platform=platform,
        ).model_dump(mode="json"),
    )


@router.delete("/import/session/{platform}", status_code=204)
def delete_stored_platform_session(
    platform: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a stored platform session."""
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=400, detail=f"Platform '{platform}' is not supported"
        )

    deleted = delete_user_session(db, current_user.id, platform)
    if not deleted:
        raise HTTPException(status_code=404, detail="Stored session not found")


def _import_detail_response(
    db: Session, import_record: JobImport
) -> ImportResultResponse:
    """Build an ``ImportResultResponse`` from a ``JobImport`` (items joined with jobs).

    Queries ``JobImportItem LEFT JOIN Job`` as the authoritative source of truth.
    Falls back to ``Job.import_id`` / 5-minute time window only for legacy imports
    that have zero ``JobImportItem`` records.
    """
    import_id = import_record.id

    # Primary path: query JobImportItem joined with Job
    items_with_jobs = (
        db.query(JobImportItem, Job)
        .outerjoin(Job, JobImportItem.job_id == Job.id)
        .filter(JobImportItem.import_id == import_id)
        .order_by(JobImportItem.created_at)
        .all()
    )

    jobs_data = []

    if items_with_jobs:
        for item, job in items_with_jobs:
            if job:
                jobs_data.append(
                    {
                        "id": str(job.id),
                        "external_id": job.external_id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "salary_min": job.salary_min,
                        "salary_max": job.salary_max,
                        "currency": job.currency,
                        "tags": job.tags or [],
                        "url": job.url,
                        "source": job.source,
                        "is_duplicate": item.status == "duplicate",
                        "import_status": item.status,
                    }
                )
            else:
                jobs_data.append(
                    {
                        "id": None,
                        "external_id": item.title_guess or "unknown",
                        "title": item.title_guess or "Unknown",
                        "company": "Unknown",
                        "location": None,
                        "salary_min": None,
                        "salary_max": None,
                        "currency": None,
                        "tags": [],
                        "url": None,
                        "source": import_record.source,
                        "is_duplicate": item.status == "duplicate",
                        "import_status": item.status,
                    }
                )
    else:
        # Legacy fallback for historical imports created before JobImportItem existed
        jobs = (
            db.query(Job)
            .filter(Job.import_id == import_id)
            .order_by(Job.created_at)
            .all()
        )
        if not jobs:
            from datetime import timedelta

            window_start = import_record.created_at - timedelta(minutes=5)
            window_end = import_record.created_at + timedelta(minutes=5)
            jobs = (
                db.query(Job)
                .filter(
                    Job.created_at >= window_start,
                    Job.created_at <= window_end,
                )
                .order_by(Job.created_at)
                .all()
            )

        jobs_data = [
            {
                "id": str(job.id),
                "external_id": job.external_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "currency": job.currency,
                "tags": job.tags or [],
                "url": job.url,
                "source": job.source,
                "is_duplicate": False,
                "import_status": "imported",
            }
            for job in jobs
        ]

    errors = import_record.errors or []

    return ImportResultResponse(
        import_record=JobImportResponse.model_validate(import_record),
        jobs=[JobData(**job) for job in jobs_data],
        errors=errors,
        scrape_method=None,
        scrape_duration_ms=None,
        fields_extracted=None,
        source_platform=None,
    )


@router.get("/import/{import_id}", response_model=ImportResultResponse)
def get_import_detail(
    import_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get details of a specific import (used for polling the async import status)."""
    import_record = db.query(JobImport).filter(JobImport.id == import_id).first()
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    if import_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return _import_detail_response(db, import_record)
