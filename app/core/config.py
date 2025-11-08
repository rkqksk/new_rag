"""Enterprise Configuration Management"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field, validator


class DatabaseConfig(BaseSettings):
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="rag_enterprise", env="DB_NAME")
    username: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")
    pool_size: int = Field(default=20, env="DB_POOL_SIZE")

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        )


class RedisConfig(BaseSettings):
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    max_connections: int = Field(default=50)


class QdrantConfig(BaseSettings):
    host: str = Field(default="localhost", env="QDRANT_HOST")
    port: int = Field(default=6333, env="QDRANT_PORT")
    products_collection: str = Field(default="products_multimodal")


class DebugConfig(BaseSettings):
    """Debug and observability settings"""

    enabled: bool = Field(default=False, env="DEBUG_ENABLED")
    log_requests: bool = Field(default=True, env="DEBUG_LOG_REQUESTS")
    log_responses: bool = Field(default=False, env="DEBUG_LOG_RESPONSES")  # Can be verbose
    log_sql: bool = Field(default=True, env="DEBUG_LOG_SQL")
    log_cache: bool = Field(default=True, env="DEBUG_LOG_CACHE")
    profile_requests: bool = Field(default=True, env="DEBUG_PROFILE_REQUESTS")
    slow_request_threshold_ms: int = Field(default=500, env="DEBUG_SLOW_REQUEST_MS")
    explain_search: bool = Field(default=True, env="DEBUG_EXPLAIN_SEARCH")


class Settings(BaseSettings):
    app_name: str = Field(default="RAG Enterprise API")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    api_prefix: str = Field(default="/api/v1")

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    debug_config: DebugConfig = Field(default_factory=DebugConfig)

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
