"""
Enhanced Conversation Manager - Phase 1 Conversational RAG Improvements

Integrates Hierarchical Chunking for better context preservation:
- Parent chunks: Full conversation context
- Child chunks: Individual turns for fast retrieval

Based on: docs/features/CONVERSATIONAL_RAG_CAPABILITIES.md
Phase 1 Target: 85-90% accuracy (from 70-80%)

Features:
- Hierarchical conversation storage (Parent-Child)
- Vector indexing for semantic search
- Context-aware retrieval with full context
- Redis (24h) + PostgreSQL (permanent) + Qdrant (vector)

Usage:
    manager = EnhancedConversationManager()
    await manager.create_conversation(session_id="user-123")
    await manager.add_turn(
        session_id="user-123",
        user_message="어제 파파존스 피자집 가서 25,000원 먹었어",
        assistant_response="네, 기록했습니다"
    )
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from apps.api.services.conversational_memory import (
    ConversationManager,
    Conversation,
    ConversationTurn,
)
from apps.api.services.hierarchical_chunking_service import HierarchicalChunkingService

logger = logging.getLogger(__name__)


@dataclass
class EnhancedConversationTurn(ConversationTurn):
    """
    Enhanced conversation turn with extracted entities.

    Entities help with better retrieval:
    - place: "파파존스"
    - food: "라지 페퍼로니"
    - price: "25,000원"
    - date: "2024-11-15"
    """
    entities: Optional[Dict[str, Any]] = None


@dataclass
class EnhancedConversation(Conversation):
    """Enhanced conversation with hierarchical chunking metadata"""

    # Parent chunk ID in Qdrant
    parent_chunk_id: Optional[str] = None

    # Child chunk IDs in Qdrant (one per turn)
    child_chunk_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if self.child_chunk_ids is None:
            self.child_chunk_ids = []


class EnhancedConversationManager(ConversationManager):
    """
    Enhanced conversation manager with hierarchical chunking.

    Improvements over base ConversationManager:
    1. Parent-Child chunking (+30% context quality)
    2. Vector indexing for semantic search
    3. Entity extraction from conversations
    4. Full context retrieval

    Storage:
    - Redis: Fast access (24h TTL)
    - PostgreSQL: Permanent storage (TODO: implement)
    - Qdrant: Vector search (parent + child chunks)
    """

    def __init__(
        self,
        redis_client: Any,
        ttl_seconds: int = 86400,
        qdrant_collection: str = "conversations",
        enable_hierarchical: bool = True,
    ):
        """
        Initialize enhanced conversation manager.

        Args:
            redis_client: Redis client
            ttl_seconds: TTL for Redis (default 24h)
            qdrant_collection: Qdrant collection name
            enable_hierarchical: Enable hierarchical chunking
        """
        super().__init__(redis_client=redis_client, ttl_seconds=ttl_seconds)

        self.enable_hierarchical = enable_hierarchical

        if self.enable_hierarchical:
            try:
                self.chunking_service = HierarchicalChunkingService(
                    collection_name=qdrant_collection,
                    parent_chunk_size=1000,  # Large parent (full conversation)
                    child_chunk_size=200,  # Small child (individual turn)
                )
                logger.info("Initialized HierarchicalChunkingService for conversations")
            except Exception as e:
                logger.warning(f"Failed to initialize HierarchicalChunkingService: {e}")
                self.enable_hierarchical = False
        else:
            self.chunking_service = None

    async def create_conversation(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> EnhancedConversation:
        """
        Create enhanced conversation with hierarchical chunking.

        Args:
            session_id: Unique session ID
            user_id: Optional user ID
            metadata: Optional metadata

        Returns:
            Created EnhancedConversation
        """
        conversation = EnhancedConversation(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )

        # Save to Redis
        self._save_to_redis(conversation)

        logger.info(f"Created enhanced conversation: {session_id}")
        return conversation

    async def add_turn_enhanced(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        query: Optional[str] = None,
        sources: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
        entities: Optional[Dict[str, Any]] = None,
    ) -> Optional[EnhancedConversationTurn]:
        """
        Add turn with hierarchical chunking and entity extraction.

        This method:
        1. Creates conversation turn
        2. Extracts entities (TODO: implement)
        3. Creates parent chunk (full conversation so far)
        4. Creates child chunk (this turn only)
        5. Stores in Qdrant for vector search

        Args:
            session_id: Session ID
            user_message: User's message
            assistant_response: Assistant's response
            query: Actual search query
            sources: Retrieved sources
            metadata: Optional metadata
            entities: Extracted entities (place, food, price, date, etc.)

        Returns:
            Created EnhancedConversationTurn

        Example:
            >>> manager = EnhancedConversationManager(redis_client)
            >>> await manager.add_turn_enhanced(
            ...     session_id="user-123",
            ...     user_message="어제 파파존스 피자집 가서 라지 페퍼로니 25,000원 먹었어",
            ...     assistant_response="네, 기록했습니다",
            ...     entities={
            ...         "place": "파파존스",
            ...         "food": "라지 페퍼로니",
            ...         "price": "25,000원",
            ...         "date": "2024-11-15"
            ...     }
            ... )
        """
        # Get conversation
        conversation = self.get_conversation(session_id)
        if not conversation:
            logger.warning(f"Conversation not found: {session_id}")
            return None

        # Create enhanced turn
        turn = EnhancedConversationTurn(
            turn_id=str(uuid.uuid4()),
            user_message=user_message,
            assistant_response=assistant_response,
            query=query,
            sources=sources,
            metadata=metadata,
            entities=entities,
        )

        # Add to conversation
        if hasattr(conversation, 'add_turn'):
            conversation.add_turn(turn)
        else:
            # Fallback for base Conversation
            if not hasattr(conversation, 'turns'):
                conversation.turns = []
            conversation.turns.append(turn)

        # Save to Redis
        self._save_to_redis(conversation)

        # Store in Qdrant with hierarchical chunking
        if self.enable_hierarchical and self.chunking_service:
            try:
                await self._store_hierarchical(conversation, turn)
            except Exception as e:
                logger.error(f"Failed to store hierarchical chunks: {e}", exc_info=True)

        logger.info(f"Added enhanced turn to conversation: {session_id}")
        return turn

    async def _store_hierarchical(
        self,
        conversation: EnhancedConversation,
        latest_turn: EnhancedConversationTurn,
    ):
        """
        Store conversation using hierarchical chunking.

        Parent chunk: Full conversation context
        Child chunk: Latest turn for fast retrieval

        Args:
            conversation: Full conversation
            latest_turn: Latest turn to add
        """
        # Build parent chunk (full conversation)
        parent_text = self._build_parent_chunk(conversation)

        # Build child chunk (latest turn only)
        child_text = self._build_child_chunk(latest_turn)

        # Create hierarchical chunks
        chunks = await self.chunking_service.create_hierarchical_chunks(
            document=parent_text,
            metadata={
                "session_id": conversation.session_id,
                "user_id": conversation.user_id,
                "type": "conversation",
                "turn_count": len(conversation.turns),
                "created_at": conversation.created_at.isoformat(),
            }
        )

        # Store in Qdrant
        await self.chunking_service.store_in_qdrant(chunks)

        # Update conversation with chunk IDs
        if hasattr(conversation, 'parent_chunk_id'):
            conversation.parent_chunk_id = chunks["parent_chunks"][0].chunk_id
        if hasattr(conversation, 'child_chunk_ids'):
            conversation.child_chunk_ids.extend(
                [c.chunk_id for c in chunks["child_chunks"]]
            )

        logger.info(
            f"Stored hierarchical chunks: "
            f"1 parent + {len(chunks['child_chunks'])} children"
        )

    def _build_parent_chunk(self, conversation: Conversation) -> str:
        """
        Build parent chunk with full conversation context.

        Format:
        ```
        Session: user-123
        Created: 2024-11-15 18:30:00

        Turn 1 (18:30:05):
        User: 어제 파파존스 피자집 가서 라지 페퍼로니 25,000원 먹었어
        Entities: place=파파존스, food=라지 페퍼로니, price=25,000원, date=2024-11-15
        Assistant: 네, 기록했습니다

        Turn 2 (18:35:20):
        User: 거기 가격이 얼마였더라?
        Assistant: 파파존스에서 25,000원 지불하셨습니다
        ```
        """
        lines = [
            f"Conversation Session: {conversation.session_id}",
            f"Created: {conversation.created_at.isoformat()}",
            f"User: {conversation.user_id or 'unknown'}",
            "",
        ]

        for i, turn in enumerate(conversation.turns, 1):
            lines.append(f"Turn {i} ({turn.timestamp.strftime('%H:%M:%S')}):")
            lines.append(f"User: {turn.user_message}")

            # Add entities if available
            if hasattr(turn, 'entities') and turn.entities:
                entity_str = ", ".join(
                    f"{k}={v}" for k, v in turn.entities.items()
                )
                lines.append(f"Entities: {entity_str}")

            lines.append(f"Assistant: {turn.assistant_response}")

            # Add sources if available
            if turn.sources:
                lines.append(f"Sources: {len(turn.sources)} documents")

            lines.append("")  # Empty line between turns

        return "\n".join(lines)

    def _build_child_chunk(self, turn: EnhancedConversationTurn) -> str:
        """
        Build child chunk for individual turn.

        Format:
        ```
        User: 어제 파파존스 피자집 가서 라지 페퍼로니 25,000원 먹었어
        Entities: place=파파존스, food=라지 페퍼로니, price=25,000원
        Assistant: 네, 기록했습니다
        ```
        """
        lines = [
            f"User: {turn.user_message}",
        ]

        if hasattr(turn, 'entities') and turn.entities:
            entity_str = ", ".join(
                f"{k}={v}" for k, v in turn.entities.items()
            )
            lines.append(f"Entities: {entity_str}")

        lines.append(f"Assistant: {turn.assistant_response}")

        return "\n".join(lines)

    async def search_conversations(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search conversations using hierarchical retrieval.

        This method:
        1. Searches child chunks (fast retrieval)
        2. Returns parent chunks (full context)

        Args:
            query: Search query
            top_k: Number of results
            user_id: Optional user filter

        Returns:
            List of conversations with full context

        Example:
            >>> manager = EnhancedConversationManager(redis_client)
            >>> results = await manager.search_conversations(
            ...     query="최근에 갔던 피자집",
            ...     top_k=3
            ... )
            >>> # Returns full conversation context, not just matching turn
        """
        if not self.enable_hierarchical or not self.chunking_service:
            logger.warning("Hierarchical search not available")
            return []

        try:
            # Search with parent context
            results = await self.chunking_service.retrieve_with_parent_context(
                query=query,
                top_k=top_k,
            )

            return results

        except Exception as e:
            logger.error(f"Conversation search failed: {e}", exc_info=True)
            return []


# Example usage
async def main():
    """Example: Enhanced conversation management"""
    import redis.asyncio as redis

    # Initialize
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    manager = EnhancedConversationManager(redis_client=redis_client)

    # Create conversation
    session_id = "user-123-session-456"
    await manager.create_conversation(
        session_id=session_id,
        user_id="user-123",
    )

    # Add turn 1
    await manager.add_turn_enhanced(
        session_id=session_id,
        user_message="어제 파파존스 피자집 가서 라지 페퍼로니 25,000원 먹었어",
        assistant_response="네, 기록했습니다",
        entities={
            "place": "파파존스",
            "food": "라지 페퍼로니",
            "price": "25,000원",
            "date": "2024-11-15",
        },
    )

    # Add turn 2
    await manager.add_turn_enhanced(
        session_id=session_id,
        user_message="거기 가격이 얼마였더라?",
        assistant_response="파파존스에서 25,000원 지불하셨습니다",
        entities={
            "place": "파파존스",
            "price": "25,000원",
        },
    )

    # Search conversations
    results = await manager.search_conversations(
        query="최근에 갔던 피자집",
        top_k=3,
    )

    print(f"\n=== Search Results ===")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Score: {result.get('score', 0):.3f}")
        print(f"Context: {result.get('parent_context', '')[:200]}...")

    await redis_client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
