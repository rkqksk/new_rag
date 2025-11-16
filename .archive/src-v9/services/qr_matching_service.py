"""
QR Code Product Matching Service
Matches QR codes to products in the database
Version: v8.3.0
"""

import re
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QRMatcher:
    """QR Code to Product Matcher"""

    # QR Code patterns
    QR_PATTERNS = {
        'product_id': r'^PROD:(\w+)$',
        'product_code': r'^CODE:([A-Z0-9-]+)$',
        'work_order': r'^WO:([A-Z0-9-]+)$',
        'location': r'^LOC:([A-Z0-9-]+)$',
        'url': r'^https?://',
        'json': r'^\{.*\}$',
    }

    def __init__(self, db_session=None, qdrant_client=None):
        """
        Initialize QR Matcher

        Args:
            db_session: PostgreSQL session
            qdrant_client: Qdrant client for product search
        """
        self.db = db_session
        self.qdrant = qdrant_client

    async def match_qr_code(self, qr_data: str) -> Dict[str, Any]:
        """
        Match QR code to product/work order/location

        Args:
            qr_data: Raw QR code string

        Returns:
            Match result with product details
        """
        try:
            # Detect QR code type
            qr_type = self._detect_qr_type(qr_data)

            if qr_type == 'product_id':
                return await self._match_product_by_id(qr_data)
            elif qr_type == 'product_code':
                return await self._match_product_by_code(qr_data)
            elif qr_type == 'work_order':
                return await self._match_work_order(qr_data)
            elif qr_type == 'location':
                return await self._match_location(qr_data)
            elif qr_type == 'url':
                return await self._match_url(qr_data)
            elif qr_type == 'json':
                return await self._match_json(qr_data)
            else:
                return await self._match_generic(qr_data)

        except Exception as e:
            logger.error(f"QR matching error: {e}")
            return {
                'matched': False,
                'type': 'error',
                'error': str(e),
                'raw_data': qr_data
            }

    def _detect_qr_type(self, qr_data: str) -> str:
        """Detect QR code type from pattern"""
        for qr_type, pattern in self.QR_PATTERNS.items():
            if re.match(pattern, qr_data):
                return qr_type
        return 'generic'

    async def _match_product_by_id(self, qr_data: str) -> Dict[str, Any]:
        """Match by product ID (PROD:xxx)"""
        match = re.match(self.QR_PATTERNS['product_id'], qr_data)
        if not match:
            return {'matched': False, 'type': 'product_id'}

        product_id = match.group(1)

        # Query database
        if self.db:
            product = await self._query_product_by_id(product_id)
            if product:
                return {
                    'matched': True,
                    'type': 'product',
                    'product_id': product_id,
                    'product': product,
                    'source': 'database'
                }

        # Fallback to Qdrant
        if self.qdrant:
            results = await self._search_qdrant(f"id:{product_id}")
            if results:
                return {
                    'matched': True,
                    'type': 'product',
                    'product_id': product_id,
                    'product': results[0],
                    'source': 'qdrant'
                }

        return {
            'matched': False,
            'type': 'product',
            'product_id': product_id,
            'error': 'Product not found'
        }

    async def _match_product_by_code(self, qr_data: str) -> Dict[str, Any]:
        """Match by product code (CODE:xxx)"""
        match = re.match(self.QR_PATTERNS['product_code'], qr_data)
        if not match:
            return {'matched': False, 'type': 'product_code'}

        product_code = match.group(1)

        # Query database
        if self.db:
            product = await self._query_product_by_code(product_code)
            if product:
                return {
                    'matched': True,
                    'type': 'product',
                    'product_code': product_code,
                    'product': product,
                    'source': 'database'
                }

        return {
            'matched': False,
            'type': 'product',
            'product_code': product_code,
            'error': 'Product not found'
        }

    async def _match_work_order(self, qr_data: str) -> Dict[str, Any]:
        """Match work order (WO:xxx)"""
        match = re.match(self.QR_PATTERNS['work_order'], qr_data)
        if not match:
            return {'matched': False, 'type': 'work_order'}

        wo_id = match.group(1)

        if self.db:
            work_order = await self._query_work_order(wo_id)
            if work_order:
                return {
                    'matched': True,
                    'type': 'work_order',
                    'wo_id': wo_id,
                    'work_order': work_order,
                    'source': 'database'
                }

        return {
            'matched': False,
            'type': 'work_order',
            'wo_id': wo_id,
            'error': 'Work order not found'
        }

    async def _match_location(self, qr_data: str) -> Dict[str, Any]:
        """Match location (LOC:xxx)"""
        match = re.match(self.QR_PATTERNS['location'], qr_data)
        if not match:
            return {'matched': False, 'type': 'location'}

        location_id = match.group(1)

        return {
            'matched': True,
            'type': 'location',
            'location_id': location_id,
            'location': {
                'id': location_id,
                'name': f'Location {location_id}',
                # TODO: Get actual location data
            }
        }

    async def _match_url(self, qr_data: str) -> Dict[str, Any]:
        """Match URL (http://... or https://...)"""
        # Extract product info from URL
        if 'product' in qr_data or 'item' in qr_data:
            # Try to extract product ID from URL
            product_id_match = re.search(r'/product/(\w+)', qr_data)
            if product_id_match:
                product_id = product_id_match.group(1)
                return await self._match_product_by_id(f'PROD:{product_id}')

        return {
            'matched': True,
            'type': 'url',
            'url': qr_data,
            'action': 'open_browser'
        }

    async def _match_json(self, qr_data: str) -> Dict[str, Any]:
        """Match JSON data"""
        import json
        try:
            data = json.loads(qr_data)

            if 'product_id' in data:
                return await self._match_product_by_id(f"PROD:{data['product_id']}")
            elif 'product_code' in data:
                return await self._match_product_by_code(f"CODE:{data['product_code']}")
            elif 'wo_id' in data:
                return await self._match_work_order(f"WO:{data['wo_id']}")

            return {
                'matched': True,
                'type': 'json',
                'data': data
            }
        except json.JSONDecodeError:
            return {'matched': False, 'type': 'json', 'error': 'Invalid JSON'}

    async def _match_generic(self, qr_data: str) -> Dict[str, Any]:
        """Match generic QR code (text search)"""
        # Try text search in Qdrant
        if self.qdrant:
            results = await self._search_qdrant(qr_data, top_k=5)
            if results:
                return {
                    'matched': True,
                    'type': 'generic',
                    'query': qr_data,
                    'results': results,
                    'source': 'search'
                }

        return {
            'matched': False,
            'type': 'generic',
            'raw_data': qr_data,
            'suggestion': 'Try scanning a valid product QR code'
        }

    async def _query_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Query product from PostgreSQL by ID"""
        if not self.db:
            return None

        try:
            # TODO: Actual SQL query
            # result = await self.db.execute(
            #     "SELECT * FROM products WHERE id = :id",
            #     {"id": product_id}
            # )
            # return result.fetchone()
            return None
        except Exception as e:
            logger.error(f"DB query error: {e}")
            return None

    async def _query_product_by_code(self, product_code: str) -> Optional[Dict]:
        """Query product from PostgreSQL by code"""
        if not self.db:
            return None

        try:
            # TODO: Actual SQL query
            return None
        except Exception as e:
            logger.error(f"DB query error: {e}")
            return None

    async def _query_work_order(self, wo_id: str) -> Optional[Dict]:
        """Query work order from database"""
        if not self.db:
            return None

        try:
            # TODO: Actual SQL query
            return None
        except Exception as e:
            logger.error(f"DB query error: {e}")
            return None

    async def _search_qdrant(self, query: str, top_k: int = 1) -> List[Dict]:
        """Search Qdrant for products"""
        if not self.qdrant:
            return []

        try:
            # TODO: Actual Qdrant search
            return []
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []

    def generate_qr_code(self, data_type: str, data_id: str) -> str:
        """
        Generate QR code string for product/work order

        Args:
            data_type: 'product', 'work_order', 'location'
            data_id: ID of the item

        Returns:
            QR code string
        """
        if data_type == 'product':
            return f'PROD:{data_id}'
        elif data_type == 'work_order':
            return f'WO:{data_id}'
        elif data_type == 'location':
            return f'LOC:{data_id}'
        else:
            return data_id

    def generate_qr_hash(self, qr_data: str) -> str:
        """Generate unique hash for QR code tracking"""
        return hashlib.sha256(qr_data.encode()).hexdigest()[:16]


# Singleton instance
_qr_matcher = None


def get_qr_matcher(db_session=None, qdrant_client=None) -> QRMatcher:
    """Get QR matcher singleton"""
    global _qr_matcher
    if _qr_matcher is None:
        _qr_matcher = QRMatcher(db_session, qdrant_client)
    return _qr_matcher
