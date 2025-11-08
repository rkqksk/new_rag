"""
Tests for Unified LLM Service
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.core.model_router import ModelEngine
from src.services.unified_llm_service import NexaConfig, OllamaConfig, UnifiedLLMService


class TestUnifiedLLMService:
    """Test unified LLM service"""

    @pytest.fixture
    def unified_llm(self):
        """Unified LLM service instance"""
        with patch("src.services.unified_llm_service.NexaService"):
            with patch("src.services.unified_llm_service.OllamaService"):
                service = UnifiedLLMService()
                service.nexa_available = True
                service.ollama_available = True
                return service

    @pytest.mark.asyncio
    async def test_generate_simple_query(self, unified_llm):
        """Test generation - simple query routed to NexaAI"""
        unified_llm.nexa.generate_text = AsyncMock(return_value="NexaAI response")

        result = await unified_llm.generate("간단한 검색")

        assert result == "NexaAI response"
        unified_llm.nexa.generate_text.assert_called_once()
        assert unified_llm.stats["nexa_requests"] == 1

    @pytest.mark.asyncio
    async def test_generate_complex_query(self, unified_llm):
        """Test generation - medium-complex query routed to NexaAI"""
        # This query scores ~0.4-0.5, so routes to NexaAI medium model
        unified_llm.nexa.generate_text = AsyncMock(return_value="NexaAI medium response")

        complex_query = "왜 PET가 PP보다 투명한지 상세히 분석하고 화학적 구조를 비교하며 각각의 특성을 설명해주세요"

        result = await unified_llm.generate(complex_query)

        assert result == "NexaAI medium response"
        unified_llm.nexa.generate_text.assert_called_once()
        assert unified_llm.stats["nexa_requests"] == 1

    @pytest.mark.asyncio
    async def test_generate_force_engine(self, unified_llm):
        """Test forced engine selection"""
        unified_llm.ollama.generate = AsyncMock(return_value="Forced Ollama")

        result = await unified_llm.generate("간단한 검색", force_engine=ModelEngine.OLLAMA)

        assert result == "Forced Ollama"
        unified_llm.ollama.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_with_nexa(self, unified_llm):
        """Test embedding generation with NexaAI"""
        unified_llm.nexa.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])

        result = await unified_llm.embed(["text1", "text2"])

        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        unified_llm.nexa.generate_embeddings.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_with_ollama(self, unified_llm):
        """Test embedding generation with Ollama"""
        unified_llm.ollama.embed = AsyncMock(return_value=[[0.5, 0.6], [0.7, 0.8]])

        result = await unified_llm.embed(["text1", "text2"], engine=ModelEngine.OLLAMA)

        assert len(result) == 2
        assert result[0] == [0.5, 0.6]
        unified_llm.ollama.embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_image(self, unified_llm):
        """Test image analysis"""
        unified_llm.nexa.analyze_image = AsyncMock(return_value="Image analysis result")

        result = await unified_llm.analyze_image(image_path="test.jpg", prompt="Describe this")

        assert result == "Image analysis result"
        unified_llm.nexa.analyze_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, unified_llm):
        """Test health check - all engines healthy"""
        unified_llm.nexa.health_check = AsyncMock(return_value={"healthy": True})
        unified_llm.ollama.health_check = AsyncMock(return_value={"healthy": True})

        health = await unified_llm.health_check()

        assert health["unified"] is True
        assert health["engines"]["nexa"]["healthy"] is True
        assert health["engines"]["ollama"]["healthy"] is True

    @pytest.mark.asyncio
    async def test_health_check_nexa_down(self, unified_llm):
        """Test health check - NexaAI down"""
        unified_llm.nexa.health_check = AsyncMock(
            return_value={"healthy": False, "error": "Connection failed"}
        )
        unified_llm.ollama.health_check = AsyncMock(return_value={"healthy": True})

        health = await unified_llm.health_check()

        assert health["unified"] is False  # System degraded
        assert health["engines"]["nexa"]["healthy"] is False
        assert health["engines"]["ollama"]["healthy"] is True

    def test_get_stats(self, unified_llm):
        """Test statistics retrieval"""
        unified_llm.stats = {"nexa_requests": 42, "ollama_requests": 15, "errors": 2}

        stats = unified_llm.get_stats()

        assert stats["nexa_requests"] == 42
        assert stats["ollama_requests"] == 15
        assert stats["errors"] == 2
        assert stats["nexa_available"] is True
        assert stats["ollama_available"] is True

    @pytest.mark.asyncio
    async def test_error_handling(self, unified_llm):
        """Test error handling and stats"""
        unified_llm.nexa.generate_text = AsyncMock(side_effect=Exception("API Error"))

        with pytest.raises(Exception):
            await unified_llm.generate("test query")

        assert unified_llm.stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_nexa_unavailable_fallback(self):
        """Test behavior when NexaAI unavailable"""
        with patch(
            "src.services.unified_llm_service.NexaService", side_effect=Exception("Not available")
        ):
            with patch("src.services.unified_llm_service.OllamaService"):
                service = UnifiedLLMService()

                assert service.nexa_available is False
                assert service.ollama_available is True

                # Simple query should fallback to Ollama
                service.ollama.generate = AsyncMock(return_value="Ollama fallback")

                result = await service.generate("simple query")

                assert result == "Ollama fallback"
