"""Cache invalidation regression tests (Remediation Plan 4.1 / 4.2).

The app cache is a no-op in the ``testing`` environment, so we cannot assert on
real cache contents. Instead we monkeypatch the low-level ``cache_delete`` /
``cache_delete_prefix`` primitives and assert that every mutation endpoint (and
the batch runner) requests deletion of the correct keys. This proves both the
key construction inside the centralized helpers and that the endpoints are wired
to invoke them.

Migrated from the legacy ``backend/tests`` suite into the canonical
``tests/`` suite. Uses the shared fixtures (``db``, ``test_user``, ``client``,
``auth_headers``) provided by ``tests/conftest.py``; the ``db`` fixture is
required at import time so the test DB schema is built before these tests run.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.api.users import get_current_user
from app.models.user import User
from app.models.job import Job, JobApplication
from app.models.batch import BatchJob


client = TestClient(app)

TEST_USER_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def override_dependencies(db):
    app.dependency_overrides[get_db] = lambda: db
    mock_user = User(
        id=TEST_USER_ID,
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_job(db) -> Job:
    job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Test Company",
        source="linkedin",
        external_id="123",
    )
    db.add(job)
    db.commit()
    return job


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def cache_recorder(monkeypatch):
    calls = {"delete": [], "prefix": []}

    def fake_delete(key):
        calls["delete"].append(key)

    def fake_delete_prefix(prefix):
        calls["prefix"].append(prefix)

    monkeypatch.setattr("app.core.cache.cache_delete", fake_delete)
    monkeypatch.setattr("app.core.cache.cache_delete_prefix", fake_delete_prefix)
    return calls


# ---------------------------------------------------------------------------
# Helper-level: key construction is correct
# ---------------------------------------------------------------------------


def test_invalidate_job_related_keys(cache_recorder):
    from app.core.cache import invalidate_job_related

    invalidate_job_related(TEST_USER_ID)

    assert any(k.startswith(f"jobs:list:{TEST_USER_ID}:") for k in cache_recorder["prefix"])
    assert f"dashboard:stats:{TEST_USER_ID}" in cache_recorder["delete"]


def test_invalidate_match_score_keys(cache_recorder):
    from app.core.cache import invalidate_match_score

    job_id = uuid.uuid4()
    invalidate_match_score(TEST_USER_ID, job_id)

    assert f"match_score:{TEST_USER_ID}:{job_id}" in cache_recorder["delete"]
    assert f"dashboard:stats:{TEST_USER_ID}" in cache_recorder["delete"]


def test_invalidate_user_profile_keys(cache_recorder):
    from app.core.cache import invalidate_user_profile

    invalidate_user_profile(TEST_USER_ID)

    assert f"user:me:{TEST_USER_ID}" in cache_recorder["delete"]


# ---------------------------------------------------------------------------
# Endpoint-level: mutations are wired to invalidate the right caches
# ---------------------------------------------------------------------------


def test_create_application_invalidates(db, mock_job, auth_headers, cache_recorder):
    response = client.post(
        "/api/v1/applications/",
        json={"job_id": str(mock_job.id)},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert any(k.startswith(f"jobs:list:{TEST_USER_ID}:") for k in cache_recorder["prefix"])
    assert f"dashboard:stats:{TEST_USER_ID}" in cache_recorder["delete"]
    assert f"match_score:{TEST_USER_ID}:{mock_job.id}" in cache_recorder["delete"]


def test_transition_status_invalidates(db, mock_job, auth_headers, cache_recorder):
    app_row = JobApplication(
        id=uuid.uuid4(),
        user_id=TEST_USER_ID,
        job_id=mock_job.id,
        status="applied",
    )
    db.add(app_row)
    db.commit()

    response = client.post(
        f"/api/v1/applications/{app_row.id}/status",
        json={"to_status": "screening"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert any(k.startswith(f"jobs:list:{TEST_USER_ID}:") for k in cache_recorder["prefix"])
    assert f"dashboard:stats:{TEST_USER_ID}" in cache_recorder["delete"]
    assert f"match_score:{TEST_USER_ID}:{mock_job.id}" in cache_recorder["delete"]


def test_update_notification_preferences_invalidates_user_me(
    db, auth_headers, cache_recorder
):
    response = client.put(
        "/api/v1/users/me/preferences/notifications",
        json={"email_job_matches": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert f"user:me:{TEST_USER_ID}" in cache_recorder["delete"]


def test_update_resume_defaults_invalidates_user_me(db, auth_headers, cache_recorder):
    response = client.put(
        "/api/v1/users/me/preferences/resume",
        json={"default_template": "classic"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert f"user:me:{TEST_USER_ID}" in cache_recorder["delete"]


def test_update_ai_provider_keys_invalidates_user_me(db, auth_headers, cache_recorder):
    response = client.put(
        "/api/v1/users/me/preferences/ai-keys",
        json={"gemini_key": ""},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert f"user:me:{TEST_USER_ID}" in cache_recorder["delete"]


def test_create_resume_invalidates_dashboard(db, auth_headers, cache_recorder):
    response = client.post(
        "/api/v1/resumes/",
        json={"title": "My Resume", "content": "experience"},
        headers=auth_headers,
    )
    assert response.status_code in (200, 201)
    assert f"dashboard:stats:{TEST_USER_ID}" in cache_recorder["delete"]


def test_create_cover_letter_invalidates_dashboard(db, auth_headers, cache_recorder):
    response = client.post(
        "/api/v1/cover-letters/",
        json={"title": "CL", "body": "hello"},
        headers=auth_headers,
    )
    assert response.status_code in (200, 201)
    assert f"dashboard:stats:{TEST_USER_ID}" in cache_recorder["delete"]


def test_batch_tag_invalidates_cache(db, mock_job, cache_recorder, monkeypatch):
    import app.services.batch as batch_module

    # Run the batch synchronously against the test DB session.
    monkeypatch.setattr("app.core.database.SessionLocal", lambda: db)

    batch_job = BatchJob(
        id=uuid.uuid4(),
        user_id=TEST_USER_ID,
        operation_type="tag",
        status="pending",
        total_items=1,
        processed_items=0,
        succeeded_items=0,
        failed_items=0,
        payload={"job_ids": [str(mock_job.id)], "params": {"tags": ["urgent"], "action": "add"}},
        result_summary={},
        cancel_requested=False,
    )
    db.add(batch_job)
    db.commit()

    batch_module._run_batch_job(batch_job.id)

    assert any(k.startswith(f"jobs:list:{TEST_USER_ID}:") for k in cache_recorder["prefix"])
    assert f"dashboard:stats:{TEST_USER_ID}" in cache_recorder["delete"]
