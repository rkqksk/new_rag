"""
OpenTelemetry + Jaeger Integration (v7.0.0)
============================================

Distributed tracing with OpenTelemetry and Jaeger.

Features:
- Automatic FastAPI instrumentation
- Distributed tracing across services
- Performance monitoring
- Request correlation
- Custom spans and attributes

Version: v7.0.0
"""

import logging
from typing import Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None

logger = logging.getLogger(__name__)


# ============================================================================
# OpenTelemetry Configuration
# ============================================================================


def setup_telemetry(
    service_name: str = "rag-enterprise-api",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
) -> Optional[TracerProvider]:
    """
    Setup OpenTelemetry with Jaeger exporter

    Args:
        service_name: Service name for tracing
        jaeger_host: Jaeger agent host
        jaeger_port: Jaeger agent port

    Returns:
        TracerProvider or None if OpenTelemetry unavailable
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available. Tracing disabled.")
        return None

    try:
        # Create resource with service name
        resource = Resource.create({SERVICE_NAME: service_name})

        # Setup tracer provider
        provider = TracerProvider(resource=resource)

        # Setup Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )

        # Add batch span processor
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        logger.info(f"✅ OpenTelemetry configured with Jaeger ({jaeger_host}:{jaeger_port})")
        return provider

    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}")
        return None


def instrument_app(app):
    """
    Instrument FastAPI app with OpenTelemetry

    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available. Skipping instrumentation.")
        return

    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ FastAPI instrumented with OpenTelemetry")

        # Instrument HTTP requests
        RequestsInstrumentor().instrument()
        logger.info("✅ Requests instrumented with OpenTelemetry")

        # Instrument Redis
        try:
            RedisInstrumentor().instrument()
            logger.info("✅ Redis instrumented with OpenTelemetry")
        except Exception as e:
            logger.warning(f"Redis instrumentation failed: {e}")

        # Instrument PostgreSQL
        try:
            Psycopg2Instrumentor().instrument()
            logger.info("✅ PostgreSQL instrumented with OpenTelemetry")
        except Exception as e:
            logger.warning(f"PostgreSQL instrumentation failed: {e}")

    except Exception as e:
        logger.error(f"Failed to instrument app: {e}")


def get_tracer(name: str = __name__):
    """
    Get tracer instance

    Args:
        name: Tracer name

    Returns:
        Tracer instance or None
    """
    if not OTEL_AVAILABLE or not trace:
        return None

    return trace.get_tracer(name)


# ============================================================================
# Custom Tracing Utilities
# ============================================================================


class TracingContext:
    """Context manager for custom spans"""

    def __init__(self, span_name: str, attributes: dict = None):
        self.span_name = span_name
        self.attributes = attributes or {}
        self.span = None
        self.tracer = get_tracer()

    def __enter__(self):
        if self.tracer:
            self.span = self.tracer.start_span(self.span_name)
            for key, value in self.attributes.items():
                self.span.set_attribute(key, value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_val:
                self.span.set_attribute("error", True)
                self.span.set_attribute("error.type", exc_type.__name__)
                self.span.set_attribute("error.message", str(exc_val))
            self.span.end()

    def add_event(self, name: str, attributes: dict = None):
        """Add event to current span"""
        if self.span:
            self.span.add_event(name, attributes or {})

    def set_attribute(self, key: str, value):
        """Set attribute on current span"""
        if self.span:
            self.span.set_attribute(key, value)


def trace_function(span_name: str = None):
    """
    Decorator for tracing functions

    Usage:
        @trace_function("my_function")
        def my_function():
            pass
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            name = span_name or f"{func.__module__}.{func.__name__}"
            with TracingContext(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Setup telemetry
    provider = setup_telemetry()

    # Use custom span
    with TracingContext("example_operation", {"user_id": "123"}) as ctx:
        # Do some work
        ctx.add_event("processing_started")
        # ... work ...
        ctx.add_event("processing_completed")

    # Use decorator
    @trace_function("my_custom_function")
    def my_function(x, y):
        return x + y

    result = my_function(1, 2)
    print(f"Result: {result}")
