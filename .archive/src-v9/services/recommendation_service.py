"""
Recommendation Engine Service
Collaborative filtering, content-based, hybrid recommendations
Version: v8.5.0
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import math
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """Recommendation item"""
    item_id: str
    score: float
    reason: str
    metadata: Dict[str, Any]


class RecommendationStrategy:
    """Recommendation strategy enum"""
    COLLABORATIVE = 'collaborative'
    CONTENT_BASED = 'content_based'
    HYBRID = 'hybrid'
    POPULAR = 'popular'
    TRENDING = 'trending'


class RecommendationService:
    """Recommendation engine with multiple strategies"""

    def __init__(self):
        """Initialize recommendation service"""
        # User interactions: user_id -> {item_id: score}
        self.user_interactions: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Item interactions: item_id -> {user_id: score}
        self.item_interactions: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Item features: item_id -> feature_vector
        self.item_features: Dict[str, np.ndarray] = {}

        # Item metadata: item_id -> metadata
        self.item_metadata: Dict[str, Dict[str, Any]] = {}

        # Interaction timestamps: (user_id, item_id) -> timestamp
        self.interaction_times: Dict[Tuple[str, str], datetime] = {}

        # Popularity scores: item_id -> popularity
        self.popularity_scores: Dict[str, float] = defaultdict(float)

        logger.info("Recommendation service initialized")

    def track_interaction(
        self,
        user_id: str,
        item_id: str,
        interaction_type: str = 'view',
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track user-item interaction

        Args:
            user_id: User ID
            item_id: Item ID
            interaction_type: Type of interaction (view, click, purchase, like, etc.)
            score: Optional explicit score (if None, will be calculated from type)
            metadata: Optional interaction metadata
        """
        # Calculate implicit score from interaction type
        if score is None:
            score = self._get_interaction_score(interaction_type)

        # Update user interactions
        current_score = self.user_interactions[user_id].get(item_id, 0)
        self.user_interactions[user_id][item_id] = current_score + score

        # Update item interactions
        current_score = self.item_interactions[item_id].get(user_id, 0)
        self.item_interactions[item_id][user_id] = current_score + score

        # Track timestamp
        self.interaction_times[(user_id, item_id)] = datetime.now()

        # Update popularity
        self.popularity_scores[item_id] += score

        logger.debug(f"Tracked {interaction_type}: user={user_id}, item={item_id}, score={score}")

    def _get_interaction_score(self, interaction_type: str) -> float:
        """Get score for interaction type"""
        scores = {
            'view': 1.0,
            'click': 2.0,
            'add_to_cart': 3.0,
            'like': 4.0,
            'share': 4.0,
            'purchase': 5.0,
            'review': 4.0,
        }
        return scores.get(interaction_type, 1.0)

    def add_item_features(
        self,
        item_id: str,
        features: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add item features for content-based filtering

        Args:
            item_id: Item ID
            features: Feature vector (embeddings)
            metadata: Optional item metadata
        """
        self.item_features[item_id] = features

        if metadata:
            self.item_metadata[item_id] = metadata

    def get_collaborative_recommendations(
        self,
        user_id: str,
        top_k: int = 10,
        min_similarity: float = 0.1
    ) -> List[Recommendation]:
        """
        Get collaborative filtering recommendations (user-based)

        Args:
            user_id: User ID
            top_k: Number of recommendations
            min_similarity: Minimum user similarity threshold

        Returns:
            List of recommendations
        """
        if user_id not in self.user_interactions:
            logger.warning(f"No interactions found for user {user_id}")
            return self.get_popular_recommendations(top_k)

        user_items = set(self.user_interactions[user_id].keys())

        # Find similar users
        similar_users = self._find_similar_users(user_id, min_similarity)

        if not similar_users:
            logger.info(f"No similar users found for {user_id}")
            return self.get_popular_recommendations(top_k)

        # Aggregate recommendations from similar users
        candidate_scores: Dict[str, float] = defaultdict(float)

        for similar_user, similarity in similar_users:
            for item_id, score in self.user_interactions[similar_user].items():
                # Skip items already interacted with
                if item_id in user_items:
                    continue

                # Weight by user similarity
                candidate_scores[item_id] += score * similarity

        # Sort and return top-k
        recommendations = []
        for item_id, score in sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            recommendations.append(Recommendation(
                item_id=item_id,
                score=score,
                reason='Similar users also liked this',
                metadata=self.item_metadata.get(item_id, {})
            ))

        logger.info(f"Generated {len(recommendations)} collaborative recommendations for {user_id}")

        return recommendations

    def get_content_based_recommendations(
        self,
        user_id: str,
        top_k: int = 10
    ) -> List[Recommendation]:
        """
        Get content-based recommendations

        Args:
            user_id: User ID
            top_k: Number of recommendations

        Returns:
            List of recommendations
        """
        if user_id not in self.user_interactions:
            return []

        if not self.item_features:
            logger.warning("No item features available for content-based filtering")
            return []

        user_items = self.user_interactions[user_id]

        # Build user profile (weighted average of liked item features)
        user_profile = None
        total_weight = 0

        for item_id, score in user_items.items():
            if item_id in self.item_features:
                if user_profile is None:
                    user_profile = self.item_features[item_id] * score
                else:
                    user_profile += self.item_features[item_id] * score
                total_weight += score

        if user_profile is None:
            return []

        user_profile /= total_weight

        # Find similar items
        candidate_scores: Dict[str, float] = {}

        for item_id, features in self.item_features.items():
            # Skip already interacted items
            if item_id in user_items:
                continue

            # Cosine similarity
            similarity = self._cosine_similarity(user_profile, features)
            candidate_scores[item_id] = similarity

        # Sort and return top-k
        recommendations = []
        for item_id, score in sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            recommendations.append(Recommendation(
                item_id=item_id,
                score=score,
                reason='Based on your preferences',
                metadata=self.item_metadata.get(item_id, {})
            ))

        logger.info(f"Generated {len(recommendations)} content-based recommendations for {user_id}")

        return recommendations

    def get_hybrid_recommendations(
        self,
        user_id: str,
        top_k: int = 10,
        collaborative_weight: float = 0.5,
        content_weight: float = 0.5
    ) -> List[Recommendation]:
        """
        Get hybrid recommendations (collaborative + content-based)

        Args:
            user_id: User ID
            top_k: Number of recommendations
            collaborative_weight: Weight for collaborative filtering
            content_weight: Weight for content-based filtering

        Returns:
            List of recommendations
        """
        # Get both types of recommendations
        collab_recs = self.get_collaborative_recommendations(user_id, top_k * 2)
        content_recs = self.get_content_based_recommendations(user_id, top_k * 2)

        # Combine scores
        combined_scores: Dict[str, Tuple[float, str]] = {}

        for rec in collab_recs:
            combined_scores[rec.item_id] = (
                rec.score * collaborative_weight,
                'Similar users liked this'
            )

        for rec in content_recs:
            if rec.item_id in combined_scores:
                # Add to existing score
                existing_score, _ = combined_scores[rec.item_id]
                combined_scores[rec.item_id] = (
                    existing_score + rec.score * content_weight,
                    'Similar users liked this and matches your preferences'
                )
            else:
                combined_scores[rec.item_id] = (
                    rec.score * content_weight,
                    'Matches your preferences'
                )

        # Sort and return top-k
        recommendations = []
        for item_id, (score, reason) in sorted(combined_scores.items(), key=lambda x: x[1][0], reverse=True)[:top_k]:
            recommendations.append(Recommendation(
                item_id=item_id,
                score=score,
                reason=reason,
                metadata=self.item_metadata.get(item_id, {})
            ))

        logger.info(f"Generated {len(recommendations)} hybrid recommendations for {user_id}")

        return recommendations

    def get_popular_recommendations(
        self,
        top_k: int = 10,
        time_window_days: Optional[int] = None
    ) -> List[Recommendation]:
        """
        Get popular items

        Args:
            top_k: Number of recommendations
            time_window_days: Optional time window for trending items

        Returns:
            List of recommendations
        """
        if time_window_days:
            # Trending items within time window
            cutoff = datetime.now() - timedelta(days=time_window_days)

            recent_scores: Dict[str, float] = defaultdict(float)

            for (user_id, item_id), timestamp in self.interaction_times.items():
                if timestamp >= cutoff:
                    score = self.user_interactions[user_id].get(item_id, 0)
                    recent_scores[item_id] += score

            sorted_items = sorted(recent_scores.items(), key=lambda x: x[1], reverse=True)
            reason = f'Trending in last {time_window_days} days'
        else:
            # All-time popular
            sorted_items = sorted(self.popularity_scores.items(), key=lambda x: x[1], reverse=True)
            reason = 'Most popular'

        recommendations = []
        for item_id, score in sorted_items[:top_k]:
            recommendations.append(Recommendation(
                item_id=item_id,
                score=score,
                reason=reason,
                metadata=self.item_metadata.get(item_id, {})
            ))

        logger.info(f"Generated {len(recommendations)} popular recommendations")

        return recommendations

    def get_similar_items(
        self,
        item_id: str,
        top_k: int = 10
    ) -> List[Recommendation]:
        """
        Get similar items (content-based)

        Args:
            item_id: Item ID
            top_k: Number of recommendations

        Returns:
            List of similar items
        """
        if item_id not in self.item_features:
            logger.warning(f"No features found for item {item_id}")
            return []

        target_features = self.item_features[item_id]

        # Calculate similarity with all other items
        similarities: Dict[str, float] = {}

        for other_id, other_features in self.item_features.items():
            if other_id == item_id:
                continue

            similarity = self._cosine_similarity(target_features, other_features)
            similarities[other_id] = similarity

        # Sort and return top-k
        recommendations = []
        for other_id, score in sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            recommendations.append(Recommendation(
                item_id=other_id,
                score=score,
                reason='Similar to this item',
                metadata=self.item_metadata.get(other_id, {})
            ))

        logger.info(f"Generated {len(recommendations)} similar items for {item_id}")

        return recommendations

    def _find_similar_users(
        self,
        user_id: str,
        min_similarity: float = 0.1,
        top_k: int = 50
    ) -> List[Tuple[str, float]]:
        """Find similar users using cosine similarity"""
        if user_id not in self.user_interactions:
            return []

        user_items = self.user_interactions[user_id]

        similarities = []

        for other_id, other_items in self.user_interactions.items():
            if other_id == user_id:
                continue

            # Compute similarity
            similarity = self._user_similarity(user_items, other_items)

            if similarity >= min_similarity:
                similarities.append((other_id, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def _user_similarity(
        self,
        user1_items: Dict[str, float],
        user2_items: Dict[str, float]
    ) -> float:
        """Calculate user similarity (cosine)"""
        common_items = set(user1_items.keys()).intersection(set(user2_items.keys()))

        if not common_items:
            return 0.0

        # Calculate cosine similarity
        dot_product = sum(user1_items[item] * user2_items[item] for item in common_items)

        norm1 = math.sqrt(sum(score ** 2 for score in user1_items.values()))
        norm2 = math.sqrt(sum(score ** 2 for score in user2_items.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get recommendation engine statistics"""
        return {
            'total_users': len(self.user_interactions),
            'total_items': len(self.item_interactions),
            'total_interactions': sum(len(items) for items in self.user_interactions.values()),
            'items_with_features': len(self.item_features),
            'avg_interactions_per_user': (
                sum(len(items) for items in self.user_interactions.values()) / len(self.user_interactions)
                if self.user_interactions else 0
            ),
            'avg_interactions_per_item': (
                sum(len(users) for users in self.item_interactions.values()) / len(self.item_interactions)
                if self.item_interactions else 0
            )
        }


# Singleton instance
_recommendation_service = None


def get_recommendation_service() -> RecommendationService:
    """Get recommendation service singleton"""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service
