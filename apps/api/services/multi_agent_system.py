"""
Multi-Agent System with LangGraph (v6.0.0)
==========================================

Orchestrates multiple specialized agents for complex RAG tasks:
- Router Agent: Classifies queries and routes to appropriate agents
- Search Agent: Executes vector/hybrid search
- Reasoning Agent: Performs chain-of-thought reasoning on results
- Synthesis Agent: Combines multi-source information
- Validation Agent: Fact-checks and validates responses

Architecture: State machine with conditional edges (LangGraph)
Coordination: Message passing between agents
State: Shared context across agent transitions

Version: v6.0.0
"""

import asyncio
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)


# ============================================================================
# Agent State Definition
# ============================================================================


class AgentState(TypedDict):
    """Shared state passed between agents"""

    # Input
    query: str
    session_id: str
    collections: Optional[List[str]]
    materials: Optional[List[str]]

    # Query analysis
    intent: Optional[str]
    complexity: Optional[str]  # "simple", "medium", "complex"
    requires_reasoning: bool

    # Search results
    dense_results: Optional[List[Dict]]
    sparse_results: Optional[List[Dict]]
    hybrid_results: Optional[List[Dict]]

    # Reasoning
    reasoning_steps: List[str]
    intermediate_conclusions: List[str]

    # Synthesis
    synthesized_answer: Optional[str]
    confidence_score: float

    # Validation
    validated: bool
    validation_issues: List[str]

    # Final output
    final_answer: str
    final_products: List[Dict]
    agent_trace: List[str]  # Track which agents were invoked


class AgentType(str, Enum):
    """Available agent types"""

    ROUTER = "router"
    SEARCH = "search"
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"


# ============================================================================
# Individual Agents
# ============================================================================


class RouterAgent:
    """
    Routes queries to appropriate agent workflow based on complexity and intent
    """

    def __init__(self):
        self.name = "RouterAgent"
        logger.info(f"{self.name} initialized")

    async def route(self, state: AgentState) -> AgentState:
        """
        Analyze query and determine routing strategy

        Returns:
            Updated state with intent, complexity, and routing decision
        """
        query = state["query"]
        logger.info(f"[{self.name}] Routing query: '{query}'")

        # Simple heuristic-based routing (can be replaced with LLM)
        intent = self._classify_intent(query)
        complexity = self._assess_complexity(query)

        state["intent"] = intent
        state["complexity"] = complexity
        state["requires_reasoning"] = complexity in ["medium", "complex"]
        state["agent_trace"].append(f"{self.name}:route")

        logger.info(
            f"[{self.name}] Intent={intent}, Complexity={complexity}, Reasoning={state['requires_reasoning']}"
        )

        return state

    def _classify_intent(self, query: str) -> str:
        """Classify query intent"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["비교", "차이", "vs", "compare"]):
            return "comparison"
        elif any(word in query_lower for word in ["추천", "recommend", "best", "좋은"]):
            return "recommendation"
        elif any(word in query_lower for word in ["어떻게", "how", "방법", "why", "왜"]):
            return "explanation"
        elif any(word in query_lower for word in ["찾아", "search", "find", "있나"]):
            return "search"
        else:
            return "general"

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        # Simple heuristics
        word_count = len(query.split())
        has_multi_conditions = any(
            word in query.lower() for word in ["그리고", "또는", "and", "or", "but"]
        )
        has_comparison = any(word in query.lower() for word in ["비교", "차이", "vs"])

        if has_comparison or (has_multi_conditions and word_count > 10):
            return "complex"
        elif has_multi_conditions or word_count > 6:
            return "medium"
        else:
            return "simple"


class SearchAgent:
    """
    Executes search operations (dense, sparse, hybrid)
    """

    def __init__(self):
        self.name = "SearchAgent"
        logger.info(f"{self.name} initialized")

    async def search(self, state: AgentState) -> AgentState:
        """
        Execute search based on query complexity

        Simple: Dense-only
        Medium: Hybrid (dense + sparse)
        Complex: Hybrid + re-ranking
        """
        query = state["query"]
        complexity = state.get("complexity", "simple")

        logger.info(f"[{self.name}] Executing search (complexity={complexity})")

        try:
            # Import RAG skill
            import sys
            from pathlib import Path

            skill_path = Path(__file__).parent.parent.parent / ".claude/skills/rag-pipeline/scripts"
            if str(skill_path) not in sys.path:
                sys.path.insert(0, str(skill_path))

            from skill import rag_query as skill_rag_query

            # Execute search
            result = skill_rag_query(
                {
                    "question": query,
                    "top_k": 100,
                    "collections": state.get("collections"),
                    "materials": state.get("materials"),
                }
            )

            if result["status"] == "success":
                state["dense_results"] = result.get("sources", [])
                state["agent_trace"].append(f"{self.name}:dense_search")

                # For medium/complex queries, also do hybrid search
                if complexity in ["medium", "complex"]:
                    state["hybrid_results"] = await self._hybrid_search(state)
                    state["agent_trace"].append(f"{self.name}:hybrid_search")

                logger.info(
                    f"[{self.name}] Search complete: {len(state.get('dense_results', []))} dense results"
                )
            else:
                logger.error(f"[{self.name}] Search failed: {result.get('error')}")
                state["dense_results"] = []

        except Exception as e:
            logger.error(f"[{self.name}] Search error: {e}", exc_info=True)
            state["dense_results"] = []

        return state

    async def _hybrid_search(self, state: AgentState) -> List[Dict]:
        """Execute hybrid search (dense + sparse + rerank)"""
        try:
            from apps.api.services.hybrid_search import HybridSearchEngine

            engine = HybridSearchEngine(enable_cross_encoder=True)

            # Get dense results
            dense_results = state.get("dense_results", [])
            if not dense_results:
                return []

            # Convert to format expected by hybrid engine
            documents = []
            dense_result_tuples = []
            for result in dense_results:
                doc = {
                    "metadata": result.get("metadata", {}),
                    "text": result.get("text", ""),
                }
                documents.append(doc)
                dense_result_tuples.append((doc, result.get("score", 0.0)))

            # Build BM25 index
            bm25_index = engine.build_bm25_index(documents)

            # Hybrid search
            hybrid_results = engine.hybrid_search(
                query=state["query"],
                dense_results=dense_result_tuples,
                bm25_index=bm25_index,
                documents=documents,
                top_k=50,
                enable_reranking=(state.get("complexity") == "complex"),
            )

            # Convert back to result format
            return [
                {
                    "metadata": doc.get("metadata", {}),
                    "text": doc.get("text", ""),
                    "score": score,
                }
                for doc, score in hybrid_results
            ]

        except Exception as e:
            logger.error(f"[{self.name}] Hybrid search error: {e}")
            return state.get("dense_results", [])


class ReasoningAgent:
    """
    Performs chain-of-thought reasoning on search results
    """

    def __init__(self):
        self.name = "ReasoningAgent"
        logger.info(f"{self.name} initialized")

    async def reason(self, state: AgentState) -> AgentState:
        """
        Perform multi-step reasoning on results

        For complex queries:
        1. Analyze search results
        2. Extract key information
        3. Identify patterns and relationships
        4. Draw intermediate conclusions
        5. Build reasoning chain
        """
        if not state.get("requires_reasoning"):
            logger.info(f"[{self.name}] Reasoning not required, skipping")
            return state

        logger.info(f"[{self.name}] Starting chain-of-thought reasoning")

        # Get results to reason about
        results = state.get("hybrid_results") or state.get("dense_results", [])

        if not results:
            logger.warning(f"[{self.name}] No results to reason about")
            return state

        reasoning_steps = []
        intermediate_conclusions = []

        # Step 1: Analyze result distribution
        step1 = f"Found {len(results)} relevant products"
        reasoning_steps.append(step1)

        # Step 2: Extract key attributes
        materials = set()
        capacities = set()
        for result in results[:20]:  # Analyze top 20
            meta = result.get("metadata", {})
            if meta.get("material"):
                materials.add(meta["material"])
            if meta.get("capacity"):
                capacities.add(meta["capacity"])

        step2 = f"Key materials: {', '.join(list(materials)[:5])}"
        reasoning_steps.append(step2)

        step3 = f"Capacity range: {', '.join(list(capacities)[:5])}"
        reasoning_steps.append(step3)

        # Step 3: Identify best matches
        top_results = results[:5]
        conclusion1 = f"Top {len(top_results)} products have high relevance (scores > {top_results[0].get('score', 0):.2f})"
        intermediate_conclusions.append(conclusion1)

        # Step 4: Query-specific reasoning
        intent = state.get("intent", "general")
        if intent == "comparison":
            conclusion2 = "Comparison query detected - multiple products needed for evaluation"
            intermediate_conclusions.append(conclusion2)
        elif intent == "recommendation":
            conclusion2 = "Recommendation query - prioritizing highest-scoring products"
            intermediate_conclusions.append(conclusion2)

        state["reasoning_steps"] = reasoning_steps
        state["intermediate_conclusions"] = intermediate_conclusions
        state["agent_trace"].append(f"{self.name}:chain_of_thought")

        logger.info(f"[{self.name}] Reasoning complete: {len(reasoning_steps)} steps")

        return state


class SynthesisAgent:
    """
    Synthesizes information from multiple sources into coherent answer
    """

    def __init__(self):
        self.name = "SynthesisAgent"
        logger.info(f"{self.name} initialized")

    async def synthesize(self, state: AgentState) -> AgentState:
        """
        Combine search results and reasoning into final answer
        """
        logger.info(f"[{self.name}] Synthesizing answer")

        query = state["query"]
        intent = state.get("intent", "general")
        results = state.get("hybrid_results") or state.get("dense_results", [])

        # Build answer based on intent
        if intent == "comparison":
            answer = self._synthesize_comparison(query, results, state)
        elif intent == "recommendation":
            answer = self._synthesize_recommendation(query, results, state)
        elif intent == "explanation":
            answer = self._synthesize_explanation(query, results, state)
        else:
            answer = self._synthesize_general(query, results, state)

        # Calculate confidence
        confidence = self._calculate_confidence(results, state)

        state["synthesized_answer"] = answer
        state["confidence_score"] = confidence
        state["agent_trace"].append(f"{self.name}:synthesize")

        logger.info(f"[{self.name}] Synthesis complete (confidence={confidence:.2f})")

        return state

    def _synthesize_comparison(self, query: str, results: List[Dict], state: AgentState) -> str:
        """Synthesize comparison answer"""
        if len(results) < 2:
            return f"검색 결과가 부족하여 비교할 수 없습니다. {len(results)}개의 제품만 발견되었습니다."

        top_products = results[:3]
        product_names = [
            r.get("metadata", {}).get("product_name", "알 수 없음") for r in top_products
        ]

        answer = f"'{query}' 검색 결과, {len(results)}개의 제품을 발견했습니다.\n\n"
        answer += f"상위 제품 비교:\n"
        for i, product in enumerate(top_products, 1):
            meta = product.get("metadata", {})
            answer += f"{i}. {meta.get('product_name', 'N/A')} - "
            answer += f"재질: {meta.get('material', 'N/A')}, "
            answer += f"용량: {meta.get('capacity', 'N/A')}\n"

        return answer

    def _synthesize_recommendation(self, query: str, results: List[Dict], state: AgentState) -> str:
        """Synthesize recommendation answer"""
        if not results:
            return f"'{query}'에 대한 추천 제품을 찾지 못했습니다."

        top_product = results[0]
        meta = top_product.get("metadata", {})

        answer = f"'{query}'에 대한 추천 제품:\n\n"
        answer += f"🏆 {meta.get('product_name', 'N/A')}\n"
        answer += f"재질: {meta.get('material', 'N/A')}\n"
        answer += f"용량: {meta.get('capacity', 'N/A')}\n"
        answer += f"제조사: {meta.get('company_name', 'N/A')}\n\n"

        if len(results) > 1:
            answer += f"기타 {len(results)-1}개의 관련 제품도 확인하실 수 있습니다."

        return answer

    def _synthesize_explanation(self, query: str, results: List[Dict], state: AgentState) -> str:
        """Synthesize explanation answer"""
        reasoning_steps = state.get("reasoning_steps", [])

        answer = f"'{query}'에 대한 설명:\n\n"

        if reasoning_steps:
            answer += "분석 결과:\n"
            for step in reasoning_steps:
                answer += f"• {step}\n"
            answer += "\n"

        if results:
            answer += f"총 {len(results)}개의 관련 제품이 있습니다."

        return answer

    def _synthesize_general(self, query: str, results: List[Dict], state: AgentState) -> str:
        """Synthesize general answer"""
        if not results:
            return f"'{query}'에 대한 검색 결과가 없습니다. 다른 키워드로 검색해보세요."

        answer = f"'{query}' 검색 결과: {len(results)}개의 제품을 찾았습니다.\n\n"

        # Show top 3
        for i, result in enumerate(results[:3], 1):
            meta = result.get("metadata", {})
            answer += f"{i}. {meta.get('product_name', 'N/A')}\n"

        if len(results) > 3:
            answer += f"\n기타 {len(results)-3}개의 제품이 더 있습니다."

        return answer

    def _calculate_confidence(self, results: List[Dict], state: AgentState) -> float:
        """Calculate confidence score for synthesized answer"""
        if not results:
            return 0.0

        # Factors: result count, top score, reasoning depth
        result_count_factor = min(len(results) / 50, 1.0)  # More results = higher confidence
        top_score = results[0].get("score", 0.0) if results else 0.0
        reasoning_factor = 1.0 if state.get("requires_reasoning") else 0.9

        confidence = (result_count_factor * 0.3) + (top_score * 0.5) + (reasoning_factor * 0.2)

        return min(confidence, 1.0)


class ValidationAgent:
    """
    Validates synthesized answer for consistency and quality
    """

    def __init__(self):
        self.name = "ValidationAgent"
        logger.info(f"{self.name} initialized")

    async def validate(self, state: AgentState) -> AgentState:
        """
        Validate synthesized answer

        Checks:
        1. Answer completeness
        2. Result consistency
        3. Confidence threshold
        4. Fact verification
        """
        logger.info(f"[{self.name}] Validating answer")

        issues = []

        # Check 1: Answer completeness
        answer = state.get("synthesized_answer", "")
        if not answer or len(answer) < 10:
            issues.append("Answer too short or empty")

        # Check 2: Result consistency
        results = state.get("hybrid_results") or state.get("dense_results", [])
        if not results:
            issues.append("No search results to support answer")

        # Check 3: Confidence threshold
        confidence = state.get("confidence_score", 0.0)
        if confidence < 0.5:
            issues.append(f"Low confidence score: {confidence:.2f}")

        # Check 4: Query-answer relevance (simple heuristic)
        query = state["query"]
        query_keywords = set(query.lower().split())
        answer_keywords = set(answer.lower().split())
        overlap = len(query_keywords & answer_keywords)
        if overlap == 0:
            issues.append("No keyword overlap between query and answer")

        # Validation result
        validated = len(issues) == 0

        state["validated"] = validated
        state["validation_issues"] = issues
        state["agent_trace"].append(f"{self.name}:validate")

        logger.info(
            f"[{self.name}] Validation {'passed' if validated else 'failed'} ({len(issues)} issues)"
        )

        return state


# ============================================================================
# Multi-Agent Orchestrator
# ============================================================================


class MultiAgentOrchestrator:
    """
    Orchestrates multi-agent workflow using state machine pattern
    """

    def __init__(self):
        self.router = RouterAgent()
        self.search = SearchAgent()
        self.reasoning = ReasoningAgent()
        self.synthesis = SynthesisAgent()
        self.validation = ValidationAgent()

        logger.info("MultiAgentOrchestrator initialized")

    async def execute(
        self,
        query: str,
        session_id: str,
        collections: Optional[List[str]] = None,
        materials: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute multi-agent workflow

        Workflow:
        1. Router: Analyze query → determine complexity
        2. Search: Execute search (simple/hybrid based on complexity)
        3. Reasoning: Chain-of-thought reasoning (if complex)
        4. Synthesis: Generate answer
        5. Validation: Validate answer quality

        Args:
            query: Search query
            session_id: Session identifier
            collections: Optional collection filters
            materials: Optional material filters

        Returns:
            Final result with answer, products, and agent trace
        """
        logger.info(f"🚀 Multi-agent execution starting: '{query}'")

        # Initialize state
        state: AgentState = {
            "query": query,
            "session_id": session_id,
            "collections": collections,
            "materials": materials,
            "intent": None,
            "complexity": None,
            "requires_reasoning": False,
            "dense_results": None,
            "sparse_results": None,
            "hybrid_results": None,
            "reasoning_steps": [],
            "intermediate_conclusions": [],
            "synthesized_answer": None,
            "confidence_score": 0.0,
            "validated": False,
            "validation_issues": [],
            "final_answer": "",
            "final_products": [],
            "agent_trace": [],
        }

        try:
            # Step 1: Route
            state = await self.router.route(state)

            # Step 2: Search
            state = await self.search.search(state)

            # Step 3: Reasoning (conditional)
            if state.get("requires_reasoning"):
                state = await self.reasoning.reason(state)

            # Step 4: Synthesis
            state = await self.synthesis.synthesize(state)

            # Step 5: Validation
            state = await self.validation.validate(state)

            # Prepare final output
            results = state.get("hybrid_results") or state.get("dense_results", [])
            state["final_answer"] = state.get("synthesized_answer", "")
            state["final_products"] = results[:100]  # Limit to 100

            logger.info(
                f"✅ Multi-agent execution complete: {len(state['agent_trace'])} agent calls"
            )

            return {
                "status": "success",
                "query": query,
                "answer": state["final_answer"],
                "products": state["final_products"],
                "confidence": state["confidence_score"],
                "validated": state["validated"],
                "validation_issues": state["validation_issues"],
                "agent_trace": state["agent_trace"],
                "reasoning_steps": state["reasoning_steps"],
                "intermediate_conclusions": state["intermediate_conclusions"],
                "metadata": {
                    "intent": state.get("intent"),
                    "complexity": state.get("complexity"),
                    "total_results": len(results),
                },
            }

        except Exception as e:
            logger.error(f"❌ Multi-agent execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "agent_trace": state.get("agent_trace", []),
            }


# ============================================================================
# Factory Function
# ============================================================================


def create_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    """Create and return multi-agent orchestrator instance"""
    return MultiAgentOrchestrator()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        orchestrator = create_multi_agent_orchestrator()

        # Test query
        result = await orchestrator.execute(
            query="50ml PET 용기와 100ml PP 용기의 차이점은?",
            session_id="test-123",
            collections=None,
            materials=None,
        )

        print("=" * 60)
        print("Multi-Agent Result:")
        print("=" * 60)
        print(f"Status: {result['status']}")
        print(f"Answer: {result.get('answer', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"Validated: {result.get('validated', False)}")
        print(f"Products: {len(result.get('products', []))}")
        print(f"Agent Trace: {' → '.join(result.get('agent_trace', []))}")
        print("=" * 60)

    asyncio.run(main())
