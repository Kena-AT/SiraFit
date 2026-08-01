"""
Agent API connection check.

Reports whether at least one AI provider is configured and reachable. Detection
is by Settings field name (each provider has its own `*_API` field), not by
key-prefix heuristics — the field name already identifies the provider.

A lightweight authenticated `GET <provider>/models` (via httpx, 5s timeout) is
used as the reachability probe. No provider SDKs are imported here; this module
must stay cheap to import (it runs on every landing-page health check).
"""

from __future__ import annotations

from typing import Optional

import httpx
from pydantic import BaseModel

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
PROVIDERS: list[dict] = [
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "attr": "OPENROUTER_API",
        "url": "https://openrouter.ai/api/v1/models",
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
        "url": "https://integrate.api.nvidia.com/v1/models",
        "auth": "bearer",
    },
]


def check_agent_api_connection() -> AgentAPIStatus:
    """
    Check whether the agent API is configured and reachable.

    Iterates configured providers in registry order; the first whose
    authenticated `GET /models` returns 2xx is the active provider. On
    failure, returns a professional, trace-free message.
    """
    configured = []
    for p in PROVIDERS:
        val = getattr(settings, p["attr"], None)
        # Consider a provider configured only if the value is a non-empty string (after stripping whitespace)
        if val and isinstance(val, str) and val.strip():
            configured.append((p, val))

    if not configured:
        return AgentAPIStatus(
            connected=False,
            source="none",
            error="No AI provider API key is configured",
        )

    for provider, key in configured:
        if _ping(provider, key):
            return AgentAPIStatus(
                connected=True,
                source="env",
                provider=provider["label"],
            )

    # Keys exist but none reached its API.
    first_label = configured[0][0]["label"]
    return AgentAPIStatus(
        connected=False,
        source="env",
        provider=first_label,
        error=f"{first_label} API key is set, but the connection check failed",
    )


def _ping(provider: dict, key: str) -> bool:
    """Return True if the provider's /models endpoint responds 2xx."""
    url = provider["url"]
    headers: dict[str, str] = {}
    auth = provider["auth"]

    if auth == "bearer":
        headers["Authorization"] = f"Bearer {key}"
    elif auth == "x-api-key":
        headers["x-api-key"] = key
        headers.update(provider.get("extra_headers", {}))
    # "query": key is embedded in the URL template

    if auth == "query":
        url = url.format(key=key)

    try:
        response = httpx.get(url, headers=headers, timeout=5.0)
        return 200 <= response.status_code < 300
    except Exception:
        return False


__all__ = ["AgentAPIStatus", "check_agent_api_connection", "PROVIDERS"]