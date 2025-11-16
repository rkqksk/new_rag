"""
Prompt Builder - LLM Prompt Construction

Provides production-ready prompt building for LLM generation
with query type-specific structures and context integration.

Features:
- Query type-specific prompt templates
- Context integration from conversation history
- Retrieval context formatting
- System instruction management

Usage:
    builder = PromptBuilder()
    prompt = builder.build_prompt(
        query="How does RAG work?",
        query_type=QueryType.FACTUAL,
        retrieval_context=["doc1", "doc2"],
        conversation_summary="Previous discussion..."
    )
"""

import logging
from typing import List, Optional

from app.rag_consultation.models import ExpertiseLevel, QueryType

logger = logging.getLogger(__name__)


class PromptBuilder:
    """LLM prompt builder with query type-specific templates.

    Constructs prompts for LLM generation with appropriate
    structure and context based on query characteristics.

    Attributes:
        system_instructions: Base system instructions for LLM
    """

    # Base system instruction
    BASE_SYSTEM_INSTRUCTION = """You are an expert AI assistant for manufacturing and industrial systems.

Your role is to provide accurate, helpful, and well-structured responses based on the provided context.

Key principles:
1. Answer based on the provided context and retrieved documents
2. If information is not in the context, acknowledge limitations
3. Provide practical, actionable information
4. Use clear, professional language
5. Structure responses for easy understanding

Remember: Quality and accuracy over speed. Be honest about limitations."""

    # Query type-specific instructions
    QUERY_TYPE_INSTRUCTIONS = {
        QueryType.FACTUAL: """Focus on providing clear, accurate definitions and explanations.
Use the retrieved context to give comprehensive answers.
Include relevant examples when helpful.""",
        QueryType.PROCEDURAL: """Provide step-by-step instructions in a clear, sequential format.
Number the steps and include important warnings or notes.
Explain the rationale behind key steps.""",
        QueryType.COMPARISON: """Present a balanced comparison of the items.
Highlight key differences and similarities.
Provide recommendations when appropriate.""",
        QueryType.TROUBLESHOOTING: """Systematically diagnose the issue.
Provide clear, actionable solutions.
Include prevention tips when relevant.""",
        QueryType.RECOMMENDATION: """Analyze the requirements carefully.
Provide ranked recommendations with rationale.
Explain trade-offs and considerations.""",
        QueryType.EXPLORATORY: """Provide a comprehensive overview of the topic.
Cover multiple relevant aspects.
Suggest areas for deeper exploration.""",
        QueryType.CONVERSATIONAL: """Respond naturally and helpfully.
Address the specific question or request.
Maintain conversation continuity.""",
    }

    # Expertise-specific adjustments
    EXPERTISE_ADJUSTMENTS = {
        ExpertiseLevel.BEGINNER: """Adjust your response for a beginner:
- Use simple, clear language
- Explain technical terms
- Provide more context and examples
- Avoid assuming prior knowledge""",
        ExpertiseLevel.INTERMEDIATE: """Adjust your response for intermediate level:
- Use standard technical terminology
- Provide moderate detail
- Include practical examples""",
        ExpertiseLevel.ADVANCED: """Adjust your response for advanced users:
- Use technical language freely
- Focus on nuances and details
- Discuss advanced concepts and trade-offs""",
        ExpertiseLevel.EXPERT: """Adjust your response for expert level:
- Use precise technical terminology
- Discuss implementation details
- Cover edge cases and optimizations
- Reference relevant research or best practices""",
    }

    def __init__(self, system_instruction: Optional[str] = None) -> None:
        """Initialize prompt builder.

        Args:
            system_instruction: Custom system instruction (optional)
        """
        self.system_instruction = system_instruction or self.BASE_SYSTEM_INSTRUCTION
        logger.info("Prompt builder initialized")

    def _format_retrieval_context(self, documents: List[str]) -> str:
        """Format retrieved documents into context string.

        Args:
            documents: List of retrieved document texts

        Returns:
            Formatted context string
        """
        if not documents:
            return "No specific documents retrieved."

        context_parts = ["Retrieved Context:\n"]
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"Document {i}:\n{doc}\n")

        return "\n".join(context_parts)

    def _format_conversation_history(
        self,
        conversation_summary: Optional[str],
    ) -> str:
        """Format conversation history for context.

        Args:
            conversation_summary: Summary of conversation history

        Returns:
            Formatted history string
        """
        if not conversation_summary:
            return ""

        return f"\nConversation Context:\n{conversation_summary}\n"

    def build_prompt(
        self,
        query: str,
        query_type: QueryType,
        retrieval_context: Optional[List[str]] = None,
        conversation_summary: Optional[str] = None,
        expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
    ) -> str:
        """Build complete prompt for LLM generation.

        Args:
            query: User query
            query_type: Classified query type
            retrieval_context: Retrieved documents (optional)
            conversation_summary: Conversation history (optional)
            expertise_level: User expertise level

        Returns:
            Complete prompt string

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Build prompt components
            components = []

            # 1. System instruction
            components.append(self.system_instruction)

            # 2. Query type-specific instruction
            type_instruction = self.QUERY_TYPE_INSTRUCTIONS.get(
                query_type,
                self.QUERY_TYPE_INSTRUCTIONS[QueryType.CONVERSATIONAL],
            )
            components.append(f"\n{type_instruction}")

            # 3. Expertise adjustment
            expertise_adjustment = self.EXPERTISE_ADJUSTMENTS.get(
                expertise_level,
                self.EXPERTISE_ADJUSTMENTS[ExpertiseLevel.INTERMEDIATE],
            )
            components.append(f"\n{expertise_adjustment}")

            # 4. Conversation history (if available)
            if conversation_summary:
                history = self._format_conversation_history(conversation_summary)
                components.append(f"\n{history}")

            # 5. Retrieval context (if available)
            if retrieval_context:
                context = self._format_retrieval_context(retrieval_context)
                components.append(f"\n{context}")

            # 6. User query
            components.append(f"\nUser Query:\n{query}")

            # 7. Response instruction
            components.append(
                "\nProvide a comprehensive, accurate response based on the above context and instructions."
            )

            # Combine all components
            full_prompt = "\n".join(components)

            logger.debug(
                f"Built prompt for {query_type.value} query " f"({len(full_prompt)} chars)"
            )

            return full_prompt

        except Exception as e:
            logger.error(f"Prompt building failed: {e}")
            raise RuntimeError(f"Prompt building error: {e}") from e

    def build_simple_prompt(
        self,
        query: str,
        context: Optional[str] = None,
    ) -> str:
        """Build simple prompt without detailed classification.

        Args:
            query: User query
            context: Optional context string

        Returns:
            Simple prompt string
        """
        components = [self.system_instruction]

        if context:
            components.append(f"\nContext:\n{context}")

        components.append(f"\nUser Query:\n{query}")
        components.append("\nProvide a helpful response.")

        return "\n".join(components)
