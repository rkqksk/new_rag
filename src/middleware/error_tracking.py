"""
Error Tracking Middleware
Automatic error tracking with Sentry integration
Version: v8.5.0
"""

import logging
import traceback
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time

from src.services.error_tracking_service import get_error_tracking_service, ErrorSeverity
from src.services.analytics_service import get_analytics_service

logger = logging.getLogger(__name__)


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """Error tracking middleware for FastAPI"""

    def __init__(
        self,
        app,
        track_performance: bool = True,
        track_errors_only: bool = False
    ):
        """
        Initialize error tracking middleware

        Args:
            app: FastAPI application
            track_performance: Track request performance
            track_errors_only: Only track errors (don't track successful requests)
        """
        super().__init__(app)
        self.track_performance = track_performance
        self.track_errors_only = track_errors_only

        logger.info("Error tracking middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error tracking"""

        # Start transaction for performance tracking
        error_tracker = get_error_tracking_service()
        transaction = None

        if self.track_performance and error_tracker.initialized:
            transaction = error_tracker.start_transaction(
                name=f"{request.method} {request.url.path}",
                op="http.server",
                description=f"{request.method} request to {request.url.path}"
            )

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Track successful request
            if not self.track_errors_only:
                await self._track_request(request, response.status_code, duration)

            # Finish transaction
            if transaction:
                transaction.finish()

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Track error
            await self._track_error(request, e, duration)

            # Finish transaction with error
            if transaction:
                transaction.finish()

            # Re-raise exception
            raise

    async def _track_request(self, request: Request, status_code: int, duration: float):
        """Track successful request"""
        try:
            analytics = get_analytics_service()

            # Get user ID if authenticated
            user = getattr(request.state, "user", None)
            user_id = user.id if user else None

            await analytics.track_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration=duration,
                user_id=user_id
            )

        except Exception as e:
            logger.error(f"Failed to track request: {e}")

    async def _track_error(self, request: Request, exception: Exception, duration: float):
        """Track error occurrence"""

        try:
            error_tracker = get_error_tracking_service()
            analytics = get_analytics_service()

            # Get user information
            user = getattr(request.state, "user", None)

            user_data = None
            if user:
                user_data = {
                    'id': user.id,
                    'email': getattr(user, 'email', None),
                    'role': getattr(user, 'role', None)
                }

            # Prepare context
            context = {
                'request': {
                    'method': request.method,
                    'url': str(request.url),
                    'path': request.url.path,
                    'query_params': dict(request.query_params),
                    'headers': dict(request.headers),
                    'client': request.client.host if request.client else None
                },
                'timing': {
                    'duration': duration
                }
            }

            # Prepare tags
            tags = {
                'method': request.method,
                'endpoint': request.url.path,
                'error_type': type(exception).__name__
            }

            # Determine severity
            severity = self._get_error_severity(exception)

            # Capture exception
            event_id = error_tracker.capture_exception(
                exception=exception,
                context=context,
                user=user_data,
                tags=tags,
                level=severity
            )

            # Track error in analytics
            await analytics.track_error(
                error_type=type(exception).__name__,
                severity=severity,
                message=str(exception),
                stacktrace=traceback.format_exc(),
                user_id=user.id if user else None
            )

            logger.error(
                f"Error tracked: {type(exception).__name__} "
                f"at {request.method} {request.url.path} "
                f"(event_id: {event_id})"
            )

        except Exception as e:
            logger.error(f"Failed to track error: {e}")

    def _get_error_severity(self, exception: Exception) -> str:
        """Determine error severity"""

        # HTTP exceptions
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code

            if status_code >= 500:
                return ErrorSeverity.ERROR
            elif status_code >= 400:
                return ErrorSeverity.WARNING
            else:
                return ErrorSeverity.INFO

        # System exceptions
        error_type = type(exception).__name__

        critical_errors = [
            'SystemExit',
            'KeyboardInterrupt',
            'MemoryError',
            'OSError'
        ]

        if error_type in critical_errors:
            return ErrorSeverity.FATAL

        # Database errors
        db_errors = [
            'OperationalError',
            'IntegrityError',
            'DatabaseError'
        ]

        if error_type in db_errors:
            return ErrorSeverity.ERROR

        # Default to error
        return ErrorSeverity.ERROR


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to error tracking"""

    def __init__(self, app):
        """Initialize request context middleware"""
        super().__init__(app)
        logger.info("Request context middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add breadcrumbs for request context"""

        error_tracker = get_error_tracking_service()

        if error_tracker.initialized:
            # Add request breadcrumb
            error_tracker.add_breadcrumb(
                message=f"{request.method} {request.url.path}",
                category="request",
                level=ErrorSeverity.INFO,
                data={
                    'url': str(request.url),
                    'method': request.method,
                    'query_params': dict(request.query_params)
                }
            )

        # Process request
        response = await call_next(request)

        return response


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic analytics tracking"""

    def __init__(self, app, track_all_requests: bool = True):
        """
        Initialize analytics middleware

        Args:
            app: FastAPI application
            track_all_requests: Track all requests (or only specific ones)
        """
        super().__init__(app)
        self.track_all_requests = track_all_requests

        logger.info("Analytics middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track request analytics"""

        # Record start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Track analytics
        if self.track_all_requests:
            try:
                analytics = get_analytics_service()

                # Get user ID if authenticated
                user = getattr(request.state, "user", None)
                user_id = user.id if user else None

                # Track active user
                if user_id:
                    await analytics.track_active_user(user_id, action='active')

                # Track request
                await analytics.track_request(
                    method=request.method,
                    endpoint=request.url.path,
                    status_code=response.status_code,
                    duration=duration,
                    user_id=user_id
                )

            except Exception as e:
                logger.error(f"Failed to track analytics: {e}")

        return response
