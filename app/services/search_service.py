"""
SearchService - Complete Integration

Integrates all existing systems:
- Tri-modal search (Text + Image + Shape)
- Query routing
- Cross-encoder re-ranking  
- Personalization
- Compatibility filtering
"""
from typing import List, Dict, Any, Optional
import logging

# Import existing systems from src/
from src.core.multimodal.multimodal_embedder import MultiModalEmbedder
from src.core.enhancements.cross_encoder_reranker import CrossEncoderReranker
from src.core.enhancements.query_router import QueryRouter
from src.core.recommendation.advanced_personalization_service import AdvancedPersonalizationService

logger = logging.getLogger(__name__)

class SearchService:
    """
    High-level search service
    
    Features:
    - Tri-modal vector search
    - Query routing (automatic strategy selection)
    - Cross-encoder re-ranking
    - Personalized results
    - Compatibility filtering
    - Caching
    """
    
    def __init__(
        self,
        qdrant_repo,
        redis_repo,
        postgres_repo=None
    ):
        """Initialize service with dependencies"""
        self.qdrant = qdrant_repo
        self.redis = redis_repo
        self.postgres = postgres_repo
        
        # Initialize existing systems
        logger.info("Initializing search components...")
        
        try:
            self.embedder = MultiModalEmbedder(
                enable_text=True,
                enable_image=True,
                enable_shape=False  # Enable if needed
            )
            logger.info("✅ MultiModalEmbedder initialized")
        except Exception as e:
            logger.warning(f"MultiModalEmbedder init failed: {e}")
            self.embedder = None
        
        try:
            self.reranker = CrossEncoderReranker()
            logger.info("✅ CrossEncoderReranker initialized")
        except Exception as e:
            logger.warning(f"CrossEncoderReranker init failed: {e}")
            self.reranker = None
        
        try:
            self.router = QueryRouter()
            logger.info("✅ QueryRouter initialized")
        except Exception as e:
            logger.warning(f"QueryRouter init failed: {e}")
            self.router = None
        
        try:
            self.personalization = AdvancedPersonalizationService(
                database=postgres_repo,
                redis_client=redis_repo,
                enable_adaptive_weights=True,
                enable_global_analytics=True,
                enable_compatibility_filter=True
            )
            logger.info("✅ AdvancedPersonalizationService initialized")
        except Exception as e:
            logger.warning(f"PersonalizationService init failed: {e}")
            self.personalization = None
    
    async def search(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 20,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Execute comprehensive search pipeline
        
        Args:
            query: Search query
            session_id: User session ID for personalization
            top_k: Number of results
            use_cache: Use Redis cache
        
        Returns:
            Search results with metadata
        """
        try:
            # Step 1: Check cache
            if use_cache:
                cache_key = f"search:{query}:{session_id}:{top_k}"
                cached = await self.redis.get(cache_key)
                if cached:
                    logger.info(f"Cache hit for: {query}")
                    return cached
            
            # Step 2: Query routing (determine best strategy)
            routing_info = {}
            if self.router:
                routing_info = self.router.route_query(query)
                logger.info(f"Query routing: {routing_info.get('query_type')}")
            
            # Step 3: Generate embeddings
            embeddings = {}
            if self.embedder:
                embeddings = self.embedder.embed(text=query)
            
            # Step 4: Vector search
            search_results = []
            if embeddings and embeddings.get('text') is not None:
                search_results = await self.qdrant.search(
                    collection_name="products_multimodal",
                    query_vector=embeddings['text'].tolist(),
                    limit=top_k * 2  # Get more for re-ranking
                )
            
            # Step 5: Cross-encoder re-ranking
            if self.reranker and search_results:
                # Extract text from results
                results_for_rerank = [
                    {
                        **r,
                        'text': r['payload'].get('name', '') + ' ' + r['payload'].get('description', '')
                    }
                    for r in search_results
                ]
                
                reranked = self.reranker.rerank(
                    query=query,
                    results=results_for_rerank,
                    top_k=top_k,
                    text_field='text'
                )
                search_results = reranked
            
            # Step 6: Personalization & Compatibility filtering
            if self.personalization and session_id:
                # Track search
                self.personalization.track_search(
                    session_id=session_id,
                    query=query,
                    results_count=len(search_results)
                )
                
                # Apply personalization
                search_results = self.personalization.personalize_search_results(
                    session_id=session_id,
                    results=search_results,
                    query=query,
                    top_k=top_k
                )
            
            # Step 7: Format response
            response = {
                "results": search_results[:top_k],
                "total": len(search_results),
                "query": query,
                "session_id": session_id,
                "routing": routing_info,
                "cached": False
            }
            
            # Step 8: Cache results
            if use_cache:
                await self.redis.set(cache_key, response, ttl=300)  # 5 min cache
            
            return response
        
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return {
                "results": [],
                "total": 0,
                "error": str(e),
                "query": query,
                "session_id": session_id
            }
    
    async def image_search(
        self,
        image_path: str,
        session_id: Optional[str] = None,
        top_k: int = 20
    ) -> Dict[str, Any]:
        """
        Image-based search
        
        Args:
            image_path: Path to image file
            session_id: User session ID
            top_k: Number of results
        
        Returns:
            Search results
        """
        try:
            # Generate image embedding
            if not self.embedder:
                return {"error": "Embedder not initialized", "results": []}
            
            embeddings = self.embedder.embed(image=image_path)
            
            if embeddings.get('image') is None:
                return {"error": "Image embedding failed", "results": []}
            
            # Search with image vector
            results = await self.qdrant.search(
                collection_name="products_multimodal",
                query_vector=embeddings['image'].tolist(),
                limit=top_k
            )
            
            return {
                "results": results,
                "total": len(results),
                "session_id": session_id,
                "search_type": "image"
            }
        
        except Exception as e:
            logger.error(f"Image search error: {e}")
            return {"error": str(e), "results": []}
    
    async def hybrid_search(
        self,
        query: Optional[str] = None,
        image_path: Optional[str] = None,
        text_weight: float = 0.6,
        image_weight: float = 0.4,
        session_id: Optional[str] = None,
        top_k: int = 20
    ) -> Dict[str, Any]:
        """
        Hybrid search (text + image)
        
        Args:
            query: Text query
            image_path: Image path
            text_weight: Weight for text
            image_weight: Weight for image
            session_id: User session ID
            top_k: Number of results
        
        Returns:
            Fused search results
        """
        try:
            if not self.embedder:
                return {"error": "Embedder not initialized", "results": []}
            
            # Generate embeddings
            query_vectors = {}
            
            if query:
                embeddings = self.embedder.embed(text=query)
                if embeddings.get('text') is not None:
                    query_vectors['text'] = embeddings['text'].tolist()
            
            if image_path:
                embeddings = self.embedder.embed(image=image_path)
                if embeddings.get('image') is not None:
                    query_vectors['image'] = embeddings['image'].tolist()
            
            if not query_vectors:
                return {"error": "No valid embeddings", "results": []}
            
            # Multi-vector search
            weights = {}
            if 'text' in query_vectors:
                weights['text'] = text_weight
            if 'image' in query_vectors:
                weights['image'] = image_weight
            
            results = await self.qdrant.search_multi_vector(
                collection_name="products_multimodal",
                query_vectors=query_vectors,
                weights=weights,
                limit=top_k
            )
            
            return {
                "results": results,
                "total": len(results),
                "session_id": session_id,
                "search_type": "hybrid",
                "weights": weights
            }
        
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return {"error": str(e), "results": []}
