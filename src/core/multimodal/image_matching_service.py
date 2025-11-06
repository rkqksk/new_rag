"""
Image Matching Service for Phase 6.2
Visual similarity search using image and shape embeddings
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import numpy as np

from qdrant_client import QdrantClient
from ..shape_processors import ShapeEmbedder

logger = logging.getLogger(__name__)


@dataclass
class ImageMatch:
    """Image match result"""
    product_id: str
    visual_score: float      # Image embedding similarity
    shape_score: float       # Shape embedding similarity
    combined_score: float    # Weighted combination
    payload: Dict[str, Any]
    image_url: Optional[str] = None


class ImageMatchingService:
    """
    Image Matching Service

    Visual similarity search using:
    1. Image embeddings (OpenCLIP, 1024-dim)
    2. Shape embeddings (Hu Moments + Fourier, 128-dim)
    3. Combined scoring

    Example:
        >>> service = ImageMatchingService(qdrant_client, image_embedder, shape_embedder)
        >>> query_image = Image.open("query.jpg")
        >>> matches = await service.find_similar(query_image, top_k=10)
        >>> for match in matches:
        ...     print(f"{match.product_id}: {match.combined_score:.3f}")
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        image_embedder,  # OpenCLIP or similar
        shape_embedder: ShapeEmbedder,
        collection_name: str = "products_multimodal",
        visual_weight: float = 0.6,
        shape_weight: float = 0.4
    ):
        """
        Initialize Image Matching Service

        Args:
            qdrant_client: Qdrant client
            image_embedder: Image embedding service (OpenCLIP)
            shape_embedder: Shape embedding service
            collection_name: Target collection
            visual_weight: Weight for visual similarity (0-1)
            shape_weight: Weight for shape similarity (0-1)
        """
        self.client = qdrant_client
        self.image_embedder = image_embedder
        self.shape_embedder = shape_embedder
        self.collection_name = collection_name

        # Normalize weights
        total = visual_weight + shape_weight
        self.visual_weight = visual_weight / total
        self.shape_weight = shape_weight / total

        logger.info(
            f"✅ ImageMatchingService initialized "
            f"(visual:{self.visual_weight:.2f}, shape:{self.shape_weight:.2f})"
        )

    async def find_similar(
        self,
        query_image: Image.Image,
        top_k: int = 20,
        use_shape: bool = True,
        filters: Optional[Dict] = None
    ) -> List[ImageMatch]:
        """
        Find visually similar products

        Args:
            query_image: Query image
            top_k: Number of results
            use_shape: Use shape embedding (in addition to visual)
            filters: Optional Qdrant filters

        Returns:
            List of ImageMatch results

        Example:
            >>> matches = await service.find_similar(query_image, top_k=10)
        """
        # Generate embeddings
        visual_embedding = await self._generate_visual_embedding(query_image)

        if use_shape:
            shape_embedding = self.shape_embedder.encode_shape(query_image)
        else:
            shape_embedding = None

        # Search by visual similarity
        visual_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=("image", visual_embedding),  # Named vector
            limit=top_k * 2,  # Get more for fusion
            query_filter=filters
        )

        if not use_shape or shape_embedding is None:
            # Return visual results only
            return [
                ImageMatch(
                    product_id=str(point.id),
                    visual_score=point.score,
                    shape_score=0.0,
                    combined_score=point.score,
                    payload=point.payload,
                    image_url=point.payload.get("image_url")
                )
                for point in visual_results
            ]

        # Search by shape similarity
        shape_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=("shape", shape_embedding.tolist()),  # Named vector
            limit=top_k * 2,
            query_filter=filters
        )

        # Combine results
        matches = self._combine_results(visual_results, shape_results, top_k)

        logger.info(f"Found {len(matches)} similar images")

        return matches

    def find_similar_sync(
        self,
        query_image: Image.Image,
        top_k: int = 20,
        use_shape: bool = True,
        filters: Optional[Dict] = None
    ) -> List[ImageMatch]:
        """Synchronous version of find_similar"""
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.find_similar(query_image, top_k, use_shape, filters)
                )
                return future.result()
        else:
            return loop.run_until_complete(
                self.find_similar(query_image, top_k, use_shape, filters)
            )

    async def _generate_visual_embedding(self, image: Image.Image) -> List[float]:
        """Generate visual embedding (OpenCLIP)"""
        # Check if embedder has async method
        if hasattr(self.image_embedder, 'encode_image_async'):
            return await self.image_embedder.encode_image_async(image)
        else:
            # Run sync method in thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.image_embedder.encode_image,
                image
            )

    def _combine_results(
        self,
        visual_results: List,
        shape_results: List,
        top_k: int
    ) -> List[ImageMatch]:
        """
        Combine visual and shape search results

        Strategy: Weighted score fusion
        """
        # Build score maps
        visual_scores = {str(p.id): p.score for p in visual_results}
        shape_scores = {str(p.id): p.score for p in shape_results}

        # Get all unique IDs
        all_ids = set(visual_scores.keys()) | set(shape_scores.keys())

        # Build payload map
        payload_map = {}
        for p in visual_results:
            payload_map[str(p.id)] = p.payload
        for p in shape_results:
            if str(p.id) not in payload_map:
                payload_map[str(p.id)] = p.payload

        # Compute combined scores
        matches = []
        for product_id in all_ids:
            visual_score = visual_scores.get(product_id, 0.0)
            shape_score = shape_scores.get(product_id, 0.0)

            # Weighted combination
            combined_score = (
                self.visual_weight * visual_score +
                self.shape_weight * shape_score
            )

            match = ImageMatch(
                product_id=product_id,
                visual_score=visual_score,
                shape_score=shape_score,
                combined_score=combined_score,
                payload=payload_map.get(product_id, {}),
                image_url=payload_map.get(product_id, {}).get("image_url")
            )
            matches.append(match)

        # Sort by combined score
        matches.sort(key=lambda m: m.combined_score, reverse=True)

        # Return top-k
        return matches[:top_k]

    def compute_similarity(
        self,
        image1: Image.Image,
        image2: Image.Image,
        use_shape: bool = True
    ) -> Tuple[float, float, float]:
        """
        Compute similarity between two images

        Args:
            image1: First image
            image2: Second image
            use_shape: Include shape similarity

        Returns:
            (visual_similarity, shape_similarity, combined_similarity)
        """
        # Generate embeddings
        import asyncio
        loop = asyncio.get_event_loop()

        visual_emb1 = loop.run_until_complete(self._generate_visual_embedding(image1))
        visual_emb2 = loop.run_until_complete(self._generate_visual_embedding(image2))

        # Cosine similarity
        visual_sim = self._cosine_similarity(visual_emb1, visual_emb2)

        if use_shape:
            shape_emb1 = self.shape_embedder.encode_shape(image1)
            shape_emb2 = self.shape_embedder.encode_shape(image2)
            shape_sim = self.shape_embedder.similarity(shape_emb1, shape_emb2)

            combined_sim = (
                self.visual_weight * visual_sim +
                self.shape_weight * shape_sim
            )
        else:
            shape_sim = 0.0
            combined_sim = visual_sim

        return visual_sim, shape_sim, combined_sim

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def __repr__(self):
        return (
            f"ImageMatchingService("
            f"visual:{self.visual_weight:.2f}, "
            f"shape:{self.shape_weight:.2f}, "
            f"collection='{self.collection_name}')"
        )
