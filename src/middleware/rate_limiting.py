"""
Rate Limiting Middleware
Automatic rate limiting for all API endpoints
Version: v8.5.0
"""

import logging
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import time

from src.services.rate_limiter_service import (
    get_rate_limiter,
    RateLimitTier,
    RateLimitAlgorithm
)

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""

    def __init__(
        self,
        app,
        default_tier: RateLimitTier = RateLimitTier.FREE,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        identifier_strategy: str = "ip",  # ip, user_id, api_key
        excluded_paths: Optional[list] = None
    ):
        """
        Initialize rate limiting middleware

        Args:
            app: FastAPI application
            default_tier: Default rate limit tier
            algorithm: Rate limiting algorithm
            identifier_strategy: How to identify users (ip, user_id, api_key)
            excluded_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.default_tier = default_tier
        self.algorithm = algorithm
        self.identifier_strategy = identifier_strategy
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]

        logger.info(f"Rate limiting middleware initialized: {algorithm}, tier={default_tier}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""

        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Get identifier
        identifier = await self._get_identifier(request)

        # Determine tier (can be customized based on user role, API key, etc.)
        tier = await self._get_tier(request)

        # Check rate limit
        rate_limiter = get_rate_limiter()

        try:
            allowed, metadata = await rate_limiter.check_rate_limit(
                identifier=identifier,
                tier=tier,
                algorithm=self.algorithm
            )

            # Add rate limit headers
            headers = {
                "X-RateLimit-Limit": str(metadata.get('limit', 0)),
                "X-RateLimit-Remaining": str(metadata.get('remaining', 0)),
                "X-RateLimit-Reset": str(metadata.get('reset_time', 0)),
            }

            if not allowed:
                # Rate limit exceeded
                retry_after = metadata.get('retry_after', 60)

                logger.warning(
                    f"Rate limit exceeded for {identifier}: "
                    f"{metadata.get('current', 0)}/{metadata.get('limit', 0)}"
                )

                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": retry_after,
                        "limit": metadata.get('limit', 0),
                        "current": metadata.get('current', 0)
                    },
                    headers={
                        **headers,
                        "Retry-After": str(retry_after)
                    }
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            for key, value in headers.items():
                response.headers[key] = value

            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request on error
            return await call_next(request)

    async def _get_identifier(self, request: Request) -> str:
        """Get user identifier for rate limiting"""

        if self.identifier_strategy == "ip":
            # Use IP address
            if request.client:
                return request.client.host
            else:
                return "unknown"

        elif self.identifier_strategy == "user_id":
            # Use authenticated user ID
            user = getattr(request.state, "user", None)
            if user:
                return f"user:{user.id}"
            else:
                # Fall back to IP
                if request.client:
                    return f"ip:{request.client.host}"
                else:
                    return "unknown"

        elif self.identifier_strategy == "api_key":
            # Use API key from header
            api_key = request.headers.get("X-API-Key")
            if api_key:
                return f"api_key:{api_key}"
            else:
                # Fall back to IP
                if request.client:
                    return f"ip:{request.client.host}"
                else:
                    return "unknown"

        else:
            # Default to IP
            if request.client:
                return request.client.host
            else:
                return "unknown"

    async def _get_tier(self, request: Request) -> RateLimitTier:
        """Determine rate limit tier for request"""

        # Check for user role
        user = getattr(request.state, "user", None)

        if user:
            role = getattr(user, "role", None)

            # Map user roles to tiers
            if role == "admin":
                return RateLimitTier.ENTERPRISE
            elif role == "manager":
                return RateLimitTier.PREMIUM
            elif role == "worker":
                return RateLimitTier.BASIC
            else:
                return RateLimitTier.FREE

        # Check for API key tier
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # TODO: Look up API key tier in database
            # For now, return BASIC for any API key
            return RateLimitTier.BASIC

        # Default tier for anonymous users
        return self.default_tier


class RateLimitDecorator:
    """Decorator for custom rate limiting on specific endpoints"""

    def __init__(
        self,
        tier: RateLimitTier = RateLimitTier.FREE,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        custom_limit: Optional[int] = None
    ):
        """
        Initialize rate limit decorator

        Args:
            tier: Rate limit tier
            algorithm: Rate limiting algorithm
            custom_limit: Optional custom limit override
        """
        self.tier = tier
        self.algorithm = algorithm
        self.custom_limit = custom_limit

    async def __call__(self, request: Request):
        """Check rate limit"""
        rate_limiter = get_rate_limiter()

        # Get identifier from request
        identifier = request.client.host if request.client else "unknown"

        allowed, metadata = await rate_limiter.check_rate_limit(
            identifier=identifier,
            tier=self.tier,
            algorithm=self.algorithm,
            custom_limit=self.custom_limit
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Rate limit exceeded",
                    "retry_after": metadata.get('retry_after', 60),
                    "limit": metadata.get('limit', 0),
                    "current": metadata.get('current', 0)
                },
                headers={
                    "Retry-After": str(metadata.get('retry_after', 60))
                }
            )

        return metadata


# Convenience function for adding rate limit dependency to routes
def rate_limit(
    tier: RateLimitTier = RateLimitTier.FREE,
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
    custom_limit: Optional[int] = None
):
    """
    Rate limit dependency for FastAPI routes

    Usage:
        @router.get("/endpoint", dependencies=[Depends(rate_limit(tier=RateLimitTier.PREMIUM))])
        async def my_endpoint():
            pass
    """
    return RateLimitDecorator(tier, algorithm, custom_limit)
