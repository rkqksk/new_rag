"""
Unit tests for Vector DB Service - v7.4.0
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.vector_db_service import (
    VectorDBService,
    DistanceMetric,
    get_vector_db_service
)


class TestVectorDBService:
    """Test VectorDBService class"""

    def setup_method(self):
        """Setup for each test"""
        with patch('src.services.vector_db_service.QdrantClient'):
            self.service = VectorDBService(url="http://localhost:6333")

    def test_service_initialization(self):
        """Test service initialization"""
        assert self.service is not None
        assert self.service.client is not None

    def test_create_collection(self):
        """Test collection creation"""
        mock_client = self.service.client
        mock_client.create_collection = Mock()

        result = self.service.create_collection(
            collection_name="test_collection",
            vector_size=768,
            distance=DistanceMetric.COSINE
        )

        assert result["collection_name"] == "test_collection"
        assert result["vector_size"] == 768
        assert result["distance"] == DistanceMetric.COSINE
        mock_client.create_collection.assert_called_once()

    def test_upsert_vector(self):
        """Test upserting a vector"""
        mock_client = self.service.client
        mock_client.upsert = Mock()

        vector = [0.1] * 768
        metadata = {"product_name": "Test Product"}

        id = self.service.upsert(
            collection_name="test_collection",
            id="product_001",
            vector=vector,
            metadata=metadata
        )

        assert id == "product_001"
        mock_client.upsert.assert_called_once()

    def test_search_vectors(self):
        """Test vector search"""
        mock_client = self.service.client

        # Mock search results
        mock_result = Mock()
        mock_result.id = "product_001"
        mock_result.score = 0.95
        mock_result.payload = {"product_name": "Test Product"}

        mock_client.search = Mock(return_value=[mock_result])

        query_vector = [0.1] * 768
        results = self.service.search(
            collection_name="test_collection",
            query_vector=query_vector,
            top_k=5
        )

        assert len(results) == 1
        assert results[0]["id"] == "product_001"
        assert results[0]["score"] == 0.95
        assert results[0]["metadata"]["product_name"] == "Test Product"

    def test_hybrid_search(self):
        """Test hybrid search"""
        mock_client = self.service.client

        # Mock dense results
        mock_dense = Mock()
        mock_dense.id = "product_001"
        mock_dense.score = 0.9
        mock_dense.payload = {"name": "Product 1"}

        # Mock sparse results
        mock_sparse = Mock()
        mock_sparse.id = "product_001"
        mock_sparse.score = 0.8
        mock_sparse.payload = {"name": "Product 1"}

        mock_client.search = Mock(side_effect=[
            [mock_dense],  # Dense search result
            [mock_sparse]  # Sparse search result
        ])

        dense_vector = [0.1] * 768
        sparse_vector = {1: 0.5, 10: 0.3, 25: 0.2}

        results = self.service.hybrid_search(
            collection_name="test_collection",
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            top_k=5,
            alpha=0.7
        )

        assert len(results) > 0
        assert "dense_score" in results[0]
        assert "sparse_score" in results[0]
        assert "score" in results[0]

    def test_batch_upsert(self):
        """Test batch upsert"""
        mock_client = self.service.client
        mock_client.upsert = Mock()

        ids = ["prod_001", "prod_002", "prod_003"]
        vectors = [[0.1] * 768 for _ in range(3)]
        metadata_list = [
            {"name": "Product 1"},
            {"name": "Product 2"},
            {"name": "Product 3"}
        ]

        result_ids = self.service.upsert_batch(
            collection_name="test_collection",
            ids=ids,
            vectors=vectors,
            metadata_list=metadata_list,
            batch_size=2
        )

        assert result_ids == ids
        # Should be called twice (batch_size=2, 3 items = 2 batches)
        assert mock_client.upsert.call_count == 2

    def test_delete_vectors(self):
        """Test deleting vectors"""
        mock_client = self.service.client
        mock_client.delete = Mock()

        ids = ["prod_001", "prod_002"]
        result = self.service.delete(
            collection_name="test_collection",
            ids=ids
        )

        assert result == True
        mock_client.delete.assert_called_once()

    def test_get_collection_info(self):
        """Test getting collection info"""
        mock_client = self.service.client

        # Mock collection info
        mock_info = Mock()
        mock_info.points_count = 1000
        mock_info.status = "green"
        mock_info.config = Mock()
        mock_info.config.params = Mock()
        mock_info.config.params.vectors = {
            "dense": Mock(distance="cosine", size=768)
        }

        mock_client.get_collection = Mock(return_value=mock_info)

        info = self.service.get_collection_info("test_collection")

        assert info["name"] == "test_collection"
        assert info["vectors_count"] == 1000
        assert info["status"] == "green"

    def test_singleton_pattern(self):
        """Test singleton pattern"""
        with patch('src.services.vector_db_service.QdrantClient'):
            service1 = get_vector_db_service()
            service2 = get_vector_db_service()

            # Should return the same instance
            assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
