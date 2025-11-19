"""Unit tests for RedisRepository"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.repositories.redis_repository import RedisRepository


@pytest.mark.unit
class TestRedisRepository:
    """Test cases for RedisRepository"""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        with patch("app.repositories.redis_repository.aioredis") as mock:
            client = AsyncMock()
            mock.from_url.return_value = client
            yield client

    @pytest.fixture
    def repository(self, mock_redis_client):
        """Create repository instance"""
        return RedisRepository(host="localhost", port=6379, db=0)

    @pytest.mark.asyncio
    async def test_get_existing_key(self, repository, mock_redis_client):
        """Test getting an existing key"""
        # Arrange
        test_value = {"product_id": "PROD-001", "name": "50ml 용기"}
        mock_redis_client.get.return_value = json.dumps(test_value)

        # Act
        result = await repository.get("test_key")

        # Assert
        assert result == test_value
        mock_redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, repository, mock_redis_client):
        """Test getting a non-existent key"""
        # Arrange
        mock_redis_client.get.return_value = None

        # Act
        result = await repository.get("nonexistent_key")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_default_ttl(self, repository, mock_redis_client):
        """Test setting a key with default TTL"""
        # Arrange
        test_value = {"product_id": "PROD-001"}

        # Act
        await repository.set("test_key", test_value)

        # Assert
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args[0]
        assert call_args[0] == "test_key"
        assert call_args[1] == 3600  # Default TTL
        assert json.loads(call_args[2]) == test_value

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, repository, mock_redis_client):
        """Test setting a key with custom TTL"""
        # Arrange
        test_value = {"session_id": "sess_123"}
        custom_ttl = 7200

        # Act
        await repository.set("session:sess_123", test_value, ttl=custom_ttl)

        # Assert
        call_args = mock_redis_client.setex.call_args[0]
        assert call_args[1] == custom_ttl

    @pytest.mark.asyncio
    async def test_delete_key(self, repository, mock_redis_client):
        """Test deleting a key"""
        # Arrange
        mock_redis_client.delete.return_value = 1

        # Act
        result = await repository.delete("test_key")

        # Assert
        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, repository, mock_redis_client):
        """Test deleting a non-existent key"""
        # Arrange
        mock_redis_client.delete.return_value = 0

        # Act
        result = await repository.delete("nonexistent_key")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(self, repository, mock_redis_client):
        """Test checking existence of existing key"""
        # Arrange
        mock_redis_client.exists.return_value = 1

        # Act
        result = await repository.exists("test_key")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, repository, mock_redis_client):
        """Test checking existence of non-existent key"""
        # Arrange
        mock_redis_client.exists.return_value = 0

        # Act
        result = await repository.exists("nonexistent_key")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_set_json_complex_object(self, repository, mock_redis_client):
        """Test setting a complex JSON object"""
        # Arrange
        complex_object = {
            "user_profile": {
                "session_id": "sess_123",
                "preferences": {"categories": ["bottle", "cap"], "suppliers": ["천진코리아"]},
                "history": ["query1", "query2"],
            }
        }

        # Act
        await repository.set("profile:sess_123", complex_object)

        # Assert
        call_args = mock_redis_client.setex.call_args[0]
        stored_value = json.loads(call_args[2])
        assert stored_value == complex_object

    @pytest.mark.asyncio
    async def test_get_with_json_decode_error(self, repository, mock_redis_client):
        """Test handling JSON decode errors"""
        # Arrange
        mock_redis_client.get.return_value = "invalid json {"

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            await repository.get("bad_key")

    @pytest.mark.asyncio
    async def test_health_check_success(self, repository, mock_redis_client):
        """Test health check when Redis is healthy"""
        # Arrange
        mock_redis_client.ping.return_value = True

        # Act
        is_healthy = await repository.health_check()

        # Assert
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, repository, mock_redis_client):
        """Test health check when Redis is down"""
        # Arrange
        mock_redis_client.ping.side_effect = Exception("Connection failed")

        # Act
        is_healthy = await repository.health_check()

        # Assert
        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_cache_invalidation_pattern(self, repository, mock_redis_client):
        """Test cache invalidation with key pattern"""
        # Arrange
        mock_redis_client.keys.return_value = ["cache:search:query1", "cache:search:query2"]

        # Act
        await repository.delete_pattern("cache:search:*")

        # Assert
        mock_redis_client.keys.assert_called_once()
        # Should delete all matching keys
