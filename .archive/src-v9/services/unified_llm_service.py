"""
Unified LLM Service

Provides a single interface to multiple LLM engines (NexaAI and Ollama)
with intelligent routing based on query complexity and requirements.
"""

import logging
import os
from typing import AsyncIterator, List, Optional, Union

import httpx
from pydantic import BaseModel, Field

from src.core.model_router import ModelEngine, ModelRouter, RoutingDecision
from src.services.nexa_service import NexaConfig, NexaService

logger = logging.getLogger(__name__)


class OllamaConfig(BaseModel):
    """Ollama configuration"""

    base_url: str = "http://localhost:11434"
    timeout: int = 60
    default_model: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    )


class OllamaService:
    """
    Ollama Service Wrapper

    Simple wrapper for Ollama API calls
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        # Override default_model with environment variable if set
        env_model = os.getenv("OLLAMA_MODEL")
        if env_model:
            self.config.default_model = env_model
        logger.info(f"Ollama service initialized: {self.config.base_url} (model: {self.config.default_model})")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        system: Optional[str] = None,
    ) -> Union[str, AsyncIterator[str]]:
        """
        Generate text with Ollama

        Args:
            prompt: Input prompt
            model: Model to use
            stream: Whether to stream response
            system: System prompt

        Returns:
            Generated text or stream
        """
        model = model or self.config.default_model

        url = f"{self.config.base_url}/api/generate"

        payload = {"model": model, "prompt": prompt, "stream": stream}

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                if stream:

                    async def stream_generator():
                        async with client.stream("POST", url, json=payload) as response:
                            async for line in response.aiter_lines():
                                if line:
                                    import json

                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"]

                    return stream_generator()
                else:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    return result["response"]

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Ollama request error: {type(e).__name__} - {str(e)}")
            raise
        except KeyError as e:
            logger.error(f"Ollama response missing key: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama generation failed: {type(e).__name__} - {str(e)}", exc_info=True)
            raise

    async def embed(
        self, texts: List[str], model: str = "nomic-embed-text:latest"
    ) -> List[List[float]]:
        """
        Generate embeddings with Ollama

        Args:
            texts: List of texts
            model: Embedding model

        Returns:
            List of embeddings
        """
        url = f"{self.config.base_url}/api/embeddings"

        embeddings = []

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                for text in texts:
                    payload = {"model": model, "prompt": text}

                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    embeddings.append(result["embedding"])

            return embeddings

        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise

    async def health_check(self) -> dict:
        """Check Ollama server health"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")
                return {"healthy": response.status_code == 200}
        except Exception as e:
            return {"healthy": False, "error": str(e)}


class UnifiedLLMService:
    """
    Unified LLM Service

    Provides a single interface to both NexaAI and Ollama engines
    with intelligent routing based on query characteristics.
    """

    def __init__(
        self,
        nexa_config: Optional[NexaConfig] = None,
        ollama_config: Optional[OllamaConfig] = None,
        router_config: Optional[dict] = None,
    ):
        """
        Initialize unified LLM service

        Args:
            nexa_config: NexaAI configuration
            ollama_config: Ollama configuration
            router_config: Model router configuration
        """
        # Check if NexaAI should be enabled
        enable_nexa = os.getenv("ENABLE_NEXA", "true").lower() == "true"

        # Initialize engines
        if enable_nexa:
            try:
                self.nexa = NexaService(nexa_config)
                self.nexa_available = True
            except Exception as e:
                logger.warning(f"NexaAI not available: {e}")
                self.nexa = None
                self.nexa_available = False
        else:
            logger.info("NexaAI disabled via ENABLE_NEXA environment variable")
            self.nexa = None
            self.nexa_available = False

        try:
            self.ollama = OllamaService(ollama_config)
            self.ollama_available = True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self.ollama = None
            self.ollama_available = False

        # Initialize router
        router_config = router_config or {}
        self.router = ModelRouter(
            enable_nexa=self.nexa_available, enable_ollama=self.ollama_available, **router_config
        )

        # Statistics
        self.stats = {"nexa_requests": 0, "ollama_requests": 0, "errors": 0}

        logger.info(
            f"UnifiedLLMService initialized "
            f"(NexaAI: {self.nexa_available}, Ollama: {self.ollama_available})"
        )

    async def generate(
        self,
        prompt: str,
        stream: bool = False,
        system_prompt: Optional[str] = None,
        force_engine: Optional[ModelEngine] = None,
        force_model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> Union[str, AsyncIterator[str]]:
        """
        Generate response with automatic routing and fallback

        Strategy: Always try NexaAI first (fast, multimodal), fallback to Ollama (quality)
        This implements the user requirement: "NexaAI as main, Ollama as fallback"

        Args:
            prompt: Input prompt
            stream: Whether to stream response
            system_prompt: System prompt
            force_engine: Force specific engine
            force_model: Force specific model
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            Generated text or stream
        """
        # Route to appropriate engine
        routing: RoutingDecision = self.router.route(
            query=prompt, force_engine=force_engine, force_model=force_model
        )

        logger.info(
            f"Routing: {routing.engine.value} / {routing.model} "
            f"(reason: {routing.reason}, score: {routing.complexity_score:.2f})"
        )

        # **Hybrid Strategy: NexaAI main, Ollama fallback**
        # Try NexaAI first (unless forced to Ollama)
        if self.nexa_available and force_engine != ModelEngine.OLLAMA:
            try:
                self.stats["nexa_requests"] += 1

                # Use routed model if NexaAI was selected, otherwise use default NexaAI model
                nexa_model = routing.model if routing.engine == ModelEngine.NEXA else self.router.routing_rules["medium"]["model"]

                logger.debug(f"Trying NexaAI: {nexa_model}")

                return await self.nexa.generate_text(
                    prompt=prompt,
                    model=nexa_model,
                    stream=stream,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            except Exception as e:
                logger.warning(f"NexaAI failed: {e}. Falling back to Ollama...")
                # Continue to Ollama fallback below

        # Fallback to Ollama (or primary if NexaAI not available/disabled)
        if not self.ollama_available:
            self.stats["errors"] += 1
            raise RuntimeError(
                "Both NexaAI and Ollama are unavailable. Cannot generate response."
            )

        try:
            self.stats["ollama_requests"] += 1

            # Use routed model if Ollama was selected, otherwise use default
            ollama_model = routing.model if routing.engine == ModelEngine.OLLAMA else self.ollama.config.default_model

            logger.info(f"Using Ollama: {ollama_model}")

            return await self.ollama.generate(
                prompt=prompt,
                model=ollama_model,
                stream=stream,
                system=system_prompt
            )

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"All engines failed. Last error: {e}")
            raise

    async def embed(
        self, texts: List[str], engine: Optional[ModelEngine] = None
    ) -> List[List[float]]:
        """
        Generate embeddings

        Args:
            texts: List of texts to embed
            engine: Preferred engine (default: NexaAI if available)

        Returns:
            List of embedding vectors
        """
        # Prefer NexaAI for embeddings (faster)
        if engine is None:
            engine = ModelEngine.NEXA if self.nexa_available else ModelEngine.OLLAMA

        try:
            if engine == ModelEngine.NEXA:
                if not self.nexa_available:
                    raise RuntimeError("NexaAI not available")

                return await self.nexa.generate_embeddings(texts)

            else:  # OLLAMA
                if not self.ollama_available:
                    raise RuntimeError("Ollama not available")

                return await self.ollama.embed(texts)

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def analyze_image(self, image_path: str, prompt: str, max_tokens: int = 500) -> str:
        """
        Analyze image (requires NexaAI)

        Args:
            image_path: Path to image
            prompt: Analysis prompt
            max_tokens: Maximum tokens

        Returns:
            Analysis result
        """
        if not self.nexa_available:
            raise RuntimeError("Image analysis requires NexaAI")

        return await self.nexa.analyze_image(
            image_path=image_path, prompt=prompt, max_tokens=max_tokens
        )

    async def health_check(self) -> dict:
        """
        Check health of all engines

        Returns:
            Health status dict
        """
        health = {"unified": True, "engines": {}}

        # Check NexaAI
        if self.nexa_available:
            nexa_health = await self.nexa.health_check()
            health["engines"]["nexa"] = nexa_health
            if not nexa_health["healthy"]:
                health["unified"] = False
        else:
            health["engines"]["nexa"] = {"healthy": False, "error": "Not configured"}

        # Check Ollama
        if self.ollama_available:
            ollama_health = await self.ollama.health_check()
            health["engines"]["ollama"] = ollama_health
            if not ollama_health["healthy"]:
                health["unified"] = False
        else:
            health["engines"]["ollama"] = {"healthy": False, "error": "Not configured"}

        # At least one engine must be healthy
        if not self.nexa_available and not self.ollama_available:
            health["unified"] = False

        return health

    def get_stats(self) -> dict:
        """Get service statistics"""
        return {
            **self.stats,
            "nexa_available": self.nexa_available,
            "ollama_available": self.ollama_available,
            "router": self.router.get_stats(),
        }


# Singleton
_unified_llm: Optional[UnifiedLLMService] = None


def get_unified_llm(
    nexa_config: Optional[NexaConfig] = None,
    ollama_config: Optional[OllamaConfig] = None,
    router_config: Optional[dict] = None,
) -> UnifiedLLMService:
    """Get or create unified LLM service singleton"""
    global _unified_llm

    if _unified_llm is None:
        _unified_llm = UnifiedLLMService(
            nexa_config=nexa_config, ollama_config=ollama_config, router_config=router_config
        )

    return _unified_llm
