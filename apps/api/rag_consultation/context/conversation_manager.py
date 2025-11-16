"""
Conversation Manager - Multi-turn Conversation Orchestration

Provides production-ready conversation management with session tracking,
context accumulation, and reference resolution.

Features:
- Session lifecycle management
- Context accumulation across turns
- Reference resolution (pronouns, "it", "that")
- Conversation summarization
- Integration with ContextStore

Usage:
    manager = ConversationManager(context_store=store)
    context = await manager.get_or_create_session(session_id)
    await manager.add_turn(session_id, query, response, analysis)
"""

import logging
import re
import uuid
from datetime import datetime
from typing import List, Optional

from apps.api.rag_consultation.context.context_store import ContextStore
from apps.api.rag_consultation.models import (
    ConversationContext,
    IntentDetection,
    QueryAnalysis,
    ToneAnalysis,
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """Multi-turn conversation manager with session tracking.

    Manages conversation sessions with context persistence,
    reference resolution, and conversation summarization.

    Attributes:
        context_store: ContextStore for persistence
        max_turns: Maximum turns to keep in memory
    """

    def __init__(
        self,
        context_store: ContextStore,
        max_turns: int = 50,
    ) -> None:
        """Initialize conversation manager.

        Args:
            context_store: ContextStore instance for persistence
            max_turns: Maximum conversation turns to maintain
        """
        self.context_store = context_store
        self.max_turns = max_turns
        logger.info(f"Conversation manager initialized (max_turns={max_turns})")

    def generate_session_id(self) -> str:
        """Generate unique session ID.

        Returns:
            UUID-based session identifier
        """
        return f"session_{uuid.uuid4().hex}"

    async def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ConversationContext:
        """Get existing session or create new one.

        Args:
            session_id: Optional existing session ID
            user_id: Optional user identifier

        Returns:
            ConversationContext (existing or new)
        """
        # Create new session if no ID provided
        if not session_id:
            session_id = self.generate_session_id()
            context = ConversationContext(
                session_id=session_id,
                user_id=user_id,
            )
            await self.context_store.save_context(session_id, context)
            logger.info(f"Created new session: {session_id}")
            return context

        # Try to retrieve existing session
        context = await self.context_store.get_context(session_id)

        if context:
            # Extend TTL on access
            await self.context_store.extend_ttl(session_id)
            logger.info(f"Retrieved existing session: {session_id}")
            return context

        # Create new session with provided ID
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
        )
        await self.context_store.save_context(session_id, context)
        logger.info(f"Created new session with provided ID: {session_id}")
        return context

    async def add_turn(
        self,
        session_id: str,
        query: str,
        response: Optional[str] = None,
        query_analysis: Optional[QueryAnalysis] = None,
        intent: Optional[IntentDetection] = None,
        tone: Optional[ToneAnalysis] = None,
    ) -> ConversationContext:
        """Add conversation turn to session.

        Args:
            session_id: Session identifier
            query: User query
            response: System response
            query_analysis: Query classification
            intent: Intent detection
            tone: Tone analysis

        Returns:
            Updated ConversationContext

        Raises:
            ValueError: If session not found
        """
        context = await self.context_store.get_context(session_id)

        if not context:
            raise ValueError(f"Session not found: {session_id}")

        # Add turn to context
        context.add_turn(
            query=query,
            response=response,
            query_analysis=query_analysis,
            intent=intent,
            tone=tone,
        )

        # Trim old turns if exceeding max
        if len(context.turns) > self.max_turns:
            removed_count = len(context.turns) - self.max_turns
            context.turns = context.turns[-self.max_turns :]
            logger.info(f"Trimmed {removed_count} old turns from session {session_id}")

        # Save updated context
        await self.context_store.save_context(session_id, context)

        logger.info(f"Added turn to session {session_id} " f"(total turns: {len(context.turns)})")

        return context

    def resolve_references(
        self,
        query: str,
        context: ConversationContext,
    ) -> str:
        """Resolve pronouns and references in query using conversation history.

        Args:
            query: Current query with potential references
            context: Conversation context

        Returns:
            Query with references resolved
        """
        if not context.turns or len(context.turns) < 2:
            # No history to resolve from
            return query

        # Get recent queries for context
        recent_queries = context.get_recent_queries(n=3)

        # Simple reference resolution patterns
        reference_patterns = [
            (r"\bit\b", "reference"),
            (r"\bthis\b", "reference"),
            (r"\bthat\b", "reference"),
            (r"\bthey\b", "reference"),
            (r"\bthose\b", "reference"),
        ]

        # Check if query contains references
        has_reference = any(
            re.search(pattern, query, re.IGNORECASE) for pattern, _ in reference_patterns
        )

        if not has_reference:
            return query

        # Add context from previous query
        previous_query = recent_queries[-2] if len(recent_queries) >= 2 else ""

        if previous_query:
            resolved = f"{previous_query}. {query}"
            logger.debug(f"Resolved references: '{query}' → '{resolved}'")
            return resolved

        return query

    async def get_conversation_summary(
        self,
        session_id: str,
        max_turns: int = 5,
    ) -> str:
        """Generate conversation summary for context.

        Args:
            session_id: Session identifier
            max_turns: Maximum turns to include

        Returns:
            Summary string

        Raises:
            ValueError: If session not found
        """
        context = await self.context_store.get_context(session_id)

        if not context:
            raise ValueError(f"Session not found: {session_id}")

        if not context.turns:
            return "No conversation history"

        # Get recent turns
        recent_turns = context.turns[-max_turns:]

        summary_parts = []
        for i, turn in enumerate(recent_turns, 1):
            summary_parts.append(f"Turn {i}: {turn.query}")

        summary = " | ".join(summary_parts)
        logger.debug(f"Generated summary for session {session_id}: {summary[:100]}...")

        return summary

    async def clear_session(self, session_id: str) -> bool:
        """Clear conversation session.

        Args:
            session_id: Session identifier

        Returns:
            True if cleared successfully
        """
        deleted = await self.context_store.delete_context(session_id)

        if deleted:
            logger.info(f"Cleared session: {session_id}")
        else:
            logger.warning(f"Failed to clear session: {session_id}")

        return deleted

    async def get_session_info(self, session_id: str) -> dict:
        """Get session metadata and statistics.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session information

        Raises:
            ValueError: If session not found
        """
        context = await self.context_store.get_context(session_id)

        if not context:
            raise ValueError(f"Session not found: {session_id}")

        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "turn_count": len(context.turns),
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "duration_minutes": ((context.updated_at - context.created_at).total_seconds() / 60),
            "summary": context.get_conversation_summary(),
        }
