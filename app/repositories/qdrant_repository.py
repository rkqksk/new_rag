"""Qdrant Repository for Vector Search"""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
import logging

logger = logging.getLogger(__name__)

class QdrantRepository:
    """
    Qdrant vector database repository
    
    Features:
    - Vector search
    - Multi-vector search (text, image, shape)
    - Filtering
    - Batch operations
    """
    
    def __init__(self, host: str, port: int, api_key: Optional[str] = None):
        """Initialize Qdrant client"""
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            prefer_grpc=True,
            timeout=30
        )
        logger.info(f"✅ QdrantRepository connected to {host}:{port}")
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 20,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search
        
        Args:
            collection_name: Collection name
            query_vector: Query vector
            limit: Max results
            score_threshold: Minimum similarity score
            filter_conditions: Filter conditions
        
        Returns:
            List of search results
        """
        try:
            search_filter = None
            if filter_conditions:
                search_filter = self._build_filter(filter_conditions)
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            # Convert to dict format
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results
            ]
        
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            raise
    
    async def search_multi_vector(
        self,
        collection_name: str,
        query_vectors: Dict[str, List[float]],
        weights: Optional[Dict[str, float]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Multi-vector search (e.g., text + image + shape)
        
        Args:
            collection_name: Collection name
            query_vectors: Dict of vector_name -> vector
            weights: Optional weights for each vector
            limit: Max results
        
        Returns:
            Fused search results
        """
        # Default weights
        if weights is None:
            weights = {k: 1.0 / len(query_vectors) for k in query_vectors.keys()}
        
        # Search with each vector
        all_results = {}
        for vector_name, query_vector in query_vectors.items():
            results = await self.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit * 2  # Get more for fusion
            )
            
            # Apply weight
            weight = weights.get(vector_name, 1.0)
            for result in results:
                result_id = result["id"]
                if result_id not in all_results:
                    all_results[result_id] = {
                        "id": result_id,
                        "payload": result["payload"],
                        "scores": {},
                        "fused_score": 0.0
                    }
                
                all_results[result_id]["scores"][vector_name] = result["score"]
                all_results[result_id]["fused_score"] += result["score"] * weight
        
        # Sort by fused score
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x["fused_score"],
            reverse=True
        )
        
        return sorted_results[:limit]
    
    async def upsert(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> bool:
        """
        Insert or update points
        
        Args:
            collection_name: Collection name
            points: List of points to upsert
        
        Returns:
            Success status
        """
        try:
            point_structs = [
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                for point in points
            ]
            
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            
            logger.info(f"✅ Upserted {len(points)} points to {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Qdrant upsert error: {e}")
            return False
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> bool:
        """Create collection if not exists"""
        try:
            # Check if exists
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection {collection_name} already exists")
                return True
            
            # Create
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclidean": Distance.EUCLID,
                "Dot": Distance.DOT
            }
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE)
                )
            )
            
            logger.info(f"✅ Created collection {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Create collection error: {e}")
            return False
    
    def _build_filter(self, conditions: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from conditions"""
        # Simplified - implement based on needs
        return Filter()
    
    def close(self):
        """Close connection"""
        self.client.close()
