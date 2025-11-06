"""
Tri-Modal Search Service for Phase 6.3
Unified search using Text + Image + Shape embeddings
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import numpy as np
import asyncio

from qdrant_client import QdrantClient
from qdrant_client.models import NamedVector
from ..shape_processors import ShapeEmbedder

logger = logging.getLogger(__name__)


@dataclass
class TriModalMatch:
    """Tri-modal search result"""
    product_id: str
    text_score: float           # Text similarity (0 if not used)
    visual_score: float         # Image similarity (0 if not used)
    shape_score: float          # Shape similarity (0 if not used)
    combined_score: float       # Weighted combination
    payload: Dict[str, Any]
    image_url: Optional[str] = None
    modalities_used: List[str] = None  # ['text', 'image', 'shape']


@dataclass
class SearchQuery:
    """Multi-modal search query"""
    text: Optional[str] = None
    image: Optional[Image.Image] = None
    use_shape: bool = True
    filters: Optional[Dict] = None


class TriModalSearchService:
    """
    Tri-Modal Search Service

    Unified product search using:
    1. Text embeddings (all-MiniLM-L6-v2, 384-dim)
    2. Image embeddings (OpenCLIP, 1024-dim)
    3. Shape embeddings (Hu Moments + Fourier, 128-dim)

    Search modes:
    - Text-only: Search by product description
    - Image-only: Search by visual similarity
    - Hybrid: Text + Image for best results

    Example:
        >>> service = TriModalSearchService(client, text_embedder, image_embedder, shape_embedder)
        >>>
        >>> # Text search
        >>> query = SearchQuery(text="100ml PET 병")
        >>> matches = await service.search(query, top_k=10)
        >>>
        >>> # Image search
        >>> query = SearchQuery(image=Image.open("product.jpg"))
        >>> matches = await service.search(query, top_k=10)
        >>>
        >>> # Hybrid search
        >>> query = SearchQuery(text="50ml PP 용기", image=Image.open("sample.jpg"))
        >>> matches = await service.search(query, top_k=10)
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        text_embedder,  # Sentence Transformer or similar
        image_embedder,  # OpenCLIP or similar
        shape_embedder: ShapeEmbedder,
        collection_name: str = "products_multimodal",
        default_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize Tri-Modal Search Service

        Args:
            qdrant_client: Qdrant client
            text_embedder: Text embedding service (encode_text method)
            image_embedder: Image embedding service (encode_image method)
            shape_embedder: Shape embedding service
            collection_name: Target collection
            default_weights: Default modality weights
                           e.g., {'text': 0.5, 'visual': 0.3, 'shape': 0.2}
        """
        self.client = qdrant_client
        self.text_embedder = text_embedder
        self.image_embedder = image_embedder
        self.shape_embedder = shape_embedder
        self.collection_name = collection_name

        # Default weights
        if default_weights is None:
            self.weights = {
                'text': 0.5,
                'visual': 0.3,
                'shape': 0.2
            }
        else:
            # Normalize weights
            total = sum(default_weights.values())
            self.weights = {k: v / total for k, v in default_weights.items()}

        logger.info(
            f"✅ TriModalSearchService initialized "
            f"(text:{self.weights['text']:.2f}, "
            f"visual:{self.weights['visual']:.2f}, "
            f"shape:{self.weights['shape']:.2f})"
        )

    async def search(
        self,
        query: SearchQuery,
        top_k: int = 20,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> List[TriModalMatch]:
        """
        Execute tri-modal search

        Args:
            query: SearchQuery with text and/or image
            top_k: Number of results to return
            custom_weights: Optional custom weights for this search

        Returns:
            List of TriModalMatch results

        Example:
            >>> query = SearchQuery(text="100ml PET 병", image=image)
            >>> matches = await service.search(query, top_k=10)
        """
        # Validate query
        if query.text is None and query.image is None:
            raise ValueError("At least one of text or image must be provided")

        # Determine active modalities
        modalities_used = []
        if query.text is not None:
            modalities_used.append('text')
        if query.image is not None:
            modalities_used.extend(['visual', 'shape'] if query.use_shape else ['visual'])

        # Get weights
        weights = custom_weights if custom_weights else self.weights

        # Normalize weights for active modalities
        active_weights = {k: v for k, v in weights.items() if k in modalities_used}
        total = sum(active_weights.values())
        active_weights = {k: v / total for k, v in active_weights.items()}

        logger.info(f"Searching with modalities: {modalities_used}, weights: {active_weights}")

        # Generate embeddings in parallel
        embeddings = await self._generate_embeddings(query)

        # Execute searches in parallel
        search_results = await self._parallel_search(
            embeddings,
            top_k * 2,  # Get more for fusion
            query.filters
        )

        # Fuse results
        matches = self._fuse_results(
            search_results,
            active_weights,
            modalities_used,
            top_k
        )

        logger.info(f"Found {len(matches)} tri-modal matches")

        return matches

    def search_sync(
        self,
        query: SearchQuery,
        top_k: int = 20,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> List[TriModalMatch]:
        """Synchronous version of search()"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.search(query, top_k, custom_weights)
                )
                return future.result()
        else:
            return loop.run_until_complete(
                self.search(query, top_k, custom_weights)
            )

    async def _generate_embeddings(
        self,
        query: SearchQuery
    ) -> Dict[str, Any]:
        """Generate embeddings for all modalities"""
        embeddings = {}

        tasks = []

        # Text embedding
        if query.text is not None:
            tasks.append(('text', self._generate_text_embedding(query.text)))

        # Image embedding
        if query.image is not None:
            tasks.append(('visual', self._generate_visual_embedding(query.image)))

            # Shape embedding (if enabled)
            if query.use_shape:
                tasks.append(('shape', self._generate_shape_embedding(query.image)))

        # Execute in parallel
        results = await asyncio.gather(*[task[1] for task in tasks])

        # Map results
        for i, (name, _) in enumerate(tasks):
            embeddings[name] = results[i]

        return embeddings

    async def _generate_text_embedding(self, text: str) -> List[float]:
        """Generate text embedding"""
        # Check if embedder has async method
        if hasattr(self.text_embedder, 'encode_text_async'):
            return await self.text_embedder.encode_text_async(text)
        else:
            # Run sync method in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.text_embedder.encode_text,
                text
            )

    async def _generate_visual_embedding(self, image: Image.Image) -> List[float]:
        """Generate visual embedding (OpenCLIP)"""
        # Check if embedder has async method
        if hasattr(self.image_embedder, 'encode_image_async'):
            return await self.image_embedder.encode_image_async(image)
        else:
            # Run sync method in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.image_embedder.encode_image,
                image
            )

    async def _generate_shape_embedding(self, image: Image.Image) -> np.ndarray:
        """Generate shape embedding"""
        # Shape embedder is typically CPU-bound, run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.shape_embedder.encode_shape,
            image
        )

    async def _parallel_search(
        self,
        embeddings: Dict[str, Any],
        limit: int,
        filters: Optional[Dict] = None
    ) -> Dict[str, List]:
        """Execute parallel searches for each modality"""
        search_tasks = []

        for modality, embedding in embeddings.items():
            # Convert numpy to list if needed
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()

            # Create search task
            task = self._search_single_modality(
                modality,
                embedding,
                limit,
                filters
            )
            search_tasks.append((modality, task))

        # Execute in parallel
        results = await asyncio.gather(*[task[1] for task in search_tasks])

        # Map results
        search_results = {}
        for i, (modality, _) in enumerate(search_tasks):
            search_results[modality] = results[i]

        return search_results

    async def _search_single_modality(
        self,
        modality: str,
        embedding: List[float],
        limit: int,
        filters: Optional[Dict] = None
    ) -> List:
        """Search using a single modality"""
        # Run search in thread pool (Qdrant client is sync)
        loop = asyncio.get_event_loop()

        def _search():
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=(modality, embedding),  # Named vector
                limit=limit,
                query_filter=filters
            )

        return await loop.run_in_executor(None, _search)

    def _fuse_results(
        self,
        search_results: Dict[str, List],
        weights: Dict[str, float],
        modalities_used: List[str],
        top_k: int
    ) -> List[TriModalMatch]:
        """
        Fuse multi-modal search results

        Strategy: Weighted score fusion
        """
        # Build score maps
        score_maps = {
            modality: {str(p.id): p.score for p in results}
            for modality, results in search_results.items()
        }

        # Get all unique IDs
        all_ids = set()
        for scores in score_maps.values():
            all_ids.update(scores.keys())

        # Build payload map
        payload_map = {}
        for results in search_results.values():
            for p in results:
                if str(p.id) not in payload_map:
                    payload_map[str(p.id)] = p.payload

        # Compute combined scores
        matches = []
        for product_id in all_ids:
            text_score = score_maps.get('text', {}).get(product_id, 0.0)
            visual_score = score_maps.get('visual', {}).get(product_id, 0.0)
            shape_score = score_maps.get('shape', {}).get(product_id, 0.0)

            # Weighted combination
            combined_score = (
                weights.get('text', 0.0) * text_score +
                weights.get('visual', 0.0) * visual_score +
                weights.get('shape', 0.0) * shape_score
            )

            match = TriModalMatch(
                product_id=product_id,
                text_score=text_score,
                visual_score=visual_score,
                shape_score=shape_score,
                combined_score=combined_score,
                payload=payload_map.get(product_id, {}),
                image_url=payload_map.get(product_id, {}).get("image_url"),
                modalities_used=modalities_used
            )
            matches.append(match)

        # Sort by combined score
        matches.sort(key=lambda m: m.combined_score, reverse=True)

        # Return top-k
        return matches[:top_k]

    def set_weights(self, weights: Dict[str, float]):
        """
        Update default modality weights

        Args:
            weights: New weights dict, e.g., {'text': 0.6, 'visual': 0.3, 'shape': 0.1}
        """
        # Normalize
        total = sum(weights.values())
        self.weights = {k: v / total for k, v in weights.items()}

        logger.info(
            f"Updated weights: text={self.weights['text']:.2f}, "
            f"visual={self.weights['visual']:.2f}, shape={self.weights['shape']:.2f}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'collection': self.collection_name,
            'weights': self.weights,
            'modalities': ['text', 'visual', 'shape']
        }

    def __repr__(self):
        return (
            f"TriModalSearchService("
            f"text:{self.weights['text']:.2f}, "
            f"visual:{self.weights['visual']:.2f}, "
            f"shape:{self.weights['shape']:.2f}, "
            f"collection='{self.collection_name}')"
        )
