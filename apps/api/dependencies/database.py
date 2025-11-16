"""Database Dependencies"""

from functools import lru_cache

from app.core.config import settings
from app.repositories.postgres_repository import PostgresRepository
from app.repositories.qdrant_repository import QdrantRepository
from app.repositories.redis_repository import RedisRepository


@lru_cache()
def get_qdrant_repo() -> QdrantRepository:
    """Get Qdrant repository instance"""
    return QdrantRepository(host=settings.qdrant.host, port=settings.qdrant.port)


@lru_cache()
def get_redis_repo() -> RedisRepository:
    """Get Redis repository instance"""
    return RedisRepository(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
    )


@lru_cache()
def get_postgres_repo() -> PostgresRepository:
    """Get Postgres repository instance"""
    return PostgresRepository(
        host=settings.database.host,
        port=settings.database.port,
        database=settings.database.database,
        username=settings.database.username,
        password=settings.database.password,
    )
