"""
Real-Time Analytics Dashboard for Phase 8.2
Live metrics collection and streaming
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Single metric value"""

    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series of metrics"""

    name: str
    values: deque  # Recent values
    max_size: int = 100

    def add(self, value: float, timestamp: Optional[datetime] = None):
        """Add value to series"""
        if timestamp is None:
            timestamp = datetime.now()

        self.values.append((timestamp, value))

        # Trim to max size
        while len(self.values) > self.max_size:
            self.values.popleft()

    def get_recent(self, seconds: int = 60) -> List[tuple]:
        """Get recent values within time window"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        return [(ts, val) for ts, val in self.values if ts >= cutoff]

    def get_stats(self) -> Dict[str, float]:
        """Calculate statistics"""
        if not self.values:
            return {"count": 0, "sum": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}

        values = [v for _, v in self.values]
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }


class RealTimeAnalytics:
    """
    Real-Time Analytics Dashboard

    Features:
    - Live metrics collection
    - Time series data
    - Aggregation and statistics
    - Automatic streaming via SSE
    - Configurable retention

    Metrics:
    - search_latency: Search request latency (ms)
    - search_qps: Queries per second
    - pipeline_progress: Pipeline execution progress
    - vector_store_ops: Vector store operations
    - cache_hit_rate: Cache hit rate
    - error_rate: Error rate

    Example:
        >>> analytics = RealTimeAnalytics(sse_manager=sse_manager)
        >>>
        >>> # Record metric
        >>> await analytics.record('search_latency', 45.2)
        >>>
        >>> # Get dashboard data
        >>> dashboard = await analytics.get_dashboard()
        >>> print(dashboard['search_qps'])
        >>>
        >>> # Start auto-streaming
        >>> await analytics.start_streaming(interval=5)
    """

    def __init__(
        self, sse_manager=None, retention_seconds: int = 3600, max_series_size: int = 1000  # 1 hour
    ):
        """
        Initialize Real-Time Analytics

        Args:
            sse_manager: SSEManager for streaming updates
            retention_seconds: How long to retain metrics
            max_series_size: Maximum points per series
        """
        self.sse_manager = sse_manager
        self.retention_seconds = retention_seconds
        self.max_series_size = max_series_size

        # Metric series
        self.series: Dict[str, MetricSeries] = {}

        # Counters
        self.counters: Dict[str, int] = defaultdict(int)

        # Timers
        self.timers: Dict[str, List[float]] = defaultdict(list)

        # Streaming task
        self.streaming_task = None
        self.streaming_interval = 5  # seconds

        logger.info("✅ RealTimeAnalytics initialized")

    async def record(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record metric value

        Args:
            metric_name: Metric name
            value: Metric value
            tags: Optional tags

        Example:
            >>> await analytics.record('search_latency', 45.2, tags={'query_type': 'semantic'})
        """
        # Get or create series
        if metric_name not in self.series:
            self.series[metric_name] = MetricSeries(
                name=metric_name,
                values=deque(maxlen=self.max_series_size),
                max_size=self.max_series_size,
            )

        # Add to series
        self.series[metric_name].add(value)

        logger.debug(f"Recorded metric: {metric_name} = {value}")

    async def increment(self, counter_name: str, delta: int = 1):
        """
        Increment counter

        Args:
            counter_name: Counter name
            delta: Increment amount

        Example:
            >>> await analytics.increment('search_count')
        """
        self.counters[counter_name] += delta

        # Also record as metric
        await self.record(counter_name, self.counters[counter_name])

    async def time(self, timer_name: str, duration_ms: float):
        """
        Record timing

        Args:
            timer_name: Timer name
            duration_ms: Duration in milliseconds

        Example:
            >>> await analytics.time('search_duration', 45.2)
        """
        self.timers[timer_name].append(duration_ms)

        # Trim old timings
        if len(self.timers[timer_name]) > 1000:
            self.timers[timer_name] = self.timers[timer_name][-1000:]

        # Record as metric
        await self.record(timer_name, duration_ms)

    async def get_dashboard(self) -> Dict[str, Any]:
        """
        Get dashboard data

        Returns:
            Dashboard metrics

        Example:
            >>> dashboard = await analytics.get_dashboard()
            >>> print(dashboard)
        """
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "counters": dict(self.counters),
            "timers": {},
        }

        # Metrics with stats
        for name, series in self.series.items():
            stats = series.get_stats()
            recent = series.get_recent(seconds=60)

            dashboard["metrics"][name] = {
                "current": recent[-1][1] if recent else 0.0,
                "stats": stats,
                "recent_count": len(recent),
            }

        # Timer stats
        for name, durations in self.timers.items():
            if durations:
                dashboard["timers"][name] = {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "p50": self._percentile(durations, 50),
                    "p95": self._percentile(durations, 95),
                    "p99": self._percentile(durations, 99),
                }

        return dashboard

    async def get_metric_series(self, metric_name: str, seconds: int = 300) -> List[Dict[str, Any]]:
        """
        Get time series for metric

        Args:
            metric_name: Metric name
            seconds: Time window in seconds

        Returns:
            Time series data

        Example:
            >>> series = await analytics.get_metric_series('search_latency', seconds=300)
        """
        if metric_name not in self.series:
            return []

        series = self.series[metric_name]
        recent = series.get_recent(seconds=seconds)

        return [{"timestamp": ts.isoformat(), "value": val} for ts, val in recent]

    async def start_streaming(self, interval: int = 5):
        """
        Start automatic dashboard streaming via SSE

        Args:
            interval: Update interval in seconds

        Example:
            >>> await analytics.start_streaming(interval=5)
        """
        if not self.sse_manager:
            logger.warning("SSEManager not configured, streaming disabled")
            return

        self.streaming_interval = interval

        if self.streaming_task and not self.streaming_task.done():
            logger.warning("Streaming already active")
            return

        self.streaming_task = asyncio.create_task(self._streaming_loop())
        logger.info(f"✅ Analytics streaming started (interval: {interval}s)")

    async def stop_streaming(self):
        """Stop analytics streaming"""
        if self.streaming_task:
            self.streaming_task.cancel()
            logger.info("Analytics streaming stopped")

    async def _streaming_loop(self):
        """Streaming loop"""
        while True:
            try:
                await asyncio.sleep(self.streaming_interval)

                # Get dashboard data
                dashboard = await self.get_dashboard()

                # Emit via SSE
                if self.sse_manager:
                    await self.sse_manager.emit(
                        channel="analytics", event="analytics_update", data=dashboard
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Streaming loop error: {e}")

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_stats(self) -> Dict[str, Any]:
        """Get analytics statistics"""
        return {
            "metrics_count": len(self.series),
            "counters_count": len(self.counters),
            "timers_count": len(self.timers),
            "streaming_active": self.streaming_task is not None and not self.streaming_task.done(),
        }

    def __repr__(self):
        return (
            f"RealTimeAnalytics("
            f"metrics={len(self.series)}, "
            f"counters={len(self.counters)}, "
            f"streaming={'active' if self.streaming_task else 'inactive'})"
        )


# Context manager for timing
class Timer:
    """
    Context manager for timing operations

    Example:
        >>> async with Timer(analytics, 'search_duration'):
        ...     results = await search(query)
    """

    def __init__(self, analytics: RealTimeAnalytics, timer_name: str):
        self.analytics = analytics
        self.timer_name = timer_name
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        await self.analytics.time(self.timer_name, duration_ms)
