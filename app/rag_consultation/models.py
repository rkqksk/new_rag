"""
Core Data Models for RAG Consultation System

Provides Pydantic models for type-safe data handling across the consultation pipeline.

Models:
- QueryAnalysis: Complete query classification results
- IntentDetection: Multi-label intent detection
- ToneAnalysis: Formality and urgency analysis
- ConversationContext: Multi-turn conversation tracking
- RetrievalStrategy: Retrieval optimization configuration
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class QueryType(str, Enum):
    """Query type classification categories."""
    FACTUAL = "factual"  # "What is X?", "How does Y work?"
    PROCEDURAL = "procedural"  # "How to do X?", "Steps for Y?"
    COMPARISON = "comparison"  # "X vs Y", "Difference between A and B"
    TROUBLESHOOTING = "troubleshooting"  # "Error in X", "Problem with Y"
    RECOMMENDATION = "recommendation"  # "Best X for Y", "Suggest Z"
    EXPLORATORY = "exploratory"  # Open-ended research queries
    CONVERSATIONAL = "conversational"  # Follow-up, clarification


class Intent(str, Enum):
    """User intent categories (multi-label)."""
    INFORMATION_SEEKING = "information_seeking"
    PROBLEM_SOLVING = "problem_solving"
    DECISION_MAKING = "decision_making"
    LEARNING = "learning"
    VALIDATION = "validation"
    CLARIFICATION = "clarification"


class FormalityLevel(str, Enum):
    """Communication formality levels."""
    VERY_FORMAL = "very_formal"
    FORMAL = "formal"
    NEUTRAL = "neutral"
    CASUAL = "casual"
    VERY_CASUAL = "very_casual"


class UrgencyLevel(str, Enum):
    """Query urgency levels."""
    CRITICAL = "critical"  # Production down, immediate action needed
    HIGH = "high"  # Important, needs quick response
    MEDIUM = "medium"  # Standard priority
    LOW = "low"  # Informational, no time pressure


class ExpertiseLevel(str, Enum):
    """User expertise level inference."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class QueryAnalysis(BaseModel):
    """Complete query classification analysis results.

    Attributes:
        query: Original user query
        query_type: Primary query type classification
        query_type_scores: Confidence scores for all query types
        confidence: Overall classification confidence
        timestamp: Analysis timestamp
    """
    query: str = Field(..., min_length=1, description="Original user query")
    query_type: QueryType = Field(..., description="Primary query type")
    query_type_scores: Dict[QueryType, float] = Field(
        ...,
        description="Confidence scores for all query types"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall classification confidence"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analysis timestamp"
    )

    @field_validator("query_type_scores")
    @classmethod
    def validate_scores(cls, v: Dict[QueryType, float]) -> Dict[QueryType, float]:
        """Validate all scores are between 0 and 1."""
        for query_type, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"Score for {query_type} must be between 0 and 1, got {score}"
                )
        return v


class IntentDetection(BaseModel):
    """Multi-label intent detection results.

    Attributes:
        intents: Detected intents with confidence scores
        primary_intent: Highest confidence intent
        timestamp: Detection timestamp
    """
    intents: Dict[Intent, float] = Field(
        ...,
        description="Detected intents with confidence scores"
    )
    primary_intent: Intent = Field(..., description="Primary intent")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Detection timestamp"
    )

    @field_validator("intents")
    @classmethod
    def validate_intent_scores(cls, v: Dict[Intent, float]) -> Dict[Intent, float]:
        """Validate all intent scores are between 0 and 1."""
        for intent, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"Score for {intent} must be between 0 and 1, got {score}"
                )
        return v


class ToneAnalysis(BaseModel):
    """Tone and communication style analysis.

    Attributes:
        formality: Communication formality level
        urgency: Query urgency level
        expertise_level: Inferred user expertise
        formality_score: Formality confidence score
        urgency_markers: Detected urgency indicators
        timestamp: Analysis timestamp
    """
    formality: FormalityLevel = Field(..., description="Formality level")
    urgency: UrgencyLevel = Field(..., description="Urgency level")
    expertise_level: ExpertiseLevel = Field(..., description="User expertise")
    formality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Formality confidence"
    )
    urgency_markers: List[str] = Field(
        default_factory=list,
        description="Detected urgency keywords"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analysis timestamp"
    )


class ConversationTurn(BaseModel):
    """Single conversation turn.

    Attributes:
        query: User query
        response: System response
        query_analysis: Query classification
        intent: Intent detection
        tone: Tone analysis
        timestamp: Turn timestamp
    """
    query: str = Field(..., min_length=1, description="User query")
    response: Optional[str] = Field(None, description="System response")
    query_analysis: Optional[QueryAnalysis] = Field(
        None,
        description="Query classification"
    )
    intent: Optional[IntentDetection] = Field(None, description="Intent detection")
    tone: Optional[ToneAnalysis] = Field(None, description="Tone analysis")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Turn timestamp"
    )


class ConversationContext(BaseModel):
    """Multi-turn conversation context.

    Attributes:
        session_id: Unique session identifier
        turns: Conversation history
        user_id: Optional user identifier
        metadata: Additional session metadata
        created_at: Session creation time
        updated_at: Last update time
    """
    session_id: str = Field(..., min_length=1, description="Session ID")
    turns: List[ConversationTurn] = Field(
        default_factory=list,
        description="Conversation history"
    )
    user_id: Optional[str] = Field(None, description="User identifier")
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Session metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )

    def add_turn(
        self,
        query: str,
        response: Optional[str] = None,
        query_analysis: Optional[QueryAnalysis] = None,
        intent: Optional[IntentDetection] = None,
        tone: Optional[ToneAnalysis] = None,
    ) -> None:
        """Add a new conversation turn.

        Args:
            query: User query
            response: System response
            query_analysis: Query classification results
            intent: Intent detection results
            tone: Tone analysis results
        """
        turn = ConversationTurn(
            query=query,
            response=response,
            query_analysis=query_analysis,
            intent=intent,
            tone=tone,
        )
        self.turns.append(turn)
        self.updated_at = datetime.utcnow()

    def get_recent_queries(self, n: int = 5) -> List[str]:
        """Get N most recent queries.

        Args:
            n: Number of recent queries to retrieve

        Returns:
            List of recent query strings
        """
        return [turn.query for turn in self.turns[-n:]]

    def get_conversation_summary(self) -> str:
        """Generate conversation summary.

        Returns:
            Summary of conversation topics
        """
        if not self.turns:
            return "No conversation history"

        queries = [turn.query for turn in self.turns]
        return f"{len(queries)} turns: " + "; ".join(queries[-3:])


class RetrievalStrategy(BaseModel):
    """Retrieval optimization strategy.

    Attributes:
        use_dense_retrieval: Enable dense vector retrieval
        use_sparse_retrieval: Enable sparse BM25 retrieval
        use_hybrid: Enable hybrid fusion
        rerank: Enable cross-encoder reranking
        top_k: Number of documents to retrieve
        expanded_queries: Query expansion variations
        filters: Metadata filters
        timestamp: Strategy creation time
    """
    use_dense_retrieval: bool = Field(
        default=True,
        description="Enable dense retrieval"
    )
    use_sparse_retrieval: bool = Field(
        default=True,
        description="Enable sparse retrieval"
    )
    use_hybrid: bool = Field(default=True, description="Enable hybrid fusion")
    rerank: bool = Field(default=True, description="Enable reranking")
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Documents to retrieve"
    )
    expanded_queries: List[str] = Field(
        default_factory=list,
        description="Query variations"
    )
    filters: Dict[str, str] = Field(
        default_factory=dict,
        description="Metadata filters"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Strategy timestamp"
    )


class ConsultationRequest(BaseModel):
    """API request for consultation endpoint.

    Attributes:
        query: User query
        session_id: Optional session ID for multi-turn
        user_id: Optional user identifier
        metadata: Additional request metadata
    """
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    session_id: Optional[str] = Field(None, description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Metadata")


class ConsultationResponse(BaseModel):
    """API response for consultation endpoint.

    Attributes:
        response: Generated response text
        session_id: Session identifier
        query_analysis: Query classification
        intent: Intent detection
        tone: Tone analysis
        retrieval_strategy: Retrieval configuration
        confidence: Overall response confidence
        timestamp: Response timestamp
    """
    response: str = Field(..., description="Generated response")
    session_id: str = Field(..., description="Session ID")
    query_analysis: QueryAnalysis = Field(..., description="Query classification")
    intent: IntentDetection = Field(..., description="Intent detection")
    tone: ToneAnalysis = Field(..., description="Tone analysis")
    retrieval_strategy: RetrievalStrategy = Field(
        ...,
        description="Retrieval strategy"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Response confidence"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
