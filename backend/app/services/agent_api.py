"""
Agent API connection check.

Reports whether at least one AI provider is configured and reachable. Detection
is by Settings field name (each provider has its own `*_API` field), not by
key-prefix heuristics — the field name already identifies the provider.

A lightweight authenticated `GET <provider>/models` (via httpx, 5s timeout) is
used as the reachability probe. No provider SDKs are imported here; this module
must stay cheap to import (it runs on every landing-page health check).

Caveat: results are cached for 60 s in Redis so that the landing-page /health/status
probe does not re-dial every provider on every poll (~once per minute). The cache key
includes provider name so each provider gets its own slot.
"""

from __future__ import annotations

from typing import Optional

import hashlib
import httpx
from pydantic import BaseModel

from app.core.cache import cache_get, cache_set
from app.core.config import settings


class AgentAPIStatus(BaseModel):
    connected: bool
    source: str  # "env" | "settings_ui" | "none"
    provider: Optional[str] = None  # human label, e.g. "OpenRouter"
    error: Optional[str] = None


# Provider registry — ordered. The first provider with a key that reaches its
# API is the "active" one surfaced on the landing page. OpenRouter first (most
# permissive / most likely configured), then the direct vendors.
#   auth: "bearer"    -> `Authorization: Bearer <key>`
#         "x-api-key" -> `x-api-key: <key>` (Anthropic)
#         "query"     -> `?key=<key>` (Gemini)
# Provider registry — ordered. The first provider with a key that reaches its
# API and is guaranteed functional is the "active" one.
PROVIDERS: list[dict] = [
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "attr": "OPENROUTER_API",
        "url": "https://openrouter.ai/api/v1/auth/key",
        "auth": "bearer",
    },
    {
        "id": "gemini",
        "label": "Gemini",
        "attr": "GEMINI_API",
        "url": "https://generativelanguage.googleapis.com/v1beta/models?key={key}",
        "auth": "query",
    },
    {
        "id": "anthropic",
        "label": "Claude (Anthropic)",
        "attr": "ANTHROPIC_API",
        "url": "https://api.anthropic.com/v1/models",
        "auth": "x-api-key",
        "extra_headers": {"anthropic-version": "2023-06-01"},
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "attr": "OPENAI_API",
        "url": "https://api.openai.com/v1/models",
        "auth": "bearer",
    },
    {
        "id": "groq",
        "label": "Groq",
        "attr": "GROQ_API",
        "url": "https://api.groq.com/openai/v1/models",
        "auth": "bearer",
    },
    {
        "id": "grok",
        "label": "Grok (xAI)",
        "attr": "GROK_API",
        "url": "https://api.x.ai/v1/models",
        "auth": "bearer",
    },
    {
        "id": "mistral",
        "label": "Mistral AI",
        "attr": "MISTRAL_API",
        "url": "https://api.mistral.ai/v1/models",
        "auth": "bearer",
    },
    {
        "id": "nvidia",
        "label": "Nvidia NIM",
        "attr": "NVIDIA_API",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "auth": "bearer",
    },
]


def is_valid_candidate_key(key: Optional[str]) -> bool:
    """Return True if the key is non-empty and not a known placeholder string."""
    if not key or not isinstance(key, str):
        return False
    k = key.strip()
    if len(k) < 10:
        return False
    low = k.lower()
    for placeholder in (
        "not_set",
        "your_key",
        "your-key",
        "your_api_key",
        "placeholder",
        "example",
        "api_key_here",
        "sk-...",
        "dummy",
        "replace_me",
        "none",
    ):
        if placeholder in low:
            return False
    return True


def check_agent_api_connection(db=None, user_id=None) -> AgentAPIStatus:
    """
    Check whether an agent API is configured and GUARANTEED functional.

    A provider is ONLY reported as connected if an authenticated live probe
    confirms reachability and authorization. Public endpoints that return 200
    without authentication (such as Nvidia/OpenRouter /models catalogs) are never
    treated as sufficient proof of connectivity.
    """
    from app.services.ai_keys import get_env_provider_keys, resolve_provider_key

    # Check if a specific user context is available
    if db is not None and user_id:
        from app.models.user import UserPreference

        prefs = (
            db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        )
        if prefs and prefs.ai_provider:
            pref_p = next(
                (p for p in PROVIDERS if p["id"] == prefs.ai_provider.lower()), None
            )
            if pref_p:
                key = resolve_provider_key(pref_p["id"], db=db, user_id=user_id)
                if is_valid_candidate_key(key) and _ping(pref_p, key):
                    return AgentAPIStatus(
                        connected=True,
                        source="settings_ui"
                        if getattr(prefs, f"encrypted_{pref_p['id']}_key", None)
                        else "env",
                        provider=pref_p["label"],
                    )

    # Inspect all configured environment keys across aliases
    env_keys = get_env_provider_keys()
    configured: list[tuple[dict, str]] = []
    for p in PROVIDERS:
        key = env_keys.get(p["id"]) or getattr(settings, p["attr"], None)
        if is_valid_candidate_key(key):
            configured.append((p, key.strip()))

    if not configured:
        return AgentAPIStatus(
            connected=False,
            source="none",
            error="No AI provider API key is configured",
        )

    # Probe each candidate in priority order
    for provider, key in configured:
        if _ping(provider, key):
            return AgentAPIStatus(
                connected=True,
                source="env",
                provider=provider["label"],
            )

    first_label = configured[0][0]["label"]
    return AgentAPIStatus(
        connected=False,
        source="env",
        provider=first_label,
        error=f"{first_label} API key is set, but the connection check failed",
    )


def _ping(provider: dict, key: str) -> bool:
    """Return True ONLY if the provider's authenticated endpoint responds 2xx with valid data.

    Checks cache first with 60s TTL so the health check doesn't spam external APIs.
    """
    if not is_valid_candidate_key(key):
        return False

    cache_key = f"agent_api_guaranteed:{provider['id']}:{hashlib.sha256(key.encode()).hexdigest()[:16]}"
    cached = cache_get(cache_key)
    if cached is not None:
        return bool(cached)

    pid = provider["id"]
    try:
        if pid == "nvidia":
            # NVIDIA's GET /models endpoint is public and unauthenticated.
            # A 1-token completion probe is required to guarantee the key is active and authorized.
            probe_url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {
                "model": "nvidia/llama-3.1-nemotron-70b-instruct",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            }
            resp = httpx.post(probe_url, headers=headers, json=payload, timeout=5.0)
            is_valid = 200 <= resp.status_code < 300 and "choices" in resp.json()
        elif pid == "openrouter":
            # OpenRouter's /models endpoint is public. /auth/key verifies the key and returns key metadata.
            resp = httpx.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {key}"},
                timeout=5.0,
            )
            is_valid = 200 <= resp.status_code < 300 and isinstance(
                resp.json().get("data"), dict
            )
        elif pid == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            resp = httpx.get(url, timeout=5.0)
            is_valid = 200 <= resp.status_code < 300 and bool(resp.json().get("models"))
        else:
            headers = {}
            if provider.get("auth") == "bearer":
                headers["Authorization"] = f"Bearer {key}"
            elif provider.get("auth") == "x-api-key":
                headers["x-api-key"] = key
                headers.update(provider.get("extra_headers", {}))
            resp = httpx.get(provider["url"], headers=headers, timeout=5.0)
            is_valid = 200 <= resp.status_code < 300 and bool(resp.json().get("data"))

        cache_set(cache_key, is_valid, ttl=60 if is_valid else 30)
        return is_valid
    except Exception:
        cache_set(cache_key, False, ttl=30)
        return False


__all__ = ["AgentAPIStatus", "check_agent_api_connection", "PROVIDERS"]
