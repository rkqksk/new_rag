"""
Push Notification Service
FCM (Firebase Cloud Messaging) and APNS integration
Version: v8.4.0
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Push notification service for iOS and Android"""

    def __init__(self, fcm_credentials_path: Optional[str] = None):
        """
        Initialize push notification service

        Args:
            fcm_credentials_path: Path to Firebase credentials JSON
        """
        self.fcm_credentials_path = fcm_credentials_path
        self.app = None
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                if self.fcm_credentials_path:
                    cred = credentials.Certificate(self.fcm_credentials_path)
                    self.app = firebase_admin.initialize_app(cred)
                    logger.info('Firebase Admin SDK initialized')
                else:
                    logger.warning('Firebase credentials not provided, FCM disabled')
        except Exception as e:
            logger.error(f'Firebase initialization failed: {e}')

    async def send_notification(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
        click_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple devices

        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Custom data payload
            image_url: Optional image URL
            click_action: URL to open on click

        Returns:
            {
                'success_count': int,
                'failure_count': int,
                'failed_tokens': List[str]
            }
        """
        if not self.app:
            logger.warning('Firebase not initialized')
            return {'success_count': 0, 'failure_count': len(tokens), 'failed_tokens': tokens}

        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url,
            )

            # Build message
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=tokens,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        click_action=click_action,
                        icon='notification_icon',
                        color='#667eea',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                            category=click_action,
                        ),
                    ),
                ),
            )

            # Send multicast message
            response = messaging.send_multicast(message)

            # Collect failed tokens
            failed_tokens = []
            if response.failure_count > 0:
                for idx, result in enumerate(response.responses):
                    if not result.success:
                        failed_tokens.append(tokens[idx])
                        logger.warning(f'Failed to send to {tokens[idx]}: {result.exception}')

            logger.info(f'Sent notifications: {response.success_count} success, {response.failure_count} failed')

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'failed_tokens': failed_tokens,
            }

        except Exception as e:
            logger.error(f'Send notification failed: {e}')
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'failed_tokens': tokens,
                'error': str(e),
            }

    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send notification to topic subscribers

        Args:
            topic: Topic name (e.g., 'all_users', 'new_products')
            title: Notification title
            body: Notification body
            data: Custom data payload

        Returns:
            Success status
        """
        if not self.app:
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                topic=topic,
            )

            response = messaging.send(message)
            logger.info(f'Sent to topic {topic}: {response}')
            return True

        except Exception as e:
            logger.error(f'Send to topic failed: {e}')
            return False

    async def subscribe_to_topic(self, tokens: List[str], topic: str) -> Dict[str, int]:
        """
        Subscribe devices to topic

        Args:
            tokens: Device tokens
            topic: Topic name

        Returns:
            {'success': int, 'errors': int}
        """
        if not self.app:
            return {'success': 0, 'errors': len(tokens)}

        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            logger.info(f'Subscribed to {topic}: {response.success_count} success, {response.failure_count} errors')
            return {'success': response.success_count, 'errors': response.failure_count}

        except Exception as e:
            logger.error(f'Subscribe to topic failed: {e}')
            return {'success': 0, 'errors': len(tokens)}

    async def unsubscribe_from_topic(self, tokens: List[str], topic: str) -> Dict[str, int]:
        """
        Unsubscribe devices from topic

        Args:
            tokens: Device tokens
            topic: Topic name

        Returns:
            {'success': int, 'errors': int}
        """
        if not self.app:
            return {'success': 0, 'errors': len(tokens)}

        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            return {'success': response.success_count, 'errors': response.failure_count}

        except Exception as e:
            logger.error(f'Unsubscribe from topic failed: {e}')
            return {'success': 0, 'errors': len(tokens)}

    async def send_work_order_notification(
        self,
        tokens: List[str],
        wo_number: str,
        product_name: str,
        quantity: int,
        due_date: str
    ) -> Dict[str, Any]:
        """
        Send work order assignment notification

        Args:
            tokens: Worker device tokens
            wo_number: Work order number
            product_name: Product name
            quantity: Quantity to produce
            due_date: Due date

        Returns:
            Send result
        """
        return await self.send_notification(
            tokens=tokens,
            title='새 작업 지시',
            body=f'{product_name} {quantity}개 - {due_date}까지',
            data={
                'type': 'work_order',
                'wo_number': wo_number,
                'product_name': product_name,
                'quantity': str(quantity),
                'due_date': due_date,
            },
            click_action='/work-orders',
        )

    async def send_quality_alert(
        self,
        tokens: List[str],
        product_name: str,
        defect_type: str,
        severity: str
    ) -> Dict[str, Any]:
        """
        Send quality issue alert

        Args:
            tokens: QC team device tokens
            product_name: Product name
            defect_type: Type of defect
            severity: Severity level

        Returns:
            Send result
        """
        severity_emoji = '🔴' if severity == 'high' else '🟡' if severity == 'medium' else '🟢'

        return await self.send_notification(
            tokens=tokens,
            title=f'{severity_emoji} 품질 이슈 발생',
            body=f'{product_name} - {defect_type}',
            data={
                'type': 'quality_alert',
                'product_name': product_name,
                'defect_type': defect_type,
                'severity': severity,
            },
            click_action='/quality-inspection',
        )

    async def send_inventory_alert(
        self,
        tokens: List[str],
        product_name: str,
        current_stock: int,
        threshold: int
    ) -> Dict[str, Any]:
        """
        Send low stock alert

        Args:
            tokens: Inventory manager tokens
            product_name: Product name
            current_stock: Current stock level
            threshold: Minimum threshold

        Returns:
            Send result
        """
        return await self.send_notification(
            tokens=tokens,
            title='재고 부족 알림',
            body=f'{product_name} - 현재 {current_stock}개 (최소 {threshold}개)',
            data={
                'type': 'inventory_alert',
                'product_name': product_name,
                'current_stock': str(current_stock),
                'threshold': str(threshold),
            },
            click_action='/inventory',
        )


# Singleton instance
_push_service = None


def get_push_notification_service(fcm_credentials_path: Optional[str] = None) -> PushNotificationService:
    """Get push notification service singleton"""
    global _push_service
    if _push_service is None:
        _push_service = PushNotificationService(fcm_credentials_path)
    return _push_service
