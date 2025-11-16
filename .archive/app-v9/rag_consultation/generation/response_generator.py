"""
Response Generator - LLM Integration with Ollama

Provides production-ready response generation using Ollama LLM
with CORRECT localhost:11434 configuration.

CRITICAL: Ollama runs on macOS via Ollama.app, NOT Docker.
Endpoint: http://localhost:11434 (LOCAL ONLY)

Features:
- Ollama LLM integration (localhost:11434)
- Template-based response formatting
- Error handling and fallbacks
- Streaming support
- Timeout management

Usage:
    generator = ResponseGenerator(
        ollama_url="http://localhost:11434",
        model_name="qwen2.5:7b-instruct-q4_K_M"
    )
    response = await generator.generate(
        prompt="...",
        query_type=QueryType.FACTUAL,
        formality=FormalityLevel.FORMAL
    )
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.rag_consultation.generation.template_system import TemplateSystem
from app.rag_consultation.models import (
    FormalityLevel,
    QueryType,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """LLM response generator with Ollama integration.

    Generates responses using Ollama LLM running on localhost:11434
    with template-based formatting.

    CRITICAL: Ollama endpoint must be http://localhost:11434
    Do NOT use Docker IP addresses (172.28.0.X).

    Attributes:
        ollama_url: Ollama API endpoint (localhost:11434)
        model_name: Ollama model name
        template_system: Template system for formatting
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model_name: str = "qwen2.5:7b-instruct-q4_K_M",
        template_system: Optional[TemplateSystem] = None,
        timeout: int = 120,
    ) -> None:
        """Initialize response generator.

        Args:
            ollama_url: Ollama API URL (must be localhost:11434)
            model_name: Ollama model name
            template_system: Template system instance
            timeout: Request timeout in seconds

        Raises:
            ValueError: If ollama_url is not localhost
        """
        # CRITICAL: Validate localhost configuration
        if "localhost" not in ollama_url and "127.0.0.1" not in ollama_url:
            raise ValueError(
                f"Ollama URL must use localhost or 127.0.0.1. "
                f"Got: {ollama_url}. "
                f"Ollama runs on macOS via Ollama.app, NOT Docker."
            )

        self.ollama_url = ollama_url.rstrip("/")
        self.model_name = model_name
        self.template_system = template_system or TemplateSystem()
        self.timeout = timeout

        logger.info(
            f"Response generator initialized: "
            f"endpoint={self.ollama_url}, model={self.model_name}"
        )

        # Verify ollama_url is localhost
        if self.ollama_url != "http://localhost:11434":
            logger.warning(
                f"Non-standard Ollama URL: {self.ollama_url}. " f"Expected: http://localhost:11434"
            )

    async def _call_ollama(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Call Ollama API for generation.

        Args:
            prompt: Complete prompt for LLM
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text

        Raises:
            RuntimeError: If Ollama API call fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                )

                response.raise_for_status()
                result = response.json()

                generated_text = result.get("response", "")

                if not generated_text:
                    raise RuntimeError("Empty response from Ollama")

                logger.info(f"Generated response from Ollama " f"({len(generated_text)} chars)")

                return generated_text.strip()

        except httpx.TimeoutException as e:
            logger.error(f"Ollama request timeout: {e}")
            raise RuntimeError(f"Ollama request timeout after {self.timeout}s") from e

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise RuntimeError(f"Ollama HTTP error: {e.response.status_code}") from e

        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise RuntimeError(f"Ollama generation failed: {e}") from e

    async def generate(
        self,
        prompt: str,
        query_type: QueryType,
        formality: FormalityLevel = FormalityLevel.NEUTRAL,
        urgency: UrgencyLevel = UrgencyLevel.MEDIUM,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        template_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate response using Ollama LLM.

        Args:
            prompt: Complete prompt for generation
            query_type: Query type for template selection
            formality: Response formality level
            urgency: Response urgency level
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            template_context: Context for template rendering

        Returns:
            Generated and formatted response

        Raises:
            ValueError: If prompt is empty
            RuntimeError: If generation fails
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Generate response from Ollama
            raw_response = await self._call_ollama(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Format response using template system
            if template_context:
                # Use template with provided context
                formatted_response = self.template_system.render_template(
                    query_type=query_type,
                    formality=formality,
                    urgency=urgency,
                    response=raw_response,
                    **template_context,
                )
            else:
                # Simple template with just response
                formatted_response = self.template_system.render_template(
                    query_type=query_type,
                    formality=formality,
                    urgency=urgency,
                    response=raw_response,
                )

            logger.info(f"Generated formatted response " f"({len(formatted_response)} chars)")

            return formatted_response

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise RuntimeError(f"Generation error: {e}") from e

    async def generate_simple(
        self,
        prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """Generate simple response without template formatting.

        Args:
            prompt: Complete prompt
            temperature: Generation temperature

        Returns:
            Raw generated response

        Raises:
            ValueError: If prompt is empty
            RuntimeError: If generation fails
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        return await self._call_ollama(prompt=prompt, temperature=temperature)

    async def health_check(self) -> bool:
        """Check if Ollama service is available.

        Returns:
            True if Ollama is responsive, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                response.raise_for_status()

                logger.info("Ollama health check: OK")
                return True

        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> list[str]:
        """List available Ollama models.

        Returns:
            List of model names

        Raises:
            RuntimeError: If API call fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                response.raise_for_status()

                result = response.json()
                models = [model["name"] for model in result.get("models", [])]

                logger.info(f"Available Ollama models: {models}")
                return models

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise RuntimeError(f"Model listing failed: {e}") from e
