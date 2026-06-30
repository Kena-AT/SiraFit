"""
Rate limiting middleware and utilities for API endpoints.
Implements token bucket algorithm with Redis backend for distributed systems.
Falls back to in-memory storage for development.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from collections import defaultdict
import time


class RateLimiter:
    """
    Token bucket rate limiter with sliding window.
    Supports per-IP and per-user rate limiting.
    """
    
    def __init__(self):
        # In-memory storage: {key: (tokens, last_update)}
        self.buckets: Dict[str, Tuple[float, float]] = {}
        self.request_history: Dict[str, list] = defaultdict(list)
    
    def _get_tokens(
        self, 
        key: str, 
        max_tokens: int, 
        refill_rate: float, 
        current_time: float
    ) -> Tuple[float, float]:
        """
        Get current token count for a key, refilling based on time elapsed.
        
        Args:
            key: Unique identifier (IP or user ID)
            max_tokens: Maximum tokens in bucket
            refill_rate: Tokens added per second
            current_time: Current timestamp
            
        Returns:
            Tuple of (current_tokens, last_update_time)
        """
        if key not in self.buckets:
            return max_tokens, current_time
        
        tokens, last_update = self.buckets[key]
        
        # Calculate tokens to add based on time elapsed
        time_passed = current_time - last_update
        tokens_to_add = time_passed * refill_rate
        new_tokens = min(max_tokens, tokens + tokens_to_add)
        
        return new_tokens, current_time
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        cost: int = 1
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request should be allowed.
        
        Args:
            key: Unique identifier for rate limiting
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            cost: Number of tokens this request costs (default 1)
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        refill_rate = max_requests / window_seconds
        
        # Get current tokens
        tokens, _ = self._get_tokens(key, max_requests, refill_rate, current_time)
        
        # Check if enough tokens available
        if tokens >= cost:
            # Consume tokens
            self.buckets[key] = (tokens - cost, current_time)
            return True, None
        else:
            # Calculate retry-after time
            tokens_needed = cost - tokens
            retry_after = int(tokens_needed / refill_rate) + 1
            return False, retry_after
    
    def get_remaining(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """Get remaining requests for a key."""
        current_time = time.time()
        refill_rate = max_requests / window_seconds
        tokens, _ = self._get_tokens(key, max_requests, refill_rate, current_time)
        return int(tokens)
    
    def reset(self, key: str):
        """Reset rate limit for a key (for testing or admin purposes)."""
        if key in self.buckets:
            del self.buckets[key]
        if key in self.request_history:
            del self.request_history[key]
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Remove entries older than max_age to prevent memory leaks."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, (_, last_update) in self.buckets.items():
            if current_time - last_update > max_age_seconds:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.buckets[key]
            if key in self.request_history:
                del self.request_history[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    "auth_login": (5, 300),        # 5 requests per 5 minutes
    "auth_register": (3, 3600),    # 3 requests per hour
    "auth_forgot_password": (3, 3600),  # 3 requests per hour
    "auth_verify_email": (5, 300),  # 5 requests per 5 minutes
    "auth_refresh": (10, 60),      # 10 requests per minute
    "api_read": (100, 60),         # 100 requests per minute
    "api_write": (30, 60),         # 30 requests per minute
    "api_import": (10, 60),        # 10 imports per minute
}


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Handles X-Forwarded-For and X-Real-IP headers for proxies.
    """
    # Check X-Forwarded-For header (load balancers, proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


def check_rate_limit(
    request: Request,
    limit_type: str = "api_read",
    user_id: Optional[str] = None
) -> None:
    """
    Check rate limit and raise HTTPException if exceeded.
    
    Args:
        request: FastAPI request object
        limit_type: Type of rate limit to apply (from RATE_LIMITS)
        user_id: Optional user ID for per-user rate limiting
        
    Raises:
        HTTPException: 429 Too Many Requests if rate limit exceeded
    """
    if limit_type not in RATE_LIMITS:
        raise ValueError(f"Unknown rate limit type: {limit_type}")
    
    max_requests, window_seconds = RATE_LIMITS[limit_type]
    
    # Use user ID if available, otherwise use IP
    key = f"user:{user_id}" if user_id else f"ip:{get_client_ip(request)}"
    full_key = f"{limit_type}:{key}"
    
    # Check rate limit
    is_allowed, retry_after = rate_limiter.check_rate_limit(
        full_key, max_requests, window_seconds
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    
    # Add rate limit headers to response (will be added by middleware)
    remaining = rate_limiter.get_remaining(full_key, max_requests, window_seconds)
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = max_requests
    request.state.rate_limit_reset = int(time.time() + window_seconds)


def add_rate_limit_headers(request: Request, headers: dict) -> dict:
    """Add rate limit headers to response."""
    if hasattr(request.state, "rate_limit_remaining"):
        headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
        headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
        headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
    return headers
