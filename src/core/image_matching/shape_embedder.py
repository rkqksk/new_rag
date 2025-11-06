"""
Shape Embedding Service
Convert shape descriptors to fixed 128-dim embeddings
"""

import logging
from typing import Union, List, Optional
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class ShapeEmbedder:
    """
    Generate 128-dimensional shape embeddings

    Workflow:
    1. Background removal (optional)
    2. Contour extraction
    3. Shape descriptor computation
    4. Dimensionality reduction/expansion to 128-dim

    Features:
    - Fixed 128-dim output
    - Rotation/scale/translation invariant
    - Batch processing
    """

    def __init__(
        self,
        target_dim: int = 128,
        use_background_removal: bool = False,
        fourier_coeffs: int = 60
    ):
        """
        Initialize shape embedder

        Args:
            target_dim: Target embedding dimension (default: 128)
            use_background_removal: Use background removal before extraction
            fourier_coeffs: Number of Fourier coefficients
        """
        self.target_dim = target_dim
        self.use_background_removal = use_background_removal
        self.fourier_coeffs = fourier_coeffs

        # Import components
        from .background_remover import BackgroundRemover
        from .contour_extractor import ContourExtractor
        from .shape_descriptor import ShapeDescriptor

        # Initialize components
        self.bg_remover = BackgroundRemover() if use_background_removal else None
        self.contour_extractor = ContourExtractor()
        self.shape_descriptor = ShapeDescriptor(fourier_coeffs=fourier_coeffs)

        # Calculate source dimension
        self.source_dim = 7 + fourier_coeffs  # Hu (7) + Fourier (60) = 67

        # Initialize projection matrix (for dimensionality adjustment)
        self._init_projection()

        logger.info(f"✅ Shape embedder initialized ({self.source_dim} → {target_dim} dim)")

    def _init_projection(self):
        """Initialize projection matrix for dimensionality adjustment"""
        if self.source_dim == self.target_dim:
            # No projection needed
            self.projection_matrix = None
            self.use_projection = False

        elif self.source_dim < self.target_dim:
            # Pad with zeros
            self.projection_matrix = None
            self.use_projection = False
            self.pad_size = self.target_dim - self.source_dim

        else:
            # Random projection to reduce dimensions
            # Using Johnson-Lindenstrauss lemma
            np.random.seed(42)
            self.projection_matrix = np.random.randn(
                self.source_dim,
                self.target_dim
            )
            # Normalize
            self.projection_matrix /= np.sqrt(self.source_dim)
            self.use_projection = True

    def is_available(self) -> bool:
        """Check if shape embedder is available"""
        return (
            self.contour_extractor.is_available() and
            self.shape_descriptor.is_available()
        )

    def embed_image(
        self,
        image_path: Union[str, Path],
        return_metadata: bool = False
    ) -> Union[List[float], tuple]:
        """
        Generate shape embedding from image

        Args:
            image_path: Path to image file
            return_metadata: Also return metadata

        Returns:
            128-dim embedding vector or (embedding, metadata) if return_metadata=True
        """
        if not self.is_available():
            raise RuntimeError("Shape embedder not available (OpenCV required)")

        from PIL import Image

        # Load image
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        pil_image = Image.open(image_path)
        image = np.array(pil_image)

        # Step 1: Background removal (optional)
        if self.use_background_removal and self.bg_remover and self.bg_remover.is_available():
            logger.debug("Removing background")
            image = self.bg_remover.remove_background(image_path)

        # Step 2: Extract contours
        logger.debug("Extracting contours")
        contours = self.contour_extractor.extract_contours(image)

        if not contours:
            logger.warning(f"No contours found in {image_path.name}")
            # Return zero vector
            embedding = [0.0] * self.target_dim
            metadata = {
                'success': False,
                'error': 'No contours found',
                'num_contours': 0
            }
            return (embedding, metadata) if return_metadata else embedding

        # Step 3: Get largest contour
        largest_contour = self.contour_extractor.get_largest_contour(contours)

        # Step 4: Compute shape descriptor
        logger.debug("Computing shape descriptor")
        descriptor = self.shape_descriptor.compute_combined_descriptor(largest_contour)

        # Step 5: Project to target dimension
        embedding = self._project_to_target_dim(descriptor)

        # Normalize to unit length
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # Convert to list
        embedding = embedding.tolist()

        if return_metadata:
            # Get contour properties
            properties = self.contour_extractor.get_contour_properties(largest_contour)

            metadata = {
                'success': True,
                'num_contours': len(contours),
                'contour_properties': properties,
                'descriptor_dim': len(descriptor),
                'embedding_dim': len(embedding),
                'source_file': str(image_path)
            }

            return embedding, metadata

        return embedding

    def _project_to_target_dim(self, descriptor: np.ndarray) -> np.ndarray:
        """
        Project descriptor to target dimension

        Args:
            descriptor: Source descriptor

        Returns:
            Target dimension vector
        """
        if self.source_dim == self.target_dim:
            return descriptor

        elif self.source_dim < self.target_dim:
            # Pad with zeros
            return np.pad(descriptor, (0, self.target_dim - self.source_dim))

        else:
            # Random projection
            if self.use_projection:
                return np.dot(descriptor, self.projection_matrix)
            else:
                # Truncate
                return descriptor[:self.target_dim]

    def embed_batch(
        self,
        image_paths: List[Union[str, Path]],
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple images

        Args:
            image_paths: List of image paths
            show_progress: Show progress bar

        Returns:
            List of 128-dim embeddings
        """
        embeddings = []

        # Progress tracking
        iterator = image_paths
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(image_paths, desc="Generating shape embeddings")
            except ImportError:
                pass

        for image_path in iterator:
            try:
                embedding = self.embed_image(image_path)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed {image_path}: {e}")
                # Add zero vector
                embeddings.append([0.0] * self.target_dim)

        return embeddings

    def embed_from_contour(
        self,
        contour: np.ndarray
    ) -> List[float]:
        """
        Generate embedding directly from contour

        Args:
            contour: Input contour (Nx2 array)

        Returns:
            128-dim embedding
        """
        if not self.is_available():
            raise RuntimeError("Shape embedder not available")

        # Compute shape descriptor
        descriptor = self.shape_descriptor.compute_combined_descriptor(contour)

        # Project to target dimension
        embedding = self._project_to_target_dim(descriptor)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.tolist()

    def compare_embeddings(
        self,
        embedding1: List[float],
        embedding2: List[float],
        metric: str = 'cosine'
    ) -> float:
        """
        Compare two shape embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Distance metric ('cosine', 'euclidean')

        Returns:
            Similarity score (higher is more similar for cosine)
        """
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)

        if metric == 'cosine':
            # Cosine similarity
            dot_product = np.dot(emb1, emb2)
            norm_product = np.linalg.norm(emb1) * np.linalg.norm(emb2)
            similarity = dot_product / (norm_product + 1e-10)
            return float(similarity)

        elif metric == 'euclidean':
            # Euclidean distance (convert to similarity)
            distance = np.linalg.norm(emb1 - emb2)
            similarity = 1.0 / (1.0 + distance)
            return float(similarity)

        else:
            raise ValueError(f"Unknown metric: {metric}")

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.target_dim

    def __repr__(self):
        status = "available" if self.is_available() else "not available"
        bg = "enabled" if self.use_background_removal else "disabled"
        return (
            f"ShapeEmbedder("
            f"dim={self.target_dim}, "
            f"bg_removal={bg}, "
            f"status={status})"
        )
