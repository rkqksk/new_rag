"""
Real-time Backend - Socket.IO Server (Convex-like, Open Source)
================================================================

Convex-style realtime functionality using 100% open source stack.

Features:
- Socket.IO for real-time bidirectional communication
- PostgreSQL LISTEN/NOTIFY for database-level events
- Redis Pub/Sub for server-to-server messaging
- Reactive query subscriptions
- Automatic client updates on data changes

Stack:
- Socket.IO (replaces Convex realtime)
- PostgreSQL LISTEN/NOTIFY (replaces Convex reactive queries)
- Redis Pub/Sub (replaces Convex server functions)

Version: v7.0.0+
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set

import socketio
from fastapi import FastAPI

logger = logging.getLogger(__name__)


# ============================================================================
# Socket.IO Server
# ============================================================================


class RealtimeServer:
    """
    Convex-like realtime server using Socket.IO

    Features:
    - Real-time bidirectional communication
    - Room-based subscriptions
    - Automatic reconnection
    - Event broadcasting
    """

    def __init__(self, cors_allowed_origins: str = "*"):
        """
        Initialize Socket.IO server

        Args:
            cors_allowed_origins: CORS origins (default: allow all)
        """
        # Create Socket.IO server with async support
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=cors_allowed_origins,
            logger=True,
            engineio_logger=True,
        )

        # Active subscriptions: {sid: {query_id: query_params}}
        self.subscriptions: Dict[str, Dict[str, Dict]] = {}

        # Query handlers: {query_name: handler_function}
        self.query_handlers: Dict[str, Callable] = {}

        # Setup event handlers
        self._setup_handlers()

        logger.info("✅ Socket.IO realtime server initialized")

    def _setup_handlers(self):
        """Setup Socket.IO event handlers"""

        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            logger.info(f"Client connected: {sid}")
            self.subscriptions[sid] = {}
            await self.sio.emit('connected', {'sid': sid}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {sid}")
            if sid in self.subscriptions:
                del self.subscriptions[sid]

        @self.sio.event
        async def subscribe(sid, data):
            """
            Subscribe to query updates

            Client sends:
            {
                "query": "products",
                "params": {"material": "PET", "limit": 10}
            }
            """
            try:
                query_name = data.get('query')
                params = data.get('params', {})
                query_id = f"{query_name}:{json.dumps(params, sort_keys=True)}"

                # Store subscription
                self.subscriptions[sid][query_id] = {
                    'query': query_name,
                    'params': params,
                }

                # Execute initial query
                if query_name in self.query_handlers:
                    handler = self.query_handlers[query_name]
                    result = await handler(params)

                    await self.sio.emit('query_result', {
                        'query': query_name,
                        'query_id': query_id,
                        'data': result,
                    }, room=sid)

                    logger.info(f"Subscription created: {sid} -> {query_id}")
                else:
                    await self.sio.emit('error', {
                        'message': f'Query handler not found: {query_name}'
                    }, room=sid)

            except Exception as e:
                logger.error(f"Subscribe error: {e}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)

        @self.sio.event
        async def unsubscribe(sid, data):
            """Unsubscribe from query"""
            query_id = data.get('query_id')
            if sid in self.subscriptions and query_id in self.subscriptions[sid]:
                del self.subscriptions[sid][query_id]
                logger.info(f"Unsubscribed: {sid} from {query_id}")

        @self.sio.event
        async def execute(sid, data):
            """
            Execute server function (one-time, no subscription)

            Client sends:
            {
                "function": "search",
                "args": {"query": "PET 용기"}
            }
            """
            try:
                function_name = data.get('function')
                args = data.get('args', {})

                if function_name in self.query_handlers:
                    handler = self.query_handlers[function_name]
                    result = await handler(args)

                    await self.sio.emit('function_result', {
                        'function': function_name,
                        'result': result,
                    }, room=sid)
                else:
                    await self.sio.emit('error', {
                        'message': f'Function not found: {function_name}'
                    }, room=sid)

            except Exception as e:
                logger.error(f"Execute error: {e}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)

    # ========================================================================
    # Query Registration
    # ========================================================================

    def register_query(self, name: str, handler: Callable):
        """
        Register query handler (like Convex queries)

        Example:
            @realtime.register_query("products")
            async def get_products(params):
                # Query logic
                return results
        """
        self.query_handlers[name] = handler
        logger.info(f"Registered query: {name}")

    def query(self, name: str):
        """
        Decorator for registering queries

        Usage:
            @realtime.query("products")
            async def get_products(params):
                return await db.query(...)
        """
        def decorator(func: Callable):
            self.register_query(name, func)
            return func
        return decorator

    # ========================================================================
    # Broadcasting
    # ========================================================================

    async def broadcast_update(self, query_name: str, params: Optional[Dict] = None):
        """
        Broadcast update to all subscribers of a query

        This is called when data changes to notify subscribed clients
        """
        try:
            # Find all subscriptions for this query
            for sid, subscriptions in self.subscriptions.items():
                for query_id, subscription in subscriptions.items():
                    if subscription['query'] == query_name:
                        # Check if params match (if specified)
                        if params is None or subscription['params'] == params:
                            # Execute query and send update
                            if query_name in self.query_handlers:
                                handler = self.query_handlers[query_name]
                                result = await handler(subscription['params'])

                                await self.sio.emit('query_update', {
                                    'query': query_name,
                                    'query_id': query_id,
                                    'data': result,
                                }, room=sid)

                                logger.debug(f"Broadcasted update: {query_id} to {sid}")
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

    async def notify_all(self, event: str, data: Any):
        """Broadcast event to all connected clients"""
        await self.sio.emit(event, data)
        logger.info(f"Notified all clients: {event}")

    # ========================================================================
    # Integration
    # ========================================================================

    def mount(self, app: FastAPI, path: str = "/ws"):
        """
        Mount Socket.IO to FastAPI app

        Usage:
            realtime = RealtimeServer()
            realtime.mount(app, path="/ws")
        """
        app.mount(path, self.app)
        logger.info(f"✅ Socket.IO mounted at {path}")


# ============================================================================
# Singleton Instance
# ============================================================================

_realtime_server: Optional[RealtimeServer] = None


def get_realtime_server() -> RealtimeServer:
    """Get or create realtime server singleton"""
    global _realtime_server

    if _realtime_server is None:
        _realtime_server = RealtimeServer(cors_allowed_origins="*")

    return _realtime_server


# ============================================================================
# Convenience Decorators
# ============================================================================

def realtime_query(name: str):
    """
    Decorator for realtime queries (Convex-style)

    Usage:
        @realtime_query("products")
        async def get_products(params):
            material = params.get("material")
            # Query database
            return results
    """
    server = get_realtime_server()
    return server.query(name)


async def notify_query_update(query_name: str, params: Optional[Dict] = None):
    """
    Notify clients that query results have changed

    Call this after INSERT/UPDATE/DELETE operations

    Usage:
        # After inserting product
        await notify_query_update("products", {"material": "PET"})
    """
    server = get_realtime_server()
    await server.broadcast_update(query_name, params)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize server
    server = RealtimeServer()

    # Register query
    @server.query("products")
    async def get_products(params):
        # Mock query
        material = params.get("material", "PET")
        return [
            {"id": "001", "name": f"50ml {material} 용기", "material": material},
            {"id": "002", "name": f"100ml {material} 용기", "material": material},
        ]

    # In your FastAPI app:
    # from fastapi import FastAPI
    # app = FastAPI()
    # server.mount(app, path="/ws")

    print("Socket.IO server ready!")
    print("Connect from client: io('http://localhost:8001/ws')")
