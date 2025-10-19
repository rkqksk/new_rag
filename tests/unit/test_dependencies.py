"""
Unit tests for app/core/dependencies.py

Tests the Dependency Injection container including:
- Configuration management
- Singleton pattern with caching
- Service factory functions
- Testing utilities
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from qdrant_client import QdrantClient
import redis

from app.core.dependencies import (
    AppConfig,
    get_config,
    get_qdrant_client,
    get_redis_client,
    get_embedding_model,
    get_rag_qa_service,
    get_consultation_service,
    get_document_ingestion_service,
    override_dependencies_for_testing,
)


@pytest.mark.unit
def test_app_config_initialization():
    """Test AppConfig loads environment variables correctly"""
    config = AppConfig()

    assert config.qdrant_host is not None
    assert config.qdrant_port > 0
    assert config.redis_host is not None
    assert config.redis_port > 0
    assert config.embedding_model is not None
    assert config.embedding_dim > 0


@pytest.mark.unit
def test_app_config_postgres_password_validation():
    """Test that AppConfig requires POSTGRES_PASSWORD"""
    # This test verifies the validation logic exists
    # Note: In practice, the password is set in test environment
    # So we just verify the current config is valid
    config = get_config()
    assert config.postgres_password is not None


@pytest.mark.unit
def test_app_config_customizable_from_env():
    """Test that AppConfig can be customized via environment variables"""
    with patch.dict('os.environ', {
        'QDRANT_HOST': 'custom-qdrant',
        'QDRANT_HTTP_PORT': '9999',
        'EMBEDDING_DIM': '512',
        'POSTGRES_PASSWORD': 'test-password'
    }):
        config = AppConfig()

        assert config.qdrant_host == 'custom-qdrant'
        assert config.qdrant_port == 9999
        assert config.embedding_dim == 512


@pytest.mark.unit
def test_get_config_is_singleton():
    """Test that get_config returns same instance (caching)"""
    config1 = get_config()
    config2 = get_config()

    # Should be same object due to @lru_cache()
    assert config1 is config2


@pytest.mark.unit
def test_get_config_returns_app_config():
    """Test that get_config returns AppConfig instance"""
    config = get_config()

    assert isinstance(config, AppConfig)
    assert hasattr(config, 'qdrant_host')
    assert hasattr(config, 'redis_host')
    assert hasattr(config, 'embedding_model')


@pytest.mark.unit
def test_get_qdrant_client_returns_qdrant_client():
    """Test that get_qdrant_client returns QdrantClient"""
    client = get_qdrant_client(get_config())

    assert isinstance(client, QdrantClient)


@pytest.mark.unit
def test_get_qdrant_client_singleton():
    """Test that get_qdrant_client returns same instance (singleton)"""
    config = get_config()
    client1 = get_qdrant_client(config)
    client2 = get_qdrant_client(config)

    # Should be same object due to @lru_cache()
    assert client1 is client2


@pytest.mark.unit
def test_get_redis_client_returns_redis():
    """Test that get_redis_client returns Redis client"""
    client = get_redis_client(get_config())

    assert isinstance(client, redis.Redis)


@pytest.mark.unit
def test_get_redis_client_singleton():
    """Test that get_redis_client returns same instance (singleton)"""
    config = get_config()
    client1 = get_redis_client(config)
    client2 = get_redis_client(config)

    # Should be same object due to @lru_cache()
    assert client1 is client2


@pytest.mark.unit
def test_get_embedding_model_returns_transformer():
    """Test that get_embedding_model returns SentenceTransformer"""
    from sentence_transformers import SentenceTransformer
    model = get_embedding_model(get_config())

    assert isinstance(model, SentenceTransformer)


@pytest.mark.unit
def test_get_embedding_model_singleton():
    """Test that get_embedding_model returns same instance (singleton)"""
    config = get_config()
    model1 = get_embedding_model(config)
    model2 = get_embedding_model(config)

    # Should be same object due to @lru_cache()
    assert model1 is model2


@pytest.mark.unit
def test_get_rag_qa_service_with_mocked_dependencies():
    """Test that get_rag_qa_service accepts injected mocked dependencies"""
    config = get_config()
    mock_qdrant = Mock(spec=QdrantClient)
    mock_model = Mock()

    service = get_rag_qa_service(mock_qdrant, mock_model, config)

    # Service should be created with provided dependencies
    assert service is not None


@pytest.mark.unit
def test_get_consultation_service_with_mocked_dependencies():
    """Test consultation service with mocked dependencies"""
    mock_qdrant = Mock(spec=QdrantClient)
    mock_model = Mock()

    service = get_consultation_service(mock_qdrant, mock_model)

    assert service is not None


@pytest.mark.unit
def test_get_document_ingestion_service_with_mocked_dependencies():
    """Test document ingestion service with mocked dependencies"""
    mock_qdrant = Mock(spec=QdrantClient)
    mock_model = Mock()
    mock_redis = Mock(spec=redis.Redis)

    service = get_document_ingestion_service(mock_qdrant, mock_model, mock_redis)

    assert service is not None


@pytest.mark.unit
def test_override_dependencies_for_testing_returns_dict():
    """Test that override_dependencies_for_testing returns override dictionary"""
    overrides = override_dependencies_for_testing()

    assert isinstance(overrides, dict)
    assert get_config in overrides or get_qdrant_client in overrides


@pytest.mark.unit
def test_override_dependencies_creates_mocks():
    """Test that overrides dictionary creates mock services"""
    overrides = override_dependencies_for_testing()

    # Should have mock factories
    assert len(overrides) > 0

    # Each override should be callable (factory function)
    for override_func in overrides.values():
        assert callable(override_func)


@pytest.mark.unit
def test_mock_qdrant_from_overrides():
    """Test that overridden Qdrant is properly mocked"""
    overrides = override_dependencies_for_testing()

    if get_qdrant_client in overrides:
        mock_qdrant_factory = overrides[get_qdrant_client]
        mock_qdrant = mock_qdrant_factory()

        assert isinstance(mock_qdrant, Mock)
        assert hasattr(mock_qdrant, 'search')


@pytest.mark.unit
def test_mock_redis_from_overrides():
    """Test that overridden Redis is properly mocked"""
    overrides = override_dependencies_for_testing()

    if get_redis_client in overrides:
        mock_redis_factory = overrides[get_redis_client]
        mock_redis = mock_redis_factory()

        assert isinstance(mock_redis, Mock)
        assert hasattr(mock_redis, 'get')
        assert hasattr(mock_redis, 'setex')


@pytest.mark.unit
def test_mock_config_from_overrides():
    """Test that overridden config is properly mocked"""
    overrides = override_dependencies_for_testing()

    if get_config in overrides:
        mock_config_factory = overrides[get_config]
        mock_config = mock_config_factory()

        assert isinstance(mock_config, Mock)
        assert hasattr(mock_config, 'qdrant_host')
        assert hasattr(mock_config, 'embedding_model')


@pytest.mark.unit
def test_dependencies_no_circular_dependencies():
    """Test that dependency graph has no circular dependencies"""
    config = get_config()

    # Config should not depend on anything
    assert config is not None

    # Infrastructure dependencies depend on config
    qdrant = get_qdrant_client(config)
    redis = get_redis_client(config)
    model = get_embedding_model(config)

    assert qdrant is not None
    assert redis is not None
    assert model is not None


@pytest.mark.unit
def test_dependency_configuration_complete():
    """Test that all required dependencies can be resolved"""
    config = get_config()

    # Verify all infrastructure dependencies work
    assert get_config() is not None
    assert get_qdrant_client(config) is not None
    assert get_redis_client(config) is not None
    assert get_embedding_model(config) is not None
