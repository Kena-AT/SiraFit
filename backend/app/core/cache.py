"""Redis-backed cache with an in-memory fallback.

The cache is a no-op in the ``testing`` environment so the test suite stays
fully deterministic (no cross-test staleness). In every other environment it
uses Redis when reachable, otherwise an in-process dict with TTLs.

Values are JSON-serialised, so only JSON-safe structures should be cached.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime

from app.core.config import settings
from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)

_MEMORY: dict[str, tuple[object, float]] = {}
# In-process singleflight locks, keyed by cache key.
# NOTE: these dedupe only within a single process/worker — see plan 3.2 caveat.
_flight: dict[str, asyncio.Lock] = {}


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
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            # Fall through to in-memory cache
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
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
    _MEMORY[key] = (value, time.time() + ttl)


def cache_delete(key: str) -> None:
    """Remove a single key from the cache."""
    if not _cache_enabled():
        return
    client = get_redis_client()
    if client is not None:
        try:
            client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
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
        except Exception as e:
            logger.warning(f"Cache delete_prefix failed for prefix {prefix}: {e}")
    for k in list(_MEMORY.keys()):
        if k.startswith(prefix):
            _MEMORY.pop(k, None)


async def cache_get_or_compute(
    key: str, ttl: int, func, *args, **kwargs
):
    """Return cached value for ``key``, or compute via ``func`` if absent.

    Deduplicates concurrent requests for the same key using an asyncio.Lock
    (singleflight pattern). Prevents thundering-herd DB hits on cold cache.

    Caveat: dedupes within a single process/worker only. With multiple
    Uvicorn/Gunicorn workers, cross-process hits may still occur — consider
    a Redis-based distributed lock if that becomes a concern at scale.
    """
    val = cache_get(key)
    if val is not None:
        return val

    lock = _flight.setdefault(key, asyncio.Lock())
    try:
        async with lock:
            # Double-check after acquiring the lock — another request may have
            # already computed and stored the value while we waited.
            val = cache_get(key)
            if val is not None:
                return val
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            cache_set(key, _to_json_safe(result), ttl)
            return result
    finally:
        # Cleanup: pop the lock if no one else is using it, to avoid unbounded
        # memory growth of the _flight dict under high key cardinality.
        if not lock.locked():
            _flight.pop(key, None)


def _to_json_safe(obj):
    """Convert Pydantic models/datetimes to JSON-serializable structures."""
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        pass
    # Pydantic v2 models
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    # Datetimes
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
