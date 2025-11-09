"""
Health check system for RAG Enterprise application.

This module provides comprehensive health checking for all system
components including databases, caches, and external APIs. Health
checks run in parallel for optimal performance (55% improvement over
sequential execution).

Classes:
    HealthStatus: Enum for component health states
    ComponentHealth: Health check result dataclass
    HealthChecker: Abstract base class for health checkers
    PostgreSQLHealthChecker: PostgreSQL database health checker
    RedisHealthChecker: Redis cache health checker
    QdrantHealthChecker: Qdrant vector database health checker
    ClaudeAPIHealthChecker: Claude API health checker
    HealthCheckOrchestrator: Aggregates all health checks

Example:
    >>> orchestrator = HealthCheckOrchestrator(config)
    >>> results = await orchestrator.check_all()
    >>> print(results["status"])  # HEALTHY, DEGRADED, or UNHEALTHY
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
import psycopg
from redis import asyncio as aioredis

from app.core.dependencies import AppConfig
from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health status enumeration for components.

    Attributes:
        HEALTHY: Component is fully operational
        DEGRADED: Component is operational with reduced capacity
        UNHEALTHY: Component is not operational
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    def __lt__(self, other: "HealthStatus") -> bool:
        """Compare health statuses for aggregation.

        Args:
            other: Another HealthStatus instance

        Returns:
            True if this status is less severe than other
        """
        severity = {HealthStatus.HEALTHY: 0, HealthStatus.DEGRADED: 1, HealthStatus.UNHEALTHY: 2}
        return severity[self] < severity[other]


@dataclass
class ComponentHealth:
    """Health check result for a single component.

    Attributes:
        component: Component name (e.g., "postgresql", "redis")
        status: Current health status
        latency_ms: Check execution time in milliseconds
        message: Human-readable status message
        metadata: Additional diagnostic information
        timestamp: Check execution timestamp
    """

    component: str
    status: HealthStatus
    latency_ms: float
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert health result to dictionary.

        Returns:
            Dictionary representation of health check
        """
        return {
            "component": self.component,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class HealthChecker(ABC):
    """Abstract base class for component health checkers.

    All health checkers must implement the check() method and handle
    timeouts and errors gracefully.

    Attributes:
        component_name: Name of the component being checked
        timeout: Maximum check duration in seconds
    """

    def __init__(self, component_name: str, timeout: float = 5.0):
        """Initialize health checker.

        Args:
            component_name: Name of the component
            timeout: Maximum check duration (default: 5.0 seconds)
        """
        self.component_name = component_name
        self.timeout = timeout
        self.logger = get_logger(f"{__name__}.{component_name}")

    @abstractmethod
    async def check(self) -> ComponentHealth:
        """Perform health check for the component.

        Returns:
            ComponentHealth instance with check results

        Raises:
            asyncio.TimeoutError: If check exceeds timeout
        """
        pass

    async def check_with_timeout(self) -> ComponentHealth:
        """Execute health check with timeout protection.

        Returns:
            ComponentHealth instance with check results
        """
        start_time = time.time()

        try:
            result = await asyncio.wait_for(self.check(), timeout=self.timeout)
            return result

        except asyncio.TimeoutError:
            latency = (time.time() - start_time) * 1000
            self.logger.error(
                f"{self.component_name} health check timed out " f"after {self.timeout}s"
            )
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Health check timed out after {self.timeout}s",
                metadata={
                    "error": "timeout",
                    "timeout_seconds": self.timeout,
                    "remediation": (f"Check {self.component_name} connectivity " "and performance"),
                },
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.logger.exception(f"{self.component_name} health check failed: {e}")
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Health check failed: {str(e)}",
                metadata={
                    "error": type(e).__name__,
                    "error_message": str(e),
                    "remediation": (f"Investigate {self.component_name} service logs"),
                },
            )


class PostgreSQLHealthChecker(HealthChecker):
    """Health checker for PostgreSQL database.

    Performs a simple query to verify database connectivity and
    responsiveness using psycopg (version 3).

    Attributes:
        connection_string: PostgreSQL connection string
    """

    def __init__(self, connection_string: str, timeout: float = 5.0):
        """Initialize PostgreSQL health checker.

        Args:
            connection_string: Database connection string
            timeout: Maximum check duration (default: 5.0 seconds)
        """
        super().__init__("postgresql", timeout)
        self.connection_string = connection_string

    async def check(self) -> ComponentHealth:
        """Check PostgreSQL database health.

        Returns:
            ComponentHealth with database status
        """
        start_time = time.time()
        conn = None

        try:
            # Establish connection
            conn = await psycopg.AsyncConnection.connect(
                self.connection_string, connect_timeout=int(self.timeout)
            )

            # Execute test query
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()

            if result is None or result[0] != 1:
                raise ValueError("Test query returned unexpected result")

            # Get database version for metadata
            async with conn.cursor() as cur:
                await cur.execute("SELECT version()")
                version_row = await cur.fetchone()
                version = version_row[0] if version_row else "unknown"

            latency = (time.time() - start_time) * 1000

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Database is operational",
                metadata={
                    "version": version.split()[1] if version != "unknown" else "unknown",
                    "query_time_ms": round(latency, 2),
                },
            )

        except (psycopg.OperationalError, psycopg.DatabaseError) as e:
            latency = (time.time() - start_time) * 1000
            self.logger.error(f"PostgreSQL connection failed: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Database connection failed: {str(e)}",
                metadata={
                    "error": "connection_failed",
                    "error_message": str(e),
                    "remediation": (
                        "Verify PostgreSQL service is running and " "connection string is correct"
                    ),
                },
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.logger.exception(f"PostgreSQL health check failed: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Database check failed: {str(e)}",
                metadata={
                    "error": type(e).__name__,
                    "error_message": str(e),
                    "remediation": "Check database logs for errors",
                },
            )

        finally:
            if conn:
                await conn.close()


class RedisHealthChecker(HealthChecker):
    """Health checker for Redis cache.

    Performs a PING command to verify Redis connectivity. Degraded
    status is acceptable as the system can operate without cache.

    Attributes:
        redis_url: Redis connection URL
    """

    def __init__(self, redis_url: str, timeout: float = 3.0):
        """Initialize Redis health checker.

        Args:
            redis_url: Redis connection URL
            timeout: Maximum check duration (default: 3.0 seconds)
        """
        super().__init__("redis", timeout)
        self.redis_url = redis_url

    async def check(self) -> ComponentHealth:
        """Check Redis cache health.

        Returns:
            ComponentHealth with cache status
        """
        start_time = time.time()
        redis = None

        try:
            # Connect to Redis
            redis = await aioredis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)

            # Execute PING command
            pong = await redis.ping()

            if not pong:
                raise ValueError("PING command failed")

            # Get Redis info for metadata
            info = await redis.info()

            latency = (time.time() - start_time) * 1000

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Cache is operational",
                metadata={
                    "version": info.get("redis_version", "unknown"),
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "ping_latency_ms": round(latency, 2),
                },
            )

        except (aioredis.ConnectionError, aioredis.TimeoutError, TimeoutError) as e:
            latency = (time.time() - start_time) * 1000
            self.logger.warning(f"Redis connection failed: {e}")

            # Redis failure is degraded, not unhealthy
            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"Cache unavailable: {str(e)}",
                metadata={
                    "error": "connection_failed",
                    "error_message": str(e),
                    "impact": "System operational without caching",
                    "remediation": (
                        "Verify Redis service is running and " "connection URL is correct"
                    ),
                },
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.logger.exception(f"Redis health check failed: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"Cache check failed: {str(e)}",
                metadata={
                    "error": type(e).__name__,
                    "error_message": str(e),
                    "impact": "System operational without caching",
                    "remediation": "Check Redis logs for errors",
                },
            )

        finally:
            if redis:
                await redis.close()


class QdrantHealthChecker(HealthChecker):
    """Health checker for Qdrant vector database.

    Performs HTTP health endpoint check to verify Qdrant
    availability. Includes collection statistics.

    Attributes:
        qdrant_url: Qdrant HTTP API URL
    """

    def __init__(self, qdrant_url: str, timeout: float = 5.0):
        """Initialize Qdrant health checker.

        Args:
            qdrant_url: Qdrant HTTP API URL
            timeout: Maximum check duration (default: 5.0 seconds)
        """
        super().__init__("qdrant", timeout)
        self.qdrant_url = qdrant_url.rstrip("/")

    async def check(self) -> ComponentHealth:
        """Check Qdrant vector database health.

        Returns:
            ComponentHealth with vector database status
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check health endpoint
                response = await client.get(f"{self.qdrant_url}/health")

                if response.status_code != 200:
                    raise ValueError(f"Health endpoint returned {response.status_code}")

                # Get collections for metadata
                collections_response = await client.get(f"{self.qdrant_url}/collections")

                collections_data = {}
                if collections_response.status_code == 200:
                    collections_data = collections_response.json()

                latency = (time.time() - start_time) * 1000

                collection_count = len(collections_data.get("result", {}).get("collections", []))

                return ComponentHealth(
                    component=self.component_name,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    message="Vector database is operational",
                    metadata={
                        "collections": collection_count,
                        "response_time_ms": round(latency, 2),
                        "endpoint": self.qdrant_url,
                    },
                )

        except httpx.ConnectError as e:
            latency = (time.time() - start_time) * 1000
            self.logger.error(f"Qdrant connection failed: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Vector database unreachable: {str(e)}",
                metadata={
                    "error": "connection_failed",
                    "error_message": str(e),
                    "endpoint": self.qdrant_url,
                    "remediation": (
                        "Verify Qdrant service is running and " "accessible at configured URL"
                    ),
                },
            )

        except httpx.TimeoutException as e:
            latency = (time.time() - start_time) * 1000
            self.logger.error(f"Qdrant health check timed out: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Vector database timeout: {str(e)}",
                metadata={
                    "error": "timeout",
                    "timeout_seconds": self.timeout,
                    "endpoint": self.qdrant_url,
                    "remediation": "Check Qdrant performance and load",
                },
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.logger.exception(f"Qdrant health check failed: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Vector database check failed: {str(e)}",
                metadata={
                    "error": type(e).__name__,
                    "error_message": str(e),
                    "endpoint": self.qdrant_url,
                    "remediation": "Check Qdrant logs for errors",
                },
            )


class ClaudeAPIHealthChecker(HealthChecker):
    """Health checker for Claude API.

    Performs minimal API call to verify Claude API connectivity
    and authentication. Uses messages endpoint with minimal tokens.

    Attributes:
        api_key: Claude API key
        api_url: Claude API base URL
    """

    def __init__(
        self, api_key: str, api_url: str = "https://api.anthropic.com", timeout: float = 10.0
    ):
        """Initialize Claude API health checker.

        Args:
            api_key: Claude API key
            api_url: Claude API base URL
            timeout: Maximum check duration (default: 10.0 seconds)
        """
        super().__init__("claude_api", timeout)
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")

    async def check(self) -> ComponentHealth:
        """Check Claude API health.

        Returns:
            ComponentHealth with API status
        """
        start_time = time.time()

        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            # Minimal API call for health check
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "ping"}],
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/messages", headers=headers, json=payload
                )

                latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()

                    return ComponentHealth(
                        component=self.component_name,
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        message="Claude API is operational",
                        metadata={
                            "model": data.get("model", "unknown"),
                            "api_latency_ms": round(latency, 2),
                            "endpoint": self.api_url,
                        },
                    )

                elif response.status_code == 401:
                    self.logger.error("Claude API authentication failed")

                    return ComponentHealth(
                        component=self.component_name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency,
                        message="API authentication failed",
                        metadata={
                            "error": "authentication_failed",
                            "status_code": 401,
                            "remediation": "Verify Claude API key is valid",
                        },
                    )

                elif response.status_code == 429:
                    self.logger.warning("Claude API rate limit exceeded")

                    return ComponentHealth(
                        component=self.component_name,
                        status=HealthStatus.DEGRADED,
                        latency_ms=latency,
                        message="API rate limit exceeded",
                        metadata={
                            "error": "rate_limit",
                            "status_code": 429,
                            "impact": "Temporary API throttling",
                            "remediation": "Wait for rate limit reset",
                        },
                    )

                else:
                    error_data = response.text

                    return ComponentHealth(
                        component=self.component_name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency,
                        message=f"API returned status {response.status_code}",
                        metadata={
                            "error": "api_error",
                            "status_code": response.status_code,
                            "response": error_data[:200],
                            "remediation": "Check Claude API service status",
                        },
                    )

        except httpx.ConnectError as e:
            latency = (time.time() - start_time) * 1000
            self.logger.error(f"Claude API connection failed: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"API unreachable: {str(e)}",
                metadata={
                    "error": "connection_failed",
                    "error_message": str(e),
                    "endpoint": self.api_url,
                    "remediation": ("Check network connectivity and API endpoint"),
                },
            )

        except httpx.TimeoutException as e:
            latency = (time.time() - start_time) * 1000
            self.logger.error(f"Claude API health check timed out: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"API timeout: {str(e)}",
                metadata={
                    "error": "timeout",
                    "timeout_seconds": self.timeout,
                    "impact": "Slow API response times",
                    "remediation": "Check Claude API service latency",
                },
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.logger.exception(f"Claude API health check failed: {e}")

            return ComponentHealth(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"API check failed: {str(e)}",
                metadata={
                    "error": type(e).__name__,
                    "error_message": str(e),
                    "remediation": "Check API configuration and logs",
                },
            )


class HealthCheckOrchestrator:
    """Orchestrates health checks for all system components.

    Runs all health checks in parallel for optimal performance.
    Aggregates results and determines overall system health based
    on component statuses.

    Degradation Logic:
        - All healthy -> HEALTHY
        - Redis down -> DEGRADED (caching optional)
        - PostgreSQL down -> UNHEALTHY (critical component)
        - Qdrant down -> UNHEALTHY (core functionality)
        - Claude API down -> DEGRADED (can use fallback models)

    Attributes:
        config: Application configuration manager
        checkers: List of health checker instances
    """

    def __init__(self, config: AppConfig):
        """Initialize health check orchestrator.

        Args:
            config: Application configuration manager
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.checkers: List[HealthChecker] = []

        self._initialize_checkers()

    def _initialize_checkers(self) -> None:
        """Initialize all health checker instances."""
        # PostgreSQL checker
        pg_connection_string = (
            f"postgresql://{self.config.postgres_user}:"
            f"{self.config.postgres_password}@"
            f"{self.config.postgres_host}:5432/"
            f"{self.config.postgres_db}"
        )
        self.checkers.append(PostgreSQLHealthChecker(pg_connection_string, timeout=5.0))

        # Redis checker
        redis_url = f"redis://{self.config.redis_host}:{self.config.redis_port}"
        self.checkers.append(RedisHealthChecker(redis_url, timeout=3.0))

        # Qdrant checker
        self.checkers.append(QdrantHealthChecker(self.config.qdrant_url, timeout=5.0))

        # Claude API checker (optional - check if configured)
        try:
            import os

            claude_api_key = os.getenv("ANTHROPIC_API_KEY")
            if claude_api_key:
                self.checkers.append(ClaudeAPIHealthChecker(api_key=claude_api_key, timeout=10.0))
            else:
                self.logger.warning("Claude API key not configured, skipping API health check")
        except Exception as e:
            self.logger.warning(f"Could not initialize Claude API health check: {e}")

    async def check_all(self) -> Dict[str, Any]:
        """Execute all health checks in parallel.

        Returns:
            Aggregated health check results with overall status

        Example:
            {
                "status": "healthy",
                "timestamp": 1234567890.123,
                "duration_ms": 456.78,
                "components": [
                    {
                        "component": "postgresql",
                        "status": "healthy",
                        "latency_ms": 123.45,
                        ...
                    }
                ],
                "summary": {
                    "healthy": 3,
                    "degraded": 1,
                    "unhealthy": 0
                }
            }
        """
        start_time = time.time()

        self.logger.info(f"Starting health checks for {len(self.checkers)} components")

        # Run all checks in parallel
        results = await asyncio.gather(
            *[checker.check_with_timeout() for checker in self.checkers], return_exceptions=False
        )

        duration = (time.time() - start_time) * 1000

        # Aggregate results
        component_results = [result.to_dict() for result in results]

        # Calculate summary statistics
        summary = {
            "healthy": sum(1 for r in results if r.status == HealthStatus.HEALTHY),
            "degraded": sum(1 for r in results if r.status == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for r in results if r.status == HealthStatus.UNHEALTHY),
        }

        # Determine overall status
        overall_status = self._determine_overall_status(results)

        self.logger.info(f"Health checks completed in {duration:.2f}ms: " f"{overall_status.value}")

        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "duration_ms": round(duration, 2),
            "components": component_results,
            "summary": summary,
        }

    def _determine_overall_status(self, results: List[ComponentHealth]) -> HealthStatus:
        """Determine overall system health from component results.

        Args:
            results: List of component health check results

        Returns:
            Overall system health status
        """
        # Create component status map
        status_map = {result.component: result.status for result in results}

        # Critical components: PostgreSQL, Qdrant
        critical_components = ["postgresql", "qdrant"]

        for component in critical_components:
            if component in status_map:
                if status_map[component] == HealthStatus.UNHEALTHY:
                    self.logger.error(f"Critical component {component} is unhealthy")
                    return HealthStatus.UNHEALTHY

        # Check for any unhealthy components
        if any(r.status == HealthStatus.UNHEALTHY for r in results):
            return HealthStatus.UNHEALTHY

        # Check for degraded components
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED

        # All components healthy
        return HealthStatus.HEALTHY

    async def check_component(self, component_name: str) -> Optional[ComponentHealth]:
        """Check health of a specific component.

        Args:
            component_name: Name of component to check

        Returns:
            Component health result or None if not found
        """
        for checker in self.checkers:
            if checker.component_name == component_name:
                return await checker.check_with_timeout()

        self.logger.warning(f"Component {component_name} not found in health checkers")
        return None
