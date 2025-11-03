from typing import List, Dict, Any, Optional
from langchain.llms import BaseLLM
from langchain.prompts import PromptTemplate

class ResponseGenerator:
    """
    Centralized LLM response generation with context-aware capabilities
    """
    DEFAULT_PROMPT_TEMPLATE = """
    You are an expert assistant helping to answer questions based on the most relevant context.

    Context:
    {context}

    Question: {question}

    If the answer cannot be found in the context, respond with "I do not have enough information to answer this question."

    Helpful Answer:
    """

    def __init__(
        self,
        llm: BaseLLM,
        prompt_template: Optional[str] = None
    ):
        """
        Initialize response generator

        Args:
            llm: Language model for generating responses
            prompt_template: Custom prompt template (optional)
        """
        self.llm = llm
        self.prompt_template = prompt_template or self.DEFAULT_PROMPT_TEMPLATE

        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )

    def generate_response(
        self,
        context_chunks: List[Dict[str, Any]],
        query: str,
        max_context_tokens: int = 1000
    ) -> str:
        """
        Generate response using retrieved context chunks

        Args:
            context_chunks: List of context dictionaries from retrieval
            query: User's original query
            max_context_tokens: Maximum tokens to include in context

        Returns:
            Generated response
        """
        # Sort context by relevance score
        sorted_context = sorted(
            context_chunks,
            key=lambda x: x.get('score', 0),
            reverse=True
        )

        # Truncate context to max tokens
        context_text = "\n\n".join([
            chunk['text'] for chunk in sorted_context
        ])

        # Prepare full prompt
        full_prompt = self.prompt.format(
            context=context_text[:max_context_tokens],
            question=query
        )

        # Generate response
        response = self.llm(full_prompt)

        return response

    def extract_citations(
        self,
        context_chunks: List[Dict[str, Any]],
        response: str
    ) -> Dict[str, Any]:
        """
        Extract citations from generated response

        Args:
            context_chunks: Original context chunks
            response: Generated response

        Returns:
            Citation metadata
        """
        citations = []
        for chunk in context_chunks:
            if chunk['text'] in response:
                citations.append({
                    'text': chunk['text'],
                    'metadata': chunk.get('metadata', {}),
                    'score': chunk.get('score', 0)
                })

        return {
            'citations': citations,
            'citation_count': len(citations)
        }