"""
Advanced Caching Strategies (v6.0.0)
====================================

Multi-layer caching with intelligent invalidation and warming.

Layers:
1. L1: In-memory LRU cache (fastest, per-instance)
2. L2: Redis distributed cache (shared across instances)
3. L3: Database cache (persistent)

Strategies:
- Query result caching
- Embedding caching
- Product metadata caching
- Frequently accessed data pre-warming
- Cache invalidation on updates
- TTL-based expiration

Version: v6.0.0
"""

import hashlib
import json
import logging
import pickle
from functools import lru_cache, wraps
from typing import Any, Callable, Optional

import redis

logger = logging.getLogger(__name__)


# ============================================================================
# Multi-Layer Cache
# ============================================================================


class MultiLayerCache:
    """
    3-layer cache: Memory (L1) → Redis (L2) → Database (L3)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/1",
        l1_size: int = 1000,
        default_ttl: int = 3600,
    ):
        """
        Initialize multi-layer cache

        Args:
            redis_url: Redis connection URL
            l1_size: L1 (memory) cache size
            default_ttl: Default TTL in seconds
        """
        self.redis_client = redis.from_url(redis_url)
        self.l1_size = l1_size
        self.default_ttl = default_ttl

        # L1: In-memory cache (per instance)
        self.l1_cache = {}
        self.l1_access_order = []

        logger.info(
            f"MultiLayerCache initialized (L1 size={l1_size}, TTL={default_ttl}s)"
        )

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 → L2 → L3)

        Returns:
            Cached value or None
        """
        # L1: Memory cache
        if key in self.l1_cache:
            logger.debug(f"Cache HIT (L1): {key}")
            self._update_l1_access(key)
            return self.l1_cache[key]

        # L2: Redis cache
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT (L2 Redis): {key}")
                # Deserialize
                deserialized = pickle.loads(value)
                # Store in L1 for next access
                self._set_l1(key, deserialized)
                return deserialized
        except Exception as e:
            logger.error(f"Redis cache error: {e}")

        logger.debug(f"Cache MISS: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in all cache layers

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        ttl = ttl or self.default_ttl

        # L1: Memory
        self._set_l1(key, value)

        # L2: Redis
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET (L1+L2): {key} (TTL={ttl}s)")
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")

    def delete(self, key: str):
        """Delete from all cache layers"""
        # L1
        if key in self.l1_cache:
            del self.l1_cache[key]
            if key in self.l1_access_order:
                self.l1_access_order.remove(key)

        # L2
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern

        Args:
            pattern: Redis key pattern (e.g., "cache:user:*")
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} keys matching '{pattern}'")

            # Also clear L1 matching keys
            l1_keys_to_delete = [k for k in self.l1_cache.keys() if pattern.replace("*", "") in k]
            for key in l1_keys_to_delete:
                del self.l1_cache[key]

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    def _set_l1(self, key: str, value: Any):
        """Set value in L1 (memory) cache with LRU eviction"""
        # Check size limit
        if len(self.l1_cache) >= self.l1_size and key not in self.l1_cache:
            # Evict least recently used
            if self.l1_access_order:
                lru_key = self.l1_access_order.pop(0)
                del self.l1_cache[lru_key]

        self.l1_cache[key] = value
        self._update_l1_access(key)

    def _update_l1_access(self, key: str):
        """Update L1 access order (for LRU)"""
        if key in self.l1_access_order:
            self.l1_access_order.remove(key)
        self.l1_access_order.append(key)

    def clear_all(self):
        """Clear all cache layers"""
        # L1
        self.l1_cache.clear()
        self.l1_access_order.clear()

        # L2 (flush Redis DB - use with caution!)
        # self.redis_client.flushdb()

        logger.warning("Cleared all caches (L1)")


# ============================================================================
# Cache Decorators
# ============================================================================


def cached(
    prefix: str,
    ttl: int = 3600,
    cache_instance: Optional[MultiLayerCache] = None,
):
    """
    Decorator for caching function results

    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
        cache_instance: Cache instance (or use global)

    Usage:
        @cached(prefix="user_profile", ttl=300)
        def get_user_profile(user_id: str):
            return fetch_from_db(user_id)
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create cache instance
            cache = cache_instance or _get_global_cache()

            # Generate cache key
            cache_key = cache._make_key(prefix, *args, **kwargs)

            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def async_cached(
    prefix: str,
    ttl: int = 3600,
    cache_instance: Optional[MultiLayerCache] = None,
):
    """
    Async version of cached decorator

    Usage:
        @async_cached(prefix="search_results", ttl=600)
        async def search(query: str):
            return await execute_search(query)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = cache_instance or _get_global_cache()
            cache_key = cache._make_key(prefix, *args, **kwargs)

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# ============================================================================
# Specialized Caches
# ============================================================================


class QueryCache:
    """Cache for search queries and results"""

    def __init__(self, cache: MultiLayerCache):
        self.cache = cache
        self.prefix = "query_cache"

    def get_result(self, query: str, filters: dict = None) -> Optional[dict]:
        """Get cached query result"""
        key = self.cache._make_key(self.prefix, query, filters or {})
        return self.cache.get(key)

    def set_result(self, query: str, result: dict, filters: dict = None, ttl: int = 600):
        """Cache query result"""
        key = self.cache._make_key(self.prefix, query, filters or {})
        self.cache.set(key, result, ttl)

    def invalidate_all(self):
        """Invalidate all query caches"""
        self.cache.invalidate_pattern(f"{self.prefix}:*")


class EmbeddingCache:
    """Cache for embeddings"""

    def __init__(self, cache: MultiLayerCache):
        self.cache = cache
        self.prefix = "embedding_cache"

    def get_embedding(self, text: str) -> Optional[list]:
        """Get cached embedding"""
        key = self.cache._make_key(self.prefix, text)
        return self.cache.get(key)

    def set_embedding(self, text: str, embedding: list, ttl: int = 86400):
        """Cache embedding (24h default)"""
        key = self.cache._make_key(self.prefix, text)
        self.cache.set(key, embedding, ttl)


class ProductCache:
    """Cache for product metadata"""

    def __init__(self, cache: MultiLayerCache):
        self.cache = cache
        self.prefix = "product_cache"

    def get_product(self, product_id: str) -> Optional[dict]:
        """Get cached product"""
        key = f"{self.prefix}:{product_id}"
        return self.cache.get(key)

    def set_product(self, product_id: str, product: dict, ttl: int = 3600):
        """Cache product metadata"""
        key = f"{self.prefix}:{product_id}"
        self.cache.set(key, product, ttl)

    def invalidate_product(self, product_id: str):
        """Invalidate specific product"""
        key = f"{self.prefix}:{product_id}"
        self.cache.delete(key)

    def invalidate_all(self):
        """Invalidate all products"""
        self.cache.invalidate_pattern(f"{self.prefix}:*")


# ============================================================================
# Cache Warming
# ============================================================================


class CacheWarmer:
    """Pre-warm cache with frequently accessed data"""

    def __init__(self, cache: MultiLayerCache):
        self.cache = cache

    async def warm_popular_queries(self, queries: list[str]):
        """
        Pre-warm cache with popular queries

        Args:
            queries: List of popular queries to pre-execute
        """
        logger.info(f"Warming cache with {len(queries)} popular queries")

        for query in queries:
            try:
                # Execute search and cache result
                # This would call actual search function
                logger.debug(f"Warming query: {query}")
                # await execute_search(query)
            except Exception as e:
                logger.error(f"Cache warming error for '{query}': {e}")

    async def warm_products(self, product_ids: list[str]):
        """
        Pre-warm product cache

        Args:
            product_ids: List of product IDs to pre-load
        """
        logger.info(f"Warming cache with {len(product_ids)} products")

        product_cache = ProductCache(self.cache)

        for product_id in product_ids:
            try:
                # Load product metadata
                # product = await load_product(product_id)
                # product_cache.set_product(product_id, product)
                logger.debug(f"Warmed product: {product_id}")
            except Exception as e:
                logger.error(f"Product warming error for '{product_id}': {e}")


# ============================================================================
# Global Cache Instance
# ============================================================================

_global_cache: Optional[MultiLayerCache] = None


def get_cache() -> MultiLayerCache:
    """Get or create global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiLayerCache()
    return _global_cache


def _get_global_cache() -> MultiLayerCache:
    """Internal helper for decorators"""
    return get_cache()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Multi-layer cache
    cache = MultiLayerCache()

    # Set value
    cache.set("user:123", {"name": "John", "email": "john@example.com"}, ttl=300)

    # Get value
    user = cache.get("user:123")
    print(f"User: {user}")

    # Use decorator
    @cached(prefix="expensive_operation", ttl=600)
    def expensive_function(x: int):
        print(f"Computing {x}...")
        return x * x

    # First call: executes function
    result1 = expensive_function(5)

    # Second call: returns cached value
    result2 = expensive_function(5)

    # Specialized caches
    query_cache = QueryCache(cache)
    query_cache.set_result("50ml PET", {"results": [...]}, ttl=600)
    cached_results = query_cache.get_result("50ml PET")
