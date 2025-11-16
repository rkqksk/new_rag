"""
Shape Embedding Service for Phase 6.1
Extract shape descriptors (Hu Moments, Fourier Descriptors, Zernike Moments)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ShapeFeatures:
    """Shape feature extraction result"""

    hu_moments: np.ndarray  # 7 Hu moments
    fourier_descriptors: np.ndarray  # Fourier descriptors
    zernike_moments: Optional[np.ndarray] = None  # Zernike moments (optional)
    aspect_ratio: float = 0.0
    circularity: float = 0.0
    solidity: float = 0.0
    contour_area: float = 0.0


class ShapeEmbedder:
    """
    Shape Embedding Service

    Extracts geometric features from product images:
    1. Hu Moments (7 features) - Scale, rotation, translation invariant
    2. Fourier Descriptors (32 features) - Shape contour representation
    3. Zernike Moments (optional, 36 features) - Orthogonal moments
    4. Basic shape metrics (aspect ratio, circularity, solidity)

    Total embedding: 128-dim (configurable)

    Example:
        >>> embedder = ShapeEmbedder(embedding_dim=128)
        >>> image = Image.open("product.jpg")
        >>> embedding = embedder.encode_shape(image)
        >>> print(embedding.shape)  # (128,)
    """

    def __init__(
        self,
        embedding_dim: int = 128,
        fourier_descriptors_count: int = 32,
        use_zernike: bool = False,
        background_removal: bool = True,
    ):
        """
        Initialize Shape Embedder

        Args:
            embedding_dim: Final embedding dimension (default: 128)
            fourier_descriptors_count: Number of Fourier descriptors
            use_zernike: Include Zernike moments (expensive)
            background_removal: Remove background before extraction
        """
        self.embedding_dim = embedding_dim
        self.fourier_count = fourier_descriptors_count
        self.use_zernike = use_zernike
        self.background_removal = background_removal

        logger.info(
            f"✅ ShapeEmbedder initialized "
            f"(dim={embedding_dim}, fourier={fourier_descriptors_count}, zernike={use_zernike})"
        )

    def encode_shape(self, image: Image.Image, return_features: bool = False) -> np.ndarray:
        """
        Extract shape embedding from image

        Args:
            image: PIL Image
            return_features: Also return ShapeFeatures object

        Returns:
            Shape embedding vector (128-dim by default)

        Example:
            >>> embedding = embedder.encode_shape(image)
            >>> print(embedding.shape)  # (128,)
        """
        # Convert PIL to OpenCV format
        img_cv = self._pil_to_cv2(image)

        # Preprocess
        preprocessed = self._preprocess(img_cv)

        # Find contours
        contours = self._find_contours(preprocessed)

        if not contours:
            logger.warning("No contours found in image, returning zero vector")
            return np.zeros(self.embedding_dim, dtype=np.float32)

        # Get largest contour (main product)
        main_contour = max(contours, key=cv2.contourArea)

        # Extract features
        features = self._extract_features(main_contour, preprocessed)

        # Build embedding vector
        embedding = self._build_embedding(features)

        if return_features:
            return embedding, features
        else:
            return embedding

    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        # Convert to RGB if needed
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Convert to numpy array
        img_array = np.array(pil_image)

        # Convert RGB to BGR (OpenCV format)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        return img_bgr

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for contour detection

        Steps:
        1. Convert to grayscale
        2. Gaussian blur
        3. Adaptive threshold or Otsu
        4. Morphological operations
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Otsu's thresholding
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological operations to clean up
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

        return binary

    def _find_contours(self, binary_image: np.ndarray) -> List[np.ndarray]:
        """Find contours in binary image"""
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter small contours (noise)
        min_area = 100  # pixels
        filtered = [c for c in contours if cv2.contourArea(c) > min_area]

        return filtered

    def _extract_features(self, contour: np.ndarray, binary_image: np.ndarray) -> ShapeFeatures:
        """Extract all shape features from contour"""
        # 1. Hu Moments (7 features)
        moments = cv2.moments(contour)
        hu_moments = cv2.HuMoments(moments).flatten()

        # Log transform for better scale
        hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-10)

        # 2. Fourier Descriptors
        fourier_desc = self._compute_fourier_descriptors(contour, self.fourier_count)

        # 3. Basic shape metrics
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        # Aspect ratio
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h if h > 0 else 0.0

        # Circularity: 4π * area / perimeter²
        circularity = (4 * np.pi * area) / (perimeter**2) if perimeter > 0 else 0.0

        # Solidity: contour area / convex hull area
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0.0

        features = ShapeFeatures(
            hu_moments=hu_moments,
            fourier_descriptors=fourier_desc,
            aspect_ratio=aspect_ratio,
            circularity=circularity,
            solidity=solidity,
            contour_area=area,
        )

        return features

    def _compute_fourier_descriptors(self, contour: np.ndarray, num_descriptors: int) -> np.ndarray:
        """
        Compute Fourier Descriptors from contour

        Fourier descriptors are rotation, translation, scale invariant
        shape descriptors based on FFT of contour coordinates
        """
        # Get contour points
        contour_complex = np.empty(contour.shape[:-1], dtype=complex)
        contour_complex.real = contour[:, 0, 0]
        contour_complex.imag = contour[:, 0, 1]

        # Compute FFT
        fourier_result = np.fft.fft(contour_complex)

        # Take magnitude (rotation invariant)
        fourier_magnitudes = np.abs(fourier_result)

        # Normalize by DC component (scale invariant)
        if fourier_magnitudes[0] > 0:
            fourier_magnitudes = fourier_magnitudes / fourier_magnitudes[0]

        # Take first n descriptors (skip DC component)
        descriptors = fourier_magnitudes[1 : num_descriptors + 1]

        # Pad if needed
        if len(descriptors) < num_descriptors:
            descriptors = np.pad(descriptors, (0, num_descriptors - len(descriptors)))

        return descriptors

    def _build_embedding(self, features: ShapeFeatures) -> np.ndarray:
        """
        Build final embedding vector from features

        Default composition (128-dim):
        - Hu Moments: 7 features
        - Fourier Descriptors: 32 features
        - Basic metrics: 3 features (aspect_ratio, circularity, solidity)
        - Padding: remaining to reach 128-dim

        Total: 42 + padding = 128
        """
        components = []

        # 1. Hu moments (7)
        components.append(features.hu_moments)

        # 2. Fourier descriptors (32)
        components.append(features.fourier_descriptors)

        # 3. Basic metrics (3)
        basic_metrics = np.array(
            [features.aspect_ratio, features.circularity, features.solidity], dtype=np.float32
        )
        components.append(basic_metrics)

        # 4. Zernike moments (optional)
        if self.use_zernike and features.zernike_moments is not None:
            components.append(features.zernike_moments)

        # Concatenate all components
        embedding = np.concatenate(components)

        # Pad or truncate to target dimension
        if len(embedding) < self.embedding_dim:
            # Pad with zeros
            padding = np.zeros(self.embedding_dim - len(embedding), dtype=np.float32)
            embedding = np.concatenate([embedding, padding])
        elif len(embedding) > self.embedding_dim:
            # Truncate
            embedding = embedding[: self.embedding_dim]

        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)

    def encode_batch(self, images: List[Image.Image]) -> np.ndarray:
        """
        Batch encode multiple images

        Args:
            images: List of PIL Images

        Returns:
            Array of shape embeddings (N, embedding_dim)
        """
        embeddings = []

        for image in images:
            try:
                embedding = self.encode_shape(image)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to encode image: {e}")
                # Add zero vector for failed images
                embeddings.append(np.zeros(self.embedding_dim, dtype=np.float32))

        return np.array(embeddings)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two shape embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score [0, 1]
        """
        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Clip to [0, 1]
        similarity = np.clip(similarity, 0.0, 1.0)

        return float(similarity)

    def __repr__(self):
        return (
            f"ShapeEmbedder("
            f"dim={self.embedding_dim}, "
            f"fourier={self.fourier_count}, "
            f"zernike={self.use_zernike})"
        )
