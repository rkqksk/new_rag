"""
Tests for NexaAI Service Integration
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.nexa_service import NexaService, NexaConfig


class TestNexaService:
    """Test NexaAI service wrapper"""

    @pytest.fixture
    def nexa_config(self):
        """Test configuration"""
        return NexaConfig(
            base_url="http://localhost:8080/v1",
            timeout=30
        )

    @pytest.fixture
    def nexa_service(self, nexa_config):
        """NexaAI service instance"""
        return NexaService(nexa_config)

    @pytest.mark.asyncio
    async def test_generate_text(self, nexa_service):
        """Test text generation"""
        with patch.object(nexa_service.async_client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            # Mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response"
            mock_create.return_value = mock_response

            # Test
            result = await nexa_service.generate_text("Test prompt")

            # Assert
            assert result == "Test response"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embeddings(self, nexa_service):
        """Test embedding generation"""
        with patch.object(nexa_service.async_client.embeddings, 'create', new_callable=AsyncMock) as mock_create:
            # Mock response
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=[0.1, 0.2, 0.3]),
                Mock(embedding=[0.4, 0.5, 0.6])
            ]
            mock_create.return_value = mock_response

            # Test
            result = await nexa_service.generate_embeddings(["text1", "text2"])

            # Assert
            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_health_check_success(self, nexa_service):
        """Test health check - success"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await nexa_service.health_check()

            assert result["healthy"] is True
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, nexa_service):
        """Test health check - failure"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("Connection failed"))

            result = await nexa_service.health_check()

            assert result["healthy"] is False
            assert "error" in result


class TestNexaConfig:
    """Test NexaAI configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = NexaConfig()

        assert config.base_url == "http://localhost:8080/v1"
        assert config.api_key == "not-needed"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_custom_config(self):
        """Test custom configuration"""
        config = NexaConfig(
            base_url="http://custom:9000/v1",
            timeout=60
        )

        assert config.base_url == "http://custom:9000/v1"
        assert config.timeout == 60
