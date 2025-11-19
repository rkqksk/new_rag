"""Unit tests for SearchService"""

from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from apps.api.services.search_service import SearchService


@pytest.mark.unit
class TestSearchService:
    """Test cases for SearchService"""

    @pytest.fixture
    def service(self, mock_qdrant_repo, mock_redis_repo, mock_postgres_repo):
        """Create service instance with mocked dependencies"""
        with (
            patch("app.services.search_service.MultiModalEmbedder") as mock_embedder_class,
            patch("app.services.search_service.CrossEncoderReranker") as mock_reranker_class,
            patch("app.services.search_service.QueryRouter") as mock_router_class,
            patch(
                "app.services.search_service.AdvancedPersonalizationService"
            ) as mock_personalization_class,
        ):

            # Create service
            service = SearchService(
                qdrant_repo=mock_qdrant_repo,
                redis_repo=mock_redis_repo,
                postgres_repo=mock_postgres_repo,
            )

            # Attach mocks for assertions
            service.embedder_mock = mock_embedder_class.return_value
            service.reranker_mock = mock_reranker_class.return_value
            service.router_mock = mock_router_class.return_value
            service.personalization_mock = mock_personalization_class.return_value

            yield service

    @pytest.mark.asyncio
    async def test_search_with_cache_hit(
        self, service, mock_redis_repo, sample_products, sample_session_id
    ):
        """Test search with cache hit"""
        # Arrange
        query = "50ml PET 용기"
        cached_results = {
            "results": sample_products,
            "total": len(sample_products),
            "query": query,
            "session_id": sample_session_id,
            "cached": True,
        }
        mock_redis_repo.get.return_value = cached_results

        # Act
        result = await service.search(
            query=query, session_id=sample_session_id, top_k=20, use_cache=True
        )

        # Assert
        assert result["cached"] is True
        assert len(result["results"]) == len(sample_products)
        mock_redis_repo.get.assert_called_once()
        # Should not call Qdrant on cache hit
        service.qdrant_repo.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_with_cache_miss(
        self, service, mock_qdrant_repo, mock_redis_repo, sample_search_results, sample_session_id
    ):
        """Test search with cache miss and full pipeline"""
        # Arrange
        query = "50ml PET 용기"
        mock_redis_repo.get.return_value = None  # Cache miss

        # Mock embedder
        service.embedder_mock.encode_text.return_value = [0.1] * 384

        # Mock router
        service.router_mock.route_query.return_value = {
            "query_type": "PRODUCT_SEARCH",
            "strategy": "TEXT_ONLY",
        }

        # Mock Qdrant search
        mock_qdrant_repo.search.return_value = sample_search_results

        # Mock reranker (returns same results)
        service.reranker_mock.rerank.return_value = sample_search_results

        # Mock personalization
        service.personalization_mock.personalize_results.return_value = sample_search_results[:2]

        # Act
        result = await service.search(
            query=query, session_id=sample_session_id, top_k=20, use_cache=True
        )

        # Assert
        assert result["cached"] is False
        assert len(result["results"]) > 0

        # Verify pipeline steps
        service.router_mock.route_query.assert_called_once_with(query)
        service.embedder_mock.encode_text.assert_called_once()
        mock_qdrant_repo.search.assert_called_once()
        service.reranker_mock.rerank.assert_called_once()
        service.personalization_mock.personalize_results.assert_called_once()

        # Should cache results
        mock_redis_repo.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_without_caching(
        self, service, mock_redis_repo, mock_qdrant_repo, sample_search_results
    ):
        """Test search with caching disabled"""
        # Arrange
        query = "20파이 캡"
        service.embedder_mock.encode_text.return_value = [0.1] * 384
        service.router_mock.route_query.return_value = {
            "query_type": "PRODUCT_SEARCH",
            "strategy": "TEXT_ONLY",
        }
        mock_qdrant_repo.search.return_value = sample_search_results
        service.reranker_mock.rerank.return_value = sample_search_results
        service.personalization_mock.personalize_results.return_value = sample_search_results

        # Act
        result = await service.search(query=query, session_id=None, top_k=20, use_cache=False)

        # Assert
        # Should not check cache
        mock_redis_repo.get.assert_not_called()
        # Should not set cache
        mock_redis_repo.set.assert_not_called()
        # Should still perform search
        mock_qdrant_repo.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_image_search(self, service, mock_qdrant_repo, sample_search_results, tmp_path):
        """Test image-based search"""
        # Arrange
        image_path = str(tmp_path / "test_image.jpg")
        # Create dummy image file
        with open(image_path, "wb") as f:
            f.write(b"fake image data")

        service.embedder_mock.encode_image.return_value = [0.2] * 1024
        mock_qdrant_repo.search.return_value = sample_search_results

        # Act
        result = await service.image_search(image_path=image_path, session_id=None, top_k=20)

        # Assert
        service.embedder_mock.encode_image.assert_called_once_with(image_path)
        mock_qdrant_repo.search.assert_called_once()
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_hybrid_search(self, service, mock_qdrant_repo, sample_search_results, tmp_path):
        """Test hybrid search (text + image)"""
        # Arrange
        query = "50ml 용기"
        image_path = str(tmp_path / "test_image.jpg")
        with open(image_path, "wb") as f:
            f.write(b"fake image data")

        service.embedder_mock.encode_text.return_value = [0.1] * 384
        service.embedder_mock.encode_image.return_value = [0.2] * 1024
        mock_qdrant_repo.search_multi_vector.return_value = sample_search_results

        # Act
        result = await service.hybrid_search(
            query=query,
            image_path=image_path,
            text_weight=0.6,
            image_weight=0.4,
            session_id=None,
            top_k=20,
        )

        # Assert
        service.embedder_mock.encode_text.assert_called_once()
        service.embedder_mock.encode_image.assert_called_once()
        mock_qdrant_repo.search_multi_vector.assert_called_once()

        # Verify weights are passed
        call_kwargs = mock_qdrant_repo.search_multi_vector.call_args[1]
        assert "weights" in call_kwargs

    @pytest.mark.asyncio
    async def test_search_with_personalization(
        self,
        service,
        mock_qdrant_repo,
        sample_search_results,
        sample_session_id,
        sample_user_profile,
    ):
        """Test search with personalization applied"""
        # Arrange
        query = "20파이 캡"
        service.embedder_mock.encode_text.return_value = [0.1] * 384
        service.router_mock.route_query.return_value = {
            "query_type": "PRODUCT_SEARCH",
            "strategy": "TEXT_ONLY",
        }
        mock_qdrant_repo.search.return_value = sample_search_results
        service.reranker_mock.rerank.return_value = sample_search_results

        # Mock personalization returns filtered/re-ranked results
        personalized_results = sample_search_results[:1]  # Only top result
        service.personalization_mock.personalize_results.return_value = personalized_results

        # Act
        result = await service.search(
            query=query, session_id=sample_session_id, top_k=20, use_cache=False
        )

        # Assert
        service.personalization_mock.personalize_results.assert_called_once()
        # Results should be personalized
        assert len(result["results"]) == len(personalized_results)

    @pytest.mark.asyncio
    async def test_search_query_routing_image_strategy(
        self, service, mock_qdrant_repo, sample_search_results
    ):
        """Test that query routing triggers correct search strategy"""
        # Arrange
        query = "이 제품과 비슷한 용기"  # Query suggesting image search

        # Router detects image search intent
        service.router_mock.route_query.return_value = {
            "query_type": "IMAGE_SEARCH",
            "strategy": "IMAGE_ONLY",
        }

        service.embedder_mock.encode_text.return_value = [0.1] * 384
        mock_qdrant_repo.search.return_value = sample_search_results
        service.reranker_mock.rerank.return_value = sample_search_results
        service.personalization_mock.personalize_results.return_value = sample_search_results

        # Act
        result = await service.search(query=query, session_id=None, top_k=20, use_cache=False)

        # Assert
        service.router_mock.route_query.assert_called_once()
        # Verify routing was used
        routing_result = service.router_mock.route_query.return_value
        assert routing_result["query_type"] == "IMAGE_SEARCH"

    @pytest.mark.asyncio
    async def test_search_with_empty_results(self, service, mock_qdrant_repo):
        """Test search that returns no results"""
        # Arrange
        query = "존재하지 않는 제품"
        service.embedder_mock.encode_text.return_value = [0.1] * 384
        service.router_mock.route_query.return_value = {
            "query_type": "PRODUCT_SEARCH",
            "strategy": "TEXT_ONLY",
        }
        mock_qdrant_repo.search.return_value = []  # No results
        service.reranker_mock.rerank.return_value = []
        service.personalization_mock.personalize_results.return_value = []

        # Act
        result = await service.search(query=query, session_id=None, top_k=20, use_cache=False)

        # Assert
        assert result["total"] == 0
        assert len(result["results"]) == 0

    @pytest.mark.asyncio
    async def test_search_error_handling(self, service, mock_qdrant_repo):
        """Test error handling in search pipeline"""
        # Arrange
        query = "test query"
        service.embedder_mock.encode_text.return_value = [0.1] * 384
        service.router_mock.route_query.return_value = {
            "query_type": "PRODUCT_SEARCH",
            "strategy": "TEXT_ONLY",
        }

        # Simulate Qdrant error
        mock_qdrant_repo.search.side_effect = Exception("Qdrant connection failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.search(query=query, session_id=None, top_k=20, use_cache=False)

        assert "Qdrant connection failed" in str(exc_info.value)
