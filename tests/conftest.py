"""Pytest configuration and fixtures for enterprise backend tests"""

import json
from typing import Any, AsyncGenerator, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Test data fixtures
@pytest.fixture
def sample_product():
    """Sample product data"""
    return {
        "id": "PROD-001",
        "name": "50ml PET 용기",
        "category": "bottle",
        "neck_size": "20파이",
        "capacity": "50ml",
        "material": "PET",
        "supplier": "천진코리아",
        "moq": "5000개",
        "price": "120원",
    }


@pytest.fixture
def sample_products():
    """List of sample products"""
    return [
        {
            "id": "PROD-001",
            "name": "50ml PET 용기",
            "category": "bottle",
            "neck_size": "20파이",
            "capacity": "50ml",
            "material": "PET",
            "supplier": "천진코리아",
            "score": 0.85,
        },
        {
            "id": "PROD-002",
            "name": "20파이 캡",
            "category": "cap",
            "neck_size": "20파이",
            "material": "PP",
            "supplier": "원하고",
            "score": 0.82,
        },
        {
            "id": "PROD-003",
            "name": "30파이 펌프",
            "category": "pump",
            "neck_size": "30파이",
            "material": "PP",
            "supplier": "프리몰드",
            "score": 0.78,
        },
    ]


@pytest.fixture
def sample_search_results():
    """Sample Qdrant search results"""
    return [
        {
            "id": "PROD-001",
            "score": 0.85,
            "payload": {
                "text": "50ml PET 용기, 20파이 넥, 천진코리아",
                "product_id": "PROD-001",
                "category": "bottle",
                "neck_size": "20파이",
            },
        },
        {
            "id": "PROD-002",
            "score": 0.82,
            "payload": {
                "text": "20파이 캡, PP 재질, 원하고",
                "product_id": "PROD-002",
                "category": "cap",
                "neck_size": "20파이",
            },
        },
    ]


@pytest.fixture
def sample_query_vector():
    """Sample embedding vector"""
    return [0.1] * 384  # 384-dim vector for all-MiniLM-L6-v2


@pytest.fixture
def sample_session_id():
    """Sample session ID"""
    return "sess_123456789"


@pytest.fixture
def sample_user_profile():
    """Sample user profile"""
    return {
        "session_id": "sess_123456789",
        "search_history": ["50ml 용기", "20파이 캡"],
        "viewed_products": ["PROD-001", "PROD-002"],
        "clicked_products": ["PROD-001"],
        "preferences": {
            "categories": {"bottle": 0.6, "cap": 0.4},
            "suppliers": {"천진코리아": 0.5, "원하고": 0.3},
            "neck_sizes": {"20파이": 0.8},
        },
        "focus_type": "compatibility",
    }


# Mock repository fixtures
@pytest.fixture
def mock_qdrant_repo():
    """Mock Qdrant repository"""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.search_multi_vector = AsyncMock()
    repo.get_point = AsyncMock()
    repo.upsert_points = AsyncMock()
    repo.health_check = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_redis_repo():
    """Mock Redis repository"""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.set = AsyncMock()
    repo.delete = AsyncMock()
    repo.exists = AsyncMock()
    repo.get_json = AsyncMock()
    repo.set_json = AsyncMock()
    repo.health_check = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_postgres_repo():
    """Mock Postgres repository"""
    repo = MagicMock()
    repo.execute = AsyncMock()
    repo.fetch = AsyncMock()
    repo.fetch_one = AsyncMock()
    repo.insert_search_event = AsyncMock()
    repo.insert_product_event = AsyncMock()
    repo.get_top_keywords = AsyncMock()
    repo.get_top_products = AsyncMock()
    repo.health_check = AsyncMock(return_value=True)
    return repo


# Mock src/ module fixtures
@pytest.fixture
def mock_embedder():
    """Mock MultiModalEmbedder"""
    embedder = MagicMock()
    embedder.encode_text = MagicMock(return_value=[0.1] * 384)
    embedder.encode_image = MagicMock(return_value=[0.2] * 1024)
    embedder.encode_shape = MagicMock(return_value=[0.3] * 128)
    return embedder


@pytest.fixture
def mock_reranker():
    """Mock CrossEncoderReranker"""
    reranker = MagicMock()
    reranker.rerank = MagicMock()
    return reranker


@pytest.fixture
def mock_router():
    """Mock QueryRouter"""
    router = MagicMock()
    router.route_query = MagicMock()
    return router


@pytest.fixture
def mock_personalization():
    """Mock AdvancedPersonalizationService"""
    service = MagicMock()
    service.track_search = AsyncMock()
    service.track_interaction = AsyncMock()
    service.get_profile = AsyncMock()
    service.personalize_results = AsyncMock()
    return service


# Database fixtures for integration tests
@pytest.fixture
async def test_db_connection():
    """Test database connection (for integration tests)"""
    # This would create a test database connection
    # For now, we'll use mocks in unit tests
    pass


@pytest.fixture
def mock_settings():
    """Mock application settings"""
    settings = MagicMock()
    settings.app_name = "RAG Enterprise API - Test"
    settings.environment = "test"
    settings.api_prefix = "/api/v1"
    settings.qdrant.host = "localhost"
    settings.qdrant.port = 6333
    settings.redis.host = "localhost"
    settings.redis.port = 6379
    settings.database.host = "localhost"
    settings.database.port = 5432
    return settings


# Test client fixture
@pytest.fixture
def test_client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient

    from apps.api.main import app

    return TestClient(app)


# Async test markers
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
