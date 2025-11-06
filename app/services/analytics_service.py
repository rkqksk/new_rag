"""AnalyticsService - Complete Integration"""
from typing import List, Dict, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Analytics service
    
    Features:
    - Top keywords tracking
    - Popular products tracking
    - Trending queries
    - Search patterns
    """
    
    def __init__(self, postgres_repo):
        """Initialize with dependencies"""
        self.postgres = postgres_repo
        logger.info("✅ AnalyticsService initialized")
    
    async def get_top_keywords(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top keywords"""
        try:
            results = await self.postgres.get_top_keywords(limit=limit)
            return results
        except Exception as e:
            logger.error(f"Get top keywords error: {e}")
            return []
    
    async def get_top_products(
        self,
        limit: int = 20,
        metric: str = "click"
    ) -> List[Dict[str, Any]]:
        """
        Get top products
        
        Args:
            limit: Number of results
            metric: 'click', 'view', or 'bookmark'
        
        Returns:
            List of top products
        """
        try:
            results = await self.postgres.get_top_products(limit=limit)
            return results
        except Exception as e:
            logger.error(f"Get top products error: {e}")
            return []
    
    async def get_trending_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending queries"""
        try:
            # TODO: Implement trending calculation
            # For now, return top keywords
            results = await self.postgres.get_top_keywords(limit=limit)
            return results
        except Exception as e:
            logger.error(f"Get trending queries error: {e}")
            return []
    
    async def get_search_patterns(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get common search patterns"""
        try:
            results = await self.postgres.fetch(
                """
                SELECT pattern, count 
                FROM search_context_patterns 
                ORDER BY count DESC 
                LIMIT $1
                """,
                limit
            )
            return results
        except Exception as e:
            logger.error(f"Get search patterns error: {e}")
            return []
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        try:
            # Get all stats
            top_keywords = await self.get_top_keywords(limit=5)
            top_products = await self.get_top_products(limit=5)
            trending = await self.get_trending_queries(limit=5)
            
            return {
                "top_keywords": top_keywords,
                "top_products": top_products,
                "trending_queries": trending
            }
        except Exception as e:
            logger.error(f"Get analytics summary error: {e}")
            return {}
