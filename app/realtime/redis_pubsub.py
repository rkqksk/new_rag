"""
Redis Pub/Sub - Multi-Server Realtime Synchronization
======================================================

Redis-based publish/subscribe for multi-server realtime architecture.

Features:
- Publish events across server instances
- Subscribe to channels
- Server-to-server messaging
- Event broadcasting

This enables horizontal scaling of realtime servers.

Version: v7.0.0+
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

try:
    import aioredis
    AIOREDIS_AVAILABLE = True
except ImportError:
    AIOREDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)


# ============================================================================
# Redis Pub/Sub Manager
# ============================================================================


class RedisPubSubManager:
    """
    Redis Pub/Sub manager for multi-server realtime sync

    Features:
    - Publish events to channels
    - Subscribe to channels
    - Handle incoming messages
    - Server-to-server broadcasting
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:16379",
    ):
        """
        Initialize Redis Pub/Sub manager

        Args:
            redis_url: Redis connection URL
        """
        if not AIOREDIS_AVAILABLE:
            logger.warning("aioredis not available. Redis Pub/Sub disabled.")
            self.redis = None
            self.pubsub = None
            return

        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None

        # Subscriptions: {channel: [callbacks]}
        self.subscriptions: Dict[str, List[Callable]] = {}

        # Listener task
        self.listener_task: Optional[asyncio.Task] = None

        logger.info("✅ Redis Pub/Sub manager initialized")

    async def connect(self):
        """Connect to Redis"""
        if not AIOREDIS_AVAILABLE:
            return

        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis.pubsub()
            logger.info("✅ Connected to Redis for Pub/Sub")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
            self.pubsub = None

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.listener_task and not self.listener_task.done():
            self.listener_task.cancel()

        if self.pubsub:
            await self.pubsub.close()

        if self.redis:
            await self.redis.close()

        logger.info("Redis Pub/Sub disconnected")

    # ========================================================================
    # Publishing
    # ========================================================================

    async def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publish message to channel

        Args:
            channel: Channel name
            message: Message data

        Usage:
            await pubsub.publish('query_updates', {
                'query': 'products',
                'params': {'material': 'PET'},
                'data': [...]
            })
        """
        if not self.redis:
            logger.warning("Cannot publish: not connected to Redis")
            return

        try:
            payload = json.dumps(message)
            await self.redis.publish(channel, payload)
            logger.debug(f"Published to {channel}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")

    async def publish_query_update(
        self,
        query_name: str,
        params: Dict[str, Any],
        data: Any
    ):
        """
        Publish query update event

        Args:
            query_name: Query identifier
            params: Query parameters
            data: Updated data
        """
        await self.publish('query_updates', {
            'type': 'query_update',
            'query': query_name,
            'params': params,
            'data': data,
        })

    async def publish_data_change(
        self,
        table: str,
        operation: str,
        data: Dict[str, Any]
    ):
        """
        Publish database change event

        Args:
            table: Table name
            operation: INSERT/UPDATE/DELETE
            data: Changed data
        """
        await self.publish('data_changes', {
            'type': 'data_change',
            'table': table,
            'operation': operation,
            'data': data,
        })

    # ========================================================================
    # Subscribing
    # ========================================================================

    async def subscribe(self, channel: str, callback: Callable):
        """
        Subscribe to channel

        Args:
            channel: Channel name
            callback: Async function to call on messages

        Usage:
            async def handle_update(channel, message):
                print(f"Update: {message}")

            await pubsub.subscribe('query_updates', handle_update)
        """
        if not self.pubsub:
            logger.warning("Cannot subscribe: not connected to Redis")
            return

        try:
            # Subscribe to channel
            if channel not in self.subscriptions:
                await self.pubsub.subscribe(channel)
                self.subscriptions[channel] = []
                logger.info(f"Subscribed to channel: {channel}")

            # Add callback
            self.subscriptions[channel].append(callback)

            # Start listener if not running
            if self.listener_task is None or self.listener_task.done():
                self.listener_task = asyncio.create_task(self._listen())

        except Exception as e:
            logger.error(f"Failed to subscribe to {channel}: {e}")

    async def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        if not self.pubsub:
            return

        try:
            await self.pubsub.unsubscribe(channel)
            if channel in self.subscriptions:
                del self.subscriptions[channel]
            logger.info(f"Unsubscribed from: {channel}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {channel}: {e}")

    # ========================================================================
    # Listener
    # ========================================================================

    async def _listen(self):
        """
        Listen for messages (async loop)

        This should run as a background task
        """
        if not self.pubsub:
            logger.warning("Cannot listen: not connected")
            return

        logger.info("Started listening for Redis messages")

        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    channel = message['channel']
                    payload = message['data']

                    logger.debug(f"Received message: {channel} -> {payload}")

                    # Parse JSON
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        data = payload

                    # Call callbacks
                    if channel in self.subscriptions:
                        for callback in self.subscriptions[channel]:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(channel, data)
                                else:
                                    callback(channel, data)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")

        except Exception as e:
            logger.error(f"Listener error: {e}")

    # ========================================================================
    # Convenience Methods
    # ========================================================================

    async def subscribe_to_query_updates(self, callback: Callable):
        """Subscribe to query update events"""
        await self.subscribe('query_updates', callback)

    async def subscribe_to_data_changes(self, callback: Callable):
        """Subscribe to data change events"""
        await self.subscribe('data_changes', callback)


# ============================================================================
# Singleton Instance
# ============================================================================

_pubsub_manager: Optional[RedisPubSubManager] = None


async def get_pubsub_manager() -> RedisPubSubManager:
    """Get or create Redis Pub/Sub manager singleton"""
    global _pubsub_manager

    if _pubsub_manager is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:16379")

        _pubsub_manager = RedisPubSubManager(redis_url=redis_url)
        await _pubsub_manager.connect()

    return _pubsub_manager


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    async def main():
        # Initialize manager
        manager = RedisPubSubManager()
        await manager.connect()

        # Subscribe to updates
        async def handle_update(channel, message):
            print(f"Received update: {message}")

        await manager.subscribe('query_updates', handle_update)

        # Publish update
        await manager.publish_query_update(
            query_name='products',
            params={'material': 'PET'},
            data=[{'id': '001', 'name': '50ml PET 용기'}]
        )

        # Keep running
        await asyncio.sleep(10)

        # Cleanup
        await manager.disconnect()

    asyncio.run(main())
