"""
RAG Consultation Module - Phase 1: Query Classification System

This module provides intelligent query classification and response generation
for manufacturing AI consultation system.

Components:
- Classification: Query type, intent, tone, and language detection
- Context: Conversation management and session tracking
- Retrieval: Query expansion and strategy selection
- Generation: Template-based response generation with LLM

Production Features:
- BERT-based query classification with 7 query types
- Multi-label intent detection
- Tone and formality analysis
- Redis-backed session persistence
- Ollama LLM integration (localhost:11434)
- Comprehensive error handling and logging
"""

__version__ = "1.0.0"
__author__ = "RAG Enterprise Team"

from app.rag_consultation.models import (
    QueryAnalysis,
    IntentDetection,
    ToneAnalysis,
    ConversationContext,
    RetrievalStrategy,
)

__all__ = [
    "QueryAnalysis",
    "IntentDetection",
    "ToneAnalysis",
    "ConversationContext",
    "RetrievalStrategy",
]
