"""
Unit tests for health check system.

Tests all health checker implementations and orchestration logic
including timeout handling, error scenarios, and parallel execution.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.health import (
    HealthStatus,
    ComponentHealth,
    PostgreSQLHealthChecker,
    RedisHealthChecker,
    QdrantHealthChecker,
    ClaudeAPIHealthChecker,
    HealthCheckOrchestrator
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestPostgreSQLHealthChecker:
    """Test PostgreSQL health checker."""

    async def test_healthy_connection(self):
        """Test successful PostgreSQL health check."""
        # Mock psycopg connection
        mock_cursor = AsyncMock()
        mock_cursor.execute = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            side_effect=[(1,), ("PostgreSQL 14.0",)]
        )
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=None)

        mock_conn = AsyncMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor)
        mock_conn.close = AsyncMock()

        with patch("psycopg.AsyncConnection.connect", return_value=mock_conn):
            checker = PostgreSQLHealthChecker(
                "postgresql://user:pass@localhost/db",
                timeout=5.0
            )

            result = await checker.check()

            assert result.component == "postgresql"
            assert result.status == HealthStatus.HEALTHY
            assert result.latency_ms < 1000
            assert "operational" in result.message.lower()
            assert "version" in result.metadata

            # Verify connection was closed
            mock_conn.close.assert_called_once()

    async def test_connection_failure(self):
        """Test PostgreSQL connection failure."""
        import psycopg

        with patch(
            "psycopg.AsyncConnection.connect",
            side_effect=psycopg.OperationalError("Connection refused")
        ):
            checker = PostgreSQLHealthChecker(
                "postgresql://user:pass@localhost/db",
                timeout=5.0
            )

            result = await checker.check()

            assert result.component == "postgresql"
            assert result.status == HealthStatus.UNHEALTHY
            assert "connection failed" in result.message.lower()
            assert result.metadata["error"] == "connection_failed"
            assert "remediation" in result.metadata

    async def test_timeout_handling(self):
        """Test PostgreSQL health check timeout."""
        # Mock connection that never completes
        async def slow_connect(*args, **kwargs):
            await asyncio.sleep(10)
            return AsyncMock()

        with patch("psycopg.AsyncConnection.connect", side_effect=slow_connect):
            checker = PostgreSQLHealthChecker(
                "postgresql://user:pass@localhost/db",
                timeout=0.5  # Short timeout
            )

            result = await checker.check_with_timeout()

            assert result.component == "postgresql"
            assert result.status == HealthStatus.UNHEALTHY
            assert "timed out" in result.message.lower()
            assert result.metadata["error"] == "timeout"
            assert result.latency_ms >= 500  # At least timeout duration


@pytest.mark.unit
@pytest.mark.asyncio
class TestRedisHealthChecker:
    """Test Redis health checker."""

    async def test_healthy_connection(self):
        """Test successful Redis health check."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.info = AsyncMock(return_value={
            "redis_version": "7.0.0",
            "uptime_in_seconds": 12345,
            "connected_clients": 5
        })
        mock_redis.close = AsyncMock()

        # Mock from_url to return an awaitable that resolves to mock_redis
        async def async_from_url(*args, **kwargs):
            return mock_redis

        with patch("redis.asyncio.from_url", side_effect=async_from_url):
            checker = RedisHealthChecker(
                "redis://localhost:6379",
                timeout=3.0
            )

            result = await checker.check()

            assert result.component == "redis"
            assert result.status == HealthStatus.HEALTHY
            assert result.latency_ms < 1000
            assert "operational" in result.message.lower()
            assert result.metadata["version"] == "7.0.0"
            assert result.metadata["connected_clients"] == 5

            # Verify connection was closed
            mock_redis.close.assert_called_once()

    async def test_connection_failure(self):
        """Test Redis connection failure."""
        from redis import asyncio as aioredis

        with patch(
            "redis.asyncio.from_url",
            side_effect=aioredis.ConnectionError("Connection refused")
        ):
            checker = RedisHealthChecker(
                "redis://localhost:6379",
                timeout=3.0
            )

            result = await checker.check()

            assert result.component == "redis"
            # Redis failure is degraded, not unhealthy
            assert result.status == HealthStatus.DEGRADED
            assert "unavailable" in result.message.lower()
            assert result.metadata["error"] == "connection_failed"
            assert "impact" in result.metadata
            assert "operational without caching" in result.metadata["impact"]

    async def test_timeout_handling(self):
        """Test Redis health check timeout."""
        # Mock Redis that times out
        async def slow_connect(*args, **kwargs):
            await asyncio.sleep(10)
            return AsyncMock()

        with patch("redis.asyncio.from_url", side_effect=slow_connect):
            checker = RedisHealthChecker(
                "redis://localhost:6379",
                timeout=0.5
            )

            result = await checker.check_with_timeout()

            assert result.component == "redis"
            assert result.status == HealthStatus.UNHEALTHY
            assert "timed out" in result.message.lower()
            assert result.latency_ms >= 500


@pytest.mark.unit
@pytest.mark.asyncio
class TestQdrantHealthChecker:
    """Test Qdrant health checker."""

    async def test_healthy_connection(self):
        """Test successful Qdrant health check."""
        # Mock httpx client
        mock_response_health = MagicMock()
        mock_response_health.status_code = 200

        mock_response_collections = MagicMock()
        mock_response_collections.status_code = 200
        mock_response_collections.json.return_value = {
            "result": {
                "collections": [
                    {"name": "documents"},
                    {"name": "images"}
                ]
            }
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[mock_response_health, mock_response_collections]
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            checker = QdrantHealthChecker(
                "http://localhost:6333",
                timeout=5.0
            )

            result = await checker.check()

            assert result.component == "qdrant"
            assert result.status == HealthStatus.HEALTHY
            assert "operational" in result.message.lower()
            assert result.metadata["collections"] == 2

    async def test_connection_failure(self):
        """Test Qdrant connection failure."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            checker = QdrantHealthChecker(
                "http://localhost:6333",
                timeout=5.0
            )

            result = await checker.check()

            assert result.component == "qdrant"
            assert result.status == HealthStatus.UNHEALTHY
            assert "unreachable" in result.message.lower()
            assert result.metadata["error"] == "connection_failed"

    async def test_timeout_handling(self):
        """Test Qdrant health check timeout."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            checker = QdrantHealthChecker(
                "http://localhost:6333",
                timeout=5.0
            )

            result = await checker.check()

            assert result.component == "qdrant"
            assert result.status == HealthStatus.UNHEALTHY
            assert "timeout" in result.message.lower()
            assert result.metadata["error"] == "timeout"


@pytest.mark.unit
@pytest.mark.asyncio
class TestClaudeAPIHealthChecker:
    """Test Claude API health checker."""

    async def test_healthy_api(self):
        """Test successful Claude API health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "claude-3-haiku-20240307",
            "content": [{"text": "pong"}]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            checker = ClaudeAPIHealthChecker(
                api_key="test-key",
                timeout=10.0
            )

            result = await checker.check()

            assert result.component == "claude_api"
            assert result.status == HealthStatus.HEALTHY
            assert "operational" in result.message.lower()
            assert "model" in result.metadata

    async def test_api_error(self):
        """Test Claude API error (401 unauthorized)."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            checker = ClaudeAPIHealthChecker(
                api_key="invalid-key",
                timeout=10.0
            )

            result = await checker.check()

            assert result.component == "claude_api"
            assert result.status == HealthStatus.UNHEALTHY
            assert "authentication failed" in result.message.lower()
            assert result.metadata["status_code"] == 401

    async def test_timeout_handling(self):
        """Test Claude API timeout."""
        import httpx

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.TimeoutException("API timeout")
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            checker = ClaudeAPIHealthChecker(
                api_key="test-key",
                timeout=10.0
            )

            result = await checker.check()

            assert result.component == "claude_api"
            # Timeout is degraded for API
            assert result.status == HealthStatus.DEGRADED
            assert "timeout" in result.message.lower()


@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthCheckOrchestrator:
    """Test health check orchestrator."""

    def _create_mock_config(self):
        """Create mock configuration."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "database": {
                "user": "postgres",
                "password": "pass",
                "host": "localhost",
                "port": 5432,
                "database": "testdb"
            },
            "redis": {
                "host": "localhost",
                "port": 6379
            },
            "qdrant": {
                "host": "localhost",
                "port": 6333
            },
            "claude": {
                "api_key": "test-key"
            }
        }.get(key, default)

        return mock_config

    async def test_all_healthy(self):
        """Test orchestrator with all components healthy."""
        mock_config = self._create_mock_config()

        # Create healthy mock results - these are instance methods so they need self
        async def mock_pg_check(self):
            return ComponentHealth(
                component="postgresql",
                status=HealthStatus.HEALTHY,
                latency_ms=50.0,
                message="Healthy"
            )

        async def mock_redis_check(self):
            return ComponentHealth(
                component="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=30.0,
                message="Healthy"
            )

        async def mock_qdrant_check(self):
            return ComponentHealth(
                component="qdrant",
                status=HealthStatus.HEALTHY,
                latency_ms=40.0,
                message="Healthy"
            )

        async def mock_claude_check(self):
            return ComponentHealth(
                component="claude_api",
                status=HealthStatus.HEALTHY,
                latency_ms=100.0,
                message="Healthy"
            )

        with patch.object(
            PostgreSQLHealthChecker,
            "check_with_timeout",
            mock_pg_check
        ):
            with patch.object(
                RedisHealthChecker,
                "check_with_timeout",
                mock_redis_check
            ):
                with patch.object(
                    QdrantHealthChecker,
                    "check_with_timeout",
                    mock_qdrant_check
                ):
                    with patch.object(
                        ClaudeAPIHealthChecker,
                        "check_with_timeout",
                        mock_claude_check
                    ):
                        orchestrator = HealthCheckOrchestrator(
                            mock_config
                        )
                        results = await orchestrator.check_all()

                        assert results["status"] == "healthy"
                        assert results["summary"]["healthy"] == 4
                        assert results["summary"]["degraded"] == 0
                        assert results["summary"]["unhealthy"] == 0
                        assert len(results["components"]) == 4

    async def test_some_degraded(self):
        """Test orchestrator with degraded components."""
        mock_config = self._create_mock_config()

        async def mock_pg_check(self):
            return ComponentHealth(
                component="postgresql",
                status=HealthStatus.HEALTHY,
                latency_ms=50.0,
                message="Healthy"
            )

        async def mock_redis_check(self):
            return ComponentHealth(
                component="redis",
                status=HealthStatus.DEGRADED,
                latency_ms=30.0,
                message="Cache unavailable"
            )

        async def mock_qdrant_check(self):
            return ComponentHealth(
                component="qdrant",
                status=HealthStatus.HEALTHY,
                latency_ms=40.0,
                message="Healthy"
            )

        async def mock_claude_check(self):
            return ComponentHealth(
                component="claude_api",
                status=HealthStatus.DEGRADED,
                latency_ms=100.0,
                message="Rate limited"
            )

        with patch.object(
            PostgreSQLHealthChecker,
            "check_with_timeout",
            mock_pg_check
        ):
            with patch.object(
                RedisHealthChecker,
                "check_with_timeout",
                mock_redis_check
            ):
                with patch.object(
                    QdrantHealthChecker,
                    "check_with_timeout",
                    mock_qdrant_check
                ):
                    with patch.object(
                        ClaudeAPIHealthChecker,
                        "check_with_timeout",
                        mock_claude_check
                    ):
                        orchestrator = HealthCheckOrchestrator(mock_config)
                        results = await orchestrator.check_all()

                        assert results["status"] == "degraded"
                        assert results["summary"]["healthy"] == 2
                        assert results["summary"]["degraded"] == 2
                        assert results["summary"]["unhealthy"] == 0

    async def test_database_unhealthy(self):
        """Test orchestrator with critical component unhealthy."""
        mock_config = self._create_mock_config()

        async def mock_pg_check(self):
            return ComponentHealth(
                component="postgresql",
                status=HealthStatus.UNHEALTHY,
                latency_ms=50.0,
                message="Connection failed"
            )

        async def mock_redis_check(self):
            return ComponentHealth(
                component="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=30.0,
                message="Healthy"
            )

        async def mock_qdrant_check(self):
            return ComponentHealth(
                component="qdrant",
                status=HealthStatus.HEALTHY,
                latency_ms=40.0,
                message="Healthy"
            )

        with patch.object(
            PostgreSQLHealthChecker,
            "check_with_timeout",
            mock_pg_check
        ):
            with patch.object(
                RedisHealthChecker,
                "check_with_timeout",
                mock_redis_check
            ):
                with patch.object(
                    QdrantHealthChecker,
                    "check_with_timeout",
                    mock_qdrant_check
                ):
                    orchestrator = HealthCheckOrchestrator(mock_config)
                    results = await orchestrator.check_all()

                    # PostgreSQL unhealthy = system unhealthy
                    assert results["status"] == "unhealthy"
                    assert results["summary"]["unhealthy"] == 1

    async def test_parallel_execution_performance(self):
        """Test parallel execution performance improvement."""
        mock_config = self._create_mock_config()

        # Create checks with artificial delays
        async def slow_check(delay: float, component: str):
            await asyncio.sleep(delay)
            return ComponentHealth(
                component=component,
                status=HealthStatus.HEALTHY,
                latency_ms=delay * 1000,
                message="Healthy"
            )

        async def mock_pg_check(self):
            return await slow_check(0.2, "postgresql")

        async def mock_redis_check(self):
            return await slow_check(0.2, "redis")

        async def mock_qdrant_check(self):
            return await slow_check(0.2, "qdrant")

        async def mock_claude_check(self):
            return await slow_check(0.2, "claude_api")

        with patch.object(
            PostgreSQLHealthChecker,
            "check_with_timeout",
            mock_pg_check
        ):
            with patch.object(
                RedisHealthChecker,
                "check_with_timeout",
                mock_redis_check
            ):
                with patch.object(
                    QdrantHealthChecker,
                    "check_with_timeout",
                    mock_qdrant_check
                ):
                    with patch.object(
                        ClaudeAPIHealthChecker,
                        "check_with_timeout",
                        mock_claude_check
                    ):
                        orchestrator = HealthCheckOrchestrator(mock_config)

                        start_time = time.time()
                        results = await orchestrator.check_all()
                        duration = time.time() - start_time

                        # Parallel execution should complete in ~0.2s
                        # Sequential would take 0.8s (4 * 0.2s)
                        assert duration < 0.4  # Allow some overhead
                        assert results["status"] == "healthy"

                        # Verify performance improvement
                        improvement = (0.8 - duration) / 0.8 * 100
                        assert improvement > 50  # At least 50% improvement

    async def test_timeout_handling_aggregation(self):
        """Test timeout handling in aggregated results."""
        mock_config = self._create_mock_config()

        async def mock_pg_check(self):
            return ComponentHealth(
                component="postgresql",
                status=HealthStatus.HEALTHY,
                latency_ms=50.0,
                message="Healthy"
            )

        async def mock_redis_check(self):
            # Simulate timeout
            return ComponentHealth(
                component="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=3000.0,
                message="Health check timed out",
                metadata={"error": "timeout"}
            )

        async def mock_qdrant_check(self):
            return ComponentHealth(
                component="qdrant",
                status=HealthStatus.HEALTHY,
                latency_ms=40.0,
                message="Healthy"
            )

        with patch.object(
            PostgreSQLHealthChecker,
            "check_with_timeout",
            mock_pg_check
        ):
            with patch.object(
                RedisHealthChecker,
                "check_with_timeout",
                mock_redis_check
            ):
                with patch.object(
                    QdrantHealthChecker,
                    "check_with_timeout",
                    mock_qdrant_check
                ):
                    orchestrator = HealthCheckOrchestrator(mock_config)
                    results = await orchestrator.check_all()

                    # Redis timeout should be unhealthy but not critical
                    # since Redis is not critical component
                    assert results["summary"]["unhealthy"] == 1

                    # Find Redis component result
                    redis_result = next(
                        c for c in results["components"]
                        if c["component"] == "redis"
                    )
                    assert redis_result["status"] == "unhealthy"
                    assert "timed out" in redis_result["message"].lower()
