"""
Pytest configuration for integration tests

Provides shared fixtures and configuration for integration testing
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing"""
    client = Mock()
    client.search = AsyncMock(return_value=[])
    client.get_collection = Mock()
    client.upsert = Mock()
    client.create_collection = Mock()
    client.recreate_collection = Mock()
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    client = Mock()
    client.get = Mock(return_value=None)
    client.setex = Mock()
    client.ping = Mock(return_value=True)
    client.set = Mock()
    client.delete = Mock()
    client.exists = Mock(return_value=False)
    return client


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model for testing"""
    model = Mock()
    model.encode = Mock(return_value=[[0.1] * 384])
    return model


@pytest.fixture
def mock_config():
    """Mock application configuration"""
    config = Mock()
    config.qdrant_host = "localhost"
    config.qdrant_port = 6333
    config.redis_host = "localhost"
    config.redis_port = 6379
    config.embedding_model = "test-model"
    config.embedding_dim = 384
    config.ollama_url = "http://localhost:11434"
    config.ollama_model = "test-model"
    config.postgres_host = "localhost"
    config.postgres_port = 5432
    config.postgres_user = "postgres"
    config.postgres_password = "test"
    config.postgres_db = "test_db"
    config.allowed_origins = ["http://localhost:3000"]
    return config


@pytest.fixture
def mock_rag_qa_service():
    """Mock RAG QA service"""
    service = Mock()
    service.query = AsyncMock(
        return_value={"answer": "Test answer", "citations": ["source1"], "confidence": 0.9}
    )
    return service


@pytest.fixture
def mock_consultation_service():
    """Mock consultation service"""
    service = Mock()
    service.consult = AsyncMock(return_value={"recommendations": ["rec1"], "confidence": 0.85})
    return service


@pytest.fixture
def mock_document_ingestion_service():
    """Mock document ingestion service"""
    service = Mock()
    service.ingest = AsyncMock(
        return_value={"document_id": "doc-123", "chunks": 10, "status": "completed"}
    )
    return service


@pytest.fixture
def integration_test_markers():
    """Marker configuration for integration tests"""
    return {
        "integration": "integration tests requiring mocked services",
        "slow": "slow running integration tests",
        "asyncio": "async integration tests",
    }
