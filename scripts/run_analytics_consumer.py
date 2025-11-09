#!/usr/bin/env python3
"""
Analytics Consumer Daemon (v6.0.0)
==================================

Background service that consumes events from Kafka and inserts into ClickHouse.

Usage:
    # Production
    python scripts/run_analytics_consumer.py

    # Docker
    docker-compose exec api python scripts/run_analytics_consumer.py

Version: v6.0.0
"""

import logging
import os
import signal
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.analytics_pipeline import AnalyticsConsumer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/analytics_consumer.log"),
    ],
)
logger = logging.getLogger(__name__)

# Global consumer instance
consumer: AnalyticsConsumer = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {sig}, shutting down...")
    if consumer:
        logger.info("Flushing remaining events...")
        consumer._flush_search_buffer()
        consumer._flush_user_buffer()
        consumer._flush_performance_buffer()
    logger.info("✅ Analytics consumer stopped")
    sys.exit(0)


def main():
    """Main consumer loop"""
    global consumer

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get configuration from environment
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "analytics-consumer")
    batch_size = int(os.getenv("KAFKA_BATCH_SIZE", "100"))

    logger.info("=" * 60)
    logger.info("Analytics Consumer Starting")
    logger.info("=" * 60)
    logger.info(f"Kafka: {bootstrap_servers}")
    logger.info(f"Group: {group_id}")
    logger.info(f"Batch Size: {batch_size}")
    logger.info("=" * 60)

    # Create consumer
    consumer = AnalyticsConsumer(
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        batch_size=batch_size,
    )

    if not consumer.consumer:
        logger.error("❌ Kafka not available. Consumer cannot start.")
        logger.error("Make sure Kafka is running and accessible.")
        sys.exit(1)

    # Start consuming
    logger.info("✅ Consumer started. Press Ctrl+C to stop.")
    logger.info("Listening on topics: search-events, user-events, performance-events")

    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, shutting down...")
    except Exception as e:
        logger.error(f"Consumer error: {e}", exc_info=True)
    finally:
        signal_handler(signal.SIGTERM, None)


if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    main()
