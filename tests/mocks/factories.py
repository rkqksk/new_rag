"""Test data factories for consistent test data generation."""
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock


def create_mock_search_result(
    score: float = 0.9,
    text: str = "Sample text",
    doc_id: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create mock Qdrant search result.

    Args:
        score: Relevance score (0.0 to 1.0)
        text: Document text content
        doc_id: Document identifier
        metadata: Additional metadata

    Returns:
        Dictionary representing a Qdrant search result
    """
    if doc_id is None:
        doc_id = f"doc_{int(datetime.now().timestamp() * 1000)}"

    if metadata is None:
        metadata = {}

    return {
        "id": doc_id,
        "score": score,
        "payload": {
            "text": text,
            "metadata": metadata
        }
    }


def create_mock_qa_response(
    answer: str = "Mock answer",
    confidence: float = 0.85,
    citations: List[str] = None,
    sources: List[str] = None
) -> Dict[str, Any]:
    """
    Create mock QA response.

    Args:
        answer: Generated answer text
        confidence: Confidence score (0.0 to 1.0)
        citations: List of citation texts
        sources: List of source identifiers

    Returns:
        Dictionary representing a QA response
    """
    if citations is None:
        citations = []

    if sources is None:
        sources = []

    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
        "sources": sources
    }


def create_mock_embedding(dimension: int = 384) -> List[float]:
    """
    Create mock embedding vector.

    Args:
        dimension: Embedding dimension

    Returns:
        List of floats representing an embedding
    """
    return [0.1] * dimension


def create_mock_document(
    doc_id: str = None,
    text: str = "Sample document text",
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create mock document.

    Args:
        doc_id: Document identifier
        text: Document text content
        metadata: Document metadata

    Returns:
        Dictionary representing a document
    """
    if doc_id is None:
        doc_id = f"doc_{int(datetime.now().timestamp() * 1000)}"

    if metadata is None:
        metadata = {"source": "test"}

    return {
        "id": doc_id,
        "text": text,
        "metadata": metadata
    }


def create_mock_chunks(count: int = 3, chunk_size: int = 50) -> List[str]:
    """
    Create mock text chunks.

    Args:
        count: Number of chunks to create
        chunk_size: Approximate size of each chunk

    Returns:
        List of text chunks
    """
    return [
        f"This is chunk {i+1} with approximately {chunk_size} characters of content."
        for i in range(count)
    ]


def create_mock_complexity_score(
    score: float = 0.5,
    length_score: float = 0.3,
    technical_score: float = 0.5,
    reasoning_score: float = 0.6
) -> Dict[str, float]:
    """
    Create mock complexity score breakdown.

    Args:
        score: Overall complexity score
        length_score: Query length component
        technical_score: Technical terms component
        reasoning_score: Reasoning requirement component

    Returns:
        Dictionary with complexity score breakdown
    """
    return {
        "score": score,
        "length_score": length_score,
        "technical_score": technical_score,
        "reasoning_score": reasoning_score
    }


def create_mock_intent_result(
    intent_type: str = "vector_search",
    confidence: float = 0.9,
    mcp_tool: str = None,
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create mock intent detection result.

    Args:
        intent_type: Type of detected intent
        confidence: Detection confidence (0.0 to 1.0)
        mcp_tool: Selected MCP tool name
        parameters: Tool parameters

    Returns:
        Dictionary representing intent detection result
    """
    if parameters is None:
        parameters = {}

    return {
        "intent": intent_type,
        "confidence": confidence,
        "mcp_tool": mcp_tool,
        "parameters": parameters
    }
