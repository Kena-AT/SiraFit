"""
Regression tests for the /api/v1/jobs/with-scores endpoint.

Locks in the response contract used by the frontend Match page:
  - top-level key is "jobs" (NOT "items")
  - each item is { job, match_score } where match_score is a full
    JobMatchScore object (with a "score" key) or null — never a bare int
  - the endpoint issues a bounded number of SQL queries (no N+1)
"""

from sqlalchemy import event

from app.core.security import create_access_token
from app.models.job import Job
from app.models.score import JobMatchScore


def test_with_scores_contract_and_no_nplusone(client, test_user, db):
    token = create_access_token(str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    jobs = []
    for i in range(5):
        job = Job(
            external_id=f"ws-ext-{i}",
            title=f"Role {i}",
            company=f"Co {i}",
            location="HQ",
            source="test",
        )
        db.add(job)
        jobs.append(job)
    db.flush()

    for job in jobs:
        db.add(
            JobMatchScore(
                user_id=test_user.id,
                job_id=job.id,
                score=70,
                breakdown={"skills": 80},
                explanation="ok",
            )
        )
    db.commit()

    query_count = {"n": 0}

    def _count(conn, cursor, statement, *args, **kwargs):
        query_count["n"] += 1

    engine = db.bind
    event.listen(engine, "before_cursor_execute", _count)
    try:
        resp = client.get("/api/v1/jobs/with-scores", headers=headers)
    finally:
        event.remove(engine, "before_cursor_execute", _count)

    assert resp.status_code == 200
    data = resp.json()

    # Top-level key must be "jobs", not "items".
    assert "jobs" in data
    assert "items" not in data
    assert len(data["jobs"]) == 5

    # Each item must be { job, match_score } with match_score a full object.
    for item in data["jobs"]:
        assert "job" in item
        assert "match_score" in item
        assert isinstance(item["match_score"], dict)
        assert item["match_score"]["score"] == 70
        assert item["match_score"]["breakdown"] == {"skills": 80}

    # Bounded queries: 1 for jobs + 1 batch score query (+ setup slack).
    assert query_count["n"] <= 3, (
        f"/with-scores issued {query_count['n']} queries for 5 jobs — "
        f"expected at most 3 (no N+1)."
    )


def test_with_scores_null_when_unscored(client, test_user, db):
    """Jobs without a stored score must return match_score=null, not 0/int."""
    token = create_access_token(str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    job = Job(
        external_id="ws-unscored",
        title="No Score Role",
        company="Co X",
        location="HQ",
        source="test",
    )
    db.add(job)
    db.commit()

    resp = client.get("/api/v1/jobs/with-scores", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    unscored = [i for i in data["jobs"] if i["job"]["external_id"] == "ws-unscored"]
    assert unscored
    assert unscored[0]["match_score"] is None
