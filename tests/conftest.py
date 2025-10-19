"""
Test fixtures and configuration for pytest test suite.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from qdrant_client import QdrantClient
import redis
from typing import List, Dict

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for unit tests"""
    client = Mock(spec=QdrantClient)
    client.search = AsyncMock(return_value=[])
    client.get_collection = Mock()
    client.upsert = Mock()
    client.create_collection = Mock()
    client.get_collections = Mock(return_value=[])
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for unit tests"""
    client = Mock(spec=redis.Redis)
    client.get = Mock(return_value=None)
    client.setex = Mock()
    client.ping = Mock(return_value=True)
    client.delete = Mock()
    return client


@pytest.fixture
def mock_embedding_model():
    """Mock SentenceTransformer for unit tests"""
    model = Mock()
    model.encode = Mock(return_value=[[0.1] * 384])
    model.get_sentence_embedding_dimension = Mock(return_value=384)
    return model


@pytest.fixture
async def test_qdrant_client():
    """Real Qdrant client for integration tests"""
    client = QdrantClient(host="172.28.0.2", port=6333)
    yield client
    # Cleanup test collections if needed


@pytest.fixture
def sample_qa_request():
    """Sample QA request for testing"""
    from app.models.schemas import QARequest
    return QARequest(
        question="What is the price?",
        max_results=5,
        score_threshold=0.3
    )


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        {"id": "doc1", "text": "Product A costs $100", "metadata": {}},
        {"id": "doc2", "text": "Product B costs $200", "metadata": {}},
    ]


@pytest.fixture
def sample_search_results():
    """Sample Qdrant search results"""
    from qdrant_client.models import ScoredPoint
    return [
        Mock(
            spec=ScoredPoint,
            id="doc1",
            score=0.95,
            payload={"text": "Product A costs $100", "metadata": {}}
        ),
        Mock(
            spec=ScoredPoint,
            id="doc2",
            score=0.85,
            payload={"text": "Product B costs $200", "metadata": {}}
        ),
    ]


@pytest.fixture
def sample_chunks():
    """Sample text chunks for testing"""
    return [
        "This is the first chunk of text for testing.",
        "This is the second chunk with different content.",
        "The third chunk contains more information.",
    ]
