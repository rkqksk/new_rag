"""
Tests for End-to-End Multi-Modal Pipeline
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from src.core.multimodal.end_to_end_pipeline import (
    EndToEndPipeline,
    PipelineResult
)


@pytest.fixture
def mock_ocr_integration():
    """Create mock OCR integration"""
    integration = Mock()

    # Mock process_document
    integration.process_document.return_value = {
        'product_id': 'test-product',
        'source_file': 'test.jpg',
        'ocr_text': 'Sample OCR text',
        'ocr_confidence': 0.92,
        'embeddings': {
            'text': [0.1] * 384,
            'image': [0.2] * 1024
        },
        'metadata': {
            'filename': 'test.jpg',
            'file_type': '.jpg',
            'character_count': 15,
            'has_text_embedding': True,
            'has_image_embedding': True,
            'capacity': '100ml'
        }
    }

    # Mock embedder
    integration.embedder = Mock()
    integration.embedder.is_available.return_value = True
    integration.embedder.embed_text.return_value = [0.1] * 384
    integration.embedder.embed_image.return_value = [0.2] * 1024
    integration.embedder.get_dimensions.return_value = {'text': 384, 'image': 1024}

    # Mock OCR processor
    integration.ocr = Mock()
    integration.ocr.is_available.return_value = True
    integration.ocr.lang = 'korean'
    integration.ocr.use_gpu = True

    # Mock cache
    integration.get_cache_stats.return_value = {
        'enabled': True,
        'entries': 0,
        'size_mb': 0.0
    }

    return integration


@pytest.fixture
def mock_uploader():
    """Create mock Qdrant uploader"""
    uploader = Mock()
    uploader.collection_name = "products_multimodal"

    # Mock upload_product
    uploader.upload_product.return_value = True

    # Mock get_collection_stats
    uploader.get_collection_stats.return_value = {
        'points_count': 100,
        'vectors_count': 100,
        'indexed_vectors_count': 100
    }

    return uploader


@pytest.fixture
def mock_search_engine():
    """Create mock search engine"""
    engine = Mock()
    engine.strategy_name = "rrf"
    engine.collection_name = "products_multimodal"

    # Mock search_hybrid
    from src.core.multimodal.hybrid_search import SearchResult
    engine.search_hybrid.return_value = [
        SearchResult(
            product_id="result-1",
            score=0.95,
            payload={'name': 'Product 1'},
            modality_scores={'text': 0.9, 'image': 0.8},
            rank=1
        ),
        SearchResult(
            product_id="result-2",
            score=0.88,
            payload={'name': 'Product 2'},
            modality_scores={'text': 0.85, 'image': 0.75},
            rank=2
        )
    ]

    return engine


# ==================== Initialization Tests ====================

def test_pipeline_initialization(mock_ocr_integration, mock_uploader):
    """Test pipeline initialization"""
    pipeline = EndToEndPipeline(
        ocr_integration=mock_ocr_integration,
        qdrant_uploader=mock_uploader
    )

    assert pipeline is not None
    assert pipeline.ocr_integration == mock_ocr_integration
    assert pipeline.uploader == mock_uploader
    assert pipeline.search_engine is None


def test_pipeline_with_search_engine(mock_ocr_integration, mock_uploader, mock_search_engine):
    """Test pipeline with search engine"""
    pipeline = EndToEndPipeline(
        ocr_integration=mock_ocr_integration,
        qdrant_uploader=mock_uploader,
        search_engine=mock_search_engine
    )

    assert pipeline.search_engine == mock_search_engine


# ==================== Document Processing Tests ====================

def test_process_document_success(mock_ocr_integration, mock_uploader):
    """Test successful document processing"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader
    )

    # Create temp file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        result = pipeline.process_document(temp_path, upload=True)

        assert isinstance(result, PipelineResult)
        assert result.success == True
        assert result.product_id == 'test-product'
        assert result.ocr_text == 'Sample OCR text'
        assert 'text' in result.embeddings
        assert 'image' in result.embeddings

        # Verify uploader was called
        mock_uploader.upload_product.assert_called_once()

    finally:
        temp_path.unlink()


def test_process_document_without_upload(mock_ocr_integration, mock_uploader):
    """Test processing without uploading"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader
    )

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        result = pipeline.process_document(temp_path, upload=False)

        assert result.success == True
        # Uploader should not be called
        mock_uploader.upload_product.assert_not_called()

    finally:
        temp_path.unlink()


def test_process_document_with_error(mock_ocr_integration, mock_uploader):
    """Test document processing with error"""
    # Make OCR fail
    mock_ocr_integration.process_document.side_effect = Exception("OCR failed")

    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader
    )

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        result = pipeline.process_document(temp_path)

        assert result.success == False
        assert result.error == "OCR failed"

    finally:
        temp_path.unlink()


# ==================== Batch Processing Tests ====================

def test_process_and_upload_batch(mock_ocr_integration, mock_uploader):
    """Test batch processing and upload"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader
    )

    # Create temp files
    import tempfile
    temp_files = []
    for i in range(3):
        f = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_files.append(Path(f.name))
        f.close()

    try:
        results = pipeline.process_and_upload(
            temp_files,
            product_ids=['prod-1', 'prod-2', 'prod-3'],
            show_progress=False
        )

        assert len(results) == 3
        assert all(r.success for r in results)

        # Verify uploader called 3 times
        assert mock_uploader.upload_product.call_count == 3

    finally:
        for temp_file in temp_files:
            temp_file.unlink()


# ==================== Search Tests ====================

def test_search_text_only(mock_ocr_integration, mock_uploader, mock_search_engine):
    """Test text-only search"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader,
        mock_search_engine
    )

    results = pipeline.search("100ml bottle", limit=10)

    assert len(results) == 2
    assert results[0].product_id == "result-1"
    assert results[0].score == 0.95

    # Verify embedder called
    mock_ocr_integration.embedder.embed_text.assert_called_with("100ml bottle")


def test_search_with_image(mock_ocr_integration, mock_uploader, mock_search_engine):
    """Test search with text + image"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader,
        mock_search_engine
    )

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        results = pipeline.search(
            query="bottle",
            query_image=temp_path,
            limit=5
        )

        assert len(results) == 2

        # Verify both embedders called
        mock_ocr_integration.embedder.embed_text.assert_called()
        mock_ocr_integration.embedder.embed_image.assert_called()

    finally:
        temp_path.unlink()


def test_search_without_engine(mock_ocr_integration, mock_uploader):
    """Test search without search engine configured"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader,
        search_engine=None
    )

    with pytest.raises(RuntimeError, match="Search engine not configured"):
        pipeline.search("test query")


def test_search_by_document(mock_ocr_integration, mock_uploader, mock_search_engine):
    """Test search by document similarity"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader,
        mock_search_engine
    )

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        results = pipeline.search_by_document(temp_path, limit=5)

        assert len(results) == 2

        # Verify OCR integration called
        mock_ocr_integration.process_document.assert_called()

    finally:
        temp_path.unlink()


# ==================== Statistics & Validation Tests ====================

def test_get_statistics(mock_ocr_integration, mock_uploader, mock_search_engine):
    """Test get pipeline statistics"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader,
        mock_search_engine
    )

    stats = pipeline.get_statistics()

    assert 'ocr' in stats
    assert 'embeddings' in stats
    assert 'cache' in stats
    assert 'qdrant' in stats
    assert 'search' in stats

    assert stats['ocr']['available'] == True
    assert stats['ocr']['language'] == 'korean'
    assert stats['embeddings']['text_available'] == True
    assert stats['search']['fusion_strategy'] == 'rrf'


def test_validate_pipeline(mock_ocr_integration, mock_uploader):
    """Test pipeline validation"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader
    )

    validation = pipeline.validate_pipeline()

    assert 'ocr_available' in validation
    assert 'text_embedder_available' in validation
    assert 'qdrant_connected' in validation
    assert 'collection_exists' in validation
    assert 'pipeline_ready' in validation

    assert validation['ocr_available'] == True
    assert validation['text_embedder_available'] == True


def test_validate_pipeline_with_errors(mock_ocr_integration, mock_uploader):
    """Test validation when components fail"""
    # Make Qdrant fail
    mock_uploader.get_collection_stats.side_effect = Exception("Connection failed")

    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader
    )

    validation = pipeline.validate_pipeline()

    assert validation['qdrant_connected'] == False
    assert validation['collection_exists'] == False
    assert validation['pipeline_ready'] == False


def test_repr(mock_ocr_integration, mock_uploader, mock_search_engine):
    """Test string representation"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader,
        mock_search_engine
    )

    repr_str = repr(pipeline)

    assert "EndToEndPipeline" in repr_str
    assert "ocr=True" in repr_str
    assert "embedder=True" in repr_str
    assert "search=True" in repr_str


# ==================== Edge Cases ====================

def test_process_document_custom_product_id(mock_ocr_integration, mock_uploader):
    """Test processing with custom product ID"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader
    )

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        result = pipeline.process_document(
            temp_path,
            product_id="custom-id-123"
        )

        # OCR integration should receive custom ID
        mock_ocr_integration.process_document.assert_called_with(
            temp_path,
            product_id="custom-id-123"
        )

    finally:
        temp_path.unlink()


def test_search_with_custom_weights(mock_ocr_integration, mock_uploader, mock_search_engine):
    """Test search with custom modality weights"""
    pipeline = EndToEndPipeline(
        mock_ocr_integration,
        mock_uploader,
        mock_search_engine
    )

    weights = {"text": 0.7, "image": 0.3}

    pipeline.search(
        "test query",
        weights=weights,
        limit=5
    )

    # Verify search engine called with weights
    mock_search_engine.search_hybrid.assert_called()
    call_kwargs = mock_search_engine.search_hybrid.call_args.kwargs
    assert call_kwargs['weights'] == weights


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
