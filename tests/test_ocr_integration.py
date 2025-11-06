"""
Tests for OCR Integration
Note: Requires PaddleOCR installed for full functionality
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.multimodal.ocr_integration import (
    OCRProcessor,
    OCRMultiModalIntegration,
    OCRResult
)


# ==================== OCRProcessor Tests ====================

def test_ocr_processor_initialization():
    """Test OCR processor initialization"""
    processor = OCRProcessor(lang='korean', use_gpu=False)

    assert processor is not None
    assert processor.lang == 'korean'
    assert processor.use_gpu == False


def test_ocr_processor_availability():
    """Test OCR availability check"""
    processor = OCRProcessor(use_gpu=False)

    # Availability depends on whether PaddleOCR is installed
    # Just check it returns a boolean
    assert isinstance(processor.is_available(), bool)


@pytest.mark.skipif(
    not Path("tests/fixtures/sample_image.jpg").exists(),
    reason="Sample image not available"
)
def test_process_image_with_real_image():
    """Test processing real image (if available)"""
    processor = OCRProcessor(use_gpu=False)

    if not processor.is_available():
        pytest.skip("PaddleOCR not installed")

    result = processor.process_image("tests/fixtures/sample_image.jpg")

    assert isinstance(result, OCRResult)
    assert result.text is not None
    assert result.confidence >= 0.0
    assert result.source_file.endswith("sample_image.jpg")


def test_process_image_file_not_found():
    """Test error when image file doesn't exist"""
    processor = OCRProcessor(use_gpu=False)

    if not processor.is_available():
        pytest.skip("PaddleOCR not installed")

    with pytest.raises(FileNotFoundError):
        processor.process_image("nonexistent_image.jpg")


@patch('src.core.multimodal.ocr_integration.PaddleOCR')
def test_process_image_with_mock(mock_paddle_ocr):
    """Test image processing with mocked PaddleOCR"""
    # Setup mock
    mock_ocr_instance = MagicMock()
    mock_paddle_ocr.return_value = mock_ocr_instance

    # Mock OCR result
    mock_ocr_instance.ocr.return_value = [[
        ([
            [0, 0], [100, 0], [100, 50], [0, 50]
        ], ("Sample Text", 0.95)),
        ([
            [0, 60], [100, 60], [100, 110], [0, 110]
        ], ("Another Line", 0.88))
    ]]

    # Create processor (will use mock)
    with patch('src.core.multimodal.ocr_integration.logger'):
        processor = OCRProcessor(use_gpu=False)

    # Create a temp image file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        # Process image
        result = processor.process_image(temp_path)

        assert result.text == "Sample Text\nAnother Line"
        assert result.confidence > 0.0
        assert result.metadata['line_count'] == 2

    finally:
        temp_path.unlink()


# ==================== OCRMultiModalIntegration Tests ====================

@pytest.fixture
def mock_ocr_processor():
    """Create mock OCR processor"""
    processor = Mock(spec=OCRProcessor)
    processor.is_available.return_value = True

    # Mock process_image
    processor.process_image.return_value = OCRResult(
        text="100ml PET Bottle\nMOQ: 5000\nPrice: 100원",
        confidence=0.92,
        metadata={'line_count': 3},
        source_file="sample.jpg",
        bounding_boxes=[]
    )

    # Mock process_pdf
    processor.process_pdf.return_value = [
        OCRResult(
            text="Page 1 content",
            confidence=0.90,
            metadata={'line_count': 1},
            source_file="sample.pdf",
            page_number=1
        )
    ]

    return processor


@pytest.fixture
def mock_embedder():
    """Create mock embedding service"""
    embedder = Mock()
    embedder.is_available.return_value = True

    # Mock embed_text
    embedder.embed_text.return_value = [0.1] * 384

    # Mock embed_image
    embedder.embed_image.return_value = [0.2] * 1024

    return embedder


def test_integration_initialization(mock_ocr_processor, mock_embedder):
    """Test OCR integration initialization"""
    integration = OCRMultiModalIntegration(
        mock_ocr_processor,
        mock_embedder,
        cache_embeddings=True
    )

    assert integration is not None
    assert integration.cache_embeddings == True


def test_process_document_image(mock_ocr_processor, mock_embedder):
    """Test processing image document"""
    integration = OCRMultiModalIntegration(
        mock_ocr_processor,
        mock_embedder,
        cache_embeddings=False
    )

    # Create temp image
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        result = integration.process_document(
            temp_path,
            product_id="test-product"
        )

        assert result['product_id'] == "test-product"
        assert 'ocr_text' in result
        assert 'embeddings' in result
        assert 'text' in result['embeddings']
        assert result['metadata']['has_text_embedding'] == True

    finally:
        temp_path.unlink()


def test_process_document_with_metadata_extraction(mock_ocr_processor, mock_embedder):
    """Test metadata extraction from OCR text"""
    integration = OCRMultiModalIntegration(
        mock_ocr_processor,
        mock_embedder
    )

    # Create temp file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        result = integration.process_document(temp_path, extract_metadata=True)

        # Check extracted metadata
        metadata = result['metadata']
        assert 'capacity' in metadata  # Should extract "100ml"
        assert 'moq' in metadata  # Should extract 5000
        assert 'material' in metadata  # Should extract "PET"

    finally:
        temp_path.unlink()


def test_process_batch(mock_ocr_processor, mock_embedder):
    """Test batch processing"""
    integration = OCRMultiModalIntegration(
        mock_ocr_processor,
        mock_embedder
    )

    # Create temp files
    import tempfile
    temp_files = []
    for i in range(3):
        f = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_files.append(Path(f.name))
        f.close()

    try:
        results = integration.process_batch(
            temp_files,
            product_ids=['prod-1', 'prod-2', 'prod-3'],
            show_progress=False
        )

        assert len(results) == 3
        assert results[0]['product_id'] == 'prod-1'
        assert results[1]['product_id'] == 'prod-2'
        assert results[2]['product_id'] == 'prod-3'

    finally:
        for temp_file in temp_files:
            temp_file.unlink()


def test_embedding_cache(mock_ocr_processor, mock_embedder):
    """Test embedding caching"""
    integration = OCRMultiModalIntegration(
        mock_ocr_processor,
        mock_embedder,
        cache_embeddings=True
    )

    # Create temp file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        # First call - should generate embeddings
        result1 = integration.process_document(temp_path)

        # Second call - should use cache
        result2 = integration.process_document(temp_path)

        # Should be same result (from cache)
        assert result1 == result2

        # Check cache stats
        stats = integration.get_cache_stats()
        assert stats['enabled'] == True
        assert stats['entries'] == 1

        # Clear cache
        integration.clear_cache()
        stats = integration.get_cache_stats()
        assert stats['entries'] == 0

    finally:
        temp_path.unlink()


def test_metadata_extraction():
    """Test product metadata extraction patterns"""
    integration = OCRMultiModalIntegration(
        Mock(),
        Mock()
    )

    # Test capacity extraction
    text = "This is a 100ml bottle for cosmetics"
    metadata = integration._extract_product_metadata(text)
    assert metadata['capacity'] == "100ml"

    # Test MOQ extraction
    text = "MOQ: 5000 pieces minimum order"
    metadata = integration._extract_product_metadata(text)
    assert metadata['moq'] == 5000

    # Test material extraction
    text = "Made of PET plastic material"
    metadata = integration._extract_product_metadata(text)
    assert metadata['material'] == "PET"

    # Test product code extraction
    text = "Product code: PET-100 for reference"
    metadata = integration._extract_product_metadata(text)
    assert metadata['product_code'] == "PET-100"


# ==================== Edge Cases ====================

def test_ocr_processor_without_paddleocr():
    """Test OCR processor when PaddleOCR not installed"""
    with patch('src.core.multimodal.ocr_integration.PaddleOCR', side_effect=ImportError):
        with patch('src.core.multimodal.ocr_integration.logger'):
            processor = OCRProcessor()

        assert processor.is_available() == False


def test_integration_without_image_embedder(mock_ocr_processor):
    """Test integration when image embedding not available"""
    embedder = Mock()
    embedder.is_available.return_value = False
    embedder.embed_text.return_value = [0.1] * 384

    integration = OCRMultiModalIntegration(
        mock_ocr_processor,
        embedder
    )

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = Path(f.name)

    try:
        result = integration.process_document(temp_path)

        # Should have text embedding but not image
        assert 'text' in result['embeddings']
        assert 'image' not in result['embeddings']
        assert result['metadata']['has_text_embedding'] == True
        assert result['metadata']['has_image_embedding'] == False

    finally:
        temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
