"""
Context Store - Redis-backed Session Persistence

Provides production-ready session storage and retrieval using Redis
with automatic serialization and TTL management.

Features:
- Redis-backed persistence
- Automatic JSON serialization
- TTL-based session expiration
- Error handling and logging

Usage:
    store = ContextStore(redis_client=redis_client)
    await store.save_context(session_id, context)
    context = await store.get_context(session_id)
"""

import logging
from typing import Optional

from redis.asyncio import Redis

from apps.api.rag_consultation.models import ConversationContext

logger = logging.getLogger(__name__)


class ContextStore:
    """Redis-backed conversation context storage.

    Provides persistent storage for conversation contexts with
    automatic serialization and TTL management.

    Attributes:
        redis_client: Redis async client
        ttl: Session TTL in seconds (default: 24 hours)
        key_prefix: Redis key prefix for namespacing
    """

    def __init__(
        self,
        redis_client: Redis,
        ttl: int = 86400,  # 24 hours
        key_prefix: str = "consultation:context:",
    ) -> None:
        """Initialize context store.

        Args:
            redis_client: Redis async client instance
            ttl: Session TTL in seconds
            key_prefix: Redis key prefix
        """
        self.redis_client = redis_client
        self.ttl = ttl
        self.key_prefix = key_prefix
        logger.info(f"Context store initialized with TTL={ttl}s, prefix={key_prefix}")

    def _get_key(self, session_id: str) -> str:
        """Generate Redis key for session.

        Args:
            session_id: Session identifier

        Returns:
            Redis key string
        """
        return f"{self.key_prefix}{session_id}"

    async def save_context(
        self,
        session_id: str,
        context: ConversationContext,
    ) -> bool:
        """Save conversation context to Redis.

        Args:
            session_id: Session identifier
            context: Conversation context to save

        Returns:
            True if saved successfully, False otherwise

        Raises:
            ValueError: If session_id is empty
        """
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")

        try:
            key = self._get_key(session_id)
            serialized = context.model_dump_json()

            await self.redis_client.setex(key, self.ttl, serialized)

            logger.info(f"Saved context for session {session_id} " f"({len(context.turns)} turns)")
            return True

        except Exception as e:
            logger.error(f"Failed to save context for session {session_id}: {e}")
            return False

    async def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Retrieve conversation context from Redis.

        Args:
            session_id: Session identifier

        Returns:
            ConversationContext if found, None otherwise

        Raises:
            ValueError: If session_id is empty
        """
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")

        try:
            key = self._get_key(session_id)
            serialized = await self.redis_client.get(key)

            if not serialized:
                logger.debug(f"No context found for session {session_id}")
                return None

            context = ConversationContext.model_validate_json(serialized)

            logger.info(
                f"Retrieved context for session {session_id} " f"({len(context.turns)} turns)"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to retrieve context for session {session_id}: {e}")
            return None

    async def delete_context(self, session_id: str) -> bool:
        """Delete conversation context from Redis.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted successfully, False otherwise

        Raises:
            ValueError: If session_id is empty
        """
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")

        try:
            key = self._get_key(session_id)
            deleted = await self.redis_client.delete(key)

            if deleted:
                logger.info(f"Deleted context for session {session_id}")
            else:
                logger.debug(f"No context to delete for session {session_id}")

            return bool(deleted)

        except Exception as e:
            logger.error(f"Failed to delete context for session {session_id}: {e}")
            return False

    async def extend_ttl(self, session_id: str, additional_seconds: int = None) -> bool:
        """Extend session TTL.

        Args:
            session_id: Session identifier
            additional_seconds: Additional seconds to add (default: reset to full TTL)

        Returns:
            True if TTL extended successfully, False otherwise

        Raises:
            ValueError: If session_id is empty
        """
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")

        try:
            key = self._get_key(session_id)

            if additional_seconds is None:
                # Reset to full TTL
                await self.redis_client.expire(key, self.ttl)
            else:
                # Add additional time
                current_ttl = await self.redis_client.ttl(key)
                if current_ttl > 0:
                    new_ttl = current_ttl + additional_seconds
                    await self.redis_client.expire(key, new_ttl)

            logger.debug(f"Extended TTL for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to extend TTL for session {session_id}: {e}")
            return False

    async def session_exists(self, session_id: str) -> bool:
        """Check if session exists in Redis.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists, False otherwise

        Raises:
            ValueError: If session_id is empty
        """
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")

        try:
            key = self._get_key(session_id)
            exists = await self.redis_client.exists(key)
            return bool(exists)

        except Exception as e:
            logger.error(f"Failed to check session existence for {session_id}: {e}")
            return False
