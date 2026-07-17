"""
Rate limiting for API endpoints.

Implemented as a FastAPI middleware that applies a fixed-window limit per
client. The counter lives in Redis when Redis is reachable (so limits are
enforced across all API replicas), and falls back to an in-process counter
when Redis is unavailable.

Limits are keyed by authenticated user when a bearer token is present,
otherwise by client IP. Rate limiting is disabled in the ``testing`` and
``development`` environments so local dev and the test suite are never
throttled.
"""

from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.security import decode_token

# ---------------------------------------------------------------------------
# In-memory fallback limiter (used when Redis is unreachable)
# ---------------------------------------------------------------------------


class RateLimiter:
    """Sliding-window token bucket kept in process memory."""

    def __init__(self):
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def _refill(self, key, max_tokens, refill_rate, now):
        if key not in self.buckets:
            return max_tokens, now
        tokens, last = self.buckets[key]
        tokens = min(max_tokens, tokens + (now - last) * refill_rate)
        return tokens, now

    def check(self, key, max_requests, window_seconds) -> Tuple[bool, Optional[int]]:
        now = time.time()
        refill_rate = max_requests / window_seconds
        tokens, _ = self._refill(key, max_requests, refill_rate, now)
        if tokens >= 1:
            self.buckets[key] = (tokens - 1, now)
            return True, None
        retry_after = int((1 - tokens) / refill_rate) + 1
        return False, retry_after

    def remaining(self, key, max_requests, window_seconds) -> int:
        now = time.time()
        refill_rate = max_requests / window_seconds
        tokens, _ = self._refill(key, max_requests, refill_rate, now)
        return int(tokens)


rate_limiter = RateLimiter()

# ---------------------------------------------------------------------------
# Limit configuration
# ---------------------------------------------------------------------------

# (max_requests, window_seconds)
RATE_LIMITS: Dict[str, Tuple[int, int]] = {
    "auth_login": (5, 300),
    "auth_register": (3, 3600),
    "auth_verify_email": (5, 300),
    "auth_forgot_password": (3, 3600),
    "auth_refresh": (10, 60),
    "api_read": (100, 60),
    "api_write": (30, 60),
    "api_import": (10, 60),
}


def get_client_ip(request: Request) -> str:
    """Best-effort client IP from proxy headers, falling back to peer."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


def _limit_type_for(path: str, method: str) -> Optional[str]:
    p = path.lower()
    if "/auth/login" in p:
        return "auth_login"
    if "/auth/register" in p:
        return "auth_register"
    if "/auth/verify" in p:
        return "auth_verify_email"
    if "/auth/forgot" in p:
        return "auth_forgot_password"
    if "/auth/refresh" in p:
        return "auth_refresh"
    if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
        return "api_write"
    return "api_read"


def _user_id_from_request(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            return decode_token(auth[7:]).get("sub")
        except Exception:
            return None
    return None


def check_rate_limit(
    request: Request,
    limit_type: str = "api_read",
    user_id: Optional[str] = None,
) -> None:
    """Enforce the limit for ``limit_type``. Raises 429 when exceeded.

    No-op in ``testing``/``development``. Uses Redis when available, else the
    in-memory fallback. On success it records header values on
    ``request.state`` for the response-header middleware to emit.
    """
    if limit_type not in RATE_LIMITS:
        raise ValueError(f"Unknown rate limit type: {limit_type}")

    if settings.ENVIRONMENT in ("testing", "test", "development"):
        return

    max_requests, window_seconds = RATE_LIMITS[limit_type]
    key_scope = f"user:{user_id}" if user_id else f"ip:{get_client_ip(request)}"
    redis_key = f"ratelimit:{limit_type}:{key_scope}"

    client = get_redis_client()
    if client is not None:
        try:
            count = client.incr(redis_key)
            if count == 1:
                client.expire(redis_key, window_seconds)
            ttl = client.ttl(redis_key)
            if ttl is None or ttl < 0:
                ttl = window_seconds
            if count > max_requests:
                retry_after = int(ttl) + 1
                _record_headers(request, max_requests, 0, int(time.time() + ttl))
                raise _too_many(retry_after)
            _record_headers(
                request,
                max_requests,
                max(0, max_requests - count),
                int(time.time() + ttl),
            )
            return
        except Exception as exc:
            if isinstance(exc, _RateLimitExceeded):
                raise
            # Redis hiccup mid-request: fall through to in-memory.
    # In-memory fallback
    allowed, retry_after = rate_limiter.check(redis_key, max_requests, window_seconds)
    if not allowed:
        _record_headers(request, max_requests, 0, int(time.time() + window_seconds))
        raise _too_many(retry_after or window_seconds)
    remaining = rate_limiter.remaining(redis_key, max_requests, window_seconds)
    _record_headers(request, max_requests, remaining, int(time.time() + window_seconds))


class _RateLimitExceeded(Exception):
    pass


def _too_many(retry_after: int) -> _RateLimitExceeded:
    return _RateLimitExceeded()


def _record_headers(request: Request, limit: int, remaining: int, reset: int) -> None:
    request.state.rate_limit_limit = limit
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting for ``/api/v1`` routes.

    Disabled outside production. Returns a 429 directly (with Retry-After and
    rate-limit headers) when the client is over budget.
    """

    def __init__(self, app, api_prefix: str = "/api/v1"):
        super().__init__(app)
        self.api_prefix = api_prefix

    async def dispatch(self, request: Request, call_next):
        if settings.ENVIRONMENT in ("testing", "test", "development"):
            return await call_next(request)
        if not request.url.path.startswith(self.api_prefix):
            return await call_next(request)

        limit_type = _limit_type_for(request.url.path, request.method)
        if limit_type is None:
            return await call_next(request)

        user_id = _user_id_from_request(request)
        try:
            check_rate_limit(request, limit_type, user_id)
        except _RateLimitExceeded:
            retry = getattr(request.state, "rate_limit_reset", None)
            reset = int(time.time() + (retry or 60)) if retry else 60
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={
                    "Retry-After": str(retry or 60),
                    "X-RateLimit-Limit": str(
                        getattr(request.state, "rate_limit_limit", "")
                    ),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                },
            )
        return await call_next(request)
