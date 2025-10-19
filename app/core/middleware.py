"""
FastAPI Middleware for Metrics Collection

Automatically collects HTTP metrics for all requests/responses
"""
import time
import logging
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes,
    active_requests,
    errors_total,
)

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that collects HTTP request/response metrics

    Tracks:
    - Request count by method, endpoint, status
    - Request latency (duration)
    - Request/response sizes
    - Active request count
    - Error rates
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response with metrics collected
        """
        # Extract metadata
        method = request.method
        path = request.url.path
        endpoint = f"{method} {path}"

        # Track active requests
        active_requests.labels(endpoint=endpoint).inc()

        # Get request size
        try:
            request_body = await request.body()
            request_size = len(request_body)
            http_request_size_bytes.labels(
                method=method,
                endpoint=path
            ).observe(request_size)
        except Exception as e:
            logger.debug(f"Could not measure request size: {e}")
            request_size = 0

        # Measure response time
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            logger.error(f"Request failed: {e}")
            errors_total.labels(
                error_type="exception",
                endpoint=path
            ).inc()

            # Re-raise the exception
            raise
        finally:
            # Decrement active requests
            active_requests.labels(endpoint=endpoint).dec()

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        status_code = response.status_code

        # Increment total requests counter
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status=status_code
        ).inc()

        # Record request duration
        http_request_duration_seconds.labels(
            method=method,
            endpoint=path
        ).observe(duration)

        # Record response size
        try:
            response_size = len(response.body) if hasattr(response, 'body') else 0
            http_response_size_bytes.labels(
                method=method,
                endpoint=path
            ).observe(response_size)
        except Exception as e:
            logger.debug(f"Could not measure response size: {e}")

        # Track errors
        if status_code >= 400:
            errors_total.labels(
                error_type=f"http_{status_code}",
                endpoint=path
            ).inc()

        return response
