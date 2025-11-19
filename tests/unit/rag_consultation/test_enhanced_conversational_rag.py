"""
Tests for Enhanced Conversational RAG Service (Phase 1)

Tests Phase 1 improvements:
1. Query Decomposition
2. HyDE (Hypothetical Document Embeddings)
3. Hierarchical Chunking
4. Enhanced retrieval strategy

Target: 85-90% accuracy (from 70-80%)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from apps.api.services.enhanced_conversational_rag import (
    EnhancedConversationalRAG,
    EnhancedRAGResponse,
)
from apps.api.rag_consultation.models import QueryType, Intent
from apps.api.services.advanced_query_optimizer import QueryComplexity


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = Mock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=True)
    return client


@pytest.fixture
async def rag_service(mock_redis_client):
    """Create RAG service with mocked dependencies"""
    service = EnhancedConversationalRAG(
        redis_client=mock_redis_client,
        enable_hierarchical=False,  # Disable for unit tests
    )
    return service


class TestEnhancedConversationalRAG:
    """Test Enhanced Conversational RAG Service"""

    @pytest.mark.asyncio
    async def test_simple_query(self, rag_service):
        """Test simple query without decomposition or HyDE"""
        # Mock classifier
        with patch.object(
            rag_service.classifier,
            'classify',
            AsyncMock(return_value=Mock(
                query_type=QueryType.FACTUAL,
                intent_detection=Mock(primary_intent=Intent.SEARCH)
            ))
        ):
            # Mock query expander
            with patch.object(
                rag_service.query_expander,
                'expand',
                AsyncMock(return_value=Mock(
                    complexity=QueryComplexity.SIMPLE,
                    use_hyde=False,
                    use_decomposition=False,
                    sub_queries=[],
                    expanded_queries=["test query"],
                    hypothetical_document=None,
                    top_k=3,
                ))
            ):
                response = await rag_service.query(
                    query="test query",
                    session_id="test-session",
                )

                assert isinstance(response, EnhancedRAGResponse)
                assert response.query_complexity == "SIMPLE"
                assert response.used_hyde is False
                assert response.used_decomposition is False

    @pytest.mark.asyncio
    async def test_complex_query_with_decomposition(self, rag_service):
        """Test complex query with decomposition"""
        # Mock classifier
        with patch.object(
            rag_service.classifier,
            'classify',
            AsyncMock(return_value=Mock(
                query_type=QueryType.CONVERSATIONAL,
                intent_detection=Mock(primary_intent=Intent.RECALL)
            ))
        ):
            # Mock query expander with decomposition
            from apps.api.rag_consultation.retrieval.enhanced_query_expander import SubQuery

            with patch.object(
                rag_service.query_expander,
                'expand',
                AsyncMock(return_value=Mock(
                    complexity=QueryComplexity.COMPLEX,
                    use_hyde=False,
                    use_decomposition=True,
                    sub_queries=[
                        SubQuery(query="최근 피자집", type="temporal", priority=1),
                        SubQuery(query="피자집 이름", type="entity", priority=2),
                        SubQuery(query="피자집 가격", type="attribute", priority=3),
                    ],
                    expanded_queries=["최근에 갔던 피자집 이름이 뭐였고, 얼마였지?"],
                    hypothetical_document=None,
                    top_k=10,
                ))
            ):
                response = await rag_service.query(
                    query="최근에 갔던 피자집 이름이 뭐였고, 얼마였지?",
                    session_id="test-session",
                )

                assert response.query_complexity == "COMPLEX"
                assert response.used_decomposition is True
                assert len(response.sub_queries) == 3
                assert "최근 피자집" in response.sub_queries

    @pytest.mark.asyncio
    async def test_ambiguous_query_with_hyde(self, rag_service):
        """Test ambiguous query with HyDE"""
        # Mock classifier
        with patch.object(
            rag_service.classifier,
            'classify',
            AsyncMock(return_value=Mock(
                query_type=QueryType.PRODUCT_SEARCH,
                intent_detection=Mock(primary_intent=Intent.SEARCH)
            ))
        ):
            # Mock query expander with HyDE
            hypothetical_doc = """
제품명: 화장품용 소형 용기
용량: 30-50ml
재질: PET, PP
용도: 화장품, 스킨케어
특징: 투명, 휴대용
가격대: 500-1,500원
            """

            with patch.object(
                rag_service.query_expander,
                'expand',
                AsyncMock(return_value=Mock(
                    complexity=QueryComplexity.MEDIUM,
                    use_hyde=True,
                    use_decomposition=False,
                    sub_queries=[],
                    expanded_queries=["화장품에 쓸 작은 용기", hypothetical_doc],
                    hypothetical_document=hypothetical_doc,
                    top_k=5,
                ))
            ):
                response = await rag_service.query(
                    query="화장품에 쓸 작은 용기",
                    session_id="test-session",
                )

                assert response.query_complexity == "MEDIUM"
                assert response.used_hyde is True
                assert response.hypothetical_document is not None
                assert "화장품" in response.hypothetical_document

    @pytest.mark.asyncio
    async def test_conversation_context_preservation(self, rag_service):
        """Test that conversation context is preserved across turns"""
        session_id = f"test-session-{datetime.now().timestamp()}"

        # First turn: Store information
        with patch.object(rag_service.classifier, 'classify'), \
             patch.object(rag_service.query_expander, 'expand'):

            response1 = await rag_service.query(
                query="어제 파파존스 갔었어",
                session_id=session_id,
            )

            # Verify conversation was created
            conversation = rag_service.conversation_manager.get_conversation(session_id)
            assert conversation is not None
            assert len(conversation.turns) >= 1

    @pytest.mark.asyncio
    async def test_entity_extraction(self, rag_service):
        """Test entity extraction from queries and answers"""
        # Test price extraction
        entities = rag_service._extract_entities(
            query="25,000원 냈어",
            answer="25,000원입니다"
        )
        assert "price" in entities
        assert "25,000" in entities["price"]

        # Test date extraction
        entities = rag_service._extract_entities(
            query="2024-11-15에 갔었어",
            answer="2024-11-15 방문 기록"
        )
        assert "date" in entities
        assert entities["date"] == "2024-11-15"

    def test_should_search_knowledge(self, rag_service):
        """Test knowledge search decision logic"""
        # Should search when no conversation results
        assert rag_service._should_search_knowledge(
            QueryType.CONVERSATIONAL,
            Intent.RECALL,
            conversation_results=[]
        ) is True

        # Should search for factual queries
        assert rag_service._should_search_knowledge(
            QueryType.FACTUAL,
            Intent.SEARCH,
            conversation_results=[{"some": "result"}]
        ) is True

        # Should search for product search
        assert rag_service._should_search_knowledge(
            QueryType.PRODUCT_SEARCH,
            Intent.SEARCH,
            conversation_results=[{"some": "result"}]
        ) is True


class TestQueryExpansionStrategies:
    """Test query expansion strategies"""

    @pytest.mark.asyncio
    async def test_decomposition_threshold(self, rag_service):
        """Test that decomposition is applied based on complexity"""
        expander = rag_service.query_expander

        # SIMPLE query should not decompose
        assert expander._should_decompose(
            QueryComplexity.SIMPLE,
            QueryType.CONVERSATIONAL
        ) is False

        # MEDIUM query should decompose
        assert expander._should_decompose(
            QueryComplexity.MEDIUM,
            QueryType.CONVERSATIONAL
        ) is True

        # COMPLEX query should decompose
        assert expander._should_decompose(
            QueryComplexity.COMPLEX,
            QueryType.CONVERSATIONAL
        ) is True

    @pytest.mark.asyncio
    async def test_hyde_threshold(self, rag_service):
        """Test that HyDE is applied based on complexity and type"""
        expander = rag_service.query_expander

        # SIMPLE query should not use HyDE
        assert expander._should_use_hyde(
            QueryComplexity.SIMPLE,
            QueryType.PRODUCT_SEARCH
        ) is False

        # MEDIUM product search should use HyDE
        assert expander._should_use_hyde(
            QueryComplexity.MEDIUM,
            QueryType.PRODUCT_SEARCH
        ) is True

        # Wrong query type should not use HyDE
        assert expander._should_use_hyde(
            QueryComplexity.MEDIUM,
            QueryType.FACTUAL
        ) is False


class TestHierarchicalChunking:
    """Test hierarchical chunking for conversations"""

    def test_parent_chunk_building(self, rag_service):
        """Test parent chunk construction"""
        from apps.api.services.conversational_memory import Conversation, ConversationTurn

        # Create test conversation
        conversation = Conversation(
            session_id="test-123",
            user_id="user-123",
        )

        turn1 = ConversationTurn(
            turn_id="turn-1",
            user_message="어제 파파존스 갔었어",
            assistant_response="네",
        )
        conversation.add_turn(turn1)

        # Build parent chunk
        manager = rag_service.conversation_manager
        parent_text = manager._build_parent_chunk(conversation)

        assert "test-123" in parent_text
        assert "파파존스" in parent_text
        assert "Turn 1" in parent_text

    def test_child_chunk_building(self, rag_service):
        """Test child chunk construction"""
        from apps.api.rag_consultation.context.enhanced_conversation_manager import (
            EnhancedConversationTurn
        )

        # Create test turn
        turn = EnhancedConversationTurn(
            turn_id="turn-1",
            user_message="어제 파파존스 갔었어",
            assistant_response="네",
            entities={"place": "파파존스", "date": "2024-11-15"}
        )

        # Build child chunk
        manager = rag_service.conversation_manager
        child_text = manager._build_child_chunk(turn)

        assert "파파존스" in child_text
        assert "Entities" in child_text
        assert "place=파파존스" in child_text


@pytest.mark.asyncio
async def test_full_pipeline_integration(mock_redis_client):
    """Integration test for full pipeline"""
    service = EnhancedConversationalRAG(
        redis_client=mock_redis_client,
        enable_hierarchical=False,
    )

    session_id = f"integration-test-{datetime.now().timestamp()}"

    try:
        # Mock all external dependencies
        with patch.object(service.classifier, 'classify'), \
             patch.object(service.query_expander, 'expand'), \
             patch.object(service.conversation_manager, 'search_conversations', AsyncMock(return_value=[])), \
             patch.object(service.knowledge_rag, 'answer_question', AsyncMock(return_value={"sources": []})):

            # Execute query
            response = await service.query(
                query="test integration",
                session_id=session_id,
            )

            # Verify response structure
            assert isinstance(response, EnhancedRAGResponse)
            assert response.answer is not None
            assert response.confidence >= 0.0
            assert response.response_time_ms is not None

    finally:
        await service.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
