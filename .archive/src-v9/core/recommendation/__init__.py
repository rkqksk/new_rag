"""
Personalized Recommendation System

Features:
- User preference profiling from search/click history
- Content-based filtering (attribute matching)
- Personalized search result re-ranking
- Compatibility-aware recommendations (container-cap matching)
- Session-based learning without login
"""

from .adaptive_weights import AdaptiveWeightsLearner, UserSearchFocus
from .advanced_personalization_service import AdvancedPersonalizationService
from .compatibility_filter import CompatibilityFilter, CompatibilityRules
from .global_analytics import GlobalAnalytics
from .integrated_service import PersonalizationService
from .personalized_recommender import PersonalizedRecommender, RecommendationConfig
from .user_profile import PreferenceExtractor, UserProfile

__all__ = [
    "UserProfile",
    "PreferenceExtractor",
    "PersonalizedRecommender",
    "RecommendationConfig",
    "PersonalizationService",
    "AdaptiveWeightsLearner",
    "UserSearchFocus",
    "GlobalAnalytics",
    "CompatibilityFilter",
    "CompatibilityRules",
    "AdvancedPersonalizationService",
]
