"""
Consultation API Routes - RAG Consultation Endpoints

Provides FastAPI endpoints for intelligent query consultation
with multi-turn conversation support.

Endpoints:
- POST /consultation/query - Submit consultation query
- GET /consultation/context/{session_id} - Get session context
- POST /consultation/feedback - Submit feedback

Usage:
    Include this router in main FastAPI app:
    app.include_router(consultation_router, prefix="/api/v1")
"""

import logging
from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException, Depends, status
from redis.asyncio import Redis

from app.core.config import get_settings
from app.rag_consultation.models import (
    ConsultationRequest,
    ConsultationResponse,
)
from app.rag_consultation.classification import (
    QueryClassifier,
    IntentDetector,
    ToneAnalyzer,
    LanguageDetector,
)
from app.rag_consultation.context import (
    ConversationManager,
    ContextStore,
)
from app.rag_consultation.retrieval import QueryExpander
from app.rag_consultation.generation import (
    PromptBuilder,
    ResponseGenerator,
    TemplateSystem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consultation", tags=["consultation"])


# Dependency: Redis client
async def get_redis_client() -> Redis:
    """Get Redis client for dependency injection.

    Returns:
        Redis async client

    Raises:
        HTTPException: If Redis connection fails
    """
    settings = get_settings()
    try:
        redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=settings.redis_pool_max_connections,
        )
        # Test connection
        await redis_client.ping()
        return redis_client
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable",
        )


# Dependency: Classification components
async def get_query_classifier(
    redis_client: Redis = Depends(get_redis_client),
) -> QueryClassifier:
    """Get query classifier instance."""
    return QueryClassifier(redis_client=redis_client)


async def get_intent_detector(
    redis_client: Redis = Depends(get_redis_client),
) -> IntentDetector:
    """Get intent detector instance."""
    return IntentDetector(redis_client=redis_client)


async def get_tone_analyzer() -> ToneAnalyzer:
    """Get tone analyzer instance."""
    return ToneAnalyzer()


async def get_language_detector() -> LanguageDetector:
    """Get language detector instance."""
    return LanguageDetector()


# Dependency: Context management
async def get_conversation_manager(
    redis_client: Redis = Depends(get_redis_client),
) -> ConversationManager:
    """Get conversation manager instance."""
    context_store = ContextStore(redis_client=redis_client)
    return ConversationManager(context_store=context_store)


# Dependency: Generation components
async def get_response_generator() -> ResponseGenerator:
    """Get response generator instance."""
    settings = get_settings()
    return ResponseGenerator(
        ollama_url=settings.ollama_url,
        model_name=settings.ollama_default_model,
    )


@router.post("/query", response_model=ConsultationResponse)
async def consultation_query(
    request: ConsultationRequest,
    classifier: QueryClassifier = Depends(get_query_classifier),
    intent_detector: IntentDetector = Depends(get_intent_detector),
    tone_analyzer: ToneAnalyzer = Depends(get_tone_analyzer),
    language_detector: LanguageDetector = Depends(get_language_detector),
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    response_generator: ResponseGenerator = Depends(get_response_generator),
) -> ConsultationResponse:
    """Process consultation query with intelligent classification and response.

    Args:
        request: Consultation request with query and session info
        classifier: Query classifier dependency
        intent_detector: Intent detector dependency
        tone_analyzer: Tone analyzer dependency
        language_detector: Language detector dependency
        conversation_manager: Conversation manager dependency
        response_generator: Response generator dependency

    Returns:
        ConsultationResponse with generated answer and metadata

    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Processing consultation query: {request.query[:50]}...")

        # 1. Get or create session
        context = await conversation_manager.get_or_create_session(
            session_id=request.session_id,
            user_id=request.user_id,
        )

        # 2. Resolve references from conversation history
        resolved_query = conversation_manager.resolve_references(
            request.query,
            context,
        )

        # 3. Classify query
        query_analysis = await classifier.classify(resolved_query)

        # 4. Detect intent
        intent_detection = await intent_detector.detect(resolved_query)

        # 5. Analyze tone
        tone_analysis = await tone_analyzer.analyze(resolved_query)

        # 6. Detect language
        language = await language_detector.detect(resolved_query)
        logger.info(f"Detected language: {language}")

        # 7. Expand query and create retrieval strategy
        query_expander = QueryExpander()
        retrieval_strategy = await query_expander.expand(
            query=resolved_query,
            query_type=query_analysis.query_type,
            intent=intent_detection.primary_intent,
        )

        # 8. Build prompt (simplified - no actual retrieval in this phase)
        prompt_builder = PromptBuilder()
        conversation_summary = await conversation_manager.get_conversation_summary(
            context.session_id
        )

        prompt = prompt_builder.build_prompt(
            query=resolved_query,
            query_type=query_analysis.query_type,
            conversation_summary=conversation_summary if len(context.turns) > 0 else None,
            expertise_level=tone_analysis.expertise_level,
        )

        # 9. Generate response
        generated_response = await response_generator.generate(
            prompt=prompt,
            query_type=query_analysis.query_type,
            formality=tone_analysis.formality,
            urgency=tone_analysis.urgency,
        )

        # 10. Add turn to conversation
        await conversation_manager.add_turn(
            session_id=context.session_id,
            query=request.query,
            response=generated_response,
            query_analysis=query_analysis,
            intent=intent_detection,
            tone=tone_analysis,
        )

        # 11. Create response
        response = ConsultationResponse(
            response=generated_response,
            session_id=context.session_id,
            query_analysis=query_analysis,
            intent=intent_detection,
            tone=tone_analysis,
            retrieval_strategy=retrieval_strategy,
            confidence=query_analysis.confidence,
        )

        logger.info(f"Successfully processed query for session {context.session_id}")

        return response

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing query",
        )


@router.get("/context/{session_id}")
async def get_session_context(
    session_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
):
    """Get conversation context for session.

    Args:
        session_id: Session identifier
        conversation_manager: Conversation manager dependency

    Returns:
        Session context and metadata

    Raises:
        HTTPException: If session not found
    """
    try:
        session_info = await conversation_manager.get_session_info(session_id)
        return session_info

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    except Exception as e:
        logger.error(f"Failed to get session context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/context/{session_id}")
async def clear_session(
    session_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
):
    """Clear conversation session.

    Args:
        session_id: Session identifier
        conversation_manager: Conversation manager dependency

    Returns:
        Success message

    Raises:
        HTTPException: If clear fails
    """
    try:
        success = await conversation_manager.clear_session(session_id)

        if success:
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

    except Exception as e:
        logger.error(f"Failed to clear session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/health")
async def health_check(
    response_generator: ResponseGenerator = Depends(get_response_generator),
    redis_client: Redis = Depends(get_redis_client),
):
    """Health check for consultation service.

    Returns:
        Service health status
    """
    try:
        # Check Ollama
        ollama_healthy = await response_generator.health_check()

        # Check Redis
        redis_healthy = await redis_client.ping()

        return {
            "status": "healthy" if (ollama_healthy and redis_healthy) else "degraded",
            "ollama": "ok" if ollama_healthy else "unavailable",
            "redis": "ok" if redis_healthy else "unavailable",
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
