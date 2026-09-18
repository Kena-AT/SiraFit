"""Embedding service for job semantic search (Sprint 8).

Implements canonical text serialization, source hashing, model loading,
vector generation, dimension validation, and normalization for:
    sentence-transformers/all-MiniLM-L6-v2 (384-d, cosine distance)
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass
from typing import Any, List

from app.core.config import settings

logger = logging.getLogger(__name__)

# Embedding Contract constants
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_VERSION = "v1"
EMBEDDING_DIMENSION = 384
INPUT_BUILDER_VERSION = "job-v1"
DISTANCE_METRIC = "cosine"


@dataclass
class EmbeddingResult:
    vector: List[float]
    model: str
    version: str
    dimension: int
    source_hash: str


_model_instance = None


def get_embedding_model():
    """Lazy singleton loader for the sentence-transformers embedding model."""
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer

        logger.info(
            "Loading embedding model: %s",
            settings.EMBEDDING_MODEL or EMBEDDING_MODEL_NAME,
        )
        _model_instance = SentenceTransformer(
            settings.EMBEDDING_MODEL or EMBEDDING_MODEL_NAME
        )
    return _model_instance


def build_job_embedding_text(job: Any) -> str:
    """Construct canonical, versioned job text representation for embedding.

    Only incorporates fields present on the Job model with stable delimiters.
    Version: job-v1.
    """
    parts = []

    title = getattr(job, "title", "") or ""
    if title.strip():
        parts.append(f"TITLE: {title.strip()}")

    company = getattr(job, "company", "") or ""
    if company.strip():
        parts.append(f"COMPANY: {company.strip()}")

    location = getattr(job, "location", "") or ""
    if location.strip():
        parts.append(f"LOCATION: {location.strip()}")

    tags = getattr(job, "tags", None)
    if tags:
        if isinstance(tags, list):
            tags_str = ", ".join(str(t).strip() for t in tags if str(t).strip())
        elif isinstance(tags, str):
            tags_str = tags.strip()
        else:
            tags_str = ""
        if tags_str:
            parts.append(f"SKILLS: {tags_str}")

    description = getattr(job, "description", "") or ""
    if description.strip():
        # Option A: Bounded canonical text fitting the token limit
        # Approximate ~4 chars per token, max ~256 tokens => ~1000 characters for description
        desc_clean = description.strip()
        if len(desc_clean) > 1200:
            desc_clean = desc_clean[:1200].rsplit(" ", 1)[0] + "..."
        parts.append(f"DESCRIPTION: {desc_clean}")

    return "\n\n".join(parts)


def compute_source_hash(canonical_text: str) -> str:
    """Calculate SHA-256 hash of canonical text coupled with input builder version."""
    payload = f"{INPUT_BUILDER_VERSION}:{canonical_text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def l2_normalize(vec: List[float]) -> List[float]:
    """Compute unit L2 normalized vector so cosine distance equals 1 - dot product."""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def generate_job_embedding(job: Any) -> EmbeddingResult:
    """Generate normalized 384-d embedding for a job."""
    canonical_text = build_job_embedding_text(job)
    source_hash = compute_source_hash(canonical_text)

    model = get_embedding_model()
    # SentenceTransformer encode
    raw_vector = model.encode(canonical_text, normalize_embeddings=True)
    if hasattr(raw_vector, "tolist"):
        vector = raw_vector.tolist()
    else:
        vector = list(raw_vector)

    # Validate output dimension
    expected_dim = settings.EMBEDDING_DIMENSION or EMBEDDING_DIMENSION
    if len(vector) != expected_dim:
        raise ValueError(
            f"Embedding dimension mismatch: expected {expected_dim}, got {len(vector)}"
        )

    # Ensure normalized
    norm = math.sqrt(sum(x * x for x in vector))
    if not math.isclose(norm, 1.0, rel_tol=1e-3):
        vector = l2_normalize(vector)

    return EmbeddingResult(
        vector=vector,
        model=settings.EMBEDDING_MODEL or EMBEDDING_MODEL_NAME,
        version=settings.EMBEDDING_VERSION or EMBEDDING_VERSION,
        dimension=expected_dim,
        source_hash=source_hash,
    )


def generate_query_embedding(query: str) -> List[float]:
    """Generate normalized embedding for search query using exact same contract."""
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Search query cannot be empty")

    model = get_embedding_model()
    raw_vector = model.encode(clean_query, normalize_embeddings=True)
    if hasattr(raw_vector, "tolist"):
        vector = raw_vector.tolist()
    else:
        vector = list(raw_vector)

    expected_dim = settings.EMBEDDING_DIMENSION or EMBEDDING_DIMENSION
    if len(vector) != expected_dim:
        raise ValueError(
            f"Query embedding dimension mismatch: expected {expected_dim}, got {len(vector)}"
        )

    norm = math.sqrt(sum(x * x for x in vector))
    if not math.isclose(norm, 1.0, rel_tol=1e-3):
        vector = l2_normalize(vector)

    return vector
