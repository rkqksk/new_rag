"""
Unit Tests: Advanced Query Optimizer

Tests for LLM-based HyDE and Query Decomposition (Phase 1, Week 2)

**Test Coverage**:
- Query complexity analysis
- HyDE document generation
- Query decomposition
- Strategy selection
- Adaptive search

**Expected Results** (from RAG_ADVANCEMENT_PLAN.md):
- Vague query handling: +25%
- Complex query accuracy: +30%
- User satisfaction: +20%

**Version**: v10.5.0
**Created**: 2025-11-17
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.services.advanced_query_optimizer import (
    AdvancedQueryOptimizer,
    QwenClient,
    QueryComplexity,
    SearchStrategy
)


@pytest.fixture
def mock_qwen_client():
    """Create mock Qwen client"""
    client = AsyncMock(spec=QwenClient)

    # Mock HyDE generation
    client.generate.return_value = """
제품명: 50ml PET 투명 화장품 보틀
용량: 50ml
재질: PET
색상: 투명
용도: 화장품, 토너, 에센스
가격대: 700-900원
"""

    return client


@pytest.fixture
def optimizer(mock_qwen_client):
    """Create optimizer with mock LLM"""
    return AdvancedQueryOptimizer(qwen_client=mock_qwen_client)


class TestQueryComplexityAnalysis:
    """Test query complexity analysis"""

    @pytest.mark.asyncio
    async def test_simple_query(self, optimizer):
        """Test simple query classification"""
        query = "50ml PET 보틀"
        complexity = await optimizer.analyze_complexity(query)

        assert complexity == QueryComplexity.SIMPLE

    @pytest.mark.asyncio
    async def test_medium_query(self, optimizer):
        """Test medium query classification"""
        query = "화장품용 투명 용기"
        complexity = await optimizer.analyze_complexity(query)

        assert complexity in [QueryComplexity.MEDIUM, QueryComplexity.SIMPLE]

    @pytest.mark.asyncio
    async def test_complex_query(self, optimizer):
        """Test complex query classification"""
        query = "100ml PET 투명 보틀 중 화장품용으로 적합하고 가격이 저렴한 것"
        complexity = await optimizer.analyze_complexity(query)

        assert complexity == QueryComplexity.COMPLEX

    @pytest.mark.asyncio
    async def test_vague_query(self, optimizer):
        """Test vague query classification"""
        query = "작은 용기"
        complexity = await optimizer.analyze_complexity(query)

        assert complexity == QueryComplexity.VAGUE

    @pytest.mark.asyncio
    async def test_conversational_query(self, optimizer):
        """Test conversational query classification"""
        query = "그것보다 큰 거"
        history = [{"role": "user", "content": "50ml 보틀 찾아줘"}]
        complexity = await optimizer.analyze_complexity(query, history)

        assert complexity == QueryComplexity.CONVERSATIONAL


class TestHyDE:
    """Test Hypothetical Document Embeddings"""

    @pytest.mark.asyncio
    async def test_generate_hypothetical_document(self, optimizer, mock_qwen_client):
        """Test HyDE document generation"""
        query = "작은 화장품 용기"

        hypothetical = await optimizer.generate_hypothetical_document(query)

        # Verify LLM was called
        assert mock_qwen_client.generate.called

        # Verify result
        assert hypothetical
        assert len(hypothetical) > 0

    @pytest.mark.asyncio
    async def test_hyde_with_vague_query(self, optimizer, mock_qwen_client):
        """Test HyDE with vague query"""
        query = "예쁜 용기"

        hypothetical = await optimizer.generate_hypothetical_document(query)

        # Should generate detailed description
        assert hypothetical
        assert len(hypothetical) > len(query)


class TestQueryDecomposition:
    """Test query decomposition"""

    @pytest.mark.asyncio
    async def test_decompose_complex_query(self, optimizer, mock_qwen_client):
        """Test decomposing complex query"""
        query = "100ml PET 투명 보틀 중 화장품용으로 적합하고 가격이 저렴한 것"

        # Mock decomposition result
        mock_qwen_client.generate.return_value = [
            "100ml PET 투명 보틀",
            "화장품용 용기",
            "가격이 저렴한 용기"
        ]

        sub_queries = await optimizer.decompose_query(query)

        # Verify result
        assert isinstance(sub_queries, list)
        assert len(sub_queries) >= 2
        assert len(sub_queries) <= 5

    @pytest.mark.asyncio
    async def test_decompose_simple_query(self, optimizer, mock_qwen_client):
        """Test decomposition with simple query"""
        query = "50ml PET 보틀"

        # Mock result (should return single query or few variations)
        mock_qwen_client.generate.return_value = [query]

        sub_queries = await optimizer.decompose_query(query)

        assert isinstance(sub_queries, list)
        assert len(sub_queries) >= 1


class TestStrategySelection:
    """Test search strategy selection"""

    def test_select_simple_strategy(self, optimizer):
        """Test strategy for simple query"""
        strategy = optimizer.select_strategy(
            complexity=QueryComplexity.SIMPLE,
            num_conditions=0,
            has_context=False
        )

        assert strategy == SearchStrategy.SEMANTIC_SEARCH

    def test_select_vague_strategy(self, optimizer):
        """Test strategy for vague query"""
        strategy = optimizer.select_strategy(
            complexity=QueryComplexity.VAGUE,
            num_conditions=0,
            has_context=False
        )

        assert strategy == SearchStrategy.HYDE_SEARCH

    def test_select_complex_strategy(self, optimizer):
        """Test strategy for complex query"""
        strategy = optimizer.select_strategy(
            complexity=QueryComplexity.COMPLEX,
            num_conditions=3,
            has_context=False
        )

        assert strategy == SearchStrategy.DECOMPOSITION_SEARCH

    def test_select_conversational_strategy(self, optimizer):
        """Test strategy for conversational query"""
        strategy = optimizer.select_strategy(
            complexity=QueryComplexity.CONVERSATIONAL,
            num_conditions=0,
            has_context=True
        )

        assert strategy == SearchStrategy.CONVERSATIONAL_RAG


class TestAdaptiveSearch:
    """Test adaptive search workflow"""

    @pytest.mark.asyncio
    async def test_adaptive_search_simple(self, optimizer, mock_qwen_client):
        """Test adaptive search with simple query"""
        query = "50ml PET 보틀"

        result = await optimizer.adaptive_search(query, top_k=5)

        # Verify result structure
        assert 'original_query' in result
        assert 'search_query' in result
        assert 'metadata' in result
        assert 'top_k' in result

        # Verify values
        assert result['original_query'] == query
        assert result['top_k'] == 5
        assert result['metadata']['strategy'] == SearchStrategy.SEMANTIC_SEARCH.value

    @pytest.mark.asyncio
    async def test_adaptive_search_vague(self, optimizer, mock_qwen_client):
        """Test adaptive search with vague query"""
        query = "작은 용기"

        result = await optimizer.adaptive_search(query, top_k=10)

        # Should use HyDE strategy
        assert result['metadata']['strategy'] == SearchStrategy.HYDE_SEARCH.value

        # Should have hypothetical document
        assert 'hypothetical_doc' in result['metadata']

    @pytest.mark.asyncio
    async def test_adaptive_search_complex(self, optimizer, mock_qwen_client):
        """Test adaptive search with complex query"""
        query = "100ml PET 투명 보틀 중 화장품용으로 적합하고 가격이 저렴한 것"

        # Mock decomposition
        mock_qwen_client.generate.return_value = [
            "100ml PET 투명 보틀",
            "화장품용 용기",
            "가격이 저렴한 용기"
        ]

        result = await optimizer.adaptive_search(query, top_k=10)

        # Should use decomposition strategy
        assert result['metadata']['strategy'] == SearchStrategy.DECOMPOSITION_SEARCH.value

        # Should have sub-queries
        assert 'sub_queries' in result['metadata']


@pytest.mark.integration
class TestQwenClient:
    """Integration tests for Qwen client (requires Ollama)"""

    @pytest.mark.skip(reason="Requires Ollama server running")
    @pytest.mark.asyncio
    async def test_qwen_generate(self):
        """Test actual Qwen generation"""
        client = QwenClient()

        prompt = "안녕하세요. 간단히 인사해주세요."
        result = await client.generate(prompt, max_tokens=50)

        assert result
        assert len(result) > 0

        await client.close()

    @pytest.mark.skip(reason="Requires Ollama server running")
    @pytest.mark.asyncio
    async def test_qwen_json_format(self):
        """Test Qwen JSON generation"""
        client = QwenClient()

        prompt = """다음을 JSON 배열로 반환하세요: ["항목1", "항목2", "항목3"]"""
        result = await client.generate(prompt, format="json")

        assert isinstance(result, (list, dict))

        await client.close()


@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks"""

    @pytest.mark.asyncio
    async def test_complexity_analysis_speed(self, optimizer, benchmark):
        """Benchmark complexity analysis speed"""
        query = "100ml PET 투명 보틀"

        import asyncio
        result = benchmark(lambda: asyncio.run(optimizer.analyze_complexity(query)))

        assert result in QueryComplexity

    @pytest.mark.asyncio
    async def test_end_to_end_latency(self, optimizer):
        """Test end-to-end adaptive search latency"""
        import time

        query = "화장품용 투명 용기"

        start = time.time()
        result = await optimizer.adaptive_search(query, top_k=10)
        elapsed = time.time() - start

        assert result
        print(f"\nEnd-to-end latency: {elapsed:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
