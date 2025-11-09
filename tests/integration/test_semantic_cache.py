"""
Integration tests for semantic cache (3-layer caching system)
"""

import pytest
from src.core.caching.cache_manager import CacheManager, cosine_similarity


class TestSemanticCache:
    """Test semantic caching with Redis"""

    @pytest.fixture
    def cache_manager(self):
        """Create cache manager with test Redis connection"""
        return CacheManager(host="localhost", port=6379, db=15)  # Use test DB

    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]

        # Identical vectors
        assert cosine_similarity(vec1, vec2) == pytest.approx(1.0)

        # Orthogonal vectors
        assert cosine_similarity(vec1, vec3) == pytest.approx(0.0)

    def test_semantic_cache_set_and_get(self, cache_manager):
        """Test setting and getting from semantic cache"""
        if not cache_manager.connected:
            pytest.skip("Redis not available")

        query = "50ml PET bottle"
        embedding = [0.1, 0.2, 0.3] * 128  # 384-dim embedding
        result = {"products": [{"id": "test_1", "name": "Test Product"}]}

        # Set cache
        cache_manager.set_semantic(query, embedding, result, ttl=60)

        # Get cache with exact same embedding
        cached_result = cache_manager.get_semantic(query, embedding, similarity_threshold=0.99)

        assert cached_result is not None
        assert cached_result["products"][0]["name"] == "Test Product"

    def test_semantic_cache_similarity_threshold(self, cache_manager):
        """Test semantic cache respects similarity threshold"""
        if not cache_manager.connected:
            pytest.skip("Redis not available")

        query1 = "50ml PET bottle"
        embedding1 = [1.0, 0.0, 0.0] * 128
        result1 = {"products": [{"id": "1"}]}

        cache_manager.set_semantic(query1, embedding1, result1, ttl=60)

        # Similar query (should hit cache at 0.8 threshold)
        query2 = "50ml PET container"
        embedding2 = [0.9, 0.1, 0.0] * 128

        # Should not match at 0.99 threshold
        cached_high = cache_manager.get_semantic(query2, embedding2, similarity_threshold=0.99)
        assert cached_high is None

        # Should match at 0.5 threshold
        cached_low = cache_manager.get_semantic(query2, embedding2, similarity_threshold=0.5)
        assert cached_low is not None

    def test_exact_cache(self, cache_manager):
        """Test exact match cache (Layer 1)"""
        if not cache_manager.connected:
            pytest.skip("Redis not available")

        query = "exact test query"
        result = {"data": "test"}

        # Set exact cache
        cache_manager.set_exact(query, result, ttl=60)

        # Get exact cache
        cached = cache_manager.get_exact(query)
        assert cached is not None
        assert cached["data"] == "test"

        # Different query should miss
        cached_miss = cache_manager.get_exact("different query")
        assert cached_miss is None

    def test_cache_statistics(self, cache_manager):
        """Test cache statistics tracking"""
        if not cache_manager.connected:
            pytest.skip("Redis not available")

        # Perform some cache operations
        cache_manager.set_exact("test1", {"data": 1}, ttl=60)
        cache_manager.get_exact("test1")  # Hit
        cache_manager.get_exact("test2")  # Miss

        stats = cache_manager.get_stats()
        assert stats is not None
        # Stats should contain hits and misses
