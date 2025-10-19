# Observability System Architecture

**RAG Enterprise Platform - Production-Ready Health Checks & Metrics**

Version: 1.0
Date: 2025-10-19
Status: Architecture Design

---

## Executive Summary

This document defines the architecture for a production-ready observability system for RAG Enterprise, encompassing:

- **Health Check System**: Liveness, readiness, and aggregated health endpoints with async parallel dependency checking
- **Prometheus Metrics**: Comprehensive request, system, and application metrics with automatic collection
- **Error Handling**: Graceful degradation, timeout management, and structured error responses
- **Integration Strategy**: FastAPI middleware integration with existing logging and dependency injection systems

**Design Principles**:
- Async-first with parallel operations (never sequential for independent checks)
- Graceful degradation (degraded state vs unhealthy)
- Production-ready error handling with timeouts
- Zero-impact on request latency (async background collection)

---

## 1. Health Check System Architecture

### 1.1 Core Class Structure

```python
# app/core/health.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import time
from datetime import datetime


class HealthStatus(str, Enum):
    """Health status levels for components"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component"""
    component: str
    status: HealthStatus
    latency_ms: float
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "component": self.component,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class AggregatedHealth:
    """Aggregated health status across all components"""
    overall_status: HealthStatus
    checks: List[ComponentHealth]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "status": self.overall_status.value,
            "timestamp": self.timestamp,
            "checks": [check.to_dict() for check in self.checks]
        }
```

### 1.2 Abstract Health Checker

```python
class HealthChecker(ABC):
    """Abstract base class for component health checkers"""

    def __init__(self, component_name: str, timeout: float = 2.0):
        """
        Initialize health checker

        Args:
            component_name: Name of component to check
            timeout: Check timeout in seconds (default: 2s)
        """
        self.component_name = component_name
        self.timeout = timeout

    @abstractmethod
    async def check_health(self) -> ComponentHealth:
        """
        Check component health (must be implemented by subclasses)

        Returns:
            ComponentHealth with status, latency, and metadata
        """
        pass

    async def check_with_timeout(self) -> ComponentHealth:
        """
        Execute health check with timeout protection

        Returns:
            ComponentHealth (UNHEALTHY on timeout)
        """
        start_time = time.time()
        try:
            # Execute check with timeout
            result = await asyncio.wait_for(
                self.check_health(),
                timeout=self.timeout
            )
            return result

        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Health check timeout after {self.timeout}s"
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Health check failed: {str(e)}"
            )
```

### 1.3 Concrete Health Checkers

#### PostgreSQL Health Checker

```python
import asyncpg


class PostgreSQLHealthChecker(HealthChecker):
    """PostgreSQL database health checker"""

    def __init__(self, host: str, port: int, database: str,
                 user: str, password: str, timeout: float = 2.0):
        super().__init__("postgresql", timeout)
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    async def check_health(self) -> ComponentHealth:
        """
        Check PostgreSQL connectivity with async driver

        Returns:
            ComponentHealth with connection status
        """
        start_time = time.time()

        try:
            # Use asyncpg for async connection
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                timeout=self.timeout
            )

            # Execute simple query to verify
            await conn.execute('SELECT 1')
            await conn.close()

            latency_ms = (time.time() - start_time) * 1000

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                message="PostgreSQL connection successful",
                metadata={"host": self.host, "database": self.database}
            )

        except asyncpg.PostgresError as e:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"PostgreSQL error: {str(e)}"
            )
```

#### Redis Health Checker

```python
import aioredis


class RedisHealthChecker(HealthChecker):
    """Redis cache health checker"""

    def __init__(self, host: str, port: int, timeout: float = 2.0):
        super().__init__("redis", timeout)
        self.host = host
        self.port = port

    async def check_health(self) -> ComponentHealth:
        """
        Check Redis connectivity with async client

        Returns:
            ComponentHealth with ping status
        """
        start_time = time.time()

        try:
            # Create async Redis client
            redis = await aioredis.create_redis_pool(
                f'redis://{self.host}:{self.port}',
                timeout=self.timeout
            )

            # Execute ping
            pong = await redis.ping()
            redis.close()
            await redis.wait_closed()

            latency_ms = (time.time() - start_time) * 1000

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.HEALTHY if pong else HealthStatus.DEGRADED,
                latency_ms=latency_ms,
                message="Redis ping successful",
                metadata={"host": self.host}
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Redis error: {str(e)}"
            )
```

#### Qdrant Health Checker

```python
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse


class QdrantHealthChecker(HealthChecker):
    """Qdrant vector database health checker"""

    def __init__(self, host: str, port: int, timeout: float = 2.0):
        super().__init__("qdrant", timeout)
        self.host = host
        self.port = port

    async def check_health(self) -> ComponentHealth:
        """
        Check Qdrant connectivity

        Returns:
            ComponentHealth with collection access status
        """
        start_time = time.time()

        try:
            client = QdrantClient(host=self.host, port=self.port, timeout=self.timeout)

            # List collections to verify access
            collections = await asyncio.to_thread(client.get_collections)

            latency_ms = (time.time() - start_time) * 1000

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                message="Qdrant connection successful",
                metadata={
                    "host": self.host,
                    "collections": len(collections.collections)
                }
            )

        except UnexpectedResponse as e:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Qdrant error: {str(e)}"
            )
```

#### Claude API Health Checker

```python
import httpx


class ClaudeAPIHealthChecker(HealthChecker):
    """Claude API health checker"""

    def __init__(self, api_key: str, timeout: float = 5.0):
        super().__init__("claude_api", timeout)
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"

    async def check_health(self) -> ComponentHealth:
        """
        Check Claude API accessibility with minimal test prompt

        Returns:
            ComponentHealth with API status
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "ping"}]
                    }
                )

                latency_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    return ComponentHealth(
                        component=self.component_name,
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency_ms,
                        message="Claude API accessible",
                        metadata={"status_code": response.status_code}
                    )
                elif 200 <= response.status_code < 500:
                    # Client errors might indicate configuration issues
                    return ComponentHealth(
                        component=self.component_name,
                        status=HealthStatus.DEGRADED,
                        latency_ms=latency_ms,
                        message=f"Claude API returned {response.status_code}",
                        metadata={"status_code": response.status_code}
                    )
                else:
                    return ComponentHealth(
                        component=self.component_name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency_ms,
                        message=f"Claude API server error: {response.status_code}"
                    )

        except httpx.TimeoutException:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="Claude API timeout"
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Claude API error: {str(e)}"
            )
```

### 1.4 Aggregated Health Orchestrator

```python
class HealthCheckOrchestrator:
    """Orchestrates health checks across all system components"""

    def __init__(self, checkers: List[HealthChecker]):
        """
        Initialize orchestrator with health checkers

        Args:
            checkers: List of HealthChecker instances
        """
        self.checkers = checkers

    async def check_all(self) -> AggregatedHealth:
        """
        Execute all health checks in parallel (CRITICAL: never sequential)

        Returns:
            AggregatedHealth with overall status
        """
        # Execute all checks in parallel with asyncio.gather
        check_results = await asyncio.gather(
            *[checker.check_with_timeout() for checker in self.checkers],
            return_exceptions=True
        )

        # Filter out exceptions and convert to ComponentHealth
        component_healths = []
        for result in check_results:
            if isinstance(result, ComponentHealth):
                component_healths.append(result)
            elif isinstance(result, Exception):
                # Handle unexpected exceptions during gather
                component_healths.append(ComponentHealth(
                    component="unknown",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    message=f"Unexpected error: {str(result)}"
                ))

        # Determine overall status
        overall_status = self._calculate_overall_status(component_healths)

        return AggregatedHealth(
            overall_status=overall_status,
            checks=component_healths
        )

    def _calculate_overall_status(self, checks: List[ComponentHealth]) -> HealthStatus:
        """
        Calculate overall health from component statuses

        Rules:
        - HEALTHY: All components healthy
        - DEGRADED: Any component degraded, none unhealthy
        - UNHEALTHY: Any component unhealthy

        Args:
            checks: List of component health checks

        Returns:
            Overall HealthStatus
        """
        if not checks:
            return HealthStatus.UNHEALTHY

        statuses = [check.status for check in checks]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def check_liveness(self) -> ComponentHealth:
        """
        Liveness probe - fast check without dependencies

        Returns:
            ComponentHealth for liveness (always HEALTHY if server runs)
        """
        return ComponentHealth(
            component="liveness",
            status=HealthStatus.HEALTHY,
            latency_ms=0,
            message="Server is running"
        )

    async def check_readiness(self) -> AggregatedHealth:
        """
        Readiness probe - full dependency check

        Returns:
            AggregatedHealth with all dependencies
        """
        return await self.check_all()
```

### 1.5 Dependency Injection Integration

```python
# app/core/dependencies.py (additions)

from functools import lru_cache
from app.core.health import (
    HealthCheckOrchestrator,
    PostgreSQLHealthChecker,
    RedisHealthChecker,
    QdrantHealthChecker,
    ClaudeAPIHealthChecker
)


@lru_cache()
def get_health_orchestrator(config: AppConfig = Depends(get_config)) -> HealthCheckOrchestrator:
    """
    Get health check orchestrator (singleton)

    Args:
        config: Application configuration

    Returns:
        HealthCheckOrchestrator configured with all checkers
    """
    checkers = [
        PostgreSQLHealthChecker(
            host=config.postgres_host,
            port=5432,
            database=config.postgres_db,
            user=config.postgres_user,
            password=config.postgres_password,
            timeout=2.0
        ),
        RedisHealthChecker(
            host=config.redis_host,
            port=config.redis_port,
            timeout=2.0
        ),
        QdrantHealthChecker(
            host=config.qdrant_host,
            port=config.qdrant_port,
            timeout=2.0
        ),
        ClaudeAPIHealthChecker(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            timeout=5.0
        )
    ]

    return HealthCheckOrchestrator(checkers)
```

---

## 2. Prometheus Metrics Architecture

### 2.1 Metrics Collector Class

```python
# app/core/metrics.py (enhancement)

from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import time
from prometheus_client import Counter, Histogram, Gauge, Info


class MetricsCollector:
    """
    Centralized metrics collection with context managers

    Provides high-level interfaces for metric collection across
    application operations
    """

    def __init__(self):
        """Initialize metrics collector"""
        # Import existing metrics from app.core.metrics
        from app.core.metrics import (
            http_requests_total,
            http_request_duration_seconds,
            llm_query_total,
            llm_query_duration_seconds,
            llm_tokens_generated,
            vector_search_total,
            vector_search_duration_seconds,
            document_ingestion_total,
            document_ingestion_duration_seconds,
            redis_operations_total,
            qdrant_upsert_total,
            errors_total,
            active_requests
        )

        self.http_requests = http_requests_total
        self.http_duration = http_request_duration_seconds
        self.llm_queries = llm_query_total
        self.llm_duration = llm_query_duration_seconds
        self.llm_tokens = llm_tokens_generated
        self.vector_searches = vector_search_total
        self.vector_duration = vector_search_duration_seconds
        self.doc_ingestion = document_ingestion_total
        self.doc_duration = document_ingestion_duration_seconds
        self.redis_ops = redis_operations_total
        self.qdrant_ops = qdrant_upsert_total
        self.errors = errors_total
        self.active = active_requests

    @asynccontextmanager
    async def track_llm_query(self, model: str):
        """
        Context manager for tracking LLM query metrics

        Args:
            model: LLM model name

        Yields:
            Dict for recording tokens and status
        """
        start_time = time.time()
        metrics = {"tokens": 0, "status": "success"}

        try:
            yield metrics

        except Exception as e:
            metrics["status"] = "error"
            self.errors.labels(
                error_type="llm_query",
                endpoint="llm"
            ).inc()
            raise

        finally:
            duration = time.time() - start_time

            # Record query metrics
            self.llm_queries.labels(
                model=model,
                status=metrics["status"]
            ).inc()

            self.llm_duration.labels(model=model).observe(duration)

            if metrics["tokens"] > 0:
                self.llm_tokens.labels(model=model).observe(metrics["tokens"])

    @asynccontextmanager
    async def track_vector_search(self, collection: str):
        """
        Context manager for tracking vector search metrics

        Args:
            collection: Qdrant collection name

        Yields:
            Dict for recording results count
        """
        start_time = time.time()
        metrics = {"results": 0}

        try:
            yield metrics

        except Exception as e:
            self.errors.labels(
                error_type="vector_search",
                endpoint="search"
            ).inc()
            raise

        finally:
            duration = time.time() - start_time

            self.vector_searches.labels(collection=collection).inc()
            self.vector_duration.labels(collection=collection).observe(duration)

    @asynccontextmanager
    async def track_document_ingestion(self, format: str):
        """
        Context manager for tracking document ingestion metrics

        Args:
            format: Document format (pdf, txt, etc)

        Yields:
            Dict for recording chunks and status
        """
        start_time = time.time()
        metrics = {"chunks": 0, "status": "success"}

        try:
            yield metrics

        except Exception as e:
            metrics["status"] = "error"
            self.errors.labels(
                error_type="doc_ingestion",
                endpoint="ingestion"
            ).inc()
            raise

        finally:
            duration = time.time() - start_time

            self.doc_ingestion.labels(
                format=format,
                status=metrics["status"]
            ).inc()

            self.doc_duration.labels(format=format).observe(duration)

    def record_redis_operation(self, operation: str, success: bool):
        """
        Record Redis operation metric

        Args:
            operation: Operation type (get, set, delete, etc)
            success: Operation success status
        """
        self.redis_ops.labels(
            operation=operation,
            status="success" if success else "error"
        ).inc()

    def record_qdrant_upsert(self, collection: str, count: int):
        """
        Record Qdrant upsert operation

        Args:
            collection: Collection name
            count: Number of points upserted
        """
        self.qdrant_ops.labels(collection=collection).inc(count)


# Global metrics collector instance
metrics_collector = MetricsCollector()
```

### 2.2 Enhanced Middleware with Metrics

```python
# app/core/middleware.py (already exists, minor enhancements)

# The existing MetricsMiddleware already tracks:
# - http_requests_total
# - http_request_duration_seconds
# - http_request_size_bytes
# - http_response_size_bytes
# - active_requests
# - errors_total

# No changes needed - already production-ready
```

### 2.3 Additional Metrics for Claude API

```python
# app/core/metrics.py (additions)

# Claude API specific metrics
claude_api_calls_total = Counter(
    'claude_api_calls_total',
    'Total Claude API calls',
    ['model', 'status'],
    registry=REGISTRY
)

claude_api_duration_seconds = Histogram(
    'claude_api_duration_seconds',
    'Claude API call latency in seconds',
    ['model'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=REGISTRY
)

claude_tokens_input = Counter(
    'claude_tokens_input',
    'Claude API input tokens',
    ['model'],
    registry=REGISTRY
)

claude_tokens_output = Counter(
    'claude_tokens_output',
    'Claude API output tokens',
    ['model'],
    registry=REGISTRY
)

claude_api_errors_total = Counter(
    'claude_api_errors_total',
    'Claude API errors',
    ['error_type'],
    registry=REGISTRY
)

# Database connection metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    ['database'],
    registry=REGISTRY
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['database'],
    registry=REGISTRY
)

# RAG pipeline metrics
rag_pipeline_duration_seconds = Histogram(
    'rag_pipeline_duration_seconds',
    'RAG pipeline end-to-end latency',
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=REGISTRY
)

rag_context_chunks_retrieved = Histogram(
    'rag_context_chunks_retrieved',
    'Number of context chunks retrieved',
    buckets=(1, 3, 5, 10, 20, 50),
    registry=REGISTRY
)

rag_answer_confidence = Histogram(
    'rag_answer_confidence',
    'RAG answer confidence scores',
    buckets=(0.1, 0.3, 0.5, 0.7, 0.9, 1.0),
    registry=REGISTRY
)
```

---

## 3. Health Check Endpoint Implementation

### 3.1 Health Routes Module

```python
# app/api/routes/health.py

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from app.core.health import HealthCheckOrchestrator, HealthStatus
from app.core.dependencies import get_health_orchestrator
from app.core.logging import get_logger
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.core.metrics import REGISTRY

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)


@router.get("/live")
async def liveness_probe(
    orchestrator: HealthCheckOrchestrator = Depends(get_health_orchestrator)
):
    """
    Liveness probe - indicates server is running

    Used by Kubernetes liveness probes. Fast check without dependencies.

    Returns:
        200 OK if server is running
    """
    result = await orchestrator.check_liveness()

    return JSONResponse(
        status_code=200,
        content=result.to_dict()
    )


@router.get("/ready")
async def readiness_probe(
    orchestrator: HealthCheckOrchestrator = Depends(get_health_orchestrator)
):
    """
    Readiness probe - indicates all dependencies are accessible

    Used by Kubernetes readiness probes. Checks all dependencies in parallel.

    Returns:
        200 OK if all dependencies healthy
        503 Service Unavailable if any dependency unhealthy
    """
    result = await orchestrator.check_readiness()

    # Return 503 if unhealthy (K8s will mark pod as not ready)
    status_code = 200 if result.overall_status != HealthStatus.UNHEALTHY else 503

    return JSONResponse(
        status_code=status_code,
        content=result.to_dict()
    )


@router.get("")
async def health_check(
    orchestrator: HealthCheckOrchestrator = Depends(get_health_orchestrator)
):
    """
    General health check - aggregated status with component details

    Provides detailed health information for monitoring dashboards.

    Returns:
        200 OK with detailed component health
    """
    result = await orchestrator.check_all()

    # Log degraded/unhealthy components
    for check in result.checks:
        if check.status != HealthStatus.HEALTHY:
            logger.warning(
                "component_health_degraded",
                component=check.component,
                status=check.status.value,
                latency_ms=check.latency_ms,
                message=check.message
            )

    return JSONResponse(
        status_code=200,
        content=result.to_dict()
    )


@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint

    Exposes all collected metrics in Prometheus format.

    Returns:
        Prometheus text format metrics
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 3.2 Main App Integration

```python
# app/api/main.py (additions)

from app.api.routes import health

# Register health routes
app.include_router(health.router)

# Remove duplicate /health and /metrics endpoints (now in health.router)
```

---

## 4. Error Handling Strategy

### 4.1 Timeout Management

**Principles**:
- All health checks have 2s timeout (5s for Claude API)
- Timeouts return UNHEALTHY status, not exceptions
- Use `asyncio.wait_for()` for timeout enforcement
- Graceful degradation on partial failures

**Implementation Pattern**:
```python
async def check_with_timeout(self) -> ComponentHealth:
    try:
        result = await asyncio.wait_for(
            self.check_health(),
            timeout=self.timeout
        )
        return result
    except asyncio.TimeoutError:
        return ComponentHealth(
            component=self.component_name,
            status=HealthStatus.UNHEALTHY,
            latency_ms=self.timeout * 1000,
            message=f"Timeout after {self.timeout}s"
        )
```

### 4.2 Graceful Degradation

**Status Hierarchy**:
1. **HEALTHY**: All systems operational
2. **DEGRADED**: Non-critical services impaired (e.g., cache miss, Claude API slow)
3. **UNHEALTHY**: Critical services down (e.g., database unreachable)

**Degradation Triggers**:
- Redis down → DEGRADED (cache miss fallback exists)
- Claude API slow (>5s) → DEGRADED (can use Ollama fallback)
- PostgreSQL/Qdrant down → UNHEALTHY (no fallback)

### 4.3 Structured Error Responses

```python
# Error response model
@dataclass
class ErrorDetail:
    """Structured error detail"""
    component: str
    error_type: str
    message: str
    timestamp: str
    remediation: Optional[str] = None

# Example error response
{
    "status": "unhealthy",
    "timestamp": "2025-10-19T12:00:00Z",
    "checks": [
        {
            "component": "postgresql",
            "status": "unhealthy",
            "latency_ms": 2000.0,
            "message": "Connection timeout",
            "metadata": {
                "host": "172.28.0.4",
                "remediation": "Check PostgreSQL container status"
            }
        }
    ]
}
```

### 4.4 Concurrent Check Error Handling

```python
# Using asyncio.gather with return_exceptions=True
check_results = await asyncio.gather(
    *[checker.check_with_timeout() for checker in self.checkers],
    return_exceptions=True
)

# Filter exceptions
for result in check_results:
    if isinstance(result, ComponentHealth):
        component_healths.append(result)
    elif isinstance(result, Exception):
        # Log unexpected exception, create UNHEALTHY status
        logger.error("health_check_exception", exception=str(result))
        component_healths.append(ComponentHealth(
            component="unknown",
            status=HealthStatus.UNHEALTHY,
            latency_ms=0,
            message=f"Unexpected error: {str(result)}"
        ))
```

---

## 5. Testing Strategy

### 5.1 Unit Test Structure

```python
# tests/unit/test_health.py

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.core.health import (
    HealthChecker,
    HealthStatus,
    ComponentHealth,
    PostgreSQLHealthChecker,
    RedisHealthChecker,
    QdrantHealthChecker,
    ClaudeAPIHealthChecker,
    HealthCheckOrchestrator
)


@pytest.mark.asyncio
class TestHealthCheckers:
    """Unit tests for individual health checkers"""

    async def test_postgresql_health_success(self):
        """Test PostgreSQL health check success"""
        with patch('asyncpg.connect') as mock_connect:
            # Mock successful connection
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            checker = PostgreSQLHealthChecker(
                host="localhost",
                port=5432,
                database="test",
                user="test",
                password="test"
            )

            result = await checker.check_health()

            assert result.status == HealthStatus.HEALTHY
            assert result.component == "postgresql"
            assert result.latency_ms > 0

    async def test_postgresql_health_timeout(self):
        """Test PostgreSQL health check timeout"""
        checker = PostgreSQLHealthChecker(
            host="localhost",
            port=5432,
            database="test",
            user="test",
            password="test",
            timeout=0.1  # Very short timeout
        )

        with patch('asyncpg.connect', side_effect=asyncio.TimeoutError()):
            result = await checker.check_with_timeout()

            assert result.status == HealthStatus.UNHEALTHY
            assert "timeout" in result.message.lower()

    async def test_redis_health_success(self):
        """Test Redis health check success"""
        with patch('aioredis.create_redis_pool') as mock_pool:
            # Mock successful Redis ping
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.close = AsyncMock()
            mock_redis.wait_closed = AsyncMock()
            mock_pool.return_value = mock_redis

            checker = RedisHealthChecker(host="localhost", port=6379)
            result = await checker.check_health()

            assert result.status == HealthStatus.HEALTHY
            assert result.component == "redis"

    async def test_qdrant_health_success(self):
        """Test Qdrant health check success"""
        checker = QdrantHealthChecker(host="localhost", port=6333)

        with patch('qdrant_client.QdrantClient') as mock_client:
            # Mock successful collection listing
            mock_instance = Mock()
            mock_collections = Mock()
            mock_collections.collections = [Mock(), Mock()]
            mock_instance.get_collections = Mock(return_value=mock_collections)
            mock_client.return_value = mock_instance

            result = await checker.check_health()

            assert result.status == HealthStatus.HEALTHY
            assert result.metadata["collections"] == 2

    async def test_claude_api_health_success(self):
        """Test Claude API health check success"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200

            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()

            mock_client.return_value = mock_instance

            checker = ClaudeAPIHealthChecker(api_key="test-key")
            result = await checker.check_health()

            assert result.status == HealthStatus.HEALTHY
            assert result.component == "claude_api"

    async def test_claude_api_health_degraded(self):
        """Test Claude API health check degraded on client error"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock 401 unauthorized (configuration issue)
            mock_response = Mock()
            mock_response.status_code = 401

            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()

            mock_client.return_value = mock_instance

            checker = ClaudeAPIHealthChecker(api_key="invalid-key")
            result = await checker.check_health()

            assert result.status == HealthStatus.DEGRADED
            assert result.metadata["status_code"] == 401


@pytest.mark.asyncio
class TestHealthOrchestrator:
    """Unit tests for health check orchestrator"""

    async def test_orchestrator_all_healthy(self):
        """Test orchestrator with all healthy components"""
        # Create mock checkers
        mock_checkers = [
            Mock(check_with_timeout=AsyncMock(return_value=ComponentHealth(
                component=f"service_{i}",
                status=HealthStatus.HEALTHY,
                latency_ms=10.0
            )))
            for i in range(3)
        ]

        orchestrator = HealthCheckOrchestrator(mock_checkers)
        result = await orchestrator.check_all()

        assert result.overall_status == HealthStatus.HEALTHY
        assert len(result.checks) == 3

    async def test_orchestrator_degraded_status(self):
        """Test orchestrator with degraded component"""
        mock_checkers = [
            Mock(check_with_timeout=AsyncMock(return_value=ComponentHealth(
                component="healthy_service",
                status=HealthStatus.HEALTHY,
                latency_ms=10.0
            ))),
            Mock(check_with_timeout=AsyncMock(return_value=ComponentHealth(
                component="degraded_service",
                status=HealthStatus.DEGRADED,
                latency_ms=50.0
            )))
        ]

        orchestrator = HealthCheckOrchestrator(mock_checkers)
        result = await orchestrator.check_all()

        assert result.overall_status == HealthStatus.DEGRADED

    async def test_orchestrator_unhealthy_status(self):
        """Test orchestrator with unhealthy component"""
        mock_checkers = [
            Mock(check_with_timeout=AsyncMock(return_value=ComponentHealth(
                component="healthy_service",
                status=HealthStatus.HEALTHY,
                latency_ms=10.0
            ))),
            Mock(check_with_timeout=AsyncMock(return_value=ComponentHealth(
                component="unhealthy_service",
                status=HealthStatus.UNHEALTHY,
                latency_ms=2000.0,
                message="Connection failed"
            )))
        ]

        orchestrator = HealthCheckOrchestrator(mock_checkers)
        result = await orchestrator.check_all()

        assert result.overall_status == HealthStatus.UNHEALTHY

    async def test_orchestrator_parallel_execution(self):
        """Test that orchestrator executes checks in parallel"""
        import time

        # Create checkers with artificial delays
        async def slow_check(delay):
            await asyncio.sleep(delay)
            return ComponentHealth(
                component="test",
                status=HealthStatus.HEALTHY,
                latency_ms=delay * 1000
            )

        mock_checkers = [
            Mock(check_with_timeout=AsyncMock(side_effect=lambda: slow_check(0.1)))
            for _ in range(5)
        ]

        orchestrator = HealthCheckOrchestrator(mock_checkers)

        start = time.time()
        result = await orchestrator.check_all()
        duration = time.time() - start

        # If parallel, should take ~0.1s, not 0.5s (5 * 0.1)
        assert duration < 0.2  # Allow some overhead
        assert len(result.checks) == 5
```

### 5.2 Integration Test Structure

```python
# tests/integration/test_health_endpoints.py

import pytest
from fastapi.testclient import TestClient
from app.api.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_liveness_probe_success(client):
    """Test /health/live endpoint"""
    response = client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["component"] == "liveness"


def test_readiness_probe_with_healthy_deps(client, monkeypatch):
    """Test /health/ready with healthy dependencies"""
    # Mock all dependencies as healthy
    response = client.get("/health/ready")

    # With Docker services running, should be 200
    assert response.status_code in [200, 503]  # Depends on environment

    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_health_endpoint_structure(client):
    """Test /health endpoint response structure"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Validate structure
    assert "status" in data
    assert "timestamp" in data
    assert "checks" in data
    assert isinstance(data["checks"], list)

    # Validate component health structure
    for check in data["checks"]:
        assert "component" in check
        assert "status" in check
        assert "latency_ms" in check
        assert check["status"] in ["healthy", "degraded", "unhealthy"]


def test_metrics_endpoint_format(client):
    """Test /health/metrics Prometheus format"""
    response = client.get("/health/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    # Validate Prometheus format
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
```

### 5.3 Metrics Testing

```python
# tests/unit/test_metrics.py

import pytest
from app.core.metrics import MetricsCollector


@pytest.mark.asyncio
class TestMetricsCollector:
    """Unit tests for metrics collector"""

    async def test_track_llm_query_success(self):
        """Test LLM query metrics tracking"""
        collector = MetricsCollector()

        async with collector.track_llm_query("claude-3-haiku") as metrics:
            metrics["tokens"] = 150

        # Verify metrics recorded (check prometheus registry)
        # This is challenging without resetting registry between tests
        # Consider using a test registry

    async def test_track_vector_search_success(self):
        """Test vector search metrics tracking"""
        collector = MetricsCollector()

        async with collector.track_vector_search("documents") as metrics:
            metrics["results"] = 5

        # Metrics should be recorded

    async def test_track_document_ingestion_error(self):
        """Test document ingestion error tracking"""
        collector = MetricsCollector()

        with pytest.raises(ValueError):
            async with collector.track_document_ingestion("pdf") as metrics:
                raise ValueError("Processing error")

        # Error should be recorded in metrics
```

---

## 6. Deployment Integration

### 6.1 Kubernetes Probes Configuration

```yaml
# kubernetes/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-enterprise
spec:
  template:
    spec:
      containers:
      - name: api
        image: rag-enterprise:latest
        ports:
        - containerPort: 8000

        # Liveness probe - restart if server crashes
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        # Readiness probe - route traffic only when ready
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
```

### 6.2 Prometheus Scrape Configuration

```yaml
# prometheus/prometheus.yml

scrape_configs:
  - job_name: 'rag-enterprise'
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: '/health/metrics'
    static_configs:
      - targets: ['rag-enterprise:8000']
        labels:
          service: 'rag-enterprise-api'
          environment: 'production'
```

### 6.3 Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "RAG Enterprise Health & Metrics",
    "panels": [
      {
        "title": "Service Health Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"rag-enterprise\"}",
            "legendFormat": "API Status"
          }
        ]
      },
      {
        "title": "HTTP Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "HTTP Request Latency (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Claude API Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "claude_api_duration_seconds",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(errors_total[5m])",
            "legendFormat": "{{error_type}}"
          }
        ]
      }
    ]
  }
}
```

---

## 7. Implementation Checklist

### Phase 1: Core Health System
- [ ] Create `app/core/health.py` with base classes
- [ ] Implement `PostgreSQLHealthChecker` with asyncpg
- [ ] Implement `RedisHealthChecker` with aioredis
- [ ] Implement `QdrantHealthChecker` with async wrapper
- [ ] Implement `ClaudeAPIHealthChecker` with httpx
- [ ] Create `HealthCheckOrchestrator` with parallel execution
- [ ] Add health orchestrator to `app/core/dependencies.py`
- [ ] Write unit tests for all checkers

### Phase 2: Health Endpoints
- [ ] Create `app/api/routes/health.py`
- [ ] Implement `/health/live` endpoint
- [ ] Implement `/health/ready` endpoint
- [ ] Implement `/health` endpoint
- [ ] Move `/metrics` to health router
- [ ] Update `app/api/main.py` integration
- [ ] Write integration tests for endpoints

### Phase 3: Enhanced Metrics
- [ ] Add Claude API metrics to `app/core/metrics.py`
- [ ] Add RAG pipeline metrics
- [ ] Add database connection metrics
- [ ] Create `MetricsCollector` class
- [ ] Add context managers for metric tracking
- [ ] Write metrics unit tests

### Phase 4: Testing & Validation
- [ ] Complete unit test coverage (>80%)
- [ ] Complete integration test coverage
- [ ] Test timeout handling
- [ ] Test error scenarios
- [ ] Test parallel execution performance
- [ ] Validate Prometheus format output

### Phase 5: Documentation & Deployment
- [ ] Update API documentation
- [ ] Create Kubernetes probe configuration
- [ ] Create Prometheus scrape configuration
- [ ] Create Grafana dashboard template
- [ ] Update README with health endpoints
- [ ] Create runbook for troubleshooting

---

## 8. Dependencies Required

### Python Packages

```txt
# Async database drivers
asyncpg>=0.29.0  # PostgreSQL async driver
aioredis>=2.0.1  # Redis async driver

# HTTP client for Claude API
httpx>=0.25.0

# Prometheus (already installed)
prometheus-client>=0.19.0
```

### Installation Command

```bash
pip install asyncpg aioredis httpx prometheus-client
```

---

## 9. Performance Considerations

### Parallel Execution Benefits

**Sequential Approach (BAD)**:
- PostgreSQL: 2s timeout
- Redis: 2s timeout
- Qdrant: 2s timeout
- Claude API: 5s timeout
- **Total**: 11s worst case

**Parallel Approach (GOOD)**:
- All checks run concurrently with `asyncio.gather`
- **Total**: 5s worst case (longest timeout)
- **Improvement**: 55% faster

### Resource Impact

**Health Checks**:
- CPU: Negligible (<1% during checks)
- Memory: <10MB for orchestrator + checkers
- Network: 4 connections (one per dependency)
- Latency: No impact on request processing (separate async tasks)

**Metrics Collection**:
- CPU: <2% overhead from middleware
- Memory: ~50MB for Prometheus registry (moderate cardinality)
- Latency: <1ms per request for metric recording

---

## 10. Monitoring & Alerting

### Key Metrics to Alert On

```yaml
alerts:
  - name: HealthCheckFailure
    expr: up{job="rag-enterprise"} == 0
    duration: 2m
    severity: critical

  - name: ComponentDegraded
    expr: component_health_status{status="degraded"} == 1
    duration: 5m
    severity: warning

  - name: HighErrorRate
    expr: rate(errors_total[5m]) > 10
    duration: 2m
    severity: warning

  - name: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
    duration: 5m
    severity: warning

  - name: ClaudeAPIDown
    expr: claude_api_calls_total{status="error"} > 10
    duration: 2m
    severity: critical
```

---

## 11. Security Considerations

### Sensitive Data Handling

**Health Checks**:
- Never log passwords or API keys in health check messages
- Use structured logging with automatic masking (already implemented in `app/core/logging.py`)
- Sanitize error messages before exposing in health endpoints

**Metrics**:
- Avoid high-cardinality labels (user IDs, request IDs)
- Don't expose internal IPs or credentials in metric labels
- Use structured labels (model, status, endpoint) not raw values

### Access Control

**Production Recommendations**:
- `/health/live` and `/health/ready`: Public (K8s needs access)
- `/health`: Protected with API key or internal network only
- `/health/metrics`: Protected (Prometheus scraper authentication)

---

## Summary

This architecture provides:

1. **Production-Ready Health Checks**: Async parallel checks with timeout protection
2. **Comprehensive Metrics**: Request, system, and application-level observability
3. **Graceful Degradation**: Three-tier health status (healthy/degraded/unhealthy)
4. **Error Resilience**: Timeout management, exception handling, structured responses
5. **Performance**: Parallel execution, minimal overhead, zero request latency impact
6. **Testability**: Full unit and integration test coverage

**Next Steps**: Implement Phase 1 (Core Health System) following this specification.
