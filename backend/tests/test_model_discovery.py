"""Unit tests for Dynamic AI Model Discovery and API Key resolution."""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.model_discovery import fetch_provider_models, get_fallback_models
from app.services.ai_keys import get_env_provider_keys, build_candidates


def test_fallback_models_exist_for_all_supported_providers():
    """Verify all 7 supported providers have fallback model definitions."""
    providers = [
        "gemini",
        "openai",
        "anthropic",
        "openrouter",
        "groq",
        "mistral",
        "nvidia",
        "grok",
    ]
    for p in providers:
        models = get_fallback_models(p)
        assert len(models) > 0
        assert "id" in models[0]
        assert "label" in models[0]


@pytest.mark.asyncio
async def test_fetch_provider_models_no_key_returns_fallback():
    """When no API key is available, should gracefully return fallback models with explanatory notice."""
    res = await fetch_provider_models("groq", api_key=None)
    assert res["provider"] == "groq"
    assert res["source"] == "fallback"
    assert len(res["models"]) > 0
    assert "No API key" in res["error"]


@pytest.mark.asyncio
async def test_fetch_provider_models_mock_api_success():
    """When external API returns 200, should parse and return live models with source='api'."""
    mock_payload = {
        "data": [
            {"id": "meta/llama-3.1-70b-instruct"},
            {"id": "nvidia/llama-3.1-nemotron-70b-instruct"},
            {"id": "test/embedding-model"},  # Should be filtered out
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_resp.json = lambda: mock_payload
        mock_get.return_value = mock_resp

        res = await fetch_provider_models(
            "nvidia", api_key="test_key_12345", force_refresh=True
        )
        assert res["provider"] == "nvidia"
        assert res["source"] == "api"
        model_ids = [m["id"] for m in res["models"]]
        assert "meta/llama-3.1-70b-instruct" in model_ids
        assert "nvidia/llama-3.1-nemotron-70b-instruct" in model_ids
        assert "test/embedding-model" not in model_ids


@pytest.mark.asyncio
async def test_fetch_provider_models_api_failure_falls_back():
    """When external API raises an error or times out, should return fallback catalog without raising exception."""
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection timed out")):
        res = await fetch_provider_models(
            "mistral", api_key="bad_key", force_refresh=True
        )
        assert res["provider"] == "mistral"
        assert res["source"] == "fallback"
        assert len(res["models"]) > 0
        assert "Showing fallback models" in res["error"]


def test_env_keys_extraction():
    """Verify that env provider keys extraction discovers available keys."""
    keys = get_env_provider_keys()
    assert isinstance(keys, dict)
    # The active environment has at least NVIDIA or GEMINI keys configured
    assert any(k in keys for k in ["nvidia", "gemini", "openai"])


def test_build_candidates_ordering():
    """Verify candidate building puts primary choice first and handles failover."""
    candidates = build_candidates(
        provider="nvidia",
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        fallback_order=["gemini", "openai", "groq"],
    )
    assert len(candidates) >= 1
    # First candidate must match primary
    assert candidates[0][0] == "nvidia"
    assert candidates[0][1] == "nvidia/llama-3.1-nemotron-70b-instruct"


def test_agent_api_unauthorized_key_never_reports_connected():
    """Verify that if an API key fails completion authorization (e.g. 404 function not found or 401),
    it is NEVER reported as connected even if public catalog /models returns 200."""
    from app.services.agent_api import _ping, PROVIDERS

    nvidia_p = next(p for p in PROVIDERS if p["id"] == "nvidia")

    # Mock chat completion returning 404 Not Found (Function not found for account)
    with patch("httpx.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status_code = 404
        mock_resp.json = lambda: {
            "status": 404,
            "detail": "Function not found for account",
        }
        mock_post.return_value = mock_resp

        is_connected = _ping(nvidia_p, "nvapi-test-unauthorized-key-123456789")
        assert is_connected is False


def test_agent_api_authorized_key_reports_connected():
    """Verify that when completion returns 200 with choices, the API is guaranteed connected."""
    from app.services.agent_api import _ping, PROVIDERS

    nvidia_p = next(p for p in PROVIDERS if p["id"] == "nvidia")

    with patch("httpx.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {"choices": [{"message": {"content": "pong"}}]}
        mock_post.return_value = mock_resp

        is_connected = _ping(nvidia_p, "nvapi-test-valid-working-key-123456789")
        assert is_connected is True
