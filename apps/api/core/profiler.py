"""Performance Profiler with Bottleneck Detection"""

import time
from collections import defaultdict
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from apps.api.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProfileResult:
    """Single profiling result"""

    name: str
    duration_ms: float
    start_time: float
    end_time: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProfileSummary:
    """Profiling summary with bottleneck analysis"""

    total_duration_ms: float
    checkpoints: List[ProfileResult]
    bottlenecks: List[Dict]
    recommendations: List[str]


# Context variable for profiler
_profiler_ctx: ContextVar[Optional["RequestProfiler"]] = ContextVar("profiler", default=None)

# Global statistics
_global_stats: Dict[str, List[float]] = defaultdict(list)
MAX_STATS_PER_CHECKPOINT = 1000


class RequestProfiler:
    """
    Context manager for profiling request performance.

    Usage:
        with RequestProfiler("search_request") as profiler:
            profiler.checkpoint("embedding")
            # ... do embedding work ...
            profiler.checkpoint("vector_search")
            # ... do vector search ...

        summary = profiler.get_summary()
    """

    def __init__(self, request_name: str):
        self.request_name = request_name
        self.start_time = None
        self.checkpoints: List[ProfileResult] = []
        self.prev_checkpoint_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.prev_checkpoint_time = self.start_time
        _profiler_ctx.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.checkpoints:
            total_duration = (time.time() - self.start_time) * 1000
            logger.info(
                f"Profile: {self.request_name}",
                extra={
                    "total_ms": round(total_duration, 2),
                    "checkpoints": [
                        {"name": cp.name, "duration_ms": round(cp.duration_ms, 2)}
                        for cp in self.checkpoints
                    ],
                },
            )

        _profiler_ctx.set(None)
        return False

    def checkpoint(self, name: str, metadata: Optional[Dict] = None):
        """Record a checkpoint"""
        current_time = time.time()
        duration_ms = (current_time - self.prev_checkpoint_time) * 1000

        result = ProfileResult(
            name=name,
            duration_ms=duration_ms,
            start_time=self.prev_checkpoint_time,
            end_time=current_time,
            metadata=metadata or {},
        )

        self.checkpoints.append(result)
        self.prev_checkpoint_time = current_time

        # Add to global stats
        _global_stats[name].append(duration_ms)
        if len(_global_stats[name]) > MAX_STATS_PER_CHECKPOINT:
            _global_stats[name].pop(0)

        # Log slow checkpoints
        avg_duration = sum(_global_stats[name]) / len(_global_stats[name])
        if duration_ms > avg_duration * 2:  # More than 2x average
            logger.warning(
                f"⚠️ SLOW CHECKPOINT: {name}",
                extra={
                    "duration_ms": round(duration_ms, 2),
                    "avg_ms": round(avg_duration, 2),
                    "threshold_multiplier": 2.0,
                },
            )

    def get_summary(self) -> ProfileSummary:
        """Get profiling summary with bottleneck analysis"""
        total_duration = (time.time() - self.start_time) * 1000

        # Identify bottlenecks (>20% of total time)
        bottlenecks = []
        for cp in self.checkpoints:
            percent = (cp.duration_ms / total_duration) * 100
            if percent > 20:
                bottlenecks.append(
                    {
                        "name": cp.name,
                        "duration_ms": round(cp.duration_ms, 2),
                        "percent_of_total": round(percent, 1),
                    }
                )

        # Sort bottlenecks by duration
        bottlenecks.sort(key=lambda x: x["duration_ms"], reverse=True)

        # Generate recommendations
        recommendations = []
        for bottleneck in bottlenecks:
            if bottleneck["name"] == "embedding":
                recommendations.append(f"Consider caching embeddings for common queries")
            elif bottleneck["name"] == "reranking":
                recommendations.append(
                    f"Re-ranking is taking {bottleneck['percent_of_total']:.1f}% - consider reducing candidates"
                )
            elif bottleneck["name"] == "vector_search":
                recommendations.append(f"Vector search is slow - check index health")
            elif bottleneck["name"] == "database_query":
                recommendations.append(f"Database query is slow - check query optimization")

        return ProfileSummary(
            total_duration_ms=round(total_duration, 2),
            checkpoints=self.checkpoints,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
        )


def get_current_profiler() -> Optional[RequestProfiler]:
    """Get current request profiler from context"""
    return _profiler_ctx.get()


def profile_checkpoint(name: str, metadata: Optional[Dict] = None):
    """Record a checkpoint in the current profiler (if active)"""
    profiler = get_current_profiler()
    if profiler:
        profiler.checkpoint(name, metadata)


def get_global_stats() -> Dict[str, Dict]:
    """Get global performance statistics"""
    stats = {}

    for name, durations in _global_stats.items():
        if durations:
            stats[name] = {
                "count": len(durations),
                "avg_ms": round(sum(durations) / len(durations), 2),
                "min_ms": round(min(durations), 2),
                "max_ms": round(max(durations), 2),
                "p50_ms": round(sorted(durations)[len(durations) // 2], 2),
                "p95_ms": (
                    round(sorted(durations)[int(len(durations) * 0.95)], 2)
                    if len(durations) > 20
                    else None
                ),
            }

    return stats


def clear_global_stats():
    """Clear global statistics (useful for testing)"""
    global _global_stats
    _global_stats = defaultdict(list)
