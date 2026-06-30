from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
import uuid

from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Job, JobImport
from app.schemas.job import (
    JobResponse, JobImportCreate, JobListResponse,
    JobImportResponse, ImportResultResponse, JobData,
)
from app.services.job_import import process_import

router = APIRouter()


@router.get("/", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in title, company, description"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    source: Optional[str] = Query(None, description="Filter by source (linkedin, indeed, etc)"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter"),
    min_salary: Optional[int] = Query(None, ge=0, description="Minimum salary"),
    max_salary: Optional[int] = Query(None, ge=0, description="Maximum salary"),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
) -> Any:
    """List jobs with search, filtering, sorting, and pagination."""
    query = db.query(Job)
    
    # Search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_term),
                Job.company.ilike(search_term),
                Job.description.ilike(search_term),
                Job.location.ilike(search_term),
            )
        )
    
    # Filters
    if company:
        query = query.filter(Job.company.ilike(f"%{company}%"))
    
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    if source:
        query = query.filter(Job.source == source)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.filter(Job.tags.contains([tag]))
    
    if min_salary is not None:
        query = query.filter(
            or_(
                Job.salary_min >= min_salary,
                Job.salary_max >= min_salary,
            )
        )
    
    if max_salary is not None:
        query = query.filter(
            or_(
                Job.salary_max <= max_salary,
                Job.salary_min <= max_salary,
            )
        )
    
    # Get total count before pagination
    total = query.count()
    
    # Sorting
    sort_column = getattr(Job, sort_by, Job.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Pagination
    jobs = query.offset(skip).limit(limit).all()
    
    return JobListResponse(
        jobs=jobs,
        total=total,
        skip=skip,
        limit=limit,
    )


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
