"""
Unit Tests for ResponseGenerator

Tests LLM response generation with Ollama integration.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from apps.api.rag_consultation.generation.response_generator import ResponseGenerator
from apps.api.rag_consultation.models import FormalityLevel, QueryType, UrgencyLevel


@pytest.fixture
def response_generator():
    """Response generator instance."""
    return ResponseGenerator(
        ollama_url="http://localhost:11434",
        model_name="qwen2.5:7b-instruct-q4_K_M",
    )


class TestResponseGenerator:
    """Test cases for ResponseGenerator."""

    def test_initialization_validates_localhost(self):
        """Test that non-localhost URLs are rejected."""
        with pytest.raises(ValueError, match="Ollama URL must use localhost"):
            ResponseGenerator(ollama_url="http://172.28.0.6:11434")

    def test_initialization_accepts_localhost(self):
        """Test that localhost URLs are accepted."""
        generator = ResponseGenerator(ollama_url="http://localhost:11434")
        assert generator.ollama_url == "http://localhost:11434"

    def test_initialization_accepts_127_0_0_1(self):
        """Test that 127.0.0.1 URLs are accepted."""
        generator = ResponseGenerator(ollama_url="http://127.0.0.1:11434")
        assert generator.ollama_url == "http://127.0.0.1:11434"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_call_ollama_success(self, mock_post, response_generator):
        """Test successful Ollama API call."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Generated text"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = await response_generator._call_ollama("Test prompt")

        assert result == "Generated text"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_call_ollama_timeout(self, mock_post, response_generator):
        """Test Ollama timeout handling."""
        mock_post.side_effect = httpx.TimeoutException("Timeout")

        with pytest.raises(RuntimeError, match="Ollama request timeout"):
            await response_generator._call_ollama("Test prompt")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_generate_with_template(self, mock_post, response_generator):
        """Test response generation with template formatting."""
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Test answer"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = await response_generator.generate(
            prompt="Test prompt",
            query_type=QueryType.FACTUAL,
            formality=FormalityLevel.FORMAL,
        )

        assert "Test answer" in result
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_empty_prompt_raises_error(self, response_generator):
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await response_generator.generate(
                prompt="",
                query_type=QueryType.FACTUAL,
            )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_health_check_success(self, mock_get, response_generator):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await response_generator.health_check()

        assert result is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_health_check_failure(self, mock_get, response_generator):
        """Test failed health check."""
        mock_get.side_effect = httpx.HTTPError("Connection failed")

        result = await response_generator.health_check()

        assert result is False
