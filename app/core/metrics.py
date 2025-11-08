"""Prometheus Metrics"""

from prometheus_client import Counter, Gauge, Histogram

search_requests = Counter("search_requests_total", "Total search requests")
search_duration = Histogram("search_duration_seconds", "Search duration")
personalization_applied = Counter("personalization_applied_total", "Personalizations applied")
compatibility_blocks = Counter("compatibility_filter_blocks_total", "Compatibility filter blocks")
