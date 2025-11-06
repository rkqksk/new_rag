"""
Advanced Personalization Service

Integrates all advanced personalization features:
1. Adaptive user-specific weights (supplier/compatibility/material focus)
2. Global analytics (keyword ranking, popular products)
3. Strict compatibility filtering (hard filter)
"""

import logging
from typing import Dict, Any, List, Optional
import json

from .user_profile import UserProfile, PreferenceExtractor
from .personalized_recommender import PersonalizedRecommender, RecommendationConfig
from .adaptive_weights import AdaptiveWeightsLearner, UserSearchFocus
from .global_analytics import GlobalAnalytics
from .compatibility_filter import CompatibilityFilter, CompatibilityRules

logger = logging.getLogger(__name__)


class AdvancedPersonalizationService:
    """
    Advanced Personalization Service

    Features:
    1. User-specific adaptive weights (auto-learns user's focus)
    2. Global analytics tracking (all searches and interactions)
    3. Strict compatibility filtering (only compatible products)
    4. Original personalization (preference matching)
    """

    def __init__(
        self,
        database=None,
        redis_client: Optional[Any] = None,
        enable_adaptive_weights: bool = True,
        enable_global_analytics: bool = True,
        enable_compatibility_filter: bool = True,
        compatibility_rules: Optional[CompatibilityRules] = None,
        profile_ttl: int = 86400 * 30  # 30 days
    ):
        """
        Initialize advanced personalization service

        Args:
            database: Database connection for analytics persistence
            redis_client: Redis client for caching
            enable_adaptive_weights: Enable adaptive weights learning
            enable_global_analytics: Enable global analytics tracking
            enable_compatibility_filter: Enable strict compatibility filtering
            compatibility_rules: Compatibility filtering rules
            profile_ttl: Profile TTL in seconds
        """
        self.database = database
        self.redis_client = redis_client
        self.profile_ttl = profile_ttl

        # Feature flags
        self.enable_adaptive_weights = enable_adaptive_weights
        self.enable_global_analytics = enable_global_analytics
        self.enable_compatibility_filter = enable_compatibility_filter

        # In-memory caches
        self.profiles: Dict[str, UserProfile] = {}
        self.focus_profiles: Dict[str, UserSearchFocus] = {}

        # Core components
        self.extractor = PreferenceExtractor()
        self.recommender = PersonalizedRecommender()

        # Advanced components
        if enable_adaptive_weights:
            self.weights_learner = AdaptiveWeightsLearner()
            logger.info("✅ Adaptive weights learning enabled")

        if enable_global_analytics:
            self.analytics = GlobalAnalytics(database=database, redis_client=redis_client)
            logger.info("✅ Global analytics tracking enabled")

        if enable_compatibility_filter:
            self.compat_filter = CompatibilityFilter(rules=compatibility_rules)
            logger.info("✅ Strict compatibility filtering enabled")

        logger.info("✅ AdvancedPersonalizationService initialized")

    def get_or_create_profile(self, session_id: str) -> UserProfile:
        """Get or create user profile"""
        if session_id in self.profiles:
            return self.profiles[session_id]

        # Try to load from Redis
        if self.redis_client:
            profile = self._load_profile_from_redis(session_id)
            if profile:
                self.profiles[session_id] = profile
                return profile

        # Create new
        profile = UserProfile(session_id=session_id)
        self.profiles[session_id] = profile
        return profile

    def get_or_create_focus(self, session_id: str) -> UserSearchFocus:
        """Get or create user search focus profile"""
        if not self.enable_adaptive_weights:
            return UserSearchFocus(session_id=session_id)

        if session_id in self.focus_profiles:
            return self.focus_profiles[session_id]

        # Try to load from Redis
        if self.redis_client:
            focus = self._load_focus_from_redis(session_id)
            if focus:
                self.focus_profiles[session_id] = focus
                return focus

        # Create new
        focus = UserSearchFocus(session_id=session_id)
        self.focus_profiles[session_id] = focus
        return focus

    def track_search(
        self,
        session_id: str,
        query: str,
        results_count: int = 0,
        previous_context: Optional[Dict[str, Any]] = None
    ):
        """
        Track search query

        Args:
            session_id: Session identifier
            query: Search query
            results_count: Number of results returned
            previous_context: Previous search context
        """
        # 1. Update user profile (preference extraction)
        profile = self.get_or_create_profile(session_id)
        self.extractor.update_profile_from_search(profile, query)

        # 2. Update search focus (adaptive weights)
        if self.enable_adaptive_weights:
            focus = self.get_or_create_focus(session_id)
            self.weights_learner.update_focus(focus, query)

            # Persist focus
            if self.redis_client:
                self._persist_focus_to_redis(focus)

        # 3. Track in global analytics
        if self.enable_global_analytics:
            self.analytics.track_search(
                session_id=session_id,
                query=query,
                results_count=results_count,
                previous_context=previous_context
            )

        # Persist profile
        if self.redis_client:
            self._persist_profile_to_redis(profile)

        logger.debug(f"Tracked search: {session_id} -> '{query}'")

    def track_view(self, session_id: str, product_id: str, product: Dict[str, Any], search_context: Optional[str] = None):
        """Track product view"""
        profile = self.get_or_create_profile(session_id)
        self.extractor.update_profile_from_view(profile, product_id, product)

        if self.enable_global_analytics:
            self.analytics.track_product_event(
                session_id=session_id,
                product_id=product_id,
                event_type='view',
                product=product,
                search_context=search_context
            )

        if self.redis_client:
            self._persist_profile_to_redis(profile)

    def track_click(self, session_id: str, product_id: str, product: Dict[str, Any], search_context: Optional[str] = None):
        """Track product click"""
        profile = self.get_or_create_profile(session_id)
        self.extractor.update_profile_from_click(profile, product_id, product)

        if self.enable_global_analytics:
            self.analytics.track_product_event(
                session_id=session_id,
                product_id=product_id,
                event_type='click',
                product=product,
                search_context=search_context
            )

        if self.redis_client:
            self._persist_profile_to_redis(profile)

    def track_bookmark(self, session_id: str, product_id: str, product: Dict[str, Any]):
        """Track product bookmark"""
        profile = self.get_or_create_profile(session_id)
        self.extractor.update_profile_from_bookmark(profile, product_id, product)

        if self.enable_global_analytics:
            self.analytics.track_product_event(
                session_id=session_id,
                product_id=product_id,
                event_type='bookmark',
                product=product
            )

        if self.redis_client:
            self._persist_profile_to_redis(profile)

    def personalize_search_results(
        self,
        session_id: str,
        results: List[Dict[str, Any]],
        query: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Personalize search results with all advanced features

        Args:
            session_id: Session identifier
            results: Search results
            query: Optional search query
            top_k: Optional result limit

        Returns:
            Personalized and filtered results
        """
        if not results:
            return results

        profile = self.get_or_create_profile(session_id)

        # 1. Apply strict compatibility filter
        if self.enable_compatibility_filter and profile.interaction_count > 0:
            compat_context = self.compat_filter.extract_compatibility_context(profile)
            results = self.compat_filter.filter_by_compatibility(
                results=results,
                user_context=compat_context,
                query=query
            )

        if not results:
            logger.warning("No results after compatibility filter")
            return []

        # 2. Get adaptive weights (if enabled)
        recommendation_config = None
        if self.enable_adaptive_weights:
            focus = self.get_or_create_focus(session_id)
            if focus.total_searches > 0:
                adaptive_weights = self.weights_learner.get_adaptive_weights(focus)
                recommendation_config = RecommendationConfig(**adaptive_weights)
                logger.debug(f"Using adaptive weights for {focus.get_dominant_focus()} focus")

        # 3. Create recommender with adaptive weights
        if recommendation_config:
            recommender = PersonalizedRecommender(
                config=recommendation_config,
                preference_extractor=self.extractor
            )
        else:
            recommender = self.recommender

        # 4. Re-rank with personalization
        personalized = recommender.rerank(
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

        # Apply compatibility filter first
        if self.enable_compatibility_filter and profile.interaction_count > 0:
            compat_context = self.compat_filter.extract_compatibility_context(profile)
            all_products = self.compat_filter.filter_by_compatibility(
                results=all_products,
                user_context=compat_context
            )

        # Get adaptive weights
        if self.enable_adaptive_weights:
            focus = self.get_or_create_focus(session_id)
            if focus.total_searches > 0:
                adaptive_weights = self.weights_learner.get_adaptive_weights(focus)
                config = RecommendationConfig(**adaptive_weights)
                recommender = PersonalizedRecommender(config=config, preference_extractor=self.extractor)
            else:
                recommender = self.recommender
        else:
            recommender = self.recommender

        # Get recommendations
        recommendations = recommender.get_recommendations(
            profile=profile,
            all_products=all_products,
            top_k=top_k,
            category_filter=category_filter
        )

        return recommendations

    def explain_recommendation(self, session_id: str, result: Dict[str, Any]) -> str:
        """Explain why a product was recommended"""
        profile = self.get_or_create_profile(session_id)
        return self.recommender.explain_recommendation(result, profile)

    def get_user_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user summary

        Returns:
            Dictionary with profile, focus, and preferences
        """
        profile = self.get_or_create_profile(session_id)

        summary = {
            'session_id': session_id,
            'interactions': profile.interaction_count,
            'preferences': {
                'capacity': profile.get_top_preferences('capacity', top_k=3),
                'material': profile.get_top_preferences('material', top_k=3),
                'neck': profile.get_top_preferences('neck', top_k=3),
                'category': profile.get_top_preferences('category', top_k=3)
            },
            'history': {
                'searches': len(profile.search_queries),
                'viewed': len(profile.viewed_products),
                'clicked': len(profile.clicked_products),
                'bookmarked': len(profile.bookmarked_products)
            }
        }

        # Add focus if enabled
        if self.enable_adaptive_weights:
            focus = self.get_or_create_focus(session_id)
            summary['focus'] = {
                'dominant': focus.get_dominant_focus(),
                'scores': {
                    'supplier': focus.supplier_focus,
                    'compatibility': focus.compatibility_focus,
                    'material': focus.material_focus,
                    'price': focus.price_focus,
                    'category': focus.category_focus,
                    'specification': focus.specification_focus
                }
            }

        return summary

    def get_global_analytics_summary(self) -> Dict[str, Any]:
        """Get global analytics summary"""
        if not self.enable_global_analytics:
            return {'error': 'Global analytics disabled'}

        return self.analytics.get_analytics_summary()

    def get_top_keywords(self, limit: int = 20) -> List[tuple]:
        """Get top keywords globally"""
        if not self.enable_global_analytics:
            return []

        return self.analytics.get_top_keywords(limit=limit)

    def get_top_products(self, limit: int = 20, metric: str = 'click') -> List[tuple]:
        """Get top products globally"""
        if not self.enable_global_analytics:
            return []

        return self.analytics.get_top_products(limit=limit, metric=metric)

    def get_trending_queries(self, limit: int = 10) -> List[tuple]:
        """Get trending queries"""
        if not self.enable_global_analytics:
            return []

        return self.analytics.get_trending_queries(limit=limit)

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

    def _persist_focus_to_redis(self, focus: UserSearchFocus):
        """Persist focus to Redis"""
        if not self.redis_client:
            return

        try:
            key = f"user_focus:{focus.session_id}"
            data = json.dumps(focus.to_dict())
            self.redis_client.setex(key, self.profile_ttl, data)
        except Exception as e:
            logger.error(f"Failed to persist focus: {e}")

    def _load_focus_from_redis(self, session_id: str) -> Optional[UserSearchFocus]:
        """Load focus from Redis"""
        if not self.redis_client:
            return None

        try:
            key = f"user_focus:{session_id}"
            data = self.redis_client.get(key)
            if data:
                focus_dict = json.loads(data)
                return UserSearchFocus.from_dict(focus_dict)
        except Exception as e:
            logger.error(f"Failed to load focus: {e}")

        return None

    def __repr__(self):
        features = []
        if self.enable_adaptive_weights:
            features.append("adaptive_weights")
        if self.enable_global_analytics:
            features.append("global_analytics")
        if self.enable_compatibility_filter:
            features.append("compatibility_filter")

        return f"AdvancedPersonalizationService(profiles={len(self.profiles)}, features=[{', '.join(features)}])"


# Usage example
"""
from src.core.recommendation import AdvancedPersonalizationService, CompatibilityRules

# Initialize with all features enabled
service = AdvancedPersonalizationService(
    database=db,
    redis_client=redis,
    enable_adaptive_weights=True,
    enable_global_analytics=True,
    enable_compatibility_filter=True,
    compatibility_rules=CompatibilityRules(strict_neck_matching=True)
)

# User searches
service.track_search(session_id, "춘진 유리병", results_count=15)
service.track_search(session_id, "20파이 캡", results_count=8, previous_context={'last_query': '춘진 유리병'})

# System learns:
# 1. User is supplier-focused (searches include "춘진")
# 2. User prefers glass material
# 3. User has 20파이 neck context
# 4. Global analytics tracks "춘진", "유리병", "20파이", "캡" keywords

# User clicks product
product = {'id': 'p1', 'name': '춘진 유리병 50ml 20파이', 'neck': '20파이', 'material': 'glass'}
service.track_click(session_id, 'p1', product, search_context="춘진 유리병")

# Next search: "캡"
results = vector_search("캡")  # Returns all caps

# Personalize results
personalized = service.personalize_search_results(session_id, results, query="캡")

# Results:
# 1. ONLY 20파이 caps (strict compatibility filter)
# 2. Glass-compatible caps prioritized (material preference)
# 3. 춘진 supplier caps boosted (supplier focus)

# Get global analytics
summary = service.get_global_analytics_summary()
# Shows top keywords: "춘진", "유리병", "20파이", "캡"
# Shows popular products across all users
# Shows trending queries

top_keywords = service.get_top_keywords(limit=10)
# [('50ml', 120), ('PET', 95), ('20파이', 80), ...]
"""
