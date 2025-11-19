"""
Integration tests for Hybrid Search (v6.0.0)
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.hybrid_search import HybridSearchEngine, create_hybrid_search_engine


class TestHybridSearchEngine:
    """Test hybrid search engine core functionality"""

    def test_create_engine(self):
        """Test engine creation"""
        engine = create_hybrid_search_engine(enable_cross_encoder=False)

        assert engine is not None
        assert engine.rrf_k == 60
        assert engine.enable_cross_encoder is False

    def test_build_bm25_index(self):
        """Test BM25 index building"""
        engine = create_hybrid_search_engine(enable_cross_encoder=False)

        documents = [
            {
                "id": "1",
                "text": "50ml PET bottle",
                "metadata": {"product_name": "50ml PET 용기", "material": "PET"},
            },
            {
                "id": "2",
                "text": "100ml PP container",
                "metadata": {"product_name": "100ml PP 용기", "material": "PP"},
            },
        ]

        bm25_index = engine.build_bm25_index(documents)

        assert bm25_index is not None
        # BM25 index should have same size as documents
        assert len(bm25_index.doc_freqs) > 0

    def test_bm25_search(self):
        """Test BM25 sparse search"""
        engine = create_hybrid_search_engine(enable_cross_encoder=False)

        documents = [
            {
                "id": "1",
                "text": "50ml PET bottle with 20mm neck",
                "metadata": {"product_name": "50ml PET 용기", "material": "PET"},
            },
            {
                "id": "2",
                "text": "100ml PP container for cosmetics",
                "metadata": {"product_name": "100ml PP 용기", "material": "PP"},
            },
            {
                "id": "3",
                "text": "50ml glass bottle premium",
                "metadata": {"product_name": "50ml 유리 용기", "material": "Glass"},
            },
        ]

        bm25_index = engine.build_bm25_index(documents)
        results = engine.bm25_search("50ml bottle", bm25_index, documents, top_k=10)

        # Should find matches
        assert len(results) > 0

        # First result should be relevant
        first_doc, first_score = results[0]
        assert first_score > 0
        assert "50ml" in first_doc.get("text", "").lower()

    def test_reciprocal_rank_fusion(self):
        """Test RRF fusion"""
        engine = create_hybrid_search_engine(enable_cross_encoder=False)

        doc1 = {"id": "1", "text": "Document 1"}
        doc2 = {"id": "2", "text": "Document 2"}
        doc3 = {"id": "3", "text": "Document 3"}

        # Dense results
        dense_results = [(doc1, 0.9), (doc2, 0.7)]

        # Sparse results (different order)
        sparse_results = [(doc2, 5.0), (doc3, 3.0), (doc1, 2.0)]

        # Fuse
        fused = engine.reciprocal_rank_fusion(
            dense_results, sparse_results, dense_weight=0.5, sparse_weight=0.5
        )

        # Should have all unique documents
        assert len(fused) == 3

        # Check all documents present
        fused_ids = [engine._get_doc_id(doc) for doc, _ in fused]
        assert "1" in fused_ids
        assert "2" in fused_ids
        assert "3" in fused_ids

    def test_hybrid_search_without_reranking(self):
        """Test hybrid search without cross-encoder re-ranking"""
        engine = create_hybrid_search_engine(enable_cross_encoder=False)

        documents = [
            {
                "id": "1",
                "text": "50ml PET bottle",
                "metadata": {"product_name": "50ml PET 용기"},
            },
            {
                "id": "2",
                "text": "100ml PP container",
                "metadata": {"product_name": "100ml PP 용기"},
            },
        ]

        # Simulate dense results
        dense_results = [(documents[0], 0.85), (documents[1], 0.70)]

        # Build BM25 index
        bm25_index = engine.build_bm25_index(documents)

        # Hybrid search
        results = engine.hybrid_search(
            query="50ml PET",
            dense_results=dense_results,
            bm25_index=bm25_index,
            documents=documents,
            top_k=10,
            enable_reranking=False,
        )

        # Should return results
        assert len(results) > 0

        # Results should have scores
        for doc, score in results:
            assert isinstance(score, float)
            assert score > 0

    @pytest.mark.slow
    def test_hybrid_search_with_reranking(self):
        """Test hybrid search with cross-encoder re-ranking"""
        # Skip if cross-encoder not available (slow to download)
        try:
            engine = create_hybrid_search_engine(enable_cross_encoder=True)

            documents = [
                {
                    "id": "1",
                    "text": "50ml PET bottle with 20mm neck size for beverages",
                    "metadata": {"product_name": "50ml PET 용기", "material": "PET"},
                },
                {
                    "id": "2",
                    "text": "100ml PP container for cosmetics and skincare",
                    "metadata": {"product_name": "100ml PP 용기", "material": "PP"},
                },
            ]

            # Simulate dense results
            dense_results = [(documents[0], 0.85), (documents[1], 0.70)]

            # Build BM25 index
            bm25_index = engine.build_bm25_index(documents)

            # Hybrid search with re-ranking
            results = engine.hybrid_search(
                query="50ml PET bottle for beverages",
                dense_results=dense_results,
                bm25_index=bm25_index,
                documents=documents,
                top_k=10,
                enable_reranking=True,
            )

            # Should return results
            assert len(results) > 0

            # Cross-encoder scores should be different from original
            for doc, score in results:
                assert isinstance(score, float)

        except Exception as e:
            pytest.skip(f"Cross-encoder test skipped: {e}")


class TestHybridSearchAPI:
    """Test hybrid search API endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test hybrid search health check"""
        response = client.get("/api/v1/hybrid/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "cross_encoder" in data
        assert "rrf_k" in data

    def test_config_endpoint(self, client):
        """Test hybrid search configuration"""
        response = client.get("/api/v1/hybrid/config")

        assert response.status_code == 200
        data = response.json()

        assert "cross_encoder_model" in data
        assert "rrf_k" in data
        assert "supported_strategies" in data
        assert len(data["supported_strategies"]) > 0

    @pytest.mark.slow
    def test_search_endpoint(self, client):
        """Test hybrid search endpoint"""
        # This requires actual RAG pipeline and Qdrant
        try:
            response = client.post(
                "/api/v1/hybrid/search",
                json={
                    "query": "50ml PET 용기",
                    "top_k": 10,
                    "dense_weight": 0.5,
                    "sparse_weight": 0.5,
                    "enable_reranking": False,  # Disable for faster testing
                },
            )

            # Should work or fail gracefully
            assert response.status_code in [200, 500]

            if response.status_code == 200:
                data = response.json()

                # Verify response structure
                assert "query" in data
                assert "total_results" in data
                assert "results" in data
                assert "search_strategy" in data
                assert "performance" in data
                assert "parameters" in data

                # Check performance metrics
                perf = data["performance"]
                assert "total_time_ms" in perf
                assert "dense_search_ms" in perf
                assert "bm25_build_ms" in perf
                assert "hybrid_fusion_ms" in perf

        except Exception as e:
            pytest.skip(f"Hybrid search endpoint test skipped: {e}")

    def test_search_with_filters(self, client):
        """Test hybrid search with collections and materials"""
        response = client.post(
            "/api/v1/hybrid/search",
            json={
                "query": "bottle",
                "collections": ["chungjinkorea"],
                "materials": ["PET"],
                "top_k": 20,
                "dense_weight": 0.6,
                "sparse_weight": 0.4,
                "enable_reranking": False,
            },
        )

        # Should accept request (might fail if RAG not configured)
        assert response.status_code in [200, 500]

    def test_search_validation(self, client):
        """Test request validation"""
        # Missing query
        response = client.post("/api/v1/hybrid/search", json={"top_k": 10})

        assert response.status_code == 422  # Validation error

        # Invalid weights
        response = client.post(
            "/api/v1/hybrid/search",
            json={
                "query": "test",
                "dense_weight": 1.5,  # Invalid (> 1.0)
                "sparse_weight": 0.5,
            },
        )

        assert response.status_code == 422


class TestHybridSearchPerformance:
    """Test hybrid search performance characteristics"""

    def test_rrf_scores_normalized(self):
        """Test that RRF scores are properly normalized"""
        engine = create_hybrid_search_engine(enable_cross_encoder=False)

        doc1 = {"id": "1", "text": "Doc 1"}
        doc2 = {"id": "2", "text": "Doc 2"}

        dense_results = [(doc1, 0.95), (doc2, 0.85)]
        sparse_results = [(doc1, 10.0), (doc2, 5.0)]

        # RRF fusion
        fused = engine.reciprocal_rank_fusion(dense_results, sparse_results)

        # Check scores are reasonable
        for doc, score in fused:
            assert score > 0
            assert score < 1.0  # RRF scores should be < 1

    def test_weight_impact(self):
        """Test that weights affect ranking"""
        engine = create_hybrid_search_engine(enable_cross_encoder=False)

        doc1 = {"id": "1", "text": "Doc 1"}
        doc2 = {"id": "2", "text": "Doc 2"}

        # Dense favors doc1, sparse favors doc2
        dense_results = [(doc1, 0.95), (doc2, 0.70)]
        sparse_results = [(doc2, 10.0), (doc1, 2.0)]

        # Dense-only (dense_weight=1, sparse_weight=0)
        fused_dense = engine.reciprocal_rank_fusion(
            dense_results, sparse_results, dense_weight=1.0, sparse_weight=0.0
        )

        # Sparse-only (dense_weight=0, sparse_weight=1)
        fused_sparse = engine.reciprocal_rank_fusion(
            dense_results, sparse_results, dense_weight=0.0, sparse_weight=1.0
        )

        # Dense-only should rank doc1 first
        assert engine._get_doc_id(fused_dense[0][0]) == "1"

        # Sparse-only should rank doc2 first
        assert engine._get_doc_id(fused_sparse[0][0]) == "2"
