"""Search Evaluation and Benchmarking Suite (Sprint 8).

Evaluates 3 retrieval systems on a labeled test set:
1. Keyword-only
2. Semantic-only
3. Hybrid RRF

Calculates Precision@5, Precision@10, and Mean Reciprocal Rank (MRR).

Usage:
    python backend/scripts/evaluate_search.py
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Set

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.job import Job
from app.repositories.job_search import (
    keyword_search_jobs,
    semantic_search_jobs,
    hybrid_search_jobs,
)
from app.services.embeddings import generate_query_embedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_search")

# Curated query test dataset with target keywords / expected skills in retrieved jobs
BENCHMARK_QUERIES = [
    {
        "query": "python backend developer fastapi postgresql",
        "relevant_keywords": ["python", "fastapi", "backend", "django", "flask", "postgresql"],
    },
    {
        "query": "react frontend typescript ui engineer",
        "relevant_keywords": ["react", "frontend", "typescript", "ui", "javascript", "web"],
    },
    {
        "query": "machine learning engineer pytorch nlp",
        "relevant_keywords": ["machine learning", "pytorch", "nlp", "ai", "deep learning", "python"],
    },
    {
        "query": "devops infrastructure kubernetes terraform aws",
        "relevant_keywords": ["devops", "kubernetes", "terraform", "aws", "cloud", "docker", "ci/cd"],
    },
    {
        "query": "data engineer spark sql pipeline etl",
        "relevant_keywords": ["data engineer", "spark", "sql", "etl", "pipeline", "airflow"],
    },
]


def is_job_relevant(job: Job, relevant_keywords: List[str]) -> bool:
    """Check if job content contains any of the target relevance keywords."""
    text_blob = f"{job.title} {job.description or ''} {' '.join(job.tags or [])}".lower()
    return any(kw.lower() in text_blob for kw in relevant_keywords)


def precision_at_k(retrieved: List[Job], relevant_keywords: List[str], k: int) -> float:
    if not retrieved or k == 0:
        return 0.0
    top_k = retrieved[:k]
    relevant_count = sum(1 for j in top_k if is_job_relevant(j, relevant_keywords))
    return relevant_count / len(top_k)


def reciprocal_rank(retrieved: List[Job], relevant_keywords: List[str]) -> float:
    for rank, j in enumerate(retrieved, start=1):
        if is_job_relevant(j, relevant_keywords):
            return 1.0 / rank
    return 0.0


def evaluate():
    db = SessionLocal()
    try:
        total_jobs = db.query(Job).count()
        embedded_jobs = db.query(Job).filter(Job.embedding_status == "ready").count()
        logger.info("Evaluation Dataset: %d jobs total (%d embedded)", total_jobs, embedded_jobs)

        metrics = {
            "keyword": {"p5": [], "p10": [], "mrr": [], "latencies": []},
            "semantic": {"p5": [], "p10": [], "mrr": [], "latencies": []},
            "hybrid": {"p5": [], "p10": [], "mrr": [], "latencies": []},
        }

        for item in BENCHMARK_QUERIES:
            query = item["query"]
            rel_kw = item["relevant_keywords"]

            # 1. Keyword search
            t0 = time.perf_counter()
            kw_jobs, _ = keyword_search_jobs(db, query_text=query, limit=10)
            metrics["keyword"]["latencies"].append(time.perf_counter() - t0)
            metrics["keyword"]["p5"].append(precision_at_k(kw_jobs, rel_kw, 5))
            metrics["keyword"]["p10"].append(precision_at_k(kw_jobs, rel_kw, 10))
            metrics["keyword"]["mrr"].append(reciprocal_rank(kw_jobs, rel_kw))

            # 2. Semantic search
            try:
                t0 = time.perf_counter()
                q_vec = generate_query_embedding(query)
                sem_jobs, _ = semantic_search_jobs(db, query_vector=q_vec, limit=10)
                metrics["semantic"]["latencies"].append(time.perf_counter() - t0)
                metrics["semantic"]["p5"].append(precision_at_k(sem_jobs, rel_kw, 5))
                metrics["semantic"]["p10"].append(precision_at_k(sem_jobs, rel_kw, 10))
                metrics["semantic"]["mrr"].append(reciprocal_rank(sem_jobs, rel_kw))
            except Exception as e:
                logger.warning("Semantic search skipped: %s", e)

            # 3. Hybrid search
            try:
                t0 = time.perf_counter()
                q_vec = generate_query_embedding(query)
                hyb_jobs, _ = hybrid_search_jobs(db, query_text=query, query_vector=q_vec, limit=10)
                metrics["hybrid"]["latencies"].append(time.perf_counter() - t0)
                metrics["hybrid"]["p5"].append(precision_at_k(hyb_jobs, rel_kw, 5))
                metrics["hybrid"]["p10"].append(precision_at_k(hyb_jobs, rel_kw, 10))
                metrics["hybrid"]["mrr"].append(reciprocal_rank(hyb_jobs, rel_kw))
            except Exception as e:
                logger.warning("Hybrid search skipped: %s", e)

        print("\n" + "=" * 65)
        print(" SPRINT 8 SEARCH RETRIEVAL BENCHMARK RESULTS")
        print("=" * 65)
        print(f"{'System':<15} | {'P@5':<8} | {'P@10':<8} | {'MRR':<8} | {'Avg Latency':<12}")
        print("-" * 65)

        for mode, data in metrics.items():
            if data["p5"]:
                avg_p5 = sum(data["p5"]) / len(data["p5"])
                avg_p10 = sum(data["p10"]) / len(data["p10"])
                avg_mrr = sum(data["mrr"]) / len(data["mrr"])
                avg_lat = (sum(data["latencies"]) / len(data["latencies"])) * 1000
                print(
                    f"{mode.capitalize():<15} | {avg_p5:<8.3f} | {avg_p10:<8.3f} | {avg_mrr:<8.3f} | {avg_lat:<8.1f} ms"
                )
            else:
                print(f"{mode.capitalize():<15} | N/A (no embeddings/models available)")
        print("=" * 65 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    evaluate()
