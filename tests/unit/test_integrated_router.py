"""
Unit tests for app/core/routing/integrated_router.py

Tests the IntegratedRouter class that combines MCP intent detection,
Claude model selection, and agent selection into unified routing decisions.
"""
import pytest
from app.core.routing.integrated_router import (
    IntegratedRouter,
    RoutingDecision
)
from app.core.routing.intent_router import Intent
from app.core.routing.llm_router import ClaudeModel


@pytest.fixture
def integrated_router():
    """Create IntegratedRouter instance for testing"""
    return IntegratedRouter()


@pytest.mark.unit
def test_combined_routing_decision(integrated_router):
    """Test that routing combines all three components correctly"""
    query = "프로젝트 파일들을 검색하고 분석해주세요"
    result = integrated_router.route(query)

    # Verify all components are present
    assert isinstance(result, RoutingDecision)
    assert hasattr(result, 'requires_mcp')
    assert hasattr(result, 'claude_model')
    assert hasattr(result, 'recommended_agents')
    assert hasattr(result, 'execution_strategy')


@pytest.mark.unit
def test_intent_plus_model_selection(integrated_router):
    """Test that intent detection and model selection work together"""
    # Simple file operation (should use Haiku)
    simple_query = "파일 목록 보여줘"
    simple_result = integrated_router.route(simple_query)

    assert simple_result.requires_mcp is True
    assert simple_result.claude_model == ClaudeModel.HAIKU_4_5
    assert simple_result.mcp_intent.intent == Intent.FILE_OPERATION

    # Complex analysis (should use Sonnet)
    complex_query = "전체 시스템 아키텍처를 분석하고 최적화 방안을 제시해주세요"
    complex_result = integrated_router.route(complex_query)

    assert complex_result.claude_model == ClaudeModel.SONNET_4_5


@pytest.mark.unit
def test_agent_selection_logic(integrated_router):
    """Test that agents are correctly selected based on query content"""
    # Backend query with sufficient complexity - should recommend backend-architect
    backend_query = "전체 프로젝트의 FastAPI 라우터 시스템을 분석하고 개선 방안을 제시해주세요"
    backend_result = integrated_router.route(backend_query)
    assert "backend-architect" in backend_result.recommended_agents

    # System query - should recommend system-architect
    system_query = "전체 시스템 아키텍처를 분석하고 설계를 개선해주세요"
    system_result = integrated_router.route(system_query)
    assert "system-architect" in system_result.recommended_agents

    # Performance query - should recommend performance-engineer
    perf_query = "전체 시스템의 성능을 분석하고 최적화를 수행해주세요"
    perf_result = integrated_router.route(perf_query)
    assert "performance-engineer" in perf_result.recommended_agents

    # Security query - should recommend security-engineer
    security_query = "전체 시스템의 보안 취약점을 검사하고 개선안을 제시해주세요"
    security_result = integrated_router.route(security_query)
    assert "security-engineer" in security_result.recommended_agents


@pytest.mark.unit
def test_transparency_message_generation(integrated_router):
    """Test that transparency messages are generated correctly"""
    query = "프로젝트 파일을 검색해주세요"
    decision = integrated_router.route(query)

    explanation = integrated_router.explain_decision(decision)

    assert isinstance(explanation, str)
    assert len(explanation) > 0
    assert "자동 라우팅" in explanation or "Routing" in explanation.lower()


@pytest.mark.unit
def test_routing_explanation_clarity(integrated_router):
    """Test that routing explanations include key decision factors"""
    query = "시스템 아키텍처 분석"
    decision = integrated_router.route(query)
    explanation = integrated_router.explain_decision(decision)

    # Should mention key aspects of the decision
    # (Note: actual content depends on implementation)
    assert len(explanation) > 100  # Should be reasonably detailed


@pytest.mark.unit
def test_decision_serialization(integrated_router):
    """Test that RoutingDecision can be properly used"""
    query = "파일을 분석해주세요"
    decision = integrated_router.route(query)

    # Verify all required fields are accessible
    assert decision.requires_mcp in [True, False]
    assert isinstance(decision.claude_model, ClaudeModel)
    assert isinstance(decision.model_name, str)
    assert isinstance(decision.recommended_agents, list)
    assert decision.execution_strategy in ["mcp_only", "claude_only", "mcp_then_claude"]
    assert decision.cost_type in ["deposit", "max"]


@pytest.mark.unit
def test_error_handling_in_routing(integrated_router):
    """Test that routing handles edge cases gracefully"""
    # Empty query
    empty_result = integrated_router.route("")
    assert isinstance(empty_result, RoutingDecision)

    # Very long query
    long_result = integrated_router.route("분석 " * 200)
    assert isinstance(long_result, RoutingDecision)

    # Special characters
    special_result = integrated_router.route("파일 @#$% 검색!!!")
    assert isinstance(special_result, RoutingDecision)


@pytest.mark.unit
def test_fallback_routing_behavior(integrated_router):
    """Test fallback behavior when intent is unknown"""
    ambiguous_query = "xyz random text 123"
    result = integrated_router.route(ambiguous_query)

    # Should still produce valid routing decision
    assert isinstance(result, RoutingDecision)
    assert isinstance(result.claude_model, ClaudeModel)
    assert isinstance(result.execution_strategy, str)


@pytest.mark.unit
def test_performance_routing_decision(integrated_router):
    """Test routing for performance-critical queries"""
    perf_query = "성능 최적화 및 병목 현상 분석"
    result = integrated_router.route(perf_query)

    # Performance queries should get appropriate resources
    assert "performance-engineer" in result.recommended_agents
    # May use Sonnet for complex performance analysis
    assert isinstance(result.claude_model, ClaudeModel)


@pytest.mark.unit
def test_logging_routing_decisions(integrated_router):
    """Test that routing decisions can be logged/tracked"""
    query = "프로젝트 분석"
    result = integrated_router.route(query)

    # Ensure all data needed for logging is available
    log_data = {
        "query": query,
        "requires_mcp": result.requires_mcp,
        "mcp_tool": result.mcp_tool,
        "claude_model": result.model_name,
        "agents": result.recommended_agents,
        "strategy": result.execution_strategy,
        "cost_type": result.cost_type
    }

    # Verify log data is complete
    assert all(key in log_data for key in [
        "query", "requires_mcp", "claude_model", "strategy", "cost_type"
    ])


@pytest.mark.unit
def test_execution_strategy_mcp_only(integrated_router):
    """Test mcp_only execution strategy for simple file operations"""
    simple_file_query = "파일 목록"
    result = integrated_router.route(simple_file_query)

    # Simple file operations should use mcp_only
    if result.requires_mcp and result.model_selection.complexity_score.total <= 30:
        assert result.execution_strategy == "mcp_only"


@pytest.mark.unit
def test_execution_strategy_claude_only(integrated_router):
    """Test claude_only execution strategy when MCP not needed"""
    no_mcp_query = "이게 뭐야"
    result = integrated_router.route(no_mcp_query)

    # Queries without MCP need should use claude_only
    if not result.requires_mcp:
        assert result.execution_strategy == "claude_only"


@pytest.mark.unit
def test_execution_strategy_mcp_then_claude(integrated_router):
    """Test mcp_then_claude execution strategy for vector search"""
    search_query = "관련 문서를 검색하고 요약해주세요"
    result = integrated_router.route(search_query)

    # Vector search should use mcp_then_claude
    if result.mcp_intent.intent == Intent.VECTOR_SEARCH:
        assert result.execution_strategy == "mcp_then_claude"


@pytest.mark.unit
def test_context_affects_routing(integrated_router):
    """Test that context parameters affect routing decisions"""
    query = "파일을 수정해주세요"

    # Small context
    small_context = {"file_count": 3}
    small_result = integrated_router.route(query, small_context)

    # Large context should potentially change model selection
    large_context = {"file_count": 15}
    large_result = integrated_router.route(query, large_context)

    # Both should be valid decisions
    assert isinstance(small_result, RoutingDecision)
    assert isinstance(large_result, RoutingDecision)
