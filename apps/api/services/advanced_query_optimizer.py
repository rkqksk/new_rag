"""
Advanced Query Optimizer - Phase 1 Week 2 Implementation

LLM-based HyDE and Query Decomposition using Qwen 2.5

**Improvements over basic optimizer**:
1. LLM-generated hypothetical documents (vs template-based)
2. Intelligent query decomposition (vs simple multi-query)
3. Adaptive search strategy selection

**Expected Results** (from RAG_ADVANCEMENT_PLAN.md):
- Vague query handling: +25%
- Complex query accuracy: +30%
- User satisfaction: +20%

**Cost**: $0/month (Qwen 2.5 local LLM)

**Usage**:
```python
from apps.api.services.advanced_query_optimizer import AdvancedQueryOptimizer

optimizer = AdvancedQueryOptimizer()

# LLM-based HyDE
hypothetical_doc = await optimizer.generate_hypothetical_document("화장품에 쓸 작은 용기")

# Query decomposition
sub_queries = await optimizer.decompose_query("100ml PET 투명 보틀 중 화장품용으로 적합하고 가격이 저렴한 것")

# Adaptive search
results = await optimizer.adaptive_search(query, top_k=10)
```

**Version**: v10.5.0
**Created**: 2025-11-17
**Status**: Phase 1 Week 2 Implementation
"""

import json
from typing import List, Dict, Optional
from enum import Enum
from loguru import logger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available, using fallback HTTP client")


class QueryComplexity(str, Enum):
    """Query complexity levels"""
    SIMPLE = "simple"          # "50ml PET 보틀"
    MEDIUM = "medium"          # "화장품용 투명 용기"
    COMPLEX = "complex"        # "100ml PET 보틀 중 가격 저렴한 것"
    VAGUE = "vague"           # "작은 용기"
    CONVERSATIONAL = "conversational"  # Follow-up questions


class SearchStrategy(str, Enum):
    """Search strategy types"""
    SEMANTIC_SEARCH = "semantic_search"
    HYDE_SEARCH = "hyde_search"
    DECOMPOSITION_SEARCH = "decomposition_search"
    CORRECTIVE_RAG = "corrective_rag"
    CONVERSATIONAL_RAG = "conversational_rag"
    HYBRID_SEARCH = "hybrid_search"


class QwenClient:
    """
    Qwen 2.5 LLM client for local inference

    **Endpoint**: http://localhost:11434/api/generate (Ollama)
    **Model**: qwen2.5:latest
    **Cost**: $0/month (local)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:latest",
        timeout: int = 60
    ):
        """
        Initialize Qwen client

        Args:
            base_url: Ollama API base URL
            model: Model name
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

        if HTTPX_AVAILABLE:
            self.client = httpx.AsyncClient(timeout=timeout)
        else:
            self.client = None
            logger.warning("HTTP client not available")

        logger.info(f"QwenClient initialized: {base_url}, model={model}")

    async def generate(
        self,
        prompt: str,
        format: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using Qwen 2.5

        Args:
            prompt: Input prompt
            format: Output format ("json" or None)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if not self.client:
            logger.error("HTTP client not available")
            return ""

        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }

            if format == "json":
                payload["format"] = "json"

            logger.debug(f"Qwen request: {prompt[:100]}...")

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            generated_text = result.get("response", "")

            logger.debug(f"Qwen response: {generated_text[:100]}...")

            # Parse JSON if requested
            if format == "json" and generated_text:
                try:
                    return json.loads(generated_text)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON response, returning raw text")
                    return generated_text

            return generated_text

        except Exception as e:
            logger.error(f"Qwen generation failed: {e}")
            return ""

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()


class AdvancedQueryOptimizer:
    """
    Advanced query optimizer with LLM-based techniques

    **Features**:
    1. LLM-based HyDE (Hypothetical Document Embeddings)
    2. Intelligent query decomposition
    3. Query complexity analysis
    4. Adaptive search strategy selection

    **LLM**: Qwen 2.5 (local, $0 cost)
    """

    def __init__(
        self,
        qwen_client: Optional[QwenClient] = None,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:latest"
    ):
        """
        Initialize advanced query optimizer

        Args:
            qwen_client: Optional Qwen client instance
            ollama_base_url: Ollama API base URL
            model: Qwen model name
        """
        if qwen_client:
            self.llm = qwen_client
        else:
            self.llm = QwenClient(base_url=ollama_base_url, model=model)

        logger.info("AdvancedQueryOptimizer initialized with Qwen 2.5")

    async def analyze_complexity(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> QueryComplexity:
        """
        Analyze query complexity using LLM

        Args:
            query: Input query
            conversation_history: Optional conversation context

        Returns:
            QueryComplexity enum
        """
        # Simple heuristic-based classification (fast)
        # Can be upgraded to LLM-based for more accuracy

        if conversation_history:
            return QueryComplexity.CONVERSATIONAL

        # Count filter conditions
        num_conditions = 0
        keywords = ["중", "이면서", "그리고", "하지만", "적합한", "저렴한", "가격", "용도"]
        for keyword in keywords:
            if keyword in query:
                num_conditions += 1

        # Vague query (lacks specificity)
        vague_keywords = ["작은", "큰", "좋은", "예쁜", "적당한"]
        is_vague = any(keyword in query for keyword in vague_keywords)

        # Determine complexity
        if num_conditions >= 3:
            return QueryComplexity.COMPLEX
        elif is_vague:
            return QueryComplexity.VAGUE
        elif num_conditions >= 1:
            return QueryComplexity.MEDIUM
        else:
            return QueryComplexity.SIMPLE

    async def generate_hypothetical_document(self, query: str) -> str:
        """
        Generate hypothetical document using Qwen 2.5 (HyDE technique)

        **Innovation**: LLM-generated vs template-based
        **Expected Impact**: +25% vague query handling

        Args:
            query: Vague or incomplete query

        Returns:
            Hypothetical document text
        """
        prompt = f"""다음 검색 쿼리에 맞는 이상적인 제품 설명을 생성하세요:

쿼리: {query}

생성할 내용:
- 제품명 (구체적으로)
- 상세 스펙 (용량, 재질, 색상, 크기)
- 일반적인 용도
- 가격대

자연스러운 제품 설명 형식으로 작성하세요. JSON이나 특수 형식은 사용하지 마세요.

제품 설명:"""

        logger.info(f"Generating hypothetical document for: {query}")

        hypothetical_doc = await self.llm.generate(
            prompt,
            max_tokens=300,
            temperature=0.7
        )

        logger.debug(f"Hypothetical doc: {hypothetical_doc[:100]}...")

        return hypothetical_doc

    async def decompose_query(self, query: str) -> List[str]:
        """
        Decompose complex query into sub-queries using Qwen 2.5

        **Innovation**: LLM-based intelligent decomposition
        **Expected Impact**: +30% complex query accuracy

        Args:
            query: Complex multi-condition query

        Returns:
            List of sub-queries
        """
        prompt = f"""다음 복잡한 쿼리를 단순한 서브 쿼리들로 분해하세요:

쿼리: {query}

각 서브 쿼리는:
1. 독립적으로 검색 가능해야 함
2. 원본 쿼리의 한 측면만 다뤄야 함
3. 2-5개 사이로 생성

JSON 배열 형식으로 반환:
["서브쿼리1", "서브쿼리2", ...]

JSON:"""

        logger.info(f"Decomposing query: {query}")

        result = await self.llm.generate(
            prompt,
            format="json",
            max_tokens=200,
            temperature=0.5
        )

        # Parse sub-queries
        try:
            if isinstance(result, list):
                sub_queries = result
            elif isinstance(result, str):
                sub_queries = json.loads(result)
            else:
                logger.warning(f"Unexpected result type: {type(result)}")
                sub_queries = [query]
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse sub-queries, using original query")
            sub_queries = [query]

        logger.info(f"Decomposed into {len(sub_queries)} sub-queries")

        return sub_queries

    async def count_conditions(self, query: str) -> int:
        """
        Count filter conditions in query

        Args:
            query: Input query

        Returns:
            Number of conditions
        """
        keywords = ["중", "이면서", "그리고", "하지만", "적합한", "저렴한", "가격", "용도"]
        count = sum(1 for keyword in keywords if keyword in query)
        return count

    def select_strategy(
        self,
        complexity: QueryComplexity,
        num_conditions: int,
        has_context: bool
    ) -> SearchStrategy:
        """
        Select optimal search strategy based on query analysis

        **Strategy Matrix**:
        - Simple + Low ambiguity → Semantic search (fast)
        - Vague → HyDE search (hypothetical doc)
        - Complex multi-condition → Decomposition search
        - Conversational → Conversational RAG
        - Default → Hybrid search

        Args:
            complexity: Query complexity level
            num_conditions: Number of filter conditions
            has_context: Has conversation history

        Returns:
            SearchStrategy enum
        """
        if complexity == QueryComplexity.SIMPLE:
            # Fast path: Direct semantic search
            return SearchStrategy.SEMANTIC_SEARCH

        elif has_context:
            # Conversational path
            return SearchStrategy.CONVERSATIONAL_RAG

        elif complexity == QueryComplexity.VAGUE:
            # Vague query: Use HyDE
            return SearchStrategy.HYDE_SEARCH

        elif num_conditions >= 3:
            # Complex multi-condition: Use decomposition
            return SearchStrategy.DECOMPOSITION_SEARCH

        elif complexity == QueryComplexity.COMPLEX:
            # Complex query: Use corrective RAG
            return SearchStrategy.CORRECTIVE_RAG

        else:
            # Default: Hybrid search with re-ranking
            return SearchStrategy.HYBRID_SEARCH

    async def adaptive_search(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        top_k: int = 10
    ) -> Dict:
        """
        Adaptive search with automatic strategy selection

        **Workflow**:
        1. Analyze query complexity
        2. Select optimal strategy
        3. Execute strategy
        4. Return results with strategy metadata

        Args:
            query: Input query
            conversation_history: Optional conversation context
            top_k: Number of results

        Returns:
            Dictionary with results and metadata
        """
        logger.info(f"Adaptive search: {query}")

        # Step 1: Analyze query
        complexity = await self.analyze_complexity(query, conversation_history)
        num_conditions = await self.count_conditions(query)
        has_context = bool(conversation_history)

        # Step 2: Select strategy
        strategy = self.select_strategy(complexity, num_conditions, has_context)

        logger.info(
            f"Query analysis: complexity={complexity.value}, "
            f"conditions={num_conditions}, strategy={strategy.value}"
        )

        # Step 3: Execute strategy
        if strategy == SearchStrategy.HYDE_SEARCH:
            # Generate hypothetical document
            hypothetical_doc = await self.generate_hypothetical_document(query)
            search_query = hypothetical_doc
            metadata = {
                "strategy": strategy.value,
                "complexity": complexity.value,
                "hypothetical_doc": hypothetical_doc
            }

        elif strategy == SearchStrategy.DECOMPOSITION_SEARCH:
            # Decompose query
            sub_queries = await self.decompose_query(query)
            search_query = sub_queries  # Will need multi-query search
            metadata = {
                "strategy": strategy.value,
                "complexity": complexity.value,
                "sub_queries": sub_queries
            }

        else:
            # Direct search with original query
            search_query = query
            metadata = {
                "strategy": strategy.value,
                "complexity": complexity.value
            }

        # Return query and metadata (actual search will be done by calling service)
        return {
            "original_query": query,
            "search_query": search_query,
            "metadata": metadata,
            "top_k": top_k
        }

    async def close(self):
        """Close LLM client"""
        await self.llm.close()


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        # Initialize optimizer
        optimizer = AdvancedQueryOptimizer()

        # Test queries
        test_queries = [
            "50ml PET 보틀",                                # Simple
            "화장품용 투명 용기",                            # Medium
            "작은 용기",                                     # Vague
            "100ml PET 투명 보틀 중 화장품용으로 적합하고 가격이 저렴한 것"  # Complex
        ]

        print("=== Advanced Query Optimizer Test ===\n")

        for query in test_queries:
            print(f"\nQuery: {query}")

            # Analyze complexity
            complexity = await optimizer.analyze_complexity(query)
            print(f"Complexity: {complexity.value}")

            # Adaptive search
            result = await optimizer.adaptive_search(query, top_k=5)
            print(f"Strategy: {result['metadata']['strategy']}")

            # Test HyDE for vague queries
            if complexity == QueryComplexity.VAGUE:
                hypothetical = await optimizer.generate_hypothetical_document(query)
                print(f"Hypothetical doc: {hypothetical[:150]}...")

            # Test decomposition for complex queries
            if complexity == QueryComplexity.COMPLEX:
                sub_queries = await optimizer.decompose_query(query)
                print(f"Sub-queries ({len(sub_queries)}):")
                for i, sq in enumerate(sub_queries, 1):
                    print(f"  {i}. {sq}")

        # Cleanup
        await optimizer.close()

    asyncio.run(main())
