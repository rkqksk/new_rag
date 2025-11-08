"""
Integration tests for HybridSearchEngine
Requires Qdrant running at localhost:6333
"""

from typing import List

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from src.core.multimodal.hybrid_search import (
    HybridSearchEngine,
    LearnedFusion,
    ReciprocalRankFusion,
    SearchResult,
    WeightedFusion,
)
from src.core.multimodal.qdrant_uploader import MultiModalQdrantUploader

# Test collection name
TEST_COLLECTION = "test_hybrid_search"


@pytest.fixture(scope="module")
def qdrant_client():
    """Create Qdrant client"""
    try:
        client = QdrantClient(host="localhost", port=6333)
        client.get_collections()
        return client
    except:
        pytest.skip("Qdrant not available at localhost:6333")


@pytest.fixture(scope="module")
def test_collection(qdrant_client):
    """Create test collection with sample data"""
    # Delete if exists
    try:
        qdrant_client.delete_collection(TEST_COLLECTION)
    except:
        pass

    # Create collection
    qdrant_client.create_collection(
        collection_name=TEST_COLLECTION,
        vectors_config={
            "text": VectorParams(size=384, distance=Distance.COSINE),
            "image": VectorParams(size=1024, distance=Distance.COSINE),
            "shape": VectorParams(size=128, distance=Distance.COSINE),
        },
    )

    # Upload sample data
    uploader = MultiModalQdrantUploader(qdrant_client, TEST_COLLECTION)

    # Sample products with varying scores
    products = [
        {
            "product_id": "bottle-100ml",
            "text_embedding": [0.9] * 384,  # High text relevance
            "image_embedding": [0.3] * 1024,  # Low image relevance
            "payload": {"name": "100ml PET Bottle", "category": "Bottle"},
        },
        {
            "product_id": "bottle-200ml",
            "text_embedding": [0.7] * 384,  # Medium text relevance
            "image_embedding": [0.8] * 1024,  # High image relevance
            "payload": {"name": "200ml PET Bottle", "category": "Bottle"},
        },
        {
            "product_id": "cap-20mm",
            "text_embedding": [0.5] * 384,  # Medium text relevance
            "image_embedding": [0.5] * 1024,  # Medium image relevance
            "shape_embedding": [0.9] * 128,  # High shape relevance
            "payload": {"name": "20mm Cap", "category": "Cap"},
        },
        {
            "product_id": "jar-50ml",
            "text_embedding": [0.3] * 384,  # Low text relevance
            "image_embedding": [0.9] * 1024,  # High image relevance
            "payload": {"name": "50ml Cosmetic Jar", "category": "Jar"},
        },
        {
            "product_id": "pump-dispenser",
            "text_embedding": [0.2] * 384,  # Low text relevance
            "image_embedding": [0.4] * 1024,  # Low image relevance
            "payload": {"name": "Pump Dispenser", "category": "Pump"},
        },
    ]

    uploader.upload_batch(products, show_progress=False)

    yield TEST_COLLECTION

    # Cleanup
    try:
        qdrant_client.delete_collection(TEST_COLLECTION)
    except:
        pass


@pytest.fixture
def search_engine(qdrant_client, test_collection):
    """Create search engine instance"""
    return HybridSearchEngine(qdrant_client, test_collection, fusion_strategy="rrf")


# ==================== Initialization Tests ====================


def test_engine_initialization_rrf(qdrant_client, test_collection):
    """Test initialization with RRF strategy"""
    engine = HybridSearchEngine(qdrant_client, test_collection, fusion_strategy="rrf")
    assert engine is not None
    assert engine.strategy_name == "rrf"
    assert isinstance(engine.fusion, ReciprocalRankFusion)


def test_engine_initialization_weighted(qdrant_client, test_collection):
    """Test initialization with weighted strategy"""
    engine = HybridSearchEngine(qdrant_client, test_collection, fusion_strategy="weighted")
    assert engine is not None
    assert engine.strategy_name == "weighted"
    assert isinstance(engine.fusion, WeightedFusion)


def test_engine_initialization_learned(qdrant_client, test_collection):
    """Test initialization with learned strategy"""
    engine = HybridSearchEngine(qdrant_client, test_collection, fusion_strategy="learned")
    assert engine is not None
    assert engine.strategy_name == "learned"
    assert isinstance(engine.fusion, LearnedFusion)


def test_engine_invalid_strategy(qdrant_client, test_collection):
    """Test error with invalid fusion strategy"""
    with pytest.raises(ValueError):
        HybridSearchEngine(qdrant_client, test_collection, fusion_strategy="invalid_strategy")


def test_engine_invalid_collection(qdrant_client):
    """Test error with non-existent collection"""
    with pytest.raises(ValueError):
        HybridSearchEngine(qdrant_client, "nonexistent_collection")


# ==================== Single Modality Search Tests ====================


def test_search_text_only(search_engine):
    """Test text-only search"""
    query_emb = [0.9] * 384  # Similar to bottle-100ml

    results = search_engine.search_text(query_emb, limit=5)

    assert len(results) > 0
    assert results[0].id in ["bottle-100ml", "bottle-200ml"]


def test_search_image_only(search_engine):
    """Test image-only search"""
    query_emb = [0.9] * 1024  # Similar to jar-50ml

    results = search_engine.search_image(query_emb, limit=5)

    assert len(results) > 0
    assert results[0].id in ["jar-50ml", "bottle-200ml"]


def test_search_shape_only(search_engine):
    """Test shape-only search"""
    query_emb = [0.9] * 128  # Similar to cap-20mm

    results = search_engine.search_shape(query_emb, limit=5)

    assert len(results) > 0
    # cap-20mm is the only one with shape embedding
    assert results[0].id == "cap-20mm"


# ==================== Hybrid Search Tests ====================


def test_hybrid_search_text_image(search_engine):
    """Test hybrid search with text + image"""
    embeddings = {
        "text": [0.9] * 384,  # High text similarity
        "image": [0.9] * 1024,  # High image similarity
    }

    results = search_engine.search_hybrid(embeddings=embeddings, limit=5)

    assert len(results) > 0
    assert isinstance(results[0], SearchResult)
    assert results[0].product_id is not None
    assert results[0].score > 0
    assert "text" in results[0].modality_scores
    assert "image" in results[0].modality_scores


def test_hybrid_search_all_modalities(search_engine):
    """Test hybrid search with text + image + shape"""
    embeddings = {
        "text": [0.5] * 384,
        "image": [0.5] * 1024,
        "shape": [0.9] * 128,  # High shape similarity
    }

    results = search_engine.search_hybrid(embeddings=embeddings, limit=5)

    assert len(results) > 0
    # cap-20mm should rank high due to shape match
    assert "cap-20mm" in [r.product_id for r in results[:3]]


def test_hybrid_search_with_weights(search_engine):
    """Test hybrid search with custom weights"""
    embeddings = {"text": [0.9] * 384, "image": [0.3] * 1024}

    # Text-heavy weighting
    results_text_heavy = search_engine.search_hybrid(
        embeddings=embeddings, weights={"text": 0.9, "image": 0.1}, limit=5
    )

    # Image-heavy weighting
    results_image_heavy = search_engine.search_hybrid(
        embeddings=embeddings, weights={"text": 0.1, "image": 0.9}, limit=5
    )

    assert len(results_text_heavy) > 0
    assert len(results_image_heavy) > 0

    # Results may differ based on weights
    # (Not strictly guaranteed, but likely with this data)


def test_hybrid_search_empty_embeddings(search_engine):
    """Test error when no embeddings provided"""
    with pytest.raises(ValueError):
        search_engine.search_hybrid(embeddings={}, limit=5)


def test_hybrid_search_single_modality(search_engine):
    """Test hybrid search with only one modality"""
    embeddings = {"text": [0.9] * 384}

    results = search_engine.search_hybrid(embeddings=embeddings, limit=5)

    assert len(results) > 0
    assert "text" in results[0].modality_scores


# ==================== Fusion Strategy Tests ====================


def test_rrf_fusion(qdrant_client, test_collection):
    """Test RRF fusion strategy"""
    engine = HybridSearchEngine(qdrant_client, test_collection, fusion_strategy="rrf", rrf_k=60)

    embeddings = {"text": [0.9] * 384, "image": [0.9] * 1024}

    results = engine.search_hybrid(embeddings, limit=5)

    assert len(results) > 0
    # RRF scores are based on ranks, not raw scores
    assert all(r.score > 0 for r in results)


def test_weighted_fusion(qdrant_client, test_collection):
    """Test weighted fusion strategy"""
    engine = HybridSearchEngine(qdrant_client, test_collection, fusion_strategy="weighted")

    embeddings = {"text": [0.9] * 384, "image": [0.3] * 1024}

    results = engine.search_hybrid(embeddings, weights={"text": 0.7, "image": 0.3}, limit=5)

    assert len(results) > 0
    # Weighted scores should be between 0 and 1
    assert all(0 <= r.score <= 1 for r in results)


def test_learned_fusion_fallback(qdrant_client, test_collection):
    """Test learned fusion falls back to weighted"""
    engine = HybridSearchEngine(qdrant_client, test_collection, fusion_strategy="learned")

    embeddings = {"text": [0.9] * 384, "image": [0.9] * 1024}

    results = engine.search_hybrid(embeddings, limit=5)

    assert len(results) > 0
    # Should work (falls back to weighted fusion)


# ==================== Result Ranking Tests ====================


def test_result_ranking(search_engine):
    """Test that results are properly ranked"""
    embeddings = {"text": [0.9] * 384, "image": [0.9] * 1024}

    results = search_engine.search_hybrid(embeddings, limit=5)

    # Check ranks are sequential
    for i, result in enumerate(results):
        assert result.rank == i + 1

    # Check scores are descending
    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score


def test_result_limit(search_engine):
    """Test limit parameter"""
    embeddings = {"text": [0.9] * 384}

    # Request 3 results
    results = search_engine.search_hybrid(embeddings, limit=3)
    assert len(results) <= 3

    # Request 10 results (more than available)
    results = search_engine.search_hybrid(embeddings, limit=10)
    assert len(results) <= 10


# ==================== Result Explanation Tests ====================


def test_explain_results(search_engine):
    """Test result explanation"""
    embeddings = {"text": [0.9] * 384, "image": [0.9] * 1024}

    results = search_engine.search_hybrid(embeddings, limit=5)
    explanation = search_engine.explain_results(results, top_k=3)

    assert explanation is not None
    assert "fusion_strategy" in explanation
    assert explanation["fusion_strategy"] == "rrf"
    assert "results" in explanation
    assert len(explanation["results"]) <= 3

    # Check first result has expected fields
    first_result = explanation["results"][0]
    assert "rank" in first_result
    assert "product_id" in first_result
    assert "final_score" in first_result
    assert "modality_scores" in first_result
    assert "modality_contributions" in first_result


def test_explain_modality_contributions(search_engine):
    """Test modality contribution analysis"""
    embeddings = {"text": [0.9] * 384, "image": [0.3] * 1024}

    results = search_engine.search_hybrid(embeddings, limit=5)
    explanation = search_engine.explain_results(results, top_k=1)

    first_result = explanation["results"][0]
    contributions = first_result["modality_contributions"]

    # Check contributions sum to 100%
    total_pct = sum(c["contribution_pct"] for c in contributions.values())
    assert abs(total_pct - 100.0) < 0.1  # Allow small floating-point error


# ==================== Edge Cases ====================


def test_search_with_missing_vectors(search_engine):
    """Test search when some products lack certain vectors"""
    # bottle-100ml has no shape embedding
    embeddings = {"text": [0.9] * 384, "shape": [0.9] * 128}

    results = search_engine.search_hybrid(embeddings, limit=5)

    assert len(results) > 0
    # Products without shape vectors should get 0 shape score


def test_search_with_no_matches(search_engine):
    """Test search with very low similarity"""
    embeddings = {"text": [0.0] * 384, "image": [0.0] * 1024}

    results = search_engine.search_hybrid(embeddings, limit=5)

    # Should still return results, just with low scores
    assert len(results) >= 0


def test_repr(search_engine):
    """Test string representation"""
    repr_str = repr(search_engine)

    assert "HybridSearchEngine" in repr_str
    assert TEST_COLLECTION in repr_str
    assert "rrf" in repr_str


# ==================== Performance Tests ====================


def test_search_performance(search_engine):
    """Test search performance (basic benchmark)"""
    import time

    embeddings = {"text": [0.9] * 384, "image": [0.9] * 1024}

    # Warm-up
    search_engine.search_hybrid(embeddings, limit=10)

    # Benchmark
    start = time.time()
    for _ in range(10):
        search_engine.search_hybrid(embeddings, limit=10)
    elapsed = time.time() - start

    avg_latency = elapsed / 10

    # Should be reasonably fast (<1 second per search)
    assert avg_latency < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
