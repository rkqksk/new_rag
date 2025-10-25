"""
Conversation management package for context-aware product search
"""

from .states import (
    ConversationState,
    IntentType,
    SearchCriteria,
    ConversationContext,
    StateTransition,
    get_next_state
)
from .intent_analyzer import IntentAnalyzer
from .manager import ConversationManager

__all__ = [
    'ConversationState',
    'IntentType',
    'SearchCriteria',
    'ConversationContext',
    'StateTransition',
    'get_next_state',
    'IntentAnalyzer',
    'ConversationManager'
]
