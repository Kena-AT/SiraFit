"""
Tests for Session Import API Endpoints (Sprint 5).

Verifies validation probe, import submission, session deletion, platform discovery,
and user session listing, ensuring credentials never leak into response bodies.
"""

from unittest.mock import patch, MagicMock
import pytest
from app.services.session_management import store_user_session


def test_get_supported_platforms(client, auth_headers):
    """Verify GET /api/v1/jobs/import/session/platforms returns platforms list."""
    res = client.get("/api/v1/jobs/import/session/platforms", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "platforms" in data
    platforms = data["platforms"]
    assert "linkedin" in platforms
    assert "indeed" in platforms


def test_validate_session_endpoint_valid(client, auth_headers):
    """Verify POST /api/v1/jobs/import/session/{platform}/validate with valid cookies."""
    with patch("app.services.scraping.session_importer.SavedJobsImporter.validate_session") as mock_val:
        mock_val.return_value = (True, "Session is valid")

        res = client.post(
            "/api/v1/jobs/import/session/linkedin/validate",
            headers=auth_headers,
            json={
                "cookies": {"li_at": "AQED_TEST_COOKIE"},
                "consent_confirmed": True,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["message"] == "Session is valid"


def test_validate_session_endpoint_unsupported_platform(client, auth_headers):
    """Verify validate endpoint rejects unsupported platform with 400."""
    res = client.post(
        "/api/v1/jobs/import/session/glassdoor/validate",
        headers=auth_headers,
        json={
            "cookies": {"gd_tok": "123"},
            "consent_confirmed": True,
        },
    )
    assert res.status_code == 400
    assert "not supported" in res.json()["detail"].lower()


def test_import_session_requires_consent(client, auth_headers):
    """Verify POST /api/v1/jobs/import/session/{platform} fails if consent is False."""
    res = client.post(
        "/api/v1/jobs/import/session/linkedin",
        headers=auth_headers,
        json={
            "cookies": {"li_at": "AQED_TEST"},
            "consent_confirmed": False,
        },
    )
    assert res.status_code == 422
    assert "consent" in str(res.json()).lower()


def test_import_session_fails_without_cookies(client, auth_headers):
    """Verify POST /api/v1/jobs/import/session/{platform} fails if cookies are empty."""
    res = client.post(
        "/api/v1/jobs/import/session/linkedin",
        headers=auth_headers,
        json={
            "cookies": {},
            "consent_confirmed": True,
        },
    )
    assert res.status_code == 422


def test_import_session_success_returns_202(client, auth_headers, db, test_user):
    """Verify POST /api/v1/jobs/import/session/{platform} queues task and returns 202."""
    with patch("app.api.jobs.enqueue_session_import", return_value={"queued": True}) as mock_enqueue:
        res = client.post(
            "/api/v1/jobs/import/session/linkedin",
            headers=auth_headers,
            json={
                "cookies": {"li_at": "AQED_TEST_COOKIE_XYZ"},
                "consent_confirmed": True,
            },
        )
        assert res.status_code == 202
        data = res.json()
        assert data["import_record"]["status"] == "processing"
        assert data["import_record"]["id"] is not None

        # Ensure enqueue was called with keyword args
        mock_enqueue.assert_called_once_with(
            import_id=str(data["import_record"]["id"]),
            platform="linkedin",
            user_id=str(test_user.id),
        )

        # Verify response body contains ZERO credentials
        res_text = res.text
        assert "AQED_TEST_COOKIE_XYZ" not in res_text


def test_delete_session_endpoint(client, auth_headers, db, test_user):
    """Verify DELETE /api/v1/jobs/import/session/{platform} removes stored session."""
    # Seed a session
    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="indeed",
        session_data={"cookies": {"CTK": "my_indeed_tok"}},
    )

    res = client.delete("/api/v1/jobs/import/session/indeed", headers=auth_headers)
    assert res.status_code == 204


def test_get_user_sessions_endpoint_never_leaks_secrets(client, auth_headers, db, test_user):
    """Verify GET /api/v1/users/me/sessions returns metadata and no cookies/tokens."""
    secret_cookie = "SUPER_SECRET_COOKIE_VAL_777"
    store_user_session(
        db=db,
        user_id=test_user.id,
        platform="linkedin",
        session_data={"cookies": {"li_at": secret_cookie}},
    )

    res = client.get("/api/v1/users/me/sessions", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["platform"] == "linkedin"
    assert "stored_at" in data[0]

    # Critical security assertion: secret cookie never in API response
    assert secret_cookie not in res.text
