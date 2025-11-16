"""
Dependency Injection Container

Manages service lifecycle and dependency resolution using FastAPI's
dependency injection system with lru_cache for singleton pattern.
"""

import logging
import os
from functools import lru_cache
from typing import Optional

import redis
from fastapi import Depends
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


# ============================================================
# Configuration Dependencies
# ============================================================


class AppConfig:
    """Application configuration loaded from environment variables"""

    def __init__(self):
        """Initialize configuration from .env and environment"""
        from dotenv import load_dotenv

        load_dotenv()

        # Qdrant Configuration
        # Default to localhost for development (local Qdrant via docker-compose)
        # Use Docker IP (172.28.0.2) in production via .env
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_HTTP_PORT", "6333"))
        self.qdrant_url = f"http://{self.qdrant_host}:{self.qdrant_port}"

        # Redis Configuration
        # Default to localhost for development
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))

        # PostgreSQL Configuration
        # Default to localhost for development
        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD")
        self.postgres_db = os.getenv("POSTGRES_DB", "rag_enterprise")

        # Embedding Model Configuration
        self.embedding_model = os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.embedding_dim = int(os.getenv("EMBEDDING_DIM", "384"))

        # Ollama Configuration
        # Default to localhost for development (local Ollama app)
        # Use Docker IP (172.28.0.6:11434) in production via .env
        ollama_host = os.getenv("OLLAMA_HOST", "localhost")
        ollama_port = os.getenv("OLLAMA_PORT", "11434")
        self.ollama_url = f"http://{ollama_host}:{ollama_port}"
        self.ollama_model = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5:7b-instruct-q4_K_M")

        # CORS Configuration
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        self.allowed_origins = [origin.strip() for origin in self.allowed_origins if origin.strip()]

        # Validate critical configuration
        if not self.postgres_password:
            raise ValueError(
                "POSTGRES_PASSWORD environment variable is required. "
                "Set it in your .env file or environment."
            )

        logger.info("✅ Configuration loaded successfully")


@lru_cache()
def get_config() -> AppConfig:
    """Get application configuration (singleton with caching)"""
    return AppConfig()


# ============================================================
# Infrastructure Dependencies
# ============================================================


def get_qdrant_client(config: AppConfig = Depends(get_config)) -> QdrantClient:
    """
    Get Qdrant client (no caching to allow config changes)

    Args:
        config: Application configuration

    Returns:
        QdrantClient configured with host and port
    """
    client = QdrantClient(host=config.qdrant_host, port=config.qdrant_port)
    logger.info(f"✅ Qdrant client initialized: {config.qdrant_host}:{config.qdrant_port}")
    return client


@lru_cache()
def get_redis_client(config: AppConfig = Depends(get_config)) -> redis.Redis:
    """
    Get Redis client (singleton)

    Args:
        config: Application configuration

    Returns:
        Redis client configured with host and port
    """
    client = redis.Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)
    # Verify connection
    try:
        client.ping()
        logger.info(f"✅ Redis client initialized: {config.redis_host}:{config.redis_port}")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection warning (may not be critical): {e}")
    return client


@lru_cache()
def get_embedding_model(config: AppConfig = Depends(get_config)) -> SentenceTransformer:
    """
    Get embedding model (singleton - expensive to load)

    Args:
        config: Application configuration

    Returns:
        SentenceTransformer model loaded from config
    """
    model = SentenceTransformer(config.embedding_model)
    logger.info(f"✅ Embedding model loaded: {config.embedding_model}")
    return model


# ============================================================
# Service Dependencies
# ============================================================


def get_rag_qa_service(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embedding_model: SentenceTransformer = Depends(get_embedding_model),
    config: AppConfig = Depends(get_config),
):
    """
    Get RAG QA Service (request-scoped - new instance per request)

    Args:
        qdrant_client: Qdrant vector database client
        embedding_model: Sentence transformer model
        config: Application configuration

    Returns:
        RAGQAService instance
    """
    from apps.api.services.rag_qa_service import RAGQAService

    return RAGQAService(
        qdrant_client=qdrant_client,
        embedding_model=embedding_model,
        ollama_url=config.ollama_url,
        model_name=config.ollama_model,
    )


def get_async_rag_qa_service(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embedding_model: SentenceTransformer = Depends(get_embedding_model),
    config: AppConfig = Depends(get_config),
):
    """
    Get Async RAG QA Service (request-scoped - new instance per request)

    Provides async/await optimized version of RAG QA service with:
    - Connection pooling for HTTP requests
    - Batch processing support
    - Intelligent retry logic
    - Thread pool execution for CPU-bound tasks

    Args:
        qdrant_client: Qdrant vector database client
        embedding_model: Sentence transformer model
        config: Application configuration

    Returns:
        AsyncRAGQAService instance
    """
    from apps.api.services.async_rag_qa_service import AsyncRAGQAService

    return AsyncRAGQAService(
        qdrant_client=qdrant_client,
        embedding_model=embedding_model,
        ollama_url=config.ollama_url,
        model_name=config.ollama_model,
        timeout=30,
        max_retries=3,
    )


def get_consultation_service(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embedding_model: SentenceTransformer = Depends(get_embedding_model),
):
    """
    Get Consultation Service (request-scoped)

    Args:
        qdrant_client: Qdrant vector database client
        embedding_model: Sentence transformer model

    Returns:
        ConsultationService instance
    """
    from apps.api.services.consultation_service import ConsultationService

    return ConsultationService(
        search_client=qdrant_client, embedding_model=embedding_model, llm_client=None
    )


def get_document_ingestion_service(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embedding_model: SentenceTransformer = Depends(get_embedding_model),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Get Document Ingestion Service (request-scoped)

    Args:
        qdrant_client: Qdrant vector database client
        embedding_model: Sentence transformer model
        redis_client: Redis cache client

    Returns:
        DocumentIngestionService instance
    """
    from apps.api.services.document_ingestion_service import DocumentIngestionService

    return DocumentIngestionService(
        qdrant_client=qdrant_client, embedding_model=embedding_model, redis_client=redis_client
    )


# ============================================================
# Testing Utilities
# ============================================================


def override_dependencies_for_testing():
    """
    Get override dependencies for testing

    Usage in tests:
        app.dependency_overrides = override_dependencies_for_testing()
    """
    from unittest.mock import AsyncMock, Mock

    def get_mock_qdrant():
        """Mock Qdrant client"""
        client = Mock(spec=QdrantClient)
        client.search = AsyncMock(return_value=[])
        client.get_collection = Mock()
        client.upsert = Mock()
        return client

    def get_mock_redis():
        """Mock Redis client"""
        client = Mock(spec=redis.Redis)
        client.get = Mock(return_value=None)
        client.setex = Mock()
        client.ping = Mock(return_value=True)
        return client

    def get_mock_config():
        """Mock AppConfig"""
        config = Mock(spec=AppConfig)
        config.qdrant_host = "localhost"
        config.qdrant_port = 6333
        config.redis_host = "localhost"
        config.redis_port = 6379
        config.embedding_model = "test-model"
        config.embedding_dim = 384
        config.ollama_url = "http://localhost:11434"
        config.ollama_model = "qwen2.5:7b-instruct-q4_K_M"
        return config

    return {
        get_config: get_mock_config,
        get_qdrant_client: get_mock_qdrant,
        get_redis_client: get_mock_redis,
    }
