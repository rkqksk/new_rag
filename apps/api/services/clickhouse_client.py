"""
ClickHouse Client for Real-time Analytics (v6.0.0)
==================================================

OLAP database client for high-performance analytics queries.

Features:
- Columnar storage for fast aggregations
- Real-time data ingestion
- Time-series analysis
- User behavior tracking
- Search quality metrics

Tables:
- search_logs: All search queries with performance metrics
- user_events: User interactions (clicks, sessions, conversions)
- search_quality: Search quality metrics (CTR, MRR, NDCG)
- performance_metrics: API performance over time

Version: v6.0.0
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    from clickhouse_driver import Client

    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    Client = None

logger = logging.getLogger(__name__)


# ============================================================================
# ClickHouse Client
# ============================================================================


class ClickHouseClient:
    """
    ClickHouse client for analytics queries

    Features:
    - Connection pooling
    - Automatic table creation
    - Batch inserts
    - Time-series queries
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        database: str = "analytics",
        user: str = "default",
        password: str = "",
    ):
        """
        Initialize ClickHouse client

        Args:
            host: ClickHouse server host
            port: ClickHouse native protocol port (9000)
            database: Database name
            user: Username
            password: Password
        """
        if not CLICKHOUSE_AVAILABLE:
            logger.warning("clickhouse-driver not installed. Analytics features disabled.")
            self.client = None
            return

        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

        # Initialize client
        try:
            self.client = Client(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                settings={"use_numpy": True},
            )
            logger.info(f"✅ ClickHouse connected: {host}:{port}/{database}")

            # Create tables
            self._create_tables()
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            self.client = None

    def _create_tables(self):
        """Create analytics tables if they don't exist"""
        if not self.client:
            return

        # Search logs table
        self.client.execute(
            """
            CREATE TABLE IF NOT EXISTS search_logs (
                timestamp DateTime,
                session_id String,
                user_id String,
                query String,
                results_count UInt32,
                response_time_ms Float32,
                search_strategy String,
                filters String,
                top_k UInt32,
                cache_hit UInt8,
                date Date DEFAULT toDate(timestamp)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (date, timestamp)
            TTL date + INTERVAL 90 DAY
        """
        )

        # User events table
        self.client.execute(
            """
            CREATE TABLE IF NOT EXISTS user_events (
                timestamp DateTime,
                session_id String,
                user_id String,
                event_type String,
                event_data String,
                product_id String,
                query String,
                date Date DEFAULT toDate(timestamp)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (date, timestamp)
            TTL date + INTERVAL 90 DAY
        """
        )

        # Search quality metrics table
        self.client.execute(
            """
            CREATE TABLE IF NOT EXISTS search_quality (
                timestamp DateTime,
                query String,
                click_position UInt32,
                clicks UInt32,
                impressions UInt32,
                ctr Float32,
                mrr Float32,
                avg_similarity Float32,
                date Date DEFAULT toDate(timestamp)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (date, timestamp)
            TTL date + INTERVAL 90 DAY
        """
        )

        # Performance metrics table
        self.client.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                timestamp DateTime,
                endpoint String,
                method String,
                status_code UInt16,
                response_time_ms Float32,
                cpu_percent Float32,
                memory_mb Float32,
                date Date DEFAULT toDate(timestamp)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (date, timestamp)
            TTL date + INTERVAL 30 DAY
        """
        )

        logger.info("✅ ClickHouse tables created")

    # ========================================================================
    # Insert Methods
    # ========================================================================

    def insert_search_log(
        self,
        session_id: str,
        user_id: str,
        query: str,
        results_count: int,
        response_time_ms: float,
        search_strategy: str = "dense",
        filters: str = "",
        top_k: int = 10,
        cache_hit: bool = False,
    ):
        """Insert search log entry"""
        if not self.client:
            return

        try:
            self.client.execute(
                """
                INSERT INTO search_logs
                (timestamp, session_id, user_id, query, results_count,
                 response_time_ms, search_strategy, filters, top_k, cache_hit)
                VALUES
                """,
                [
                    {
                        "timestamp": datetime.now(),
                        "session_id": session_id,
                        "user_id": user_id,
                        "query": query,
                        "results_count": results_count,
                        "response_time_ms": response_time_ms,
                        "search_strategy": search_strategy,
                        "filters": filters,
                        "top_k": top_k,
                        "cache_hit": 1 if cache_hit else 0,
                    }
                ],
            )
        except Exception as e:
            logger.error(f"Failed to insert search log: {e}")

    def insert_user_event(
        self,
        session_id: str,
        user_id: str,
        event_type: str,
        event_data: str = "",
        product_id: str = "",
        query: str = "",
    ):
        """Insert user event"""
        if not self.client:
            return

        try:
            self.client.execute(
                """
                INSERT INTO user_events
                (timestamp, session_id, user_id, event_type, event_data, product_id, query)
                VALUES
                """,
                [
                    {
                        "timestamp": datetime.now(),
                        "session_id": session_id,
                        "user_id": user_id,
                        "event_type": event_type,
                        "event_data": event_data,
                        "product_id": product_id,
                        "query": query,
                    }
                ],
            )
        except Exception as e:
            logger.error(f"Failed to insert user event: {e}")

    def insert_search_quality(
        self,
        query: str,
        click_position: int,
        clicks: int,
        impressions: int,
        ctr: float,
        mrr: float,
        avg_similarity: float,
    ):
        """Insert search quality metrics"""
        if not self.client:
            return

        try:
            self.client.execute(
                """
                INSERT INTO search_quality
                (timestamp, query, click_position, clicks, impressions, ctr, mrr, avg_similarity)
                VALUES
                """,
                [
                    {
                        "timestamp": datetime.now(),
                        "query": query,
                        "click_position": click_position,
                        "clicks": clicks,
                        "impressions": impressions,
                        "ctr": ctr,
                        "mrr": mrr,
                        "avg_similarity": avg_similarity,
                    }
                ],
            )
        except Exception as e:
            logger.error(f"Failed to insert search quality: {e}")

    def insert_performance_metric(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        cpu_percent: float = 0.0,
        memory_mb: float = 0.0,
    ):
        """Insert performance metric"""
        if not self.client:
            return

        try:
            self.client.execute(
                """
                INSERT INTO performance_metrics
                (timestamp, endpoint, method, status_code, response_time_ms, cpu_percent, memory_mb)
                VALUES
                """,
                [
                    {
                        "timestamp": datetime.now(),
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": status_code,
                        "response_time_ms": response_time_ms,
                        "cpu_percent": cpu_percent,
                        "memory_mb": memory_mb,
                    }
                ],
            )
        except Exception as e:
            logger.error(f"Failed to insert performance metric: {e}")

    # ========================================================================
    # Query Methods
    # ========================================================================

    def get_search_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get search statistics for last N hours

        Returns:
            Dict with total_searches, avg_response_time, cache_hit_rate, etc.
        """
        if not self.client:
            return self._mock_search_stats()

        try:
            result = self.client.execute(
                """
                SELECT
                    count() as total_searches,
                    avg(response_time_ms) as avg_response_time,
                    sum(cache_hit) / count() as cache_hit_rate,
                    avg(results_count) as avg_results_count,
                    uniq(session_id) as unique_sessions,
                    uniq(query) as unique_queries
                FROM search_logs
                WHERE timestamp >= now() - INTERVAL ? HOUR
                """,
                [hours],
            )

            if result:
                row = result[0]
                return {
                    "total_searches": row[0],
                    "avg_response_time": round(row[1], 2),
                    "cache_hit_rate": round(row[2], 2),
                    "avg_results_count": round(row[3], 1),
                    "unique_sessions": row[4],
                    "unique_queries": row[5],
                }
        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")

        return self._mock_search_stats()

    def get_top_queries(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular queries"""
        if not self.client:
            return self._mock_top_queries()

        try:
            result = self.client.execute(
                """
                SELECT
                    query,
                    count() as search_count,
                    avg(response_time_ms) as avg_response_time,
                    avg(results_count) as avg_results
                FROM search_logs
                WHERE timestamp >= now() - INTERVAL ? HOUR
                GROUP BY query
                ORDER BY search_count DESC
                LIMIT ?
                """,
                [hours, limit],
            )

            return [
                {
                    "query": row[0],
                    "search_count": row[1],
                    "avg_response_time": round(row[2], 2),
                    "avg_results": round(row[3], 1),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to get top queries: {e}")

        return self._mock_top_queries()

    def get_hourly_search_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly search volume trend"""
        if not self.client:
            return self._mock_hourly_trend()

        try:
            result = self.client.execute(
                """
                SELECT
                    toStartOfHour(timestamp) as hour,
                    count() as searches,
                    avg(response_time_ms) as avg_response_time
                FROM search_logs
                WHERE timestamp >= now() - INTERVAL ? HOUR
                GROUP BY hour
                ORDER BY hour
                """,
                [hours],
            )

            return [
                {
                    "hour": row[0].strftime("%Y-%m-%d %H:00"),
                    "searches": row[1],
                    "avg_response_time": round(row[2], 2),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to get hourly trend: {e}")

        return self._mock_hourly_trend()

    def get_performance_by_strategy(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance metrics by search strategy"""
        if not self.client:
            return self._mock_performance_by_strategy()

        try:
            result = self.client.execute(
                """
                SELECT
                    search_strategy,
                    count() as count,
                    avg(response_time_ms) as avg_response_time,
                    quantile(0.95)(response_time_ms) as p95_response_time
                FROM search_logs
                WHERE timestamp >= now() - INTERVAL ? HOUR
                GROUP BY search_strategy
                ORDER BY count DESC
                """,
                [hours],
            )

            return [
                {
                    "strategy": row[0],
                    "count": row[1],
                    "avg_response_time": round(row[2], 2),
                    "p95_response_time": round(row[3], 2),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to get performance by strategy: {e}")

        return self._mock_performance_by_strategy()

    # ========================================================================
    # Mock Data (for when ClickHouse is unavailable)
    # ========================================================================

    def _mock_search_stats(self) -> Dict[str, Any]:
        """Mock search statistics"""
        return {
            "total_searches": 1247,
            "avg_response_time": 342.5,
            "cache_hit_rate": 0.68,
            "avg_results_count": 87.3,
            "unique_sessions": 456,
            "unique_queries": 312,
        }

    def _mock_top_queries(self) -> List[Dict[str, Any]]:
        """Mock top queries"""
        return [
            {
                "query": "50ml PET 용기",
                "search_count": 45,
                "avg_response_time": 320.5,
                "avg_results": 92.0,
            },
            {
                "query": "100ml PP 용기",
                "search_count": 38,
                "avg_response_time": 295.3,
                "avg_results": 78.0,
            },
            {
                "query": "화장품 용기",
                "search_count": 32,
                "avg_response_time": 410.2,
                "avg_results": 156.0,
            },
        ]

    def _mock_hourly_trend(self) -> List[Dict[str, Any]]:
        """Mock hourly trend"""
        now = datetime.now()
        return [
            {
                "hour": (now - timedelta(hours=i)).strftime("%Y-%m-%d %H:00"),
                "searches": 45 + (i * 3),
                "avg_response_time": 320.0 + (i * 10),
            }
            for i in range(24, 0, -1)
        ]

    def _mock_performance_by_strategy(self) -> List[Dict[str, Any]]:
        """Mock performance by strategy"""
        return [
            {
                "strategy": "dense",
                "count": 856,
                "avg_response_time": 298.5,
                "p95_response_time": 450.2,
            },
            {
                "strategy": "hybrid",
                "count": 312,
                "avg_response_time": 425.3,
                "p95_response_time": 680.1,
            },
            {
                "strategy": "hybrid+rerank",
                "count": 79,
                "avg_response_time": 1250.7,
                "p95_response_time": 1850.3,
            },
        ]


# ============================================================================
# Singleton Instance
# ============================================================================

_clickhouse_client: Optional[ClickHouseClient] = None


def get_clickhouse_client() -> ClickHouseClient:
    """Get or create ClickHouse client singleton"""
    global _clickhouse_client

    if _clickhouse_client is None:
        host = os.getenv("CLICKHOUSE_HOST", "localhost")
        port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
        database = os.getenv("CLICKHOUSE_DB", "analytics")
        user = os.getenv("CLICKHOUSE_USER", "default")
        password = os.getenv("CLICKHOUSE_PASSWORD", "")

        _clickhouse_client = ClickHouseClient(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )

    return _clickhouse_client


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Create client
    client = get_clickhouse_client()

    # Insert search log
    client.insert_search_log(
        session_id="session-123",
        user_id="user-456",
        query="50ml PET 용기",
        results_count=95,
        response_time_ms=342.5,
        search_strategy="hybrid",
        top_k=10,
        cache_hit=False,
    )

    # Query stats
    stats = client.get_search_stats(hours=24)
    print(f"Search stats: {stats}")

    # Top queries
    top_queries = client.get_top_queries(hours=24, limit=10)
    print(f"Top queries: {top_queries}")
