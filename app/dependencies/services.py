"""Service Dependencies"""
from functools import lru_cache
from fastapi import Depends

from app.services.search_service import SearchService
from app.services.personalization_service import PersonalizationService
from app.services.analytics_service import AnalyticsService
from app.dependencies.database import (
    get_qdrant_repo,
    get_redis_repo,
    get_postgres_repo
)

@lru_cache()
def get_search_service(
    qdrant_repo=Depends(get_qdrant_repo),
    redis_repo=Depends(get_redis_repo),
    postgres_repo=Depends(get_postgres_repo)
) -> SearchService:
    """Get SearchService instance"""
    return SearchService(
        qdrant_repo=qdrant_repo,
        redis_repo=redis_repo,
        postgres_repo=postgres_repo
    )

@lru_cache()
def get_personalization_service(
    redis_repo=Depends(get_redis_repo),
    postgres_repo=Depends(get_postgres_repo)
) -> PersonalizationService:
    """Get PersonalizationService instance"""
    return PersonalizationService(
        redis_repo=redis_repo,
        postgres_repo=postgres_repo
    )

@lru_cache()
def get_analytics_service(
    postgres_repo=Depends(get_postgres_repo)
) -> AnalyticsService:
    """Get AnalyticsService instance"""
    return AnalyticsService(
        postgres_repo=postgres_repo
    )
