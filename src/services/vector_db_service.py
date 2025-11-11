"""
Vector Database Service - v7.4.0
Real Qdrant integration with hybrid search support
"""

from typing import List, Dict, Optional, Any, Union, Tuple
from enum import Enum
from datetime import datetime
import uuid

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
        Range,
        SearchRequest,
        SparseVector,
        SparseVectorParams,
        NamedVector,
        NamedSparseVector
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


class DistanceMetric(str, Enum):
    """Distance metric for vector similarity"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot"


class VectorDBService:
    """
    Qdrant vector database service

    Features:
    - Dense vector search
    - Sparse vector search (keyword-based)
    - Hybrid search (dense + sparse)
    - Metadata filtering
    - Batch operations
    - Collection management
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        timeout: int = 30,
        prefer_grpc: bool = False
    ):
        if not QDRANT_AVAILABLE:
            raise ImportError("qdrant-client not installed. Run: pip install qdrant-client")

        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=timeout,
            prefer_grpc=prefer_grpc
        )

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: DistanceMetric = DistanceMetric.COSINE,
        enable_sparse: bool = True,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Create vector collection

        Args:
            collection_name: Collection name
            vector_size: Vector dimension
            distance: Distance metric (cosine, euclidean, dot)
            enable_sparse: Enable sparse vectors for hybrid search
            overwrite: Overwrite if exists

        Returns:
            Collection info
        """
        # Delete if exists and overwrite is True
        if overwrite:
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass

        # Map distance metric
        distance_map = {
            DistanceMetric.COSINE: Distance.COSINE,
            DistanceMetric.EUCLIDEAN: Distance.EUCLIDEAN,
            DistanceMetric.DOT_PRODUCT: Distance.DOT
        }

        # Create collection config
        vectors_config = {
            "dense": VectorParams(
                size=vector_size,
                distance=distance_map[distance]
            )
        }

        # Add sparse vector support for hybrid search
        if enable_sparse:
            vectors_config["sparse"] = SparseVectorParams()

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config
        )

        return {
            "collection_name": collection_name,
            "vector_size": vector_size,
            "distance": distance,
            "sparse_enabled": enable_sparse,
            "created_at": datetime.now().isoformat()
        }

    def upsert(
        self,
        collection_name: str,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        sparse_vector: Optional[Dict[int, float]] = None
    ) -> str:
        """
        Insert or update vector

        Args:
            collection_name: Collection name
            id: Point ID
            vector: Dense vector
            metadata: Metadata payload
            sparse_vector: Sparse vector for hybrid search (optional)

        Returns:
            Point ID
        """
        # Prepare vectors
        vectors = {"dense": vector}
        if sparse_vector:
            # Convert dict to sparse vector format
            indices = list(sparse_vector.keys())
            values = list(sparse_vector.values())
            vectors["sparse"] = SparseVector(indices=indices, values=values)

        point = PointStruct(
            id=id,
            vector=vectors,
            payload=metadata or {}
        )

        self.client.upsert(
            collection_name=collection_name,
            points=[point]
        )

        return id

    def upsert_batch(
        self,
        collection_name: str,
        ids: List[str],
        vectors: List[List[float]],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        sparse_vectors: Optional[List[Dict[int, float]]] = None,
        batch_size: int = 100
    ) -> List[str]:
        """
        Batch insert or update vectors

        Args:
            collection_name: Collection name
            ids: List of point IDs
            vectors: List of dense vectors
            metadata_list: List of metadata payloads
            sparse_vectors: List of sparse vectors (optional)
            batch_size: Batch size for upload

        Returns:
            List of point IDs
        """
        if metadata_list is None:
            metadata_list = [{}] * len(ids)

        points = []
        for i, (id_, vector, metadata) in enumerate(zip(ids, vectors, metadata_list)):
            # Prepare vectors
            vector_dict = {"dense": vector}
            if sparse_vectors and i < len(sparse_vectors):
                sparse = sparse_vectors[i]
                indices = list(sparse.keys())
                values = list(sparse.values())
                vector_dict["sparse"] = SparseVector(indices=indices, values=values)

            point = PointStruct(
                id=id_,
                vector=vector_dict,
                payload=metadata
            )
            points.append(point)

        # Upload in batches
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=batch
            )

        return ids

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Dense vector search

        Args:
            collection_name: Collection name
            query_vector: Query vector
            top_k: Number of results
            score_threshold: Minimum similarity score
            filters: Metadata filters

        Returns:
            Search results with scores
        """
        # Build filter
        query_filter = self._build_filter(filters) if filters else None

        # Search
        results = self.client.search(
            collection_name=collection_name,
            query_vector=("dense", query_vector),
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=query_filter
        )

        # Format results
        return [
            {
                "id": result.id,
                "score": result.score,
                "metadata": result.payload
            }
            for result in results
        ]

    def hybrid_search(
        self,
        collection_name: str,
        dense_vector: List[float],
        sparse_vector: Dict[int, float],
        top_k: int = 10,
        alpha: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search (dense + sparse vectors)

        Args:
            collection_name: Collection name
            dense_vector: Dense query vector
            sparse_vector: Sparse query vector (keyword-based)
            top_k: Number of results
            alpha: Weight for dense vector (1-alpha for sparse)
            filters: Metadata filters

        Returns:
            Search results with scores
        """
        # Build filter
        query_filter = self._build_filter(filters) if filters else None

        # Perform dense search
        dense_results = self.client.search(
            collection_name=collection_name,
            query_vector=("dense", dense_vector),
            limit=top_k * 2,  # Get more for reranking
            query_filter=query_filter
        )

        # Perform sparse search
        sparse_indices = list(sparse_vector.keys())
        sparse_values = list(sparse_vector.values())
        sparse_results = self.client.search(
            collection_name=collection_name,
            query_vector=("sparse", SparseVector(indices=sparse_indices, values=sparse_values)),
            limit=top_k * 2,
            query_filter=query_filter
        )

        # Merge results with weighted scores
        merged_scores = {}
        for result in dense_results:
            merged_scores[result.id] = {
                "dense_score": result.score,
                "sparse_score": 0.0,
                "metadata": result.payload
            }

        for result in sparse_results:
            if result.id in merged_scores:
                merged_scores[result.id]["sparse_score"] = result.score
            else:
                merged_scores[result.id] = {
                    "dense_score": 0.0,
                    "sparse_score": result.score,
                    "metadata": result.payload
                }

        # Calculate hybrid scores
        results = []
        for id_, scores in merged_scores.items():
            hybrid_score = (alpha * scores["dense_score"] +
                          (1 - alpha) * scores["sparse_score"])
            results.append({
                "id": id_,
                "score": hybrid_score,
                "dense_score": scores["dense_score"],
                "sparse_score": scores["sparse_score"],
                "metadata": scores["metadata"]
            })

        # Sort by hybrid score
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]

    def delete(self, collection_name: str, ids: List[str]) -> bool:
        """Delete points by IDs"""
        self.client.delete(
            collection_name=collection_name,
            points_selector=ids
        )
        return True

    def delete_collection(self, collection_name: str) -> bool:
        """Delete collection"""
        self.client.delete_collection(collection_name)
        return True

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        info = self.client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.points_count,
            "status": info.status,
            "config": {
                "distance": info.config.params.vectors.get("dense").distance if info.config.params.vectors else None,
                "vector_size": info.config.params.vectors.get("dense").size if info.config.params.vectors else None
            }
        }

    def list_collections(self) -> List[str]:
        """List all collections"""
        collections = self.client.get_collections()
        return [col.name for col in collections.collections]

    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from dict"""
        conditions = []

        for field, value in filters.items():
            if isinstance(value, (str, int, bool)):
                # Exact match
                conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=value)
                    )
                )
            elif isinstance(value, dict):
                # Range query
                if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                    conditions.append(
                        FieldCondition(
                            key=field,
                            range=Range(
                                gte=value.get("gte"),
                                lte=value.get("lte"),
                                gt=value.get("gt"),
                                lt=value.get("lt")
                            )
                        )
                    )

        return Filter(must=conditions) if conditions else None

    def count(self, collection_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count points in collection"""
        query_filter = self._build_filter(filters) if filters else None
        result = self.client.count(
            collection_name=collection_name,
            count_filter=query_filter
        )
        return result.count


# Global instance
_vector_db_service: Optional[VectorDBService] = None


def get_vector_db_service(
    url: str = "http://localhost:6333",
    api_key: Optional[str] = None
) -> VectorDBService:
    """
    Get or create vector DB service instance

    Args:
        url: Qdrant URL
        api_key: API key (optional)

    Returns:
        VectorDBService instance
    """
    global _vector_db_service

    if _vector_db_service is None:
        _vector_db_service = VectorDBService(url=url, api_key=api_key)

    return _vector_db_service


# Convenience functions
async def create_collection(
    collection_name: str,
    vector_size: int,
    distance: DistanceMetric = DistanceMetric.COSINE
) -> Dict[str, Any]:
    """Quick function to create collection"""
    service = get_vector_db_service()
    return service.create_collection(collection_name, vector_size, distance)


async def upsert_vector(
    collection_name: str,
    id: str,
    vector: List[float],
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Quick function to upsert vector"""
    service = get_vector_db_service()
    return service.upsert(collection_name, id, vector, metadata)


async def search_vectors(
    collection_name: str,
    query_vector: List[float],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """Quick function to search vectors"""
    service = get_vector_db_service()
    return service.search(collection_name, query_vector, top_k)
