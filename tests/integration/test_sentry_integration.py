"""
Integration Tests for Sentry Error Tracking

Integration tests verifying Sentry works correctly with FastAPI application
and configuration, focusing on core integration logic without TestClient.

Note: These tests focus on integration logic rather than end-to-end HTTP
testing due to httpx/starlette version compatibility issues in the environment.
"""

import hashlib
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import FastAPI

from app.core.sentry import (
    Environment,
    SentryConfig,
    SentryIntegration,
    SentryMiddleware,
)


# ============================================================
# Test Sentry Configuration Integration
# ============================================================


class TestSentryConfigIntegration:
    """Integration tests for Sentry configuration."""

    def test_development_config_allows_missing_dsn(self) -> None:
        """Development environment should allow missing DSN."""
        config = SentryConfig(
            dsn=None,
            environment=Environment.DEVELOPMENT,
        )

        # Should create config without errors
        assert config.environment == Environment.DEVELOPMENT
        assert config.dsn is None

    def test_production_config_requires_dsn(self) -> None:
        """Production environment requires DSN."""
        with pytest.raises(ValueError, match="DSN is required for production"):
            SentryConfig(
                dsn=None,
                environment=Environment.PRODUCTION,
            )

    def test_staging_config_with_dsn(self) -> None:
        """Staging environment should work with DSN."""
        config = SentryConfig(
            dsn="https://key@sentry.io/123",
            environment=Environment.STAGING,
            traces_sample_rate=0.1,
        )

        assert config.environment == Environment.STAGING
        assert config.dsn == "https://key@sentry.io/123"
        assert config.traces_sample_rate == 0.1


# ============================================================
# Test Sentry with FastAPI Application
# ============================================================


class TestSentryWithFastAPI:
    """Integration tests for Sentry with FastAPI."""

    def test_middleware_integration_without_errors(self) -> None:
        """Test that middleware can be added to FastAPI app without errors."""
        # Create simple app
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> Dict[str, str]:
            return {"status": "ok"}

        # Add middleware (should not raise)
        app.add_middleware(SentryMiddleware)

        # Verify middleware is added
        assert len(app.user_middleware) > 0

    def test_multiple_middleware_instances(self) -> None:
        """Test that multiple apps can have separate middleware."""
        # Create two apps
        app1 = FastAPI()
        app2 = FastAPI()

        # Add middleware to both
        app1.add_middleware(SentryMiddleware)
        app2.add_middleware(SentryMiddleware)

        # Both should have middleware
        assert len(app1.user_middleware) > 0
        assert len(app2.user_middleware) > 0

    def test_middleware_with_various_endpoints(self) -> None:
        """Test middleware works with different endpoint types."""
        app = FastAPI()

        @app.get("/get-endpoint")
        async def get_endpoint() -> Dict[str, str]:
            return {"method": "GET"}

        @app.post("/post-endpoint")
        async def post_endpoint() -> Dict[str, str]:
            return {"method": "POST"}

        @app.put("/put-endpoint")
        async def put_endpoint() -> Dict[str, str]:
            return {"method": "PUT"}

        # Add middleware (should work with all endpoints)
        app.add_middleware(SentryMiddleware)

        # Verify middleware is added
        assert len(app.user_middleware) > 0


# ============================================================
# Test Sentry Error Grouping Integration
# ============================================================


class TestSentryErrorGrouping:
    """Integration tests for error grouping and fingerprinting."""

    @pytest.fixture
    def sentry_integration(self) -> SentryIntegration:
        """Create Sentry integration instance."""
        config = SentryConfig(
            dsn="https://key@sentry.io/123",
            environment=Environment.DEVELOPMENT,
        )
        return SentryIntegration(config)

    def test_similar_database_errors_grouped_together(
        self,
        sentry_integration: SentryIntegration,
    ) -> None:
        """Similar database errors should be grouped together."""
        # Create mock events for database errors
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

        event3 = {"level": "error", "request": {}}
        hint3 = {
            "exc_info": (
                type("DatabaseError", (), {}),
                Exception("SELECT * FROM users WHERE id = 789"),
                None,
            )
        }

        # Generate fingerprints
        fingerprint1 = sentry_integration._generate_fingerprint(event1, hint1)
        fingerprint2 = sentry_integration._generate_fingerprint(event2, hint2)
        fingerprint3 = sentry_integration._generate_fingerprint(event3, hint3)

        # All should have the same fingerprint (grouped together)
        assert fingerprint1 == fingerprint2 == fingerprint3
        assert "database-error" in fingerprint1

    def test_different_endpoints_separate_groups(
        self,
        sentry_integration: SentryIntegration,
    ) -> None:
        """Errors from different endpoints should be in separate groups."""
        # Create mock events for different endpoints
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
                "url": "http://api.example.com/posts/456",
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

        # Different endpoints should have different fingerprints
        assert fingerprint1 != fingerprint2
        assert "api-error" in fingerprint1
        assert "api-error" in fingerprint2

    def test_validation_field_changes_separate_groups(
        self,
        sentry_integration: SentryIntegration,
    ) -> None:
        """Validation errors with different fields should be separate groups."""
        # Create mock events for validation errors
        event1 = {"level": "error", "request": {}}
        hint1 = {
            "exc_info": (
                type("ValidationError", (), {}),
                Exception("Invalid field: email"),
                None,
            )
        }

        event2 = {"level": "error", "request": {}}
        hint2 = {
            "exc_info": (
                type("ValidationError", (), {}),
                Exception("Invalid field: password"),
                None,
            )
        }

        # Generate fingerprints
        fingerprint1 = sentry_integration._generate_fingerprint(event1, hint1)
        fingerprint2 = sentry_integration._generate_fingerprint(event2, hint2)

        # Different fields should have different fingerprints
        assert fingerprint1 != fingerprint2
        assert "validation-error" in fingerprint1
        assert "validation-error" in fingerprint2


# ============================================================
# Test Sentry Initialization Integration
# ============================================================


class TestSentryInitialization:
    """Integration tests for Sentry initialization."""

    def test_initialization_without_sentry_sdk(self) -> None:
        """Test graceful degradation without Sentry SDK."""
        # Mock HAS_SENTRY to False
        with patch("app.core.sentry.HAS_SENTRY", False):
            config = SentryConfig(
                dsn=None,
                environment=Environment.DEVELOPMENT,
            )
            sentry = SentryIntegration(config)

            # Should not raise even without Sentry SDK
            sentry.initialize()

            # Should not be initialized
            assert not sentry._initialized

    def test_initialization_without_dsn_in_development(self) -> None:
        """Test initialization without DSN in development."""
        config = SentryConfig(
            dsn=None,
            environment=Environment.DEVELOPMENT,
        )
        sentry = SentryIntegration(config)

        # Should not raise
        sentry.initialize()

        # Should not be initialized without DSN
        assert not sentry._initialized

    def test_initialization_with_dsn_requires_sentry_sdk(self) -> None:
        """Test initialization with DSN requires Sentry SDK."""
        config = SentryConfig(
            dsn="https://key@sentry.io/123",
            environment=Environment.DEVELOPMENT,
        )
        sentry = SentryIntegration(config)

        # Mock HAS_SENTRY
        with patch("app.core.sentry.HAS_SENTRY", False):
            # Should log warning but not raise in development
            sentry.initialize()
            assert not sentry._initialized


# ============================================================
# Test Environment Detection
# ============================================================


class TestEnvironmentDetection:
    """Integration tests for environment detection."""

    def test_is_production_with_various_environments(self) -> None:
        """Test is_production with different environment values."""
        from app.core.sentry import is_production

        # Test production
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
            assert is_production() is True

        # Test Production (capitalized)
        with patch.dict("os.environ", {"ENVIRONMENT": "Production"}):
            assert is_production() is True

        # Test PRODUCTION (uppercase)
        with patch.dict("os.environ", {"ENVIRONMENT": "PRODUCTION"}):
            assert is_production() is True

        # Test development
        with patch.dict("os.environ", {"ENVIRONMENT": "development"}):
            assert is_production() is False

        # Test staging
        with patch.dict("os.environ", {"ENVIRONMENT": "staging"}):
            assert is_production() is False


# ============================================================
# Test Sampling Logic Integration
# ============================================================


class TestSamplingIntegration:
    """Integration tests for sampling logic."""

    def test_sampling_with_various_rates(self) -> None:
        """Test sampling with different rates."""
        from app.core.sentry import should_sample_event

        sample_rates = {
            "critical": 1.0,
            "error": 0.5,
            "warning": 0.2,
            "info": 0.1,
        }

        # Critical should always sample
        with patch("random.random", return_value=0.99):
            assert should_sample_event("critical", sample_rates) is True

        # Error at boundary
        with patch("random.random", return_value=0.5):
            assert should_sample_event("error", sample_rates) is True

        # Warning above threshold
        with patch("random.random", return_value=0.25):
            assert should_sample_event("warning", sample_rates) is False

        # Info below threshold
        with patch("random.random", return_value=0.05):
            assert should_sample_event("info", sample_rates) is True


# ============================================================
# Test Complete Integration Flow
# ============================================================


class TestCompleteIntegrationFlow:
    """Integration tests for complete Sentry flow."""

    def test_full_integration_flow_development(self) -> None:
        """Test complete integration flow in development."""
        # 1. Create configuration
        config = SentryConfig(
            dsn=None,
            environment=Environment.DEVELOPMENT,
        )

        # 2. Initialize Sentry
        sentry = SentryIntegration(config)
        sentry.initialize()

        # 3. Create FastAPI app
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> Dict[str, str]:
            return {"status": "ok"}

        # 4. Add middleware
        app.add_middleware(SentryMiddleware)

        # 5. Verify everything is set up
        assert len(app.user_middleware) > 0

    def test_full_integration_flow_with_error_capture(self) -> None:
        """Test complete flow with error capture."""
        # 1. Create configuration
        config = SentryConfig(
            dsn=None,
            environment=Environment.DEVELOPMENT,
        )

        # 2. Initialize Sentry
        sentry = SentryIntegration(config)
        sentry.initialize()

        # 3. Capture exception (should not raise even without DSN)
        try:
            raise ValueError("Test error")
        except Exception as e:
            event_id = sentry.capture_exception(e)
            # Without DSN, returns None
            assert event_id is None

        # 4. Capture message (should not raise)
        event_id = sentry.capture_message("Test message", level="info")
        assert event_id is None
