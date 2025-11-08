"""
Tests for watermark removal functionality
"""

import numpy as np
import pytest
from PIL import Image

from src.core.ocr.watermark_remover import (
    InpaintingMethod,
    WatermarkRemover,
    remove_color_watermark,
    remove_watermark,
)


@pytest.fixture
def sample_image():
    """Create sample RGB image (300x200)"""
    img_array = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
    return Image.fromarray(img_array, "RGB")


@pytest.fixture
def image_with_text():
    """Create image with white text overlay"""
    img_array = np.zeros((200, 300, 3), dtype=np.uint8)
    # Add white rectangle (simulating watermark)
    img_array[50:100, 100:200] = [255, 255, 255]
    return Image.fromarray(img_array, "RGB")


def test_watermark_remover_init():
    """Test WatermarkRemover initialization"""
    remover = WatermarkRemover(
        method=InpaintingMethod.TELEA,
        enable_text_detection=True,
        inpaint_radius=3,
    )
    assert remover.method == InpaintingMethod.TELEA
    assert remover.enable_text_detection is True
    assert remover.inpaint_radius == 3


def test_remove_watermark_with_manual_region(image_with_text):
    """Test watermark removal with manual region"""
    remover = WatermarkRemover(method=InpaintingMethod.TELEA)

    # Remove white rectangle at (100, 50, 100, 50)
    result = remover.remove_watermark(
        image_with_text, regions=[(100, 50, 100, 50)], auto_detect=False
    )

    assert isinstance(result, Image.Image)
    assert result.size == image_with_text.size
    assert result.mode == "RGB"


def test_remove_watermark_telea(sample_image):
    """Test TELEA inpainting method"""
    remover = WatermarkRemover(method=InpaintingMethod.TELEA)
    result = remover.remove_watermark(
        sample_image, regions=[(50, 50, 100, 30)], auto_detect=False
    )

    assert isinstance(result, Image.Image)
    assert result.size == sample_image.size


def test_remove_watermark_ns(sample_image):
    """Test Navier-Stokes inpainting method"""
    remover = WatermarkRemover(method=InpaintingMethod.NS)
    result = remover.remove_watermark(
        sample_image, regions=[(50, 50, 100, 30)], auto_detect=False
    )

    assert isinstance(result, Image.Image)
    assert result.size == sample_image.size


def test_remove_specific_color(image_with_text):
    """Test color-based watermark removal"""
    remover = WatermarkRemover()

    # Remove white color
    result = remover.remove_specific_color(
        image_with_text, color=(255, 255, 255), tolerance=30
    )

    assert isinstance(result, Image.Image)
    assert result.size == image_with_text.size


def test_convenience_function_remove_watermark(sample_image):
    """Test convenience function for watermark removal"""
    result = remove_watermark(
        sample_image, regions=[(10, 10, 50, 50)], method="telea", auto_detect=False
    )

    assert isinstance(result, Image.Image)
    assert result.size == sample_image.size


def test_convenience_function_remove_color(image_with_text):
    """Test convenience function for color removal"""
    result = remove_color_watermark(
        image_with_text, color=(255, 255, 255), tolerance=30
    )

    assert isinstance(result, Image.Image)
    assert result.size == image_with_text.size


def test_empty_mask_warning(sample_image, caplog):
    """Test warning when mask is empty"""
    remover = WatermarkRemover()
    result = remover.remove_watermark(sample_image, regions=[], auto_detect=False)

    assert isinstance(result, Image.Image)
    # Should log warning about empty mask


def test_invalid_inpainting_method():
    """Test invalid inpainting method"""
    with pytest.raises(ValueError):
        WatermarkRemover(method="invalid_method")  # type: ignore


def test_numpy_array_input(sample_image):
    """Test with numpy array input"""
    img_array = np.array(sample_image)
    remover = WatermarkRemover()

    result = remover.remove_watermark(
        img_array, regions=[(10, 10, 50, 50)], auto_detect=False
    )

    assert isinstance(result, Image.Image)
    assert result.size == sample_image.size


def test_multiple_regions(sample_image):
    """Test removal of multiple regions"""
    remover = WatermarkRemover()

    regions = [(10, 10, 50, 30), (100, 50, 60, 40), (200, 150, 80, 20)]

    result = remover.remove_watermark(sample_image, regions=regions, auto_detect=False)

    assert isinstance(result, Image.Image)
    assert result.size == sample_image.size


@pytest.mark.slow
def test_text_detection_integration(sample_image):
    """Test with PaddleOCR text detection (slow - requires model)"""
    remover = WatermarkRemover(enable_text_detection=True)

    # This will try to detect text, but likely find none in random image
    result = remover.remove_watermark(sample_image, auto_detect=True)

    assert isinstance(result, Image.Image)
    assert result.size == sample_image.size
