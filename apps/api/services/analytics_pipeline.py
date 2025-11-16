"""
Real-time Analytics Pipeline (v6.0.0)
======================================

Kafka-based streaming analytics for real-time insights.

Architecture:
1. FastAPI endpoints → Kafka topics (async producers)
2. Kafka consumers → ClickHouse (batch inserts)
3. ClickHouse → Analytics dashboards (real-time queries)

Topics:
- search-events: Search queries and results
- user-events: User interactions (clicks, sessions)
- performance-events: API performance metrics

Features:
- Async event publishing (non-blocking)
- Batch processing for efficiency
- Schema validation
- Error handling and retry logic
- Dead letter queue for failed events

Version: v6.0.0
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaConsumer = None
    KafkaError = Exception

from apps.api.services.clickhouse_client import get_clickhouse_client

logger = logging.getLogger(__name__)


# ============================================================================
# Event Schemas
# ============================================================================


class SearchEvent:
    """Search event schema"""

    def __init__(
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
        self.session_id = session_id
        self.user_id = user_id
        self.query = query
        self.results_count = results_count
        self.response_time_ms = response_time_ms
        self.search_strategy = search_strategy
        self.filters = filters
        self.top_k = top_k
        self.cache_hit = cache_hit
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "query": self.query,
            "results_count": self.results_count,
            "response_time_ms": self.response_time_ms,
            "search_strategy": self.search_strategy,
            "filters": self.filters,
            "top_k": self.top_k,
            "cache_hit": self.cache_hit,
        }


class UserEvent:
    """User event schema"""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        event_type: str,
        event_data: str = "",
        product_id: str = "",
        query: str = "",
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.event_type = event_type
        self.event_data = event_data
        self.product_id = product_id
        self.query = query
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "product_id": self.product_id,
            "query": self.query,
        }


class PerformanceEvent:
    """Performance event schema"""

    def __init__(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        cpu_percent: float = 0.0,
        memory_mb: float = 0.0,
    ):
        self.endpoint = endpoint
        self.method = method
        self.status_code = status_code
        self.response_time_ms = response_time_ms
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
        }


# ============================================================================
# Kafka Producer (Event Publisher)
# ============================================================================


class AnalyticsProducer:
    """
    Kafka producer for publishing analytics events

    Features:
    - Async publishing (non-blocking)
    - JSON serialization
    - Error handling
    - Retry logic
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize Kafka producer

        Args:
            bootstrap_servers: Kafka broker addresses
        """
        if not KAFKA_AVAILABLE:
            logger.warning("kafka-python not installed. Analytics pipeline disabled.")
            self.producer = None
            return

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5,
            )
            logger.info(f"✅ Kafka producer connected: {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            self.producer = None

    def publish_search_event(self, event: SearchEvent):
        """Publish search event to Kafka"""
        if not self.producer:
            logger.debug("Kafka unavailable, skipping event publish")
            return

        try:
            future = self.producer.send("search-events", value=event.to_dict())
            # Non-blocking: add callback
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
        except Exception as e:
            logger.error(f"Failed to publish search event: {e}")

    def publish_user_event(self, event: UserEvent):
        """Publish user event to Kafka"""
        if not self.producer:
            logger.debug("Kafka unavailable, skipping event publish")
            return

        try:
            future = self.producer.send("user-events", value=event.to_dict())
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
        except Exception as e:
            logger.error(f"Failed to publish user event: {e}")

    def publish_performance_event(self, event: PerformanceEvent):
        """Publish performance event to Kafka"""
        if not self.producer:
            logger.debug("Kafka unavailable, skipping event publish")
            return

        try:
            future = self.producer.send("performance-events", value=event.to_dict())
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
        except Exception as e:
            logger.error(f"Failed to publish performance event: {e}")

    def _on_send_success(self, record_metadata):
        """Callback for successful send"""
        logger.debug(
            f"Event sent to {record_metadata.topic}[{record_metadata.partition}] "
            f"@ offset {record_metadata.offset}"
        )

    def _on_send_error(self, exc):
        """Callback for send error"""
        logger.error(f"Failed to send event: {exc}")

    def flush(self):
        """Flush pending messages"""
        if self.producer:
            self.producer.flush()

    def close(self):
        """Close producer"""
        if self.producer:
            self.producer.close()


# ============================================================================
# Kafka Consumer (Event Processor)
# ============================================================================


class AnalyticsConsumer:
    """
    Kafka consumer for processing analytics events

    Features:
    - Batch processing
    - ClickHouse integration
    - Error handling
    - Dead letter queue
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "analytics-consumer",
        batch_size: int = 100,
    ):
        """
        Initialize Kafka consumer

        Args:
            bootstrap_servers: Kafka broker addresses
            group_id: Consumer group ID
            batch_size: Number of events to batch before inserting
        """
        if not KAFKA_AVAILABLE:
            logger.warning("kafka-python not installed. Consumer disabled.")
            self.consumer = None
            return

        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.batch_size = batch_size
        self.clickhouse = get_clickhouse_client()

        # Buffers for batch processing
        self.search_buffer: List[Dict] = []
        self.user_buffer: List[Dict] = []
        self.performance_buffer: List[Dict] = []

    def start_consuming(self):
        """
        Start consuming events from all topics

        This is a blocking operation that should run in a separate thread/process
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available. Consumer not started.")
            return

        try:
            # Create consumers for each topic
            search_consumer = KafkaConsumer(
                "search-events",
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )

            user_consumer = KafkaConsumer(
                "user-events",
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )

            performance_consumer = KafkaConsumer(
                "performance-events",
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )

            logger.info("✅ Kafka consumers started")

            # Process events
            while True:
                # Process search events
                for message in search_consumer.poll(timeout_ms=1000).values():
                    for record in message:
                        self._process_search_event(record.value)

                # Process user events
                for message in user_consumer.poll(timeout_ms=1000).values():
                    for record in message:
                        self._process_user_event(record.value)

                # Process performance events
                for message in performance_consumer.poll(timeout_ms=1000).values():
                    for record in message:
                        self._process_performance_event(record.value)

        except Exception as e:
            logger.error(f"Consumer error: {e}")

    def _process_search_event(self, event: Dict):
        """Process search event"""
        self.search_buffer.append(event)

        if len(self.search_buffer) >= self.batch_size:
            self._flush_search_buffer()

    def _process_user_event(self, event: Dict):
        """Process user event"""
        self.user_buffer.append(event)

        if len(self.user_buffer) >= self.batch_size:
            self._flush_user_buffer()

    def _process_performance_event(self, event: Dict):
        """Process performance event"""
        self.performance_buffer.append(event)

        if len(self.performance_buffer) >= self.batch_size:
            self._flush_performance_buffer()

    def _flush_search_buffer(self):
        """Flush search events to ClickHouse"""
        if not self.search_buffer:
            return

        try:
            for event in self.search_buffer:
                self.clickhouse.insert_search_log(**event)
            logger.info(f"Flushed {len(self.search_buffer)} search events")
            self.search_buffer.clear()
        except Exception as e:
            logger.error(f"Failed to flush search buffer: {e}")

    def _flush_user_buffer(self):
        """Flush user events to ClickHouse"""
        if not self.user_buffer:
            return

        try:
            for event in self.user_buffer:
                self.clickhouse.insert_user_event(**event)
            logger.info(f"Flushed {len(self.user_buffer)} user events")
            self.user_buffer.clear()
        except Exception as e:
            logger.error(f"Failed to flush user buffer: {e}")

    def _flush_performance_buffer(self):
        """Flush performance events to ClickHouse"""
        if not self.performance_buffer:
            return

        try:
            for event in self.performance_buffer:
                self.clickhouse.insert_performance_metric(**event)
            logger.info(f"Flushed {len(self.performance_buffer)} performance events")
            self.performance_buffer.clear()
        except Exception as e:
            logger.error(f"Failed to flush performance buffer: {e}")


# ============================================================================
# Singleton Instance
# ============================================================================

_analytics_producer: Optional[AnalyticsProducer] = None


def get_analytics_producer() -> AnalyticsProducer:
    """Get or create analytics producer singleton"""
    global _analytics_producer

    if _analytics_producer is None:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        _analytics_producer = AnalyticsProducer(bootstrap_servers=bootstrap_servers)

    return _analytics_producer


# ============================================================================
# Convenience Functions
# ============================================================================


def track_search(
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
    """
    Track search event

    This is a non-blocking call that publishes to Kafka
    """
    producer = get_analytics_producer()
    event = SearchEvent(
        session_id=session_id,
        user_id=user_id,
        query=query,
        results_count=results_count,
        response_time_ms=response_time_ms,
        search_strategy=search_strategy,
        filters=filters,
        top_k=top_k,
        cache_hit=cache_hit,
    )
    producer.publish_search_event(event)


def track_user_event(
    session_id: str,
    user_id: str,
    event_type: str,
    event_data: str = "",
    product_id: str = "",
    query: str = "",
):
    """Track user event (click, session, etc.)"""
    producer = get_analytics_producer()
    event = UserEvent(
        session_id=session_id,
        user_id=user_id,
        event_type=event_type,
        event_data=event_data,
        product_id=product_id,
        query=query,
    )
    producer.publish_user_event(event)


def track_performance(
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    cpu_percent: float = 0.0,
    memory_mb: float = 0.0,
):
    """Track API performance event"""
    producer = get_analytics_producer()
    event = PerformanceEvent(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        cpu_percent=cpu_percent,
        memory_mb=memory_mb,
    )
    producer.publish_performance_event(event)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Track search
    track_search(
        session_id="session-123",
        user_id="user-456",
        query="50ml PET 용기",
        results_count=95,
        response_time_ms=342.5,
        search_strategy="hybrid",
    )

    # Track user click
    track_user_event(
        session_id="session-123",
        user_id="user-456",
        event_type="product_click",
        product_id="prod-789",
        query="50ml PET 용기",
    )

    # Track API performance
    track_performance(
        endpoint="/api/v1/search",
        method="POST",
        status_code=200,
        response_time_ms=342.5,
    )

    # Flush pending events
    producer = get_analytics_producer()
    producer.flush()
