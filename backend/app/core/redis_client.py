"""Lazy Redis client with availability detection.

A single shared client is created on first use and pinged to confirm
reachability. If Redis is unreachable (local dev, CI, tests), callers fall
back to in-memory behaviour. The result is memoised so we only probe once per
process.
"""

from __future__ import annotations

from app.core.config import settings

_client = None
_available: bool | None = None


def get_redis_client():
    """Return a connected Redis client, or ``None`` if Redis is unavailable."""
    global _client, _available
    if _available is not None:
        return _client if _available else None
    try:
        import redis

        client = redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        client.ping()
        _client = client
        _available = True
    except Exception:
        _client = None
        _available = False
    return _client


def redis_available() -> bool:
    return get_redis_client() is not None


def reset_redis_cache() -> None:
    """Forget the memoised client (used by tests that toggle Redis)."""
    global _client, _available
    _client = None
    _available = None
