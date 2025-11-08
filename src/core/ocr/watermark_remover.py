"""Watermark and Text Removal from Images

100% Open-Source implementation using:
- OpenCV Inpainting (fast, good quality)
- PaddleOCR (text detection)
- Optional: LaMa model (high quality, requires download)
"""

import logging
from enum import Enum
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class InpaintingMethod(str, Enum):
    """Inpainting algorithms"""

    TELEA = "telea"  # Fast, good for thin structures
    NS = "ns"  # Navier-Stokes, slower but better quality
    LAMA = "lama"  # State-of-the-art (requires model download)


class WatermarkRemover:
    """
    Remove watermarks, text overlays, and unwanted elements from images.

    Features:
    - Automatic text detection using PaddleOCR
    - Manual mask specification (x, y, width, height)
    - Multiple inpainting algorithms (OpenCV TELEA, NS, LaMa)
    - Batch processing support

    Cost: $0/month (100% open-source)
    """

    def __init__(
        self,
        method: InpaintingMethod = InpaintingMethod.TELEA,
        enable_text_detection: bool = True,
        inpaint_radius: int = 3,
        text_threshold: float = 0.3,
    ):
        """
        Initialize WatermarkRemover.

        Args:
            method: Inpainting algorithm to use
            enable_text_detection: Auto-detect text regions
            inpaint_radius: Radius of circular neighborhood for inpainting
            text_threshold: Confidence threshold for text detection (0.0-1.0)
        """
        self.method = method
        self.enable_text_detection = enable_text_detection
        self.inpaint_radius = inpaint_radius
        self.text_threshold = text_threshold
        self._ocr_model = None

    def remove_watermark(
        self,
        image: Union[Image.Image, np.ndarray],
        regions: Optional[List[Tuple[int, int, int, int]]] = None,
        auto_detect: bool = True,
    ) -> Image.Image:
        """
        Remove watermarks and text from image.

        Args:
            image: PIL Image or numpy array
            regions: Manual regions to remove [(x, y, width, height), ...]
            auto_detect: Automatically detect text regions

        Returns:
            PIL Image with watermarks removed

        Example:
            >>> remover = WatermarkRemover()
            >>> # Automatic detection
            >>> clean_img = remover.remove_watermark(image)
            >>> # Manual regions
            >>> clean_img = remover.remove_watermark(
            ...     image,
            ...     regions=[(100, 50, 200, 30)],  # x, y, w, h
            ...     auto_detect=False
            ... )
        """
        # Convert to OpenCV format
        img_cv = self._to_cv2(image)
        h, w = img_cv.shape[:2]

        # Create mask
        mask = np.zeros((h, w), dtype=np.uint8)

        # Add manual regions to mask
        if regions:
            for x, y, width, height in regions:
                cv2.rectangle(mask, (x, y), (x + width, y + height), 255, -1)
                logger.info(f"Manual region added: ({x}, {y}, {width}, {height})")

        # Auto-detect text regions
        if auto_detect and self.enable_text_detection:
            text_boxes = self._detect_text_regions(img_cv)
            for box in text_boxes:
                x, y, w_box, h_box = box
                cv2.rectangle(mask, (x, y), (x + w_box, y + h_box), 255, -1)
                logger.info(f"Auto-detected region: ({x}, {y}, {w_box}, {h_box})")

        # Check if mask is empty
        if mask.max() == 0:
            logger.warning("No regions to remove (mask is empty)")
            return self._to_pil(img_cv)

        # Apply inpainting
        result = self._inpaint(img_cv, mask)

        return self._to_pil(result)

    def _detect_text_regions(
        self, img: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        Detect text regions using PaddleOCR.

        Args:
            img: OpenCV image

        Returns:
            List of bounding boxes [(x, y, width, height), ...]
        """
        try:
            from paddleocr import PaddleOCR

            # Initialize OCR model (cached)
            if self._ocr_model is None:
                self._ocr_model = PaddleOCR(
                    use_angle_cls=True,
                    lang="en",  # Support: en, ch, korean
                    show_log=False,
                )

            # Run OCR
            result = self._ocr_model.ocr(img, cls=True)

            if not result or not result[0]:
                logger.info("No text detected")
                return []

            # Extract bounding boxes
            boxes = []
            for line in result[0]:
                # line[0] = [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                # line[1] = (text, confidence)
                points = line[0]
                text, confidence = line[1]

                if confidence < self.text_threshold:
                    continue

                # Convert polygon to bounding box
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]

                x_min = int(min(x_coords))
                y_min = int(min(y_coords))
                x_max = int(max(x_coords))
                y_max = int(max(y_coords))

                # Add margin (10% on each side)
                margin_x = int((x_max - x_min) * 0.1)
                margin_y = int((y_max - y_min) * 0.1)

                x = max(0, x_min - margin_x)
                y = max(0, y_min - margin_y)
                w = (x_max - x_min) + 2 * margin_x
                h = (y_max - y_min) + 2 * margin_y

                boxes.append((x, y, w, h))
                logger.debug(f"Detected text '{text}' at ({x}, {y}, {w}, {h})")

            logger.info(f"Detected {len(boxes)} text regions")
            return boxes

        except ImportError:
            logger.error("PaddleOCR not installed. Run: pip install paddleocr")
            return []
        except Exception as e:
            logger.error(f"Text detection failed: {e}")
            return []

    def _inpaint(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Apply inpainting algorithm.

        Args:
            img: OpenCV image
            mask: Binary mask (255 = remove, 0 = keep)

        Returns:
            Inpainted image
        """
        if self.method == InpaintingMethod.TELEA:
            # Fast Marching Method (Telea 2004)
            # Good for: thin structures, text
            result = cv2.inpaint(
                img, mask, self.inpaint_radius, cv2.INPAINT_TELEA
            )
            logger.info("Applied TELEA inpainting")

        elif self.method == InpaintingMethod.NS:
            # Navier-Stokes (Bertalmio 2001)
            # Good for: larger regions, smoother results
            result = cv2.inpaint(img, mask, self.inpaint_radius, cv2.INPAINT_NS)
            logger.info("Applied Navier-Stokes inpainting")

        elif self.method == InpaintingMethod.LAMA:
            # LaMa (Large Mask Inpainting)
            # State-of-the-art, requires model download
            result = self._inpaint_lama(img, mask)
            logger.info("Applied LaMa inpainting")

        else:
            raise ValueError(f"Unknown inpainting method: {self.method}")

        return result

    def _inpaint_lama(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Apply LaMa inpainting (high quality, requires model).

        Note: This requires downloading the LaMa model (~60MB).
        Falls back to TELEA if model not available.

        Args:
            img: OpenCV image
            mask: Binary mask

        Returns:
            Inpainted image
        """
        try:
            # Try to import lama-cleaner
            from lama_cleaner.model_manager import ModelManager
            from lama_cleaner.schema import Config

            # Initialize model (cached)
            if not hasattr(self, "_lama_model"):
                self._lama_model = ModelManager(
                    name="lama", device="cpu"  # Use "cuda" if GPU available
                )

            # Prepare config
            config = Config(
                ldm_steps=25,
                ldm_sampler="plms",
                hd_strategy="Original",
                hd_strategy_crop_margin=32,
                hd_strategy_crop_trigger_size=512,
                hd_strategy_resize_limit=512,
            )

            # Run inpainting
            result = self._lama_model(image=img, mask=mask, config=config)

            return result

        except ImportError:
            logger.warning(
                "LaMa model not available. Install with: pip install lama-cleaner"
            )
            logger.info("Falling back to TELEA inpainting")
            return cv2.inpaint(img, mask, self.inpaint_radius, cv2.INPAINT_TELEA)
        except Exception as e:
            logger.error(f"LaMa inpainting failed: {e}")
            logger.info("Falling back to TELEA inpainting")
            return cv2.inpaint(img, mask, self.inpaint_radius, cv2.INPAINT_TELEA)

    def remove_specific_color(
        self, image: Union[Image.Image, np.ndarray], color: Tuple[int, int, int], tolerance: int = 30
    ) -> Image.Image:
        """
        Remove specific color (useful for solid watermarks).

        Args:
            image: PIL Image or numpy array
            color: RGB color to remove (e.g., (255, 255, 255) for white)
            tolerance: Color tolerance (0-255)

        Returns:
            PIL Image with color removed

        Example:
            >>> # Remove white watermarks
            >>> clean_img = remover.remove_specific_color(
            ...     image,
            ...     color=(255, 255, 255),
            ...     tolerance=30
            ... )
        """
        img_cv = self._to_cv2(image)

        # Convert color to BGR
        target_color = np.array([color[2], color[1], color[0]], dtype=np.uint8)

        # Create mask for similar colors
        lower = np.clip(target_color - tolerance, 0, 255)
        upper = np.clip(target_color + tolerance, 0, 255)

        mask = cv2.inRange(img_cv, lower, upper)

        # Inpaint
        result = self._inpaint(img_cv, mask)

        return self._to_pil(result)

    def _to_cv2(self, image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """Convert to OpenCV format"""
        if isinstance(image, Image.Image):
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return image

    def _to_pil(self, image: np.ndarray) -> Image.Image:
        """Convert to PIL format"""
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


# Helper functions for convenience

def remove_watermark(
    image: Union[Image.Image, np.ndarray],
    regions: Optional[List[Tuple[int, int, int, int]]] = None,
    method: str = "telea",
    auto_detect: bool = True,
) -> Image.Image:
    """
    Convenience function to remove watermarks.

    Args:
        image: PIL Image or numpy array
        regions: Manual regions to remove [(x, y, width, height), ...]
        method: Inpainting method ("telea", "ns", or "lama")
        auto_detect: Automatically detect text regions

    Returns:
        PIL Image with watermarks removed

    Example:
        >>> from src.core.ocr.watermark_remover import remove_watermark
        >>> clean_img = remove_watermark(image)
    """
    remover = WatermarkRemover(method=InpaintingMethod(method))
    return remover.remove_watermark(image, regions=regions, auto_detect=auto_detect)


def remove_color_watermark(
    image: Union[Image.Image, np.ndarray],
    color: Tuple[int, int, int] = (255, 255, 255),
    tolerance: int = 30,
) -> Image.Image:
    """
    Convenience function to remove color-based watermarks.

    Args:
        image: PIL Image or numpy array
        color: RGB color to remove
        tolerance: Color tolerance (0-255)

    Returns:
        PIL Image with color removed

    Example:
        >>> # Remove white watermarks
        >>> clean_img = remove_color_watermark(image, color=(255, 255, 255))
    """
    remover = WatermarkRemover()
    return remover.remove_specific_color(image, color, tolerance)
