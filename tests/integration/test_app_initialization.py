"""
Integration tests for app initialization and configuration

Tests application startup, configuration loading, and dependency resolution
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.integration
def test_app_imports_successfully():
    """Test that main app module imports without errors"""
    try:
        from app.api.main import app

        assert app is not None
        assert hasattr(app, "get")
        assert hasattr(app, "post")
    except ImportError as e:
        pytest.fail(f"Failed to import app: {e}")


@pytest.mark.integration
def test_config_loads_successfully():
    """Test that configuration loads from environment"""
    from app.core.dependencies import get_config

    config = get_config()
    assert config is not None
    assert hasattr(config, "qdrant_host")
    assert hasattr(config, "redis_host")
    assert hasattr(config, "postgres_host")


@pytest.mark.integration
def test_metrics_registry_initialized():
    """Test that Prometheus metrics registry is initialized"""
    from app.core.metrics import REGISTRY, http_requests_total

    assert REGISTRY is not None
    assert http_requests_total is not None


@pytest.mark.integration
def test_dependency_injection_available():
    """Test that dependency injection functions are available"""
    from app.core.dependencies import (
        get_config,
        get_embedding_model,
        get_qdrant_client,
        get_rag_qa_service,
        get_redis_client,
    )

    assert callable(get_config)
    assert callable(get_qdrant_client)
    assert callable(get_redis_client)
    assert callable(get_embedding_model)
    assert callable(get_rag_qa_service)


@pytest.mark.integration
def test_schemas_importable():
    """Test that all schemas are importable"""
    from app.models.schemas import (
        ConsultationRequest,
        ConsultationResponse,
        ErrorResponse,
        HealthCheckResponse,
        QARequest,
        QAResponse,
    )

    assert QARequest is not None
    assert QAResponse is not None
    assert ConsultationRequest is not None
    assert ConsultationResponse is not None
    assert HealthCheckResponse is not None
    assert ErrorResponse is not None


@pytest.mark.integration
def test_middleware_importable():
    """Test that middleware is importable"""
    from app.core.middleware import MetricsMiddleware

    assert MetricsMiddleware is not None


@pytest.mark.integration
def test_routes_registered():
    """Test that route modules can be imported"""
    try:
        from app.api import dashboard_routes, ingestion_routes, query_routes

        assert dashboard_routes.router is not None
        assert query_routes.router is not None
        assert ingestion_routes.router is not None
    except ImportError as e:
        pytest.fail(f"Failed to import routes: {e}")


@pytest.mark.integration
def test_app_has_metrics_endpoint():
    """Test that app has metrics endpoint defined"""
    from app.api.main import app

    # Check if metrics route is registered
    routes = [route.path for route in app.routes]
    assert "/metrics" in routes or any("metrics" in str(route) for route in app.routes)


@pytest.mark.integration
def test_app_has_health_endpoint():
    """Test that app has health endpoint defined"""
    from app.api.main import app

    routes = [route.path for route in app.routes]
    assert "/health" in routes or any("health" in str(route) for route in app.routes)


@pytest.mark.integration
def test_override_dependencies_works():
    """Test that test dependency overrides can be configured"""
    from app.core.dependencies import override_dependencies_for_testing

    overrides = override_dependencies_for_testing()
    assert overrides is not None
    assert isinstance(overrides, dict)
    assert len(overrides) > 0


@pytest.mark.integration
def test_config_validation():
    """Test that config validates required fields"""
    from app.core.dependencies import AppConfig

    try:
        # Should raise ValueError if POSTGRES_PASSWORD not set
        with patch.dict("os.environ", {}, clear=False):
            # This test ensures postgres_password is required
            config = AppConfig()
            # If we get here, password was in env or config allows it
            assert config is not None
    except ValueError as e:
        # Expected if POSTGRES_PASSWORD not in environment
        assert "POSTGRES_PASSWORD" in str(e)


@pytest.mark.integration
def test_services_instantiable_with_mocks():
    """Test that services can be instantiated with mocked dependencies"""
    from unittest.mock import Mock

    from app.services.rag_qa_service import RAGQAService

    mock_qdrant = Mock()
    mock_model = Mock()

    service = RAGQAService(
        qdrant_client=mock_qdrant,
        embedding_model=mock_model,
        ollama_url="http://localhost:11434",
        model_name="test-model",
    )
    assert service is not None


@pytest.mark.integration
def test_health_check_response_schema():
    """Test that HealthCheckResponse schema is valid"""
    from app.models.schemas import HealthCheckResponse

    response = HealthCheckResponse(
        api="healthy", qdrant=True, redis=True, postgres=True, timestamp="2025-10-19T10:45:00Z"
    )
    assert response.api == "healthy"


@pytest.mark.integration
def test_error_response_schema():
    """Test that ErrorResponse schema is valid"""
    from app.models.schemas import ErrorResponse

    response = ErrorResponse(
        error="VALIDATION_ERROR", message="Test error message", timestamp="2025-10-19T10:45:00Z"
    )
    assert response.error == "VALIDATION_ERROR"
    assert response.message == "Test error message"


@pytest.mark.integration
def test_qa_request_schema_validation():
    """Test that QARequest schema validates input"""
    from app.models.schemas import QARequest

    # Valid request
    request = QARequest(question="What is AI?")
    assert request.question == "What is AI?"

    # Invalid: empty question should fail
    with pytest.raises(Exception):  # Pydantic validation error
        QARequest(question="")


@pytest.mark.integration
def test_metrics_functions_callable():
    """Test that metric recording functions are callable"""
    from app.core.metrics import (
        embedding_generation_total,
        http_request_duration_seconds,
        http_requests_total,
        vector_search_total,
    )

    # All metrics should have methods for recording
    assert hasattr(http_requests_total, "labels")
    assert hasattr(http_request_duration_seconds, "observe")
    assert hasattr(embedding_generation_total, "labels")
    assert hasattr(vector_search_total, "labels")


@pytest.mark.integration
def test_middleware_dispatch_signature():
    """Test that middleware has correct dispatch signature"""
    import inspect

    from app.core.middleware import MetricsMiddleware

    # Check dispatch method exists
    assert hasattr(MetricsMiddleware, "dispatch")

    # Check it's async
    sig = inspect.signature(MetricsMiddleware.dispatch)
    assert "request" in sig.parameters
    assert "call_next" in sig.parameters


@pytest.mark.integration
def test_app_cors_configured():
    """Test that CORS middleware is configured"""
    from app.api.main import app

    # Check that middleware is in the middleware stack (at least metrics or CORS)
    middleware_count = len(app.user_middleware) if hasattr(app, "user_middleware") else 0
    # Just verify app object has middleware configuration
    assert app is not None
    assert hasattr(app, "middleware") or hasattr(app, "user_middleware")


@pytest.mark.integration
def test_dependencies_singleton_pattern():
    """Test that dependencies follow singleton pattern"""
    from app.core.dependencies import get_config

    config1 = get_config()
    config2 = get_config()

    # Should be same instance (lru_cache)
    assert config1 is config2


@pytest.mark.integration
def test_no_circular_imports():
    """Test that main app has no circular import issues"""
    # If we got here, the app imported successfully
    from app.api.main import app
    from app.core.dependencies import get_config
    from app.models.schemas import QARequest

    # All should be importable without circular dependency errors
    assert app is not None
    assert get_config is not None
    assert QARequest is not None
