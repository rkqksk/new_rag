"""
Background Removal Service
Uses U2-Net (rembg) for high-quality background removal
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


class BackgroundRemover:
    """
    Remove background from product images using U2-Net

    Features:
    - High-quality segmentation
    - Alpha matting support
    - Batch processing
    - Quality validation
    """

    def __init__(self, model_name: str = "u2net", alpha_matting: bool = True, use_gpu: bool = True):
        """
        Initialize background remover

        Args:
            model_name: Model to use ('u2net', 'u2netp', 'u2net_human_seg')
            alpha_matting: Enable alpha matting for better edges
            use_gpu: Use GPU acceleration if available
        """
        self.model_name = model_name
        self.alpha_matting = alpha_matting
        self.use_gpu = use_gpu
        self.model = None

        # Try to import rembg
        try:
            from rembg import new_session, remove

            self.remove = remove
            self.new_session = new_session
            self.available = True
            logger.info(f"✅ rembg initialized (model={model_name})")
        except ImportError:
            logger.warning("rembg not installed. Install with: pip install rembg")
            self.available = False
            self.remove = None
            self.new_session = None

    def is_available(self) -> bool:
        """Check if background removal is available"""
        return self.available

    def remove_background(
        self,
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        return_mask: bool = False,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Remove background from image

        Args:
            image_path: Path to input image
            output_path: Optional output path (if None, returns array)
            return_mask: Also return binary mask

        Returns:
            Image array (RGBA) or tuple (image, mask) if return_mask=True
        """
        if not self.available:
            raise RuntimeError("rembg not available. Install with: pip install rembg")

        from PIL import Image

        # Load image
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        input_image = Image.open(image_path)

        # Remove background
        logger.debug(f"Removing background from {image_path.name}")
        output_image = self.remove(
            input_image,
            alpha_matting=self.alpha_matting,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10,
        )

        # Save if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_image.save(output_path)
            logger.info(f"✅ Saved to {output_path}")

        # Convert to numpy array
        output_array = np.array(output_image)

        if return_mask:
            # Extract alpha channel as mask
            if output_array.shape[-1] == 4:
                mask = output_array[:, :, 3]
            else:
                # No alpha channel, create full mask
                mask = np.ones(output_array.shape[:2], dtype=np.uint8) * 255

            return output_array, mask

        return output_array

    def batch_remove(
        self,
        image_paths: list,
        output_dir: Optional[Union[str, Path]] = None,
        show_progress: bool = True,
    ) -> list:
        """
        Batch process multiple images

        Args:
            image_paths: List of image paths
            output_dir: Output directory (if None, returns arrays)
            show_progress: Show progress bar

        Returns:
            List of processed images
        """
        if not self.available:
            raise RuntimeError("rembg not available")

        results = []

        # Progress tracking
        iterator = image_paths
        if show_progress:
            try:
                from tqdm import tqdm

                iterator = tqdm(image_paths, desc="Removing backgrounds")
            except ImportError:
                pass

        for image_path in iterator:
            try:
                # Determine output path
                if output_dir:
                    output_dir = Path(output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / Path(image_path).name
                else:
                    output_path = None

                # Process image
                result = self.remove_background(image_path, output_path=output_path)

                results.append(result)

            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                results.append(None)

        return results

    def validate_quality(
        self,
        image: np.ndarray,
        min_foreground_ratio: float = 0.1,
        max_foreground_ratio: float = 0.9,
    ) -> dict:
        """
        Validate background removal quality

        Args:
            image: RGBA image array
            min_foreground_ratio: Minimum foreground ratio
            max_foreground_ratio: Maximum foreground ratio

        Returns:
            Dictionary with quality metrics
        """
        if image.shape[-1] != 4:
            raise ValueError("Image must have alpha channel (RGBA)")

        alpha = image[:, :, 3]

        # Calculate metrics
        total_pixels = alpha.size
        foreground_pixels = np.sum(alpha > 128)
        foreground_ratio = foreground_pixels / total_pixels

        # Edge smoothness (variance of alpha channel)
        edge_smoothness = 1.0 / (1.0 + np.std(alpha))

        # Quality flags
        is_valid = min_foreground_ratio <= foreground_ratio <= max_foreground_ratio

        return {
            "is_valid": is_valid,
            "foreground_ratio": foreground_ratio,
            "foreground_pixels": int(foreground_pixels),
            "total_pixels": int(total_pixels),
            "edge_smoothness": float(edge_smoothness),
            "alpha_mean": float(np.mean(alpha)),
            "alpha_std": float(np.std(alpha)),
        }

    def get_bounding_box(self, image: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Get tight bounding box around foreground

        Args:
            image: RGBA image array

        Returns:
            Tuple (x1, y1, x2, y2)
        """
        if image.shape[-1] != 4:
            raise ValueError("Image must have alpha channel (RGBA)")

        alpha = image[:, :, 3]

        # Find non-zero pixels
        rows = np.any(alpha > 0, axis=1)
        cols = np.any(alpha > 0, axis=0)

        if not rows.any() or not cols.any():
            # No foreground found
            return (0, 0, 0, 0)

        y1, y2 = np.where(rows)[0][[0, -1]]
        x1, x2 = np.where(cols)[0][[0, -1]]

        return (int(x1), int(y1), int(x2), int(y2))

    def crop_to_foreground(self, image: np.ndarray, padding: int = 10) -> np.ndarray:
        """
        Crop image to tight bounding box around foreground

        Args:
            image: RGBA image array
            padding: Padding pixels around bounding box

        Returns:
            Cropped image
        """
        x1, y1, x2, y2 = self.get_bounding_box(image)

        if x1 == x2 or y1 == y2:
            # No foreground, return original
            return image

        # Add padding
        h, w = image.shape[:2]
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)

        return image[y1:y2, x1:x2]

    def __repr__(self):
        status = "available" if self.available else "not available"
        return f"BackgroundRemover(model={self.model_name}, status={status})"
