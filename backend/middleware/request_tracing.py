"""Request Tracing Middleware - Correlation IDs"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import correlation_id_var, get_logger, request_path_var, user_session_var

logger = get_logger(__name__)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Adds correlation ID to every request for distributed tracing.

    Features:
    - Generates unique correlation ID per request
    - Extracts from header if provided (X-Correlation-ID)
    - Stores in context variable for access throughout request lifecycle
    - Returns correlation ID in response header
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Set context variables
        correlation_id_var.set(correlation_id)
        request_path_var.set(f"{request.method} {request.url.path}")

        # Extract session ID from query params or headers if available
        session_id = request.query_params.get("session_id") or request.headers.get("X-Session-ID")
        if session_id:
            user_session_var.set(session_id)

        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else None,
            },
        )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-Duration-Ms"] = f"{duration_ms:.2f}"

        # Log request completion
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
