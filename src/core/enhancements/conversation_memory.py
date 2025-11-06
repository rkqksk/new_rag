"""
Conversation Memory for Context-Aware Chat
Maintains conversation history and context
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single conversation message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary"""
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


@dataclass
class ConversationContext:
    """Extracted conversation context"""
    recent_products: List[str] = field(default_factory=list)
    recent_specifications: Dict[str, str] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    search_filters: Dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """
    Conversation Memory Manager

    Features:
    - Short-term memory (current session)
    - Long-term memory (Redis/database)
    - Context extraction
    - Conversation summarization
    """

    def __init__(
        self,
        max_history: int = 10,
        context_window: int = 3,
        redis_client: Optional[Any] = None
    ):
        """
        Initialize conversation memory

        Args:
            max_history: Maximum messages to keep in memory
            context_window: Number of recent messages for context
            redis_client: Optional Redis client for persistence
        """
        self.max_history = max_history
        self.context_window = context_window
        self.redis_client = redis_client

        # In-memory storage
        self.conversations: Dict[str, List[Message]] = {}

        logger.info(f"✅ Conversation memory initialized (max_history={max_history})")

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add message to conversation history

        Args:
            session_id: Unique session identifier
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (search results, etc.)
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        # Initialize conversation if needed
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        # Add message
        self.conversations[session_id].append(message)

        # Trim history if too long
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]

        # Persist to Redis if available
        if self.redis_client:
            self._persist_to_redis(session_id)

        logger.debug(f"Added {role} message to session {session_id}")

    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get conversation history

        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages

        Returns:
            List of messages
        """
        if session_id not in self.conversations:
            # Try to load from Redis
            if self.redis_client:
                self._load_from_redis(session_id)

        messages = self.conversations.get(session_id, [])

        if limit:
            return messages[-limit:]

        return messages

    def get_context(self, session_id: str) -> ConversationContext:
        """
        Extract context from recent conversation

        Args:
            session_id: Session identifier

        Returns:
            ConversationContext object
        """
        messages = self.get_history(session_id, limit=self.context_window)

        context = ConversationContext()

        # Extract context from messages
        for message in messages:
            if message.role == 'user':
                # Extract products mentioned
                products = self._extract_products(message.content)
                context.recent_products.extend(products)

                # Extract specifications
                specs = self._extract_specifications(message.content)
                context.recent_specifications.update(specs)

                # Extract filters
                filters = self._extract_filters(message.content)
                context.search_filters.update(filters)

            elif message.role == 'assistant':
                # Extract search results if available
                if 'search_results' in message.metadata:
                    results = message.metadata['search_results']
                    if results:
                        # Add top result as recent product
                        top_result = results[0]
                        if hasattr(top_result, 'product_id'):
                            context.recent_products.append(top_result.product_id)

        # Deduplicate
        context.recent_products = list(set(context.recent_products))[-5:]  # Keep last 5

        return context

    def get_context_summary(self, session_id: str) -> str:
        """
        Generate text summary of conversation context

        Args:
            session_id: Session identifier

        Returns:
            Context summary string
        """
        context = self.get_context(session_id)

        summary_parts = []

        if context.recent_products:
            summary_parts.append(f"Recent products: {', '.join(context.recent_products)}")

        if context.recent_specifications:
            specs = ', '.join([f"{k}: {v}" for k, v in context.recent_specifications.items()])
            summary_parts.append(f"Specifications: {specs}")

        if context.search_filters:
            filters = ', '.join([f"{k}: {v}" for k, v in context.search_filters.items()])
            summary_parts.append(f"Filters: {filters}")

        if not summary_parts:
            return "No context available"

        return " | ".join(summary_parts)

    def enhance_query_with_context(
        self,
        session_id: str,
        query: str
    ) -> str:
        """
        Enhance query with conversation context

        Args:
            session_id: Session identifier
            query: Original query

        Returns:
            Enhanced query with context
        """
        context = self.get_context(session_id)

        # Build context prefix
        context_parts = []

        if context.recent_specifications:
            # Add recent specs to query
            for key, value in list(context.recent_specifications.items())[-3:]:
                context_parts.append(f"{key}: {value}")

        if context.search_filters:
            # Add active filters
            for key, value in context.search_filters.items():
                if key not in context.recent_specifications:
                    context_parts.append(f"{key}: {value}")

        if context_parts:
            enhanced_query = f"{' '.join(context_parts)} {query}"
            logger.debug(f"Enhanced query: {query} → {enhanced_query}")
            return enhanced_query

        return query

    def clear_session(self, session_id: str):
        """Clear conversation history for session"""
        if session_id in self.conversations:
            del self.conversations[session_id]

        # Clear from Redis
        if self.redis_client:
            key = f"conversation:{session_id}"
            self.redis_client.delete(key)

        logger.info(f"Cleared session {session_id}")

    def get_all_sessions(self) -> List[str]:
        """Get list of all active session IDs"""
        return list(self.conversations.keys())

    def _extract_products(self, text: str) -> List[str]:
        """Extract product mentions from text"""
        import re

        # Pattern for product codes
        pattern = r'[A-Z]{2,}-\d{2,}'
        products = re.findall(pattern, text)

        return products

    def _extract_specifications(self, text: str) -> Dict[str, str]:
        """Extract specifications from text"""
        import re

        specs = {}

        # Capacity
        capacity_match = re.search(r'(\d+)\s*(ml|cc|L)', text, re.IGNORECASE)
        if capacity_match:
            specs['capacity'] = capacity_match.group(1) + capacity_match.group(2)

        # Neck size
        neck_match = re.search(r'(\d+)\s*(파이|mm)', text, re.IGNORECASE)
        if neck_match:
            specs['neck'] = neck_match.group(1) + neck_match.group(2)

        # Material
        materials = ['PET', 'PP', 'PE', 'HDPE', 'Glass']
        for material in materials:
            if material.lower() in text.lower():
                specs['material'] = material
                break

        return specs

    def _extract_filters(self, text: str) -> Dict[str, Any]:
        """Extract search filters from text"""
        filters = {}

        # MOQ
        if 'moq' in text.lower() or '최소' in text.lower():
            import re
            moq_match = re.search(r'(\d+)', text)
            if moq_match:
                filters['moq'] = int(moq_match.group(1))

        return filters

    def _persist_to_redis(self, session_id: str):
        """Persist conversation to Redis"""
        if not self.redis_client:
            return

        try:
            key = f"conversation:{session_id}"
            messages = self.conversations[session_id]

            # Serialize messages
            data = json.dumps([msg.to_dict() for msg in messages])

            # Store with expiry (24 hours)
            self.redis_client.setex(key, 86400, data)

        except Exception as e:
            logger.error(f"Failed to persist to Redis: {e}")

    def _load_from_redis(self, session_id: str):
        """Load conversation from Redis"""
        if not self.redis_client:
            return

        try:
            key = f"conversation:{session_id}"
            data = self.redis_client.get(key)

            if data:
                messages_data = json.loads(data)
                messages = [Message.from_dict(msg) for msg in messages_data]
                self.conversations[session_id] = messages

                logger.debug(f"Loaded {len(messages)} messages from Redis")

        except Exception as e:
            logger.error(f"Failed to load from Redis: {e}")

    def export_conversation(
        self,
        session_id: str,
        format: str = 'json'
    ) -> str:
        """
        Export conversation history

        Args:
            session_id: Session identifier
            format: Export format ('json', 'text')

        Returns:
            Formatted conversation string
        """
        messages = self.get_history(session_id)

        if format == 'json':
            return json.dumps(
                [msg.to_dict() for msg in messages],
                indent=2
            )

        elif format == 'text':
            lines = []
            for msg in messages:
                timestamp = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                lines.append(f"[{timestamp}] {msg.role.upper()}: {msg.content}")

            return '\n'.join(lines)

        else:
            raise ValueError(f"Unknown format: {format}")

    def __repr__(self):
        active_sessions = len(self.conversations)
        total_messages = sum(len(msgs) for msgs in self.conversations.values())

        return (
            f"ConversationMemory("
            f"sessions={active_sessions}, "
            f"messages={total_messages}, "
            f"max_history={self.max_history})"
        )
