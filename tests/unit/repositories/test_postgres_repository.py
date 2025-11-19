"""Unit tests for PostgresRepository"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.repositories.postgres_repository import PostgresRepository


@pytest.mark.unit
class TestPostgresRepository:
    """Test cases for PostgresRepository"""

    @pytest.fixture
    def mock_pool(self):
        """Mock asyncpg connection pool"""
        pool = AsyncMock()
        connection = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = connection
        return pool, connection

    @pytest.fixture
    def repository(self, mock_pool):
        """Create repository instance"""
        with patch("app.repositories.postgres_repository.asyncpg") as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool[0])
            repo = PostgresRepository(
                host="localhost",
                port=5432,
                database="rag_analytics",
                username="test",
                password="test",
            )
            return repo

    @pytest.mark.asyncio
    async def test_insert_search_event(self, repository, mock_pool):
        """Test inserting a search event"""
        # Arrange
        _, connection = mock_pool
        session_id = "sess_123"
        query = "50ml PET 용기"
        keywords = ["50ml", "PET", "용기"]
        results_count = 10

        # Act
        await repository.insert_search_event(
            session_id=session_id, query=query, keywords=keywords, results_count=results_count
        )

        # Assert
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0][0]
        assert "INSERT INTO search_events" in call_args

    @pytest.mark.asyncio
    async def test_insert_product_event(self, repository, mock_pool):
        """Test inserting a product interaction event"""
        # Arrange
        _, connection = mock_pool

        # Act
        await repository.insert_product_event(
            session_id="sess_123",
            product_id="PROD-001",
            event_type="click",
            search_context="50ml 용기",
        )

        # Assert
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0][0]
        assert "INSERT INTO product_events" in call_args

    @pytest.mark.asyncio
    async def test_get_top_keywords(self, repository, mock_pool):
        """Test retrieving top keywords"""
        # Arrange
        _, connection = mock_pool
        connection.fetch.return_value = [
            {"keyword": "50ml", "search_count": 100},
            {"keyword": "PET", "search_count": 85},
            {"keyword": "용기", "search_count": 75},
        ]

        # Act
        results = await repository.get_top_keywords(limit=3)

        # Assert
        assert len(results) == 3
        assert results[0]["keyword"] == "50ml"
        assert results[0]["search_count"] == 100
        connection.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_top_products(self, repository, mock_pool):
        """Test retrieving top products by metric"""
        # Arrange
        _, connection = mock_pool
        connection.fetch.return_value = [
            {"product_id": "PROD-001", "click_count": 50, "view_count": 200},
            {"product_id": "PROD-002", "click_count": 45, "view_count": 180},
        ]

        # Act
        results = await repository.get_top_products(limit=2, metric="click")

        # Assert
        assert len(results) == 2
        assert results[0]["product_id"] == "PROD-001"
        connection.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trending_queries(self, repository, mock_pool):
        """Test retrieving trending queries"""
        # Arrange
        _, connection = mock_pool
        connection.fetch.return_value = [
            {"query": "20파이 캡", "recent_count": 15, "growth_rate": 2.5},
            {"query": "50ml 용기", "recent_count": 12, "growth_rate": 1.8},
        ]

        # Act
        results = await repository.get_trending_queries(hours=24, limit=2)

        # Assert
        assert len(results) == 2
        assert results[0]["query"] == "20파이 캡"
        assert results[0]["growth_rate"] == 2.5

    @pytest.mark.asyncio
    async def test_get_search_patterns(self, repository, mock_pool):
        """Test retrieving common search patterns"""
        # Arrange
        _, connection = mock_pool
        connection.fetch.return_value = [
            {
                "pattern": "bottle_then_cap",
                "first_category": "bottle",
                "second_category": "cap",
                "frequency": 45,
            }
        ]

        # Act
        results = await repository.get_search_patterns(limit=10)

        # Assert
        assert len(results) == 1
        assert results[0]["pattern"] == "bottle_then_cap"

    @pytest.mark.asyncio
    async def test_get_user_focus_profile(self, repository, mock_pool):
        """Test retrieving user's search focus profile"""
        # Arrange
        _, connection = mock_pool
        connection.fetchrow.return_value = {
            "session_id": "sess_123",
            "supplier_score": 0.7,
            "compatibility_score": 0.8,
            "material_score": 0.5,
            "price_score": 0.3,
            "dominant_focus": "compatibility",
        }

        # Act
        result = await repository.get_user_focus_profile("sess_123")

        # Assert
        assert result is not None
        assert result["dominant_focus"] == "compatibility"
        assert result["compatibility_score"] == 0.8

    @pytest.mark.asyncio
    async def test_update_user_focus_profile(self, repository, mock_pool):
        """Test updating user focus profile"""
        # Arrange
        _, connection = mock_pool
        focus_scores = {"supplier_score": 0.6, "compatibility_score": 0.9, "material_score": 0.4}

        # Act
        await repository.update_user_focus_profile("sess_123", focus_scores)

        # Assert
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0][0]
        assert "INSERT INTO user_focus_profiles" in call_args or "UPDATE" in call_args

    @pytest.mark.asyncio
    async def test_fetch_with_no_results(self, repository, mock_pool):
        """Test fetch query with no results"""
        # Arrange
        _, connection = mock_pool
        connection.fetch.return_value = []

        # Act
        results = await repository.fetch(
            "SELECT * FROM search_events WHERE session_id = $1", "nonexistent"
        )

        # Assert
        assert len(results) == 0
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_health_check_success(self, repository, mock_pool):
        """Test health check when database is healthy"""
        # Arrange
        _, connection = mock_pool
        connection.fetchval.return_value = 1

        # Act
        is_healthy = await repository.health_check()

        # Assert
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, repository, mock_pool):
        """Test health check when database is down"""
        # Arrange
        _, connection = mock_pool
        connection.fetchval.side_effect = Exception("Connection failed")

        # Act
        is_healthy = await repository.health_check()

        # Assert
        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, repository, mock_pool):
        """Test transaction rollback on error"""
        # Arrange
        _, connection = mock_pool
        connection.execute.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception):
            await repository.insert_search_event(
                session_id="sess_123", query="test", keywords=["test"], results_count=0
            )
