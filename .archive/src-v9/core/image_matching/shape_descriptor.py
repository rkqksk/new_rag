"""
Shape Descriptor Service
Generate shape descriptors (Hu Moments, Fourier Descriptors)
"""

import logging
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ShapeDescriptor:
    """
    Generate shape descriptors for contours

    Features:
    - Hu Moments (7 invariant moments)
    - Fourier Descriptors (frequency domain shape representation)
    - Combined descriptor (Hu + Fourier)
    - Rotation, scale, translation invariant
    """

    def __init__(self, fourier_coeffs: int = 60, normalize: bool = True):
        """
        Initialize shape descriptor

        Args:
            fourier_coeffs: Number of Fourier coefficients to keep
            normalize: Normalize descriptors to unit length
        """
        self.fourier_coeffs = fourier_coeffs
        self.normalize = normalize

        # Check OpenCV availability
        try:
            import cv2

            self.cv2 = cv2
            self.available = True
            logger.info("✅ Shape descriptor initialized")
        except ImportError:
            logger.warning("OpenCV not installed")
            self.available = False
            self.cv2 = None

    def is_available(self) -> bool:
        """Check if shape descriptor is available"""
        return self.available

    def compute_hu_moments(self, contour: np.ndarray) -> np.ndarray:
        """
        Compute Hu Moments (7 invariant moments)

        Invariant to:
        - Translation
        - Scale
        - Rotation

        Args:
            contour: Input contour (Nx2 array)

        Returns:
            7-dimensional Hu moments vector
        """
        if not self.available:
            raise RuntimeError("OpenCV not available")

        # Calculate moments
        moments = self.cv2.moments(contour)

        # Calculate Hu moments
        hu_moments = self.cv2.HuMoments(moments).flatten()

        # Log transform for better scale invariance
        # Use sign to preserve negative values
        hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-10)

        return hu_moments

    def compute_fourier_descriptors(
        self, contour: np.ndarray, num_coeffs: Optional[int] = None
    ) -> np.ndarray:
        """
        Compute Fourier Descriptors

        Invariant to:
        - Starting point
        - Translation (using relative descriptors)
        - Scale (normalization)
        - Rotation (using magnitude only)

        Args:
            contour: Input contour (Nx2 array)
            num_coeffs: Number of coefficients (default: self.fourier_coeffs)

        Returns:
            Fourier descriptor vector
        """
        num_coeffs = num_coeffs or self.fourier_coeffs

        # Reshape contour to complex numbers (x + iy)
        contour = contour.reshape(-1, 2)
        complex_contour = contour[:, 0] + 1j * contour[:, 1]

        # FFT
        fourier_result = np.fft.fft(complex_contour)

        # Take magnitude (rotation invariant)
        fourier_magnitudes = np.abs(fourier_result)

        # Normalize by DC component (translation invariant)
        if fourier_magnitudes[0] != 0:
            fourier_magnitudes = fourier_magnitudes / fourier_magnitudes[0]

        # Keep only first num_coeffs (low frequencies)
        # Skip DC component (index 0) as it's now normalized to 1
        descriptors = fourier_magnitudes[1 : num_coeffs + 1]

        # Pad if contour is too small
        if len(descriptors) < num_coeffs:
            descriptors = np.pad(descriptors, (0, num_coeffs - len(descriptors)), mode="constant")

        return descriptors

    def compute_combined_descriptor(
        self, contour: np.ndarray, hu_weight: float = 0.3, fourier_weight: float = 0.7
    ) -> np.ndarray:
        """
        Compute combined descriptor (Hu + Fourier)

        Args:
            contour: Input contour
            hu_weight: Weight for Hu moments (default: 0.3)
            fourier_weight: Weight for Fourier (default: 0.7)

        Returns:
            Combined descriptor vector
        """
        # Compute Hu moments (7 dims)
        hu = self.compute_hu_moments(contour)

        # Compute Fourier descriptors (num_coeffs dims)
        fourier = self.compute_fourier_descriptors(contour)

        # Normalize each component
        if self.normalize:
            hu = hu / (np.linalg.norm(hu) + 1e-10)
            fourier = fourier / (np.linalg.norm(fourier) + 1e-10)

        # Weight and combine
        hu_weighted = hu * hu_weight
        fourier_weighted = fourier * fourier_weight

        # Concatenate
        combined = np.concatenate([hu_weighted, fourier_weighted])

        return combined

    def compute_shape_context(
        self,
        contour: np.ndarray,
        num_points: int = 100,
        num_bins_r: int = 5,
        num_bins_theta: int = 12,
    ) -> np.ndarray:
        """
        Compute Shape Context descriptor

        Args:
            contour: Input contour
            num_points: Number of points to sample
            num_bins_r: Number of radial bins
            num_bins_theta: Number of angular bins

        Returns:
            Shape context descriptor
        """
        # Reshape contour
        contour = contour.reshape(-1, 2).astype(np.float32)

        # Sample points uniformly
        if len(contour) > num_points:
            indices = np.linspace(0, len(contour) - 1, num_points, dtype=int)
            sampled = contour[indices]
        else:
            sampled = contour

        # Compute pairwise distances and angles
        num_sampled = len(sampled)
        shape_contexts = []

        for i in range(num_sampled):
            # Point of interest
            point = sampled[i]

            # Compute relative positions
            diff = sampled - point

            # Distances (log scale for better distribution)
            distances = np.sqrt(diff[:, 0] ** 2 + diff[:, 1] ** 2)
            log_r = np.log(distances + 1e-10)

            # Angles
            theta = np.arctan2(diff[:, 1], diff[:, 0])

            # Create histogram
            hist, _, _ = np.histogram2d(log_r, theta, bins=[num_bins_r, num_bins_theta])

            shape_contexts.append(hist.flatten())

        # Average across all points
        shape_context = np.mean(shape_contexts, axis=0)

        return shape_context

    def match_shapes(
        self, descriptor1: np.ndarray, descriptor2: np.ndarray, metric: str = "euclidean"
    ) -> float:
        """
        Compare two shape descriptors

        Args:
            descriptor1: First descriptor
            descriptor2: Second descriptor
            metric: Distance metric ('euclidean', 'cosine', 'correlation')

        Returns:
            Similarity score (lower is more similar for euclidean)
        """
        if metric == "euclidean":
            distance = np.linalg.norm(descriptor1 - descriptor2)

        elif metric == "cosine":
            # Cosine similarity (convert to distance)
            dot_product = np.dot(descriptor1, descriptor2)
            norm_product = np.linalg.norm(descriptor1) * np.linalg.norm(descriptor2)
            cosine_sim = dot_product / (norm_product + 1e-10)
            distance = 1.0 - cosine_sim

        elif metric == "correlation":
            # Correlation (convert to distance)
            correlation = np.corrcoef(descriptor1, descriptor2)[0, 1]
            distance = 1.0 - correlation

        else:
            raise ValueError(f"Unknown metric: {metric}")

        return float(distance)

    def batch_compute(self, contours: List[np.ndarray], method: str = "combined") -> np.ndarray:
        """
        Compute descriptors for multiple contours

        Args:
            contours: List of contours
            method: Descriptor method ('hu', 'fourier', 'combined', 'shape_context')

        Returns:
            Array of descriptors (num_contours x descriptor_dim)
        """
        descriptors = []

        for contour in contours:
            if method == "hu":
                desc = self.compute_hu_moments(contour)
            elif method == "fourier":
                desc = self.compute_fourier_descriptors(contour)
            elif method == "combined":
                desc = self.compute_combined_descriptor(contour)
            elif method == "shape_context":
                desc = self.compute_shape_context(contour)
            else:
                raise ValueError(f"Unknown method: {method}")

            descriptors.append(desc)

        return np.array(descriptors)

    def get_descriptor_dimension(self, method: str = "combined") -> int:
        """
        Get dimension of descriptor

        Args:
            method: Descriptor method

        Returns:
            Descriptor dimension
        """
        if method == "hu":
            return 7
        elif method == "fourier":
            return self.fourier_coeffs
        elif method == "combined":
            return 7 + self.fourier_coeffs
        elif method == "shape_context":
            return 5 * 12  # Default bins
        else:
            raise ValueError(f"Unknown method: {method}")

    def __repr__(self):
        status = "available" if self.available else "not available"
        return f"ShapeDescriptor(fourier_coeffs={self.fourier_coeffs}, status={status})"
