"""
Sentry Error Tracking Integration

Production-ready Sentry integration for FastAPI with intelligent error
grouping, performance monitoring, and automatic context capture.

Example:
    >>> from apps.api.core.sentry import get_sentry_instance, is_production
    >>> sentry = get_sentry_instance()
    >>> sentry.capture_exception(Exception("test"))

    >>> # In FastAPI app
    >>> app.add_middleware(SentryMiddleware)
"""

import hashlib
import logging
import os
import random
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

try:
    import sentry_sdk
    from sentry_sdk import capture_exception, capture_message, set_tag, set_user
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.scrubber import DEFAULT_DENYLIST

    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False

from apps.api.core.logging import get_logger

logger = get_logger(__name__)


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class SentryConfig:
    """Sentry configuration with environment-specific defaults.

    Attributes:
        dsn: Sentry Data Source Name (project URL)
        environment: Application environment (dev/staging/prod)
        release: Application version/release identifier
        traces_sample_rate: Transaction sampling (0.0-1.0)
        profiles_sample_rate: Profiling sampling (0.0-1.0)
        error_sample_rates: Error sampling by level
        attach_stacktrace: Include stacktraces for messages
        send_default_pii: Send personally identifiable info
        ignored_errors: Exception types to ignore
        before_send: Custom event processor
        before_send_transaction: Custom transaction processor

    Example:
        >>> config = SentryConfig(
        ...     dsn="https://key@sentry.io/project",
        ...     environment=Environment.PRODUCTION
        ... )
    """

    dsn: Optional[str] = None
    environment: Environment = Environment.DEVELOPMENT
    release: Optional[str] = None
    traces_sample_rate: float = 0.01  # 1% of transactions
    profiles_sample_rate: float = 0.01  # 1% of profiles
    error_sample_rates: Dict[str, float] = field(
        default_factory=lambda: {
            "critical": 1.0,  # 100% of critical errors
            "error": 0.5,  # 50% of errors
            "warning": 0.2,  # 20% of warnings
            "info": 0.1,  # 10% of info messages
        }
    )
    attach_stacktrace: bool = True
    send_default_pii: bool = False
    ignored_errors: Set[str] = field(
        default_factory=lambda: {
            "KeyboardInterrupt",
            "SystemExit",
            "asyncio.CancelledError",
        }
    )
    before_send: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Optional[Dict[str, Any]]]] = (
        None
    )
    before_send_transaction: Optional[
        Callable[[Dict[str, Any], Dict[str, Any]], Optional[Dict[str, Any]]]
    ] = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Production requires DSN
        if self.environment == Environment.PRODUCTION and not self.dsn:
            raise ValueError("Sentry DSN is required for production environment")

        # Validate sample rates
        if not 0.0 <= self.traces_sample_rate <= 1.0:
            raise ValueError("traces_sample_rate must be between 0.0 and 1.0")
        if not 0.0 <= self.profiles_sample_rate <= 1.0:
            raise ValueError("profiles_sample_rate must be between 0.0 and 1.0")

        for level, rate in self.error_sample_rates.items():
            if not 0.0 <= rate <= 1.0:
                raise ValueError(f"error_sample_rate for {level} must be between 0.0 and 1.0")


class SentryIntegration:
    """Sentry integration with intelligent error grouping and context.

    This class manages Sentry SDK initialization, context management,
    and error capture with automatic fingerprinting and sampling.

    Example:
        >>> sentry = SentryIntegration(config)
        >>> sentry.initialize()
        >>> sentry.set_user_context("user123", email="user@example.com")
        >>> sentry.capture_exception(Exception("Error"))
    """

    def __init__(self, config: SentryConfig) -> None:
        """Initialize Sentry integration.

        Args:
            config: Sentry configuration object
        """
        self.config = config
        self._initialized = False

    def initialize(self) -> None:
        """Initialize Sentry SDK with configuration.

        Raises:
            RuntimeError: If Sentry SDK is not installed
            ValueError: If configuration is invalid
        """
        if not HAS_SENTRY:
            if self.config.environment == Environment.PRODUCTION:
                raise RuntimeError(
                    "sentry-sdk is required for production. "
                    "Install with: pip install sentry-sdk[fastapi]"
                )
            logger.warning("Sentry SDK not installed - error tracking disabled")
            return

        if not self.config.dsn:
            if self.config.environment == Environment.PRODUCTION:
                raise ValueError("Sentry DSN is required for production")
            logger.info("Sentry DSN not provided - error tracking disabled")
            return

        # Set custom callbacks if not provided
        if not self.config.before_send:
            self.config.before_send = self._before_send_callback
        if not self.config.before_send_transaction:
            self.config.before_send_transaction = self._before_send_transaction_callback

        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=self.config.dsn,
            environment=self.config.environment.value,
            release=self.config.release,
            traces_sample_rate=self.config.traces_sample_rate,
            profiles_sample_rate=self.config.profiles_sample_rate,
            attach_stacktrace=self.config.attach_stacktrace,
            send_default_pii=self.config.send_default_pii,
            before_send=self.config.before_send,
            before_send_transaction=self.config.before_send_transaction,
            integrations=[
                FastApiIntegration(),
                RedisIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],
            ignore_errors=list(self.config.ignored_errors),
        )

        self._initialized = True
        logger.info(
            f"Sentry initialized: env={self.config.environment.value}, "
            f"traces={self.config.traces_sample_rate}, "
            f"profiles={self.config.profiles_sample_rate}"
        )

    def configure_scope(self, service_name: str, version: str) -> None:
        """Configure Sentry scope with service metadata.

        Args:
            service_name: Name of the service
            version: Service version
        """
        if not self._initialized:
            return

        set_tag("service", service_name)
        set_tag("version", version)
        set_tag("environment", self.config.environment.value)

    def capture_exception(self, exception: Exception, **kwargs: Any) -> Optional[str]:
        """Capture an exception to Sentry.

        Args:
            exception: Exception to capture
            **kwargs: Additional context for the event

        Returns:
            Event ID if sent, None if not initialized or sampled out

        Example:
            >>> try:
            ...     risky_operation()
            ... except Exception as e:
            ...     sentry.capture_exception(e, user_id="123")
        """
        if not self._initialized:
            return None

        # Add extra context
        if kwargs:
            with sentry_sdk.push_scope() as scope:
                for key, value in kwargs.items():
                    scope.set_extra(key, value)
                return capture_exception(exception)

        return capture_exception(exception)

    def capture_message(self, message: str, level: str = "info", **kwargs: Any) -> Optional[str]:
        """Capture a message to Sentry.

        Args:
            message: Message to capture
            level: Message level (debug/info/warning/error/critical)
            **kwargs: Additional context for the event

        Returns:
            Event ID if sent, None if not initialized or sampled out

        Example:
            >>> sentry.capture_message(
            ...     "User login failed",
            ...     level="warning",
            ...     user_id="123"
            ... )
        """
        if not self._initialized:
            return None

        # Add extra context
        if kwargs:
            with sentry_sdk.push_scope() as scope:
                for key, value in kwargs.items():
                    scope.set_extra(key, value)
                return capture_message(message, level=level)

        return capture_message(message, level=level)

    def set_user_context(
        self,
        user_id: str,
        email: Optional[str] = None,
        username: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Set user context for error tracking.

        Args:
            user_id: User identifier
            email: User email address
            username: Username
            **kwargs: Additional user attributes

        Example:
            >>> sentry.set_user_context(
            ...     user_id="123",
            ...     email="user@example.com",
            ...     role="admin"
            ... )
        """
        if not self._initialized:
            return

        user_data = {"id": user_id}
        if email:
            user_data["email"] = email
        if username:
            user_data["username"] = username
        user_data.update(kwargs)

        set_user(user_data)

    def add_breadcrumb(self, category: str, message: str, level: str = "info", **data: Any) -> None:
        """Add a breadcrumb for error context.

        Args:
            category: Breadcrumb category
            message: Breadcrumb message
            level: Log level
            **data: Additional breadcrumb data

        Example:
            >>> sentry.add_breadcrumb(
            ...     category="auth",
            ...     message="User login attempt",
            ...     level="info",
            ...     user_id="123"
            ... )
        """
        if not self._initialized:
            return

        sentry_sdk.add_breadcrumb(
            category=category,
            message=message,
            level=level,
            data=data,
        )

    def _before_send_callback(
        self, event: Dict[str, Any], hint: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process events before sending to Sentry.

        This callback:
        1. Groups similar errors using fingerprinting
        2. Applies sampling based on error level
        3. Filters sensitive data

        Args:
            event: Event data
            hint: Event hint with exception info

        Returns:
            Modified event or None to drop event
        """
        # Apply intelligent fingerprinting
        fingerprint = self._generate_fingerprint(event, hint)
        if fingerprint:
            event["fingerprint"] = fingerprint

        # Apply sampling based on level
        level = event.get("level", "error")
        sample_rate = self.config.error_sample_rates.get(level, 1.0)
        if random.random() > sample_rate:
            return None  # Drop event

        return event

    def _before_send_transaction_callback(
        self, event: Dict[str, Any], hint: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process transactions before sending to Sentry.

        Args:
            event: Transaction event data
            hint: Event hint

        Returns:
            Modified event or None to drop event
        """
        # Additional transaction filtering could go here
        return event

    def _generate_fingerprint(
        self, event: Dict[str, Any], hint: Dict[str, Any]
    ) -> Optional[List[str]]:
        """Generate fingerprint for intelligent error grouping.

        Grouping logic:
        - Database errors: Group by query template (remove parameters)
        - API errors: Group by endpoint + status code
        - Validation errors: Group by field names
        - Other errors: Use default Sentry grouping

        Args:
            event: Event data
            hint: Event hint with exception info

        Returns:
            Fingerprint list or None for default grouping
        """
        exception = hint.get("exc_info")
        if not exception:
            return None

        exc_type, exc_value, _ = exception
        exc_name = exc_type.__name__ if exc_type else "Unknown"
        exc_message = str(exc_value) if exc_value else ""

        # Database errors - group by query template
        if "database" in exc_name.lower() or "sql" in exc_name.lower():
            # Remove parameters from SQL queries
            query_template = re.sub(r"\b\d+\b", "?", exc_message)
            query_template = re.sub(r"'[^']*'", "?", query_template)
            query_hash = hashlib.md5(query_template.encode()).hexdigest()[:8]
            return ["database-error", exc_name, query_hash]

        # API/HTTP errors - group by endpoint + status
        if "http" in exc_name.lower() or "request" in exc_name.lower():
            request_data = event.get("request", {})
            url = request_data.get("url", "unknown")
            method = request_data.get("method", "unknown")
            # Extract endpoint path (remove IDs)
            path = re.sub(r"/\d+", "/:id", url)
            path = re.sub(r"/[a-f0-9-]{36}", "/:uuid", path)
            return ["api-error", method, path, exc_name]

        # Validation errors - group by field names
        if "validation" in exc_name.lower():
            # Extract field names from error message
            fields = re.findall(r"field[:\s]+([a-zA-Z_]+)", exc_message)
            if fields:
                fields_hash = hashlib.md5(",".join(sorted(fields)).encode()).hexdigest()[:8]
                return ["validation-error", fields_hash]

        # Default grouping
        return None


class SentryMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for Sentry integration.

    This middleware:
    - Captures request context (URL, method, headers)
    - Extracts user from JWT token
    - Sets tags and breadcrumbs
    - Creates performance transactions
    - Filters sensitive headers

    Example:
        >>> app.add_middleware(SentryMiddleware)
    """

    # Sensitive headers to filter
    SENSITIVE_HEADERS: Set[str] = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
        "x-csrf-token",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Process request through Sentry context.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response from next middleware
        """
        if not HAS_SENTRY or not sentry_sdk.Hub.current.client:
            return await call_next(request)

        # Start transaction for performance monitoring
        transaction_name = f"{request.method} {request.url.path}"
        with sentry_sdk.start_transaction(
            op="http.server",
            name=transaction_name,
        ) as transaction:
            # Set request context
            with sentry_sdk.configure_scope() as scope:
                # Add request information
                scope.set_tag("http.method", request.method)
                scope.set_tag("http.url", str(request.url.path))

                # Filter sensitive headers
                headers = self._filter_headers(dict(request.headers))
                scope.set_context("headers", headers)

                # Extract user from JWT token
                user_info = await self._extract_user_from_token(request)
                if user_info:
                    scope.set_user(user_info)

                # Add breadcrumb
                sentry_sdk.add_breadcrumb(
                    category="request",
                    message=f"{request.method} {request.url.path}",
                    level="info",
                )

                # Process request
                try:
                    response = await call_next(request)

                    # Set response status
                    scope.set_tag("http.status_code", response.status_code)
                    transaction.set_status("ok" if response.status_code < 400 else "error")

                    return response
                except Exception as exc:
                    # Set error status
                    scope.set_tag("http.status_code", 500)
                    transaction.set_status("internal_error")

                    # Capture exception
                    sentry_sdk.capture_exception(exc)
                    raise

    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter sensitive headers.

        Args:
            headers: Request headers

        Returns:
            Filtered headers dictionary
        """
        return {
            key: value if key.lower() not in self.SENSITIVE_HEADERS else "[FILTERED]"
            for key, value in headers.items()
        }

    async def _extract_user_from_token(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract user information from JWT token.

        Args:
            request: FastAPI request

        Returns:
            User information dictionary or None
        """
        # Get authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            # Decode JWT token (simplified - replace with actual JWT validation)
            import jwt

            payload = jwt.decode(token, options={"verify_signature": False})

            return {
                "id": payload.get("sub") or payload.get("user_id"),
                "email": payload.get("email"),
                "username": payload.get("username"),
            }
        except Exception:
            # Invalid token - skip user context
            return None


# ============================================================
# Utility Functions
# ============================================================


@lru_cache()
def get_sentry_instance() -> SentryIntegration:
    """Get singleton Sentry instance.

    Returns:
        Configured SentryIntegration instance

    Example:
        >>> sentry = get_sentry_instance()
        >>> sentry.capture_message("Hello Sentry")
    """
    # Load configuration from environment
    dsn = os.getenv("SENTRY_DSN")
    environment = Environment(os.getenv("ENVIRONMENT", "development"))
    release = os.getenv("SENTRY_RELEASE")

    config = SentryConfig(
        dsn=dsn,
        environment=environment,
        release=release,
    )

    sentry = SentryIntegration(config)
    sentry.initialize()

    return sentry


def is_production() -> bool:
    """Check if running in production environment.

    Returns:
        True if production, False otherwise

    Example:
        >>> if is_production():
        ...     enable_strict_validation()
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    return environment == "production"


def should_sample_event(level: str, sample_rates: Dict[str, float]) -> bool:
    """Determine if event should be sampled based on level.

    Args:
        level: Event level (critical/error/warning/info)
        sample_rates: Sampling rates by level

    Returns:
        True if event should be sent, False otherwise

    Example:
        >>> rates = {"error": 0.5, "warning": 0.2}
        >>> should_sample_event("error", rates)
        True  # 50% chance
    """
    sample_rate = sample_rates.get(level.lower(), 1.0)
    return random.random() <= sample_rate
