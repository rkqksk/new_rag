"""
Unit tests for app/core/routing/llm_router.py

Tests the ClaudeRouter and ComplexityAnalyzer classes for automatic
selection between Claude Haiku 4.5 and Sonnet 4.5 based on query complexity.
"""
import pytest
from app.core.routing.llm_router import (
    ClaudeRouter,
    ComplexityAnalyzer,
    ClaudeModel,
    ComplexityScore,
    ModelSelection
)


@pytest.fixture
def complexity_analyzer():
    """Create ComplexityAnalyzer instance for testing"""
    return ComplexityAnalyzer()


@pytest.fixture
def claude_router():
    """Create ClaudeRouter instance for testing"""
    return ClaudeRouter()


@pytest.mark.unit
def test_complexity_score_calculation(complexity_analyzer):
    """Test that complexity score is calculated correctly"""
    query = "프로젝트 전체 아키텍처를 분석하고 최적화 방안을 제시해주세요"
    score = complexity_analyzer.analyze(query)

    assert isinstance(score, ComplexityScore)
    assert 0 <= score.total <= 100
    assert score.total > 50  # Should be complex


@pytest.mark.unit
def test_haiku_selection_simple_query(claude_router):
    """Test that Haiku is selected for simple queries"""
    simple_query = "이게 뭐야?"
    result = claude_router.route(simple_query)

    assert result.model == ClaudeModel.HAIKU_4_5
    assert result.cost_type == "deposit"
    assert result.complexity_score.total <= 50


@pytest.mark.unit
def test_sonnet_selection_complex_query(claude_router):
    """Test that Sonnet is selected for complex queries"""
    complex_query = "전체 시스템 아키텍처를 분석하고 성능 최적화 및 보안 검증을 수행해주세요"
    result = claude_router.route(complex_query)

    assert result.model == ClaudeModel.SONNET_4_5
    assert result.cost_type == "max"
    assert result.complexity_score.total > 50


@pytest.mark.unit
def test_length_score_component(complexity_analyzer):
    """Test length score calculation for queries of different lengths"""
    short_query = "뭐야"  # ≤10 words
    medium_query = " ".join(["코드를"] * 20)  # ~20 words (11-30 range)
    long_query = " ".join(["분석"] * 150)  # >100 words

    short_score = complexity_analyzer._score_length(short_query)
    medium_score = complexity_analyzer._score_length(medium_query)
    long_score = complexity_analyzer._score_length(long_query)

    assert short_score == 5
    assert medium_score == 10
    assert long_score == 20
    assert short_score < medium_score < long_score


@pytest.mark.unit
def test_technical_score_component(complexity_analyzer):
    """Test technical complexity scoring"""
    simple_query = "이게 뭐야"
    moderate_query = "어떻게 구현하나요"
    complex_query = "전체 아키텍처를 설계해주세요"
    advanced_query = "대규모 시스템 마이그레이션 전략을 수립해주세요"

    simple_score = complexity_analyzer._score_technical_complexity(simple_query.lower())
    moderate_score = complexity_analyzer._score_technical_complexity(moderate_query.lower())
    complex_score = complexity_analyzer._score_technical_complexity(complex_query.lower())
    advanced_score = complexity_analyzer._score_technical_complexity(advanced_query.lower())

    assert simple_score == 5
    assert moderate_score == 10
    assert complex_score == 18
    assert advanced_score == 25


@pytest.mark.unit
def test_scope_score_component(complexity_analyzer):
    """Test scope scoring for different operation scopes"""
    single_query = "이 함수를 수정해주세요"
    multiple_query = "여러 파일을 리팩토링해주세요"
    project_query = "프로젝트 전체를 분석해주세요"

    single_score = complexity_analyzer._score_scope(single_query.lower())
    multiple_score = complexity_analyzer._score_scope(multiple_query.lower())
    project_score = complexity_analyzer._score_scope(project_query.lower())

    assert single_score == 5
    assert multiple_score == 12
    assert project_score == 20


@pytest.mark.unit
def test_reasoning_score_component(complexity_analyzer):
    """Test reasoning depth scoring"""
    shallow_query = "이게 뭐야"
    moderate_query = "왜 이렇게 작동하나요"
    deep_query = "이 버그의 원인을 분석해주세요"
    strategic_query = "시스템 설계 전략을 제시해주세요"

    shallow_score = complexity_analyzer._score_reasoning_depth(shallow_query.lower())
    moderate_score = complexity_analyzer._score_reasoning_depth(moderate_query.lower())
    deep_score = complexity_analyzer._score_reasoning_depth(deep_query.lower())
    strategic_score = complexity_analyzer._score_reasoning_depth(strategic_query.lower())

    assert shallow_score == 5
    assert moderate_score == 10
    assert deep_score == 15
    assert strategic_score == 20


@pytest.mark.unit
def test_creativity_score_component(complexity_analyzer):
    """Test creativity/generation scoring"""
    no_creativity_query = "이게 뭐야"
    simple_creative_query = "간단한 함수를 만들어주세요"
    complex_creative_query = "새로운 아키텍처를 디자인해주세요"

    no_score = complexity_analyzer._score_creativity(no_creativity_query.lower())
    simple_score = complexity_analyzer._score_creativity(simple_creative_query.lower())
    complex_score = complexity_analyzer._score_creativity(complex_creative_query.lower())

    assert no_score == 0
    assert simple_score == 5
    assert complex_score == 12


@pytest.mark.unit
def test_force_sonnet_conditions(claude_router):
    """Test that certain conditions force Sonnet selection"""
    # Architecture/system keywords
    arch_query = "전체 시스템 아키텍처를 설계해주세요"
    arch_result = claude_router.route(arch_query)
    assert arch_result.model == ClaudeModel.SONNET_4_5

    # Verification keywords
    verify_query = "테스트 결과를 검증해주세요"
    verify_result = claude_router.route(verify_query)
    assert verify_result.model == ClaudeModel.SONNET_4_5

    # Performance optimization
    perf_query = "성능 최적화를 수행해주세요"
    perf_result = claude_router.route(perf_query)
    assert perf_result.model == ClaudeModel.SONNET_4_5


@pytest.mark.unit
def test_cost_type_determination(claude_router):
    """Test that cost types are correctly assigned"""
    haiku_query = "간단히 설명해주세요"
    haiku_result = claude_router.route(haiku_query)
    assert haiku_result.cost_type == "deposit"

    sonnet_query = "전체 프로젝트 아키텍처 분석"
    sonnet_result = claude_router.route(sonnet_query)
    assert sonnet_result.cost_type == "max"


@pytest.mark.unit
def test_model_selection_edge_cases(claude_router):
    """Test model selection for edge cases"""
    # Empty query
    empty_result = claude_router.route("")
    assert empty_result.model == ClaudeModel.HAIKU_4_5  # Should default to Haiku

    # Very long but simple query
    long_simple = "뭐야 " * 100
    long_result = claude_router.route(long_simple)
    # Length score will be high but no technical complexity
    assert isinstance(long_result.model, ClaudeModel)


@pytest.mark.unit
def test_context_based_routing(claude_router):
    """Test that context affects routing decisions"""
    query = "파일을 수정해주세요"

    # Small context - should use Haiku
    small_context = {"file_count": 3}
    small_result = claude_router.route(query, small_context)
    assert small_result.model == ClaudeModel.HAIKU_4_5

    # Large context - should force Sonnet
    large_context = {"file_count": 15}
    large_result = claude_router.route(query, large_context)
    assert large_result.model == ClaudeModel.SONNET_4_5


@pytest.mark.unit
def test_result_structure(claude_router):
    """Test that ModelSelection result has correct structure"""
    query = "테스트 질의입니다"
    result = claude_router.route(query)

    # Verify all required fields
    assert hasattr(result, 'model')
    assert hasattr(result, 'complexity_score')
    assert hasattr(result, 'reason')
    assert hasattr(result, 'cost_type')

    # Verify types
    assert isinstance(result.model, ClaudeModel)
    assert isinstance(result.complexity_score, ComplexityScore)
    assert isinstance(result.reason, str)
    assert result.cost_type in ["deposit", "max"]
