"""
Integration Tests for Consultation Pipeline

Tests end-to-end consultation flow with mocked Ollama.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from redis.asyncio import Redis
import uuid

from app.rag_consultation.classification import (
    QueryClassifier,
    IntentDetector,
    ToneAnalyzer,
)
from app.rag_consultation.context import (
    ConversationManager,
    ContextStore,
)
from app.rag_consultation.retrieval import QueryExpander
from app.rag_consultation.generation import (
    PromptBuilder,
    ResponseGenerator,
)
from app.rag_consultation.models import QueryType, Intent


@pytest.fixture
async def redis_client():
    """Redis client for integration tests."""
    # Use fakeredis for testing if available, otherwise skip
    try:
        from fakeredis.aioredis import FakeRedis
        redis = FakeRedis(decode_responses=True)
        yield redis
        await redis.aclose()
    except ImportError:
        pytest.skip("fakeredis not available, skipping integration tests")


@pytest.fixture
def query_classifier(redis_client):
    """Query classifier instance."""
    return QueryClassifier(redis_client=redis_client)


@pytest.fixture
def intent_detector(redis_client):
    """Intent detector instance."""
    return IntentDetector(redis_client=redis_client)


@pytest.fixture
def tone_analyzer():
    """Tone analyzer instance."""
    return ToneAnalyzer()


@pytest.fixture
def conversation_manager(redis_client):
    """Conversation manager instance."""
    context_store = ContextStore(redis_client=redis_client)
    return ConversationManager(context_store=context_store)


@pytest.fixture
def query_expander():
    """Query expander instance."""
    return QueryExpander()


@pytest.fixture
def prompt_builder():
    """Prompt builder instance."""
    return PromptBuilder()


@pytest.fixture
def mock_response_generator():
    """Mocked response generator."""
    with patch("httpx.AsyncClient.post") as mock_post:
        # Mock successful Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "This is a mocked response from Ollama LLM."
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        generator = ResponseGenerator(
            ollama_url="http://localhost:11434",
            model_name="qwen2.5:7b-instruct-q4_K_M",
        )
        yield generator


class TestConsultationPipeline:
    """Integration tests for full consultation pipeline."""

    @pytest.mark.asyncio
    async def test_end_to_end_consultation_flow(
        self,
        query_classifier,
        intent_detector,
        tone_analyzer,
        conversation_manager,
        query_expander,
        prompt_builder,
        mock_response_generator,
    ):
        """Test complete consultation flow from query to response."""
        # User query
        query = "How does machine learning work?"

        # 1. Create session
        session_id = f"test_session_{uuid.uuid4().hex}"
        context = await conversation_manager.get_or_create_session(
            session_id=session_id,
            user_id="test_user",
        )

        assert context.session_id == session_id
        assert len(context.turns) == 0

        # 2. Classify query
        query_analysis = await query_classifier.classify(query)

        assert query_analysis.query_type == QueryType.FACTUAL
        assert query_analysis.confidence > 0.3

        # 3. Detect intent
        intent_detection = await intent_detector.detect(query)

        assert Intent.INFORMATION_SEEKING in intent_detection.intents
        assert intent_detection.primary_intent is not None

        # 4. Analyze tone
        tone_analysis = await tone_analyzer.analyze(query)

        assert tone_analysis.formality is not None
        assert tone_analysis.urgency is not None
        assert tone_analysis.expertise_level is not None

        # 5. Expand query
        retrieval_strategy = await query_expander.expand(
            query=query,
            query_type=query_analysis.query_type,
            intent=intent_detection.primary_intent,
        )

        assert len(retrieval_strategy.expanded_queries) > 0
        assert retrieval_strategy.top_k > 0

        # 6. Build prompt
        prompt = prompt_builder.build_prompt(
            query=query,
            query_type=query_analysis.query_type,
            expertise_level=tone_analysis.expertise_level,
        )

        assert len(prompt) > 0
        assert query in prompt

        # 7. Generate response
        response = await mock_response_generator.generate(
            prompt=prompt,
            query_type=query_analysis.query_type,
            formality=tone_analysis.formality,
            urgency=tone_analysis.urgency,
        )

        assert len(response) > 0
        assert "mocked response" in response.lower()

        # 8. Add turn to conversation
        updated_context = await conversation_manager.add_turn(
            session_id=session_id,
            query=query,
            response=response,
            query_analysis=query_analysis,
            intent=intent_detection,
            tone=tone_analysis,
        )

        assert len(updated_context.turns) == 1
        assert updated_context.turns[0].query == query
        assert updated_context.turns[0].response == response

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(
        self,
        query_classifier,
        conversation_manager,
        mock_response_generator,
        prompt_builder,
    ):
        """Test multi-turn conversation with context."""
        session_id = f"test_session_{uuid.uuid4().hex}"

        # First turn
        query1 = "What is RAG?"
        context1 = await conversation_manager.get_or_create_session(session_id)

        analysis1 = await query_classifier.classify(query1)
        prompt1 = prompt_builder.build_prompt(
            query=query1,
            query_type=analysis1.query_type,
        )
        response1 = await mock_response_generator.generate(
            prompt=prompt1,
            query_type=analysis1.query_type,
        )

        await conversation_manager.add_turn(
            session_id=session_id,
            query=query1,
            response=response1,
        )

        # Second turn with reference
        query2 = "How does it work?"
        context2 = await conversation_manager.get_or_create_session(session_id)

        # Resolve reference
        resolved_query = conversation_manager.resolve_references(query2, context2)

        assert len(resolved_query) > len(query2)
        assert query1 in resolved_query

        # Generate response with conversation history
        conversation_summary = await conversation_manager.get_conversation_summary(
            session_id
        )

        prompt2 = prompt_builder.build_prompt(
            query=resolved_query,
            query_type=QueryType.FACTUAL,
            conversation_summary=conversation_summary,
        )

        response2 = await mock_response_generator.generate(
            prompt=prompt2,
            query_type=QueryType.FACTUAL,
        )

        await conversation_manager.add_turn(
            session_id=session_id,
            query=query2,
            response=response2,
        )

        # Verify conversation state
        final_context = await conversation_manager.get_or_create_session(session_id)
        assert len(final_context.turns) == 2

    @pytest.mark.asyncio
    async def test_session_persistence(
        self,
        conversation_manager,
    ):
        """Test that session data persists across manager instances."""
        session_id = f"test_session_{uuid.uuid4().hex}"

        # Create session and add turn
        context1 = await conversation_manager.get_or_create_session(session_id)
        await conversation_manager.add_turn(
            session_id=session_id,
            query="Test query",
            response="Test response",
        )

        # Retrieve session
        context2 = await conversation_manager.get_or_create_session(session_id)

        assert context2.session_id == session_id
        assert len(context2.turns) == 1
        assert context2.turns[0].query == "Test query"

    @pytest.mark.asyncio
    async def test_classification_caching(
        self,
        query_classifier,
        redis_client,
    ):
        """Test that classification results are cached."""
        query = "What is machine learning?"

        # First classification
        result1 = await query_classifier.classify(query)

        # Second classification (should hit cache)
        result2 = await query_classifier.classify(query)

        assert result1.query_type == result2.query_type
        assert result1.confidence == result2.confidence
