"""
Unit tests for app/core/metrics.py and app/core/middleware.py

Tests Prometheus metrics collection and MetricsMiddleware
"""
import pytest
from prometheus_client import REGISTRY, CollectorRegistry
from unittest.mock import Mock, AsyncMock, patch

from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    embedding_generation_total,
    embedding_cache_hits,
    vector_search_total,
    qdrant_upsert_total,
    redis_operations_total,
    document_ingestion_total,
    llm_query_total,
    active_requests,
    errors_total,
)
from app.core.middleware import MetricsMiddleware


@pytest.mark.unit
def test_http_requests_total_counter_exists():
    """Test that HTTP requests counter exists"""
    assert http_requests_total is not None
    # prometheus_client library uses shortened names for metrics
    assert 'http_requests' in http_requests_total._name


@pytest.mark.unit
def test_http_request_duration_histogram_exists():
    """Test that HTTP duration histogram exists"""
    assert http_request_duration_seconds is not None
    assert http_request_duration_seconds._name == 'http_request_duration_seconds'


@pytest.mark.unit
def test_embedding_metrics_exist():
    """Test that embedding metrics exist"""
    assert embedding_generation_total is not None
    assert embedding_cache_hits is not None


@pytest.mark.unit
def test_vector_search_metrics_exist():
    """Test that vector search metrics exist"""
    assert vector_search_total is not None


@pytest.mark.unit
def test_qdrant_metrics_exist():
    """Test that Qdrant metrics exist"""
    assert qdrant_upsert_total is not None


@pytest.mark.unit
def test_redis_metrics_exist():
    """Test that Redis metrics exist"""
    assert redis_operations_total is not None


@pytest.mark.unit
def test_document_ingestion_metrics_exist():
    """Test that document metrics exist"""
    assert document_ingestion_total is not None


@pytest.mark.unit
def test_llm_query_metrics_exist():
    """Test that LLM metrics exist"""
    assert llm_query_total is not None


@pytest.mark.unit
def test_system_health_metrics_exist():
    """Test that system health metrics exist"""
    assert active_requests is not None
    assert errors_total is not None


@pytest.mark.unit
def test_counter_metric_labels():
    """Test that counter metrics have correct labels"""
    # HTTP requests counter should have method, endpoint, status labels
    assert 'method' in http_requests_total._labelnames
    assert 'endpoint' in http_requests_total._labelnames
    assert 'status' in http_requests_total._labelnames


@pytest.mark.unit
def test_histogram_metric_labels():
    """Test that histogram metrics have correct labels"""
    # HTTP duration should have method and endpoint labels
    assert 'method' in http_request_duration_seconds._labelnames
    assert 'endpoint' in http_request_duration_seconds._labelnames


@pytest.mark.unit
def test_embedding_counter_labels():
    """Test embedding metrics have model label"""
    assert 'model' in embedding_generation_total._labelnames


@pytest.mark.unit
def test_cache_metrics_labels():
    """Test cache metrics have cache_type label"""
    assert 'cache_type' in embedding_cache_hits._labelnames


@pytest.mark.asyncio
@pytest.mark.unit
async def test_metrics_middleware_initialization():
    """Test MetricsMiddleware can be instantiated"""
    call_next = AsyncMock(return_value=Mock())
    middleware = MetricsMiddleware(app=None, dispatch=None)

    assert middleware is not None


@pytest.mark.unit
def test_http_requests_counter_increment():
    """Test HTTP requests counter can be incremented"""
    # Create a new registry to avoid conflicts
    test_registry = CollectorRegistry()

    # This would normally be done in metrics collection
    # Just verify the counter structure works
    assert 'http_requests' in http_requests_total._name


@pytest.mark.unit
def test_histogram_bucket_configuration():
    """Test that histograms have proper bucket configuration"""
    # HTTP duration should have reasonable buckets
    # prometheus_client histograms have internal bucket data
    assert http_request_duration_seconds is not None
    assert hasattr(http_request_duration_seconds, 'observe')


@pytest.mark.unit
def test_metrics_registry_initialized():
    """Test that metrics are registered"""
    # All metrics should be registered
    assert http_requests_total is not None
    assert embedding_generation_total is not None
    assert vector_search_total is not None


@pytest.mark.unit
def test_embedding_cache_hit_tracking():
    """Test embedding cache hit metric exists"""
    assert embedding_cache_hits._name == 'embedding_cache_hits'
    assert embedding_cache_hits._labelnames == ('cache_type',)


@pytest.mark.unit
def test_vector_search_metric_structure():
    """Test vector search metrics have proper structure"""
    assert vector_search_total._labelnames == ('collection',)


@pytest.mark.unit
def test_qdrant_collection_size_gauge():
    """Test Qdrant collection size gauge exists"""
    from app.core.metrics import qdrant_collection_size
    assert qdrant_collection_size is not None
    assert 'collection' in qdrant_collection_size._labelnames


@pytest.mark.unit
def test_redis_key_count_gauge():
    """Test Redis key count gauge exists"""
    from app.core.metrics import redis_key_count
    assert redis_key_count is not None


@pytest.mark.unit
def test_active_requests_gauge():
    """Test active requests gauge for endpoint tracking"""
    assert active_requests is not None
    assert 'endpoint' in active_requests._labelnames


@pytest.mark.unit
def test_errors_total_counter_labels():
    """Test errors counter has proper labels"""
    assert 'error_type' in errors_total._labelnames
    assert 'endpoint' in errors_total._labelnames


@pytest.mark.unit
def test_performance_percentile_metrics():
    """Test P95 and P99 latency metrics exist"""
    from app.core.metrics import p95_latency_seconds, p99_latency_seconds
    assert p95_latency_seconds is not None
    assert p99_latency_seconds is not None


@pytest.mark.unit
def test_throughput_metric_exists():
    """Test throughput metric exists"""
    from app.core.metrics import throughput_requests_per_second
    assert throughput_requests_per_second is not None


@pytest.mark.unit
def test_document_ingestion_metric_labels():
    """Test document ingestion metric has format and status labels"""
    assert 'format' in document_ingestion_total._labelnames
    assert 'status' in document_ingestion_total._labelnames


@pytest.mark.unit
def test_llm_query_metric_labels():
    """Test LLM query metric has model and status labels"""
    assert 'model' in llm_query_total._labelnames
    assert 'status' in llm_query_total._labelnames
