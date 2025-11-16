"""
Multi-Agent System API Endpoints (v6.0.0)
=========================================

Endpoints for multi-agent orchestration with specialized agents:
- Router, Search, Reasoning, Synthesis, Validation

Features:
- Intelligent query routing
- Chain-of-thought reasoning for complex queries
- Multi-source information synthesis
- Answer validation and quality checks
- Detailed agent execution traces

Endpoints:
- POST /api/v1/agents/query - Execute multi-agent query
- GET  /api/v1/agents/health - Health check
- GET  /api/v1/agents/trace/{session_id} - Get agent execution trace
"""

import logging
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.multi_agent_system import MultiAgentOrchestrator, create_multi_agent_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["multi-agent"])

# Global orchestrator (singleton)
_orchestrator: Optional[MultiAgentOrchestrator] = None

# Store execution traces (in-memory, could be Redis/DB in production)
_execution_traces: Dict[str, Dict] = {}


def get_orchestrator() -> MultiAgentOrchestrator:
    """Get or create multi-agent orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = create_multi_agent_orchestrator()
    return _orchestrator


# ============================================================================
# Request/Response Models
# ============================================================================


class MultiAgentQueryRequest(BaseModel):
    """Multi-agent query request"""

    query: str = Field(..., description="Search query", min_length=1)
    session_id: str = Field(..., description="Session ID")
    collections: Optional[List[str]] = Field(None, description="Collections to search")
    materials: Optional[List[str]] = Field(None, description="Material filters")
    enable_reasoning: bool = Field(True, description="Enable chain-of-thought reasoning")
    enable_validation: bool = Field(True, description="Enable answer validation")


class MultiAgentQueryResponse(BaseModel):
    """Multi-agent query response"""

    status: str
    query: str
    answer: str
    products: List[Dict]
    confidence: float
    validated: bool
    validation_issues: List[str]
    agent_trace: List[str]
    reasoning_steps: List[str]
    intermediate_conclusions: List[str]
    metadata: Dict
    performance: Dict


class AgentTraceResponse(BaseModel):
    """Agent execution trace response"""

    session_id: str
    query: str
    agent_trace: List[str]
    reasoning_steps: List[str]
    execution_time_ms: float
    timestamp: str


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/query", response_model=MultiAgentQueryResponse)
async def multi_agent_query(request: MultiAgentQueryRequest):
    """
    Execute multi-agent query with orchestrated workflow

    Workflow:
    1. Router Agent: Classify query and determine complexity
    2. Search Agent: Execute appropriate search strategy
    3. Reasoning Agent: Chain-of-thought reasoning (if complex)
    4. Synthesis Agent: Generate coherent answer
    5. Validation Agent: Validate answer quality

    Args:
        request: Query parameters

    Returns:
        Multi-agent query results with detailed trace
    """
    start_time = time.time()

    try:
        logger.info(f"Multi-agent query: {request.query}")

        orchestrator = get_orchestrator()

        # Execute multi-agent workflow
        result = await orchestrator.execute(
            query=request.query,
            session_id=request.session_id,
            collections=request.collections,
            materials=request.materials,
        )

        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Query failed"))

        total_time = time.time() - start_time

        # Store execution trace
        _execution_traces[request.session_id] = {
            "query": request.query,
            "agent_trace": result.get("agent_trace", []),
            "reasoning_steps": result.get("reasoning_steps", []),
            "execution_time_ms": total_time * 1000,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Format products
        formatted_products = []
        for product in result.get("products", [])[:100]:
            metadata = product.get("metadata", {})
            formatted_products.append(
                {
                    "product_id": metadata.get("product_id", ""),
                    "product_name": metadata.get("product_name", ""),
                    "product_code": metadata.get("product_code", ""),
                    "material": metadata.get("material", ""),
                    "capacity": metadata.get("capacity", ""),
                    "score": product.get("score", 0.0),
                    "source_collection": metadata.get("source_collection", "unknown"),
                }
            )

        # Performance metrics
        performance = {
            "total_time_ms": round(total_time * 1000, 2),
            "agents_invoked": len(result.get("agent_trace", [])),
            "reasoning_steps": len(result.get("reasoning_steps", [])),
        }

        return MultiAgentQueryResponse(
            status="success",
            query=request.query,
            answer=result.get("answer", ""),
            products=formatted_products,
            confidence=result.get("confidence", 0.0),
            validated=result.get("validated", False),
            validation_issues=result.get("validation_issues", []),
            agent_trace=result.get("agent_trace", []),
            reasoning_steps=result.get("reasoning_steps", []),
            intermediate_conclusions=result.get("intermediate_conclusions", []),
            metadata=result.get("metadata", {}),
            performance=performance,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-agent query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trace/{session_id}", response_model=AgentTraceResponse)
async def get_agent_trace(session_id: str):
    """
    Get agent execution trace for a session

    Args:
        session_id: Session identifier

    Returns:
        Agent execution trace with reasoning steps
    """
    if session_id not in _execution_traces:
        raise HTTPException(status_code=404, detail=f"No trace found for session: {session_id}")

    trace = _execution_traces[session_id]

    return AgentTraceResponse(
        session_id=session_id,
        query=trace["query"],
        agent_trace=trace["agent_trace"],
        reasoning_steps=trace["reasoning_steps"],
        execution_time_ms=trace["execution_time_ms"],
        timestamp=trace["timestamp"],
    )


@router.get("/health")
async def multi_agent_health():
    """Check multi-agent system health"""
    orchestrator = get_orchestrator()

    return {
        "status": "healthy",
        "agents": {
            "router": orchestrator.router.name,
            "search": orchestrator.search.name,
            "reasoning": orchestrator.reasoning.name,
            "synthesis": orchestrator.synthesis.name,
            "validation": orchestrator.validation.name,
        },
        "capabilities": [
            "Intent classification",
            "Complexity assessment",
            "Dense/Hybrid search routing",
            "Chain-of-thought reasoning",
            "Multi-source synthesis",
            "Answer validation",
        ],
        "execution_traces_stored": len(_execution_traces),
        "endpoint": "/api/v1/agents/query",
    }


@router.get("/config")
async def multi_agent_config():
    """Get multi-agent system configuration"""
    return {
        "agents": [
            {
                "name": "RouterAgent",
                "role": "Query classification and routing",
                "features": ["Intent detection", "Complexity assessment"],
            },
            {
                "name": "SearchAgent",
                "role": "Execute search operations",
                "features": ["Dense search", "Hybrid search", "Adaptive strategy"],
            },
            {
                "name": "ReasoningAgent",
                "role": "Chain-of-thought reasoning",
                "features": ["Multi-step analysis", "Pattern identification", "Conclusions"],
            },
            {
                "name": "SynthesisAgent",
                "role": "Answer generation",
                "features": [
                    "Intent-based synthesis",
                    "Comparison/Recommendation/Explanation",
                    "Confidence scoring",
                ],
            },
            {
                "name": "ValidationAgent",
                "role": "Quality assurance",
                "features": [
                    "Completeness check",
                    "Consistency check",
                    "Confidence threshold",
                    "Relevance check",
                ],
            },
        ],
        "workflow": [
            "1. Router → Classify query",
            "2. Search → Execute search",
            "3. Reasoning → Analyze results (if complex)",
            "4. Synthesis → Generate answer",
            "5. Validation → Validate quality",
        ],
        "complexity_levels": {
            "simple": "Direct search (dense-only)",
            "medium": "Hybrid search (dense + sparse)",
            "complex": "Hybrid search + re-ranking + reasoning",
        },
    }


@router.delete("/traces")
async def clear_traces():
    """Clear all execution traces (admin only)"""
    global _execution_traces
    count = len(_execution_traces)
    _execution_traces.clear()

    return {"status": "success", "traces_cleared": count}
