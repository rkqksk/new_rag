"""
Advanced RAG API Routes - v7.3.0
Enterprise-grade RAG with hybrid search and intelligent routing
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.advanced_rag_service import (
    AdvancedRAGService,
    QueryType,
    RetrievalStrategy,
    SearchResult,
    RAGMetrics,
    get_advanced_rag_service
)


# ========================================================================
# Request/Response Models
# ========================================================================

class AdvancedSearchRequest(BaseModel):
    """Request model for advanced RAG search"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    strategy: Optional[RetrievalStrategy] = Field(None, description="Force specific strategy")
    enable_reranking: bool = Field(True, description="Enable cross-encoder reranking")
    enable_compression: bool = Field(True, description="Enable context compression")
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="Hybrid search weight (0=BM25, 1=Vector)")


class AdvancedSearchResponse(BaseModel):
    """Response model for advanced RAG search"""
    results: List[Dict[str, Any]]
    query_type: QueryType
    strategy_used: RetrievalStrategy
    metrics: Dict[str, Any]
    compressed_context: Optional[str] = None


class QueryAnalysisRequest(BaseModel):
    """Request model for query analysis"""
    query: str = Field(..., min_length=1, max_length=1000)


class QueryAnalysisResponse(BaseModel):
    """Response model for query analysis"""
    query_type: QueryType
    confidence: float
    recommended_strategy: RetrievalStrategy
    query_variations: Optional[List[str]] = None


class MetricsSummaryResponse(BaseModel):
    """Response model for metrics summary"""
    total_queries: int
    avg_retrieval_time_ms: float
    avg_num_results: float
    avg_score: float
    query_type_distribution: Dict[str, int]
    strategy_distribution: Dict[str, int]


# ========================================================================
# Router Class
# ========================================================================

class AdvancedRAGRouter:
    """Advanced RAG API Router"""

    def __init__(self, rag_service: Optional[AdvancedRAGService] = None):
        """
        Initialize Advanced RAG Router

        Args:
            rag_service: Advanced RAG service instance
        """
        self.router = APIRouter(prefix="/advanced-rag", tags=["Advanced RAG"])
        self.rag_service = rag_service or get_advanced_rag_service()
        self._setup_routes()

    def _setup_routes(self):
        """Configure API routes"""

        @self.router.post("/search", response_model=AdvancedSearchResponse)
        async def advanced_search(request: AdvancedSearchRequest):
            """
            Advanced RAG search with hybrid retrieval and intelligent routing

            Features:
            - Automatic query classification
            - Strategy routing (hybrid/multi-query/parent-doc)
            - Cross-encoder reranking
            - Context compression
            - Performance metrics
            """
            try:
                start_time = datetime.now()

                # Perform search
                results = await self.rag_service.search(
                    query=request.query,
                    top_k=request.top_k,
                    strategy=request.strategy,
                    enable_reranking=request.enable_reranking,
                    enable_compression=request.enable_compression,
                    alpha=request.alpha
                )

                # Extract metrics
                query_type = results.get("query_type", QueryType.FACTUAL)
                strategy_used = results.get("strategy_used", RetrievalStrategy.HYBRID)
                search_results = results.get("results", [])
                compressed_context = results.get("compressed_context")

                retrieval_time_ms = (datetime.now() - start_time).total_seconds() * 1000

                metrics = {
                    "retrieval_time_ms": retrieval_time_ms,
                    "num_results": len(search_results),
                    "avg_score": sum(r["score"] for r in search_results) / len(search_results) if search_results else 0.0,
                    "context_compression_ratio": results.get("context_compression_ratio"),
                }

                return AdvancedSearchResponse(
                    results=search_results,
                    query_type=query_type,
                    strategy_used=strategy_used,
                    metrics=metrics,
                    compressed_context=compressed_context
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

        @self.router.post("/analyze-query", response_model=QueryAnalysisResponse)
        async def analyze_query(request: QueryAnalysisRequest):
            """
            Analyze query and recommend optimal retrieval strategy

            Returns:
            - Query classification (factual/analytical/comparative/procedural/troubleshooting)
            - Confidence score
            - Recommended retrieval strategy
            - Query variations for multi-query retrieval
            """
            try:
                # Classify query
                query_type, confidence = await self.rag_service.classify_query(request.query)

                # Get recommended strategy
                recommended_strategy = self.rag_service.route_query(query_type)

                # Generate query variations (for multi-query strategy)
                query_variations = None
                if recommended_strategy == RetrievalStrategy.MULTI_QUERY:
                    query_variations = await self.rag_service._generate_query_variations(request.query)

                return QueryAnalysisResponse(
                    query_type=query_type,
                    confidence=confidence,
                    recommended_strategy=recommended_strategy,
                    query_variations=query_variations
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")

        @self.router.post("/hybrid-search")
        async def hybrid_search(
            query: str = Query(..., min_length=1, max_length=1000),
            top_k: int = Query(5, ge=1, le=50),
            alpha: float = Query(0.5, ge=0.0, le=1.0)
        ):
            """
            Direct hybrid search (BM25 + Vector with RRF)

            Args:
                query: Search query
                top_k: Number of results
                alpha: Hybrid weight (0=BM25 only, 1=Vector only, 0.5=balanced)

            Returns:
                Fused search results with scores
            """
            try:
                results = await self.rag_service.hybrid_search(
                    query=query,
                    top_k=top_k,
                    alpha=alpha
                )

                return {
                    "results": results,
                    "method": "hybrid_search",
                    "alpha": alpha
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")

        @self.router.post("/multi-query-retrieval")
        async def multi_query_retrieval(
            query: str = Query(..., min_length=1, max_length=1000),
            top_k: int = Query(5, ge=1, le=50),
            num_variations: int = Query(3, ge=2, le=5)
        ):
            """
            Multi-query retrieval (generate query variations and merge results)

            Useful for:
            - Complex analytical queries
            - Capturing different aspects of the question
            - Improving recall

            Args:
                query: Original query
                top_k: Number of results per variation
                num_variations: Number of query variations to generate
            """
            try:
                results = await self.rag_service.multi_query_retrieval(
                    query=query,
                    top_k=top_k
                )

                return {
                    "results": results,
                    "method": "multi_query_retrieval"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Multi-query retrieval failed: {str(e)}")

        @self.router.post("/parent-document-retrieval")
        async def parent_document_retrieval(
            query: str = Query(..., min_length=1, max_length=1000),
            top_k: int = Query(5, ge=1, le=50)
        ):
            """
            Parent document retrieval (retrieve full parent documents)

            Useful for:
            - Procedural queries (how-to guides)
            - Questions requiring full context
            - Multi-step procedures

            Returns full documents instead of chunks for better context.
            """
            try:
                results = await self.rag_service.parent_document_retrieval(
                    query=query,
                    top_k=top_k
                )

                return {
                    "results": results,
                    "method": "parent_document_retrieval"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Parent document retrieval failed: {str(e)}")

        @self.router.post("/rerank")
        async def rerank_results(
            query: str = Query(..., min_length=1, max_length=1000),
            candidates: List[Dict[str, Any]] = None
        ):
            """
            Rerank search results using cross-encoder

            Improves precision by reordering results based on relevance.

            Args:
                query: Search query
                candidates: List of candidate results to rerank
            """
            try:
                if not candidates:
                    raise HTTPException(status_code=400, detail="No candidates provided for reranking")

                # Convert to SearchResult objects
                search_results = []
                for i, candidate in enumerate(candidates):
                    search_results.append(
                        SearchResult(
                            document_id=candidate.get("document_id", f"doc_{i}"),
                            content=candidate.get("content", ""),
                            score=candidate.get("score", 0.0),
                            metadata=candidate.get("metadata", {}),
                            rank=i,
                            retrieval_method="external"
                        )
                    )

                reranked = await self.rag_service.rerank_results(
                    query=query,
                    results=search_results
                )

                return {
                    "results": [r.dict() for r in reranked],
                    "method": "cross_encoder_reranking"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Reranking failed: {str(e)}")

        @self.router.post("/compress-context")
        async def compress_context(
            query: str = Query(..., min_length=1, max_length=1000),
            context: str = Query(..., min_length=1),
            target_ratio: float = Query(0.3, ge=0.1, le=0.8)
        ):
            """
            Compress context while preserving query-relevant information

            Reduces context size by 2-5x while maintaining relevance.

            Args:
                query: Search query
                context: Original context to compress
                target_ratio: Target compression ratio (0.3 = 70% reduction)
            """
            try:
                compressed = await self.rag_service.compress_context(
                    query=query,
                    context=context,
                    target_ratio=target_ratio
                )

                original_length = len(context)
                compressed_length = len(compressed)
                actual_ratio = compressed_length / original_length if original_length > 0 else 0

                return {
                    "original_context": context,
                    "compressed_context": compressed,
                    "original_length": original_length,
                    "compressed_length": compressed_length,
                    "compression_ratio": actual_ratio,
                    "compression_factor": f"{1/actual_ratio:.1f}x" if actual_ratio > 0 else "N/A"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Context compression failed: {str(e)}")

        @self.router.get("/metrics/summary", response_model=MetricsSummaryResponse)
        async def get_metrics_summary():
            """
            Get RAG performance metrics summary

            Returns:
            - Total queries processed
            - Average retrieval time
            - Average number of results
            - Average relevance score
            - Query type distribution
            - Strategy usage distribution
            """
            try:
                summary = self.rag_service.get_metrics_summary()
                return MetricsSummaryResponse(**summary)

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

        @self.router.get("/health")
        async def health_check():
            """
            Health check endpoint

            Returns service status and configuration
            """
            return {
                "status": "healthy",
                "service": "Advanced RAG",
                "version": "7.3.0",
                "features": {
                    "hybrid_search": self.rag_service.enable_hybrid,
                    "reranking": self.rag_service.enable_reranking,
                    "compression": self.rag_service.enable_compression
                },
                "metrics_count": len(self.rag_service.metrics)
            }


def get_advanced_rag_router(rag_service: Optional[AdvancedRAGService] = None) -> APIRouter:
    """
    Factory function to create Advanced RAG router

    Args:
        rag_service: Optional Advanced RAG service instance

    Returns:
        Configured APIRouter
    """
    router_instance = AdvancedRAGRouter(rag_service=rag_service)
    return router_instance.router
