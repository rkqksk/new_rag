"""
Server-Sent Events (SSE) Manager for Phase 8.1
Real-time streaming for search results, pipeline progress, and analytics
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class SSEEvent:
    """Server-Sent Event"""
    event: str  # Event type (e.g., 'search_result', 'pipeline_update')
    data: Dict[str, Any]  # Event data
    id: Optional[str] = None  # Event ID
    retry: Optional[int] = None  # Retry interval (ms)

    def format(self) -> str:
        """
        Format event as SSE message

        SSE format:
        id: <event-id>
        event: <event-type>
        data: <json-data>
        retry: <retry-ms>

        """
        lines = []

        if self.id:
            lines.append(f"id: {self.id}")

        if self.event:
            lines.append(f"event: {self.event}")

        if self.data:
            data_json = json.dumps(self.data)
            lines.append(f"data: {data_json}")

        if self.retry:
            lines.append(f"retry: {self.retry}")

        # SSE messages end with double newline
        return "\n".join(lines) + "\n\n"


class SSEConnection:
    """Single SSE connection"""

    def __init__(self, client_id: str, channels: List[str]):
        """
        Initialize SSE connection

        Args:
            client_id: Unique client identifier
            channels: List of channel names to subscribe to
        """
        self.client_id = client_id
        self.channels = set(channels)
        self.queue: asyncio.Queue = asyncio.Queue()
        self.connected_at = datetime.now()
        self.last_event_id = 0

    async def send(self, event: SSEEvent):
        """Send event to this connection"""
        await self.queue.put(event)

    async def receive(self) -> SSEEvent:
        """Receive next event"""
        return await self.queue.get()

    def subscribe(self, channel: str):
        """Subscribe to additional channel"""
        self.channels.add(channel)

    def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        self.channels.discard(channel)


class SSEManager:
    """
    Server-Sent Events Manager

    Features:
    - Multi-client connection management
    - Channel-based event routing
    - Event filtering and throttling
    - Connection keepalive
    - Automatic cleanup

    Channels:
    - search: Real-time search results
    - pipeline: Pipeline progress updates
    - analytics: Analytics dashboard updates
    - notifications: System notifications

    Example:
        >>> manager = SSEManager()
        >>>
        >>> # Client connects
        >>> async for event in manager.subscribe(client_id="abc", channels=["search"]):
        ...     # Stream events to client
        ...     yield event.format()
        >>>
        >>> # Emit event
        >>> await manager.emit(
        ...     channel="search",
        ...     event="search_result",
        ...     data={"query": "100ml PET", "result": {...}}
        ... )
    """

    def __init__(
        self,
        keepalive_interval: int = 30,  # seconds
        max_queue_size: int = 100
    ):
        """
        Initialize SSE Manager

        Args:
            keepalive_interval: Keepalive ping interval (seconds)
            max_queue_size: Maximum events per client queue
        """
        self.connections: Dict[str, SSEConnection] = {}
        self.channels: Dict[str, List[str]] = defaultdict(list)  # channel -> client_ids

        self.keepalive_interval = keepalive_interval
        self.max_queue_size = max_queue_size

        self.stats = {
            'total_connections': 0,
            'total_events_sent': 0,
            'active_connections': 0
        }

        # Start keepalive task
        self.keepalive_task = None

        logger.info("✅ SSEManager initialized")

    async def subscribe(
        self,
        client_id: Optional[str] = None,
        channels: Optional[List[str]] = None
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        Subscribe to SSE events

        Args:
            client_id: Optional client ID (auto-generated if not provided)
            channels: Channels to subscribe to (default: all)

        Yields:
            SSEEvent objects

        Example:
            >>> async for event in manager.subscribe(channels=["search"]):
            ...     yield event.format()
        """
        # Generate client ID if not provided
        if client_id is None:
            client_id = str(uuid.uuid4())

        # Default channels
        if channels is None:
            channels = ["search", "pipeline", "analytics", "notifications"]

        # Create connection
        connection = SSEConnection(client_id, channels)
        self.connections[client_id] = connection

        # Register in channels
        for channel in channels:
            self.channels[channel].append(client_id)

        # Update stats
        self.stats['total_connections'] += 1
        self.stats['active_connections'] = len(self.connections)

        logger.info(f"✅ Client connected: {client_id} (channels: {channels})")

        try:
            # Start keepalive if not running
            if self.keepalive_task is None or self.keepalive_task.done():
                self.keepalive_task = asyncio.create_task(self._keepalive_loop())

            # Stream events
            while True:
                event = await connection.receive()
                yield event

                self.stats['total_events_sent'] += 1

        except asyncio.CancelledError:
            logger.info(f"Client disconnected: {client_id}")
        finally:
            # Cleanup
            await self._cleanup_connection(client_id)

    async def emit(
        self,
        channel: str,
        event: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None
    ):
        """
        Emit event to channel

        Args:
            channel: Target channel
            event: Event type
            data: Event data
            event_id: Optional event ID

        Example:
            >>> await manager.emit(
            ...     channel="search",
            ...     event="search_result",
            ...     data={"query": "100ml PET", "results": [...]}
            ... )
        """
        # Get clients subscribed to this channel
        client_ids = self.channels.get(channel, [])

        if not client_ids:
            logger.debug(f"No clients subscribed to channel: {channel}")
            return

        # Create event
        sse_event = SSEEvent(
            event=event,
            data=data,
            id=event_id or str(uuid.uuid4())
        )

        # Send to all subscribed clients
        for client_id in client_ids:
            connection = self.connections.get(client_id)
            if connection:
                try:
                    await connection.send(sse_event)
                except Exception as e:
                    logger.error(f"Failed to send event to {client_id}: {e}")

        logger.debug(f"Emitted event '{event}' to {len(client_ids)} clients on channel '{channel}'")

    async def emit_to_client(
        self,
        client_id: str,
        event: str,
        data: Dict[str, Any]
    ):
        """
        Emit event to specific client

        Args:
            client_id: Target client ID
            event: Event type
            data: Event data

        Example:
            >>> await manager.emit_to_client(
            ...     client_id="abc123",
            ...     event="notification",
            ...     data={"message": "Pipeline complete"}
            ... )
        """
        connection = self.connections.get(client_id)
        if not connection:
            logger.warning(f"Client not found: {client_id}")
            return

        sse_event = SSEEvent(
            event=event,
            data=data,
            id=str(uuid.uuid4())
        )

        await connection.send(sse_event)

    async def _keepalive_loop(self):
        """Send periodic keepalive pings"""
        while self.connections:
            try:
                await asyncio.sleep(self.keepalive_interval)

                # Send keepalive to all connections
                keepalive_event = SSEEvent(
                    event="keepalive",
                    data={"timestamp": datetime.now().isoformat()}
                )

                for client_id, connection in list(self.connections.items()):
                    try:
                        await connection.send(keepalive_event)
                    except Exception as e:
                        logger.error(f"Keepalive failed for {client_id}: {e}")
                        await self._cleanup_connection(client_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Keepalive loop error: {e}")

    async def _cleanup_connection(self, client_id: str):
        """Cleanup disconnected client"""
        connection = self.connections.pop(client_id, None)

        if connection:
            # Remove from channels
            for channel in connection.channels:
                if client_id in self.channels[channel]:
                    self.channels[channel].remove(client_id)

            # Update stats
            self.stats['active_connections'] = len(self.connections)

            logger.debug(f"Cleaned up connection: {client_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        return {
            **self.stats,
            'channels': {
                channel: len(clients)
                for channel, clients in self.channels.items()
            }
        }

    def get_active_clients(self, channel: Optional[str] = None) -> List[str]:
        """
        Get active client IDs

        Args:
            channel: Optional channel filter

        Returns:
            List of client IDs
        """
        if channel:
            return self.channels.get(channel, [])
        else:
            return list(self.connections.keys())

    async def shutdown(self):
        """Shutdown manager and disconnect all clients"""
        # Cancel keepalive
        if self.keepalive_task:
            self.keepalive_task.cancel()

        # Close all connections
        for client_id in list(self.connections.keys()):
            await self._cleanup_connection(client_id)

        logger.info("SSEManager shutdown complete")

    def __repr__(self):
        return (
            f"SSEManager("
            f"active_connections={self.stats['active_connections']}, "
            f"channels={len(self.channels)})"
        )
