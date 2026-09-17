"""Unit and integration tests for Sprint 8: Semantic Search & Embeddings (pgvector)."""
import math
import uuid
import pytest
from unittest.mock import MagicMock, patch

from app.models.job import Job
from app.models.user import User
from app.services.embeddings import (
    build_job_embedding_text,
    compute_source_hash,
    l2_normalize,
    generate_job_embedding,
    generate_query_embedding,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_VERSION,
)
from app.repositories.job_search import (
    keyword_search_jobs,
    semantic_search_jobs,
    reciprocal_rank_fusion,
    hybrid_search_jobs,
    find_similar_jobs,
)


# ---------------------------------------------------------------------------
# Embedding Service Unit Tests
# ---------------------------------------------------------------------------


def test_build_job_embedding_text_canonical_sections():
    """Verify canonical text builder includes existing fields with stable tags."""
    job = MagicMock()
    job.title = "Senior Backend Engineer"
    job.company = "SiraFit Tech"
    job.location = "Addis Ababa, Ethiopia"
    job.tags = ["Python", "FastAPI", "PostgreSQL"]
    job.description = "Build scalable vector search and microservices."

    text = build_job_embedding_text(job)
    assert "TITLE: Senior Backend Engineer" in text
    assert "COMPANY: SiraFit Tech" in text
    assert "LOCATION: Addis Ababa, Ethiopia" in text
    assert "SKILLS: Python, FastAPI, PostgreSQL" in text
    assert "DESCRIPTION: Build scalable vector search and microservices." in text


def test_build_job_embedding_text_handles_missing_fields():
    """Verify canonical text omits None/empty fields gracefully without crash."""
    job = MagicMock()
    job.title = "Frontend Developer"
    job.company = ""
    job.location = None
    job.tags = []
    job.description = None

    text = build_job_embedding_text(job)
    assert text == "TITLE: Frontend Developer"


def test_compute_source_hash_changes_with_content():
    """Verify hash is deterministic and changes when content changes."""
    text_a = "TITLE: Software Engineer\n\nCOMPANY: Acorn"
    text_b = "TITLE: Senior Software Engineer\n\nCOMPANY: Acorn"

    hash_a1 = compute_source_hash(text_a)
    hash_a2 = compute_source_hash(text_a)
    hash_b = compute_source_hash(text_b)

    assert hash_a1 == hash_a2
    assert hash_a1 != hash_b
    assert len(hash_a1) == 64


def test_l2_normalize():
    """Verify unit L2 normalization."""
    vec = [3.0, 4.0]
    normed = l2_normalize(vec)
    assert math.isclose(normed[0], 0.6)
    assert math.isclose(normed[1], 0.8)
    norm = math.sqrt(sum(x * x for x in normed))
    assert math.isclose(norm, 1.0)


@patch("app.services.embeddings.get_embedding_model")
def test_generate_job_embedding(mock_get_model):
    """Test generating a job embedding with mocked model."""
    mock_model = MagicMock()
    # Mock return of 384-dimensional vector
    dummy_vec = [0.1] * EMBEDDING_DIMENSION
    mock_model.encode.return_value = dummy_vec
    mock_get_model.return_value = mock_model

    job = MagicMock()
    job.title = "ML Engineer"
    job.company = "DeepMind"
    job.location = "London"
    job.tags = ["PyTorch"]
    job.description = "Train transformers"

    result = generate_job_embedding(job)
    assert len(result.vector) == EMBEDDING_DIMENSION
    assert result.model == EMBEDDING_MODEL_NAME
    assert result.version == EMBEDDING_VERSION
    assert result.dimension == EMBEDDING_DIMENSION
    assert result.source_hash is not None


@patch("app.services.embeddings.get_embedding_model")
def test_generate_query_embedding_empty_query_raises(mock_get_model):
    """Empty search query raises ValueError."""
    with pytest.raises(ValueError):
        generate_query_embedding("   ")


# ---------------------------------------------------------------------------
# Search Repository & RRF Unit Tests
# ---------------------------------------------------------------------------


def test_reciprocal_rank_fusion():
    """Test RRF fusion merges candidate lists and computes correct rank reciprocal scores."""
    job1 = MagicMock()
    job1.id = "j1"
    job1.created_at = "2026-09-01"

    job2 = MagicMock()
    job2.id = "j2"
    job2.created_at = "2026-09-02"

    job3 = MagicMock()
    job3.id = "j3"
    job3.created_at = "2026-09-03"

    # List 1 (e.g. keyword): j1 (rank 1), j2 (rank 2)
    # List 2 (e.g. semantic): j2 (rank 1), j3 (rank 2)
    ranked_lists = [[job1, job2], [job2, job3]]
    k = 60

    fused = reciprocal_rank_fusion(ranked_lists, k=k)
    # Scores:
    # j2: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 ~ 0.016129 + 0.016393 ~ 0.03252
    # j1: 1/(60+1) = 1/61 ~ 0.01639
    # j3: 1/(60+2) = 1/62 ~ 0.01613
    assert len(fused) == 3
    assert fused[0][0].id == "j2"
    assert fused[1][0].id == "j1"
    assert fused[2][0].id == "j3"


def test_keyword_and_semantic_search_with_db(db):
    """Test search repository with SQLite in-memory database."""
    # Create test jobs
    vec1 = [1.0] + [0.0] * (EMBEDDING_DIMENSION - 1)
    vec2 = [0.0, 1.0] + [0.0] * (EMBEDDING_DIMENSION - 2)

    j1 = Job(
        external_id="ext-1",
        title="FastAPI Backend Engineer",
        company="Fast Co",
        location="Remote",
        description="Write high performance Python APIs",
        embedding=vec1,
        embedding_model=EMBEDDING_MODEL_NAME,
        embedding_version=EMBEDDING_VERSION,
        embedding_status="ready",
    )
    j2 = Job(
        external_id="ext-2",
        title="React Frontend Developer",
        company="UI Corp",
        location="Berlin",
        description="Design intuitive web interfaces with TypeScript",
        embedding=vec2,
        embedding_model=EMBEDDING_MODEL_NAME,
        embedding_version=EMBEDDING_VERSION,
        embedding_status="ready",
    )
    db.add_all([j1, j2])
    db.commit()

    # Keyword search
    kw_jobs, total_kw = keyword_search_jobs(db, query_text="FastAPI")
    assert total_kw == 1
    assert kw_jobs[0].title == "FastAPI Backend Engineer"

    # Semantic search with query close to vec1
    q_vec1 = [0.9] + [0.0] * (EMBEDDING_DIMENSION - 1)
    sem_jobs, total_sem = semantic_search_jobs(db, query_vector=q_vec1)
    assert total_sem == 2
    assert sem_jobs[0].id == j1.id

    # Similar jobs
    similar = find_similar_jobs(db, source_job_id=j1.id, limit=5)
    assert len(similar) == 1
    assert similar[0].id == j2.id  # source job j1 excluded


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------


def test_api_jobs_search_keyword_and_modes(client, auth_headers, db):
    """Test /jobs/search with mode=keyword and similar jobs endpoint."""
    j = Job(
        external_id="ext-search-test",
        title="DevOps Cloud Architect",
        company="CloudScale",
        description="Kubernetes, Terraform and AWS deployments",
        embedding_status="pending",
    )
    db.add(j)
    db.commit()

    # Keyword mode
    resp = client.get("/api/v1/jobs/search?q=DevOps&mode=keyword", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(job["title"] == "DevOps Cloud Architect" for job in data["jobs"])

    # Similar endpoint with nonexistent job
    bad_id = uuid.uuid4()
    resp_bad = client.get(f"/api/v1/jobs/{bad_id}/similar", headers=auth_headers)
    assert resp_bad.status_code == 404

    # Similar endpoint with valid job
    resp_sim = client.get(f"/api/v1/jobs/{j.id}/similar", headers=auth_headers)
    assert resp_sim.status_code == 200
    assert "jobs" in resp_sim.json()
