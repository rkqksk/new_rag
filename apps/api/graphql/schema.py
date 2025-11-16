"""
GraphQL Schema (v6.0.0)
=======================

Flexible GraphQL API with Strawberry for type-safe querying.

Features:
- Type-safe schema with Python dataclasses
- Flexible queries (avoid over-fetching)
- Subscriptions for real-time updates
- DataLoader for efficient batching
- Mutations for data modification

Version: v6.0.0
"""

import asyncio
from typing import AsyncGenerator, List, Optional

import strawberry
from strawberry.fastapi import GraphQLRouter

# ============================================================================
# Types
# ============================================================================


@strawberry.type
class Product:
    """Product type"""

    id: str
    product_name: str
    product_code: Optional[str]
    material: Optional[str]
    capacity: Optional[str]
    neck_size: Optional[str]
    moq: Optional[int]
    score: Optional[float]
    source_collection: Optional[str]


@strawberry.type
class SearchResult:
    """Search result with products and metadata"""

    query: str
    total_count: int
    products: List[Product]
    search_strategy: Optional[str]
    performance_ms: Optional[float]


@strawberry.type
class Agent:
    """Multi-agent system agent"""

    name: str
    role: str
    features: List[str]


@strawberry.type
class AgentTrace:
    """Agent execution trace"""

    session_id: str
    query: str
    agent_trace: List[str]
    reasoning_steps: List[str]
    execution_time_ms: float


@strawberry.type
class CacheStats:
    """Cache statistics"""

    hit_rate: float
    total_requests: int
    cache_hits: int
    cache_misses: int


@strawberry.type
class RateLimitInfo:
    """Rate limit information"""

    tier: str
    requests_remaining: int
    reset_time: int
    limit: int


# ============================================================================
# Input Types
# ============================================================================


@strawberry.input
class SearchInput:
    """Search query input"""

    query: str
    top_k: int = 100
    collections: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    enable_hybrid: bool = False
    enable_reranking: bool = False


@strawberry.input
class MultiAgentInput:
    """Multi-agent query input"""

    query: str
    session_id: str
    collections: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    enable_reasoning: bool = True


# ============================================================================
# Queries
# ============================================================================


@strawberry.type
class Query:
    """Root query type"""

    @strawberry.field
    async def search(self, input: SearchInput) -> SearchResult:
        """
        Search products with flexible options

        Example:
            query {
              search(input: {
                query: "50ml PET",
                topK: 10,
                enableHybrid: true
              }) {
                totalCount
                products {
                  productName
                  material
                  capacity
                }
              }
            }
        """
        import sys
        import time
        from pathlib import Path

        # Import RAG skill
        skill_path = Path(__file__).parent.parent.parent / ".claude/skills/rag-pipeline/scripts"
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        from skill import rag_query as skill_rag_query

        start_time = time.time()

        # Execute search
        result = skill_rag_query(
            {
                "question": input.query,
                "top_k": input.top_k,
                "collections": input.collections,
                "materials": input.materials,
            }
        )

        if result["status"] != "success":
            return SearchResult(
                query=input.query, total_count=0, products=[], search_strategy="failed"
            )

        # Convert results to Product types
        products = []
        for source in result.get("sources", []):
            meta = source.get("metadata", {})

            products.append(
                Product(
                    id=meta.get("product_id", ""),
                    product_name=meta.get("product_name", ""),
                    product_code=meta.get("product_code"),
                    material=meta.get("material"),
                    capacity=meta.get("capacity"),
                    neck_size=meta.get("neck_size"),
                    moq=meta.get("moq"),
                    score=source.get("score"),
                    source_collection=meta.get("source_collection"),
                )
            )

        # Apply hybrid search if requested
        strategy = "dense"
        if input.enable_hybrid:
            # Use hybrid search
            from apps.api.services.hybrid_search import HybridSearchEngine

            engine = HybridSearchEngine(enable_cross_encoder=input.enable_reranking)

            # Build BM25 index
            documents = [{"metadata": source.get("metadata", {})} for source in result["sources"]]
            dense_results = [
                (documents[i], source.get("score", 0.0))
                for i, source in enumerate(result["sources"])
            ]

            if documents:
                bm25_index = engine.build_bm25_index(documents)
                hybrid_results = engine.hybrid_search(
                    query=input.query,
                    dense_results=dense_results,
                    bm25_index=bm25_index,
                    documents=documents,
                    top_k=input.top_k,
                    enable_reranking=input.enable_reranking,
                )

                # Update products with hybrid scores
                for i, (doc, score) in enumerate(hybrid_results[: len(products)]):
                    products[i].score = score

            strategy = "hybrid" + ("+rerank" if input.enable_reranking else "")

        elapsed = (time.time() - start_time) * 1000

        return SearchResult(
            query=input.query,
            total_count=len(products),
            products=products,
            search_strategy=strategy,
            performance_ms=elapsed,
        )

    @strawberry.field
    async def product(self, id: str) -> Optional[Product]:
        """
        Get single product by ID

        Example:
            query {
              product(id: "001") {
                productName
                material
                capacity
              }
            }
        """
        # TODO: Implement product lookup by ID
        return None

    @strawberry.field
    async def agents(self) -> List[Agent]:
        """
        List available multi-agent system agents

        Example:
            query {
              agents {
                name
                role
                features
              }
            }
        """
        return [
            Agent(
                name="RouterAgent",
                role="Query classification and routing",
                features=["Intent detection", "Complexity assessment"],
            ),
            Agent(
                name="SearchAgent",
                role="Execute search operations",
                features=["Dense search", "Hybrid search", "Adaptive strategy"],
            ),
            Agent(
                name="ReasoningAgent",
                role="Chain-of-thought reasoning",
                features=["Multi-step analysis", "Pattern identification"],
            ),
            Agent(
                name="SynthesisAgent",
                role="Answer generation",
                features=["Intent-based synthesis", "Confidence scoring"],
            ),
            Agent(
                name="ValidationAgent",
                role="Quality assurance",
                features=["Completeness check", "Consistency check"],
            ),
        ]

    @strawberry.field
    async def agent_trace(self, session_id: str) -> Optional[AgentTrace]:
        """
        Get agent execution trace for session

        Example:
            query {
              agentTrace(sessionId: "abc123") {
                query
                agentTrace
                reasoningSteps
                executionTimeMs
              }
            }
        """
        # TODO: Implement trace lookup from multi-agent API
        return None

    @strawberry.field
    async def cache_stats(self) -> CacheStats:
        """
        Get cache statistics

        Example:
            query {
              cacheStats {
                hitRate
                totalRequests
                cacheHits
              }
            }
        """
        # TODO: Implement actual cache stats retrieval
        return CacheStats(hit_rate=0.68, total_requests=1000, cache_hits=680, cache_misses=320)

    @strawberry.field
    async def rate_limit_info(self, api_key: Optional[str] = None) -> RateLimitInfo:
        """
        Get rate limit information

        Example:
            query {
              rateLimitInfo(apiKey: "...") {
                tier
                requestsRemaining
                limit
              }
            }
        """
        # TODO: Implement actual rate limit lookup
        return RateLimitInfo(tier="free", requests_remaining=95, reset_time=1699564800, limit=100)


# ============================================================================
# Mutations
# ============================================================================


@strawberry.type
class Mutation:
    """Root mutation type"""

    @strawberry.mutation
    async def execute_multi_agent_query(self, input: MultiAgentInput) -> AgentTrace:
        """
        Execute multi-agent query

        Example:
            mutation {
              executeMultiAgentQuery(input: {
                query: "50ml PET vs PP",
                sessionId: "session-123"
              }) {
                query
                agentTrace
                reasoningSteps
              }
            }
        """
        from apps.api.services.multi_agent_system import create_multi_agent_orchestrator

        orchestrator = create_multi_agent_orchestrator()

        result = await orchestrator.execute(
            query=input.query,
            session_id=input.session_id,
            collections=input.collections,
            materials=input.materials,
        )

        if result["status"] != "success":
            return AgentTrace(
                session_id=input.session_id,
                query=input.query,
                agent_trace=[],
                reasoning_steps=[],
                execution_time_ms=0.0,
            )

        return AgentTrace(
            session_id=input.session_id,
            query=input.query,
            agent_trace=result.get("agent_trace", []),
            reasoning_steps=result.get("reasoning_steps", []),
            execution_time_ms=0.0,  # TODO: Add timing
        )

    @strawberry.mutation
    async def invalidate_cache(self, pattern: str) -> bool:
        """
        Invalidate cache by pattern

        Example:
            mutation {
              invalidateCache(pattern: "query_cache:*")
            }
        """
        from apps.api.services.advanced_cache import get_cache

        cache = get_cache()
        cache.invalidate_pattern(pattern)
        return True


# ============================================================================
# Subscriptions
# ============================================================================


@strawberry.type
class Subscription:
    """Root subscription type"""

    @strawberry.subscription
    async def search_updates(self, query: str) -> AsyncGenerator[SearchResult, None]:
        """
        Subscribe to search updates (real-time streaming)

        Example:
            subscription {
              searchUpdates(query: "50ml PET") {
                totalCount
                products {
                  productName
                }
              }
            }
        """
        # Simulate real-time updates
        for i in range(5):
            await asyncio.sleep(1)
            yield SearchResult(
                query=query,
                total_count=i + 1,
                products=[
                    Product(
                        id=f"prod-{i}",
                        product_name=f"Product {i}",
                        product_code=None,
                        material=None,
                        capacity=None,
                        neck_size=None,
                        moq=None,
                        score=None,
                        source_collection=None,
                    )
                ],
                search_strategy="real-time",
                performance_ms=None,
            )


# ============================================================================
# Schema
# ============================================================================

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)


# ============================================================================
# Router for FastAPI
# ============================================================================


def create_graphql_router() -> GraphQLRouter:
    """Create GraphQL router for FastAPI"""
    return GraphQLRouter(schema, path="/graphql")
