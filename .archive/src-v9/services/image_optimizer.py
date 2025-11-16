"""
Image Optimization Service
Handles WebP conversion, thumbnails, and compression
Version: v8.3.0
"""

import io
import logging
from typing import Optional, Tuple
from PIL import Image
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Image optimization service"""

    # Thumbnail sizes (width, height)
    SIZES = {
        'thumb': (200, 200),
        'small': (400, 400),
        'medium': (800, 800),
        'large': (1200, 1200),
    }

    # Quality settings
    QUALITY = {
        'thumb': 70,
        'small': 75,
        'medium': 80,
        'large': 85,
    }

    def __init__(self, storage_path: str = './storage/images'):
        """
        Initialize image optimizer

        Args:
            storage_path: Path to store optimized images
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def optimize_image(
        self,
        image_data: bytes,
        size: str = 'medium',
        format: str = 'webp',
        quality: Optional[int] = None
    ) -> Tuple[bytes, str]:
        """
        Optimize image

        Args:
            image_data: Original image bytes
            size: Target size ('thumb', 'small', 'medium', 'large')
            format: Output format ('webp', 'jpeg', 'png')
            quality: Quality (1-100), defaults to preset

        Returns:
            (optimized_bytes, mime_type)
        """
        try:
            # Load image
            img = Image.open(io.BytesIO(image_data))

            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA') and format != 'png':
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img, mask=img.split()[1])
                img = background

            # Resize
            if size in self.SIZES:
                target_size = self.SIZES[size]
                img.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Set quality
            if quality is None:
                quality = self.QUALITY.get(size, 80)

            # Convert to target format
            output = io.BytesIO()

            if format == 'webp':
                img.save(output, format='WEBP', quality=quality, method=6)
                mime_type = 'image/webp'
            elif format == 'jpeg':
                img.save(output, format='JPEG', quality=quality, optimize=True)
                mime_type = 'image/jpeg'
            elif format == 'png':
                img.save(output, format='PNG', optimize=True)
                mime_type = 'image/png'
            else:
                raise ValueError(f'Unsupported format: {format}')

            output.seek(0)
            optimized_data = output.getvalue()

            logger.info(f'Optimized image: {len(image_data)} -> {len(optimized_data)} bytes '
                       f'({format}, {size}, Q{quality})')

            return optimized_data, mime_type

        except Exception as e:
            logger.error(f'Image optimization failed: {e}')
            raise

    def create_thumbnails(
        self,
        image_data: bytes,
        sizes: list = ['thumb', 'small', 'medium'],
        format: str = 'webp'
    ) -> dict:
        """
        Create multiple thumbnail sizes

        Args:
            image_data: Original image bytes
            sizes: List of sizes to generate
            format: Output format

        Returns:
            Dictionary of {size: bytes}
        """
        thumbnails = {}

        for size in sizes:
            try:
                optimized, _ = self.optimize_image(image_data, size=size, format=format)
                thumbnails[size] = optimized
            except Exception as e:
                logger.error(f'Failed to create {size} thumbnail: {e}')

        return thumbnails

    def get_image_info(self, image_data: bytes) -> dict:
        """
        Get image information

        Args:
            image_data: Image bytes

        Returns:
            Image metadata
        """
        try:
            img = Image.open(io.BytesIO(image_data))

            return {
                'width': img.width,
                'height': img.height,
                'mode': img.mode,
                'format': img.format,
                'size_bytes': len(image_data),
            }
        except Exception as e:
            logger.error(f'Failed to get image info: {e}')
            return {}

    def generate_image_hash(self, image_data: bytes) -> str:
        """Generate unique hash for image"""
        return hashlib.sha256(image_data).hexdigest()[:16]

    def save_optimized_image(
        self,
        image_data: bytes,
        filename: str,
        size: str = 'medium',
        format: str = 'webp'
    ) -> Path:
        """
        Save optimized image to disk

        Args:
            image_data: Original image bytes
            filename: Target filename (without extension)
            size: Size preset
            format: Output format

        Returns:
            Path to saved file
        """
        # Optimize
        optimized, mime_type = self.optimize_image(image_data, size=size, format=format)

        # Generate path
        ext = format if format != 'jpeg' else 'jpg'
        file_path = self.storage_path / size / f'{filename}.{ext}'
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save
        with open(file_path, 'wb') as f:
            f.write(optimized)

        logger.info(f'Saved optimized image: {file_path}')
        return file_path

    def batch_optimize(
        self,
        images: list,
        sizes: list = ['thumb', 'small', 'medium'],
        format: str = 'webp'
    ) -> list:
        """
        Batch optimize multiple images

        Args:
            images: List of (image_data, filename) tuples
            sizes: Sizes to generate
            format: Output format

        Returns:
            List of results
        """
        results = []

        for image_data, filename in images:
            try:
                thumbnails = self.create_thumbnails(image_data, sizes=sizes, format=format)

                # Save all sizes
                saved_paths = {}
                for size, thumb_data in thumbnails.items():
                    path = self.save_optimized_image(
                        thumb_data,
                        filename,
                        size=size,
                        format=format
                    )
                    saved_paths[size] = str(path)

                results.append({
                    'filename': filename,
                    'success': True,
                    'paths': saved_paths,
                })

            except Exception as e:
                logger.error(f'Failed to optimize {filename}: {e}')
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': str(e),
                })

        return results


# Singleton instance
_image_optimizer = None


def get_image_optimizer(storage_path: str = './storage/images') -> ImageOptimizer:
    """Get image optimizer singleton"""
    global _image_optimizer
    if _image_optimizer is None:
        _image_optimizer = ImageOptimizer(storage_path)
    return _image_optimizer
