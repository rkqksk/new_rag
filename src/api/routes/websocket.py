"""
WebSocket API Routes
Real-time notifications and messaging
Version: v8.5.0
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import Dict, Any, Optional, List
import logging
import json

from src.auth.dependencies import get_current_user
from src.auth.models import CurrentUser
from src.auth.jwt_utils import JWTUtils
from src.services.websocket_notification_service import (
    get_websocket_notification_service,
    NotificationType,
    NotificationPriority
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class BroadcastRequest(BaseModel):
    """Broadcast notification request"""
    notification_type: str
    data: Dict[str, Any]
    priority: str = "normal"
    title: Optional[str] = None
    message: Optional[str] = None
    exclude_users: Optional[List[str]] = None


class RoomBroadcastRequest(BaseModel):
    """Room broadcast request"""
    room: str
    notification_type: str
    data: Dict[str, Any]
    priority: str = "normal"
    title: Optional[str] = None
    message: Optional[str] = None


class SendNotificationRequest(BaseModel):
    """Send notification to specific user"""
    user_id: str
    notification_type: str
    data: Dict[str, Any]
    priority: str = "normal"
    title: Optional[str] = None
    message: Optional[str] = None


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT access token")
):
    """
    WebSocket endpoint for real-time notifications

    Args:
        websocket: WebSocket connection
        token: JWT access token for authentication

    Usage:
        ws = new WebSocket('ws://localhost:8001/api/v1/ws/notifications?token=YOUR_TOKEN')
        ws.onmessage = (event) => {
            const notification = JSON.parse(event.data)
            console.log(notification)
        }
    """
    ws_service = get_websocket_notification_service()

    # Authenticate user
    user_id = "anonymous"
    if token:
        try:
            payload = JWTUtils.verify_token(token, token_type="access")
            user_id = payload.get("sub")
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return

    # Accept connection
    await websocket.accept()

    # Register connection
    await ws_service.connect(user_id, websocket)

    try:
        logger.info(f"WebSocket connected: user={user_id}")

        # Send welcome message
        await websocket.send_json({
            "type": NotificationType.SYSTEM_MESSAGE,
            "priority": NotificationPriority.LOW,
            "message": "Connected to notification service",
            "data": {"user_id": user_id}
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()

                # Parse message
                message = json.loads(data)

                # Handle commands
                command = message.get("command")

                if command == "ping":
                    # Respond with pong
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    })

                elif command == "join_room":
                    # Join room
                    room = message.get("room")
                    if room:
                        await ws_service.join_room(user_id, room)
                        await websocket.send_json({
                            "type": "room_joined",
                            "room": room
                        })

                elif command == "leave_room":
                    # Leave room
                    room = message.get("room")
                    if room:
                        await ws_service.leave_room(user_id, room)
                        await websocket.send_json({
                            "type": "room_left",
                            "room": room
                        })

                else:
                    # Unknown command
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown command: {command}"
                    })

            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        # Unregister connection
        await ws_service.disconnect(user_id, websocket)


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send notification to specific user

    Requires: Authenticated user

    Args:
        request: Notification data

    Returns:
        Success status
    """
    try:
        ws_service = get_websocket_notification_service()

        # Validate notification type
        notification_type = NotificationType(request.notification_type)
        priority = NotificationPriority(request.priority)

        # Send notification
        sent = await ws_service.send_notification(
            user_id=request.user_id,
            notification_type=notification_type,
            data=request.data,
            priority=priority,
            title=request.title,
            message=request.message
        )

        return {
            "success": True,
            "sent": sent,
            "user_id": request.user_id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid notification type or priority: {e}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@router.post("/broadcast")
async def broadcast_notification(
    request: BroadcastRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Broadcast notification to all connected users

    Requires: Authenticated user

    Args:
        request: Broadcast notification data

    Returns:
        Success status with recipient count
    """
    try:
        ws_service = get_websocket_notification_service()

        # Validate notification type
        notification_type = NotificationType(request.notification_type)
        priority = NotificationPriority(request.priority)

        # Broadcast
        await ws_service.broadcast(
            notification_type=notification_type,
            data=request.data,
            priority=priority,
            title=request.title,
            message=request.message,
            exclude_users=request.exclude_users
        )

        # Get connected users count
        recipient_count = ws_service.get_connection_count()

        return {
            "success": True,
            "recipients": recipient_count
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid notification type or priority: {e}")
    except Exception as e:
        logger.error(f"Failed to broadcast notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to broadcast: {str(e)}")


@router.post("/room/broadcast")
async def broadcast_to_room(
    request: RoomBroadcastRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Broadcast notification to room subscribers

    Requires: Authenticated user

    Args:
        request: Room broadcast data

    Returns:
        Success status with subscriber count
    """
    try:
        ws_service = get_websocket_notification_service()

        # Validate notification type
        notification_type = NotificationType(request.notification_type)
        priority = NotificationPriority(request.priority)

        # Broadcast to room
        await ws_service.send_to_room(
            room=request.room,
            notification_type=notification_type,
            data=request.data,
            priority=priority,
            title=request.title,
            message=request.message
        )

        # Get room subscribers
        subscribers = ws_service.get_room_subscribers(request.room)

        return {
            "success": True,
            "room": request.room,
            "subscribers": len(subscribers)
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid notification type or priority: {e}")
    except Exception as e:
        logger.error(f"Failed to broadcast to room: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to broadcast to room: {str(e)}")


@router.get("/status")
async def get_websocket_status(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get WebSocket service status

    Requires: Authenticated user

    Returns:
        Connection statistics
    """
    try:
        ws_service = get_websocket_notification_service()

        connected_users = ws_service.get_connected_users()
        total_connections = ws_service.get_connection_count()

        return {
            "success": True,
            "data": {
                "connected_users": len(connected_users),
                "total_connections": total_connections,
                "users": connected_users
            }
        }

    except Exception as e:
        logger.error(f"Failed to get WebSocket status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
