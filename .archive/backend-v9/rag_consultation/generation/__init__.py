"""
Generation Module - Response Generation with LLM

Provides response generation:
- PromptBuilder: Template-based prompt construction
- ResponseGenerator: Ollama LLM integration
- TemplateSystem: Response template management
"""

from app.rag_consultation.generation.prompt_builder import PromptBuilder
from app.rag_consultation.generation.response_generator import ResponseGenerator
from app.rag_consultation.generation.template_system import TemplateSystem

__all__ = [
    "PromptBuilder",
    "ResponseGenerator",
    "TemplateSystem",
]
