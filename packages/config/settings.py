"""
Centralized configuration management for RAG Enterprise v10.0.0

This module provides a unified configuration interface using Pydantic.
All configuration is loaded from environment variables with sensible defaults.

Usage:
    from packages.config.settings import get_settings

    settings = get_settings()
    print(settings.DATABASE_URL)
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings have sensible defaults for local development.
    Override via .env file or environment variables in production.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "RAG Enterprise"
    APP_VERSION: str = "10.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://rag:rag@localhost:15432/rag_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:16379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # Qdrant (Vector DB)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 16333
    QDRANT_COLLECTION: str = "rag_products"
    QDRANT_VECTOR_SIZE: int = 384

    # ClickHouse (Analytics)
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 8123
    CLICKHOUSE_DATABASE: str = "rag_analytics"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_EVENTS: str = "rag_events"

    # NexaAI / Ollama
    NEXA_MODEL: str = "qwen-1.5:7b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Keycloak
    KEYCLOAK_SERVER_URL: Optional[str] = None
    KEYCLOAK_REALM: str = "rag-enterprise"
    KEYCLOAK_CLIENT_ID: str = "rag-api"
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None

    # Vault
    VAULT_ADDR: Optional[str] = None
    VAULT_TOKEN: Optional[str] = None

    # MinIO (S3-compatible)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "rag-data"
    MINIO_SECURE: bool = False

    # Stripe (Billing)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Observability
    JAEGER_ENABLED: bool = False
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831

    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8001"
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: list[str] = ["pdf", "xlsx", "csv", "txt", "json", "xml"]

    # Search
    DEFAULT_SEARCH_TOP_K: int = 5
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.7

    # WebSocket
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_PING_INTERVAL: int = 20
    WEBSOCKET_PING_TIMEOUT: int = 5


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function is cached to avoid re-loading settings from environment
    on every call. Settings are loaded once and reused.

    Returns:
        Settings: Application settings

    Example:
        >>> from packages.config.settings import get_settings
        >>> settings = get_settings()
        >>> print(settings.DATABASE_URL)
        postgresql://rag:rag@localhost:15432/rag_db
    """
    return Settings()


# Convenience: Import settings directly
settings = get_settings()


__all__ = ["Settings", "get_settings", "settings"]
