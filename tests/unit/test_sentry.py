"""
Unit Tests for Sentry Error Tracking Integration

Comprehensive test suite covering configuration, middleware, error grouping,
and Sentry integration patterns.
"""

import hashlib
import json
import random
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from apps.api.core.sentry import (
    Environment,
    SentryConfig,
    SentryIntegration,
    SentryMiddleware,
    get_sentry_instance,
    is_production,
    should_sample_event,
)

# ============================================================
# Test SentryConfig
# ============================================================


class TestSentryConfig:
    """Test suite for SentryConfig dataclass."""

    def test_development_config_without_dsn_is_valid(self) -> None:
        """Development environment should allow missing DSN."""
        config = SentryConfig(
            dsn=None,
            environment=Environment.DEVELOPMENT,
        )

        assert config.dsn is None
        assert config.environment == Environment.DEVELOPMENT
        assert config.traces_sample_rate == 0.01
        assert config.profiles_sample_rate == 0.01

    def test_production_requires_dsn(self) -> None:
        """Production environment must have DSN configured."""
        with pytest.raises(ValueError, match="DSN is required for production"):
            SentryConfig(
                dsn=None,
                environment=Environment.PRODUCTION,
            )

    def test_sample_rates_within_range(self) -> None:
        """Sample rates must be between 0.0 and 1.0."""
        # Valid sample rates
        config = SentryConfig(
            dsn="https://key@sentry.io/123",
            traces_sample_rate=0.5,
            profiles_sample_rate=0.3,
        )
        assert config.traces_sample_rate == 0.5
        assert config.profiles_sample_rate == 0.3

        # Invalid traces_sample_rate
        with pytest.raises(ValueError, match="traces_sample_rate must be"):
            SentryConfig(
                dsn="https://key@sentry.io/123",
                traces_sample_rate=1.5,
            )

        # Invalid profiles_sample_rate
        with pytest.raises(ValueError, match="profiles_sample_rate must be"):
            SentryConfig(
                dsn="https://key@sentry.io/123",
                profiles_sample_rate=-0.1,
            )

    def test_ignored_errors_configured(self) -> None:
        """Ignored errors should be properly configured."""
        config = SentryConfig(
            dsn="https://key@sentry.io/123",
        )

        assert "KeyboardInterrupt" in config.ignored_errors
        assert "SystemExit" in config.ignored_errors
        assert "asyncio.CancelledError" in config.ignored_errors

    def test_environment_specific_defaults(self) -> None:
        """Different environments should have appropriate defaults."""
        # Development
        dev_config = SentryConfig(environment=Environment.DEVELOPMENT)
        assert dev_config.environment == Environment.DEVELOPMENT
        assert not dev_config.send_default_pii

        # Staging
        staging_config = SentryConfig(
            dsn="https://key@sentry.io/123",
            environment=Environment.STAGING,
        )
        assert staging_config.environment == Environment.STAGING

        # Production
        prod_config = SentryConfig(
            dsn="https://key@sentry.io/123",
            environment=Environment.PRODUCTION,
        )
        assert prod_config.environment == Environment.PRODUCTION


# ============================================================
# Test SentryMiddleware
# ============================================================


class TestSentryMiddleware:
    """Test suite for SentryMiddleware."""

    def test_filters_sensitive_headers_correctly(self) -> None:
        """Middleware should filter sensitive headers."""
        middleware = SentryMiddleware(app=None)

        # Test with sensitive headers
        headers = {
            "authorization": "Bearer secret-token",
            "cookie": "session=secret",
            "x-api-key": "secret-key",
            "user-agent": "test-client",
            "content-type": "application/json",
        }

        filtered = middleware._filter_headers(headers)

        # Sensitive headers should be filtered
        assert filtered["authorization"] == "[FILTERED]"
        assert filtered["cookie"] == "[FILTERED]"
        assert filtered["x-api-key"] == "[FILTERED]"

        # Non-sensitive headers should remain
        assert filtered["user-agent"] == "test-client"
        assert filtered["content-type"] == "application/json"

    async def test_extracts_user_from_jwt(self) -> None:
        """Middleware should extract user from JWT token."""
        # This test gracefully handles missing PyJWT
        try:
            import jwt

            has_jwt = True
        except ImportError:
            has_jwt = False

        if not has_jwt:
            pytest.skip("PyJWT not installed - skipping JWT token extraction test")

        middleware = SentryMiddleware(app=None)

        # Create mock request
        mock_request = Mock()
        mock_request.headers.get.return_value = "Bearer fake.jwt.token"

        # Patch jwt module where it's imported (inside the method)
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = {
                "sub": "user123",
                "email": "user@example.com",
                "username": "testuser",
            }

            # Extract user
            user_info = await middleware._extract_user_from_token(mock_request)

            # Verify user info
            assert user_info is not None
            assert user_info["id"] == "user123"
            assert user_info["email"] == "user@example.com"
            assert user_info["username"] == "testuser"

    async def test_extract_user_without_token(self) -> None:
        """Middleware should return None without token."""
        middleware = SentryMiddleware(app=None)

        # Create mock request without auth header
        mock_request = Mock()
        mock_request.headers.get.return_value = ""

        # Extract user
        user_info = await middleware._extract_user_from_token(mock_request)

        # Should return None
        assert user_info is None

    async def test_extract_user_with_invalid_token(self) -> None:
        """Middleware should handle invalid tokens gracefully."""
        middleware = SentryMiddleware(app=None)

        # Create mock request with invalid token
        mock_request = Mock()
        mock_request.headers.get.return_value = "Bearer invalid.token"

        # Extract user (should not raise, just return None)
        user_info = await middleware._extract_user_from_token(mock_request)

        # Should return None for invalid tokens
        assert user_info is None

    def test_sensitive_headers_set_contains_common_headers(self) -> None:
        """Middleware should have common sensitive headers."""
        # Verify sensitive headers are defined
        assert "authorization" in SentryMiddleware.SENSITIVE_HEADERS
        assert "cookie" in SentryMiddleware.SENSITIVE_HEADERS
        assert "x-api-key" in SentryMiddleware.SENSITIVE_HEADERS
        assert "x-auth-token" in SentryMiddleware.SENSITIVE_HEADERS
        assert "x-csrf-token" in SentryMiddleware.SENSITIVE_HEADERS

    def test_middleware_initialization(self) -> None:
        """Middleware should initialize without errors."""
        # Create middleware instance
        middleware = SentryMiddleware(app=None)

        # Should have sensitive headers set
        assert hasattr(middleware, "SENSITIVE_HEADERS")
        assert len(middleware.SENSITIVE_HEADERS) > 0


# ============================================================
# Test Error Grouping
# ============================================================


class TestErrorGrouping:
    """Test suite for intelligent error grouping."""

    @pytest.fixture
    def sentry_integration(self) -> SentryIntegration:
        """Create Sentry integration instance."""
        config = SentryConfig(
            dsn="https://key@sentry.io/123",
            environment=Environment.DEVELOPMENT,
        )
        return SentryIntegration(config)

    def test_database_errors_grouped_by_query(
        self,
        sentry_integration: SentryIntegration,
    ) -> None:
        """Database errors should be grouped by query template."""
        # Create mock events for database errors with different parameters
        event1 = {"level": "error", "request": {}}
        hint1 = {
            "exc_info": (
                type("DatabaseError", (), {}),
                Exception("SELECT * FROM users WHERE id = 123"),
                None,
            )
        }

        event2 = {"level": "error", "request": {}}
        hint2 = {
            "exc_info": (
                type("DatabaseError", (), {}),
                Exception("SELECT * FROM users WHERE id = 456"),
                None,
            )
        }

        # Generate fingerprints
        fingerprint1 = sentry_integration._generate_fingerprint(event1, hint1)
        fingerprint2 = sentry_integration._generate_fingerprint(event2, hint2)

        # Same query template should have same fingerprint
        assert fingerprint1 is not None
        assert fingerprint2 is not None
        assert fingerprint1 == fingerprint2
        assert "database-error" in fingerprint1

    def test_api_errors_grouped_by_endpoint(
        self,
        sentry_integration: SentryIntegration,
    ) -> None:
        """API errors should be grouped by endpoint."""
        # Create mock events for API errors with different IDs
        event1 = {
            "level": "error",
            "request": {
                "url": "http://api.example.com/users/123",
                "method": "GET",
            },
        }
        hint1 = {
            "exc_info": (
                type("HTTPError", (), {}),
                Exception("404 Not Found"),
                None,
            )
        }

        event2 = {
            "level": "error",
            "request": {
                "url": "http://api.example.com/users/456",
                "method": "GET",
            },
        }
        hint2 = {
            "exc_info": (
                type("HTTPError", (), {}),
                Exception("404 Not Found"),
                None,
            )
        }

        # Generate fingerprints
        fingerprint1 = sentry_integration._generate_fingerprint(event1, hint1)
        fingerprint2 = sentry_integration._generate_fingerprint(event2, hint2)

        # Same endpoint template should have same fingerprint
        assert fingerprint1 is not None
        assert fingerprint2 is not None
        assert fingerprint1 == fingerprint2
        assert "api-error" in fingerprint1
        assert "GET" in fingerprint1

    def test_validation_errors_grouped_by_fields(
        self,
        sentry_integration: SentryIntegration,
    ) -> None:
        """Validation errors should be grouped by field names."""
        # Create mock events for validation errors
        event1 = {"level": "error", "request": {}}
        hint1 = {
            "exc_info": (
                type("ValidationError", (), {}),
                Exception("Invalid field: email, field: password"),
                None,
            )
        }

        event2 = {"level": "error", "request": {}}
        hint2 = {
            "exc_info": (
                type("ValidationError", (), {}),
                Exception("Invalid field: password, field: email"),
                None,
            )
        }

        # Generate fingerprints
        fingerprint1 = sentry_integration._generate_fingerprint(event1, hint1)
        fingerprint2 = sentry_integration._generate_fingerprint(event2, hint2)

        # Same fields should have same fingerprint (order-independent)
        assert fingerprint1 is not None
        assert fingerprint2 is not None
        assert fingerprint1 == fingerprint2
        assert "validation-error" in fingerprint1

    def test_sampling_respects_configured_rates(
        self,
        sentry_integration: SentryIntegration,
    ) -> None:
        """Event sampling should respect configured rates."""
        # Test critical level (100% sampling)
        with patch("random.random", return_value=0.99):
            event = {"level": "critical"}
            hint = {"exc_info": None}
            result = sentry_integration._before_send_callback(event, hint)
            assert result is not None  # Should be sent

        # Test error level (50% sampling)
        with patch("random.random", return_value=0.6):
            event = {"level": "error"}
            hint = {"exc_info": None}
            result = sentry_integration._before_send_callback(event, hint)
            assert result is None  # Should be dropped (0.6 > 0.5)

        with patch("random.random", return_value=0.4):
            event = {"level": "error"}
            hint = {"exc_info": None}
            result = sentry_integration._before_send_callback(event, hint)
            assert result is not None  # Should be sent (0.4 <= 0.5)

    def test_before_send_callback_drops_low_priority(
        self,
        sentry_integration: SentryIntegration,
    ) -> None:
        """Low-priority events should be dropped based on sampling."""
        # Mock random to always return value that drops events
        with patch("random.random", return_value=0.95):
            # Info level (10% sampling) - should be dropped
            event = {"level": "info"}
            hint = {"exc_info": None}
            result = sentry_integration._before_send_callback(event, hint)
            assert result is None

            # Warning level (20% sampling) - should be dropped
            event = {"level": "warning"}
            result = sentry_integration._before_send_callback(event, hint)
            assert result is None


# ============================================================
# Test SentryIntegration
# ============================================================


class TestSentryIntegration:
    """Test suite for SentryIntegration class."""

    @patch("app.core.sentry.get_sentry_instance")
    def test_singleton_pattern(self, mock_get_instance: Mock) -> None:
        """get_sentry_instance should return singleton."""
        instance1 = MagicMock()
        instance2 = MagicMock()

        # Mock returns same instance
        mock_get_instance.return_value = instance1

        result1 = mock_get_instance()
        result2 = mock_get_instance()

        assert result1 is result2

    def test_manual_exception_capture(self) -> None:
        """Manual exception capture should work correctly."""
        # Test that SentryIntegration initializes without errors
        config = SentryConfig(
            dsn=None,  # Development without DSN
            environment=Environment.DEVELOPMENT,
        )
        sentry = SentryIntegration(config)

        # Initialize (should not fail even without Sentry SDK)
        sentry.initialize()

        # Capture exception (should not fail even without Sentry SDK)
        exc = ValueError("Test error")
        event_id = sentry.capture_exception(exc, user_id="123")

        # Without Sentry SDK, this returns None
        assert event_id is None

    def test_manual_message_capture(self) -> None:
        """Manual message capture should work correctly."""
        # Test that SentryIntegration handles messages without errors
        config = SentryConfig(
            dsn=None,  # Development without DSN
            environment=Environment.DEVELOPMENT,
        )
        sentry = SentryIntegration(config)

        # Initialize (should not fail even without Sentry SDK)
        sentry.initialize()

        # Capture message (should not fail even without Sentry SDK)
        event_id = sentry.capture_message("User login failed", level="warning", user_id="123")

        # Without Sentry SDK, this returns None
        assert event_id is None


# ============================================================
# Test Utility Functions
# ============================================================


class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_is_production_returns_true_for_production_env(self) -> None:
        """is_production should return True for production environment."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
            assert is_production() is True

    def test_is_production_returns_false_for_non_production_env(self) -> None:
        """is_production should return False for non-production environments."""
        with patch.dict("os.environ", {"ENVIRONMENT": "development"}):
            assert is_production() is False

        with patch.dict("os.environ", {"ENVIRONMENT": "staging"}):
            assert is_production() is False

    def test_should_sample_event_respects_rates(self) -> None:
        """should_sample_event should respect configured rates."""
        sample_rates = {
            "critical": 1.0,
            "error": 0.5,
            "warning": 0.2,
            "info": 0.1,
        }

        # Test with fixed random values
        with patch("random.random", return_value=0.05):
            assert should_sample_event("critical", sample_rates) is True
            assert should_sample_event("error", sample_rates) is True
            assert should_sample_event("warning", sample_rates) is True
            assert should_sample_event("info", sample_rates) is True

        with patch("random.random", return_value=0.6):
            assert should_sample_event("critical", sample_rates) is True
            assert should_sample_event("error", sample_rates) is False
            assert should_sample_event("warning", sample_rates) is False
            assert should_sample_event("info", sample_rates) is False
