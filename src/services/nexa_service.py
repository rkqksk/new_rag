"""
NexaAI SDK Service Wrapper

Provides a unified interface to NexaAI SDK's OpenAI-compatible API
for text generation, embeddings, and multi-modal analysis.
"""

from typing import List, Dict, Optional, Union, AsyncIterator
import httpx
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel, Field
import logging
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class NexaConfig(BaseModel):
    """NexaAI configuration"""

    base_url: str = Field(
        default="http://localhost:8080/v1",
        description="NexaAI server base URL"
    )
    api_key: str = Field(
        default="not-needed",
        description="API key (not needed for local server)"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries"
    )
    default_text_model: str = Field(
        default="Qwen3-1.7B",
        description="Default model for text generation"
    )
    default_vision_model: str = Field(
        default="Qwen3-VL-4B-Instruct",
        description="Default model for vision-language tasks"
    )
    default_embedding_model: str = Field(
        default="EmbeddingGemma",
        description="Default model for embeddings"
    )


class NexaService:
    """
    NexaAI SDK Service

    Provides methods for:
    - Text generation (with streaming support)
    - Image analysis (vision-language)
    - Embedding generation
    - Health checks
    """

    def __init__(self, config: Optional[NexaConfig] = None):
        """
        Initialize NexaAI service

        Args:
            config: Optional configuration. If None, uses defaults.
        """
        self.config = config or NexaConfig()

        # Initialize OpenAI client
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )

        # Initialize async client
        self.async_client = AsyncOpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )

        logger.info(f"NexaAI service initialized with base URL: {self.config.base_url}")

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> Union[str, AsyncIterator[str]]:
        """
        Generate text completion

        Args:
            prompt: Input prompt
            model: Model to use (default: from config)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            stream: Whether to stream the response
            system_prompt: Optional system prompt

        Returns:
            Generated text or async iterator of text chunks
        """
        model = model or self.config.default_text_model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )

            if stream:
                async def stream_generator():
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content

                return stream_generator()
            else:
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for texts

        Args:
            texts: List of texts to embed
            model: Model to use (default: from config)

        Returns:
            List of embedding vectors
        """
        model = model or self.config.default_embedding_model

        try:
            response = await self.async_client.embeddings.create(
                model=model,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]

            logger.debug(
                f"Generated {len(embeddings)} embeddings "
                f"(dim: {len(embeddings[0]) if embeddings else 0})"
            )

            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def analyze_image(
        self,
        image_path: Union[str, Path],
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        """
        Analyze image with vision-language model

        Args:
            image_path: Path to image file
            prompt: Text prompt for analysis
            model: Model to use (default: from config)
            max_tokens: Maximum tokens to generate

        Returns:
            Analysis result as text
        """
        model = model or self.config.default_vision_model
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            # Detect image format
            suffix = image_path.suffix.lower()
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp'
            }.get(suffix, 'image/jpeg')

            # Create vision-language request
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens
            )

            result = response.choices[0].message.content

            logger.debug(f"Image analysis complete: {image_path.name}")

            return result

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise

    async def analyze_image_batch(
        self,
        image_paths: List[Union[str, Path]],
        prompts: List[str],
        model: Optional[str] = None,
        max_tokens: int = 500
    ) -> List[str]:
        """
        Analyze multiple images in batch

        Args:
            image_paths: List of image paths
            prompts: List of prompts (one per image)
            model: Model to use
            max_tokens: Maximum tokens per response

        Returns:
            List of analysis results
        """
        if len(image_paths) != len(prompts):
            raise ValueError("Number of images must match number of prompts")

        results = []

        for image_path, prompt in zip(image_paths, prompts):
            result = await self.analyze_image(
                image_path=image_path,
                prompt=prompt,
                model=model,
                max_tokens=max_tokens
            )
            results.append(result)

        return results

    async def health_check(self) -> Dict[str, Union[bool, str]]:
        """
        Check NexaAI server health

        Returns:
            Health status dict with 'healthy' and optional 'error'
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to access base URL
                health_url = self.config.base_url.replace('/v1', '/health')

                response = await client.get(health_url)

                if response.status_code == 200:
                    return {"healthy": True}
                else:
                    return {
                        "healthy": False,
                        "error": f"HTTP {response.status_code}"
                    }

        except httpx.TimeoutException:
            logger.error("NexaAI health check timed out")
            return {"healthy": False, "error": "Timeout"}

        except Exception as e:
            logger.error(f"NexaAI health check failed: {e}")
            return {"healthy": False, "error": str(e)}

    def list_models(self) -> List[str]:
        """
        List available models

        Returns:
            List of model names
        """
        try:
            response = self.client.models.list()
            return [model.id for model in response.data]

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def get_model_info(self, model: str) -> Dict:
        """
        Get information about a specific model

        Args:
            model: Model name

        Returns:
            Model information dict
        """
        try:
            response = self.client.models.retrieve(model)
            return {
                "id": response.id,
                "created": response.created,
                "owned_by": response.owned_by
            }

        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}


# Singleton instance
_nexa_service: Optional[NexaService] = None


def get_nexa_service(config: Optional[NexaConfig] = None) -> NexaService:
    """
    Get or create NexaAI service singleton

    Args:
        config: Optional configuration

    Returns:
        NexaService instance
    """
    global _nexa_service

    if _nexa_service is None:
        _nexa_service = NexaService(config)

    return _nexa_service
