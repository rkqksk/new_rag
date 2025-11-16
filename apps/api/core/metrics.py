"""Metrics Collection and Management"""

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from apps.api.core.prometheus_metrics import registry


class MetricsCollector:
    """Metrics collector for Prometheus integration.

    This class provides a unified interface for collecting and
    generating metrics in Prometheus exposition format.
    """

    def __init__(self):
        """Initialize metrics collector with the global registry."""
        self.registry = registry

    def generate_metrics(self) -> bytes:
        """Generate metrics in Prometheus exposition format.

        Returns:
            bytes: Metrics data in Prometheus text format
        """
        return generate_latest(self.registry)


# Singleton instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the metrics collector singleton.

    This function can be used as a FastAPI dependency.

    Returns:
        MetricsCollector: The singleton metrics collector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
