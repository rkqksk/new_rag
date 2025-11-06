"""
Integrated Personalization Service

Combines ConversationMemory with PersonalizedRecommender
"""

import logging
from typing import Dict, Any, List, Optional
import json

from .user_profile import UserProfile, PreferenceExtractor
from .personalized_recommender import PersonalizedRecommender, RecommendationConfig

logger = logging.getLogger(__name__)


class PersonalizationService:
    """
    Integrated Personalization Service

    Manages user profiles and provides personalized recommendations

    Features:
    - Session-based user profiling (no login required)
    - Automatic preference extraction from interactions
    - Personalized search result re-ranking
    - Redis persistence
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        recommendation_config: Optional[RecommendationConfig] = None,
        profile_ttl: int = 86400 * 30  # 30 days
    ):
        """
        Initialize personalization service

        Args:
            redis_client: Optional Redis client for persistence
            recommendation_config: Recommendation configuration
            profile_ttl: Profile TTL in seconds (default 30 days)
        """
        self.redis_client = redis_client
        self.profile_ttl = profile_ttl

        # In-memory profile cache
        self.profiles: Dict[str, UserProfile] = {}

        # Components
        self.extractor = PreferenceExtractor()
        self.recommender = PersonalizedRecommender(
            config=recommendation_config,
            preference_extractor=self.extractor
        )

        logger.info("✅ PersonalizationService initialized")

    def get_or_create_profile(self, session_id: str) -> UserProfile:
        """
        Get existing profile or create new one

        Args:
            session_id: Session identifier

        Returns:
            User profile
        """
        # Check in-memory cache
        if session_id in self.profiles:
            return self.profiles[session_id]

        # Try to load from Redis
        if self.redis_client:
            profile = self._load_profile_from_redis(session_id)
            if profile:
                self.profiles[session_id] = profile
                return profile

        # Create new profile
        profile = UserProfile(session_id=session_id)
        self.profiles[session_id] = profile

        logger.debug(f"Created new profile: {session_id}")

        return profile

    def track_search(
        self,
        session_id: str,
        query: str
    ):
        """
        Track search query

        Args:
            session_id: Session identifier
            query: Search query
        """
        profile = self.get_or_create_profile(session_id)
        self.extractor.update_profile_from_search(profile, query)

        # Persist to Redis
        if self.redis_client:
            self._persist_profile_to_redis(profile)

        logger.debug(f"Tracked search: {session_id} -> {query}")

    def track_view(
        self,
        session_id: str,
        product_id: str,
        product: Dict[str, Any]
    ):
        """
        Track product view

        Args:
            session_id: Session identifier
            product_id: Product ID
            product: Product data
        """
        profile = self.get_or_create_profile(session_id)
        self.extractor.update_profile_from_view(profile, product_id, product)

        # Persist to Redis
        if self.redis_client:
            self._persist_profile_to_redis(profile)

        logger.debug(f"Tracked view: {session_id} -> {product_id}")

    def track_click(
        self,
        session_id: str,
        product_id: str,
        product: Dict[str, Any]
    ):
        """
        Track product click

        Args:
            session_id: Session identifier
            product_id: Product ID
            product: Product data
        """
        profile = self.get_or_create_profile(session_id)
        self.extractor.update_profile_from_click(profile, product_id, product)

        # Persist to Redis
        if self.redis_client:
            self._persist_profile_to_redis(profile)

        logger.debug(f"Tracked click: {session_id} -> {product_id}")

    def track_bookmark(
        self,
        session_id: str,
        product_id: str,
        product: Dict[str, Any]
    ):
        """
        Track product bookmark

        Args:
            session_id: Session identifier
            product_id: Product ID
            product: Product data
        """
        profile = self.get_or_create_profile(session_id)
        self.extractor.update_profile_from_bookmark(profile, product_id, product)

        # Persist to Redis
        if self.redis_client:
            self._persist_profile_to_redis(profile)

        logger.debug(f"Tracked bookmark: {session_id} -> {product_id}")

    def personalize_search_results(
        self,
        session_id: str,
        results: List[Dict[str, Any]],
        query: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Personalize search results

        Args:
            session_id: Session identifier
            results: Search results
            query: Optional search query
            top_k: Optional result limit

        Returns:
            Personalized results
        """
        profile = self.get_or_create_profile(session_id)

        # Re-rank with personalization
        personalized = self.recommender.rerank(
            results=results,
            profile=profile,
            query=query,
            top_k=top_k
        )

        return personalized

    def get_recommendations(
        self,
        session_id: str,
        all_products: List[Dict[str, Any]],
        top_k: int = 10,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations

        Args:
            session_id: Session identifier
            all_products: All available products
            top_k: Number of recommendations
            category_filter: Optional category filter

        Returns:
            Recommended products
        """
        profile = self.get_or_create_profile(session_id)

        recommendations = self.recommender.get_recommendations(
            profile=profile,
            all_products=all_products,
            top_k=top_k,
            category_filter=category_filter
        )

        return recommendations

    def explain_recommendation(
        self,
        session_id: str,
        result: Dict[str, Any]
    ) -> str:
        """
        Explain why a product was recommended

        Args:
            session_id: Session identifier
            result: Recommended result

        Returns:
            Explanation string
        """
        profile = self.get_or_create_profile(session_id)
        return self.recommender.explain_recommendation(result, profile)

    def get_profile_summary(self, session_id: str) -> str:
        """
        Get human-readable profile summary

        Args:
            session_id: Session identifier

        Returns:
            Profile summary
        """
        profile = self.get_or_create_profile(session_id)
        return self.extractor.get_profile_summary(profile)

    def _persist_profile_to_redis(self, profile: UserProfile):
        """Persist profile to Redis"""
        if not self.redis_client:
            return

        try:
            key = f"user_profile:{profile.session_id}"
            data = json.dumps(profile.to_dict())
            self.redis_client.setex(key, self.profile_ttl, data)

        except Exception as e:
            logger.error(f"Failed to persist profile: {e}")

    def _load_profile_from_redis(self, session_id: str) -> Optional[UserProfile]:
        """Load profile from Redis"""
        if not self.redis_client:
            return None

        try:
            key = f"user_profile:{session_id}"
            data = self.redis_client.get(key)

            if data:
                profile_dict = json.loads(data)
                return UserProfile.from_dict(profile_dict)

        except Exception as e:
            logger.error(f"Failed to load profile: {e}")

        return None

    def clear_profile(self, session_id: str):
        """
        Clear user profile

        Args:
            session_id: Session identifier
        """
        # Remove from memory
        if session_id in self.profiles:
            del self.profiles[session_id]

        # Remove from Redis
        if self.redis_client:
            key = f"user_profile:{session_id}"
            self.redis_client.delete(key)

        logger.info(f"Cleared profile: {session_id}")

    def __repr__(self):
        return f"PersonalizationService(profiles={len(self.profiles)})"


# Usage example with FastAPI
"""
from fastapi import FastAPI, Request
from src.core.recommendation import PersonalizationService

app = FastAPI()
personalization = PersonalizationService(redis_client=redis)

@app.post("/search")
async def search(request: Request):
    session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')
    query = request.json().get('query')

    # Track search
    personalization.track_search(session_id, query)

    # Get search results
    results = vector_search(query)

    # Personalize results
    personalized_results = personalization.personalize_search_results(
        session_id=session_id,
        results=results,
        query=query,
        top_k=20
    )

    return {'results': personalized_results}

@app.post("/track/click")
async def track_click(request: Request):
    session_id = request.cookies.get('session_id')
    product_id = request.json().get('product_id')
    product = request.json().get('product')

    # Track click
    personalization.track_click(session_id, product_id, product)

    return {'status': 'ok'}

@app.get("/recommendations")
async def get_recommendations(request: Request):
    session_id = request.cookies.get('session_id')

    # Get all products
    all_products = load_all_products()

    # Get personalized recommendations
    recommendations = personalization.get_recommendations(
        session_id=session_id,
        all_products=all_products,
        top_k=10
    )

    # Add explanations
    for rec in recommendations:
        rec['explanation'] = personalization.explain_recommendation(session_id, rec)

    return {'recommendations': recommendations}

@app.get("/profile")
async def get_profile(request: Request):
    session_id = request.cookies.get('session_id')

    summary = personalization.get_profile_summary(session_id)

    return {'profile': summary}
"""
