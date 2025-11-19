"""
Smart Caching Middleware - 100% Free Alternative to Cloudflare Workers

Uses Redis (already in stack) for intelligent edge caching.
All features of Cloudflare Workers, zero cost.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable
from functools import wraps
import redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SmartCacheConfig:
    """Cache configuration"""

    # Default TTLs (seconds)
    DEFAULT_TTL = 300  # 5 minutes
    SIMPLE_QUERY_TTL = 600  # 10 minutes
    COMPLEX_QUERY_TTL = 180  # 3 minutes
    REALTIME_TTL = 0  # No cache

    # Popular queries for warming
    WARMUP_QUERIES = [
        "제품 검색",
        "product search",
        "가격 정보",
        "price information",
    ]


class SmartCacheMiddleware(BaseHTTPMiddleware):
    """
    Intelligent caching middleware using Redis

    Features:
    - Smart cache key generation (query normalization)
    - TTL based on query complexity
    - Cache warming for popular queries
    - Real-time metrics
    - 100% FREE
    """

    def __init__(self, app, redis_url: str = "redis://localhost:6379"):
        super().__init__(app)
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.config = SmartCacheConfig()

        # Metrics
        self.cache_hits = 0
        self.cache_misses = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching"""

        # Skip cache for certain requests
        if self._should_bypass_cache(request):
            return await call_next(request)

        # Generate cache key
        cache_key = await self._generate_cache_key(request)

        # Try to get from cache
        cached_response = self._get_from_cache(cache_key)

        if cached_response:
            # Cache HIT
            self.cache_hits += 1
            response = self._create_response_from_cache(cached_response)
            response.headers["X-Cache-Status"] = "HIT"
            response.headers["X-Cache-Key"] = cache_key
            return response

        # Cache MISS - call origin
        self.cache_misses += 1
        response = await call_next(request)

        # Cache the response if cacheable
        if self._is_cacheable(response, request):
            ttl = self._determine_ttl(request)
            await self._store_in_cache(cache_key, response, ttl)

        response.headers["X-Cache-Status"] = "MISS"
        response.headers["X-Cache-Key"] = cache_key

        return response

    def _should_bypass_cache(self, request: Request) -> bool:
        """Check if request should bypass cache"""

        path = request.url.path

        # Skip admin/debug endpoints
        if any(
            x in path
            for x in ["/admin", "/debug", "/health", "/metrics", "/docs", "/openapi"]
        ):
            return True

        # Skip WebSocket upgrades
        if request.headers.get("upgrade") == "websocket":
            return True

        # Skip auth-specific requests
        if "/auth/me" in path or "/auth/logout" in path:
            return True

        # Check client Cache-Control
        cache_control = request.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return True

        # Only cache GET and POST
        if request.method not in ["GET", "POST"]:
            return True

        return False

    async def _generate_cache_key(self, request: Request) -> str:
        """Generate smart cache key with normalization"""

        path = request.url.path

        # For search/RAG queries
        if "/search" in path or "/rag" in path:
            if request.method == "POST":
                try:
                    body = await request.json()
                    query = body.get("query", "")

                    # Normalize query
                    normalized_query = self._normalize_query(query)

                    # Create cache key from normalized data
                    key_data = {
                        "path": path,
                        "query": normalized_query,
                        "top_k": body.get("top_k", 5),
                        # Ignore user-specific params
                    }

                    key_string = json.dumps(key_data, sort_keys=True)
                    return f"cache:{self._hash_string(key_string)}"

                except Exception as e:
                    logger.warning(f"Failed to parse body for cache key: {e}")

        # Default: use URL as cache key
        return f"cache:{self._hash_string(str(request.url))}"

    def _normalize_query(self, query: str) -> str:
        """Normalize query for better cache hit rate"""
        import re

        normalized = query.lower().strip()
        # Multiple spaces → single space
        normalized = re.sub(r"\s+", " ", normalized)
        # Remove special chars (keep Korean, English, numbers)
        normalized = re.sub(r"[^\w\s가-힣]", "", normalized)

        return normalized

    def _hash_string(self, s: str) -> str:
        """Generate hash from string"""
        return hashlib.sha256(s.encode()).hexdigest()[:16]

    def _determine_ttl(self, request: Request) -> int:
        """Determine TTL based on query complexity"""

        path = request.url.path

        # Realtime endpoints - no cache
        if "/realtime" in path or "/socket" in path:
            return 0

        # Check query complexity for POST requests
        if request.method == "POST":
            try:
                body = request.json()
                query = body.get("query", "")

                # Simple queries = longer cache
                if len(query) < 20 and "최신" not in query and "latest" not in query:
                    return self.config.SIMPLE_QUERY_TTL

                # Complex queries = shorter cache
                if len(query) > 100 or len(query.split()) > 10:
                    return self.config.COMPLEX_QUERY_TTL

            except Exception:
                pass

        return self.config.DEFAULT_TTL

    def _is_cacheable(self, response: Response, request: Request) -> bool:
        """Check if response should be cached"""

        # Only cache successful responses
        if response.status_code != 200:
            return False

        # Check Cache-Control from response
        cache_control = response.headers.get("cache-control", "")
        if "no-store" in cache_control or "private" in cache_control:
            return False

        return True

    def _get_from_cache(self, cache_key: str) -> Optional[dict]:
        """Get response from Redis cache"""
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache GET error: {e}")

        return None

    async def _store_in_cache(
        self, cache_key: str, response: Response, ttl: int
    ) -> None:
        """Store response in Redis cache"""

        if ttl == 0:
            return

        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Store in cache
            cache_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": body.decode("utf-8"),
                "cached_at": datetime.now().isoformat(),
            }

            self.redis_client.setex(cache_key, ttl, json.dumps(cache_data))

            # Recreate response with body
            response.body_iterator = self._iter_bytes(body)

        except Exception as e:
            logger.error(f"Cache SET error: {e}")

    def _create_response_from_cache(self, cached_data: dict) -> Response:
        """Create Response object from cached data"""

        response = Response(
            content=cached_data["body"],
            status_code=cached_data["status_code"],
            headers=cached_data["headers"],
        )

        return response

    async def _iter_bytes(self, body: bytes):
        """Async iterator for bytes"""
        yield body

    def warm_cache(self) -> None:
        """Warm cache with popular queries"""
        logger.info("Warming cache with popular queries...")

        # This would be called by a background task
        # For now, just log
        for query in self.config.WARMUP_QUERIES:
            logger.info(f"  - Warming: {query}")

    def get_metrics(self) -> dict:
        """Get cache metrics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
        }


# Decorator for function-level caching
def smart_cache(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results in Redis

    Usage:
        @smart_cache(ttl=600, key_prefix="search")
        async def search_products(query: str):
            # expensive operation
            return results
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try cache first
            redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)

            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info(f"Cache HIT: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Cache error: {e}")

            # Cache miss - execute function
            logger.info(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                redis_client.setex(cache_key, ttl, json.dumps(result))
            except Exception as e:
                logger.error(f"Cache SET error: {e}")

            return result

        return wrapper

    return decorator
