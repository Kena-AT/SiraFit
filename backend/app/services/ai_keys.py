"""Shared AI credential resolution and fallback-chain building.

All three AI features (job analysis, resume generation, cover-letter
generation) resolve keys identically and can fall back across providers /
models when the chosen one is unavailable. Centralising this here removes the
three near-identical resolution blocks that used to live in each service.

Key resolution order (first match wins), per provider:
  1. An explicit API key passed in the request (e.g. ``X-AI-API-Key`` header).
  2. The user's own encrypted key stored via the Settings UI (DB).
  3. A server / user env key (``.env`` or ``USER_KEYS_ENV_FILE``).

When the chosen provider/model fails, ``build_candidates`` assembles an
ordered list of (provider, model, key) tuples so the caller can try each in
turn — this is the "juggle multiple models" behaviour.
"""

import json
import logging
import uuid
from typing import Optional

from app.core.config import settings
from app.core.security import decrypt_value

logger = logging.getLogger(__name__)

# Provider-to-API-key mapping
PROVIDER_KEY_FIELDS: dict[str, str] = {
    "gemini": "GEMINI_API",
    "openrouter": "OPENROUTER_API",
    "anthropic": "ANTHROPIC_API",
    "openai": "OPENAI_API",
    "grok": "GROK_API",
    "mistral": "MISTRAL_API",
    "nvidia": "NVIDIA_API",
}

# Default order to try when the user's chosen provider/model fails and they
# haven't configured an explicit fallback order in their preferences.
DEFAULT_FALLBACK_ORDER: list[str] = [
    "gemini",
    "openrouter",
    "anthropic",
    "openai",
    "mistral",
    "grok",
    "nvidia",
]

# Per-provider default model, used when a fallback candidate has no model set.
# Mirrors services/ai.DEFAULT_MODELS; kept local to avoid an import cycle.
DEFAULT_MODELS: dict[str, str] = {
    "gemini": "gemini-1.5-flash",
    "anthropic": "claude-3-5-sonnet-20240620",
    "openrouter": "openai/gpt-4o-mini",
    "openai": "gpt-4o-mini",
    "grok": "grok-beta",
    "mistral": "mistral-large-latest",
    "nvidia": "meta/llama-3.1-405b-instruct",
}

_PROVIDERS: list[str] = list(PROVIDER_KEY_FIELDS.keys())

_ENV_KEYS_CACHE: Optional[dict] = None


def get_env_provider_keys() -> dict:
    """Return ``provider -> api_key`` from server ``.env`` overlaid by a user file.

    Server env fields (``GEMINI_API``, ``OPENROUTER_API``, ...) are read first.
    If ``USER_KEYS_ENV_FILE`` is configured, its keys overlay the server ones.
    Result is cached after the first call within the process.
    """
    global _ENV_KEYS_CACHE
    if _ENV_KEYS_CACHE is not None:
        return _ENV_KEYS_CACHE

    keys: dict = {}
    for provider, field in PROVIDER_KEY_FIELDS.items():
        val = getattr(settings, field, None)
        if val:
            keys[provider] = val

    env_file = getattr(settings, "USER_KEYS_ENV_FILE", None)
    if env_file:
        try:
            from dotenv import dotenv_values

            vals = dotenv_values(env_file)
            for provider in _PROVIDERS:
                v = (
                    vals.get(PROVIDER_KEY_FIELDS[provider])
                    or vals.get(f"{provider.upper()}_API_KEY")
                    or vals.get(provider.upper())
                )
                if v:
                    keys[provider] = v
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load USER_KEYS_ENV_FILE (%s): %s", env_file, exc)

    _ENV_KEYS_CACHE = keys
    return keys


def get_user_stored_keys(db, user_id) -> dict:
    """Return ``provider -> decrypted key`` from the user's UI-stored keys."""
    from app.models.user import UserPreference

    try:
        uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    except Exception:
        return {}

    prefs = db.query(UserPreference).filter(UserPreference.user_id == uid).first()
    if not prefs:
        return {}

    out: dict = {}
    for provider in _PROVIDERS:
        enc = getattr(prefs, f"encrypted_{provider}_key", None)
        if enc:
            dec = decrypt_value(enc)
            if dec:
                out[provider] = dec

    # Stash the configured fallback order for callers that want it.
    prefs._ai_fallback_order = _parse_fallback_order(getattr(prefs, "ai_fallback_order", None))
    return out


def _parse_fallback_order(raw) -> Optional[list]:
    """Parse a stored fallback-order value (JSON string or list) -> list or None."""
    if not raw:
        return None
    if isinstance(raw, (list, tuple)):
        order = list(raw)
    else:
        try:
            order = json.loads(raw)
        except Exception:
            return None
    # Keep only known providers, de-duplicated, preserving order.
    seen = set()
    cleaned = []
    for p in order:
        p = (p or "").lower()
        if p in _PROVIDERS and p not in seen:
            seen.add(p)
            cleaned.append(p)
    return cleaned or None


def build_candidates(
    *,
    db=None,
    user_id=None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    request_api_key: Optional[str] = None,
    fallback_order: Optional[list] = None,
) -> list:
    """Assemble an ordered list of ``(provider, model, key)`` candidates to try.

    Order:
      1. Explicit request key (header) with its provider/model.
      2. The user's UI-stored key for the chosen provider.
      3. The env key for the chosen provider.
      4. Remaining providers (from ``fallback_order``) that have any key
         (user or env), each with its default model.
    """
    candidates: list = []
    seen: set = set()

    def add(prov: Optional[str], mdl: Optional[str], key: Optional[str]):
        if not prov or not key:
            return
        prov = prov.lower()
        if (prov, key) in seen:
            return
        candidates.append((prov, mdl or DEFAULT_MODELS.get(prov, ""), key))
        seen.add((prov, key))

    env_keys = get_env_provider_keys()
    user_keys = get_user_stored_keys(db, user_id) if db is not None and user_id else {}

    # 1. Request-supplied key (header override).
    if request_api_key:
        add(provider, model, request_api_key)

    # 2 & 3. Chosen provider from user/UI then env.
    if provider:
        provider = provider.lower()
        add(provider, model, user_keys.get(provider))
        add(provider, model, env_keys.get(provider))

    # 4. Fallback providers.
    order = fallback_order or DEFAULT_FALLBACK_ORDER
    for prov in order:
        if provider and prov == provider:
            continue
        add(prov, None, user_keys.get(prov))
        add(prov, None, env_keys.get(prov))

    return candidates


def get_user_fallback_order(db, user_id) -> Optional[list]:
    """Return the user's configured fallback order (list of providers) or None."""
    from app.models.user import UserPreference

    try:
        uid = uuid.UUID(str(user_id))
    except Exception:
        return None
    prefs = db.query(UserPreference).filter(UserPreference.user_id == uid).first()
    if not prefs:
        return None
    return _parse_fallback_order(getattr(prefs, "ai_fallback_order", None))


def available_providers(db=None, user_id=None) -> dict:
    """Return ``provider -> {"ui": bool, "env": bool}`` describing key availability.

    Used by the Settings UI to show whether a key is set via the UI, an env
    file, or neither (without ever exposing the key itself).
    """
    env_keys = get_env_provider_keys()
    user_keys = get_user_stored_keys(db, user_id) if db is not None and user_id else {}
    return {
        p: {"ui": p in user_keys, "env": p in env_keys} for p in _PROVIDERS
    }
