"""Unit tests for AnalyticsService"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.analytics_service import AnalyticsService


@pytest.mark.unit
class TestAnalyticsService:
    """Test cases for AnalyticsService"""

    @pytest.fixture
    def service(self, mock_postgres_repo):
        """Create service instance"""
        return AnalyticsService(postgres_repo=mock_postgres_repo)

    @pytest.mark.asyncio
    async def test_get_top_keywords(self, service, mock_postgres_repo):
        """Test retrieving top keywords"""
        # Arrange
        keywords_data = [
            {"keyword": "50ml", "search_count": 120, "last_searched": "2025-11-06"},
            {"keyword": "PET", "search_count": 95, "last_searched": "2025-11-06"},
            {"keyword": "20파이", "search_count": 85, "last_searched": "2025-11-06"},
        ]
        mock_postgres_repo.get_top_keywords.return_value = keywords_data

        # Act
        result = await service.get_top_keywords(limit=3)

        # Assert
        assert len(result) == 3
        assert result[0]["keyword"] == "50ml"
        assert result[0]["search_count"] == 120
        mock_postgres_repo.get_top_keywords.assert_called_once_with(limit=3)

    @pytest.mark.asyncio
    async def test_get_top_keywords_default_limit(self, service, mock_postgres_repo):
        """Test retrieving top keywords with default limit"""
        # Arrange
        keywords_data = [{"keyword": f"keyword{i}", "search_count": 100 - i} for i in range(20)]
        mock_postgres_repo.get_top_keywords.return_value = keywords_data

        # Act
        result = await service.get_top_keywords()

        # Assert
        assert len(result) == 20
        mock_postgres_repo.get_top_keywords.assert_called_once_with(limit=20)

    @pytest.mark.asyncio
    async def test_get_top_products_by_click(self, service, mock_postgres_repo):
        """Test retrieving top products by click count"""
        # Arrange
        products_data = [
            {
                "product_id": "PROD-001",
                "product_name": "50ml PET 용기",
                "click_count": 50,
                "view_count": 200,
                "bookmark_count": 10,
            },
            {
                "product_id": "PROD-002",
                "product_name": "20파이 캡",
                "click_count": 45,
                "view_count": 180,
                "bookmark_count": 8,
            },
        ]
        mock_postgres_repo.get_top_products.return_value = products_data

        # Act
        result = await service.get_top_products(limit=2, metric="click")

        # Assert
        assert len(result) == 2
        assert result[0]["click_count"] == 50
        mock_postgres_repo.get_top_products.assert_called_once_with(limit=2, metric="click")

    @pytest.mark.asyncio
    async def test_get_top_products_by_view(self, service, mock_postgres_repo):
        """Test retrieving top products by view count"""
        # Arrange
        products_data = [{"product_id": "PROD-001", "view_count": 200}]
        mock_postgres_repo.get_top_products.return_value = products_data

        # Act
        result = await service.get_top_products(limit=1, metric="view")

        # Assert
        assert result[0]["view_count"] == 200

    @pytest.mark.asyncio
    async def test_get_trending_queries(self, service, mock_postgres_repo):
        """Test retrieving trending queries"""
        # Arrange
        trending_data = [
            {
                "query": "20파이 캡",
                "recent_count": 25,
                "previous_count": 10,
                "growth_rate": 2.5,
                "trend": "up",
            },
            {
                "query": "50ml 용기",
                "recent_count": 20,
                "previous_count": 15,
                "growth_rate": 1.33,
                "trend": "up",
            },
        ]
        mock_postgres_repo.get_trending_queries.return_value = trending_data

        # Act
        result = await service.get_trending_queries(limit=2)

        # Assert
        assert len(result) == 2
        assert result[0]["growth_rate"] == 2.5
        assert result[0]["trend"] == "up"

    @pytest.mark.asyncio
    async def test_get_search_patterns(self, service, mock_postgres_repo):
        """Test retrieving common search patterns"""
        # Arrange
        patterns_data = [
            {
                "pattern": "bottle_then_cap",
                "first_category": "bottle",
                "second_category": "cap",
                "frequency": 85,
                "avg_time_between": 120,  # seconds
            },
            {
                "pattern": "bottle_then_pump",
                "first_category": "bottle",
                "second_category": "pump",
                "frequency": 45,
                "avg_time_between": 150,
            },
        ]
        mock_postgres_repo.get_search_patterns.return_value = patterns_data

        # Act
        result = await service.get_search_patterns(limit=2)

        # Assert
        assert len(result) == 2
        assert result[0]["pattern"] == "bottle_then_cap"
        assert result[0]["frequency"] == 85

    @pytest.mark.asyncio
    async def test_get_analytics_summary(self, service, mock_postgres_repo):
        """Test retrieving comprehensive analytics summary"""
        # Arrange
        mock_postgres_repo.get_top_keywords.return_value = [
            {"keyword": "50ml", "search_count": 120}
        ]
        mock_postgres_repo.get_top_products.return_value = [
            {"product_id": "PROD-001", "click_count": 50}
        ]
        mock_postgres_repo.get_trending_queries.return_value = [
            {"query": "20파이 캡", "growth_rate": 2.5}
        ]
        mock_postgres_repo.get_search_patterns.return_value = [
            {"pattern": "bottle_then_cap", "frequency": 85}
        ]

        # Mock total counts
        mock_postgres_repo.fetch_one.return_value = {
            "total_searches": 1500,
            "total_clicks": 450,
            "unique_sessions": 320,
        }

        # Act
        result = await service.get_analytics_summary()

        # Assert
        assert "top_keywords" in result
        assert "top_products" in result
        assert "trending_queries" in result
        assert "search_patterns" in result
        assert "total_searches" in result

    @pytest.mark.asyncio
    async def test_get_top_keywords_empty_results(self, service, mock_postgres_repo):
        """Test handling empty results"""
        # Arrange
        mock_postgres_repo.get_top_keywords.return_value = []

        # Act
        result = await service.get_top_keywords(limit=20)

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_top_products_invalid_metric(self, service, mock_postgres_repo):
        """Test handling invalid metric parameter"""
        # Arrange
        # Service should validate or repo should handle
        mock_postgres_repo.get_top_products.return_value = []

        # Act
        result = await service.get_top_products(limit=10, metric="invalid_metric")

        # Assert - depends on implementation
        # Either returns empty or raises exception
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_trending_queries_no_trends(self, service, mock_postgres_repo):
        """Test when there are no trending queries"""
        # Arrange
        mock_postgres_repo.get_trending_queries.return_value = []

        # Act
        result = await service.get_trending_queries(limit=10)

        # Assert
        assert len(result) == 0
