"""
Embedding Service - v7.4.0
Real embedding generation service with multiple providers
"""

from typing import List, Dict, Optional, Any, Union
from enum import Enum
import hashlib
import asyncio
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from nexa.gguf import NexaTextInference
    NEXA_AVAILABLE = True
except ImportError:
    NEXA_AVAILABLE = False


class EmbeddingProvider(str, Enum):
    """Embedding provider"""
    OPENAI = "openai"
    NEXA = "nexa"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    OLLAMA = "ollama"


class EmbeddingModel(str, Enum):
    """Embedding models"""
    # OpenAI
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"      # 1536 dimensions
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"      # 3072 dimensions
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"      # 1536 dimensions

    # NexaAI
    NEXA_NOMIC_EMBED = "nomic-embed-text-v1.5"             # 768 dimensions
    NEXA_BGE_BASE = "bge-base-en-v1.5"                     # 768 dimensions
    NEXA_BGE_LARGE = "bge-large-en-v1.5"                   # 1024 dimensions

    # Sentence Transformers
    ALL_MINILM_L6_V2 = "all-MiniLM-L6-v2"                  # 384 dimensions
    ALL_MPNET_BASE_V2 = "all-mpnet-base-v2"                # 768 dimensions

    # Ollama
    OLLAMA_NOMIC_EMBED = "nomic-embed-text"                # 768 dimensions


class EmbeddingService:
    """
    Multi-provider embedding service

    Supports:
    - OpenAI (text-embedding-3-small, text-embedding-3-large, ada-002)
    - NexaAI (nomic-embed, bge-base, bge-large)
    - Sentence Transformers (local models)
    - Ollama (local models)
    """

    def __init__(
        self,
        provider: EmbeddingProvider = EmbeddingProvider.OPENAI,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_enabled: bool = True
    ):
        self.provider = provider
        self.model = model or self._get_default_model(provider)
        self.api_key = api_key
        self.base_url = base_url
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, List[float]] = {}

        # Initialize provider
        self._initialize_provider()

    def _get_default_model(self, provider: EmbeddingProvider) -> str:
        """Get default model for provider"""
        defaults = {
            EmbeddingProvider.OPENAI: EmbeddingModel.TEXT_EMBEDDING_3_SMALL.value,
            EmbeddingProvider.NEXA: EmbeddingModel.NEXA_NOMIC_EMBED.value,
            EmbeddingProvider.SENTENCE_TRANSFORMERS: EmbeddingModel.ALL_MPNET_BASE_V2.value,
            EmbeddingProvider.OLLAMA: EmbeddingModel.OLLAMA_NOMIC_EMBED.value
        }
        return defaults[provider]

    def _initialize_provider(self):
        """Initialize embedding provider"""
        if self.provider == EmbeddingProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed. Run: pip install openai")
            if self.api_key:
                openai.api_key = self.api_key
            if self.base_url:
                openai.base_url = self.base_url

        elif self.provider == EmbeddingProvider.NEXA:
            if not NEXA_AVAILABLE:
                raise ImportError("nexa package not installed. Run: pip install nexaai")
            # Initialize NexaAI model
            self.nexa_model = NexaTextInference(
                model_path=self.model,
                local_path=None,
                stop_words=[],
                temperature=0.0
            )

        elif self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            try:
                from sentence_transformers import SentenceTransformer
                self.st_model = SentenceTransformer(self.model)
            except ImportError:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")

        elif self.provider == EmbeddingProvider.OLLAMA:
            # Ollama uses HTTP API
            import httpx
            self.ollama_client = httpx.AsyncClient(base_url=self.base_url or "http://localhost:11434")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text

        Args:
            text: Input text

        Returns:
            Embedding vector (list of floats)
        """
        # Check cache
        if self.cache_enabled:
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                return self.cache[cache_key]

        # Generate embedding based on provider
        if self.provider == EmbeddingProvider.OPENAI:
            embedding = await self._generate_openai_embedding(text)
        elif self.provider == EmbeddingProvider.NEXA:
            embedding = await self._generate_nexa_embedding(text)
        elif self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            embedding = await self._generate_st_embedding(text)
        elif self.provider == EmbeddingProvider.OLLAMA:
            embedding = await self._generate_ollama_embedding(text)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        # Cache result
        if self.cache_enabled:
            self.cache[cache_key] = embedding

        return embedding

    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await asyncio.gather(*[
                self.generate_embedding(text) for text in batch
            ])
            embeddings.extend(batch_embeddings)

        return embeddings

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            response = await openai.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding generation failed: {str(e)}")

    async def _generate_nexa_embedding(self, text: str) -> List[float]:
        """Generate embedding using NexaAI"""
        try:
            # NexaAI embedding (synchronous, run in executor)
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.nexa_model.embed(text)
            )
            return embedding.tolist() if hasattr(embedding, 'tolist') else embedding
        except Exception as e:
            raise RuntimeError(f"NexaAI embedding generation failed: {str(e)}")

    async def _generate_st_embedding(self, text: str) -> List[float]:
        """Generate embedding using Sentence Transformers"""
        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.st_model.encode(text)
            )
            return embedding.tolist()
        except Exception as e:
            raise RuntimeError(f"Sentence Transformers embedding generation failed: {str(e)}")

    async def _generate_ollama_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        try:
            response = await self.ollama_client.post(
                "/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            raise RuntimeError(f"Ollama embedding generation failed: {str(e)}")

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{self.provider}:{self.model}:{text_hash}"

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension for current model"""
        dimensions = {
            # OpenAI
            EmbeddingModel.TEXT_EMBEDDING_3_SMALL.value: 1536,
            EmbeddingModel.TEXT_EMBEDDING_3_LARGE.value: 3072,
            EmbeddingModel.TEXT_EMBEDDING_ADA_002.value: 1536,
            # NexaAI
            EmbeddingModel.NEXA_NOMIC_EMBED.value: 768,
            EmbeddingModel.NEXA_BGE_BASE.value: 768,
            EmbeddingModel.NEXA_BGE_LARGE.value: 1024,
            # Sentence Transformers
            EmbeddingModel.ALL_MINILM_L6_V2.value: 384,
            EmbeddingModel.ALL_MPNET_BASE_V2.value: 768,
            # Ollama
            EmbeddingModel.OLLAMA_NOMIC_EMBED.value: 768
        }
        return dimensions.get(self.model, 768)  # Default to 768

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self.cache),
            "provider": self.provider,
            "model": self.model,
            "dimension": self.get_embedding_dimension()
        }

    def clear_cache(self):
        """Clear embedding cache"""
        self.cache.clear()


# Global instances for different providers
_embedding_services: Dict[str, EmbeddingService] = {}


def get_embedding_service(
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> EmbeddingService:
    """
    Get or create embedding service instance

    Args:
        provider: Embedding provider
        model: Model name (optional, uses default if not specified)
        api_key: API key for provider (optional)
        base_url: Base URL for provider (optional)

    Returns:
        EmbeddingService instance
    """
    cache_key = f"{provider}:{model or 'default'}"

    if cache_key not in _embedding_services:
        _embedding_services[cache_key] = EmbeddingService(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url
        )

    return _embedding_services[cache_key]


# Convenience functions for quick access
async def embed_text(
    text: str,
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI,
    model: Optional[str] = None
) -> List[float]:
    """Quick function to generate embedding"""
    service = get_embedding_service(provider, model)
    return await service.generate_embedding(text)


async def embed_texts(
    texts: List[str],
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI,
    model: Optional[str] = None,
    batch_size: int = 32
) -> List[List[float]]:
    """Quick function to generate embeddings for multiple texts"""
    service = get_embedding_service(provider, model)
    return await service.generate_embeddings_batch(texts, batch_size)
