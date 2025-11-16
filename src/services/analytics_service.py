"""
Analytics Service
Real-time metrics collection and monitoring with Prometheus
Version: v8.5.0
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from prometheus_client import Counter, Histogram, Gauge, Summary, Info
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Real-time analytics and metrics service"""

    def __init__(self, redis_url: str = None):
        """
        Initialize analytics service

        Args:
            redis_url: Redis connection URL
        """
        if redis_url is None:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = os.getenv("REDIS_PORT", "6379")
            redis_url = f"redis://{redis_host}:{redis_port}/0"
        self.redis_url = redis_url
        self.redis_client = None

        # Prometheus Metrics
        self.request_count = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status']
        )

        self.request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint']
        )

        self.search_queries = Counter(
            'search_queries_total',
            'Total search queries',
            ['query_type', 'status']
        )

        self.search_latency = Histogram(
            'search_latency_seconds',
            'Search query latency',
            ['query_type']
        )

        self.active_users = Gauge(
            'active_users',
            'Currently active users'
        )

        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type']
        )

        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type']
        )

        self.error_count = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'severity']
        )

        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['query_type']
        )

        self.embeddings_generated = Counter(
            'embeddings_generated_total',
            'Total embeddings generated',
            ['model']
        )

        self.vector_search_results = Summary(
            'vector_search_results_count',
            'Number of vector search results',
            ['similarity_threshold']
        )

        # In-memory metrics (for detailed analytics)
        self.metrics_buffer = defaultdict(list)
        self.max_buffer_size = 1000

    async def connect_redis(self):
        """Connect to Redis"""
        if self.redis_client is None:
            try:
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Connected to Redis for analytics")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")

    async def track_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        user_id: Optional[str] = None
    ):
        """
        Track API request

        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: Response status code
            duration: Request duration in seconds
            user_id: Optional user ID
        """
        # Prometheus metrics
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()

        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        # Store in Redis for detailed analytics
        await self.connect_redis()
        if self.redis_client:
            try:
                request_data = {
                    'method': method,
                    'endpoint': endpoint,
                    'status': status_code,
                    'duration': duration,
                    'user_id': user_id or 'anonymous',
                    'timestamp': datetime.now().isoformat()
                }

                # Store with 7-day expiry
                key = f"request:{datetime.now().strftime('%Y%m%d%H%M%S')}"
                await self.redis_client.setex(
                    key,
                    7 * 24 * 60 * 60,  # 7 days
                    str(request_data)
                )
            except Exception as e:
                logger.error(f"Failed to store request in Redis: {e}")

    async def track_search(
        self,
        query: str,
        query_type: str,
        results_count: int,
        latency: float,
        similarity_scores: Optional[List[float]] = None,
        user_id: Optional[str] = None
    ):
        """
        Track search query

        Args:
            query: Search query text
            query_type: Type of search (hybrid, vector, text)
            results_count: Number of results returned
            latency: Search latency in seconds
            similarity_scores: List of similarity scores
            user_id: Optional user ID
        """
        # Prometheus metrics
        self.search_queries.labels(
            query_type=query_type,
            status='success' if results_count > 0 else 'no_results'
        ).inc()

        self.search_latency.labels(query_type=query_type).observe(latency)

        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            self.vector_search_results.observe(results_count)

        # Store in buffer
        search_data = {
            'query': query,
            'type': query_type,
            'results': results_count,
            'latency': latency,
            'avg_similarity': avg_similarity if similarity_scores else None,
            'user_id': user_id or 'anonymous',
            'timestamp': datetime.now().isoformat()
        }

        self.metrics_buffer['searches'].append(search_data)
        await self._flush_buffer_if_needed('searches')

    async def track_cache(self, cache_type: str, hit: bool):
        """
        Track cache hit/miss

        Args:
            cache_type: Type of cache (redis, memory, disk)
            hit: True if cache hit, False if miss
        """
        if hit:
            self.cache_hits.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type).inc()

    async def track_error(
        self,
        error_type: str,
        severity: str,
        message: str,
        stacktrace: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Track error occurrence

        Args:
            error_type: Type of error
            severity: Error severity (low, medium, high, critical)
            message: Error message
            stacktrace: Optional stack trace
            user_id: Optional user ID
        """
        self.error_count.labels(
            error_type=error_type,
            severity=severity
        ).inc()

        # Store detailed error in Redis
        await self.connect_redis()
        if self.redis_client:
            try:
                error_data = {
                    'type': error_type,
                    'severity': severity,
                    'message': message,
                    'stacktrace': stacktrace,
                    'user_id': user_id or 'anonymous',
                    'timestamp': datetime.now().isoformat()
                }

                key = f"error:{datetime.now().strftime('%Y%m%d%H%M%S')}"
                await self.redis_client.setex(
                    key,
                    30 * 24 * 60 * 60,  # 30 days
                    str(error_data)
                )
            except Exception as e:
                logger.error(f"Failed to store error in Redis: {e}")

    async def track_active_user(self, user_id: str, action: str = 'active'):
        """
        Track active user

        Args:
            user_id: User ID
            action: 'active' or 'inactive'
        """
        await self.connect_redis()
        if self.redis_client:
            try:
                key = f"active_user:{user_id}"

                if action == 'active':
                    # Set with 5-minute expiry
                    await self.redis_client.setex(key, 5 * 60, '1')
                else:
                    await self.redis_client.delete(key)

                # Update gauge
                active_count = await self.get_active_users_count()
                self.active_users.set(active_count)
            except Exception as e:
                logger.error(f"Failed to track active user: {e}")

    async def get_active_users_count(self) -> int:
        """Get count of active users"""
        await self.connect_redis()
        if self.redis_client:
            try:
                keys = await self.redis_client.keys("active_user:*")
                return len(keys)
            except Exception as e:
                logger.error(f"Failed to get active users: {e}")
                return 0
        return 0

    async def track_db_query(self, query_type: str, duration: float):
        """
        Track database query

        Args:
            query_type: Type of query (select, insert, update, delete)
            duration: Query duration in seconds
        """
        self.db_query_duration.labels(query_type=query_type).observe(duration)

    async def track_embedding(self, model: str, count: int = 1):
        """
        Track embedding generation

        Args:
            model: Model name
            count: Number of embeddings generated
        """
        self.embeddings_generated.labels(model=model).inc(count)

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get real-time dashboard metrics

        Returns:
            Dashboard metrics dictionary
        """
        await self.connect_redis()

        metrics = {
            'timestamp': datetime.now().isoformat(),
            'active_users': await self.get_active_users_count(),
            'recent_searches': len(self.metrics_buffer.get('searches', [])),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
        }

        # Get recent errors from Redis
        if self.redis_client:
            try:
                error_keys = await self.redis_client.keys("error:*")
                metrics['recent_errors'] = len(error_keys)
            except Exception as e:
                logger.error(f"Failed to get error count: {e}")
                metrics['recent_errors'] = 0

        return metrics

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        try:
            # Access internal Prometheus metrics
            hits = sum(
                sample.value
                for sample in self.cache_hits.collect()[0].samples
            )
            misses = sum(
                sample.value
                for sample in self.cache_misses.collect()[0].samples
            )

            total = hits + misses
            if total == 0:
                return 0.0

            return (hits / total) * 100
        except Exception:
            return 0.0

    async def _flush_buffer_if_needed(self, buffer_name: str):
        """Flush metrics buffer to Redis if needed"""
        if len(self.metrics_buffer[buffer_name]) >= self.max_buffer_size:
            await self._flush_buffer(buffer_name)

    async def _flush_buffer(self, buffer_name: str):
        """Flush specific buffer to Redis"""
        await self.connect_redis()
        if self.redis_client and self.metrics_buffer[buffer_name]:
            try:
                # Store aggregated metrics
                key = f"metrics:{buffer_name}:{datetime.now().strftime('%Y%m%d%H')}"
                await self.redis_client.setex(
                    key,
                    7 * 24 * 60 * 60,  # 7 days
                    str(self.metrics_buffer[buffer_name])
                )

                # Clear buffer
                self.metrics_buffer[buffer_name] = []
                logger.info(f"Flushed {buffer_name} buffer to Redis")
            except Exception as e:
                logger.error(f"Failed to flush buffer: {e}")

    async def get_search_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get search analytics

        Args:
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            Search analytics dictionary
        """
        searches = self.metrics_buffer.get('searches', [])

        if start_date or end_date:
            searches = [
                s for s in searches
                if (not start_date or datetime.fromisoformat(s['timestamp']) >= start_date)
                and (not end_date or datetime.fromisoformat(s['timestamp']) <= end_date)
            ]

        if not searches:
            return {
                'total_searches': 0,
                'avg_latency': 0,
                'avg_results': 0,
                'top_queries': []
            }

        total = len(searches)
        avg_latency = sum(s['latency'] for s in searches) / total
        avg_results = sum(s['results'] for s in searches) / total

        # Top queries
        query_counts = defaultdict(int)
        for s in searches:
            query_counts[s['query']] += 1

        top_queries = sorted(
            query_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            'total_searches': total,
            'avg_latency': round(avg_latency, 3),
            'avg_results': round(avg_results, 1),
            'top_queries': [{'query': q, 'count': c} for q, c in top_queries]
        }


# Singleton instance
_analytics_service = None


def get_analytics_service(redis_url: str = None) -> AnalyticsService:
    """Get analytics service singleton"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(redis_url)
    return _analytics_service
