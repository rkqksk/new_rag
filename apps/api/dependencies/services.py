"""Service Dependencies"""

from functools import lru_cache

from fastapi import Depends

from apps.api.dependencies.database import get_postgres_repo, get_qdrant_repo, get_redis_repo
from apps.api.services.analytics_service import AnalyticsService
from apps.api.services.personalization_service import PersonalizationService
from apps.api.services.search_service import SearchService


@lru_cache()
def get_search_service(
    qdrant_repo=Depends(get_qdrant_repo),
    redis_repo=Depends(get_redis_repo),
    postgres_repo=Depends(get_postgres_repo),
) -> SearchService:
    """Get SearchService instance"""
    return SearchService(
        qdrant_repo=qdrant_repo, redis_repo=redis_repo, postgres_repo=postgres_repo
    )


@lru_cache()
def get_personalization_service(
    redis_repo=Depends(get_redis_repo), postgres_repo=Depends(get_postgres_repo)
) -> PersonalizationService:
    """Get PersonalizationService instance"""
    return PersonalizationService(redis_repo=redis_repo, postgres_repo=postgres_repo)


@lru_cache()
def get_analytics_service(postgres_repo=Depends(get_postgres_repo)) -> AnalyticsService:
    """Get AnalyticsService instance"""
    return AnalyticsService(postgres_repo=postgres_repo)
