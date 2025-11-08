"""
Integration tests for MultiModalQdrantUploader
Requires Qdrant running at localhost:6333
"""

from typing import List

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from src.core.multimodal.qdrant_uploader import MultiModalQdrantUploader

# Test collection name (separate from production)
TEST_COLLECTION = "test_multimodal"


@pytest.fixture(scope="module")
def qdrant_client():
    """Create Qdrant client"""
    try:
        client = QdrantClient(host="localhost", port=6333)
        # Test connection
        client.get_collections()
        return client
    except:
        pytest.skip("Qdrant not available at localhost:6333")


@pytest.fixture(scope="module")
def test_collection(qdrant_client):
    """Create test collection"""
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

    yield TEST_COLLECTION

    # Cleanup
    try:
        qdrant_client.delete_collection(TEST_COLLECTION)
    except:
        pass


@pytest.fixture
def uploader(qdrant_client, test_collection):
    """Create uploader instance"""
    return MultiModalQdrantUploader(qdrant_client, test_collection)


# ==================== Initialization Tests ====================


def test_uploader_initialization(uploader):
    """Test uploader initialization"""
    assert uploader is not None
    assert uploader.collection_name == TEST_COLLECTION


def test_uploader_invalid_collection(qdrant_client):
    """Test initialization with invalid collection"""
    with pytest.raises(ValueError):
        MultiModalQdrantUploader(qdrant_client, "nonexistent_collection")


# ==================== Single Upload Tests ====================


def test_upload_text_only(uploader):
    """Test upload with text embedding only"""
    success = uploader.upload_product(
        product_id="test-text-001", text_embedding=[0.1] * 384, payload={"name": "Test Product"}
    )

    assert success == True

    # Verify
    product = uploader.get_product("test-text-001")
    assert product is not None
    assert "text" in product["vectors"]
    assert len(product["vectors"]["text"]) == 384


def test_upload_text_image(uploader):
    """Test upload with text + image embeddings"""
    success = uploader.upload_product(
        product_id="test-multi-001",
        text_embedding=[0.2] * 384,
        image_embedding=[0.3] * 1024,
        payload={"name": "Multi-modal Product"},
    )

    assert success == True

    # Verify
    product = uploader.get_product("test-multi-001")
    assert product is not None
    assert "text" in product["vectors"]
    assert "image" in product["vectors"]
    assert len(product["vectors"]["text"]) == 384
    assert len(product["vectors"]["image"]) == 1024


def test_upload_all_vectors(uploader):
    """Test upload with all three vectors"""
    success = uploader.upload_product(
        product_id="test-all-001",
        text_embedding=[0.4] * 384,
        image_embedding=[0.5] * 1024,
        shape_embedding=[0.6] * 128,
        payload={"name": "Full Multi-modal"},
    )

    assert success == True

    # Verify
    product = uploader.get_product("test-all-001")
    assert product is not None
    assert "text" in product["vectors"]
    assert "image" in product["vectors"]
    assert "shape" in product["vectors"]


def test_upload_no_embeddings(uploader):
    """Test error when no embeddings provided"""
    with pytest.raises(ValueError):
        uploader.upload_product(product_id="test-empty-001", payload={"name": "Empty"})


def test_upload_wrong_dimension(uploader):
    """Test error with wrong vector dimension"""
    with pytest.raises(ValueError):
        uploader.upload_product(
            product_id="test-wrong-001", text_embedding=[0.1] * 100  # Wrong: should be 384
        )


# ==================== Batch Upload Tests ====================


def test_batch_upload(uploader):
    """Test batch upload"""
    products = [
        {
            "product_id": f"batch-{i:03d}",
            "text_embedding": [0.1 * i] * 384,
            "payload": {"name": f"Product {i}"},
        }
        for i in range(10)
    ]

    stats = uploader.upload_batch(products, show_progress=False)

    assert stats["success"] == 10
    assert stats["failed"] == 0
    assert stats["total"] == 10


def test_batch_upload_large(uploader):
    """Test large batch upload"""
    products = [
        {
            "product_id": f"large-{i:04d}",
            "text_embedding": [0.01 * i] * 384,
            "payload": {"index": i},
        }
        for i in range(250)  # 2.5 batches (batch_size=100)
    ]

    stats = uploader.upload_batch(products, batch_size=100, show_progress=False)

    assert stats["success"] == 250
    assert stats["total"] == 250


def test_batch_upload_mixed(uploader):
    """Test batch with mixed vector types"""
    products = [
        # Text only
        {
            "product_id": "mixed-001",
            "text_embedding": [0.1] * 384,
            "payload": {"type": "text_only"},
        },
        # Text + Image
        {
            "product_id": "mixed-002",
            "text_embedding": [0.2] * 384,
            "image_embedding": [0.3] * 1024,
            "payload": {"type": "text_image"},
        },
        # All three
        {
            "product_id": "mixed-003",
            "text_embedding": [0.4] * 384,
            "image_embedding": [0.5] * 1024,
            "shape_embedding": [0.6] * 128,
            "payload": {"type": "all"},
        },
    ]

    stats = uploader.upload_batch(products, show_progress=False)

    assert stats["success"] == 3

    # Verify each
    p1 = uploader.get_product("mixed-001")
    assert "text" in p1["vectors"]
    assert "image" not in p1["vectors"]

    p2 = uploader.get_product("mixed-002")
    assert "text" in p2["vectors"]
    assert "image" in p2["vectors"]

    p3 = uploader.get_product("mixed-003")
    assert "text" in p3["vectors"]
    assert "image" in p3["vectors"]
    assert "shape" in p3["vectors"]


# ==================== Retrieval Tests ====================


def test_get_product(uploader):
    """Test product retrieval"""
    # Upload
    uploader.upload_product(
        product_id="retrieve-001", text_embedding=[0.7] * 384, payload={"name": "Retrieve Test"}
    )

    # Retrieve
    product = uploader.get_product("retrieve-001")

    assert product is not None
    assert product["id"] == "retrieve-001"
    assert "text" in product["vectors"]
    assert product["payload"]["name"] == "Retrieve Test"


def test_get_product_not_found(uploader):
    """Test retrieval of non-existent product"""
    product = uploader.get_product("nonexistent-999")
    assert product is None


# ==================== Deletion Tests ====================


def test_delete_product(uploader):
    """Test product deletion"""
    # Upload
    uploader.upload_product(
        product_id="delete-001", text_embedding=[0.8] * 384, payload={"name": "To Delete"}
    )

    # Verify exists
    product = uploader.get_product("delete-001")
    assert product is not None

    # Delete
    success = uploader.delete_product("delete-001")
    assert success == True

    # Verify deleted
    product = uploader.get_product("delete-001")
    assert product is None


# ==================== Statistics Tests ====================


def test_collection_stats(uploader):
    """Test collection statistics"""
    stats = uploader.get_collection_stats()

    assert "collection_name" in stats
    assert stats["collection_name"] == TEST_COLLECTION
    assert "points_count" in stats
    assert "vectors" in stats
    assert "text" in stats["vectors"]
    assert "image" in stats["vectors"]
    assert "shape" in stats["vectors"]


# ==================== Metadata Tests ====================


def test_metadata_auto_added(uploader):
    """Test that metadata is automatically added"""
    uploader.upload_product(
        product_id="meta-001", text_embedding=[0.9] * 384, payload={"name": "Metadata Test"}
    )

    product = uploader.get_product("meta-001")

    # Check auto-added metadata
    assert "product_id" in product["payload"]
    assert "uploaded_at" in product["payload"]
    assert "vector_types" in product["payload"]
    assert "text" in product["payload"]["vector_types"]


# ==================== Edge Cases ====================


def test_upload_with_special_characters(uploader):
    """Test upload with special characters in payload"""
    uploader.upload_product(
        product_id="special-001",
        text_embedding=[0.1] * 384,
        payload={"name": "제품명: 20파이 캡", "spec": "Ø20, MOQ: 5,000개", "price": "₩1,500"},
    )

    product = uploader.get_product("special-001")
    assert product is not None
    assert "제품명" in product["payload"]["name"]


def test_repr(uploader):
    """Test string representation"""
    repr_str = repr(uploader)

    assert "MultiModalQdrantUploader" in repr_str
    assert TEST_COLLECTION in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
