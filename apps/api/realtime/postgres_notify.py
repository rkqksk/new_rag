"""
PostgreSQL LISTEN/NOTIFY - Realtime Database Events
====================================================

Database-level realtime notifications using PostgreSQL LISTEN/NOTIFY.

Features:
- Listen to database events in real-time
- Trigger notifications on INSERT/UPDATE/DELETE
- Automatic reconnection
- Channel-based subscriptions

This replaces Convex's automatic reactivity at the database level.

Version: v7.0.0+
"""

import asyncio
import json
import logging
from typing import Callable, Dict, List, Optional

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None

logger = logging.getLogger(__name__)


# ============================================================================
# PostgreSQL LISTEN/NOTIFY Manager
# ============================================================================


class PostgresNotifyManager:
    """
    PostgreSQL LISTEN/NOTIFY manager for realtime events

    Features:
    - Subscribe to database channels
    - Receive notifications on data changes
    - Trigger callbacks on events
    - Automatic reconnection
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "rag_enterprise",
        user: str = "postgres",
        password: str = "postgres",
    ):
        """
        Initialize PostgreSQL LISTEN/NOTIFY manager

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Username
            password: Password
        """
        if not PSYCOPG2_AVAILABLE:
            logger.warning("psycopg2 not available. PostgreSQL notifications disabled.")
            self.connection = None
            return

        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }

        self.connection = None
        self.cursor = None

        # Subscriptions: {channel: [callbacks]}
        self.subscriptions: Dict[str, List[Callable]] = {}

        # Listener task
        self.listener_task: Optional[asyncio.Task] = None

        # Connect
        self._connect()

        logger.info("✅ PostgreSQL LISTEN/NOTIFY manager initialized")

    def _connect(self):
        """Connect to PostgreSQL"""
        if not PSYCOPG2_AVAILABLE:
            return

        try:
            self.connection = psycopg2.connect(**self.connection_params)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.connection.cursor()
            logger.info("✅ Connected to PostgreSQL for LISTEN/NOTIFY")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.connection = None
            self.cursor = None

    def listen(self, channel: str, callback: Callable):
        """
        Listen to a PostgreSQL channel

        Args:
            channel: Channel name (e.g., 'product_changes')
            callback: Function to call on notification (async or sync)

        Usage:
            manager.listen('product_changes', handle_product_change)
        """
        if not self.cursor:
            logger.warning("Cannot listen: not connected to PostgreSQL")
            return

        try:
            # Subscribe to channel
            if channel not in self.subscriptions:
                self.cursor.execute(f"LISTEN {channel};")
                self.subscriptions[channel] = []
                logger.info(f"Listening on channel: {channel}")

            # Add callback
            self.subscriptions[channel].append(callback)

        except Exception as e:
            logger.error(f"Failed to listen on {channel}: {e}")

    def unlisten(self, channel: str):
        """Stop listening to a channel"""
        if not self.cursor:
            return

        try:
            self.cursor.execute(f"UNLISTEN {channel};")
            if channel in self.subscriptions:
                del self.subscriptions[channel]
            logger.info(f"Stopped listening on: {channel}")
        except Exception as e:
            logger.error(f"Failed to unlisten from {channel}: {e}")

    async def start_listening(self):
        """
        Start listening for notifications (async loop)

        This should be run as a background task
        """
        if not self.connection:
            logger.warning("Cannot start listening: not connected")
            return

        logger.info("Started listening for PostgreSQL notifications")

        try:
            while True:
                # Wait for notification (with timeout)
                if self.connection.poll() is None:
                    await asyncio.sleep(0.1)
                    continue

                # Process notifications
                while self.connection.notifies:
                    notify = self.connection.notifies.pop(0)
                    channel = notify.channel
                    payload = notify.payload

                    logger.debug(f"Received notification: {channel} -> {payload}")

                    # Call callbacks
                    if channel in self.subscriptions:
                        for callback in self.subscriptions[channel]:
                            try:
                                # Parse payload as JSON
                                try:
                                    data = json.loads(payload)
                                except json.JSONDecodeError:
                                    data = payload

                                # Call callback (support both sync and async)
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(channel, data)
                                else:
                                    callback(channel, data)

                            except Exception as e:
                                logger.error(f"Callback error: {e}")

        except Exception as e:
            logger.error(f"Listener error: {e}")
            # Attempt reconnection
            self._connect()

    def start_listener_task(self):
        """Start background listener task"""
        if self.listener_task is None or self.listener_task.done():
            self.listener_task = asyncio.create_task(self.start_listening())
            logger.info("✅ Listener task started")

    def stop_listener_task(self):
        """Stop background listener task"""
        if self.listener_task and not self.listener_task.done():
            self.listener_task.cancel()
            logger.info("Listener task stopped")

    def close(self):
        """Close connection"""
        self.stop_listener_task()
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("PostgreSQL connection closed")


# ============================================================================
# Database Trigger Setup
# ============================================================================


def create_notify_trigger_sql(table: str, channel: str) -> str:
    """
    Generate SQL to create a trigger that sends notifications

    Args:
        table: Table name
        channel: Notification channel

    Returns:
        SQL statements to create trigger
    """
    function_name = f"notify_{table}_changes"
    trigger_name = f"{table}_notify_trigger"

    sql = f"""
    -- Create notification function
    CREATE OR REPLACE FUNCTION {function_name}()
    RETURNS TRIGGER AS $$
    DECLARE
        payload JSON;
    BEGIN
        -- Build payload with operation and row data
        IF (TG_OP = 'DELETE') THEN
            payload = json_build_object(
                'operation', TG_OP,
                'table', TG_TABLE_NAME,
                'old', row_to_json(OLD)
            );
        ELSE
            payload = json_build_object(
                'operation', TG_OP,
                'table', TG_TABLE_NAME,
                'new', row_to_json(NEW)
            );
        END IF;

        -- Send notification
        PERFORM pg_notify('{channel}', payload::text);

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Create trigger
    DROP TRIGGER IF EXISTS {trigger_name} ON {table};
    CREATE TRIGGER {trigger_name}
    AFTER INSERT OR UPDATE OR DELETE ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION {function_name}();
    """

    return sql


def setup_table_notifications(connection, table: str, channel: Optional[str] = None):
    """
    Setup database triggers for table notifications

    Args:
        connection: psycopg2 connection
        table: Table name
        channel: Channel name (defaults to '{table}_changes')
    """
    if channel is None:
        channel = f"{table}_changes"

    sql = create_notify_trigger_sql(table, channel)

    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()
        cursor.close()
        logger.info(f"✅ Triggers created for {table} -> {channel}")
    except Exception as e:
        logger.error(f"Failed to create triggers: {e}")
        connection.rollback()


# ============================================================================
# Singleton Instance
# ============================================================================

_notify_manager: Optional[PostgresNotifyManager] = None


def get_notify_manager() -> PostgresNotifyManager:
    """Get or create PostgreSQL notify manager singleton"""
    global _notify_manager

    if _notify_manager is None:
        import os

        host = os.getenv("POSTGRES_HOST", "localhost")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        database = os.getenv("POSTGRES_DB", "rag_enterprise")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")

        _notify_manager = PostgresNotifyManager(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )

    return _notify_manager


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize manager
    manager = PostgresNotifyManager()

    # Setup trigger (run once)
    # setup_table_notifications(manager.connection, 'products')

    # Listen to channel
    async def handle_product_change(channel, data):
        print(f"Product changed: {data}")

    manager.listen("product_changes", handle_product_change)

    # Start listening (in background)
    manager.start_listener_task()

    # Keep running
    # asyncio.run(manager.start_listening())
