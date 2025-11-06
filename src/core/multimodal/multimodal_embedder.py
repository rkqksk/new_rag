"""
Multi-Modal Embedding Service
Unified service for text, image, and shape embeddings
"""

import logging
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import torch
import numpy as np
from PIL import Image

# Text embedding
from sentence_transformers import SentenceTransformer

# Image embedding
try:
    import open_clip
    OPENCLIP_AVAILABLE = True
except ImportError:
    OPENCLIP_AVAILABLE = False
    logging.warning("OpenCLIP not available. Install with: pip install open_clip_torch")

logger = logging.getLogger(__name__)


class MultiModalEmbeddingService:
    """
    Unified Multi-Modal Embedding Service

    Supports:
    - Text embeddings (Sentence Transformers, 384-dim)
    - Image embeddings (OpenCLIP ViT-H-14, 1024-dim)
    - Shape embeddings (Custom descriptors, 128-dim) [Coming in Phase 6]

    Example:
        >>> embedder = MultiModalEmbeddingService()
        >>>
        >>> # Text only
        >>> text_emb = embedder.embed_text("20파이 캡 5000개")
        >>>
        >>> # Image only
        >>> image_emb = embedder.embed_image("product.jpg")
        >>>
        >>> # Multi-modal (text + image)
        >>> embeddings = embedder.embed(
        ...     text="100ml PET 보틀",
        ...     image="bottle.jpg"
        ... )
        >>> # Returns: {"text": [...], "image": [...]}
    """

    def __init__(
        self,
        text_model: str = 'all-MiniLM-L6-v2',
        image_model: str = 'ViT-H-14',
        device: str = 'auto',
        enable_image: bool = True,
        enable_shape: bool = False
    ):
        """
        Initialize Multi-Modal Embedding Service

        Args:
            text_model: Sentence Transformers model name
            image_model: OpenCLIP model name
            device: 'auto', 'cpu', 'cuda', or 'mps'
            enable_image: Enable image embedding (requires open_clip_torch)
            enable_shape: Enable shape embedding (Phase 6)
        """
        # Auto-detect device
        if device == 'auto':
            if torch.backends.mps.is_available():
                self.device = 'mps'
            elif torch.cuda.is_available():
                self.device = 'cuda'
            else:
                self.device = 'cpu'
        else:
            self.device = device

        logger.info(f"🚀 MultiModalEmbeddingService initializing on device: {self.device}")

        # Configuration
        self.text_model_name = text_model
        self.image_model_name = image_model
        self.enable_image = enable_image and OPENCLIP_AVAILABLE
        self.enable_shape = enable_shape

        # Initialize text embedder (always enabled)
        self._init_text_embedder()

        # Initialize image embedder (optional)
        if self.enable_image:
            self._init_image_embedder()
        else:
            self.image_model = None
            self.image_preprocess = None
            if enable_image and not OPENCLIP_AVAILABLE:
                logger.warning("⚠️ Image embedding requested but OpenCLIP not available")

        # Shape embedder (Phase 6)
        if self.enable_shape:
            logger.warning("⚠️ Shape embedding not yet implemented (Phase 6)")
            self.shape_embedder = None

        logger.info("✅ MultiModalEmbeddingService initialized successfully")
        self._log_config()

    def _init_text_embedder(self):
        """Initialize Sentence Transformers text embedder"""
        logger.info(f"📝 Loading text model: {self.text_model_name}")

        try:
            self.text_model = SentenceTransformer(
                f'sentence-transformers/{self.text_model_name}'
            )

            # Move to device
            if self.device in ['cuda', 'mps']:
                self.text_model = self.text_model.to(self.device)

            # Get embedding dimension
            self.text_dim = self.text_model.get_sentence_embedding_dimension()

            logger.info(f"✅ Text model loaded: {self.text_dim}-dim")

        except Exception as e:
            logger.error(f"❌ Failed to load text model: {e}")
            raise

    def _init_image_embedder(self):
        """Initialize OpenCLIP image embedder"""
        logger.info(f"🖼️ Loading image model: {self.image_model_name}")

        try:
            self.image_model, self.image_preprocess, _ = open_clip.create_model_and_transforms(
                model_name=self.image_model_name,
                pretrained='laion2b-s32b-b79k',
                device=self.device
            )
            self.image_model.eval()  # Inference mode

            # Get embedding dimension
            self.image_dim = 1024  # ViT-H-14 output dimension

            logger.info(f"✅ Image model loaded: {self.image_dim}-dim")

        except Exception as e:
            logger.error(f"❌ Failed to load image model: {e}")
            self.enable_image = False
            self.image_model = None
            self.image_preprocess = None

    def _log_config(self):
        """Log current configuration"""
        logger.info("=" * 60)
        logger.info("Multi-Modal Configuration:")
        logger.info(f"  Device: {self.device}")
        logger.info(f"  Text Model: {self.text_model_name} ({self.text_dim}-dim)")
        logger.info(f"  Image Model: {self.image_model_name if self.enable_image else 'Disabled'} "
                   f"({self.image_dim if self.enable_image else 0}-dim)")
        logger.info(f"  Shape Model: {'Phase 6' if self.enable_shape else 'Disabled'}")
        logger.info("=" * 60)

    # ==================== Text Embedding ====================

    def embed_text(self, text: str) -> List[float]:
        """
        Generate text embedding

        Args:
            text: Input text

        Returns:
            384-dimensional embedding vector
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")

        embedding = self.text_model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return embedding.tolist()

    def embed_texts_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Batch text embedding for efficiency

        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Show progress bar

        Returns:
            List of 384-dimensional embeddings
        """
        if not texts:
            return []

        embeddings = self.text_model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )

        return embeddings.tolist()

    # ==================== Image Embedding ====================

    def embed_image(self, image_path: Union[str, Path]) -> List[float]:
        """
        Generate image embedding

        Args:
            image_path: Path to image file

        Returns:
            1024-dimensional embedding vector

        Raises:
            ValueError: If image embedding is not enabled
            FileNotFoundError: If image file not found
        """
        if not self.enable_image:
            raise ValueError("Image embedding is not enabled. Install open_clip_torch.")

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.image_preprocess(image).unsqueeze(0).to(self.device)

            # Generate embedding
            with torch.no_grad():
                embedding = self.image_model.encode_image(image_tensor)

            # Convert to list
            return embedding.squeeze(0).cpu().numpy().tolist()

        except Exception as e:
            logger.error(f"Image embedding error for {image_path}: {e}")
            raise

    def embed_images_batch(
        self,
        image_paths: List[Union[str, Path]],
        batch_size: int = 8,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Batch image embedding for efficiency

        Args:
            image_paths: List of image file paths
            batch_size: Batch size for processing
            show_progress: Show progress bar

        Returns:
            List of 1024-dimensional embeddings
        """
        if not self.enable_image:
            raise ValueError("Image embedding is not enabled")

        if not image_paths:
            return []

        embeddings = []

        # Process in batches
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i+batch_size]

            # Load and preprocess batch
            batch_images = []
            for path in batch_paths:
                try:
                    image = Image.open(path).convert("RGB")
                    batch_images.append(image)
                except Exception as e:
                    logger.warning(f"Failed to load image {path}: {e}")
                    continue

            if not batch_images:
                continue

            # Stack tensors
            batch_tensors = torch.stack([
                self.image_preprocess(img) for img in batch_images
            ]).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                batch_embeddings = self.image_model.encode_image(batch_tensors)

            # Convert to list
            embeddings.extend(batch_embeddings.cpu().numpy().tolist())

            if show_progress:
                logger.info(f"Processed {min(i+batch_size, len(image_paths))}/{len(image_paths)} images")

        return embeddings

    # ==================== Multi-Modal Embedding ====================

    def embed(
        self,
        text: Optional[str] = None,
        image: Optional[Union[str, Path]] = None,
        shape: Optional[Union[str, Path]] = None
    ) -> Dict[str, List[float]]:
        """
        Generate multi-modal embeddings

        Args:
            text: Input text (optional)
            image: Image file path (optional)
            shape: Shape image for contour extraction (optional, Phase 6)

        Returns:
            Dictionary with available embeddings:
            {
                "text": [384-dim vector],
                "image": [1024-dim vector],
                "shape": [128-dim vector]  # Phase 6
            }

        Example:
            >>> embeddings = embedder.embed(
            ...     text="100ml PET bottle",
            ...     image="bottle.jpg"
            ... )
            >>> embeddings.keys()
            dict_keys(['text', 'image'])
        """
        embeddings = {}

        # Text embedding
        if text:
            embeddings['text'] = self.embed_text(text)

        # Image embedding
        if image and self.enable_image:
            embeddings['image'] = self.embed_image(image)

        # Shape embedding (Phase 6)
        if shape and self.enable_shape:
            # embeddings['shape'] = self.embed_shape(shape)
            logger.warning("Shape embedding not yet implemented (Phase 6)")

        if not embeddings:
            raise ValueError("At least one modality (text/image/shape) must be provided")

        return embeddings

    def embed_batch(
        self,
        items: List[Dict[str, Any]],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[Dict[str, List[float]]]:
        """
        Batch multi-modal embedding

        Args:
            items: List of items with 'text', 'image', 'shape' keys
            batch_size: Batch size for processing
            show_progress: Show progress bar

        Returns:
            List of embedding dictionaries

        Example:
            >>> items = [
            ...     {"text": "20파이 캡", "image": "cap1.jpg"},
            ...     {"text": "100ml 보틀", "image": "bottle1.jpg"}
            ... ]
            >>> embeddings = embedder.embed_batch(items)
        """
        if not items:
            return []

        results = []

        # Extract texts and images
        texts = [item.get('text', '') for item in items if item.get('text')]
        images = [item.get('image') for item in items if item.get('image')]

        # Batch embed texts
        text_embeddings = {}
        if texts:
            text_vecs = self.embed_texts_batch(texts, batch_size=batch_size, show_progress=show_progress)
            text_idx = 0
            for i, item in enumerate(items):
                if item.get('text'):
                    text_embeddings[i] = text_vecs[text_idx]
                    text_idx += 1

        # Batch embed images
        image_embeddings = {}
        if images and self.enable_image:
            image_vecs = self.embed_images_batch(images, batch_size=8, show_progress=show_progress)
            image_idx = 0
            for i, item in enumerate(items):
                if item.get('image'):
                    image_embeddings[i] = image_vecs[image_idx]
                    image_idx += 1

        # Combine results
        for i, item in enumerate(items):
            emb = {}
            if i in text_embeddings:
                emb['text'] = text_embeddings[i]
            if i in image_embeddings:
                emb['image'] = image_embeddings[i]
            results.append(emb)

        return results

    # ==================== Utility Methods ====================

    def get_dimensions(self) -> Dict[str, int]:
        """
        Get embedding dimensions for each modality

        Returns:
            Dictionary with dimensions: {"text": 384, "image": 1024, "shape": 128}
        """
        dims = {"text": self.text_dim}

        if self.enable_image:
            dims["image"] = self.image_dim

        if self.enable_shape:
            dims["shape"] = 128  # Phase 6

        return dims

    def is_available(self, modality: str) -> bool:
        """
        Check if a modality is available

        Args:
            modality: 'text', 'image', or 'shape'

        Returns:
            True if modality is available
        """
        if modality == 'text':
            return True
        elif modality == 'image':
            return self.enable_image
        elif modality == 'shape':
            return self.enable_shape
        else:
            return False

    def __repr__(self):
        return (
            f"MultiModalEmbeddingService("
            f"text={self.text_dim}d, "
            f"image={self.image_dim if self.enable_image else 'disabled'}d, "
            f"device={self.device})"
        )


# ==================== Convenience Functions ====================

def create_embedder(
    device: str = 'auto',
    enable_image: bool = True
) -> MultiModalEmbeddingService:
    """
    Create a default MultiModalEmbeddingService

    Args:
        device: Device to use ('auto', 'cpu', 'cuda', 'mps')
        enable_image: Enable image embedding

    Returns:
        Configured MultiModalEmbeddingService
    """
    return MultiModalEmbeddingService(device=device, enable_image=enable_image)
