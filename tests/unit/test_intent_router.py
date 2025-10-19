"""
Unit tests for app/core/routing/intent_router.py

Tests the IntentDetector class for automatic user query intent detection
and MCP tool routing decisions.
"""
import pytest
from app.core.routing.intent_router import (
    IntentDetector,
    Intent,
    IntentResult
)


@pytest.fixture
def intent_detector():
    """Create IntentDetector instance for testing"""
    return IntentDetector()


@pytest.mark.unit
def test_detect_file_operation_intent(intent_detector):
    """Test detection of file operation intent with Korean query"""
    query = "프로젝트 폴더에 있는 파일들을 보여줘"
    result = intent_detector.detect(query)

    assert result.intent == Intent.FILE_OPERATION
    assert result.confidence >= 0.3
    assert result.mcp_tool == "filesystem"


@pytest.mark.unit
def test_detect_file_operation_intent_english(intent_detector):
    """Test detection of file operation intent with English query"""
    query = "show me files in the directory"
    result = intent_detector.detect(query)

    assert result.intent == Intent.FILE_OPERATION
    assert result.confidence >= 0.3
    assert result.mcp_tool == "filesystem"


@pytest.mark.unit
def test_detect_vector_search_intent(intent_detector):
    """Test detection of vector search intent"""
    query = "제품 가격 관련 문서를 검색해줘"
    result = intent_detector.detect(query)

    assert result.intent == Intent.VECTOR_SEARCH
    assert result.confidence >= 0.3
    assert result.mcp_tool == "qdrant"


@pytest.mark.unit
def test_detect_vector_search_intent_english(intent_detector):
    """Test detection of vector search intent with English query"""
    query = "search for similar documents about pricing"
    result = intent_detector.detect(query)

    assert result.intent == Intent.VECTOR_SEARCH
    assert result.confidence >= 0.3
    assert result.mcp_tool == "qdrant"


@pytest.mark.unit
def test_detect_simple_query_intent(intent_detector):
    """Test detection of simple query intent"""
    query = "이게 뭐야?"
    result = intent_detector.detect(query)

    assert result.intent == Intent.SIMPLE_QUERY
    assert result.confidence >= 0.3
    assert result.mcp_tool == "ollama"


@pytest.mark.unit
def test_detect_simple_query_intent_explanation(intent_detector):
    """Test detection of simple explanation query"""
    query = "간단히 설명해줘"
    result = intent_detector.detect(query)

    assert result.intent == Intent.SIMPLE_QUERY
    assert result.mcp_tool == "ollama"


@pytest.mark.unit
def test_detect_complex_analysis_intent(intent_detector):
    """Test detection of complex analysis intent"""
    query = "이 시스템의 아키텍처를 분석해줘"
    result = intent_detector.detect(query)

    assert result.intent == Intent.COMPLEX_ANALYSIS
    assert result.confidence >= 0.3
    assert result.mcp_tool == "claude_haiku"


@pytest.mark.unit
def test_detect_complex_analysis_intent_why(intent_detector):
    """Test detection of complex analysis with 'why' question"""
    query = "왜 이 설계를 선택했나요?"
    result = intent_detector.detect(query)

    assert result.intent == Intent.COMPLEX_ANALYSIS
    assert result.mcp_tool == "claude_haiku"


@pytest.mark.unit
def test_confidence_scoring_accuracy(intent_detector):
    """Test that confidence scores are within valid range"""
    queries = [
        "파일을 읽어줘",
        "문서를 검색해줘",
        "이게 뭐야",
        "시스템 분석해줘",
        "random text with no clear intent"
    ]

    for query in queries:
        result = intent_detector.detect(query)
        assert 0.0 <= result.confidence <= 1.0, f"Confidence out of range for: {query}"


@pytest.mark.unit
def test_mcp_tool_selection(intent_detector):
    """Test that correct MCP tools are selected for different intents"""
    test_cases = [
        ("파일 목록 보여줘", "filesystem"),
        ("문서 검색", "qdrant"),
        ("간단히 설명", "ollama"),
        ("아키텍처 분석", "claude_haiku"),
    ]

    for query, expected_tool in test_cases:
        result = intent_detector.detect(query)
        assert result.mcp_tool == expected_tool, f"Wrong tool for query: {query}"


@pytest.mark.unit
def test_parameter_extraction(intent_detector):
    """Test parameter extraction from queries"""
    query = "프로젝트 폴더의 파일을 읽어줘"
    result = intent_detector.detect(query)

    assert isinstance(result.params, dict)


@pytest.mark.unit
def test_edge_case_empty_query(intent_detector):
    """Test handling of empty query"""
    result = intent_detector.detect("")

    assert result.intent == Intent.UNKNOWN
    assert result.mcp_tool is None
    assert "ollama" in result.fallback_tools or "claude_haiku" in result.fallback_tools


@pytest.mark.unit
def test_edge_case_very_long_query(intent_detector):
    """Test handling of very long queries"""
    long_query = "파일을 읽어줘 " * 100  # 100 repetitions
    result = intent_detector.detect(long_query)

    assert result.intent == Intent.FILE_OPERATION
    assert result.confidence >= 0.3


@pytest.mark.unit
def test_korean_query_handling(intent_detector):
    """Test proper handling of Korean language queries"""
    korean_queries = [
        "폴더 보여줘",
        "문서 찾아줘",
        "이거 뭐야",
        "왜 그래?"
    ]

    for query in korean_queries:
        result = intent_detector.detect(query)
        assert result.intent != Intent.UNKNOWN, f"Failed to detect Korean query: {query}"


@pytest.mark.unit
def test_multilingual_support(intent_detector):
    """Test handling of mixed language queries"""
    query = "show me 파일 in the folder"
    result = intent_detector.detect(query)

    assert result.intent == Intent.FILE_OPERATION
    assert result.mcp_tool == "filesystem"


@pytest.mark.unit
def test_special_characters_handling(intent_detector):
    """Test handling of special characters in queries"""
    query = "파일 읽어줘!!! @#$%"
    result = intent_detector.detect(query)

    assert result.intent == Intent.FILE_OPERATION
    assert result.confidence > 0


@pytest.mark.unit
def test_intent_fallback_behavior(intent_detector):
    """Test fallback tool selection for unknown intents"""
    query = "completely random nonsense text xyz123"
    result = intent_detector.detect(query)

    if result.confidence < 0.3:
        assert result.intent == Intent.UNKNOWN
        assert result.mcp_tool is None
        assert len(result.fallback_tools) > 0


@pytest.mark.unit
def test_tool_routing_decision_tree(intent_detector):
    """Test that routing decisions follow expected decision tree"""
    # File operation should route to filesystem
    file_result = intent_detector.detect("파일 보여줘")
    assert file_result.mcp_tool == "filesystem"

    # Vector search should route to qdrant
    search_result = intent_detector.detect("문서 검색")
    assert search_result.mcp_tool == "qdrant"

    # Simple query should route to ollama
    simple_result = intent_detector.detect("이게 뭐야")
    assert simple_result.mcp_tool == "ollama"

    # Complex analysis should route to claude_haiku
    complex_result = intent_detector.detect("아키텍처 분석")
    assert complex_result.mcp_tool == "claude_haiku"


@pytest.mark.unit
def test_result_serialization(intent_detector):
    """Test that IntentResult can be properly serialized"""
    query = "파일 읽어줘"
    result = intent_detector.detect(query)

    # Verify all required fields are present
    assert hasattr(result, 'intent')
    assert hasattr(result, 'confidence')
    assert hasattr(result, 'mcp_tool')
    assert hasattr(result, 'fallback_tools')
    assert hasattr(result, 'params')

    # Verify types
    assert isinstance(result.intent, Intent)
    assert isinstance(result.confidence, float)
    assert isinstance(result.fallback_tools, list)
    assert isinstance(result.params, dict)
