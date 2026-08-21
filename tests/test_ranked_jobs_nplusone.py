"""
Regression tests for the N+1 query fix in list_ranked_jobs.

Verifies that fetching N ranked jobs issues a bounded number of SQL
statements, NOT the old N+1 pattern of fetching each match score
individually via a separate query per job.

After the fix, the endpoint issues:
  - 1 query to SELECT the jobs
  - 1 batch query to SELECT all match scores (WHERE job_id IN ...)
for a total of 2 queries regardless of job count.
"""

from sqlalchemy import event

from app.core.security import create_access_token
from app.models.job import Job
from app.models.score import JobMatchScore


def test_ranked_jobs_does_not_nplusone(client, test_user, db):
    """Requesting ranked jobs for N jobs + N scores must issue <= 3 queries."""
    token = create_access_token(str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    jobs = []
    for i in range(5):
        job = Job(
            external_id=f"nplus1-ext-{i}",
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
                breakdown={},
                explanation="x",
            )
        )
    db.commit()

    query_count = {"n": 0}

    def _count(conn, cursor, statement, *args, **kwargs):
        query_count["n"] += 1

    engine = db.bind
    event.listen(engine, "before_cursor_execute", _count)
    try:
        resp = client.get("/api/v1/jobs/ranked", headers=headers)
    finally:
        event.remove(engine, "before_cursor_execute", _count)

    assert resp.status_code == 200
    # 1 query for jobs + 1 batch query for scores = 2.
    # Allow up to 3 to account for transaction setup overhead.
    assert query_count["n"] <= 3, (
        f"N+1 regression: list_ranked_jobs issued {query_count['n']} queries "
        f"for 5 jobs — expected at most 3 (1 for jobs + 1 batch score query)."
    )
    data = resp.json()
    assert len(data["jobs"]) == 5
