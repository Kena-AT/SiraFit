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
    "anthropic": "claude-3-5-sonnet-20241022",
    "openrouter": "openai/gpt-4o-mini",
    "openai": "gpt-4o-mini",
    "grok": "grok-beta",
    "mistral": "mistral-large-latest",
    "nvidia": "nvidia/llama-3.1-nemotron-70b-instruct",
}

_PROVIDERS: list[str] = list(PROVIDER_KEY_FIELDS.keys())

_ENV_KEYS_CACHE: Optional[dict] = None
_CACHE_TIMESTAMP: float = 0.0


def get_env_provider_keys(force_reload: bool = False) -> dict:
    """Return ``provider -> api_key`` from server ``.env`` overlaid by a user file and os.environ.

    Checks:
    1. settings (Pydantic settings)
    2. os.environ directly for both PROVIDER_API and PROVIDER_API_KEY
    3. backend/.env and root .env via dotenv_values
    4. USER_KEYS_ENV_FILE if configured
    """
    global _ENV_KEYS_CACHE, _CACHE_TIMESTAMP
    import os
    import time
    from pathlib import Path
    from dotenv import dotenv_values

    # Cache for 15 seconds unless forced, so changes to .env files are picked up quickly
    if (
        not force_reload
        and _ENV_KEYS_CACHE is not None
        and (time.time() - _CACHE_TIMESTAMP < 15.0)
    ):
        return _ENV_KEYS_CACHE

    keys: dict = {}

    # 1. Read from settings
    for provider, field in PROVIDER_KEY_FIELDS.items():
        val = getattr(settings, field, None)
        if val:
            keys[provider] = val

    # 2. Inspect backend/.env and root .env directly
    root_env = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
    for env_path in (root_env, backend_env):
        if env_path.exists():
            try:
                env_vals = dotenv_values(str(env_path))
                for provider in _PROVIDERS:
                    val = (
                        env_vals.get(PROVIDER_KEY_FIELDS[provider])
                        or env_vals.get(f"{provider.upper()}_API_KEY")
                        or env_vals.get(f"{provider.upper()}_API")
                        or env_vals.get(provider.upper())
                    )
                    if not val and provider == "grok":
                        val = env_vals.get("XAI_API_KEY")
                    if val:
                        keys[provider] = val
            except Exception as exc:
                logger.debug("Failed reading env file %s: %s", env_path, exc)

    # 3. Inspect os.environ directly
    for provider in _PROVIDERS:
        val = (
            os.environ.get(PROVIDER_KEY_FIELDS[provider])
            or os.environ.get(f"{provider.upper()}_API_KEY")
            or os.environ.get(f"{provider.upper()}_API")
            or os.environ.get(provider.upper())
        )
        if not val and provider == "grok":
            val = os.environ.get("XAI_API_KEY")
        if val:
            keys[provider] = val

    # 4. Overlay user keys file if configured
    env_file = getattr(settings, "USER_KEYS_ENV_FILE", None)
    if env_file:
        try:
            vals = dotenv_values(env_file)
            for provider in _PROVIDERS:
                v = (
                    vals.get(PROVIDER_KEY_FIELDS[provider])
                    or vals.get(f"{provider.upper()}_API_KEY")
                    or vals.get(f"{provider.upper()}_API")
                    or vals.get(provider.upper())
                )
                if not v and provider == "grok":
                    v = vals.get("XAI_API_KEY")
                if v:
                    keys[provider] = v
        except Exception as exc:
            logger.warning("Failed to load USER_KEYS_ENV_FILE (%s): %s", env_file, exc)

    _ENV_KEYS_CACHE = keys
    _CACHE_TIMESTAMP = time.time()
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
    prefs._ai_fallback_order = _parse_fallback_order(
        getattr(prefs, "ai_fallback_order", None)
    )
    return out


def resolve_provider_key(provider: str, db=None, user_id=None) -> Optional[str]:
    """Return the active API key for a specific provider (User UI key first, then env)."""
    p = (provider or "").lower().strip()
    if not p:
        return None

    # Check user database first
    if db is not None and user_id:
        user_keys = get_user_stored_keys(db, user_id)
        if user_keys.get(p):
            return user_keys[p]

    # Fall back to server/environment keys
    env_keys = get_env_provider_keys()
    return env_keys.get(p)


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
      2. The user's preferred provider & model from Settings (UI key first, then env).
      3. Fallback providers (from user's ``fallback_order`` or default),
         each with its configured/default model.
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

    # If provider/model or fallback_order not explicitly passed, inspect user preferences
    if db is not None and user_id:
        from app.models.user import UserPreference

        try:
            uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
            prefs = (
                db.query(UserPreference).filter(UserPreference.user_id == uid).first()
            )
            if prefs:
                if not provider and prefs.ai_provider:
                    provider = prefs.ai_provider
                if not model and prefs.ai_model:
                    model = prefs.ai_model
                if not fallback_order and prefs.ai_fallback_order:
                    fallback_order = _parse_fallback_order(prefs.ai_fallback_order)
        except Exception as exc:
            logger.debug("Failed loading user preference in build_candidates: %s", exc)

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

    # 4. Fallback providers (Automatic substitution).
    order = fallback_order or DEFAULT_FALLBACK_ORDER
    for prov in order:
        prov = prov.lower()
        if provider and prov == provider:
            continue
        # Use chosen model if this provider happens to be the primary provider,
        # otherwise use default model for this provider
        cand_model = (
            model if (provider and prov == provider) else DEFAULT_MODELS.get(prov, "")
        )
        add(prov, cand_model, user_keys.get(prov))
        add(prov, cand_model, env_keys.get(prov))

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
    return {p: {"ui": p in user_keys, "env": p in env_keys} for p in _PROVIDERS}
