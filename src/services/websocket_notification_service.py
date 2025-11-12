"""
WebSocket Notification Service
Real-time notifications via WebSocket/Socket.IO
Version: v8.5.0
"""

import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import asyncio
import json
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification types"""
    SEARCH_RESULT = 'search_result'
    DATA_UPDATE = 'data_update'
    WORK_ORDER = 'work_order'
    QUALITY_ALERT = 'quality_alert'
    INVENTORY_ALERT = 'inventory_alert'
    SYSTEM_MESSAGE = 'system_message'
    USER_MESSAGE = 'user_message'
    ERROR = 'error'


class NotificationPriority(str, Enum):
    """Notification priority"""
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'


class WebSocketNotificationService:
    """WebSocket-based real-time notification service"""

    def __init__(self):
        """Initialize WebSocket notification service"""
        # Active connections by user
        self.connections: Dict[str, Set[Any]] = {}

        # Room subscriptions (topic-based)
        self.rooms: Dict[str, Set[str]] = {}

        # Message queue for offline users
        self.message_queue: Dict[str, List[Dict[str, Any]]] = {}

        # Max queued messages per user
        self.max_queue_size = 100

        logger.info("WebSocket notification service initialized")

    async def connect(self, user_id: str, websocket: Any):
        """
        Register new WebSocket connection

        Args:
            user_id: User ID
            websocket: WebSocket connection object
        """
        if user_id not in self.connections:
            self.connections[user_id] = set()

        self.connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected (total: {len(self.connections[user_id])})")

        # Send queued messages
        await self._send_queued_messages(user_id, websocket)

    async def disconnect(self, user_id: str, websocket: Any):
        """
        Unregister WebSocket connection

        Args:
            user_id: User ID
            websocket: WebSocket connection object
        """
        if user_id in self.connections:
            self.connections[user_id].discard(websocket)

            if not self.connections[user_id]:
                del self.connections[user_id]
                logger.info(f"User {user_id} disconnected (all sessions closed)")
            else:
                logger.info(f"User {user_id} session closed (remaining: {len(self.connections[user_id])})")

    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        title: Optional[str] = None,
        message: Optional[str] = None
    ) -> bool:
        """
        Send notification to specific user

        Args:
            user_id: Target user ID
            notification_type: Notification type
            data: Notification data
            priority: Notification priority
            title: Optional title
            message: Optional message

        Returns:
            True if sent, False if queued
        """
        notification = {
            'type': notification_type,
            'priority': priority,
            'title': title,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat(),
        }

        # Send to active connections
        if user_id in self.connections and self.connections[user_id]:
            await self._send_to_user(user_id, notification)
            return True
        else:
            # Queue for offline user
            self._queue_message(user_id, notification)
            logger.debug(f"Queued notification for offline user: {user_id}")
            return False

    async def broadcast(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        title: Optional[str] = None,
        message: Optional[str] = None,
        exclude_users: Optional[List[str]] = None
    ):
        """
        Broadcast notification to all connected users

        Args:
            notification_type: Notification type
            data: Notification data
            priority: Notification priority
            title: Optional title
            message: Optional message
            exclude_users: Optional list of user IDs to exclude
        """
        notification = {
            'type': notification_type,
            'priority': priority,
            'title': title,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat(),
        }

        exclude = set(exclude_users or [])

        for user_id in list(self.connections.keys()):
            if user_id not in exclude:
                await self._send_to_user(user_id, notification)

        logger.info(f"Broadcast notification to {len(self.connections)} users")

    async def send_to_room(
        self,
        room: str,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        title: Optional[str] = None,
        message: Optional[str] = None
    ):
        """
        Send notification to room subscribers

        Args:
            room: Room name
            notification_type: Notification type
            data: Notification data
            priority: Notification priority
            title: Optional title
            message: Optional message
        """
        if room not in self.rooms:
            logger.warning(f"Room {room} has no subscribers")
            return

        notification = {
            'type': notification_type,
            'priority': priority,
            'title': title,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat(),
        }

        for user_id in self.rooms[room]:
            if user_id in self.connections:
                await self._send_to_user(user_id, notification)

        logger.info(f"Sent notification to room {room} ({len(self.rooms[room])} users)")

    async def join_room(self, user_id: str, room: str):
        """
        Subscribe user to room

        Args:
            user_id: User ID
            room: Room name
        """
        if room not in self.rooms:
            self.rooms[room] = set()

        self.rooms[room].add(user_id)
        logger.info(f"User {user_id} joined room {room}")

    async def leave_room(self, user_id: str, room: str):
        """
        Unsubscribe user from room

        Args:
            user_id: User ID
            room: Room name
        """
        if room in self.rooms:
            self.rooms[room].discard(user_id)

            if not self.rooms[room]:
                del self.rooms[room]

            logger.info(f"User {user_id} left room {room}")

    async def send_search_notification(
        self,
        user_id: str,
        query: str,
        results: List[Dict[str, Any]],
        total_results: int
    ):
        """
        Send search result notification

        Args:
            user_id: User ID
            query: Search query
            results: Search results
            total_results: Total result count
        """
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.SEARCH_RESULT,
            data={
                'query': query,
                'results': results,
                'total': total_results,
            },
            priority=NotificationPriority.NORMAL,
            title='검색 완료',
            message=f'"{query}" 검색 결과 {total_results}개 발견'
        )

    async def send_work_order_notification(
        self,
        user_id: str,
        wo_number: str,
        product_name: str,
        quantity: int,
        due_date: str,
        priority: str = 'normal'
    ):
        """
        Send work order notification

        Args:
            user_id: User ID
            wo_number: Work order number
            product_name: Product name
            quantity: Quantity
            due_date: Due date
            priority: Work order priority
        """
        notification_priority = (
            NotificationPriority.URGENT if priority == 'urgent'
            else NotificationPriority.HIGH if priority == 'high'
            else NotificationPriority.NORMAL
        )

        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.WORK_ORDER,
            data={
                'wo_number': wo_number,
                'product_name': product_name,
                'quantity': quantity,
                'due_date': due_date,
                'priority': priority,
            },
            priority=notification_priority,
            title='새 작업 지시',
            message=f'{product_name} {quantity}개 - {due_date}까지'
        )

    async def send_quality_alert(
        self,
        user_ids: List[str],
        product_name: str,
        defect_type: str,
        severity: str,
        location: Optional[str] = None
    ):
        """
        Send quality alert notification

        Args:
            user_ids: List of user IDs
            product_name: Product name
            defect_type: Defect type
            severity: Severity level
            location: Optional location
        """
        severity_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴',
        }.get(severity, '⚠️')

        notification_priority = (
            NotificationPriority.URGENT if severity == 'critical'
            else NotificationPriority.HIGH if severity == 'high'
            else NotificationPriority.NORMAL
        )

        for user_id in user_ids:
            await self.send_notification(
                user_id=user_id,
                notification_type=NotificationType.QUALITY_ALERT,
                data={
                    'product_name': product_name,
                    'defect_type': defect_type,
                    'severity': severity,
                    'location': location,
                },
                priority=notification_priority,
                title=f'{severity_emoji} 품질 이슈 발생',
                message=f'{product_name} - {defect_type}'
            )

    async def send_inventory_alert(
        self,
        user_ids: List[str],
        product_name: str,
        current_stock: int,
        threshold: int,
        reorder_quantity: Optional[int] = None
    ):
        """
        Send inventory alert notification

        Args:
            user_ids: List of user IDs
            product_name: Product name
            current_stock: Current stock level
            threshold: Minimum threshold
            reorder_quantity: Optional reorder quantity
        """
        for user_id in user_ids:
            await self.send_notification(
                user_id=user_id,
                notification_type=NotificationType.INVENTORY_ALERT,
                data={
                    'product_name': product_name,
                    'current_stock': current_stock,
                    'threshold': threshold,
                    'reorder_quantity': reorder_quantity,
                },
                priority=NotificationPriority.HIGH,
                title='재고 부족 알림',
                message=f'{product_name} - 현재 {current_stock}개 (최소 {threshold}개)'
            )

    async def send_system_message(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        target_users: Optional[List[str]] = None
    ):
        """
        Send system message

        Args:
            message: System message
            data: Optional data
            priority: Message priority
            target_users: Optional target users (None = broadcast)
        """
        if target_users:
            for user_id in target_users:
                await self.send_notification(
                    user_id=user_id,
                    notification_type=NotificationType.SYSTEM_MESSAGE,
                    data=data or {},
                    priority=priority,
                    title='시스템 메시지',
                    message=message
                )
        else:
            await self.broadcast(
                notification_type=NotificationType.SYSTEM_MESSAGE,
                data=data or {},
                priority=priority,
                title='시스템 메시지',
                message=message
            )

    async def _send_to_user(self, user_id: str, notification: Dict[str, Any]):
        """Send notification to all user's connections"""
        if user_id not in self.connections:
            return

        # Send to all user's active connections
        disconnected = []
        for websocket in self.connections[user_id]:
            try:
                await websocket.send_json(notification)
            except Exception as e:
                logger.error(f"Failed to send to {user_id}: {e}")
                disconnected.append(websocket)

        # Remove disconnected websockets
        for websocket in disconnected:
            self.connections[user_id].discard(websocket)

    def _queue_message(self, user_id: str, notification: Dict[str, Any]):
        """Queue message for offline user"""
        if user_id not in self.message_queue:
            self.message_queue[user_id] = []

        # Add to queue
        self.message_queue[user_id].append(notification)

        # Trim queue if too large
        if len(self.message_queue[user_id]) > self.max_queue_size:
            self.message_queue[user_id] = self.message_queue[user_id][-self.max_queue_size:]

    async def _send_queued_messages(self, user_id: str, websocket: Any):
        """Send queued messages to newly connected user"""
        if user_id not in self.message_queue:
            return

        queued = self.message_queue[user_id]
        if not queued:
            return

        logger.info(f"Sending {len(queued)} queued messages to {user_id}")

        for notification in queued:
            try:
                await websocket.send_json(notification)
            except Exception as e:
                logger.error(f"Failed to send queued message: {e}")
                break

        # Clear queue
        del self.message_queue[user_id]

    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.connections.keys())

    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """
        Get connection count

        Args:
            user_id: Optional user ID (None = total count)

        Returns:
            Connection count
        """
        if user_id:
            return len(self.connections.get(user_id, set()))
        else:
            return sum(len(conns) for conns in self.connections.values())

    def get_room_subscribers(self, room: str) -> List[str]:
        """Get list of room subscribers"""
        return list(self.rooms.get(room, set()))


# Singleton instance
_websocket_service = None


def get_websocket_notification_service() -> WebSocketNotificationService:
    """Get WebSocket notification service singleton"""
    global _websocket_service
    if _websocket_service is None:
        _websocket_service = WebSocketNotificationService()
    return _websocket_service
