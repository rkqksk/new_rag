"""
Ultimate RAG API Routes - v7.4.0
Complete API for Ultimate RAG System
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

from src.services.ultimate_rag_service import (
    UltimateRAGService,
    SearchMode,
    get_ultimate_rag_service
)


class MultimodalSearchRequest(BaseModel):
    """Request for multimodal search"""
    text_query: Optional[str] = None
    mode: SearchMode = SearchMode.MULTIMODAL
    top_k: int = Field(10, ge=1, le=100)
    user_id: Optional[str] = None


class UltimateRAGRouter:
    """Ultimate RAG API Router"""

    def __init__(self, service: Optional[UltimateRAGService] = None):
        self.router = APIRouter(prefix="/ultimate-rag", tags=["Ultimate RAG"])
        self.service = service or get_ultimate_rag_service()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.router.post("/search")
        async def multimodal_search(request: MultimodalSearchRequest):
            """
            Multimodal search with CLIP
            
            Modes:
            - text_only: Text → Text
            - image_only: Image → Image
            - multimodal: Text + Image → Combined
            - cross_modal: Text → Image or Image → Text
            """
            try:
                results = await self.service.multimodal_search(
                    text_query=request.text_query,
                    image_query=None,  # Would be passed as file
                    mode=request.mode,
                    top_k=request.top_k,
                    user_id=request.user_id
                )
                return {"results": results}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

        @self.router.post("/search-with-image")
        async def search_with_image(
            text_query: Optional[str] = None,
            image: UploadFile = File(...),
            mode: SearchMode = SearchMode.MULTIMODAL,
            top_k: int = 10,
            user_id: Optional[str] = None
        ):
            """Search with uploaded image"""
            try:
                image_bytes = await image.read()
                
                results = await self.service.multimodal_search(
                    text_query=text_query,
                    image_query=image_bytes,
                    mode=mode,
                    top_k=top_k,
                    user_id=user_id
                )
                return {"results": results}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

        @self.router.get("/cache-stats")
        async def get_cache_stats():
            """
            Get semantic cache statistics
            
            Returns:
            - Cache hit rate (target 99%)
            - Cache size
            - Total searches
            """
            try:
                stats = self.service.get_stats()
                return {
                    "cache_hit_rate": stats.get("cache_hit_rate", 0.0),
                    "cache_size": stats.get("cache_size", 0),
                    "cache_hits": self.service.stats["cache_hits"],
                    "cache_misses": self.service.stats["cache_misses"],
                    "total_searches": self.service.stats["total_searches"]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

        @self.router.delete("/cache")
        async def clear_cache():
            """Clear semantic cache"""
            try:
                self.service.cache.clear()
                return {"status": "cleared", "message": "Cache cleared successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

        @self.router.get("/stats")
        async def get_stats():
            """Get comprehensive RAG statistics"""
            try:
                return self.service.get_stats()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "Ultimate RAG",
                "version": "7.4.0",
                "features": {
                    "caching": self.service.enable_caching,
                    "personalization": self.service.enable_personalization
                },
                "stats": self.service.get_stats()
            }


def get_ultimate_rag_router(service: Optional[UltimateRAGService] = None) -> APIRouter:
    """Factory function to create router"""
    router_instance = UltimateRAGRouter(service=service)
    return router_instance.router
