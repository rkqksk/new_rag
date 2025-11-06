"""
Cached Search Engine
기존 SearchEngine을 캐싱으로 감싸는 래퍼

목적: 기존 코드 변경 최소화하면서 캐싱 적용
전략:
- SearchEngine API와 동일한 인터페이스
- Transparent caching (캐시 히트 시 원본 호출 생략)
- 성능 메트릭 수집
"""

from typing import Dict, Any, List, Optional
import time
import logging

from src.core.caching.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class CachedSearchEngine:
    """
    캐싱이 적용된 검색 엔진 래퍼

    기존 SearchEngine을 감싸서 캐싱 기능 추가
    API는 동일하게 유지
    """

    def __init__(
        self,
        search_engine,  # Original SearchEngine instance
        cache_manager: Optional[CacheManager] = None,
        enable_cache: bool = True
    ):
        """
        Initialize Cached Search Engine

        Args:
            search_engine: 원본 SearchEngine 인스턴스
            cache_manager: CacheManager 인스턴스 (None이면 새로 생성)
            enable_cache: 캐싱 활성화 여부
        """
        self.search_engine = search_engine
        self.cache = cache_manager or CacheManager()
        self.enable_cache = enable_cache and self.cache.connected

        # Performance metrics
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time_saved': 0.0,  # seconds
            'avg_cached_response_time': 0.0,
            'avg_uncached_response_time': 0.0
        }

        logger.info(f"CachedSearchEngine initialized (cache: {self.enable_cache})")

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        캐싱이 적용된 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            filters: 메타데이터 필터
            **kwargs: 추가 파라미터

        Returns:
            검색 결과 리스트
        """
        start_time = time.time()
        self.stats['total_queries'] += 1

        # Step 1: Try exact match cache
        if self.enable_cache:
            cached_result = self._try_cache(query, filters)
            if cached_result is not None:
                response_time = time.time() - start_time
                self.stats['cache_hits'] += 1
                self._update_cached_response_time(response_time)

                logger.info(f"[Cache HIT] Query: {query[:50]}... ({response_time*1000:.1f}ms)")
                return cached_result[:top_k]

        # Step 2: Cache miss - call original search engine
        self.stats['cache_misses'] += 1

        logger.debug(f"[Cache MISS] Calling original search engine...")
        results = self.search_engine.search(
            query=query,
            top_k=top_k,
            filters=filters,
            **kwargs
        )

        # Step 3: Cache the result
        if self.enable_cache and results:
            self._cache_result(query, filters, results)

        response_time = time.time() - start_time
        self._update_uncached_response_time(response_time)

        logger.info(f"[Cache MISS] Query: {query[:50]}... ({response_time*1000:.1f}ms)")
        return results

    def _try_cache(
        self,
        query: str,
        filters: Optional[Dict] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        캐시 조회 (Layer 1: Exact Match)

        Args:
            query: 검색 쿼리
            filters: 메타데이터 필터

        Returns:
            캐시된 결과 or None
        """
        # Try exact match
        cached = self.cache.get_exact(query)
        if cached and cached.get('filters') == filters:
            return cached.get('results')

        # TODO: Try semantic cache (Layer 2)
        # TODO: Try search result cache (Layer 3)

        return None

    def _cache_result(
        self,
        query: str,
        filters: Optional[Dict],
        results: List[Dict[str, Any]]
    ):
        """
        검색 결과 캐싱

        Args:
            query: 검색 쿼리
            filters: 메타데이터 필터
            results: 검색 결과
        """
        # Cache in Layer 1 (Exact Match)
        cache_data = {
            'query': query,
            'filters': filters,
            'results': results
        }
        self.cache.set_exact(query, cache_data, ttl=3600)  # 1 hour

        # Also cache in Layer 3 (Search Result) with query hash
        query_hash = CacheManager.make_query_hash(query, filters)
        self.cache.set_search_result(query_hash, results, ttl=600)  # 10 minutes

    def _update_cached_response_time(self, response_time: float):
        """캐시 히트 응답 시간 업데이트"""
        n = self.stats['cache_hits']
        if n == 1:
            self.stats['avg_cached_response_time'] = response_time
        else:
            # Running average
            current_avg = self.stats['avg_cached_response_time']
            self.stats['avg_cached_response_time'] = (
                (current_avg * (n - 1) + response_time) / n
            )

    def _update_uncached_response_time(self, response_time: float):
        """캐시 미스 응답 시간 업데이트"""
        n = self.stats['cache_misses']
        if n == 1:
            self.stats['avg_uncached_response_time'] = response_time
        else:
            # Running average
            current_avg = self.stats['avg_uncached_response_time']
            self.stats['avg_uncached_response_time'] = (
                (current_avg * (n - 1) + response_time) / n
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        캐싱 성능 통계 조회

        Returns:
            {
                'total_queries': int,
                'cache_hits': int,
                'cache_misses': int,
                'hit_rate': float,
                'avg_cached_response_ms': float,
                'avg_uncached_response_ms': float,
                'time_saved_total': float (seconds),
                'cache_info': Dict (from CacheManager)
            }
        """
        total_queries = self.stats['total_queries']
        hit_rate = self.stats['cache_hits'] / total_queries if total_queries > 0 else 0.0

        # Calculate time saved
        if self.stats['cache_hits'] > 0 and self.stats['cache_misses'] > 0:
            avg_uncached = self.stats['avg_uncached_response_time']
            avg_cached = self.stats['avg_cached_response_time']
            time_saved_per_hit = max(0, avg_uncached - avg_cached)
            total_time_saved = time_saved_per_hit * self.stats['cache_hits']
        else:
            total_time_saved = 0.0

        return {
            'total_queries': total_queries,
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate': hit_rate,
            'avg_cached_response_ms': self.stats['avg_cached_response_time'] * 1000,
            'avg_uncached_response_ms': self.stats['avg_uncached_response_time'] * 1000,
            'time_saved_total_sec': total_time_saved,
            'cache_enabled': self.enable_cache,
            'cache_info': self.cache.get_stats()
        }

    def print_stats(self):
        """통계를 보기 좋게 출력"""
        stats = self.get_stats()

        print("=" * 80)
        print("CACHED SEARCH ENGINE - PERFORMANCE STATS")
        print("=" * 80)

        print(f"\n📊 Query Statistics:")
        print(f"  Total Queries:    {stats['total_queries']}")
        print(f"  Cache Hits:       {stats['cache_hits']}")
        print(f"  Cache Misses:     {stats['cache_misses']}")
        print(f"  Hit Rate:         {stats['hit_rate']:.1%}")

        print(f"\n⚡ Response Time:")
        print(f"  Cached (avg):     {stats['avg_cached_response_ms']:.1f} ms")
        print(f"  Uncached (avg):   {stats['avg_uncached_response_ms']:.1f} ms")

        if stats['time_saved_total_sec'] > 0:
            print(f"  Time Saved:       {stats['time_saved_total_sec']:.2f} seconds")
            speedup = stats['avg_uncached_response_ms'] / max(1, stats['avg_cached_response_ms'])
            print(f"  Speedup:          {speedup:.1f}x faster (when cached)")

        print(f"\n💾 Cache Status:")
        print(f"  Enabled:          {stats['cache_enabled']}")
        print(f"  Connected:        {stats['cache_info']['connected']}")
        print(f"  Total Keys:       {stats['cache_info']['total_keys']}")
        print(f"  Memory Used:      {stats['cache_info']['memory_used']}")

        print("=" * 80)

    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear_all()
        logger.info("Cache cleared")

    def close(self):
        """리소스 정리"""
        self.cache.close()


if __name__ == "__main__":
    # Test cached search engine
    print("=" * 80)
    print("CACHED SEARCH ENGINE TEST")
    print("=" * 80)

    # Mock SearchEngine for testing
    class MockSearchEngine:
        """Mock search engine for testing"""

        def search(self, query: str, top_k: int = 5, filters=None, **kwargs):
            """Simulate search with delay"""
            import time
            time.sleep(0.1)  # Simulate 100ms search

            # Return mock results
            return [
                {'product_id': '001', 'name': f'Result for: {query}', 'score': 0.95},
                {'product_id': '002', 'name': 'Another result', 'score': 0.90}
            ]

    # Initialize
    mock_engine = MockSearchEngine()
    cached_engine = CachedSearchEngine(mock_engine)

    print(f"\n[Test] Cache enabled: {cached_engine.enable_cache}")

    # Test 1: First query (cache miss)
    print("\n" + "-" * 80)
    print("[Test 1] First query (should miss)")

    query1 = "20파이 캡 5,000개"
    results1 = cached_engine.search(query1, top_k=3)
    print(f"✅ Results: {len(results1)} items")

    # Test 2: Same query (cache hit)
    print("\n" + "-" * 80)
    print("[Test 2] Same query (should hit)")

    results2 = cached_engine.search(query1, top_k=3)
    print(f"✅ Results: {len(results2)} items")

    # Test 3: Different query (cache miss)
    print("\n" + "-" * 80)
    print("[Test 3] Different query (should miss)")

    query2 = "100ml PE 보틀"
    results3 = cached_engine.search(query2, top_k=3)
    print(f"✅ Results: {len(results3)} items")

    # Test 4: Query 1 again (cache hit)
    print("\n" + "-" * 80)
    print("[Test 4] Query 1 again (should hit)")

    results4 = cached_engine.search(query1, top_k=3)
    print(f"✅ Results: {len(results4)} items")

    # Print stats
    print("\n")
    cached_engine.print_stats()

    # Cleanup
    cached_engine.close()

    print("\n✅ TEST COMPLETED")
