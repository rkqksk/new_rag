"""
Unit tests for Embedding Service - v7.4.0
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.services.embedding_service import (
    EmbeddingService,
    EmbeddingProvider,
    EmbeddingModel,
    get_embedding_service,
    embed_text
)


class TestEmbeddingService:
    """Test EmbeddingService class"""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization"""
        service = EmbeddingService(
            provider=EmbeddingProvider.OPENAI,
            model=EmbeddingModel.TEXT_EMBEDDING_3_SMALL.value
        )

        assert service.provider == EmbeddingProvider.OPENAI
        assert service.model == EmbeddingModel.TEXT_EMBEDDING_3_SMALL.value
        assert service.cache_enabled == True

    @pytest.mark.asyncio
    async def test_get_embedding_dimension(self):
        """Test get embedding dimension"""
        service = EmbeddingService(
            provider=EmbeddingProvider.OPENAI,
            model=EmbeddingModel.TEXT_EMBEDDING_3_SMALL.value
        )

        dimension = service.get_embedding_dimension()
        assert dimension == 1536

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test embedding caching"""
        service = EmbeddingService(
            provider=EmbeddingProvider.OPENAI,
            cache_enabled=True
        )

        # Mock the OpenAI API call
        with patch.object(service, '_generate_openai_embedding',
                         new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = [0.1] * 1536

            # First call - should hit API
            embedding1 = await service.generate_embedding("test text")
            assert mock_generate.call_count == 1

            # Second call with same text - should use cache
            embedding2 = await service.generate_embedding("test text")
            assert mock_generate.call_count == 1  # Not called again
            assert embedding1 == embedding2

    @pytest.mark.asyncio
    async def test_batch_embedding_generation(self):
        """Test batch embedding generation"""
        service = EmbeddingService(
            provider=EmbeddingProvider.OPENAI
        )

        texts = ["text 1", "text 2", "text 3"]

        with patch.object(service, '_generate_openai_embedding',
                         new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = [0.1] * 1536

            embeddings = await service.generate_embeddings_batch(texts, batch_size=2)

            assert len(embeddings) == 3
            assert mock_generate.call_count == 3

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics"""
        service = EmbeddingService(
            provider=EmbeddingProvider.OPENAI,
            cache_enabled=True
        )

        stats = service.get_cache_stats()

        assert stats["cache_enabled"] == True
        assert stats["cache_size"] == 0
        assert stats["provider"] == EmbeddingProvider.OPENAI
        assert stats["dimension"] == 1536

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test cache clearing"""
        service = EmbeddingService(
            provider=EmbeddingProvider.OPENAI,
            cache_enabled=True
        )

        # Add something to cache
        with patch.object(service, '_generate_openai_embedding',
                         new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = [0.1] * 1536
            await service.generate_embedding("test")

        assert len(service.cache) > 0

        # Clear cache
        service.clear_cache()
        assert len(service.cache) == 0

    @pytest.mark.asyncio
    async def test_get_embedding_service_singleton(self):
        """Test singleton pattern"""
        service1 = get_embedding_service(EmbeddingProvider.OPENAI)
        service2 = get_embedding_service(EmbeddingProvider.OPENAI)

        assert service1 is service2

    @pytest.mark.asyncio
    async def test_embed_text_convenience_function(self):
        """Test convenience function"""
        with patch('src.services.embedding_service.get_embedding_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_embedding = AsyncMock(return_value=[0.1] * 768)
            mock_get_service.return_value = mock_service

            embedding = await embed_text("test", EmbeddingProvider.NEXA)

            assert len(embedding) == 768
            mock_service.generate_embedding.assert_called_once_with("test")


class TestEmbeddingProviders:
    """Test different embedding providers"""

    @pytest.mark.asyncio
    async def test_default_models(self):
        """Test default model selection"""
        service_openai = EmbeddingService(provider=EmbeddingProvider.OPENAI)
        assert service_openai.model == EmbeddingModel.TEXT_EMBEDDING_3_SMALL.value

        service_nexa = EmbeddingService(provider=EmbeddingProvider.NEXA)
        assert service_nexa.model == EmbeddingModel.NEXA_NOMIC_EMBED.value

    @pytest.mark.asyncio
    async def test_custom_model(self):
        """Test custom model specification"""
        service = EmbeddingService(
            provider=EmbeddingProvider.OPENAI,
            model=EmbeddingModel.TEXT_EMBEDDING_3_LARGE.value
        )

        assert service.model == EmbeddingModel.TEXT_EMBEDDING_3_LARGE.value
        assert service.get_embedding_dimension() == 3072


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
