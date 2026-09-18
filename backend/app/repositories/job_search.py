"""Job Search Repository Layer (Sprint 8).

Encapsulates SQL and pgvector query abstractions, semantic search,
keyword search, and Reciprocal Rank Fusion (RRF) hybrid retrieval.
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import or_, text, cast, String

from app.core.config import settings
from app.models.job import Job
from app.services.embeddings import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_VERSION,
)

logger = logging.getLogger(__name__)


def is_postgres(db: Session) -> bool:
    """Check if current database session is PostgreSQL."""
    return db.bind.dialect.name == "postgresql" if db.bind else False


def keyword_search_jobs(
    db: Session,
    query_text: Optional[str],
    skip: int = 0,
    limit: int = 50,
    company: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    tags: Optional[str] = None,
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
    include_archived: bool = False,
) -> Tuple[List[Job], int]:
    """Standard keyword search filtering across title, company, description, location."""
    q = db.query(Job)
    if not include_archived:
        q = q.filter(Job.is_archived == False)  # noqa: E712

    if query_text and query_text.strip():
        term_clean = query_text.strip()
        if is_postgres(db):
            # Postgres FTS + Trigram
            fts_cond = text("search_vector @@ websearch_to_tsquery('english', :query)")
            # For fuzzy trigram matching, use similarity operator %
            trgm_cond = or_(
                Job.title.op("%")(term_clean), Job.company.op("%")(term_clean)
            )
            q = q.filter(or_(fts_cond, trgm_cond)).params(query=term_clean)

            # Rank based on a combination of FTS rank and Trigram word_similarity
            # We use GREATEST for word_similarity because we just care about the best fuzzy match
            fts_rank = text(
                "ts_rank_cd(search_vector, websearch_to_tsquery('english', :query))"
            )
            trgm_rank = text(
                "GREATEST(word_similarity(:query, title), word_similarity(:query, company))"
            )

            # Combine the scores. word_similarity is 0-1, ts_rank_cd can be > 1.
            # Normalization can be complex, but simple addition works as a baseline.
            relevance = (fts_rank + trgm_rank).desc()

            # Update order_by
            q = q.order_by(relevance, Job.created_at.desc())
        else:
            term = f"%{term_clean}%"
            q = q.filter(
                or_(
                    Job.title.ilike(term),
                    Job.company.ilike(term),
                    Job.description.ilike(term),
                    Job.location.ilike(term),
                )
            )
            q = q.order_by(Job.created_at.desc())
    else:
        q = q.order_by(Job.created_at.desc())

    if company:
        q = q.filter(Job.company.ilike(f"%{company}%"))
    if location:
        q = q.filter(Job.location.ilike(f"%{location}%"))
    if source:
        q = q.filter(Job.source == source)
    if tags:
        for tag in [t.strip() for t in tags.split(",")]:
            q = q.filter(cast(Job.tags, String).like(f'%"{tag}"%'))
    if min_salary is not None:
        q = q.filter(or_(Job.salary_min >= min_salary, Job.salary_max >= min_salary))
    if max_salary is not None:
        q = q.filter(or_(Job.salary_max <= max_salary, Job.salary_min <= max_salary))

    total = q.count()
    jobs = q.offset(skip).limit(limit).all()
    return jobs, total


def semantic_search_jobs(
    db: Session,
    query_vector: List[float],
    skip: int = 0,
    limit: int = 50,
    company: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    tags: Optional[str] = None,
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
    include_archived: bool = False,
) -> Tuple[List[Job], int]:
    """Semantic vector search using cosine distance on pgvector (or fallback in SQLite)."""
    expected_model = settings.EMBEDDING_MODEL or EMBEDDING_MODEL_NAME
    expected_version = settings.EMBEDDING_VERSION or EMBEDDING_VERSION

    # Base filter conditions
    filters = [
        Job.embedding_status == "ready",
        Job.embedding_model == expected_model,
        Job.embedding_version == expected_version,
    ]
    if not include_archived:
        filters.append(Job.is_archived == False)  # noqa: E712

    if company:
        filters.append(Job.company.ilike(f"%{company}%"))
    if location:
        filters.append(Job.location.ilike(f"%{location}%"))
    if source:
        filters.append(Job.source == source)
    if tags:
        for tag in [t.strip() for t in tags.split(",")]:
            filters.append(cast(Job.tags, String).like(f'%"{tag}"%'))
    if min_salary is not None:
        filters.append(or_(Job.salary_min >= min_salary, Job.salary_max >= min_salary))
    if max_salary is not None:
        filters.append(or_(Job.salary_max <= max_salary, Job.salary_min <= max_salary))

    if is_postgres(db):
        # Native pgvector cosine distance operator: <=>
        # ORDER BY embedding <=> query_vector ASC (closest first)
        query = db.query(Job).filter(*filters)
        total = query.count()
        # Bind vector literal formatted as PostgreSQL array format '[0.1,0.2,...]'
        vector_str = f"[{','.join(f'{x:.6f}' for x in query_vector)}]"
        jobs = (
            query.order_by(text(f"jobs.embedding <=> '{vector_str}'"))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return jobs, total
    else:
        # SQLite / Mock fallback: compute in-memory cosine distance for testing
        query = db.query(Job).filter(*filters)
        candidates = query.all()
        total = len(candidates)

        def cosine_dist(j: Job) -> float:
            emb = j.embedding
            if not emb or not isinstance(emb, list) or len(emb) != len(query_vector):
                return 2.0  # max cosine distance
            # Both vectors are unit normalized, cosine distance = 1 - dot_product
            dot = sum(a * b for a, b in zip(emb, query_vector))
            return 1.0 - dot

        candidates.sort(key=cosine_dist)
        return candidates[skip : skip + limit], total


def reciprocal_rank_fusion(
    ranked_lists: List[List[Job]], k: int = 60
) -> List[Tuple[Job, float]]:
    """Compute Reciprocal Rank Fusion (RRF) score for candidate jobs across ranked lists.

    Formula:
        RRF(d) = sum(1.0 / (k + rank_i(d)))
    where rank is 1-indexed.
    """
    scores: Dict[str, float] = {}
    job_map: Dict[str, Job] = {}

    for ranked_list in ranked_lists:
        for rank, job in enumerate(ranked_list, start=1):
            jid = str(job.id)
            job_map[jid] = job
            scores[jid] = scores.get(jid, 0.0) + (1.0 / (k + rank))

    # Sort descending by RRF score; tie-break deterministically by job.created_at desc
    sorted_items = sorted(
        [(job_map[jid], score) for jid, score in scores.items()],
        key=lambda item: (item[1], item[0].created_at or ""),
        reverse=True,
    )
    return sorted_items


def hybrid_search_jobs(
    db: Session,
    query_text: str,
    query_vector: List[float],
    skip: int = 0,
    limit: int = 50,
    candidate_k: int = 100,
    rrf_k: int = 60,
    **filter_kwargs,
) -> Tuple[List[Job], int]:
    """Execute hybrid retrieval: union of top-K keyword + top-K semantic, fused via RRF."""
    keyword_candidates, _ = keyword_search_jobs(
        db, query_text, skip=0, limit=candidate_k, **filter_kwargs
    )
    semantic_candidates, _ = semantic_search_jobs(
        db, query_vector, skip=0, limit=candidate_k, **filter_kwargs
    )

    fused_results = reciprocal_rank_fusion(
        [keyword_candidates, semantic_candidates], k=rrf_k
    )
    total = len(fused_results)
    page_jobs = [job for job, _score in fused_results[skip : skip + limit]]
    return page_jobs, total


def find_similar_jobs(
    db: Session,
    source_job_id: uuid.UUID | str,
    limit: int = 10,
    include_archived: bool = False,
) -> List[Job]:
    """Retrieve similar jobs based on pgvector cosine similarity to the source job.

    Excludes the source job itself, un-embedded jobs, and archived jobs.
    """
    if isinstance(source_job_id, str):
        try:
            source_uuid = uuid.UUID(source_job_id)
        except ValueError:
            return []
    else:
        source_uuid = source_job_id

    source_job = db.query(Job).filter(Job.id == source_uuid).first()
    if not source_job or not source_job.embedding:
        return []

    source_vector = source_job.embedding
    expected_model = settings.EMBEDDING_MODEL or EMBEDDING_MODEL_NAME
    expected_version = settings.EMBEDDING_VERSION or EMBEDDING_VERSION

    filters = [
        Job.id != source_uuid,
        Job.embedding_status == "ready",
        Job.embedding_model == expected_model,
        Job.embedding_version == expected_version,
    ]
    if not include_archived:
        filters.append(Job.is_archived == False)  # noqa: E712

    if is_postgres(db):
        vector_str = f"[{','.join(f'{x:.6f}' for x in source_vector)}]"
        return (
            db.query(Job)
            .filter(*filters)
            .order_by(text(f"jobs.embedding <=> '{vector_str}'"))
            .limit(limit)
            .all()
        )
    else:
        candidates = db.query(Job).filter(*filters).all()

        def cosine_dist(j: Job) -> float:
            emb = j.embedding
            if not emb or not isinstance(emb, list) or len(emb) != len(source_vector):
                return 2.0
            dot = sum(a * b for a, b in zip(emb, source_vector))
            return 1.0 - dot

        candidates.sort(key=cosine_dist)
        return candidates[:limit]
