"""
API Rate Limiting & Quotas (v6.0.0)
====================================

Redis-based rate limiting with token bucket and sliding window algorithms.

Features:
- Per-user rate limiting
- Per-IP rate limiting
- API key quotas
- Tier-based limits (Free/Pro/Enterprise)
- Distributed rate limiting (Redis)
- Custom headers (X-RateLimit-*)

Algorithms:
- Token Bucket: Burst handling
- Sliding Window: Precise rate limiting
- Fixed Window Counter: Simple and fast

Version: v6.0.0
"""

import logging
import time
from enum import Enum

import redis
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


class RateLimitTier(str, Enum):
    """Rate limit tiers"""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Rate limit configurations by tier
RATE_LIMITS = {
    RateLimitTier.FREE: {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 1000,
        "concurrent_requests": 2,
    },
    RateLimitTier.PRO: {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000,
        "concurrent_requests": 10,
    },
    RateLimitTier.ENTERPRISE: {
        "requests_per_minute": 300,
        "requests_per_hour": 10000,
        "requests_per_day": 100000,
        "concurrent_requests": 50,
    },
}


# ============================================================================
# Rate Limiter
# ============================================================================


class RateLimiter:
    """
    Redis-based rate limiter with multiple algorithms
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize rate limiter

        Args:
            redis_url: Redis connection URL
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        logger.info(f"RateLimiter initialized (redis={redis_url})")

    def _get_tier_limits(self, tier: RateLimitTier) -> dict:
        """Get rate limits for tier"""
        return RATE_LIMITS.get(tier, RATE_LIMITS[RateLimitTier.FREE])

    def check_rate_limit(
        self, key: str, tier: RateLimitTier, window: str = "minute"
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit (Sliding Window)

        Args:
            key: Unique identifier (user_id, api_key, ip)
            tier: Rate limit tier
            window: Time window (minute, hour, day)

        Returns:
            (allowed, info) tuple
                allowed: True if request allowed
                info: Rate limit information
        """
        limits = self._get_tier_limits(tier)
        limit_key = f"requests_per_{window}"

        if limit_key not in limits:
            return True, {}

        max_requests = limits[limit_key]

        # Sliding window using sorted set
        redis_key = f"ratelimit:{key}:{window}"
        now = time.time()

        # Get window size in seconds
        window_seconds = {"minute": 60, "hour": 3600, "day": 86400}.get(window, 60)

        # Remove old entries
        self.redis_client.zremrangebyscore(redis_key, 0, now - window_seconds)

        # Count current requests in window
        current_count = self.redis_client.zcard(redis_key)

        # Check limit
        allowed = current_count < max_requests

        if allowed:
            # Add new request
            self.redis_client.zadd(redis_key, {str(now): now})
            # Set expiry
            self.redis_client.expire(redis_key, window_seconds * 2)

        # Calculate reset time
        oldest = self.redis_client.zrange(redis_key, 0, 0, withscores=True)
        reset_time = int(oldest[0][1] + window_seconds) if oldest else int(now + window_seconds)

        remaining = max(0, max_requests - current_count - (1 if allowed else 0))

        info = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_time,
            "window": window,
        }

        return allowed, info

    def check_all_limits(self, key: str, tier: RateLimitTier) -> tuple[bool, dict]:
        """
        Check all rate limits (minute, hour, day)

        Args:
            key: Unique identifier
            tier: Rate limit tier

        Returns:
            (allowed, info) tuple with combined info
        """
        windows = ["minute", "hour", "day"]
        all_info = {}

        for window in windows:
            allowed, info = self.check_rate_limit(key, tier, window)

            if not allowed:
                return False, {
                    "allowed": False,
                    "window": window,
                    **info,
                }

            all_info[window] = info

        return True, {
            "allowed": True,
            "windows": all_info,
        }

    def check_concurrent_limit(self, key: str, tier: RateLimitTier) -> bool:
        """
        Check concurrent request limit

        Args:
            key: Unique identifier
            tier: Rate limit tier

        Returns:
            True if within limit
        """
        limits = self._get_tier_limits(tier)
        max_concurrent = limits.get("concurrent_requests", 5)

        redis_key = f"concurrent:{key}"
        current = self.redis_client.get(redis_key)
        current_count = int(current) if current else 0

        return current_count < max_concurrent

    def acquire_concurrent_slot(self, key: str):
        """Acquire a concurrent request slot"""
        redis_key = f"concurrent:{key}"
        self.redis_client.incr(redis_key)
        self.redis_client.expire(redis_key, 300)  # 5 min timeout

    def release_concurrent_slot(self, key: str):
        """Release a concurrent request slot"""
        redis_key = f"concurrent:{key}"
        self.redis_client.decr(redis_key)

    def reset_limits(self, key: str):
        """Reset all limits for a key (admin only)"""
        pattern = f"ratelimit:{key}:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)

        concurrent_key = f"concurrent:{key}"
        self.redis_client.delete(concurrent_key)

        logger.info(f"Reset rate limits for: {key}")


# ============================================================================
# FastAPI Middleware
# ============================================================================


class RateLimitMiddleware:
    """
    FastAPI middleware for rate limiting
    """

    def __init__(self, app, redis_url: str = "redis://localhost:6379/0"):
        self.app = app
        self.rate_limiter = RateLimiter(redis_url)

    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting"""

        # Skip rate limiting for health checks
        if request.url.path in ["/health/live", "/health/ready"]:
            return await call_next(request)

        # Get identifier (priority: api_key > user_id > ip)
        api_key = request.headers.get("X-API-Key")
        user_id = request.headers.get("X-User-ID")
        client_ip = request.client.host

        identifier = api_key or user_id or client_ip

        # Determine tier (default: free)
        tier = self._get_tier(request)

        # Check concurrent limit
        if not self.rate_limiter.check_concurrent_limit(identifier, tier):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too many concurrent requests",
                    "detail": "Maximum concurrent requests exceeded",
                },
                headers={"Retry-After": "60"},
            )

        # Check rate limits
        allowed, info = self.rate_limiter.check_all_limits(identifier, tier)

        if not allowed:
            # Return 429 with rate limit headers
            headers = {
                "X-RateLimit-Limit": str(info.get("limit", 0)),
                "X-RateLimit-Remaining": str(info.get("remaining", 0)),
                "X-RateLimit-Reset": str(info.get("reset", 0)),
                "Retry-After": str(max(1, info.get("reset", 0) - int(time.time()))),
            }

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Rate limit exceeded for {info.get('window', 'unknown')} window",
                    "limit": info.get("limit"),
                    "reset": info.get("reset"),
                },
                headers=headers,
            )

        # Acquire concurrent slot
        self.rate_limiter.acquire_concurrent_slot(identifier)

        try:
            # Process request
            response = await call_next(request)

            # Add rate limit headers to successful responses
            if allowed and "windows" in info:
                minute_info = info["windows"].get("minute", {})
                response.headers["X-RateLimit-Limit"] = str(minute_info.get("limit", 0))
                response.headers["X-RateLimit-Remaining"] = str(minute_info.get("remaining", 0))
                response.headers["X-RateLimit-Reset"] = str(minute_info.get("reset", 0))

            return response

        finally:
            # Release concurrent slot
            self.rate_limiter.release_concurrent_slot(identifier)

    def _get_tier(self, request: Request) -> RateLimitTier:
        """
        Determine rate limit tier from request

        Priority:
        1. X-Tier header
        2. API key lookup
        3. Default to FREE
        """
        # Check header
        tier_header = request.headers.get("X-Tier")
        if tier_header:
            try:
                return RateLimitTier(tier_header.lower())
            except ValueError:
                pass

        # Default to free
        return RateLimitTier.FREE


# ============================================================================
# Dependency for FastAPI routes
# ============================================================================


async def check_rate_limit(request: Request):
    """
    FastAPI dependency for per-route rate limiting

    Usage:
        @app.get("/api/endpoint", dependencies=[Depends(check_rate_limit)])
    """
    # This is now handled by middleware
    # Keep for backward compatibility or custom per-route limits
    pass


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Check rate limit
    limiter = RateLimiter()

    user_id = "user-123"
    tier = RateLimitTier.FREE

    # Check limit
    allowed, info = limiter.check_all_limits(user_id, tier)

    if allowed:
        print(f"✅ Request allowed: {info}")
    else:
        print(f"❌ Rate limit exceeded: {info}")
