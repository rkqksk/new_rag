"""
MQTT Service - Industrial IoT Messaging

v7.2.0 - Edge Computing Platform
MQTT broker integration for sensor data streaming and device control

Features:
- Pub/Sub messaging
- QoS levels (0, 1, 2)
- Retained messages
- Last Will and Testament
- TLS/SSL encryption
- Auto-reconnect
- Topic wildcards
- Message buffering
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import json
import threading
import time
from enum import Enum

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

logger = logging.getLogger(__name__)


class QoS(int, Enum):
    """MQTT Quality of Service levels"""
    AT_MOST_ONCE = 0  # Fire and forget
    AT_LEAST_ONCE = 1  # Acknowledged delivery
    EXACTLY_ONCE = 2  # Assured delivery


class MQTTStatus(str, Enum):
    """MQTT connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class MQTTService:
    """
    MQTT Service for Industrial IoT

    Manages MQTT messaging with:
    - Pub/Sub pattern
    - Auto-reconnect
    - Message buffering
    - Topic management
    """

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        keepalive: int = 60
    ):
        """
        Initialize MQTT Service

        Args:
            broker_host: MQTT broker hostname/IP
            broker_port: MQTT broker port (1883 for TCP, 8883 for TLS)
            client_id: Client identifier (None = auto-generate)
            username: Username for authentication
            password: Password for authentication
            use_tls: Enable TLS/SSL encryption
            keepalive: Keep-alive interval in seconds
        """
        if not MQTT_AVAILABLE:
            raise ImportError("paho-mqtt not installed. Install: pip install paho-mqtt")

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"mqtt_service_{int(time.time())}"
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.keepalive = keepalive

        # Connection state
        self.status = MQTTStatus.DISCONNECTED
        self.connected = False

        # Subscriptions
        self.subscriptions: Dict[str, Dict] = {}  # topic -> {qos, callback}

        # Message buffer (for when disconnected)
        self.message_buffer: List[Dict] = []
        self.max_buffer_size = 1000

        # Statistics
        self.stats = {
            "messages_published": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "connection_count": 0,
            "disconnection_count": 0
        }

        # Create MQTT client
        self.client = mqtt.Client(client_id=self.client_id)

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe

        # Authentication
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # TLS/SSL
        if self.use_tls:
            self.client.tls_set()

        logger.info(f"MQTT Service initialized (broker={broker_host}:{broker_port})")

    # ========================================================================
    # Connection Management
    # ========================================================================

    def connect(self) -> bool:
        """
        Connect to MQTT broker

        Returns:
            Success status
        """
        if self.connected:
            logger.warning("Already connected to MQTT broker")
            return True

        try:
            self.status = MQTTStatus.CONNECTING
            logger.info(f"Connecting to MQTT broker: {self.broker_host}:{self.broker_port}")

            self.client.connect(
                self.broker_host,
                self.broker_port,
                self.keepalive
            )

            # Start network loop in background thread
            self.client.loop_start()

            # Wait for connection (up to 5 seconds)
            timeout = 5.0
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.connected:
                logger.info("Connected to MQTT broker")
                return True
            else:
                logger.error("Connection timeout")
                self.status = MQTTStatus.ERROR
                return False

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.status = MQTTStatus.ERROR
            return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if not self.connected:
            return

        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.status = MQTTStatus.DISCONNECTED
            logger.info("Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connected

    # ========================================================================
    # Publishing
    # ========================================================================

    def publish(
        self,
        topic: str,
        payload: Any,
        qos: QoS = QoS.AT_MOST_ONCE,
        retain: bool = False
    ) -> bool:
        """
        Publish message to topic

        Args:
            topic: Topic name
            payload: Message payload (dict, str, bytes)
            qos: Quality of Service level
            retain: Retain message flag

        Returns:
            Success status
        """
        # Convert payload to JSON if dict
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        elif not isinstance(payload, (str, bytes)):
            payload = str(payload)

        # Buffer message if disconnected
        if not self.connected:
            logger.warning(f"Not connected, buffering message to {topic}")
            if len(self.message_buffer) < self.max_buffer_size:
                self.message_buffer.append({
                    "topic": topic,
                    "payload": payload,
                    "qos": qos,
                    "retain": retain,
                    "timestamp": datetime.now()
                })
            return False

        try:
            result = self.client.publish(
                topic,
                payload,
                qos=int(qos),
                retain=retain
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.stats["messages_published"] += 1
                if isinstance(payload, str):
                    self.stats["bytes_sent"] += len(payload.encode())
                elif isinstance(payload, bytes):
                    self.stats["bytes_sent"] += len(payload)
                return True
            else:
                logger.error(f"Publish failed: {mqtt.error_string(result.rc)}")
                return False

        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False

    def publish_sensor_data(
        self,
        sensor_id: str,
        data: Dict,
        qos: QoS = QoS.AT_LEAST_ONCE
    ) -> bool:
        """
        Publish sensor data to standardized topic

        Args:
            sensor_id: Sensor identifier
            data: Sensor data dictionary
            qos: Quality of Service level

        Returns:
            Success status
        """
        topic = f"sensors/{sensor_id}/data"

        # Add metadata
        message = {
            "sensor_id": sensor_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        return self.publish(topic, message, qos=qos)

    def _flush_buffer(self):
        """Flush buffered messages after reconnection"""
        if not self.message_buffer:
            return

        logger.info(f"Flushing {len(self.message_buffer)} buffered messages")

        messages_sent = 0
        for msg in self.message_buffer[:]:
            success = self.publish(
                msg["topic"],
                msg["payload"],
                qos=msg["qos"],
                retain=msg["retain"]
            )
            if success:
                self.message_buffer.remove(msg)
                messages_sent += 1

        logger.info(f"Flushed {messages_sent} messages")

    # ========================================================================
    # Subscribing
    # ========================================================================

    def subscribe(
        self,
        topic: str,
        callback: Callable,
        qos: QoS = QoS.AT_MOST_ONCE
    ) -> bool:
        """
        Subscribe to topic

        Args:
            topic: Topic name (supports wildcards: +, #)
            callback: Function to call on message (topic, payload)
            qos: Quality of Service level

        Returns:
            Success status
        """
        # Store subscription
        self.subscriptions[topic] = {
            "qos": qos,
            "callback": callback
        }

        if not self.connected:
            logger.warning(f"Not connected, subscription to {topic} pending")
            return False

        try:
            result, mid = self.client.subscribe(topic, qos=int(qos))

            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to {topic} (QoS {qos})")
                return True
            else:
                logger.error(f"Subscribe failed: {mqtt.error_string(result)}")
                return False

        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from topic

        Args:
            topic: Topic name

        Returns:
            Success status
        """
        if topic in self.subscriptions:
            del self.subscriptions[topic]

        if not self.connected:
            return False

        try:
            result, mid = self.client.unsubscribe(topic)

            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Unsubscribed from {topic}")
                return True
            else:
                logger.error(f"Unsubscribe failed: {mqtt.error_string(result)}")
                return False

        except Exception as e:
            logger.error(f"Failed to unsubscribe from {topic}: {e}")
            return False

    def subscribe_sensor_pattern(
        self,
        sensor_pattern: str,
        callback: Callable,
        qos: QoS = QoS.AT_LEAST_ONCE
    ) -> bool:
        """
        Subscribe to sensor data pattern

        Args:
            sensor_pattern: Sensor ID or pattern (e.g., "temp_*", "+", "#")
            callback: Function to call on message
            qos: Quality of Service level

        Returns:
            Success status
        """
        topic = f"sensors/{sensor_pattern}/data"
        return self.subscribe(topic, callback, qos)

    # ========================================================================
    # Callbacks
    # ========================================================================

    def _on_connect(self, client, userdata, flags, rc):
        """Callback on connection"""
        if rc == 0:
            self.connected = True
            self.status = MQTTStatus.CONNECTED
            self.stats["connection_count"] += 1
            logger.info("MQTT connected")

            # Resubscribe to topics
            for topic, sub_info in self.subscriptions.items():
                self.client.subscribe(topic, qos=int(sub_info["qos"]))

            # Flush buffered messages
            self._flush_buffer()

        else:
            self.status = MQTTStatus.ERROR
            logger.error(f"MQTT connection failed: {mqtt.connack_string(rc)}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback on disconnection"""
        self.connected = False
        self.status = MQTTStatus.DISCONNECTED
        self.stats["disconnection_count"] += 1

        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {mqtt.error_string(rc)}")
            # Auto-reconnect handled by paho-mqtt
        else:
            logger.info("MQTT disconnected")

    def _on_message(self, client, userdata, msg):
        """Callback on message received"""
        try:
            # Decode payload
            payload = msg.payload.decode('utf-8')

            # Try to parse as JSON
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                pass  # Keep as string

            self.stats["messages_received"] += 1
            self.stats["bytes_received"] += len(msg.payload)

            # Find matching subscription callback
            topic = msg.topic
            for sub_topic, sub_info in self.subscriptions.items():
                if mqtt.topic_matches_sub(sub_topic, topic):
                    callback = sub_info["callback"]
                    try:
                        callback(topic, payload)
                    except Exception as e:
                        logger.error(f"Callback error for {topic}: {e}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _on_publish(self, client, userdata, mid):
        """Callback on message published"""
        pass  # Can track message IDs if needed

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback on subscription"""
        logger.debug(f"Subscription confirmed (mid={mid}, qos={granted_qos})")

    # ========================================================================
    # Utilities
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get MQTT statistics"""
        return {
            **self.stats,
            "status": self.status,
            "connected": self.connected,
            "subscriptions": len(self.subscriptions),
            "buffered_messages": len(self.message_buffer)
        }

    def list_subscriptions(self) -> List[str]:
        """List active subscriptions"""
        return list(self.subscriptions.keys())


# Global singleton
_mqtt_service: Optional[MQTTService] = None


def get_mqtt_service(
    broker_host: str = "localhost",
    broker_port: int = 1883,
    **kwargs
) -> MQTTService:
    """Get or create MQTT Service singleton"""
    global _mqtt_service
    if _mqtt_service is None:
        _mqtt_service = MQTTService(
            broker_host=broker_host,
            broker_port=broker_port,
            **kwargs
        )
    return _mqtt_service
