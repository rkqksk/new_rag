"""
Unit tests for Multi-Modal Embedding Service
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from src.core.multimodal.multimodal_embedder import MultiModalEmbeddingService, create_embedder

# ==================== Fixtures ====================


@pytest.fixture
def embedder():
    """Create embedder with text only (no image for CI/CD)"""
    return MultiModalEmbeddingService(enable_image=False)


@pytest.fixture
def embedder_full():
    """Create full embedder with image support"""
    try:
        embedder = MultiModalEmbeddingService(enable_image=True)
        return embedder
    except:
        pytest.skip("OpenCLIP not available")


@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        # Create a simple RGB image
        img = Image.new("RGB", (224, 224), color="red")
        img.save(f.name)
        yield f.name
        # Cleanup
        os.unlink(f.name)


# ==================== Text Embedding Tests ====================


def test_embedder_initialization(embedder):
    """Test basic initialization"""
    assert embedder is not None
    assert embedder.text_dim == 384
    assert embedder.device in ["cpu", "cuda", "mps"]


def test_text_embedding_single(embedder):
    """Test single text embedding"""
    text = "20파이 캡 5000개"
    embedding = embedder.embed_text(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)


def test_text_embedding_batch(embedder):
    """Test batch text embedding"""
    texts = ["20파이 캡", "100ml PET 보틀", "화장품 용기"]

    embeddings = embedder.embed_texts_batch(texts, show_progress=False)

    assert len(embeddings) == 3
    assert all(len(emb) == 384 for emb in embeddings)


def test_text_embedding_empty():
    """Test error handling for empty text"""
    embedder = MultiModalEmbeddingService(enable_image=False)

    with pytest.raises(ValueError):
        embedder.embed_text("")


def test_text_embedding_korean(embedder):
    """Test Korean text embedding"""
    korean_texts = ["제품코드: PE-001234", "SPEC: 100ml, Ø20", "MOQ: 5000개"]

    for text in korean_texts:
        embedding = embedder.embed_text(text)
        assert len(embedding) == 384


# ==================== Image Embedding Tests ====================


def test_image_embedding_single(embedder_full, sample_image):
    """Test single image embedding"""
    embedding = embedder_full.embed_image(sample_image)

    assert isinstance(embedding, list)
    assert len(embedding) == 1024  # OpenCLIP ViT-H-14 dimension
    assert all(isinstance(x, float) for x in embedding)


def test_image_embedding_not_found(embedder_full):
    """Test error handling for missing image"""
    with pytest.raises(FileNotFoundError):
        embedder_full.embed_image("nonexistent.jpg")


def test_image_embedding_disabled():
    """Test image embedding when disabled"""
    embedder = MultiModalEmbeddingService(enable_image=False)

    with pytest.raises(ValueError):
        embedder.embed_image("test.jpg")


# ==================== Multi-Modal Embedding Tests ====================


def test_multimodal_text_only(embedder):
    """Test multi-modal with text only"""
    embeddings = embedder.embed(text="20파이 캡")

    assert "text" in embeddings
    assert len(embeddings["text"]) == 384
    assert "image" not in embeddings


def test_multimodal_full(embedder_full, sample_image):
    """Test multi-modal with text and image"""
    embeddings = embedder_full.embed(text="100ml PET bottle", image=sample_image)

    assert "text" in embeddings
    assert "image" in embeddings
    assert len(embeddings["text"]) == 384
    assert len(embeddings["image"]) == 1024


def test_multimodal_no_input(embedder):
    """Test error when no input provided"""
    with pytest.raises(ValueError):
        embedder.embed()


def test_multimodal_batch(embedder):
    """Test batch multi-modal embedding"""
    items = [{"text": "20파이 캡"}, {"text": "100ml 보틀"}, {"text": "화장품 용기"}]

    embeddings = embedder.embed_batch(items, show_progress=False)

    assert len(embeddings) == 3
    assert all("text" in emb for emb in embeddings)
    assert all(len(emb["text"]) == 384 for emb in embeddings)


# ==================== Utility Methods Tests ====================


def test_get_dimensions(embedder):
    """Test get_dimensions method"""
    dims = embedder.get_dimensions()

    assert "text" in dims
    assert dims["text"] == 384


def test_get_dimensions_full(embedder_full):
    """Test get_dimensions with image"""
    dims = embedder_full.get_dimensions()

    assert "text" in dims
    assert "image" in dims
    assert dims["text"] == 384
    assert dims["image"] == 1024


def test_is_available(embedder):
    """Test is_available method"""
    assert embedder.is_available("text") == True
    assert embedder.is_available("image") == False
    assert embedder.is_available("shape") == False


def test_is_available_full(embedder_full):
    """Test is_available with image enabled"""
    assert embedder_full.is_available("text") == True
    assert embedder_full.is_available("image") == True
    assert embedder_full.is_available("shape") == False


# ==================== Device Tests ====================


def test_device_auto():
    """Test auto device detection"""
    embedder = MultiModalEmbeddingService(device="auto", enable_image=False)

    assert embedder.device in ["cpu", "cuda", "mps"]


def test_device_cpu():
    """Test CPU device"""
    embedder = MultiModalEmbeddingService(device="cpu", enable_image=False)

    assert embedder.device == "cpu"


# ==================== Convenience Function Tests ====================


def test_create_embedder():
    """Test create_embedder convenience function"""
    embedder = create_embedder(enable_image=False)

    assert isinstance(embedder, MultiModalEmbeddingService)
    assert embedder.text_dim == 384


# ==================== Representation Tests ====================


def test_repr(embedder):
    """Test string representation"""
    repr_str = repr(embedder)

    assert "MultiModalEmbeddingService" in repr_str
    assert "text=384d" in repr_str
    assert "device=" in repr_str


# ==================== Performance Tests ====================


@pytest.mark.slow
def test_batch_performance(embedder):
    """Test batch processing performance"""
    texts = [f"Product {i}" for i in range(100)]

    # Batch should be faster than individual
    embeddings = embedder.embed_texts_batch(texts, batch_size=32, show_progress=False)

    assert len(embeddings) == 100
    assert all(len(emb) == 384 for emb in embeddings)


# ==================== Edge Cases ====================


def test_very_long_text(embedder):
    """Test embedding very long text"""
    long_text = " ".join(["word"] * 1000)  # 1000 words

    embedding = embedder.embed_text(long_text)

    assert len(embedding) == 384


def test_special_characters(embedder):
    """Test text with special characters"""
    texts = ["제품코드: PE-001234!@#$%", "100ml (± 5ml)", "Ø20 파이 / 28파이"]

    for text in texts:
        embedding = embedder.embed_text(text)
        assert len(embedding) == 384


def test_empty_batch(embedder):
    """Test empty batch"""
    embeddings = embedder.embed_texts_batch([], show_progress=False)

    assert embeddings == []


# ==================== Integration Tests ====================


def test_end_to_end_workflow(embedder):
    """Test end-to-end workflow"""
    # Product data
    product = {
        "product_name": "100ml PET Bottle",
        "category": "Bottle",
        "specifications": "Capacity: 100ml, Neck: Ø20",
    }

    # Generate text
    text = f"{product['product_name']} {product['specifications']}"

    # Embed
    embedding = embedder.embed_text(text)

    # Validate
    assert len(embedding) == 384
    assert all(-1.0 <= x <= 1.0 for x in embedding)  # Normalized vectors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
