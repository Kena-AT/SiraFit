"""Dynamic AI Model Discovery service.

Queries provider API models endpoints (the "curl" discovery function) across
all supported providers (OpenAI, Anthropic, Gemini, OpenRouter, Groq, Mistral,
NVIDIA NIM) and returns standardized, selectable model choices.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
import httpx

logger = logging.getLogger(__name__)

# Standard fallback model lists when API key is missing or endpoint is unreachable.
FALLBACK_MODELS: dict[str, list[dict[str, str]]] = {
    "gemini": [
        {"id": "gemini-1.5-pro", "label": "Gemini 1.5 Pro (Google)"},
        {"id": "gemini-1.5-flash", "label": "Gemini 1.5 Flash (Google)"},
        {"id": "gemini-2.0-flash-exp", "label": "Gemini 2.0 Flash (Experimental)"},
    ],
    "openai": [
        {"id": "gpt-4o", "label": "GPT-4o (OpenAI Omni)"},
        {"id": "gpt-4o-mini", "label": "GPT-4o Mini (OpenAI Fast)"},
        {"id": "gpt-4-turbo", "label": "GPT-4 Turbo (OpenAI)"},
        {"id": "o1-mini", "label": "o1-mini (Reasoning)"},
        {"id": "o1-preview", "label": "o1-preview (Reasoning)"},
    ],
    "anthropic": [
        {"id": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet (Latest)"},
        {"id": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku (Fast)"},
        {"id": "claude-3-opus-20240229", "label": "Claude 3 Opus (High Intelligence)"},
    ],
    "openrouter": [
        {"id": "openai/gpt-4o-mini", "label": "OpenAI: GPT-4o-mini"},
        {"id": "anthropic/claude-3.5-sonnet", "label": "Anthropic: Claude 3.5 Sonnet"},
        {"id": "meta-llama/llama-3.3-70b-instruct", "label": "Meta: Llama 3.3 70B"},
        {"id": "deepseek/deepseek-chat", "label": "DeepSeek: V3"},
        {
            "id": "google/gemini-2.0-flash-exp:free",
            "label": "Google: Gemini 2.0 Flash (Free)",
        },
    ],
    "groq": [
        {"id": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B Versatile (Groq)"},
        {"id": "llama-3.1-8b-instant", "label": "Llama 3.1 8B Instant (Groq)"},
        {"id": "mixtral-8x7b-32768", "label": "Mixtral 8x7B (Groq)"},
        {
            "id": "deepseek-r1-distill-llama-70b",
            "label": "DeepSeek R1 Distill Llama 70B (Groq)",
        },
    ],
    "mistral": [
        {"id": "mistral-large-latest", "label": "Mistral Large (Latest)"},
        {"id": "mistral-small-latest", "label": "Mistral Small (Latest)"},
        {"id": "codestral-latest", "label": "Codestral (Code Specialist)"},
        {"id": "open-mistral-nemo", "label": "Mistral Nemo (12B)"},
    ],
    "grok": [
        {"id": "grok-2-latest", "label": "Grok 2 (xAI)"},
        {"id": "grok-2-vision-1212", "label": "Grok 2 Vision (xAI)"},
        {"id": "grok-beta", "label": "Grok Beta (xAI)"},
    ],
    "nvidia": [
        {
            "id": "nvidia/llama-3.1-nemotron-70b-instruct",
            "label": "Llama 3.1 Nemotron 70B (NVIDIA)",
        },
        {
            "id": "meta/llama-3.2-90b-vision-instruct",
            "label": "Llama 3.2 90B Vision (Meta/NVIDIA)",
        },
        {
            "id": "meta/llama-3.2-11b-vision-instruct",
            "label": "Llama 3.2 11B Vision (Meta/NVIDIA)",
        },
        {
            "id": "meta/llama-3.1-70b-instruct",
            "label": "Llama 3.1 70B Instruct (Meta/NVIDIA)",
        },
        {
            "id": "deepseek-ai/deepseek-coder-6.7b-instruct",
            "label": "DeepSeek Coder 6.7B (NVIDIA)",
        },
        {"id": "01-ai/yi-large", "label": "Yi Large (01.AI/NVIDIA)"},
    ],
}

# In-memory discovery cache: cache_key -> (timestamp, result_dict)
_MODEL_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 600  # 10 minutes cache


def get_fallback_models(provider: str) -> list[dict[str, str]]:
    """Return static fallback models for a provider."""
    return FALLBACK_MODELS.get(
        provider.lower(), [{"id": "default", "label": f"Default {provider} Model"}]
    )


async def fetch_provider_models(
    provider: str,
    api_key: Optional[str] = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Discover available models for a provider by calling its API models endpoint.

    Returns:
        dict with keys:
            provider: str
            source: "api" | "fallback"
            models: list of {"id": str, "label": str, "description": Optional[str]}
            error: Optional[str] explaining why fallback was used
    """
    prov = (provider or "").lower().strip()
    cache_key = f"{prov}:{(api_key or '')[:8]}"

    if not force_refresh and cache_key in _MODEL_CACHE:
        cached_time, cached_data = _MODEL_CACHE[cache_key]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            return cached_data

    if not api_key:
        fallback = {
            "provider": prov,
            "source": "fallback",
            "models": get_fallback_models(prov),
            "error": "No API key configured for this provider. Showing recommended models.",
        }
        return fallback

    try:
        models = await _query_provider_models_api(prov, api_key)
        if models:
            res = {
                "provider": prov,
                "source": "api",
                "models": models,
                "error": None,
            }
            _MODEL_CACHE[cache_key] = (time.time(), res)
            return res
        else:
            raise ValueError(f"Provider {prov} returned 0 models")
    except Exception as exc:
        logger.warning("Dynamic model discovery failed for %s: %s", prov, exc)
        fallback = {
            "provider": prov,
            "source": "fallback",
            "models": get_fallback_models(prov),
            "error": f"API error ({type(exc).__name__}): {str(exc)}. Showing fallback models.",
        }
        return fallback


async def _query_provider_models_api(
    provider: str, api_key: str
) -> list[dict[str, str]]:
    """Execute the HTTP query to the provider's /models endpoint."""
    async with httpx.AsyncClient(timeout=12.0) as client:
        if provider == "gemini":
            return await _fetch_gemini_models(client, api_key)
        elif provider == "anthropic":
            return await _fetch_anthropic_models(client, api_key)
        elif provider == "openai":
            return await _fetch_openai_models(client, api_key)
        elif provider == "openrouter":
            return await _fetch_openrouter_models(client, api_key)
        elif provider == "groq":
            return await _fetch_groq_models(client, api_key)
        elif provider == "mistral":
            return await _fetch_mistral_models(client, api_key)
        elif provider == "nvidia":
            return await _fetch_nvidia_models(client, api_key)
        elif provider == "grok":
            return await _fetch_grok_models(client, api_key)
        else:
            raise ValueError(
                f"Unsupported provider for dynamic model discovery: {provider}"
            )


async def _fetch_openai_models(
    client: httpx.AsyncClient, api_key: str
) -> list[dict[str, str]]:
    res = await client.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    res.raise_for_status()
    data = res.json()
    items = data.get("data", [])

    # Filter for relevant generative/chat models
    valid_models = []
    for item in items:
        mid = item.get("id", "")
        # Keep chat / reasoning models, exclude embeddings/tts/whisper/moderation
        if any(mid.startswith(p) for p in ("gpt-", "o1-", "o3-", "chatgpt-")):
            valid_models.append({"id": mid, "label": mid})

    # Sort so top models are first
    def _rank(m: dict[str, str]) -> int:
        mid = m["id"]
        if "gpt-4o" in mid:
            return 0
        if "o1" in mid or "o3" in mid:
            return 1
        if "gpt-4" in mid:
            return 2
        return 3

    valid_models.sort(key=_rank)
    return valid_models or FALLBACK_MODELS["openai"]


async def _fetch_anthropic_models(
    client: httpx.AsyncClient, api_key: str
) -> list[dict[str, str]]:
    res = await client.get(
        "https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    res.raise_for_status()
    data = res.json()
    items = data.get("data", [])
    models = []
    for item in items:
        mid = item.get("id", "")
        display = item.get("display_name", mid)
        models.append({"id": mid, "label": f"{display} ({mid})"})
    return models or FALLBACK_MODELS["anthropic"]


async def _fetch_gemini_models(
    client: httpx.AsyncClient, api_key: str
) -> list[dict[str, str]]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    res = await client.get(url)
    res.raise_for_status()
    data = res.json()
    items = data.get("models", [])
    models = []
    for item in items:
        methods = item.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            raw_name = item.get("name", "")
            mid = raw_name.replace("models/", "")
            display = item.get("displayName", mid)
            # Filter out embedding and vision-only legacy models
            if "embedding" not in mid and "aqa" not in mid:
                models.append({"id": mid, "label": f"{display} ({mid})"})
    return models or FALLBACK_MODELS["gemini"]


async def _fetch_openrouter_models(
    client: httpx.AsyncClient, api_key: str
) -> list[dict[str, str]]:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    res = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
    res.raise_for_status()
    data = res.json()
    items = data.get("data", [])
    models = []
    for item in items[:60]:  # Top 60 popular models
        mid = item.get("id", "")
        name = item.get("name", mid)
        models.append({"id": mid, "label": name})
    return models or FALLBACK_MODELS["openrouter"]


async def _fetch_groq_models(
    client: httpx.AsyncClient, api_key: str
) -> list[dict[str, str]]:
    res = await client.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    res.raise_for_status()
    data = res.json()
    items = data.get("data", [])
    models = []
    for item in items:
        if item.get("active", True):
            mid = item.get("id", "")
            if not mid.startswith("whisper"):
                models.append({"id": mid, "label": mid})
    return models or FALLBACK_MODELS["groq"]


async def _fetch_mistral_models(
    client: httpx.AsyncClient, api_key: str
) -> list[dict[str, str]]:
    res = await client.get(
        "https://api.mistral.ai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    res.raise_for_status()
    data = res.json()
    items = data.get("data", [])
    models = []
    for item in items:
        mid = item.get("id", "")
        # Filter for text/chat models
        if not mid.startswith("mistral-embed"):
            models.append({"id": mid, "label": mid})
    return models or FALLBACK_MODELS["mistral"]


async def _fetch_nvidia_models(
    client: httpx.AsyncClient, api_key: str
) -> list[dict[str, str]]:
    res = await client.get(
        "https://integrate.api.nvidia.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    res.raise_for_status()
    data = res.json()
    items = data.get("data", [])
    models = []
    for item in items:
        mid = item.get("id", "")
        # Exclude embedding/retriever/guard models unless chat capable
        if not any(x in mid.lower() for x in ("embed", "retriever", "guard")):
            models.append({"id": mid, "label": mid})
    # If filtered list is empty, take all
    if not models:
        for item in items:
            mid = item.get("id", "")
            models.append({"id": mid, "label": mid})
    return models or FALLBACK_MODELS["nvidia"]


async def _fetch_grok_models(
    client: httpx.AsyncClient, api_key: str
) -> list[dict[str, str]]:
    res = await client.get(
        "https://api.x.ai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    res.raise_for_status()
    data = res.json()
    items = data.get("data", [])
    models = [{"id": item.get("id", ""), "label": item.get("id", "")} for item in items]
    return models or FALLBACK_MODELS["grok"]
