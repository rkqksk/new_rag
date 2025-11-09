"""
Unit tests for Prometheus metrics collection system.

Tests metrics collector, context managers, middleware integration,
and Prometheus exposition format.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from prometheus_client import CollectorRegistry

from app.core.metrics import (
    LLMQueryTracker,
    MetricsCollector,
    RequestTracker,
    get_metrics_collector,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestMetricsCollector:
    """Test metrics collector initialization and operations."""

    def test_metric_registration(self):
        """Test metric registration during initialization."""
        # Create isolated registry
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Verify all metric families are registered
        # Note: Prometheus client strips _total suffix from Counter names
        metric_names = [m.name for m in registry.collect()]

        # HTTP metrics (Counters lose _total suffix)
        assert "http_requests" in metric_names
        assert "http_request_duration_seconds" in metric_names
        assert "http_requests_in_flight" in metric_names
        assert "http_request_size_bytes" in metric_names
        assert "http_response_size_bytes" in metric_names

        # Claude API metrics (Counters lose _total suffix)
        assert "claude_api_calls" in metric_names
        assert "claude_api_duration_seconds" in metric_names
        assert "claude_tokens" in metric_names

        # RAG metrics
        assert "rag_pipeline_duration_seconds" in metric_names
        assert "rag_documents_retrieved" in metric_names
        assert "rag_confidence_scores" in metric_names

        # Database metrics (Counters lose _total suffix)
        assert "db_connections_active" in metric_names
        assert "db_query_duration_seconds" in metric_names
        assert "db_errors" in metric_names

        # Cache metrics (Counters lose _total suffix)
        assert "cache_operations" in metric_names
        assert "cache_hit_ratio" in metric_names

    def test_counter_increment(self):
        """Test counter metric increment."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Increment cache operation counter
        collector.record_cache_operation("get", "hit")
        collector.record_cache_operation("get", "hit")
        collector.record_cache_operation("get", "miss")

        # Get counter value (Prometheus strips _total suffix from metric family name)
        metrics = list(registry.collect())
        cache_ops = next((m for m in metrics if m.name == "cache_operations"), None)
        assert cache_ops is not None, "cache_operations metric not found"

        # Verify counts (filter for _total samples, not _created)
        samples = {
            (s.labels["operation"], s.labels["status"]): s.value
            for s in cache_ops.samples
            if s.name.endswith("_total")
        }

        assert samples[("get", "hit")] == 2.0
        assert samples[("get", "miss")] == 1.0

    def test_gauge_set(self):
        """Test gauge metric set operation."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Set gauge values
        collector.record_db_connection("postgresql", 10)
        collector.record_db_connection("redis", 5)

        # Get gauge values
        metrics = registry.collect()
        db_conns = next(m for m in metrics if m.name == "db_connections_active")

        # Verify values
        samples = {s.labels["db_type"]: s.value for s in db_conns.samples}

        assert samples["postgresql"] == 10.0
        assert samples["redis"] == 5.0

        # Update gauge
        collector.record_db_connection("postgresql", 15)

        metrics = registry.collect()
        db_conns = next(m for m in metrics if m.name == "db_connections_active")

        samples = {s.labels["db_type"]: s.value for s in db_conns.samples}

        assert samples["postgresql"] == 15.0

    def test_histogram_observe(self):
        """Test histogram metric observation."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Record database query durations
        collector.record_db_query("postgresql", 0.05)
        collector.record_db_query("postgresql", 0.15)
        collector.record_db_query("postgresql", 0.25)

        # Get histogram values
        metrics = registry.collect()
        db_query_hist = next(m for m in metrics if m.name == "db_query_duration_seconds")

        # Find count and sum for postgresql
        pg_samples = [s for s in db_query_hist.samples if s.labels.get("db_type") == "postgresql"]

        count_sample = next(s for s in pg_samples if s.name.endswith("_count"))
        sum_sample = next(s for s in pg_samples if s.name.endswith("_sum"))

        assert count_sample.value == 3.0
        assert sum_sample.value == pytest.approx(0.45, rel=0.01)


@pytest.mark.unit
@pytest.mark.asyncio
class TestContextManagers:
    """Test context manager implementations."""

    async def test_track_request_context(self):
        """Test request tracking context manager."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Track a request
        async with collector.track_request("/api/query", "POST") as tracker:
            tracker.set_status(200)
            tracker.add_request_size(1024)
            tracker.add_response_size(4096)

        # Verify metrics were recorded (Prometheus strips _total suffix)
        metrics = list(registry.collect())

        # Check requests total
        requests_total = next((m for m in metrics if m.name == "http_requests"), None)
        assert requests_total is not None, "http_requests metric not found"

        sample = next(
            (
                s
                for s in requests_total.samples
                if s.labels == {"method": "POST", "endpoint": "/api/query", "status_code": "200"}
            ),
            None,
        )
        assert sample is not None, "Expected sample not found"
        assert sample.value == 1.0

        # Check in-flight requests is back to 0
        in_flight = next((m for m in metrics if m.name == "http_requests_in_flight"), None)
        assert in_flight is not None, "http_requests_in_flight metric not found"
        assert in_flight.samples[0].value == 0.0

    async def test_track_llm_query_context(self):
        """Test LLM query tracking context manager."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Track an LLM query
        async with collector.track_llm_query("claude-3-opus-20240229") as tracker:
            tracker.set_status("success")
            tracker.add_tokens(100, 200)

        # Verify metrics were recorded (Prometheus strips _total suffix)
        metrics = list(registry.collect())

        # Check API calls total
        api_calls = next((m for m in metrics if m.name == "claude_api_calls"), None)
        assert api_calls is not None, "claude_api_calls metric not found"

        sample = next(
            (
                s
                for s in api_calls.samples
                if s.labels
                == {"model": "claude-3-opus-20240229", "endpoint": "messages", "status": "success"}
            ),
            None,
        )
        assert sample is not None, "Expected API call sample not found"
        assert sample.value == 1.0

        # Check tokens
        tokens = next((m for m in metrics if m.name == "claude_tokens"), None)
        assert tokens is not None, "claude_tokens metric not found"

        input_tokens = next(
            (
                s
                for s in tokens.samples
                if s.labels == {"model": "claude-3-opus-20240229", "direction": "input"}
            ),
            None,
        )
        output_tokens = next(
            (
                s
                for s in tokens.samples
                if s.labels == {"model": "claude-3-opus-20240229", "direction": "output"}
            ),
            None,
        )

        assert input_tokens is not None, "Input tokens sample not found"
        assert output_tokens is not None, "Output tokens sample not found"
        assert input_tokens.value == 100.0
        assert output_tokens.value == 200.0

    async def test_nested_contexts(self):
        """Test nested context managers."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Nested tracking
        async with collector.track_request("/api/query", "POST") as req:
            req.set_status(200)

            async with collector.track_llm_query("claude-3") as llm:
                llm.set_status("success")
                llm.add_tokens(50, 100)

            req.add_response_size(2048)

        # Verify both sets of metrics (Prometheus strips _total suffix)
        metrics = list(registry.collect())

        # HTTP metrics
        requests = next((m for m in metrics if m.name == "http_requests"), None)
        assert requests is not None, "http_requests metric not found"
        assert len([s for s in requests.samples if s.value > 0]) > 0

        # LLM metrics
        api_calls = next((m for m in metrics if m.name == "claude_api_calls"), None)
        assert api_calls is not None, "claude_api_calls metric not found"
        assert len([s for s in api_calls.samples if s.value > 0]) > 0

    async def test_exception_in_context(self):
        """Test exception handling in context managers."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Request with exception
        try:
            async with collector.track_request("/api/error") as tracker:
                tracker.add_request_size(512)
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Verify error was recorded with status 500 (Prometheus strips _total suffix)
        metrics = list(registry.collect())
        requests = next((m for m in metrics if m.name == "http_requests"), None)
        assert requests is not None, "http_requests metric not found"

        error_sample = next(
            (s for s in requests.samples if s.labels.get("status_code") == "500"), None
        )
        assert error_sample is not None, "Error sample with status 500 not found"
        assert error_sample.value == 1.0

        # LLM query with exception
        try:
            async with collector.track_llm_query("claude-3") as tracker:
                raise RuntimeError("API error")
        except RuntimeError:
            pass

        # Verify error status (Prometheus strips _total suffix)
        metrics = list(registry.collect())
        api_calls = next((m for m in metrics if m.name == "claude_api_calls"), None)
        assert api_calls is not None, "claude_api_calls metric not found"

        error_sample = next(
            (s for s in api_calls.samples if s.labels.get("status") == "error"), None
        )
        assert error_sample is not None, "Error sample not found"
        assert error_sample.value == 1.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestMiddlewareIntegration:
    """Test FastAPI middleware integration."""

    def test_middleware_initialization(self):
        """Test middleware creation."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        middleware = collector.get_middleware()

        assert middleware is not None
        assert middleware.__name__ == "MetricsMiddleware"

    async def test_request_metrics_collection(self):
        """Test automatic metrics collection via middleware."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        middleware_class = collector.get_middleware()

        # Create mock request and response
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = "1024"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.body = b"x" * 2048

        # Mock call_next
        async def mock_call_next(request):
            return mock_response

        # Create middleware instance
        middleware = middleware_class(app=MagicMock())

        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response == mock_response

        # Verify metrics were collected (Prometheus strips _total suffix)
        metrics = list(registry.collect())

        requests_total = next((m for m in metrics if m.name == "http_requests"), None)
        assert requests_total is not None, "http_requests metric not found"

        sample = next(
            (s for s in requests_total.samples if s.labels.get("endpoint") == "/api/test"), None
        )
        assert sample is not None, "Expected sample not found"
        assert sample.value == 1.0

    async def test_error_handling(self):
        """Test middleware error handling."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        middleware_class = collector.get_middleware()

        # Create mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/error"
        mock_request.method = "POST"
        mock_request.headers.get.return_value = "0"

        # Mock call_next that raises exception
        async def mock_call_next_error(request):
            raise RuntimeError("Internal error")

        # Create middleware instance
        middleware = middleware_class(app=MagicMock())

        # Process request (should not raise)
        try:
            await middleware.dispatch(mock_request, mock_call_next_error)
        except RuntimeError:
            # Exception should propagate but metrics should be recorded
            pass

        # Verify error metrics (Prometheus strips _total suffix)
        metrics = list(registry.collect())

        requests_total = next((m for m in metrics if m.name == "http_requests"), None)
        assert requests_total is not None, "http_requests metric not found"

        error_sample = next(
            (s for s in requests_total.samples if s.labels.get("status_code") == "500"), None
        )
        assert error_sample is not None, "Error sample not found"


@pytest.mark.unit
class TestPrometheusExposition:
    """Test Prometheus exposition format."""

    def test_metrics_format(self):
        """Test Prometheus text format output."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        # Record some metrics
        collector.record_cache_operation("get", "hit")
        collector.record_db_connection("postgresql", 5)

        # Generate metrics
        output = collector.generate_metrics()

        # Verify format
        assert isinstance(output, bytes)
        text = output.decode("utf-8")

        # Check for metric presence
        assert "cache_operations_total" in text
        assert "db_connections_active" in text

        # Check for labels
        assert 'operation="get"' in text
        assert 'status="hit"' in text
        assert 'db_type="postgresql"' in text

    def test_content_type(self):
        """Test metrics content type."""
        registry = CollectorRegistry()
        collector = MetricsCollector(registry=registry)

        output = collector.generate_metrics()

        # Prometheus expects text format
        text = output.decode("utf-8")

        # Should contain TYPE and HELP comments
        assert "# HELP" in text
        assert "# TYPE" in text


@pytest.mark.unit
def test_singleton_pattern():
    """Test global metrics collector singleton."""
    # Get collector twice
    collector1 = get_metrics_collector()
    collector2 = get_metrics_collector()

    # Should be same instance
    assert collector1 is collector2


@pytest.mark.unit
async def test_rag_pipeline_metrics():
    """Test RAG pipeline metrics recording."""
    registry = CollectorRegistry()
    collector = MetricsCollector(registry=registry)

    # Record RAG pipeline metrics
    collector.record_rag_pipeline(
        duration_seconds=1.5, documents_retrieved=10, confidence_score=0.85
    )

    # Verify metrics
    metrics = list(registry.collect())

    # Check documents retrieved gauge
    docs_retrieved = next((m for m in metrics if m.name == "rag_documents_retrieved"), None)
    assert docs_retrieved is not None, "rag_documents_retrieved metric not found"
    assert docs_retrieved.samples[0].value == 10.0

    # Check duration histogram
    duration_hist = next((m for m in metrics if m.name == "rag_pipeline_duration_seconds"), None)
    assert duration_hist is not None, "rag_pipeline_duration_seconds metric not found"

    count_sample = next((s for s in duration_hist.samples if s.name.endswith("_count")), None)
    assert count_sample is not None, "Duration count sample not found"
    assert count_sample.value == 1.0

    # Check confidence score histogram
    confidence_hist = next((m for m in metrics if m.name == "rag_confidence_scores"), None)
    assert confidence_hist is not None, "rag_confidence_scores metric not found"

    count_sample = next((s for s in confidence_hist.samples if s.name.endswith("_count")), None)
    assert count_sample is not None, "Confidence count sample not found"
    assert count_sample.value == 1.0


@pytest.mark.unit
def test_cache_hit_ratio_update():
    """Test cache hit ratio metric update."""
    registry = CollectorRegistry()
    collector = MetricsCollector(registry=registry)

    # Update hit ratio
    collector.update_cache_hit_ratio(0.75)

    # Verify metric
    metrics = registry.collect()
    hit_ratio = next(m for m in metrics if m.name == "cache_hit_ratio")

    assert hit_ratio.samples[0].value == 0.75

    # Update again
    collector.update_cache_hit_ratio(0.85)

    metrics = registry.collect()
    hit_ratio = next(m for m in metrics if m.name == "cache_hit_ratio")

    assert hit_ratio.samples[0].value == 0.85


@pytest.mark.unit
def test_database_error_recording():
    """Test database error counter."""
    registry = CollectorRegistry()
    collector = MetricsCollector(registry=registry)

    # Record errors
    collector.record_db_error("postgresql", "connection_timeout")
    collector.record_db_error("postgresql", "connection_timeout")
    collector.record_db_error("redis", "connection_refused")

    # Verify metrics (Prometheus strips _total suffix from metric family name)
    metrics = list(registry.collect())
    db_errors = next((m for m in metrics if m.name == "db_errors"), None)
    assert db_errors is not None, "db_errors metric not found"

    # Check error counts (filter for _total samples, not _created)
    samples = {
        (s.labels["db_type"], s.labels["error_type"]): s.value
        for s in db_errors.samples
        if s.name.endswith("_total")
    }

    assert samples[("postgresql", "connection_timeout")] == 2.0
    assert samples[("redis", "connection_refused")] == 1.0
