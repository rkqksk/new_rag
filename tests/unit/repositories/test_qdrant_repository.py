"""Unit tests for QdrantRepository"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.repositories.qdrant_repository import QdrantRepository

@pytest.mark.unit
class TestQdrantRepository:
    """Test cases for QdrantRepository"""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client"""
        with patch('app.repositories.qdrant_repository.QdrantClient') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client
    
    @pytest.fixture
    def repository(self, mock_qdrant_client):
        """Create repository instance"""
        return QdrantRepository(host="localhost", port=6333)
    
    @pytest.mark.asyncio
    async def test_search_basic(self, repository, mock_qdrant_client, sample_search_results):
        """Test basic vector search"""
        # Arrange
        mock_qdrant_client.search.return_value = [
            MagicMock(
                id=result["id"],
                score=result["score"],
                payload=result["payload"]
            )
            for result in sample_search_results
        ]
        
        query_vector = [0.1] * 384
        
        # Act
        results = await repository.search(
            collection_name="products",
            query_vector=query_vector,
            limit=10
        )
        
        # Assert
        assert len(results) == 2
        assert results[0]["id"] == "PROD-001"
        assert results[0]["score"] == 0.85
        assert "text" in results[0]["payload"]
        
        mock_qdrant_client.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, repository, mock_qdrant_client):
        """Test search with metadata filters"""
        # Arrange
        mock_qdrant_client.search.return_value = []
        query_vector = [0.1] * 384
        filters = {"category": "bottle", "neck_size": "20파이"}
        
        # Act
        results = await repository.search(
            collection_name="products",
            query_vector=query_vector,
            limit=10,
            filter_conditions=filters
        )
        
        # Assert
        mock_qdrant_client.search.assert_called_once()
        call_kwargs = mock_qdrant_client.search.call_args[1]
        assert "query_filter" in call_kwargs
    
    @pytest.mark.asyncio
    async def test_search_with_score_threshold(self, repository, mock_qdrant_client):
        """Test search with score threshold"""
        # Arrange
        mock_qdrant_client.search.return_value = [
            MagicMock(id="PROD-001", score=0.85, payload={"text": "test"}),
            MagicMock(id="PROD-002", score=0.75, payload={"text": "test2"})
        ]
        
        query_vector = [0.1] * 384
        
        # Act
        results = await repository.search(
            collection_name="products",
            query_vector=query_vector,
            limit=10,
            score_threshold=0.8
        )
        
        # Assert
        mock_qdrant_client.search.assert_called_once()
        call_kwargs = mock_qdrant_client.search.call_args[1]
        assert call_kwargs["score_threshold"] == 0.8
    
    @pytest.mark.asyncio
    async def test_search_multi_vector(self, repository, mock_qdrant_client):
        """Test multi-vector search (text + image + shape)"""
        # Arrange
        mock_qdrant_client.search.return_value = [
            MagicMock(id="PROD-001", score=0.85, payload={"text": "test"})
        ]
        
        query_vectors = {
            "text": [0.1] * 384,
            "image": [0.2] * 1024,
            "shape": [0.3] * 128
        }
        weights = {"text": 0.5, "image": 0.3, "shape": 0.2}
        
        # Act
        results = await repository.search_multi_vector(
            collection_name="products_multimodal",
            query_vectors=query_vectors,
            weights=weights,
            limit=10
        )
        
        # Assert
        assert isinstance(results, list)
        # Multi-vector search would call search multiple times and fuse results
    
    @pytest.mark.asyncio
    async def test_get_point(self, repository, mock_qdrant_client):
        """Test retrieving a single point by ID"""
        # Arrange
        mock_qdrant_client.retrieve.return_value = [
            MagicMock(
                id="PROD-001",
                payload={"text": "50ml PET 용기"}
            )
        ]
        
        # Act
        result = await repository.get_point(
            collection_name="products",
            point_id="PROD-001"
        )
        
        # Assert
        assert result is not None
        assert result["id"] == "PROD-001"
        mock_qdrant_client.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upsert_points(self, repository, mock_qdrant_client):
        """Test upserting points to collection"""
        # Arrange
        points = [
            {"id": "PROD-001", "vector": [0.1] * 384, "payload": {"text": "test"}},
            {"id": "PROD-002", "vector": [0.2] * 384, "payload": {"text": "test2"}}
        ]
        
        # Act
        success = await repository.upsert_points(
            collection_name="products",
            points=points
        )
        
        # Assert
        assert success is True
        mock_qdrant_client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, repository, mock_qdrant_client):
        """Test health check when Qdrant is healthy"""
        # Arrange
        mock_qdrant_client.get_collections.return_value = MagicMock()
        
        # Act
        is_healthy = await repository.health_check()
        
        # Assert
        assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, repository, mock_qdrant_client):
        """Test health check when Qdrant is down"""
        # Arrange
        mock_qdrant_client.get_collections.side_effect = Exception("Connection failed")
        
        # Act
        is_healthy = await repository.health_check()
        
        # Assert
        assert is_healthy is False
    
    @pytest.mark.asyncio
    async def test_search_empty_results(self, repository, mock_qdrant_client):
        """Test search with no results"""
        # Arrange
        mock_qdrant_client.search.return_value = []
        
        # Act
        results = await repository.search(
            collection_name="products",
            query_vector=[0.1] * 384,
            limit=10
        )
        
        # Assert
        assert len(results) == 0
        assert isinstance(results, list)
