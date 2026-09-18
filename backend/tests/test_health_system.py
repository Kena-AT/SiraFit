"""Health and System Status API tests (Sprint 15)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_live_is_lightweight():
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["alive"] is True


def test_health_ready_checks_dependencies():
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "database" in data


def test_system_status_sanitized_contract():
    response = client.get("/health/system-status")
    assert response.status_code == 200
    data = response.json()

    # Must contain top-level operational states
    assert "overall" in data
    assert "api" in data
    assert "database" in data
    assert "redis" in data
    assert "background_jobs" in data
    assert "last_checked" in data

    # Must NOT expose sensitive infrastructure details
    assert "pool_size" not in data
    assert "checked_out" not in data
    assert "disk_path" not in data
    assert "worker_hostname" not in data
