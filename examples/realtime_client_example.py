"""
Realtime Client Example (Python)
==================================

Example of using the realtime backend from Python clients.

This demonstrates:
- Connecting to Socket.IO server
- Subscribing to queries
- Executing server functions
- Handling realtime updates

Version: v7.0.0+
"""

import asyncio
import json
from typing import Any, Callable, Dict, Optional

try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    print("❌ python-socketio not installed. Run: pip install python-socketio")
    SOCKETIO_AVAILABLE = False


# ============================================================================
# Realtime Client
# ============================================================================


class RealtimeClient:
    """
    Python client for RAG Enterprise realtime backend

    Features:
    - Subscribe to queries (like Convex useQuery)
    - Execute server functions (like Convex useMutation)
    - Receive automatic updates
    """

    def __init__(self, server_url: str = "http://localhost:8001"):
        """
        Initialize realtime client

        Args:
            server_url: Server URL
        """
        if not SOCKETIO_AVAILABLE:
            raise ImportError("python-socketio not available")

        self.sio = socketio.AsyncClient()
        self.server_url = server_url

        # Subscriptions: {query_id: callback}
        self.subscriptions: Dict[str, Callable] = {}

        # Setup event handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup Socket.IO event handlers"""

        @self.sio.event
        async def connect():
            print("✅ Connected to realtime server")

        @self.sio.event
        async def disconnect():
            print("🔴 Disconnected from realtime server")

        @self.sio.event
        async def query_update(data):
            """Handle query updates"""
            query_id = data.get("query_id")
            if query_id in self.subscriptions:
                callback = self.subscriptions[query_id]
                await callback(data.get("data"))

        @self.sio.event
        async def function_result(data):
            """Handle function results"""
            if data.get("success"):
                print(f"✅ Function executed successfully")
            else:
                print(f"❌ Function failed: {data.get('error')}")

        @self.sio.event
        async def error(error):
            """Handle errors"""
            print(f"❌ Error: {error.get('message')}")

    async def connect(self):
        """Connect to realtime server"""
        await self.sio.connect(
            self.server_url,
            socketio_path='/socket.io'
        )
        print(f"🔗 Connecting to {self.server_url}...")

    async def disconnect(self):
        """Disconnect from server"""
        await self.sio.disconnect()

    # ========================================================================
    # Query Subscriptions (like Convex useQuery)
    # ========================================================================

    async def subscribe(
        self,
        query_name: str,
        params: Dict[str, Any],
        callback: Callable
    ) -> str:
        """
        Subscribe to query with automatic updates

        Args:
            query_name: Query identifier (e.g., "products", "search_results")
            params: Query parameters
            callback: Async function to call on updates

        Returns:
            query_id for unsubscribing

        Usage:
            async def on_products_update(data):
                print(f"Products updated: {data}")

            query_id = await client.subscribe(
                "products",
                {"material": "PET"},
                on_products_update
            )
        """
        import uuid
        query_id = f"{query_name}_{uuid.uuid4().hex[:8]}"

        # Store callback
        self.subscriptions[query_id] = callback

        # Send subscription request
        await self.sio.emit('subscribe', {
            'query_id': query_id,
            'query_name': query_name,
            'params': params
        })

        print(f"📡 Subscribed to query: {query_name} (id: {query_id})")
        return query_id

    async def unsubscribe(self, query_id: str):
        """
        Unsubscribe from query

        Args:
            query_id: Query ID from subscribe()
        """
        if query_id in self.subscriptions:
            del self.subscriptions[query_id]

        await self.sio.emit('unsubscribe', {'query_id': query_id})
        print(f"🔕 Unsubscribed from query: {query_id}")

    # ========================================================================
    # Server Functions (like Convex useMutation)
    # ========================================================================

    async def execute(
        self,
        function_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute server function

        Args:
            function_name: Function identifier
            params: Function parameters

        Returns:
            Function result

        Usage:
            result = await client.execute(
                "create_product",
                {
                    "name": "New Product",
                    "material": "PET",
                    "capacity": "100ml"
                }
            )
        """
        await self.sio.emit('execute', {
            'function_name': function_name,
            'params': params
        })

        print(f"⚙️  Executing function: {function_name}")

        # Wait for result (simplified - in production use proper async/await pattern)
        await asyncio.sleep(0.1)

    # ========================================================================
    # Convenience Methods
    # ========================================================================

    async def query_products(
        self,
        material: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """Query products with optional material filter"""
        params = {}
        if material:
            params['material'] = material

        if callback is None:
            async def default_callback(data):
                print(f"Products: {len(data)} results")
                for product in data:
                    print(f"  - {product.get('name')}")

            callback = default_callback

        return await self.subscribe("products", params, callback)

    async def query_search(
        self,
        query: str,
        top_k: int = 5,
        callback: Optional[Callable] = None
    ) -> str:
        """Query search results"""
        params = {'query': query, 'top_k': top_k}

        if callback is None:
            async def default_callback(data):
                print(f"Search results: {len(data)} results")
                for i, result in enumerate(data, 1):
                    print(f"  {i}. {result.get('text')[:100]}...")

            callback = default_callback

        return await self.subscribe("search_results", params, callback)


# ============================================================================
# Example Usage
# ============================================================================


async def example_basic():
    """Basic usage example"""
    print("=" * 60)
    print("Example 1: Basic Query Subscription")
    print("=" * 60)

    client = RealtimeClient()
    await client.connect()

    # Subscribe to products
    async def on_products(data):
        print(f"\n📦 Products updated ({len(data)} items):")
        for product in data[:5]:  # Show first 5
            print(f"  - {product.get('name')}")

    query_id = await client.subscribe(
        "products",
        {"material": "PET"},
        on_products
    )

    # Keep listening for 10 seconds
    print("\n⏳ Listening for updates (10 seconds)...")
    await asyncio.sleep(10)

    # Unsubscribe
    await client.unsubscribe(query_id)
    await client.disconnect()


async def example_multiple_queries():
    """Multiple query subscriptions"""
    print("\n" + "=" * 60)
    print("Example 2: Multiple Query Subscriptions")
    print("=" * 60)

    client = RealtimeClient()
    await client.connect()

    # Subscribe to multiple queries
    pet_id = await client.query_products(material="PET")
    pp_id = await client.query_products(material="PP")

    async def on_search(data):
        print(f"\n🔍 Search results: {len(data)} items")

    search_id = await client.query_search(
        "용기",
        top_k=10,
        callback=on_search
    )

    # Listen for updates
    print("\n⏳ Listening to 3 queries simultaneously (15 seconds)...")
    await asyncio.sleep(15)

    # Cleanup
    await client.unsubscribe(pet_id)
    await client.unsubscribe(pp_id)
    await client.unsubscribe(search_id)
    await client.disconnect()


async def example_server_functions():
    """Execute server functions"""
    print("\n" + "=" * 60)
    print("Example 3: Server Function Execution")
    print("=" * 60)

    client = RealtimeClient()
    await client.connect()

    # Execute functions
    await client.execute("log_activity", {
        "user_id": "user_123",
        "action": "search",
        "query": "PET 용기"
    })

    await client.execute("track_event", {
        "event": "product_view",
        "product_id": "001"
    })

    await asyncio.sleep(2)
    await client.disconnect()


async def main():
    """Run all examples"""
    if not SOCKETIO_AVAILABLE:
        return

    print("\n🚀 RAG Enterprise - Realtime Client Examples\n")

    # Run examples
    await example_basic()
    await example_multiple_queries()
    await example_server_functions()

    print("\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
