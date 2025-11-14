"""
Middleware compatibility layer for backward compatibility with tests.

This module re-exports middleware components from their actual locations
to maintain backward compatibility with existing tests.
"""

# Placeholder MetricsMiddleware for backward compatibility
class MetricsMiddleware:
    """Metrics middleware placeholder.

    Actual metrics collection is handled by app.middleware.performance_timing
    and app.core.prometheus_metrics.

    This class exists for backward compatibility with tests that
    import from app.core.middleware.
    """

    def __init__(self, app=None):
        """Initialize middleware placeholder."""
        self.app = app

    async def __call__(self, request, call_next):
        """Process request (placeholder)."""
        return await call_next(request)
