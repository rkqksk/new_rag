"""
Personalized Recommendation System

Features:
- User preference profiling from search/click history
- Content-based filtering (attribute matching)
- Personalized search result re-ranking
- Compatibility-aware recommendations (container-cap matching)
- Session-based learning without login
"""

from .user_profile import UserProfile, PreferenceExtractor
from .personalized_recommender import PersonalizedRecommender, RecommendationConfig
from .integrated_service import PersonalizationService

__all__ = [
    'UserProfile',
    'PreferenceExtractor',
    'PersonalizedRecommender',
    'RecommendationConfig',
    'PersonalizationService'
]
