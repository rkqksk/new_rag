"""
Personalized Recommender

Re-ranks search results based on user preferences
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .user_profile import PreferenceExtractor, UserProfile

logger = logging.getLogger(__name__)


@dataclass
class RecommendationConfig:
    """Configuration for personalized recommendation"""

    # Scoring weights
    vector_score_weight: float = 0.6  # Weight for original vector similarity
    preference_score_weight: float = 0.4  # Weight for preference matching

    # Attribute importance
    capacity_importance: float = 1.0
    material_importance: float = 0.8
    neck_importance: float = 0.9
    category_importance: float = 0.7
    supplier_importance: float = 0.5  # NEW: For adaptive weights
    price_importance: float = 0.6  # NEW: For adaptive weights

    # Compatibility
    enable_compatibility_boost: bool = True
    compatibility_boost: float = 0.2

    # Diversity
    enable_diversity: bool = False
    diversity_penalty: float = 0.1

    # Recency boost
    enable_recency_boost: bool = True
    viewed_penalty: float = 0.1  # Reduce score for already viewed items
    clicked_boost: float = 0.1  # Boost previously clicked items


class PersonalizedRecommender:
    """
    Personalized Search Recommender

    Features:
    - Content-based preference matching
    - Compatibility-aware recommendations (container-cap)
    - Re-ranking with fusion scoring
    - Diversity promotion (optional)
    """

    def __init__(
        self,
        config: Optional[RecommendationConfig] = None,
        preference_extractor: Optional[PreferenceExtractor] = None,
    ):
        """
        Initialize personalized recommender

        Args:
            config: Recommendation configuration
            preference_extractor: Preference extractor instance
        """
        self.config = config or RecommendationConfig()
        self.extractor = preference_extractor or PreferenceExtractor()

        logger.info("✅ PersonalizedRecommender initialized")

    def rerank(
        self,
        results: List[Dict[str, Any]],
        profile: UserProfile,
        query: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results based on user preferences

        Args:
            results: Search results from vector search
            profile: User profile with preferences
            query: Optional search query for context
            top_k: Optional limit on results

        Returns:
            Re-ranked results with personalized scores
        """
        if not results:
            return results

        if profile.interaction_count == 0:
            # No personalization for new users
            logger.debug("No profile history, returning original results")
            return results[:top_k] if top_k else results

        # Calculate personalized scores
        scored_results = []

        for result in results:
            # Original vector similarity score
            vector_score = result.get("score", 0.0)

            # Calculate preference score
            preference_score = self._calculate_preference_score(result, profile)

            # Calculate compatibility boost
            compatibility_boost = 0.0
            if self.config.enable_compatibility_boost:
                compatibility_boost = self._calculate_compatibility_boost(result, profile)

            # Calculate recency adjustment
            recency_adjustment = 0.0
            if self.config.enable_recency_boost:
                recency_adjustment = self._calculate_recency_adjustment(result, profile)

            # Fuse scores
            final_score = (
                self.config.vector_score_weight * vector_score
                + self.config.preference_score_weight * preference_score
                + compatibility_boost
                + recency_adjustment
            )

            # Add personalization metadata
            result_copy = result.copy()
            result_copy["personalized_score"] = final_score
            result_copy["original_score"] = vector_score
            result_copy["preference_score"] = preference_score
            result_copy["compatibility_boost"] = compatibility_boost
            result_copy["recency_adjustment"] = recency_adjustment

            scored_results.append(result_copy)

        # Sort by personalized score
        scored_results.sort(key=lambda x: x["personalized_score"], reverse=True)

        # Apply diversity (optional)
        if self.config.enable_diversity:
            scored_results = self._apply_diversity(scored_results, profile)

        # Limit results
        if top_k:
            scored_results = scored_results[:top_k]

        logger.debug(f"Re-ranked {len(results)} results with personalization")

        return scored_results

    def _calculate_preference_score(self, result: Dict[str, Any], profile: UserProfile) -> float:
        """
        Calculate preference matching score

        Args:
            result: Search result
            profile: User profile

        Returns:
            Preference score (0.0 - 1.0)
        """
        scores = []

        # Capacity matching
        capacity = result.get("capacity")
        if capacity:
            weight = profile.get_preference_weight("capacity", capacity)
            if weight > 0:
                scores.append(weight * self.config.capacity_importance)

        # Material matching
        material = result.get("material")
        if material:
            weight = profile.get_preference_weight("material", material)
            if weight > 0:
                scores.append(weight * self.config.material_importance)

        # Neck matching
        neck = result.get("neck")
        if neck:
            weight = profile.get_preference_weight("neck", neck)
            if weight > 0:
                scores.append(weight * self.config.neck_importance)

        # Category matching
        category = result.get("category")
        if category:
            weight = profile.get_preference_weight("category", category)
            if weight > 0:
                scores.append(weight * self.config.category_importance)

        # Average of matched attributes
        if scores:
            return float(np.mean(scores))
        else:
            return 0.0

    def _calculate_compatibility_boost(self, result: Dict[str, Any], profile: UserProfile) -> float:
        """
        Calculate compatibility boost for container-cap matching

        Example:
        - User viewed 50ml PET bottle with 20파이 neck
        - User now searches for cap
        - Boost caps with 20파이 neck

        Args:
            result: Search result
            profile: User profile

        Returns:
            Compatibility boost score
        """
        boost = 0.0

        result_category = result.get("category", "")
        result_neck = result.get("neck")

        # If searching for Cap/Pump and user has Bottle/Jar history
        if result_category in ["Cap", "Pump"]:
            # Check if neck matches previously viewed containers
            if result_neck:
                # Check if user has strong preference for this neck size
                neck_weight = profile.get_preference_weight("neck", result_neck)
                if neck_weight > 0.5:  # Strong preference
                    boost += self.config.compatibility_boost
                    logger.debug(f"Compatibility boost: {result_neck} matches user preference")

        # If searching for Bottle/Jar and user has Cap/Pump history
        elif result_category in ["Bottle", "Jar"]:
            if result_neck:
                # Check if neck matches previously viewed caps
                neck_weight = profile.get_preference_weight("neck", result_neck)
                if neck_weight > 0.5:
                    boost += self.config.compatibility_boost
                    logger.debug(f"Compatibility boost: {result_neck} matches user preference")

        return boost

    def _calculate_recency_adjustment(self, result: Dict[str, Any], profile: UserProfile) -> float:
        """
        Calculate recency-based adjustment

        - Penalty for already viewed (avoid showing same items)
        - Boost for previously clicked (user showed interest)

        Args:
            result: Search result
            profile: User profile

        Returns:
            Recency adjustment
        """
        adjustment = 0.0

        product_id = result.get("id") or result.get("product_id")

        if not product_id:
            return adjustment

        # Penalty for viewed items (user already saw this)
        if product_id in profile.viewed_products:
            adjustment -= self.config.viewed_penalty

        # Boost for clicked items (user showed interest)
        if product_id in profile.clicked_products:
            adjustment += self.config.clicked_boost

        # Strong boost for bookmarked items
        if product_id in profile.bookmarked_products:
            adjustment += 0.2

        return adjustment

    def _apply_diversity(
        self, results: List[Dict[str, Any]], profile: UserProfile
    ) -> List[Dict[str, Any]]:
        """
        Apply diversity to prevent showing too many similar items

        Uses Maximal Marginal Relevance (MMR) approach

        Args:
            results: Ranked results
            profile: User profile

        Returns:
            Diversified results
        """
        if len(results) <= 1:
            return results

        diversified = [results[0]]  # Start with top result
        remaining = results[1:]

        while remaining and len(diversified) < len(results):
            # Find item with max (relevance - similarity_to_selected)
            best_idx = 0
            best_score = -float("inf")

            for idx, candidate in enumerate(remaining):
                # Relevance score
                relevance = candidate["personalized_score"]

                # Similarity to already selected items
                similarity = self._calculate_similarity_to_set(candidate, diversified)

                # MMR score
                mmr_score = relevance - self.config.diversity_penalty * similarity

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            # Add best candidate
            diversified.append(remaining.pop(best_idx))

        return diversified

    def _calculate_similarity_to_set(
        self, candidate: Dict[str, Any], selected: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate similarity between candidate and selected items

        Args:
            candidate: Candidate item
            selected: Already selected items

        Returns:
            Average similarity (0.0 - 1.0)
        """
        if not selected:
            return 0.0

        similarities = []

        for item in selected:
            sim = 0.0
            matches = 0

            # Check attribute overlap
            for attr in ["capacity", "material", "neck", "category"]:
                if candidate.get(attr) and item.get(attr):
                    matches += 1
                    if candidate[attr] == item[attr]:
                        sim += 1.0

            if matches > 0:
                similarities.append(sim / matches)

        return float(np.mean(similarities)) if similarities else 0.0

    def get_recommendations(
        self,
        profile: UserProfile,
        all_products: List[Dict[str, Any]],
        top_k: int = 10,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations without query

        Use this for "Recommended for you" feature

        Args:
            profile: User profile
            all_products: All available products
            top_k: Number of recommendations
            category_filter: Optional category filter

        Returns:
            Top K recommended products
        """
        if profile.interaction_count == 0:
            logger.debug("No profile history, returning popular items")
            return all_products[:top_k]

        # Filter by category if specified
        products = all_products
        if category_filter:
            products = [p for p in products if p.get("category") == category_filter]

        # Calculate preference scores
        scored_products = []

        for product in products:
            # Skip already viewed items
            product_id = product.get("id") or product.get("product_id")
            if product_id in profile.viewed_products:
                continue

            # Calculate preference score
            score = self._calculate_preference_score(product, profile)

            # Add compatibility boost
            if self.config.enable_compatibility_boost:
                score += self._calculate_compatibility_boost(product, profile)

            product_copy = product.copy()
            product_copy["recommendation_score"] = score

            scored_products.append(product_copy)

        # Sort by score
        scored_products.sort(key=lambda x: x["recommendation_score"], reverse=True)

        return scored_products[:top_k]

    def explain_recommendation(self, result: Dict[str, Any], profile: UserProfile) -> str:
        """
        Generate human-readable explanation for recommendation

        Args:
            result: Recommended result
            profile: User profile

        Returns:
            Explanation string
        """
        reasons = []

        # Check attribute matches
        capacity = result.get("capacity")
        if capacity:
            weight = profile.get_preference_weight("capacity", capacity)
            if weight > 0.5:
                reasons.append(f"용량 {capacity}을(를) 선호하시네요")

        material = result.get("material")
        if material:
            weight = profile.get_preference_weight("material", material)
            if weight > 0.5:
                reasons.append(f"재질 {material}을(를) 자주 찾으셨어요")

        neck = result.get("neck")
        if neck:
            weight = profile.get_preference_weight("neck", neck)
            if weight > 0.5:
                reasons.append(f"넥 사이즈 {neck}와(과) 호환됩니다")

        category = result.get("category")
        if category:
            weight = profile.get_preference_weight("category", category)
            if weight > 0.5:
                reasons.append(f"{category} 카테고리를 관심있어 하시네요")

        # Compatibility
        if self.config.enable_compatibility_boost:
            boost = self._calculate_compatibility_boost(result, profile)
            if boost > 0:
                reasons.append("이전에 본 제품과 호환됩니다")

        # Previous interaction
        product_id = result.get("id") or result.get("product_id")
        if product_id and product_id in profile.clicked_products:
            reasons.append("이전에 관심을 보이셨습니다")

        if not reasons:
            return "검색 기록을 바탕으로 추천드립니다"

        return " • ".join(reasons)


# Usage example
"""
# Initialize
recommender = PersonalizedRecommender()
profile = UserProfile(session_id="sess_123")

# User has search history
extractor = PreferenceExtractor()
extractor.update_profile_from_search(profile, "50ml PET 병")

# Click on product
product = {'id': 'p1', 'capacity': '50ml', 'material': 'PET', 'neck': '20파이', 'category': 'Bottle'}
extractor.update_profile_from_click(profile, 'p1', product)

# Now user searches for "캡"
search_results = [
    {'id': 'c1', 'name': '20파이 캡', 'neck': '20파이', 'category': 'Cap', 'score': 0.85},
    {'id': 'c2', 'name': '24파이 캡', 'neck': '24파이', 'category': 'Cap', 'score': 0.87},
    {'id': 'c3', 'name': '20파이 펌프', 'neck': '20파이', 'category': 'Pump', 'score': 0.80}
]

# Re-rank with personalization
personalized = recommender.rerank(search_results, profile)

# Result:
# 1. c1 (20파이 캡) - personalized_score: 0.92 (compatibility boost!)
# 2. c2 (24파이 캡) - personalized_score: 0.87 (original)
# 3. c3 (20파이 펌프) - personalized_score: 0.88 (compatibility boost)

# Explain
explanation = recommender.explain_recommendation(personalized[0], profile)
# "넥 사이즈 20파이와(과) 호환됩니다 • 이전에 본 제품과 호환됩니다"
"""
