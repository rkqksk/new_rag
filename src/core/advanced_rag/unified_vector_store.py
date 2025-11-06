"""
Unified Vector Store Manager
Manages multiple Qdrant collections for integrated search
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)


@dataclass
class CollectionConfig:
    """Configuration for a collection"""
    name: str
    vector_size: int
    distance: Distance = Distance.COSINE
    description: str = ""
    enabled: bool = True


class UnifiedVectorStore:
    """
    Unified Vector Store Manager

    Manages multiple collections:
    - products_multimodal: Product data (text 384, image 1024, shape 128)
    - documents_semantic: PDF documents (text 384)
    - images_visual: Product images (image 1024)
    - tables_structured: Table data (text 384)
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collections: Optional[List[CollectionConfig]] = None
    ):
        """
        Initialize Unified Vector Store

        Args:
            qdrant_client: Qdrant client instance
            collections: List of collection configurations
        """
        self.client = qdrant_client
        self.collections = collections or self._default_collections()

        # Verify collections
        self._verify_collections()

        logger.info(f"✅ Unified Vector Store initialized with {len(self.collections)} collections")

    def _default_collections(self) -> List[CollectionConfig]:
        """Default collection configurations"""
        return [
            CollectionConfig(
                name="products_multimodal",
                vector_size=384,  # Text dimension (primary)
                description="Multi-modal product data (text, image, shape)",
                enabled=True
            ),
            CollectionConfig(
                name="documents_semantic",
                vector_size=384,
                description="PDF documents and manuals",
                enabled=False  # Not yet created
            ),
            CollectionConfig(
                name="images_visual",
                vector_size=1024,
                description="Product images",
                enabled=False  # Not yet created
            ),
            CollectionConfig(
                name="tables_structured",
                vector_size=384,
                description="Structured table data",
                enabled=False  # Not yet created
            )
        ]

    def _verify_collections(self):
        """Verify that collections exist"""
        existing_collections = {
            col.name for col in self.client.get_collections().collections
        }

        for collection in self.collections:
            if collection.enabled:
                if collection.name not in existing_collections:
                    logger.warning(f"⚠️  Collection '{collection.name}' not found (disabled)")
                    collection.enabled = False
                else:
                    logger.info(f"✅ Collection '{collection.name}' verified")

    def get_enabled_collections(self) -> List[CollectionConfig]:
        """Get list of enabled collections"""
        return [col for col in self.collections if col.enabled]

    def get_collection(self, name: str) -> Optional[CollectionConfig]:
        """Get collection by name"""
        for col in self.collections:
            if col.name == name:
                return col
        return None

    def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
        description: str = "",
        **kwargs
    ) -> bool:
        """
        Create a new collection

        Args:
            name: Collection name
            vector_size: Vector dimension
            distance: Distance metric
            description: Collection description
            **kwargs: Additional Qdrant parameters

        Returns:
            True if created successfully
        """
        try:
            # Check if already exists
            existing = {col.name for col in self.client.get_collections().collections}

            if name in existing:
                logger.warning(f"Collection '{name}' already exists")
                return False

            # Create collection
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                ),
                **kwargs
            )

            # Add to managed collections
            config = CollectionConfig(
                name=name,
                vector_size=vector_size,
                distance=distance,
                description=description,
                enabled=True
            )

            self.collections.append(config)

            logger.info(f"✅ Created collection '{name}' ({vector_size}-dim)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create collection '{name}': {e}")
            return False

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection

        Args:
            name: Collection name

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_collection(name)

            # Remove from managed collections
            self.collections = [col for col in self.collections if col.name != name]

            logger.info(f"✅ Deleted collection '{name}'")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete collection '{name}': {e}")
            return False

    def get_collection_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a collection"""
        try:
            collection_info = self.client.get_collection(name)

            return {
                'name': name,
                'points_count': collection_info.points_count,
                'vectors_count': collection_info.vectors_count,
                'indexed_vectors_count': collection_info.indexed_vectors_count,
                'status': collection_info.status
            }

        except Exception as e:
            logger.error(f"Failed to get stats for '{name}': {e}")
            return {}

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all enabled collections"""
        stats = {}

        for collection in self.get_enabled_collections():
            stats[collection.name] = self.get_collection_stats(collection.name)

        return stats

    async def search_async(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Any]:
        """
        Async search in a single collection

        Args:
            collection_name: Collection to search
            query_vector: Query embedding
            limit: Number of results
            filters: Optional filters

        Returns:
            List of search results
        """
        loop = asyncio.get_event_loop()

        # Run blocking search in thread pool
        results = await loop.run_in_executor(
            None,
            lambda: self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filters
            )
        )

        return results

    async def search_parallel(
        self,
        queries: Dict[str, tuple],
        limit: int = 10
    ) -> Dict[str, List[Any]]:
        """
        Search multiple collections in parallel

        Args:
            queries: Dict of {collection_name: (query_vector, filters)}
            limit: Number of results per collection

        Returns:
            Dict of {collection_name: [results]}

        Example:
            >>> queries = {
            ...     'products_multimodal': (text_emb, None),
            ...     'documents_semantic': (text_emb, {'type': 'manual'})
            ... }
            >>> results = await store.search_parallel(queries, limit=10)
        """
        # Create tasks for each collection
        tasks = []
        collection_names = []

        for collection_name, (query_vector, filters) in queries.items():
            # Check if collection is enabled
            collection = self.get_collection(collection_name)
            if not collection or not collection.enabled:
                logger.warning(f"Skipping disabled collection: {collection_name}")
                continue

            task = self.search_async(
                collection_name,
                query_vector,
                limit=limit,
                filters=filters
            )

            tasks.append(task)
            collection_names.append(collection_name)

        # Execute all searches in parallel
        if not tasks:
            return {}

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Build results dict
        results = {}
        for collection_name, result in zip(collection_names, results_list):
            if isinstance(result, Exception):
                logger.error(f"Search failed for '{collection_name}': {result}")
                results[collection_name] = []
            else:
                results[collection_name] = result

        return results

    def search_all(
        self,
        query_vectors: Dict[str, List[float]],
        limit: int = 10,
        filters: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, List[Any]]:
        """
        Synchronous search across all enabled collections

        Args:
            query_vectors: Dict of {collection_name: query_vector}
            limit: Number of results per collection
            filters: Optional dict of {collection_name: filters}

        Returns:
            Dict of {collection_name: [results]}
        """
        results = {}
        filters = filters or {}

        for collection in self.get_enabled_collections():
            name = collection.name

            if name not in query_vectors:
                continue

            try:
                search_results = self.client.search(
                    collection_name=name,
                    query_vector=query_vectors[name],
                    limit=limit,
                    query_filter=filters.get(name)
                )

                results[name] = search_results

            except Exception as e:
                logger.error(f"Search failed for '{name}': {e}")
                results[name] = []

        return results

    def __repr__(self):
        enabled_count = len(self.get_enabled_collections())
        total_count = len(self.collections)

        return (
            f"UnifiedVectorStore("
            f"enabled={enabled_count}/{total_count}, "
            f"collections={[col.name for col in self.get_enabled_collections()]})"
        )
