"""Redis-backed cache with an in-memory fallback.

The cache is a no-op in the ``testing`` environment so the test suite stays
fully deterministic (no cross-test staleness). In every other environment it
uses Redis when reachable, otherwise an in-process dict with TTLs.

Values are JSON-serialised, so only JSON-safe structures should be cached.
"""

from __future__ import annotations

import json
import time

from app.core.config import settings
from app.core.redis_client import get_redis_client

_MEMORY: dict[str, tuple[object, float]] = {}


def _cache_enabled() -> bool:
    # Keep the test suite deterministic: never serve or store cached values.
    return settings.ENVIRONMENT not in ("testing", "test")


def cache_get(key: str):
    """Return the cached value for ``key`` or ``None`` on miss/disabled."""
    if not _cache_enabled():
        return None
    client = get_redis_client()
    if client is not None:
        try:
            raw = client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            pass
    entry = _MEMORY.get(key)
    if entry and entry[1] > time.time():
        return entry[0]
    if entry:
        _MEMORY.pop(key, None)
    return None


def cache_set(key: str, value, ttl: int = 60) -> None:
    """Store ``value`` under ``key`` for ``ttl`` seconds."""
    if not _cache_enabled():
        return
    data = json.dumps(value)
    client = get_redis_client()
    if client is not None:
        try:
            client.set(key, data, ex=ttl)
            return
        except Exception:
            pass
    _MEMORY[key] = (value, time.time() + ttl)


def cache_delete(key: str) -> None:
    """Remove a single key from the cache."""
    if not _cache_enabled():
        return
    client = get_redis_client()
    if client is not None:
        try:
            client.delete(key)
        except Exception:
            pass
    _MEMORY.pop(key, None)


def cache_delete_prefix(prefix: str) -> None:
    """Remove every key beginning with ``prefix``."""
    if not _cache_enabled():
        return
    client = get_redis_client()
    if client is not None:
        try:
            for k in client.scan_iter(match=f"{prefix}*"):
                client.delete(k)
        except Exception:
            pass
    for k in list(_MEMORY.keys()):
        if k.startswith(prefix):
            _MEMORY.pop(k, None)
