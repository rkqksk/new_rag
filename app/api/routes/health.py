"""
Health check and metrics endpoints for RAG Enterprise.

This module provides comprehensive health monitoring endpoints including:
- Liveness probe (simple health check)
- Readiness probe (full dependency checks)
- Detailed health status with component diagnostics
- Prometheus metrics exposition

Endpoints:
    GET /health/live - Liveness probe (Kubernetes)
    GET /health/ready - Readiness probe (Kubernetes)
    GET /health - Detailed health status
    GET /health/metrics - Prometheus metrics
    GET /health/status - Quick status summary

Example:
    >>> import httpx
    >>> response = httpx.get("http://localhost:8000/health/ready")
    >>> print(response.json()["status"])  # "healthy" or "degraded"
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field

from app.core.dependencies import AppConfig, get_config
from app.core.health import (
    ComponentHealth,
    HealthCheckOrchestrator,
    HealthStatus,
)
from app.core.metrics import MetricsCollector, get_metrics_collector

# Application start time for uptime calculation
_app_start_time = time.time()


# ============================================================
# Pydantic Response Models
# ============================================================


class HealthStatusResponse(BaseModel):
    """Single component health status response.

    Attributes:
        component: Component name (e.g., "postgresql", "redis")
        status: Health status (healthy, degraded, unhealthy)
        latency_ms: Health check execution time in milliseconds
        message: Human-readable status message
        metadata: Additional diagnostic information
        remediation: Suggested remediation steps (if unhealthy)
    """

    component: str = Field(..., description="Component name")
    status: str = Field(..., description="Health status")
    latency_ms: float = Field(..., description="Check latency in milliseconds")
    message: str = Field(..., description="Status message")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Diagnostic metadata"
    )
    remediation: Optional[str] = Field(
        None, description="Remediation suggestions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "component": "postgresql",
                "status": "healthy",
                "latency_ms": 12.5,
                "message": "Database is operational",
                "metadata": {"version": "14.5", "query_time_ms": 12.5},
                "remediation": None,
            }
        }


class HealthCheckResponse(BaseModel):
    """Complete health check response with all components.

    Attributes:
        status: Overall system status (healthy, degraded, unhealthy)
        timestamp: Health check execution timestamp (ISO 8601)
        duration_ms: Total health check duration in milliseconds
        checks: List of individual component health checks
        summary: Summary statistics of component health
    """

    status: str = Field(..., description="Overall system status")
    timestamp: str = Field(..., description="Check timestamp (ISO 8601)")
    duration_ms: float = Field(..., description="Total check duration")
    checks: List[HealthStatusResponse] = Field(
        ..., description="Component health checks"
    )
    summary: Dict[str, int] = Field(..., description="Health summary")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-19T10:30:00Z",
                "duration_ms": 456.78,
                "checks": [
                    {
                        "component": "postgresql",
                        "status": "healthy",
                        "latency_ms": 12.5,
                        "message": "Database is operational",
                        "metadata": {"version": "14.5"},
                        "remediation": None,
                    }
                ],
                "summary": {"healthy": 4, "degraded": 0, "unhealthy": 0},
            }
        }


class LivenessResponse(BaseModel):
    """Liveness probe response.

    Attributes:
        status: Always "healthy" if server is running
        timestamp: Current timestamp (ISO 8601)
        uptime_seconds: Server uptime in seconds
    """

    status: str = Field(..., description="Liveness status")
    timestamp: str = Field(..., description="Current timestamp")
    uptime_seconds: float = Field(..., description="Server uptime")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-19T10:30:00Z",
                "uptime_seconds": 3600.5,
            }
        }


class ReadinessResponse(BaseModel):
    """Readiness probe response.

    Attributes:
        status: Overall readiness status
        timestamp: Check timestamp (ISO 8601)
        ready: Boolean readiness indicator
        checks_passed: Number of checks passed
        checks_total: Total number of checks
    """

    status: str = Field(..., description="Readiness status")
    timestamp: str = Field(..., description="Check timestamp")
    ready: bool = Field(..., description="Ready to serve traffic")
    checks_passed: int = Field(..., description="Checks passed")
    checks_total: int = Field(..., description="Total checks")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-19T10:30:00Z",
                "ready": True,
                "checks_passed": 4,
                "checks_total": 4,
            }
        }


class StatusSummaryResponse(BaseModel):
    """Quick status summary response.

    Attributes:
        status: Overall system status
        timestamp: Current timestamp (ISO 8601)
        checks_count: Total number of health checks
        uptime_seconds: Server uptime in seconds
    """

    status: str = Field(..., description="System status")
    timestamp: str = Field(..., description="Current timestamp")
    checks_count: int = Field(..., description="Total health checks")
    uptime_seconds: float = Field(..., description="Server uptime")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-19T10:30:00Z",
                "checks_count": 4,
                "uptime_seconds": 3600.5,
            }
        }


# ============================================================
# Dependency Injection Functions
# ============================================================


async def get_health_orchestrator(
    config: AppConfig = Depends(get_config),
) -> HealthCheckOrchestrator:
    """Get health check orchestrator instance.

    Args:
        config: Application configuration

    Returns:
        HealthCheckOrchestrator: Configured health check orchestrator
    """
    return HealthCheckOrchestrator(config)


# ============================================================
# FastAPI Router Setup
# ============================================================

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy or degraded"},
    },
)


# ============================================================
# Health Check Endpoints
# ============================================================


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description=(
        "Kubernetes liveness probe endpoint. Returns 200 if the server "
        "is running. Does not check dependencies. Fast response (<10ms)."
    ),
)
async def liveness_probe() -> LivenessResponse:
    """Liveness probe for Kubernetes health checks.

    This endpoint always returns 200 OK if the server is running.
    It does not check any dependencies or external services.
    Used by Kubernetes to determine if the container should be restarted.

    Returns:
        LivenessResponse: Liveness status with uptime

    Example:
        >>> response = await client.get("/health/live")
        >>> assert response.status_code == 200
        >>> assert response.json()["status"] == "healthy"
    """
    uptime = time.time() - _app_start_time

    return LivenessResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
        uptime_seconds=round(uptime, 2),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        200: {"description": "Service is ready to accept traffic"},
        503: {"description": "Service is not ready"},
    },
    summary="Readiness probe",
    description=(
        "Kubernetes readiness probe endpoint. Returns 200 if all "
        "dependencies are healthy, 503 if degraded or unhealthy. "
        "Checks: PostgreSQL, Redis, Qdrant, Claude API."
    ),
)
async def readiness_probe(
    orchestrator: HealthCheckOrchestrator = Depends(
        get_health_orchestrator
    ),
    response: Response = None,
) -> ReadinessResponse:
    """Readiness probe for Kubernetes traffic routing.

    This endpoint checks all system dependencies in parallel and returns:
    - 200 OK if all checks pass (status: healthy)
    - 503 Service Unavailable if any checks fail (status: degraded/unhealthy)

    Used by Kubernetes to determine if the service should receive traffic.

    Args:
        orchestrator: Health check orchestrator
        response: FastAPI response object

    Returns:
        ReadinessResponse: Readiness status with check results

    Example:
        >>> response = await client.get("/health/ready")
        >>> if response.status_code == 200:
        ...     print("Service is ready")
        >>> else:
        ...     print("Service is not ready")
    """
    # Execute all health checks in parallel
    health_result = await orchestrator.check_all()

    # Determine readiness based on overall status
    overall_status = health_result["status"]
    is_ready = overall_status == HealthStatus.HEALTHY.value

    # Set HTTP status code based on readiness
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # Calculate checks passed
    summary = health_result["summary"]
    checks_passed = summary["healthy"]
    checks_total = sum(summary.values())

    return ReadinessResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        ready=is_ready,
        checks_passed=checks_passed,
        checks_total=checks_total,
    )


@router.get(
    "",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description=(
        "Comprehensive health check with component details, latencies, "
        "and remediation suggestions. Always returns 200 with full details."
    ),
)
async def health_check(
    orchestrator: HealthCheckOrchestrator = Depends(
        get_health_orchestrator
    ),
) -> HealthCheckResponse:
    """Detailed health check with all component diagnostics.

    This endpoint provides comprehensive health information including:
    - Overall system status
    - Individual component health checks
    - Latency measurements for each component
    - Remediation suggestions for unhealthy components
    - Summary statistics

    Always returns 200 OK with full details, even if components are unhealthy.

    Args:
        orchestrator: Health check orchestrator

    Returns:
        HealthCheckResponse: Complete health check results

    Example:
        >>> response = await client.get("/health")
        >>> result = response.json()
        >>> print(f"Status: {result['status']}")
        >>> for check in result['checks']:
        ...     print(f"{check['component']}: {check['status']}")
    """
    # Execute all health checks in parallel
    health_result = await orchestrator.check_all()

    # Convert component results to response models
    checks = []
    for component_data in health_result["components"]:
        # Extract remediation from metadata if present
        remediation = component_data.get("metadata", {}).get(
            "remediation", None
        )

        check_response = HealthStatusResponse(
            component=component_data["component"],
            status=component_data["status"],
            latency_ms=component_data["latency_ms"],
            message=component_data["message"],
            metadata=component_data.get("metadata", {}),
            remediation=remediation,
        )
        checks.append(check_response)

    return HealthCheckResponse(
        status=health_result["status"],
        timestamp=datetime.utcnow().isoformat() + "Z",
        duration_ms=health_result["duration_ms"],
        checks=checks,
        summary=health_result["summary"],
    )


@router.get(
    "/status",
    response_model=StatusSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Quick status summary",
    description=(
        "Quick health status summary without detailed checks. "
        "Returns basic status and uptime information."
    ),
)
async def status_summary(
    orchestrator: HealthCheckOrchestrator = Depends(
        get_health_orchestrator
    ),
) -> StatusSummaryResponse:
    """Quick status summary without detailed checks.

    This endpoint provides a fast status overview including:
    - Overall system status
    - Number of health checks
    - Server uptime

    Executes full health checks but returns only summary information.

    Args:
        orchestrator: Health check orchestrator

    Returns:
        StatusSummaryResponse: Status summary

    Example:
        >>> response = await client.get("/health/status")
        >>> summary = response.json()
        >>> print(f"Status: {summary['status']}")
        >>> print(f"Uptime: {summary['uptime_seconds']}s")
    """
    # Execute health checks
    health_result = await orchestrator.check_all()

    # Calculate uptime
    uptime = time.time() - _app_start_time

    # Get total checks count
    checks_count = sum(health_result["summary"].values())

    return StatusSummaryResponse(
        status=health_result["status"],
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks_count=checks_count,
        uptime_seconds=round(uptime, 2),
    )


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Prometheus metrics",
    description=(
        "Prometheus metrics endpoint in exposition format. "
        "Returns all application metrics for monitoring."
    ),
    responses={
        200: {
            "description": "Metrics in Prometheus format",
            "content": {"text/plain": {"example": "# HELP http_requests_total ..."}},
        }
    },
)
async def metrics_endpoint(
    collector: MetricsCollector = Depends(get_metrics_collector),
) -> Response:
    """Prometheus metrics endpoint.

    This endpoint returns all application metrics in Prometheus
    exposition format for scraping by Prometheus server.

    Metrics include:
    - HTTP request metrics (count, duration, size)
    - Claude API metrics (calls, tokens, duration)
    - RAG pipeline metrics (duration, documents, confidence)
    - Database metrics (connections, queries, errors)
    - Cache metrics (operations, hit ratio)

    Args:
        collector: Metrics collector instance

    Returns:
        Response: Metrics in Prometheus text format

    Example:
        >>> response = await client.get("/health/metrics")
        >>> assert response.headers["content-type"] == "text/plain; charset=utf-8"
        >>> assert b"http_requests_total" in response.content
    """
    # Generate Prometheus metrics
    metrics_data = collector.generate_metrics()

    # Return as plain text with correct content type
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
