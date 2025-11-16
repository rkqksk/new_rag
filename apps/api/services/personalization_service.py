"""PersonalizationService - Complete Integration"""

import logging
from typing import Any, Dict, List

from apps.api.core.recommendation import UserProfile
from apps.api.core.recommendation.advanced_personalization_service import AdvancedPersonalizationService

logger = logging.getLogger(__name__)


class PersonalizationService:
    """
    Personalization service wrapper

    Features:
    - User profile management
    - Adaptive weights learning
    - Compatibility filtering
    - Global analytics tracking
    """

    def __init__(self, redis_repo, postgres_repo):
        """Initialize with dependencies"""
        self.redis = redis_repo
        self.postgres = postgres_repo

        try:
            self.service = AdvancedPersonalizationService(
                database=postgres_repo,
                redis_client=redis_repo,
                enable_adaptive_weights=True,
                enable_global_analytics=True,
                enable_compatibility_filter=True,
            )
            logger.info("✅ PersonalizationService initialized")
        except Exception as e:
            logger.error(f"PersonalizationService init failed: {e}")
            self.service = None

    async def track_search(self, session_id: str, query: str, results_count: int = 0) -> bool:
        """Track search query"""
        try:
            if not self.service:
                return False

            self.service.track_search(
                session_id=session_id, query=query, results_count=results_count
            )
            return True
        except Exception as e:
            logger.error(f"Track search error: {e}")
            return False

    async def track_interaction(
        self,
        session_id: str,
        product_id: str,
        event_type: str,
        product_data: Dict[str, Any],
        search_context: str = None,
    ) -> bool:
        """
        Track user interaction

        Args:
            session_id: Session ID
            product_id: Product ID
            event_type: 'view', 'click', 'bookmark'
            product_data: Product information
            search_context: Search query that led to this

        Returns:
            Success status
        """
        try:
            if not self.service:
                return False

            if event_type == "click":
                self.service.track_click(
                    session_id=session_id,
                    product_id=product_id,
                    product=product_data,
                    search_context=search_context,
                )
            elif event_type == "view":
                self.service.track_view(
                    session_id=session_id,
                    product_id=product_id,
                    product=product_data,
                    search_context=search_context,
                )
            elif event_type == "bookmark":
                self.service.track_bookmark(
                    session_id=session_id, product_id=product_id, product=product_data
                )

            return True
        except Exception as e:
            logger.error(f"Track interaction error: {e}")
            return False

    async def get_profile(self, session_id: str) -> Dict[str, Any]:
        """Get user profile"""
        try:
            if not self.service:
                return {"session_id": session_id, "error": "Service not initialized"}

            summary = self.service.get_user_summary(session_id)
            return summary
        except Exception as e:
            logger.error(f"Get profile error: {e}")
            return {"session_id": session_id, "error": str(e)}

    async def get_recommendations(
        self,
        session_id: str,
        all_products: List[Dict[str, Any]],
        top_k: int = 10,
        category_filter: str = None,
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations"""
        try:
            if not self.service:
                return []

            recommendations = self.service.get_recommendations(
                session_id=session_id,
                all_products=all_products,
                top_k=top_k,
                category_filter=category_filter,
            )
            return recommendations
        except Exception as e:
            logger.error(f"Get recommendations error: {e}")
            return []
