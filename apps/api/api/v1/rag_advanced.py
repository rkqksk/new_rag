"""
Advanced RAG API Endpoints (v6.0.0)
====================================

API endpoints for advanced RAG features:
- Query optimization
- Context compression
- Citation tracking
- Answer verification
- Conversational memory

Version: v6.0.0
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.services.rag_optimizer import RAGOptimizer
from apps.api.services.conversational_memory import (
    HistoryAwareSearcher,
    get_conversation_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class QueryOptimizationRequest(BaseModel):
    """Request for query optimization"""

    query: str = Field(..., description="Original query")
    strategy: str = Field(
        default="expand",
        description="Optimization strategy (expand, rewrite, multi, hyde)",
    )


class QueryOptimizationResponse(BaseModel):
    """Response for query optimization"""

    original_query: str
    optimized_queries: List[str]
    strategy: str


class ContextCompressionRequest(BaseModel):
    """Request for context compression"""

    query: str = Field(..., description="Search query")
    documents: List[Dict[str, Any]] = Field(..., description="Documents to compress")
    target_ratio: float = Field(default=0.5, ge=0.1, le=1.0, description="Compression ratio")


class ContextCompressionResponse(BaseModel):
    """Response for context compression"""

    compressed_documents: List[Dict[str, Any]]
    compression_ratio: float
    original_count: int
    compressed_count: int


class CitationRequest(BaseModel):
    """Request for citation"""

    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents")
    citation_style: str = Field(default="inline", description="Citation style")


class CitationResponse(BaseModel):
    """Response for citation"""

    cited_answer: str
    bibliography: List[Dict[str, Any]]
    num_citations: int


class VerificationRequest(BaseModel):
    """Request for answer verification"""

    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents")


class VerificationResponse(BaseModel):
    """Response for answer verification"""

    confidence: float
    verified_facts: int
    total_facts: int
    hallucinations: List[str]
    is_reliable: bool


class ConversationCreateRequest(BaseModel):
    """Request to create conversation"""

    user_id: str = Field(..., description="User ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class ConversationCreateResponse(BaseModel):
    """Response for conversation creation"""

    session_id: str
    user_id: str
    created_at: str


class ConversationTurnRequest(BaseModel):
    """Request to add conversation turn"""

    session_id: str = Field(..., description="Session ID")
    user_message: str = Field(..., description="User's message")
    assistant_response: str = Field(..., description="Assistant's response")
    query: Optional[str] = Field(default=None, description="Actual search query")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Retrieved sources")


class ConversationTurnResponse(BaseModel):
    """Response for conversation turn"""

    turn_id: str
    session_id: str
    timestamp: str


class ConversationContextRequest(BaseModel):
    """Request for conversation context"""

    session_id: str = Field(..., description="Session ID")
    num_turns: int = Field(default=5, ge=1, le=20, description="Number of turns")
    max_tokens: int = Field(default=2000, ge=100, le=10000, description="Max tokens")


class ConversationContextResponse(BaseModel):
    """Response for conversation context"""

    session_id: str
    context_turns: List[Dict[str, Any]]
    num_turns: int


# ============================================================================
# Query Optimization Endpoints
# ============================================================================


@router.post(
    "/optimize/query",
    response_model=QueryOptimizationResponse,
    summary="Optimize search query",
    description="Apply query optimization strategies for better retrieval",
)
async def optimize_query(request: QueryOptimizationRequest) -> QueryOptimizationResponse:
    """
    Optimize query using various strategies

    Strategies:
    - expand: Expand with synonyms and related terms
    - rewrite: Rewrite for clarity
    - multi: Generate multiple query variations
    - hyde: Generate hypothetical document (HyDE)
    """
    try:
        optimizer = RAGOptimizer()
        optimized_queries = optimizer.optimize_query(request.query, strategy=request.strategy)

        return QueryOptimizationResponse(
            original_query=request.query,
            optimized_queries=optimized_queries,
            strategy=request.strategy,
        )
    except Exception as e:
        logger.error(f"Query optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get(
    "/optimize/query/{query}",
    response_model=QueryOptimizationResponse,
    summary="Optimize query (GET)",
    description="Simple GET endpoint for query optimization",
)
async def optimize_query_get(
    query: str, strategy: str = Query(default="expand", description="Optimization strategy")
) -> QueryOptimizationResponse:
    """Optimize query via GET request"""
    return await optimize_query(QueryOptimizationRequest(query=query, strategy=strategy))


# ============================================================================
# Context Compression Endpoints
# ============================================================================


@router.post(
    "/compress/context",
    response_model=ContextCompressionResponse,
    summary="Compress context documents",
    description="Compress retrieved documents to fit LLM context window",
)
async def compress_context(request: ContextCompressionRequest) -> ContextCompressionResponse:
    """
    Compress context documents

    Uses relevance-based sentence selection to reduce document size
    while preserving key information.
    """
    try:
        optimizer = RAGOptimizer()
        compressed_docs = optimizer.compress_context(
            request.query, request.documents, target_ratio=request.target_ratio
        )

        # Calculate actual compression ratio
        original_size = sum(len(doc.get("text", "")) for doc in request.documents)
        compressed_size = sum(len(doc.get("text", "")) for doc in compressed_docs)
        actual_ratio = compressed_size / original_size if original_size > 0 else 0

        return ContextCompressionResponse(
            compressed_documents=compressed_docs,
            compression_ratio=actual_ratio,
            original_count=len(request.documents),
            compressed_count=len(compressed_docs),
        )
    except Exception as e:
        logger.error(f"Context compression failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")


# ============================================================================
# Citation Endpoints
# ============================================================================


@router.post(
    "/citations/add",
    response_model=CitationResponse,
    summary="Add citations to answer",
    description="Add source citations to generated answer",
)
async def add_citations(request: CitationRequest) -> CitationResponse:
    """
    Add citations to answer

    Matches answer statements to source documents and adds
    inline citations with bibliography.
    """
    try:
        optimizer = RAGOptimizer()
        cited_answer, bibliography = optimizer.add_citations(request.answer, request.sources)

        return CitationResponse(
            cited_answer=cited_answer,
            bibliography=bibliography,
            num_citations=len(bibliography),
        )
    except Exception as e:
        logger.error(f"Citation addition failed: {e}")
        raise HTTPException(status_code=500, detail=f"Citation failed: {str(e)}")


# ============================================================================
# Verification Endpoints
# ============================================================================


@router.post(
    "/verify/answer",
    response_model=VerificationResponse,
    summary="Verify answer accuracy",
    description="Verify answer against source documents",
)
async def verify_answer(request: VerificationRequest) -> VerificationResponse:
    """
    Verify answer accuracy

    Checks if answer statements are supported by source documents.
    Detects hallucinations and provides confidence score.
    """
    try:
        optimizer = RAGOptimizer()
        verification = optimizer.verify_answer(request.answer, request.sources)

        return VerificationResponse(
            confidence=verification["confidence"],
            verified_facts=verification["verified_facts"],
            total_facts=verification["total_facts"],
            hallucinations=verification["hallucinations"],
            is_reliable=verification["is_reliable"],
        )
    except Exception as e:
        logger.error(f"Answer verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


# ============================================================================
# Conversational Memory Endpoints
# ============================================================================


@router.post(
    "/conversation/create",
    response_model=ConversationCreateResponse,
    summary="Create new conversation",
    description="Create a new conversation session",
)
async def create_conversation(request: ConversationCreateRequest) -> ConversationCreateResponse:
    """
    Create new conversation session

    Initializes a new conversation with unique session ID.
    Conversations are cached in Redis with 24-hour TTL.
    """
    try:
        manager = get_conversation_manager()
        conversation = manager.create_conversation(
            user_id=request.user_id, metadata=request.metadata
        )

        return ConversationCreateResponse(
            session_id=conversation.session_id,
            user_id=conversation.user_id,
            created_at=conversation.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Conversation creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Creation failed: {str(e)}")


@router.post(
    "/conversation/turn",
    response_model=ConversationTurnResponse,
    summary="Add conversation turn",
    description="Add a turn to existing conversation",
)
async def add_conversation_turn(request: ConversationTurnRequest) -> ConversationTurnResponse:
    """
    Add turn to conversation

    Records user message and assistant response.
    Maintains conversation history for context-aware search.
    """
    try:
        manager = get_conversation_manager()
        turn = manager.add_turn(
            session_id=request.session_id,
            user_message=request.user_message,
            assistant_response=request.assistant_response,
            query=request.query,
            sources=request.sources,
        )

        if not turn:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ConversationTurnResponse(
            turn_id=turn.turn_id,
            session_id=request.session_id,
            timestamp=turn.timestamp.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Turn addition failed: {e}")
        raise HTTPException(status_code=500, detail=f"Turn addition failed: {str(e)}")


@router.get(
    "/conversation/{session_id}/context",
    response_model=ConversationContextResponse,
    summary="Get conversation context",
    description="Get recent conversation turns for context",
)
async def get_conversation_context(
    session_id: str,
    num_turns: int = Query(default=5, ge=1, le=20, description="Number of turns"),
    max_tokens: int = Query(default=2000, ge=100, le=10000, description="Max tokens"),
) -> ConversationContextResponse:
    """
    Get conversation context

    Retrieves recent conversation turns that fit within token budget.
    Used for context-aware search and response generation.
    """
    try:
        manager = get_conversation_manager()
        context_turns = manager.get_context(
            session_id=session_id, num_turns=num_turns, max_tokens=max_tokens
        )

        return ConversationContextResponse(
            session_id=session_id,
            context_turns=[turn.to_dict() for turn in context_turns],
            num_turns=len(context_turns),
        )
    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")


@router.delete(
    "/conversation/{session_id}",
    summary="Delete conversation",
    description="Delete conversation from cache",
)
async def delete_conversation(session_id: str) -> Dict[str, str]:
    """Delete conversation"""
    try:
        manager = get_conversation_manager()
        manager.delete_conversation(session_id)
        return {"status": "deleted", "session_id": session_id}
    except Exception as e:
        logger.error(f"Conversation deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get(
    "/conversation/{session_id}/reformulate",
    summary="Reformulate query with context",
    description="Reformulate query using conversation history",
)
async def reformulate_query(
    session_id: str,
    query: str = Query(..., description="Query to reformulate"),
    num_context_turns: int = Query(default=3, ge=1, le=10, description="Context turns"),
) -> Dict[str, str]:
    """
    Reformulate query with conversation context

    Uses conversation history to resolve coreferences and
    add missing context to the query.
    """
    try:
        manager = get_conversation_manager()
        searcher = HistoryAwareSearcher(manager)
        reformulated = searcher.reformulate_query(
            session_id=session_id, query=query, num_context_turns=num_context_turns
        )

        return {
            "original_query": query,
            "reformulated_query": reformulated,
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Query reformulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reformulation failed: {str(e)}")


# ============================================================================
# Health Check
# ============================================================================


@router.get(
    "/health",
    summary="Check advanced RAG health",
    description="Check if advanced RAG features are available",
)
async def check_health() -> Dict[str, Any]:
    """Check advanced RAG health"""
    return {
        "status": "healthy",
        "features": {
            "query_optimization": "available",
            "context_compression": "available",
            "citation_tracking": "available",
            "answer_verification": "available",
            "conversational_memory": "available",
        },
    }


# ============================================================================
# Export Router
# ============================================================================

__all__ = ["router"]
