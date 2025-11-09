"""
Conversation management package for context-aware product search
"""

from .intent_analyzer import IntentAnalyzer
from .manager import ConversationManager
from .states import (
    ConversationContext,
    ConversationState,
    IntentType,
    SearchCriteria,
    StateTransition,
    get_next_state,
)

__all__ = [
    "ConversationState",
    "IntentType",
    "SearchCriteria",
    "ConversationContext",
    "StateTransition",
    "get_next_state",
    "IntentAnalyzer",
    "ConversationManager",
]
