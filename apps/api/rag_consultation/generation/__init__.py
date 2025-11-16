"""
Generation Module - Response Generation with LLM

Provides response generation:
- PromptBuilder: Template-based prompt construction
- ResponseGenerator: Ollama LLM integration
- TemplateSystem: Response template management
"""

from apps.api.rag_consultation.generation.prompt_builder import PromptBuilder
from apps.api.rag_consultation.generation.response_generator import ResponseGenerator
from apps.api.rag_consultation.generation.template_system import TemplateSystem

__all__ = [
    "PromptBuilder",
    "ResponseGenerator",
    "TemplateSystem",
]
