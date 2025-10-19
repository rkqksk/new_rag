"""
Production-Ready Configuration Management with Pydantic Validation

This module provides comprehensive environment variable validation using
Pydantic with environment-specific rules enforcement.

Features:
- Environment-based validation (development, staging, production)
- Automatic type conversion and validation
- Singleton pattern for configuration access
- Production safety checks
- Comprehensive error messages

Usage:
    from app.core.config import get_settings, Environment

    settings = get_settings()
    print(settings.environment)
    print(settings.postgres_dsn)
"""

import os
from enum import Enum
from functools import lru_cache
from typing import List, Optional

from pydantic import (
    Field,
    field_validator,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment enumeration.

    Attributes:
        DEVELOPMENT: Local development with debug mode
        STAGING: Production-like environment for testing
        PRODUCTION: Live production environment
    """
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with comprehensive validation.

    All settings are loaded from environment variables with sensible defaults.
    Production environment enforces stricter validation rules.

    Attributes:
        Organized by category with detailed docstrings
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    app_name: str = Field(
        default="RAG Enterprise",
        description="Application name for logging and monitoring"
    )

    app_version: str = Field(
        default="2.4.0",
        description="Application version"
    )

    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # -------------------------------------------------------------------------
    # API Server Configuration
    # -------------------------------------------------------------------------
    api_host: str = Field(
        default="0.0.0.0",
        description="Server bind address"
    )

    api_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Server port"
    )

    uvicorn_workers: int = Field(
        default=1,
        ge=1,
        le=16,
        description="Number of Uvicorn worker processes"
    )

    uvicorn_timeout_keep_alive: int = Field(
        default=75,
        ge=1,
        description="Keep-alive timeout in seconds"
    )

    uvicorn_backlog: int = Field(
        default=2048,
        ge=128,
        description="Maximum pending connections"
    )

    # -------------------------------------------------------------------------
    # PostgreSQL Database Configuration
    # -------------------------------------------------------------------------
    postgres_host: str = Field(
        default="172.28.0.4",
        description="PostgreSQL host"
    )

    postgres_port: int = Field(
        default=5432,
        ge=1024,
        le=65535,
        description="PostgreSQL port"
    )

    postgres_user: str = Field(
        default="postgres",
        description="PostgreSQL username"
    )

    postgres_password: str = Field(
        description="PostgreSQL password (REQUIRED)"
    )

    postgres_db: str = Field(
        default="rag_enterprise",
        description="PostgreSQL database name"
    )

    postgres_pool_size: int = Field(
        default=10,
        ge=5,
        le=100,
        description="Connection pool size"
    )

    postgres_max_overflow: int = Field(
        default=5,
        ge=0,
        le=50,
        description="Maximum overflow connections"
    )

    postgres_pool_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Connection pool timeout in seconds"
    )

    postgres_pool_recycle: int = Field(
        default=3600,
        ge=-1,
        description="Recycle connections after N seconds (-1 to disable)"
    )

    @computed_field
    @property
    def postgres_dsn(self) -> str:
        """Build PostgreSQL connection string.

        Returns:
            PostgreSQL DSN in format: postgresql://user:pass@host:port/db
        """
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # -------------------------------------------------------------------------
    # Redis Cache Configuration
    # -------------------------------------------------------------------------
    redis_host: str = Field(
        default="172.28.0.3",
        description="Redis host"
    )

    redis_port: int = Field(
        default=6379,
        ge=1024,
        le=65535,
        description="Redis port"
    )

    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database number"
    )

    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password (optional)"
    )

    redis_ttl: int = Field(
        default=3600,
        ge=1,
        description="Default cache TTL in seconds"
    )

    redis_pool_max_connections: int = Field(
        default=50,
        ge=10,
        le=500,
        description="Maximum Redis pool connections"
    )

    redis_pool_min_idle: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Minimum idle connections in pool"
    )

    @computed_field
    @property
    def redis_url(self) -> str:
        """Build Redis connection URL.

        Returns:
            Redis URL in format: redis://[:password@]host:port/db
        """
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:"
                f"{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # -------------------------------------------------------------------------
    # Qdrant Vector Database Configuration
    # -------------------------------------------------------------------------
    qdrant_host: str = Field(
        default="172.28.0.2",
        description="Qdrant host"
    )

    qdrant_http_port: int = Field(
        default=6333,
        ge=1024,
        le=65535,
        description="Qdrant HTTP API port"
    )

    qdrant_grpc_port: int = Field(
        default=6334,
        ge=1024,
        le=65535,
        description="Qdrant gRPC port"
    )

    qdrant_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds"
    )

    qdrant_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts on failure"
    )

    qdrant_api_key: Optional[str] = Field(
        default=None,
        description="Qdrant API key (optional, for Qdrant Cloud)"
    )

    qdrant_collection: str = Field(
        default="rag_enterprise",
        description="Default collection name"
    )

    @computed_field
    @property
    def qdrant_url(self) -> str:
        """Build Qdrant HTTP API URL.

        Returns:
            Qdrant URL in format: http://host:port
        """
        return f"http://{self.qdrant_host}:{self.qdrant_http_port}"

    # -------------------------------------------------------------------------
    # Embedding Model Configuration
    # -------------------------------------------------------------------------
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model name"
    )

    embedding_dim: int = Field(
        default=384,
        ge=128,
        le=4096,
        description="Embedding vector dimension"
    )

    embedding_batch_size: int = Field(
        default=32,
        ge=1,
        le=256,
        description="Batch size for embedding generation"
    )

    embedding_device: str = Field(
        default="cpu",
        description="Device for embedding model (cpu, cuda, mps)"
    )

    # -------------------------------------------------------------------------
    # LLM Configuration
    # -------------------------------------------------------------------------
    ollama_host: str = Field(
        default="localhost",
        description="Ollama server host"
    )

    ollama_port: int = Field(
        default=11434,
        ge=1024,
        le=65535,
        description="Ollama server port"
    )

    ollama_default_model: str = Field(
        default="qwen2.5:7b-instruct-q4_K_M",
        description="Default Ollama model"
    )

    ollama_timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Request timeout in seconds"
    )

    @computed_field
    @property
    def ollama_url(self) -> str:
        """Build Ollama API URL.

        Returns:
            Ollama URL in format: http://host:port
        """
        return f"http://{self.ollama_host}:{self.ollama_port}"

    # -------------------------------------------------------------------------
    # Security Configuration
    # -------------------------------------------------------------------------
    jwt_secret_key: str = Field(
        description="JWT signing secret key (REQUIRED)"
    )

    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )

    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Access token expiration in minutes"
    )

    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Refresh token expiration in days"
    )

    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="CORS allowed origins (comma-separated)"
    )

    @computed_field
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated origins into list.

        Returns:
            List of allowed origin URLs
        """
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # -------------------------------------------------------------------------
    # External API Keys (Optional)
    # -------------------------------------------------------------------------
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Claude API key (optional)"
    )

    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (optional)"
    )

    # -------------------------------------------------------------------------
    # Monitoring & Observability
    # -------------------------------------------------------------------------
    prometheus_port: int = Field(
        default=9090,
        ge=1024,
        le=65535,
        description="Prometheus metrics port"
    )

    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry error tracking DSN"
    )

    sentry_environment: str = Field(
        default="development",
        description="Sentry environment tag"
    )

    sentry_traces_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Percentage of transactions to trace"
    )

    sentry_profiles_sample_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Percentage of profiles to collect"
    )

    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics"
    )

    metrics_path: str = Field(
        default="/metrics",
        description="Prometheus metrics endpoint path"
    )

    # -------------------------------------------------------------------------
    # Performance & Caching
    # -------------------------------------------------------------------------
    cache_ttl_default: int = Field(
        default=3600,
        ge=60,
        description="Default cache TTL in seconds"
    )

    cache_ttl_embeddings: int = Field(
        default=86400,
        ge=3600,
        description="Embedding cache TTL in seconds"
    )

    cache_ttl_search_results: int = Field(
        default=1800,
        ge=300,
        description="Search results cache TTL in seconds"
    )

    max_batch_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Maximum batch size for bulk operations"
    )

    max_upload_size_mb: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum file upload size in megabytes"
    )

    # -------------------------------------------------------------------------
    # Rate Limiting
    # -------------------------------------------------------------------------
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )

    rate_limit_per_minute: int = Field(
        default=60,
        ge=10,
        le=10000,
        description="Maximum requests per minute per IP"
    )

    rate_limit_burst: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Burst size for rate limiting"
    )

    # -------------------------------------------------------------------------
    # Feature Flags
    # -------------------------------------------------------------------------
    enable_swagger: bool = Field(
        default=True,
        description="Enable Swagger UI documentation"
    )

    enable_cors: bool = Field(
        default=True,
        description="Enable CORS middleware"
    )

    enable_compression: bool = Field(
        default=True,
        description="Enable gzip compression"
    )

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v_upper

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, v: str, info) -> str:
        """Validate JWT secret key meets security requirements.

        Requirements:
        - Development: minimum 32 characters
        - Staging: minimum 64 characters
        - Production: minimum 64 characters (enforced)
        """
        environment = info.data.get("environment", Environment.DEVELOPMENT)

        min_length = 32
        if environment in {Environment.STAGING, Environment.PRODUCTION}:
            min_length = 64

        if len(v) < min_length:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {min_length} characters "
                f"for {environment.value} environment (current length: {len(v)})"
            )

        # Additional production checks
        if environment == Environment.PRODUCTION:
            if v == "dev-secret-key-change-in-production-use-openssl-rand-base64-64":
                raise ValueError(
                    "Production environment detected with default JWT secret. "
                    "Generate a secure secret with: openssl rand -base64 64"
                )

        return v

    @field_validator("postgres_password")
    @classmethod
    def validate_postgres_password(cls, v: str, info) -> str:
        """Validate PostgreSQL password meets security requirements."""
        environment = info.data.get("environment", Environment.DEVELOPMENT)

        if not v or v == "your_secure_password_here":
            raise ValueError(
                "POSTGRES_PASSWORD is required. "
                "Set a secure password in your .env file"
            )

        # Production password strength requirements
        if environment == Environment.PRODUCTION:
            if len(v) < 16:
                raise ValueError(
                    "Production PostgreSQL password must be at least 16 characters"
                )
            if v in {"changeme", "postgres", "password", "admin"}:
                raise ValueError(
                    "Production PostgreSQL password is too weak. "
                    "Use a strong, randomly generated password"
                )

        return v

    @field_validator("sentry_traces_sample_rate", "sentry_profiles_sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: float) -> float:
        """Validate sample rate is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Sample rate must be between 0.0 and 1.0, got {v}")
        return v

    @model_validator(mode="after")
    def validate_production_requirements(self) -> "Settings":
        """Enforce production-specific requirements.

        Production requirements:
        - SENTRY_DSN must be configured
        - DEBUG must be False
        - LOG_LEVEL must be WARNING or ERROR
        - ALLOWED_ORIGINS must use HTTPS
        """
        if self.environment != Environment.PRODUCTION:
            return self

        # Sentry DSN required in production
        if not self.sentry_dsn:
            raise ValueError(
                "SENTRY_DSN is required for production environment. "
                "Configure Sentry error tracking for production monitoring."
            )

        # Debug mode must be disabled
        if self.debug:
            raise ValueError(
                "DEBUG mode must be disabled in production. "
                "Set DEBUG=false in your environment"
            )

        # Appropriate log level
        if self.log_level not in {"WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(
                f"Production LOG_LEVEL must be WARNING, ERROR, or CRITICAL. "
                f"Current: {self.log_level}"
            )

        # HTTPS origins in production
        for origin in self.allowed_origins_list:
            if origin.startswith("http://") and "localhost" not in origin:
                raise ValueError(
                    f"Production ALLOWED_ORIGINS must use HTTPS: {origin}. "
                    "HTTP is only allowed for localhost"
                )

        return self

    @model_validator(mode="after")
    def validate_port_conflicts(self) -> "Settings":
        """Ensure no port conflicts between services."""
        ports = {
            "API": self.api_port,
            "PostgreSQL": self.postgres_port,
            "Redis": self.redis_port,
            "Qdrant HTTP": self.qdrant_http_port,
            "Qdrant gRPC": self.qdrant_grpc_port,
            "Prometheus": self.prometheus_port,
            "Ollama": self.ollama_port,
        }

        # Check for duplicate ports
        port_mapping = {}
        for service, port in ports.items():
            if port in port_mapping:
                raise ValueError(
                    f"Port conflict detected: {service} and {port_mapping[port]} "
                    f"both use port {port}"
                )
            port_mapping[port] = service

        return self


# -----------------------------------------------------------------------------
# Singleton Pattern
# -----------------------------------------------------------------------------

@lru_cache()
def get_settings() -> Settings:
    """Get application settings singleton.

    Uses lru_cache to ensure only one Settings instance is created.
    Settings are loaded from environment variables and .env file.

    Returns:
        Settings: Application settings instance

    Raises:
        ValidationError: If configuration validation fails

    Example:
        >>> from app.core.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.environment)
        'development'
    """
    return Settings()


def reset_settings() -> None:
    """Reset settings cache.

    Useful for testing when you need to reload settings with different
    environment variables.

    Example:
        >>> from app.core.config import reset_settings, get_settings
        >>> import os
        >>> os.environ['ENVIRONMENT'] = 'production'
        >>> reset_settings()
        >>> settings = get_settings()  # Reloads with new environment
    """
    get_settings.cache_clear()
