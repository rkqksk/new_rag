"""
Unit Tests for QueryClassifier

Tests query classification functionality with various query types.
"""

from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from apps.api.rag_consultation.classification.query_classifier import QueryClassifier
from apps.api.rag_consultation.models import QueryType


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock()
    return redis_mock


@pytest.fixture
def query_classifier(mock_redis):
    """Query classifier instance with mocked dependencies."""
    return QueryClassifier(redis_client=mock_redis)


class TestQueryClassifier:
    """Test cases for QueryClassifier."""

    @pytest.mark.asyncio
    async def test_classify_factual_query(self, query_classifier):
        """Test classification of factual query."""
        query = "What is machine learning?"
        analysis = await query_classifier.classify(query)

        assert analysis.query_type == QueryType.FACTUAL
        assert analysis.confidence > 0.3
        assert len(analysis.query_type_scores) == 7

    @pytest.mark.asyncio
    async def test_classify_procedural_query(self, query_classifier):
        """Test classification of procedural query."""
        query = "How do I configure the system?"
        analysis = await query_classifier.classify(query)

        assert analysis.query_type == QueryType.PROCEDURAL
        assert analysis.confidence > 0.3

    @pytest.mark.asyncio
    async def test_classify_troubleshooting_query(self, query_classifier):
        """Test classification of troubleshooting query."""
        query = "Error connecting to database"
        analysis = await query_classifier.classify(query)

        assert analysis.query_type == QueryType.TROUBLESHOOTING
        assert analysis.confidence > 0.3

    @pytest.mark.asyncio
    async def test_empty_query_raises_error(self, query_classifier):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await query_classifier.classify("")

    @pytest.mark.asyncio
    async def test_cache_hit(self, query_classifier, mock_redis):
        """Test cache retrieval on second query."""
        query = "What is RAG?"

        # First call - cache miss
        analysis1 = await query_classifier.classify(query)

        # Second call - should use cache
        # Mock cache hit
        mock_redis.get = AsyncMock(return_value=analysis1.model_dump_json())
        analysis2 = await query_classifier.classify(query)

        assert analysis1.query == analysis2.query
        assert analysis1.query_type == analysis2.query_type

    def test_prototype_embeddings_initialization(self, query_classifier):
        """Test that prototype embeddings are initialized."""
        assert len(query_classifier._prototype_embeddings) == 7
        for query_type, embedding in query_classifier._prototype_embeddings.items():
            assert isinstance(embedding, np.ndarray)
            assert embedding.shape[0] > 0
