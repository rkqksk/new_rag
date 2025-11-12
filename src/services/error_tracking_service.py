"""
Error Tracking Service
Sentry integration for error monitoring and alerting
Version: v8.5.0
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback
import sys
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

logger = logging.getLogger(__name__)


class ErrorSeverity(str):
    """Error severity levels"""
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    FATAL = 'fatal'


class ErrorTrackingService:
    """Sentry-based error tracking and monitoring"""

    def __init__(
        self,
        dsn: Optional[str] = None,
        environment: str = 'development',
        release: Optional[str] = None,
        sample_rate: float = 1.0,
        traces_sample_rate: float = 0.1
    ):
        """
        Initialize error tracking service

        Args:
            dsn: Sentry DSN (Data Source Name)
            environment: Environment name (development, staging, production)
            release: Application release version
            sample_rate: Error sampling rate (0.0 - 1.0)
            traces_sample_rate: Transaction tracing sample rate (0.0 - 1.0)
        """
        self.dsn = dsn
        self.environment = environment
        self.release = release or 'v8.5.0'
        self.sample_rate = sample_rate
        self.traces_sample_rate = traces_sample_rate
        self.initialized = False

        if dsn:
            self._initialize_sentry()

    def _initialize_sentry(self):
        """Initialize Sentry SDK"""
        try:
            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                release=self.release,
                sample_rate=self.sample_rate,
                traces_sample_rate=self.traces_sample_rate,
                integrations=[
                    FastApiIntegration(),
                    RedisIntegration(),
                    SqlalchemyIntegration(),
                    AsyncioIntegration(),
                ],
                # Performance monitoring
                enable_tracing=True,
                # Profiling
                profiles_sample_rate=0.1,
                # Send default PII (Personally Identifiable Information)
                send_default_pii=False,
                # Attach stacktrace to messages
                attach_stacktrace=True,
                # Max breadcrumbs
                max_breadcrumbs=50,
            )

            self.initialized = True
            logger.info(f"Sentry initialized: {self.environment} - {self.release}")

        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            self.initialized = False

    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        user: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        level: str = ErrorSeverity.ERROR
    ) -> Optional[str]:
        """
        Capture exception with context

        Args:
            exception: Exception to capture
            context: Additional context data
            user: User information
            tags: Tags for filtering
            level: Error severity level

        Returns:
            Event ID if captured, None otherwise
        """
        if not self.initialized:
            logger.error(f"Sentry not initialized: {exception}")
            return None

        try:
            # Set scope
            with sentry_sdk.push_scope() as scope:
                # Set level
                scope.level = level

                # Set user
                if user:
                    scope.set_user(user)

                # Set tags
                if tags:
                    for key, value in tags.items():
                        scope.set_tag(key, value)

                # Set context
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)

                # Capture exception
                event_id = sentry_sdk.capture_exception(exception)
                logger.info(f"Exception captured: {event_id}")
                return event_id

        except Exception as e:
            logger.error(f"Failed to capture exception: {e}")
            return None

    def capture_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        level: str = ErrorSeverity.INFO
    ) -> Optional[str]:
        """
        Capture message with context

        Args:
            message: Message to capture
            context: Additional context data
            user: User information
            tags: Tags for filtering
            level: Message severity level

        Returns:
            Event ID if captured, None otherwise
        """
        if not self.initialized:
            logger.info(f"Sentry not initialized: {message}")
            return None

        try:
            with sentry_sdk.push_scope() as scope:
                scope.level = level

                if user:
                    scope.set_user(user)

                if tags:
                    for key, value in tags.items():
                        scope.set_tag(key, value)

                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)

                event_id = sentry_sdk.capture_message(message, level=level)
                logger.debug(f"Message captured: {event_id}")
                return event_id

        except Exception as e:
            logger.error(f"Failed to capture message: {e}")
            return None

    def add_breadcrumb(
        self,
        message: str,
        category: str = 'default',
        level: str = ErrorSeverity.INFO,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Add breadcrumb for context trail

        Args:
            message: Breadcrumb message
            category: Breadcrumb category
            level: Breadcrumb level
            data: Additional data
        """
        if not self.initialized:
            return

        try:
            sentry_sdk.add_breadcrumb(
                category=category,
                message=message,
                level=level,
                data=data or {}
            )
        except Exception as e:
            logger.error(f"Failed to add breadcrumb: {e}")

    def set_user(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs
    ):
        """
        Set user context

        Args:
            user_id: User ID
            email: User email
            username: Username
            ip_address: IP address
            **kwargs: Additional user data
        """
        if not self.initialized:
            return

        try:
            user_data = {
                'id': user_id,
                'email': email,
                'username': username,
                'ip_address': ip_address,
                **kwargs
            }

            # Remove None values
            user_data = {k: v for k, v in user_data.items() if v is not None}

            sentry_sdk.set_user(user_data)

        except Exception as e:
            logger.error(f"Failed to set user: {e}")

    def set_tag(self, key: str, value: str):
        """
        Set global tag

        Args:
            key: Tag key
            value: Tag value
        """
        if not self.initialized:
            return

        try:
            sentry_sdk.set_tag(key, value)
        except Exception as e:
            logger.error(f"Failed to set tag: {e}")

    def set_context(self, key: str, value: Dict[str, Any]):
        """
        Set global context

        Args:
            key: Context key
            value: Context data
        """
        if not self.initialized:
            return

        try:
            sentry_sdk.set_context(key, value)
        except Exception as e:
            logger.error(f"Failed to set context: {e}")

    def start_transaction(
        self,
        name: str,
        op: str = 'http.server',
        description: Optional[str] = None
    ):
        """
        Start performance transaction

        Args:
            name: Transaction name
            op: Operation type
            description: Optional description

        Returns:
            Transaction object
        """
        if not self.initialized:
            return None

        try:
            transaction = sentry_sdk.start_transaction(
                name=name,
                op=op,
                description=description
            )
            return transaction

        except Exception as e:
            logger.error(f"Failed to start transaction: {e}")
            return None

    def capture_api_error(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        error: Exception,
        user_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Capture API error with rich context

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            error: Exception
            user_id: Optional user ID
            request_data: Optional request data

        Returns:
            Event ID
        """
        context = {
            'api': {
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'timestamp': datetime.now().isoformat(),
            }
        }

        if request_data:
            context['request'] = request_data

        user = {'id': user_id} if user_id else None

        tags = {
            'endpoint': endpoint,
            'method': method,
            'status_code': str(status_code),
        }

        return self.capture_exception(
            exception=error,
            context=context,
            user=user,
            tags=tags,
            level=ErrorSeverity.ERROR
        )

    def capture_search_error(
        self,
        query: str,
        error: Exception,
        search_type: str = 'hybrid',
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Capture search error

        Args:
            query: Search query
            error: Exception
            search_type: Type of search
            user_id: Optional user ID

        Returns:
            Event ID
        """
        context = {
            'search': {
                'query': query,
                'type': search_type,
                'timestamp': datetime.now().isoformat(),
            }
        }

        user = {'id': user_id} if user_id else None

        tags = {
            'search_type': search_type,
            'query_length': str(len(query)),
        }

        return self.capture_exception(
            exception=error,
            context=context,
            user=user,
            tags=tags,
            level=ErrorSeverity.ERROR
        )

    def capture_database_error(
        self,
        query: str,
        error: Exception,
        operation: str = 'select',
        table: Optional[str] = None
    ) -> Optional[str]:
        """
        Capture database error

        Args:
            query: SQL query
            error: Exception
            operation: Database operation
            table: Optional table name

        Returns:
            Event ID
        """
        context = {
            'database': {
                'query': query[:500],  # Limit query length
                'operation': operation,
                'table': table,
                'timestamp': datetime.now().isoformat(),
            }
        }

        tags = {
            'db_operation': operation,
            'db_table': table or 'unknown',
        }

        return self.capture_exception(
            exception=error,
            context=context,
            tags=tags,
            level=ErrorSeverity.ERROR
        )

    def capture_ml_error(
        self,
        model: str,
        error: Exception,
        operation: str = 'inference',
        input_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Capture ML/AI error

        Args:
            model: Model name
            error: Exception
            operation: ML operation
            input_data: Optional input data

        Returns:
            Event ID
        """
        context = {
            'ml': {
                'model': model,
                'operation': operation,
                'timestamp': datetime.now().isoformat(),
            }
        }

        if input_data:
            context['input'] = input_data

        tags = {
            'model': model,
            'ml_operation': operation,
        }

        return self.capture_exception(
            exception=error,
            context=context,
            tags=tags,
            level=ErrorSeverity.ERROR
        )

    def flush(self, timeout: int = 2):
        """
        Flush pending events

        Args:
            timeout: Timeout in seconds
        """
        if not self.initialized:
            return

        try:
            sentry_sdk.flush(timeout=timeout)
            logger.info("Flushed Sentry events")
        except Exception as e:
            logger.error(f"Failed to flush Sentry: {e}")

    def close(self):
        """Close Sentry client"""
        if self.initialized:
            try:
                sentry_sdk.flush(timeout=5)
                sentry_sdk.close()
                self.initialized = False
                logger.info("Closed Sentry client")
            except Exception as e:
                logger.error(f"Failed to close Sentry: {e}")

    def get_last_event_id(self) -> Optional[str]:
        """Get last captured event ID"""
        if not self.initialized:
            return None

        try:
            return sentry_sdk.last_event_id()
        except Exception as e:
            logger.error(f"Failed to get last event ID: {e}")
            return None


# Singleton instance
_error_tracking_service = None


def get_error_tracking_service(
    dsn: Optional[str] = None,
    environment: str = 'development',
    release: Optional[str] = None
) -> ErrorTrackingService:
    """Get error tracking service singleton"""
    global _error_tracking_service
    if _error_tracking_service is None:
        _error_tracking_service = ErrorTrackingService(
            dsn=dsn,
            environment=environment,
            release=release
        )
    return _error_tracking_service
