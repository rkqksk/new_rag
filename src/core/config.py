"""
Configuration Management for RAG Enterprise

Centralized configuration with environment variable support.
Handles both local development and Docker environments.

Usage:
    from src.core.config import get_config

    config = get_config()
    qdrant_client = QdrantClient(url=config.qdrant_url)
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration with environment variable fallbacks"""

    # Qdrant Configuration
    qdrant_url: str
    qdrant_timeout: int

    # Embedding Configuration
    embedding_model: str
    embedding_dim: int

    # Ollama Configuration
    ollama_url: str
    ollama_model: str

    # PostgreSQL Configuration
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    # Redis Configuration
    redis_host: str
    redis_port: int
    redis_db: int

    # Environment
    environment: str
    debug: bool


def get_config() -> Config:
    """
    Get application configuration from environment variables

    Returns:
        Config object with all settings

    Environment Variables:
        QDRANT_HOST: Qdrant host (default: localhost)
        QDRANT_HTTP_PORT: Qdrant HTTP port (default: 6333)
        QDRANT_TIMEOUT: Qdrant timeout in seconds (default: 30)

        EMBEDDING_MODEL: Embedding model name (default: all-MiniLM-L6-v2)
        EMBEDDING_DIM: Embedding dimension (default: 384)

        OLLAMA_HOST: Ollama host (default: localhost)
        OLLAMA_PORT: Ollama port (default: 11434)
        OLLAMA_DEFAULT_MODEL: Ollama model (default: qwen2.5:7b-instruct)

        POSTGRES_HOST: PostgreSQL host (default: localhost)
        POSTGRES_PORT: PostgreSQL port (default: 5432)
        POSTGRES_USER: PostgreSQL user (default: postgres)
        POSTGRES_PASSWORD: PostgreSQL password (default: changeme)
        POSTGRES_DB: PostgreSQL database (default: rag_enterprise)

        REDIS_HOST: Redis host (default: localhost)
        REDIS_PORT: Redis port (default: 6379)
        REDIS_DB: Redis database (default: 0)

        ENVIRONMENT: Environment name (default: development)
        DEBUG: Debug mode (default: true)
    """
    # Qdrant
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_HTTP_PORT", "6333"))
    qdrant_url = f"http://{qdrant_host}:{qdrant_port}"
    qdrant_timeout = int(os.getenv("QDRANT_TIMEOUT", "30"))

    # Embedding
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_dim = int(os.getenv("EMBEDDING_DIM", "384"))

    # Ollama
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
    ollama_url = f"http://{ollama_host}:{ollama_port}"
    ollama_model = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5:7b-instruct")

    # PostgreSQL
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "changeme")
    postgres_db = os.getenv("POSTGRES_DB", "rag_enterprise")

    # Redis
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))

    # Environment
    environment = os.getenv("ENVIRONMENT", "development")
    debug = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    return Config(
        qdrant_url=qdrant_url,
        qdrant_timeout=qdrant_timeout,
        embedding_model=embedding_model,
        embedding_dim=embedding_dim,
        ollama_url=ollama_url,
        ollama_model=ollama_model,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_db=postgres_db,
        redis_host=redis_host,
        redis_port=redis_port,
        redis_db=redis_db,
        environment=environment,
        debug=debug,
    )


# Singleton instance
_config: Optional[Config] = None


def get_singleton_config() -> Config:
    """Get singleton configuration instance"""
    global _config
    if _config is None:
        _config = get_config()
    return _config
