"""
Prometheus metrics collection system for RAG Enterprise.

This module provides comprehensive metrics collection for monitoring
application performance, API usage, and system health. Metrics are
exposed in Prometheus exposition format.

Classes:
    MetricsCollector: Thread-safe metrics collection and management
    RequestTracker: Context manager for HTTP request tracking
    LLMQueryTracker: Context manager for LLM query tracking

Example:
    >>> collector = MetricsCollector()
    >>> async with collector.track_request("/api/query") as tracker:
    ...     tracker.set_status(200)
    ...     tracker.add_size(4096)
"""

import asyncio
import time
from contextlib import asynccontextmanager
from threading import Lock
from typing import Any, Dict, Optional

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestTracker:
    """Context manager for tracking HTTP request metrics.

    Attributes:
        collector: Parent metrics collector
        endpoint: Request endpoint path
        method: HTTP method
        start_time: Request start timestamp
        status_code: HTTP response status code
        request_size: Request body size in bytes
        response_size: Response body size in bytes
    """

    def __init__(
        self,
        collector: "MetricsCollector",
        endpoint: str,
        method: str = "GET"
    ):
        """Initialize request tracker.

        Args:
            collector: Parent metrics collector instance
            endpoint: Request endpoint path
            method: HTTP method (default: GET)
        """
        self.collector = collector
        self.endpoint = endpoint
        self.method = method
        self.start_time = time.time()
        self.status_code: Optional[int] = None
        self.request_size: int = 0
        self.response_size: int = 0

    def set_status(self, status_code: int) -> None:
        """Set HTTP response status code.

        Args:
            status_code: HTTP status code
        """
        self.status_code = status_code

    def add_request_size(self, size_bytes: int) -> None:
        """Add request body size.

        Args:
            size_bytes: Request size in bytes
        """
        self.request_size = size_bytes

    def add_response_size(self, size_bytes: int) -> None:
        """Add response body size.

        Args:
            size_bytes: Response size in bytes
        """
        self.response_size = size_bytes

    def add_size(self, size_bytes: int) -> None:
        """Add size (alias for add_response_size).

        Args:
            size_bytes: Response size in bytes
        """
        self.add_response_size(size_bytes)

    async def __aenter__(self) -> "RequestTracker":
        """Enter async context manager.

        Returns:
            RequestTracker instance
        """
        # Increment in-flight requests
        self.collector._http_requests_in_flight.inc()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any
    ) -> None:
        """Exit async context manager and record metrics.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        # Decrement in-flight requests
        self.collector._http_requests_in_flight.dec()

        # Calculate duration
        duration = time.time() - self.start_time

        # Determine status code
        if exc_type is not None:
            status = 500
        else:
            status = self.status_code or 200

        # Record metrics
        self.collector._http_requests_total.labels(
            method=self.method,
            endpoint=self.endpoint,
            status_code=status
        ).inc()

        self.collector._http_request_duration_seconds.labels(
            endpoint=self.endpoint
        ).observe(duration)

        if self.request_size > 0:
            self.collector._http_request_size_bytes.labels(
                endpoint=self.endpoint
            ).observe(self.request_size)

        if self.response_size > 0:
            self.collector._http_response_size_bytes.labels(
                endpoint=self.endpoint
            ).observe(self.response_size)


class LLMQueryTracker:
    """Context manager for tracking LLM query metrics.

    Attributes:
        collector: Parent metrics collector
        model: LLM model name
        endpoint: API endpoint
        start_time: Query start timestamp
        status: Query status (success/error)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """

    def __init__(
        self,
        collector: "MetricsCollector",
        model: str,
        endpoint: str = "messages"
    ):
        """Initialize LLM query tracker.

        Args:
            collector: Parent metrics collector instance
            model: LLM model name
            endpoint: API endpoint (default: messages)
        """
        self.collector = collector
        self.model = model
        self.endpoint = endpoint
        self.start_time = time.time()
        self.status: str = "success"
        self.input_tokens: int = 0
        self.output_tokens: int = 0

    def set_status(self, status: str) -> None:
        """Set query status.

        Args:
            status: Query status (success/error/timeout)
        """
        self.status = status

    def add_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Add token counts.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    async def __aenter__(self) -> "LLMQueryTracker":
        """Enter async context manager.

        Returns:
            LLMQueryTracker instance
        """
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any
    ) -> None:
        """Exit async context manager and record metrics.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        # Calculate duration
        duration = time.time() - self.start_time

        # Determine status
        if exc_type is not None:
            status = "error"
        else:
            status = self.status

        # Record metrics
        self.collector._claude_api_calls_total.labels(
            model=self.model,
            endpoint=self.endpoint,
            status=status
        ).inc()

        self.collector._claude_api_duration_seconds.labels(
            model=self.model
        ).observe(duration)

        if self.input_tokens > 0:
            self.collector._claude_tokens_total.labels(
                model=self.model,
                direction="input"
            ).inc(self.input_tokens)

        if self.output_tokens > 0:
            self.collector._claude_tokens_total.labels(
                model=self.model,
                direction="output"
            ).inc(self.output_tokens)


class MetricsCollector:
    """Thread-safe Prometheus metrics collector.

    Provides comprehensive metrics collection for HTTP requests,
    Claude API calls, RAG pipeline operations, database queries,
    and cache operations.

    Attributes:
        registry: Prometheus collector registry
        _lock: Thread lock for metric registration
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics collector.

        Args:
            registry: Prometheus registry (default: global REGISTRY)
        """
        self.registry = registry or REGISTRY
        self._lock = Lock()
        self.logger = get_logger(__name__)

        # Initialize all metrics
        self._initialize_http_metrics()
        self._initialize_claude_metrics()
        self._initialize_rag_metrics()
        self._initialize_database_metrics()
        self._initialize_cache_metrics()

        self.logger.info("Metrics collector initialized")

    def _initialize_http_metrics(self) -> None:
        """Initialize HTTP request metrics."""
        with self._lock:
            self._http_requests_total = Counter(
                "http_requests_total",
                "Total HTTP requests by method, endpoint, and status",
                ["method", "endpoint", "status_code"],
                registry=self.registry
            )

            self._http_request_duration_seconds = Histogram(
                "http_request_duration_seconds",
                "HTTP request duration in seconds",
                ["endpoint"],
                registry=self.registry,
                buckets=(
                    0.005, 0.01, 0.025, 0.05, 0.1,
                    0.25, 0.5, 1.0, 2.5, 5.0, 10.0
                )
            )

            self._http_requests_in_flight = Gauge(
                "http_requests_in_flight",
                "Number of HTTP requests currently being processed",
                registry=self.registry
            )

            self._http_request_size_bytes = Histogram(
                "http_request_size_bytes",
                "HTTP request body size in bytes",
                ["endpoint"],
                registry=self.registry,
                buckets=(
                    100, 1000, 10000, 100000,
                    1000000, 10000000
                )
            )

            self._http_response_size_bytes = Histogram(
                "http_response_size_bytes",
                "HTTP response body size in bytes",
                ["endpoint"],
                registry=self.registry,
                buckets=(
                    100, 1000, 10000, 100000,
                    1000000, 10000000
                )
            )

    def _initialize_claude_metrics(self) -> None:
        """Initialize Claude API metrics."""
        with self._lock:
            self._claude_api_calls_total = Counter(
                "claude_api_calls_total",
                "Total Claude API calls by model, endpoint, and status",
                ["model", "endpoint", "status"],
                registry=self.registry
            )

            self._claude_api_duration_seconds = Histogram(
                "claude_api_duration_seconds",
                "Claude API request duration in seconds",
                ["model"],
                registry=self.registry,
                buckets=(
                    0.1, 0.25, 0.5, 1.0, 2.0,
                    5.0, 10.0, 30.0, 60.0
                )
            )

            self._claude_tokens_total = Counter(
                "claude_tokens_total",
                "Total Claude API tokens by model and direction",
                ["model", "direction"],
                registry=self.registry
            )

    def _initialize_rag_metrics(self) -> None:
        """Initialize RAG pipeline metrics."""
        with self._lock:
            self._rag_pipeline_duration_seconds = Histogram(
                "rag_pipeline_duration_seconds",
                "RAG pipeline execution duration in seconds",
                registry=self.registry,
                buckets=(
                    0.1, 0.25, 0.5, 1.0, 2.0,
                    5.0, 10.0, 30.0
                )
            )

            self._rag_documents_retrieved = Gauge(
                "rag_documents_retrieved",
                "Number of documents retrieved in last RAG query",
                registry=self.registry
            )

            self._rag_confidence_scores = Histogram(
                "rag_confidence_scores",
                "RAG query confidence scores",
                registry=self.registry,
                buckets=(
                    0.1, 0.2, 0.3, 0.4, 0.5,
                    0.6, 0.7, 0.8, 0.9, 1.0
                )
            )

    def _initialize_database_metrics(self) -> None:
        """Initialize database metrics."""
        with self._lock:
            self._db_connections_active = Gauge(
                "db_connections_active",
                "Number of active database connections",
                ["db_type"],
                registry=self.registry
            )

            self._db_query_duration_seconds = Histogram(
                "db_query_duration_seconds",
                "Database query duration in seconds",
                ["db_type"],
                registry=self.registry,
                buckets=(
                    0.001, 0.005, 0.01, 0.025, 0.05,
                    0.1, 0.25, 0.5, 1.0, 5.0
                )
            )

            self._db_errors_total = Counter(
                "db_errors_total",
                "Total database errors by type",
                ["db_type", "error_type"],
                registry=self.registry
            )

    def _initialize_cache_metrics(self) -> None:
        """Initialize cache metrics."""
        with self._lock:
            self._cache_operations_total = Counter(
                "cache_operations_total",
                "Total cache operations by operation and status",
                ["operation", "status"],
                registry=self.registry
            )

            self._cache_hit_ratio = Gauge(
                "cache_hit_ratio",
                "Cache hit ratio (0.0 to 1.0)",
                registry=self.registry
            )

    @asynccontextmanager
    async def track_request(
        self,
        endpoint: str,
        method: str = "GET"
    ):
        """Track HTTP request metrics.

        Args:
            endpoint: Request endpoint path
            method: HTTP method (default: GET)

        Yields:
            RequestTracker instance

        Example:
            >>> async with collector.track_request("/api/query") as t:
            ...     t.set_status(200)
            ...     t.add_size(4096)
        """
        tracker = RequestTracker(self, endpoint, method)
        async with tracker:
            yield tracker

    @asynccontextmanager
    async def track_llm_query(
        self,
        model: str,
        endpoint: str = "messages"
    ):
        """Track LLM query metrics.

        Args:
            model: LLM model name
            endpoint: API endpoint (default: messages)

        Yields:
            LLMQueryTracker instance

        Example:
            >>> async with collector.track_llm_query("claude-3") as t:
            ...     t.set_status("success")
            ...     t.add_tokens(100, 200)
        """
        tracker = LLMQueryTracker(self, model, endpoint)
        async with tracker:
            yield tracker

    def record_rag_pipeline(
        self,
        duration_seconds: float,
        documents_retrieved: int,
        confidence_score: float
    ) -> None:
        """Record RAG pipeline metrics.

        Args:
            duration_seconds: Pipeline execution duration
            documents_retrieved: Number of documents retrieved
            confidence_score: Query confidence score (0.0 to 1.0)
        """
        self._rag_pipeline_duration_seconds.observe(duration_seconds)
        self._rag_documents_retrieved.set(documents_retrieved)
        self._rag_confidence_scores.observe(confidence_score)

    def record_db_connection(self, db_type: str, count: int) -> None:
        """Record database connection count.

        Args:
            db_type: Database type (postgresql, redis, qdrant)
            count: Number of active connections
        """
        self._db_connections_active.labels(db_type=db_type).set(count)

    def record_db_query(
        self,
        db_type: str,
        duration_seconds: float
    ) -> None:
        """Record database query duration.

        Args:
            db_type: Database type (postgresql, redis, qdrant)
            duration_seconds: Query execution duration
        """
        self._db_query_duration_seconds.labels(
            db_type=db_type
        ).observe(duration_seconds)

    def record_db_error(
        self,
        db_type: str,
        error_type: str
    ) -> None:
        """Record database error.

        Args:
            db_type: Database type (postgresql, redis, qdrant)
            error_type: Error classification
        """
        self._db_errors_total.labels(
            db_type=db_type,
            error_type=error_type
        ).inc()

    def record_cache_operation(
        self,
        operation: str,
        status: str
    ) -> None:
        """Record cache operation.

        Args:
            operation: Cache operation (get, set, delete)
            status: Operation status (hit, miss, error)
        """
        self._cache_operations_total.labels(
            operation=operation,
            status=status
        ).inc()

    def update_cache_hit_ratio(self, ratio: float) -> None:
        """Update cache hit ratio metric.

        Args:
            ratio: Hit ratio (0.0 to 1.0)
        """
        self._cache_hit_ratio.set(ratio)

    def generate_metrics(self) -> bytes:
        """Generate Prometheus exposition format metrics.

        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(self.registry)

    def get_middleware(self):
        """Get FastAPI middleware for automatic request tracking.

        Returns:
            Starlette BaseHTTPMiddleware instance

        Example:
            >>> app.add_middleware(collector.get_middleware())
        """
        collector = self

        class MetricsMiddleware(BaseHTTPMiddleware):
            """FastAPI middleware for automatic metrics collection."""

            async def dispatch(
                self,
                request: Request,
                call_next
            ) -> Response:
                """Process request and collect metrics.

                Args:
                    request: Incoming HTTP request
                    call_next: Next middleware in chain

                Returns:
                    HTTP response
                """
                # Extract endpoint and method
                endpoint = request.url.path
                method = request.method

                # Get request size
                request_size = int(
                    request.headers.get("content-length", 0)
                )

                # Track request
                async with collector.track_request(
                    endpoint,
                    method
                ) as tracker:
                    tracker.add_request_size(request_size)

                    # Process request
                    response = await call_next(request)

                    # Record response metrics
                    tracker.set_status(response.status_code)

                    # Get response size if available
                    if hasattr(response, "body"):
                        tracker.add_response_size(len(response.body))

                    return response

        return MetricsMiddleware


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None
_collector_lock = Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance.

    Returns:
        MetricsCollector singleton instance
    """
    global _metrics_collector

    if _metrics_collector is None:
        with _collector_lock:
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()

    return _metrics_collector
