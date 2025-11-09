"""
Cache Manager
Redis 기반 다층 캐싱 시스템

목적: 쿼리 응답 속도 향상 (5초 → <500ms)
전략:
- Layer 1: Exact Match Cache (TTL: 1시간)
- Layer 2: Semantic Cache (TTL: 30분, similarity >0.95)
- Layer 3: Search Result Cache (TTL: 10분)
"""

import hashlib
import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

import redis

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis 기반 캐시 관리자

    Features:
    - 3-layer caching (Exact, Semantic, Result)
    - TTL 관리
    - Cache statistics
    - Automatic eviction (LRU)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
    ):
        """
        Initialize Cache Manager

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
            decode_responses: Decode responses to str
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                socket_connect_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
            self.connected = True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            logger.warning("Cache will be disabled (in-memory fallback)")
            self.redis_client = None
            self.connected = False

            # In-memory fallback (dict)
            self._memory_cache: Dict[str, Any] = {}

    # =========================================================================
    # Layer 1: Exact Match Cache
    # =========================================================================

    def get_exact(self, query: str) -> Optional[Dict[str, Any]]:
        """
        정확한 쿼리 매칭 캐시 조회

        Args:
            query: 검색 쿼리

        Returns:
            캐시된 결과 or None
        """
        cache_key = self._make_exact_key(query)

        if self.connected:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"[Cache HIT] Exact: {query[:50]}")
                return json.loads(cached)
        else:
            # In-memory fallback
            if cache_key in self._memory_cache:
                logger.debug(f"[Memory HIT] Exact: {query[:50]}")
                return self._memory_cache[cache_key]

        logger.debug(f"[Cache MISS] Exact: {query[:50]}")
        return None

    def set_exact(self, query: str, result: Dict[str, Any], ttl: int = 3600):  # 1 hour
        """
        정확한 쿼리 매칭 캐시 저장

        Args:
            query: 검색 쿼리
            result: 검색 결과
            ttl: Time to live (seconds)
        """
        cache_key = self._make_exact_key(query)

        if self.connected:
            self.redis_client.setex(cache_key, ttl, json.dumps(result, ensure_ascii=False))
        else:
            # In-memory fallback (no TTL)
            self._memory_cache[cache_key] = result

        logger.debug(f"[Cache SET] Exact: {query[:50]} (TTL: {ttl}s)")

    def _make_exact_key(self, query: str) -> str:
        """정확한 매칭용 캐시 키 생성"""
        # Normalize query (lowercase, strip)
        normalized = query.lower().strip()
        return f"exact:{normalized}"

    # =========================================================================
    # Layer 2: Semantic Cache
    # =========================================================================

    def get_semantic(
        self, query: str, query_embedding: List[float], similarity_threshold: float = 0.95
    ) -> Optional[Dict[str, Any]]:
        """
        의미적 유사 쿼리 캐시 조회

        Args:
            query: 검색 쿼리
            query_embedding: 쿼리 임베딩 벡터
            similarity_threshold: 유사도 임계값

        Returns:
            캐시된 결과 or None
        """
        # TODO: Implement semantic similarity search
        # Requires:
        # 1. Store query embeddings in Redis
        # 2. Compute cosine similarity
        # 3. Return if similarity > threshold

        logger.debug(f"[Semantic Cache] Not implemented yet")
        return None

    def set_semantic(
        self,
        query: str,
        query_embedding: List[float],
        result: Dict[str, Any],
        ttl: int = 1800,  # 30 minutes
    ):
        """
        의미적 유사 쿼리 캐시 저장

        Args:
            query: 검색 쿼리
            query_embedding: 쿼리 임베딩 벡터
            result: 검색 결과
            ttl: Time to live (seconds)
        """
        # TODO: Implement semantic cache storage
        logger.debug(f"[Semantic Cache SET] Not implemented yet")
        pass

    # =========================================================================
    # Layer 3: Search Result Cache
    # =========================================================================

    def get_search_result(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """
        검색 결과 캐시 조회

        Args:
            query_hash: 쿼리 해시

        Returns:
            캐시된 검색 결과 or None
        """
        cache_key = f"search:{query_hash}"

        if self.connected:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"[Cache HIT] Search: {query_hash[:16]}")
                return json.loads(cached)
        else:
            if cache_key in self._memory_cache:
                logger.debug(f"[Memory HIT] Search: {query_hash[:16]}")
                return self._memory_cache[cache_key]

        logger.debug(f"[Cache MISS] Search: {query_hash[:16]}")
        return None

    def set_search_result(
        self, query_hash: str, results: List[Dict[str, Any]], ttl: int = 600  # 10 minutes
    ):
        """
        검색 결과 캐시 저장

        Args:
            query_hash: 쿼리 해시
            results: 검색 결과 리스트
            ttl: Time to live (seconds)
        """
        cache_key = f"search:{query_hash}"

        if self.connected:
            self.redis_client.setex(cache_key, ttl, json.dumps(results, ensure_ascii=False))
        else:
            self._memory_cache[cache_key] = results

        logger.debug(f"[Cache SET] Search: {query_hash[:16]} (TTL: {ttl}s)")

    # =========================================================================
    # Utilities
    # =========================================================================

    @staticmethod
    def make_query_hash(query: str, filters: Optional[Dict] = None) -> str:
        """
        쿼리 + 필터를 조합한 해시 생성

        Args:
            query: 검색 쿼리
            filters: 메타데이터 필터

        Returns:
            MD5 해시 (16진수)
        """
        # Combine query and filters
        combined = {"query": query.lower().strip(), "filters": filters or {}}

        # Serialize to JSON (sorted keys for consistency)
        serialized = json.dumps(combined, sort_keys=True, ensure_ascii=False)

        # Compute MD5 hash
        hash_obj = hashlib.md5(serialized.encode("utf-8"))
        return hash_obj.hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 조회

        Returns:
            {
                'connected': bool,
                'total_keys': int,
                'memory_used': str,
                'hit_rate': float (if available)
            }
        """
        if self.connected:
            info = self.redis_client.info("stats")
            memory_info = self.redis_client.info("memory")

            # Calculate hit rate
            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)
            total_requests = keyspace_hits + keyspace_misses

            hit_rate = keyspace_hits / total_requests if total_requests > 0 else 0.0

            return {
                "connected": True,
                "total_keys": self.redis_client.dbsize(),
                "memory_used": memory_info.get("used_memory_human", "N/A"),
                "hit_rate": hit_rate,
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses,
            }
        else:
            return {
                "connected": False,
                "total_keys": len(self._memory_cache),
                "memory_used": "In-memory fallback",
                "hit_rate": 0.0,
            }

    def clear_all(self):
        """모든 캐시 삭제 (개발/테스트용)"""
        if self.connected:
            self.redis_client.flushdb()
            logger.info("Redis cache cleared")
        else:
            self._memory_cache.clear()
            logger.info("In-memory cache cleared")

    def close(self):
        """Redis 연결 종료"""
        if self.connected:
            self.redis_client.close()
            logger.info("Redis connection closed")


if __name__ == "__main__":
    # Test cache manager
    print("=" * 80)
    print("CACHE MANAGER TEST")
    print("=" * 80)

    # Initialize (will use in-memory fallback if Redis not available)
    cache = CacheManager()

    print(f"\n[Test] Connection status: {cache.connected}")
    print(f"[Test] Stats: {cache.get_stats()}")

    # Test exact match cache
    print("\n" + "-" * 80)
    print("[Test 1] Exact Match Cache")

    query1 = "20파이 캡 5,000개 주문 가능한 제품"
    result1 = {
        "products": [
            {"name": "GY-20-뾰족캡B", "score": 0.95},
            {"name": "20파이 일반캡", "score": 0.90},
        ],
        "total": 2,
    }

    # Set cache
    cache.set_exact(query1, result1)
    print(f"✅ Cached query: {query1[:50]}...")

    # Get cache (should hit)
    cached1 = cache.get_exact(query1)
    print(f"✅ Cache retrieved: {cached1 is not None}")
    print(f"   Products: {len(cached1['products']) if cached1 else 0}")

    # Get cache with different query (should miss)
    query2 = "24파이 캡"
    cached2 = cache.get_exact(query2)
    print(f"✅ Different query (miss): {cached2 is None}")

    # Test query hash
    print("\n" + "-" * 80)
    print("[Test 2] Query Hash")

    hash1 = CacheManager.make_query_hash("20파이 캡", {"category": "cap"})
    hash2 = CacheManager.make_query_hash("20파이 캡", {"category": "cap"})
    hash3 = CacheManager.make_query_hash("20파이 캡", {"category": "bottle"})

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")
    print(f"✅ Same query+filter → Same hash: {hash1 == hash2}")
    print(f"✅ Different filter → Different hash: {hash1 != hash3}")

    # Test search result cache
    print("\n" + "-" * 80)
    print("[Test 3] Search Result Cache")

    search_results = [{"chunk_id": "001", "score": 0.95}, {"chunk_id": "002", "score": 0.90}]

    cache.set_search_result(hash1, search_results)
    print(f"✅ Cached search results for hash: {hash1[:16]}...")

    cached_search = cache.get_search_result(hash1)
    print(f"✅ Retrieved: {len(cached_search) if cached_search else 0} results")

    # Stats
    print("\n" + "-" * 80)
    print("[Test 4] Cache Statistics")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Cleanup
    cache.close()

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)
