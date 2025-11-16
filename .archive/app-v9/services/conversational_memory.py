"""
Conversational Memory System (v6.0.0)
======================================

Multi-turn conversation management with context-aware search.

Features:
1. Conversation History: Store and retrieve conversation turns
2. Context Window Management: Fit conversations within LLM limits
3. Conversation Summarization: Compress long conversations
4. History-aware Search: Use conversation context for better retrieval
5. Session Management: Manage multiple concurrent conversations

Storage:
- Redis: In-memory conversation cache (fast access)
- PostgreSQL: Persistent conversation history (long-term storage)

Version: v6.0.0
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis

logger = logging.getLogger(__name__)


# ============================================================================
# Conversation Models
# ============================================================================


class ConversationTurn:
    """Single conversation turn (user message + assistant response)"""

    def __init__(
        self,
        turn_id: str,
        user_message: str,
        assistant_response: str,
        query: Optional[str] = None,
        sources: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.turn_id = turn_id
        self.user_message = user_message
        self.assistant_response = assistant_response
        self.query = query or user_message
        self.sources = sources or []
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "turn_id": self.turn_id,
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "query": self.query,
            "sources": self.sources,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTurn":
        """Create from dictionary"""
        return cls(
            turn_id=data["turn_id"],
            user_message=data["user_message"],
            assistant_response=data["assistant_response"],
            query=data.get("query"),
            sources=data.get("sources"),
            metadata=data.get("metadata"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class Conversation:
    """Multi-turn conversation"""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        turns: Optional[List[ConversationTurn]] = None,
        metadata: Optional[Dict] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.turns = turns or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def add_turn(self, turn: ConversationTurn):
        """Add conversation turn"""
        self.turns.append(turn)
        self.updated_at = datetime.now()

    def get_recent_turns(self, num_turns: int = 5) -> List[ConversationTurn]:
        """Get recent conversation turns"""
        return self.turns[-num_turns:]

    def get_context_window(self, max_tokens: int = 2000) -> List[ConversationTurn]:
        """
        Get conversation turns that fit within token budget

        Args:
            max_tokens: Maximum tokens in context window

        Returns:
            List of turns that fit in window
        """
        # Estimate tokens (rough: 4 chars = 1 token)
        budget = max_tokens
        selected_turns = []

        # Add turns from most recent
        for turn in reversed(self.turns):
            turn_text = turn.user_message + turn.assistant_response
            turn_tokens = len(turn_text) // 4

            if turn_tokens <= budget:
                selected_turns.insert(0, turn)
                budget -= turn_tokens
            else:
                break

        return selected_turns

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "turns": [turn.to_dict() for turn in self.turns],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create from dictionary"""
        turns = [ConversationTurn.from_dict(t) for t in data.get("turns", [])]
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            turns=turns,
            metadata=data.get("metadata"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


# ============================================================================
# Conversation Manager
# ============================================================================


class ConversationManager:
    """
    Manage conversations with Redis and PostgreSQL storage

    Features:
    - Store conversations in Redis (cache)
    - Persist to PostgreSQL (long-term)
    - Automatic expiration (TTL)
    - Session management
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        ttl_hours: int = 24,
    ):
        """
        Initialize conversation manager

        Args:
            redis_client: Redis client for caching
            ttl_hours: Time-to-live for conversations (hours)
        """
        self.redis_client = redis_client
        self.ttl_seconds = ttl_hours * 3600
        logger.info(f"ConversationManager initialized (TTL={ttl_hours}h)")

    def create_conversation(self, user_id: str, metadata: Optional[Dict] = None) -> Conversation:
        """
        Create new conversation

        Args:
            user_id: User ID
            metadata: Optional metadata

        Returns:
            New conversation
        """
        session_id = str(uuid.uuid4())
        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )

        self._save_to_redis(conversation)
        logger.info(f"Created conversation: {session_id}")
        return conversation

    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """
        Get conversation by session ID

        Args:
            session_id: Session ID

        Returns:
            Conversation or None if not found
        """
        # Try Redis first
        conversation = self._load_from_redis(session_id)

        if conversation:
            logger.debug(f"Loaded conversation from Redis: {session_id}")
        else:
            logger.debug(f"Conversation not found: {session_id}")

        return conversation

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        query: Optional[str] = None,
        sources: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[ConversationTurn]:
        """
        Add turn to conversation

        Args:
            session_id: Session ID
            user_message: User's message
            assistant_response: Assistant's response
            query: Actual search query (if different from message)
            sources: Retrieved sources
            metadata: Optional metadata

        Returns:
            Created turn or None if conversation not found
        """
        conversation = self.get_conversation(session_id)
        if not conversation:
            logger.warning(f"Conversation not found: {session_id}")
            return None

        # Create turn
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            user_message=user_message,
            assistant_response=assistant_response,
            query=query,
            sources=sources,
            metadata=metadata,
        )

        # Add to conversation
        conversation.add_turn(turn)

        # Save
        self._save_to_redis(conversation)

        logger.info(f"Added turn to conversation: {session_id}")
        return turn

    def get_context(
        self, session_id: str, num_turns: int = 5, max_tokens: int = 2000
    ) -> List[ConversationTurn]:
        """
        Get conversation context for new turn

        Args:
            session_id: Session ID
            num_turns: Number of recent turns to retrieve
            max_tokens: Maximum tokens in context

        Returns:
            List of context turns
        """
        conversation = self.get_conversation(session_id)
        if not conversation:
            return []

        # Get turns within token budget
        context_turns = conversation.get_context_window(max_tokens)

        # Limit to num_turns
        if len(context_turns) > num_turns:
            context_turns = context_turns[-num_turns:]

        logger.debug(f"Retrieved {len(context_turns)} context turns")
        return context_turns

    def delete_conversation(self, session_id: str):
        """Delete conversation"""
        if self.redis_client:
            key = self._get_redis_key(session_id)
            self.redis_client.delete(key)
            logger.info(f"Deleted conversation: {session_id}")

    def _save_to_redis(self, conversation: Conversation):
        """Save conversation to Redis"""
        if not self.redis_client:
            return

        key = self._get_redis_key(conversation.session_id)
        data = json.dumps(conversation.to_dict())
        self.redis_client.setex(key, self.ttl_seconds, data)

    def _load_from_redis(self, session_id: str) -> Optional[Conversation]:
        """Load conversation from Redis"""
        if not self.redis_client:
            return None

        key = self._get_redis_key(session_id)
        data = self.redis_client.get(key)

        if data:
            return Conversation.from_dict(json.loads(data))
        return None

    def _get_redis_key(self, session_id: str) -> str:
        """Get Redis key for conversation"""
        return f"conversation:{session_id}"


# ============================================================================
# Conversation Summarizer
# ============================================================================


class ConversationSummarizer:
    """
    Summarize long conversations to fit context window

    Techniques:
    - Progressive summarization
    - Key entity extraction
    - Topic tracking
    """

    def __init__(self):
        """Initialize summarizer"""
        logger.info("ConversationSummarizer initialized")

    def summarize(self, turns: List[ConversationTurn], max_length: int = 500) -> str:
        """
        Summarize conversation turns

        Args:
            turns: Conversation turns to summarize
            max_length: Maximum summary length (characters)

        Returns:
            Summary text
        """
        if not turns:
            return ""

        # Extract key points from each turn
        key_points = []
        for turn in turns:
            # Extract entities (simple keyword extraction)
            keywords = self._extract_keywords(turn.user_message)
            if keywords:
                key_points.append(f"User asked about: {', '.join(keywords)}")

        # Build summary
        summary = " ".join(key_points)

        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        logger.debug(f"Summarized {len(turns)} turns into {len(summary)} chars")
        return summary

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text

        Simple implementation - can be enhanced with NER/keyword extraction
        """
        # Remove common words
        stopwords = {"이", "그", "저", "것", "수", "등", "및", "a", "the", "is", "are"}

        words = text.split()
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]

        # Return top 3 keywords
        return keywords[:3]


# ============================================================================
# History-Aware Search
# ============================================================================


class HistoryAwareSearcher:
    """
    Search with conversation context

    Features:
    - Query reformulation with context
    - Entity resolution
    - Coreference resolution
    """

    def __init__(self, conversation_manager: ConversationManager):
        """
        Initialize history-aware searcher

        Args:
            conversation_manager: Conversation manager
        """
        self.conversation_manager = conversation_manager
        logger.info("HistoryAwareSearcher initialized")

    def reformulate_query(self, session_id: str, query: str, num_context_turns: int = 3) -> str:
        """
        Reformulate query using conversation context

        Args:
            session_id: Session ID
            query: Current query
            num_context_turns: Number of context turns to use

        Returns:
            Reformulated query
        """
        # Get conversation context
        context_turns = self.conversation_manager.get_context(session_id, num_turns=num_context_turns)

        if not context_turns:
            return query

        # Extract entities from context
        context_entities = []
        for turn in context_turns:
            entities = self._extract_entities(turn.user_message)
            context_entities.extend(entities)

        # Resolve coreferences in query
        reformulated = self._resolve_coreferences(query, context_entities)

        logger.info(f"Reformulated query: '{query}' → '{reformulated}'")
        return reformulated

    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract named entities from text

        Simple implementation - can be enhanced with NER
        """
        # Look for product-related entities
        entities = []

        # Materials
        materials = ["PET", "PP", "PE", "PS", "PVC"]
        for material in materials:
            if material in text.upper():
                entities.append(material)

        # Capacities
        import re
        capacity_match = re.search(r"(\d+)\s*(ml|cc|L)", text, re.IGNORECASE)
        if capacity_match:
            entities.append(capacity_match.group(0))

        return entities

    def _resolve_coreferences(self, query: str, context_entities: List[str]) -> str:
        """
        Resolve coreferences in query using context

        Args:
            query: Query with possible coreferences
            context_entities: Entities from context

        Returns:
            Query with coreferences resolved
        """
        # Simple pronoun resolution
        pronouns = ["그것", "이것", "저것", "같은", "그런"]

        reformulated = query
        for pronoun in pronouns:
            if pronoun in reformulated and context_entities:
                # Replace with most recent entity
                reformulated = reformulated.replace(pronoun, context_entities[-1])

        return reformulated


# ============================================================================
# Singleton Instances
# ============================================================================

_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager(redis_client: Optional[redis.Redis] = None) -> ConversationManager:
    """Get or create conversation manager singleton"""
    global _conversation_manager

    if _conversation_manager is None:
        _conversation_manager = ConversationManager(redis_client=redis_client)

    return _conversation_manager


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Create conversation
    manager = ConversationManager()
    conversation = manager.create_conversation(user_id="user-123")

    # Add turns
    manager.add_turn(
        session_id=conversation.session_id,
        user_message="50ml PET 용기를 찾고 있습니다",
        assistant_response="50ml PET 용기 제품을 찾았습니다. 10개의 결과가 있습니다.",
    )

    manager.add_turn(
        session_id=conversation.session_id,
        user_message="그것의 가격은 얼마인가요?",
        assistant_response="MOQ 1000개 기준으로 개당 150원입니다.",
    )

    # Get context
    context = manager.get_context(conversation.session_id, num_turns=2)
    print(f"Context: {len(context)} turns")

    # History-aware search
    searcher = HistoryAwareSearcher(manager)
    reformulated = searcher.reformulate_query(conversation.session_id, "그것의 색상 옵션은?")
    print(f"Reformulated: {reformulated}")
