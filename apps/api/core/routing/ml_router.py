"""
ML-Based Smart Model Router

Learns from historical routing decisions to predict optimal model selection.
Replaces simple if-else logic with data-driven decision making.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RoutingFeatures:
    """Features extracted from query for ML routing"""

    # Query characteristics
    query_length: int
    word_count: int
    avg_word_length: float
    has_code: bool
    has_technical_terms: bool
    has_verification_keywords: bool
    has_system_keywords: bool

    # Context features
    file_count: int
    has_errors: bool
    time_of_day: int  # 0-23
    day_of_week: int  # 0-6

    # Historical features
    user_avg_complexity: float
    recent_sonnet_ratio: float

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for ML model"""
        return np.array([
            self.query_length,
            self.word_count,
            self.avg_word_length,
            int(self.has_code),
            int(self.has_technical_terms),
            int(self.has_verification_keywords),
            int(self.has_system_keywords),
            self.file_count,
            int(self.has_errors),
            self.time_of_day,
            self.day_of_week,
            self.user_avg_complexity,
            self.recent_sonnet_ratio,
        ])


@dataclass
class RoutingMetrics:
    """Metrics for model routing decision"""

    model: str
    confidence: float
    predicted_latency_ms: float
    predicted_cost: float
    predicted_quality: float
    feature_importance: Dict[str, float]


class MLModelRouter:
    """
    ML-based model router that learns from historical data

    Features:
    - Random Forest classifier for model selection
    - Feature importance analysis
    - Confidence-based routing
    - Continuous learning from feedback
    - A/B testing support
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "models/routing_model.joblib"
        self.model: Optional[RandomForestClassifier] = None
        self.label_encoder = LabelEncoder()
        self.feature_names = self._get_feature_names()

        # Load model if exists
        self._load_model()

        # Training data buffer (for continuous learning)
        self.training_buffer: List[Tuple[RoutingFeatures, str, Dict]] = []
        self.buffer_size = 1000

    def _get_feature_names(self) -> List[str]:
        """Get feature names for importance analysis"""
        return [
            "query_length",
            "word_count",
            "avg_word_length",
            "has_code",
            "has_technical_terms",
            "has_verification_keywords",
            "has_system_keywords",
            "file_count",
            "has_errors",
            "time_of_day",
            "day_of_week",
            "user_avg_complexity",
            "recent_sonnet_ratio",
        ]

    def route(
        self,
        query: str,
        context: Optional[Dict] = None,
        user_id: Optional[str] = None,
    ) -> Tuple[str, RoutingMetrics]:
        """
        Route query to optimal model using ML prediction

        Args:
            query: User query
            context: Additional context
            user_id: User identifier for personalization

        Returns:
            Tuple of (model_name, routing_metrics)
        """
        context = context or {}

        # Extract features
        features = self._extract_features(query, context, user_id)

        # If model not trained, fall back to rule-based
        if self.model is None:
            return self._fallback_route(features)

        # Predict with confidence
        feature_array = features.to_array().reshape(1, -1)
        probabilities = self.model.predict_proba(feature_array)[0]
        predicted_class = self.model.predict(feature_array)[0]
        model_name = self.label_encoder.inverse_transform([predicted_class])[0]

        confidence = float(max(probabilities))

        # Get feature importance
        feature_importance = dict(
            zip(self.feature_names, self.model.feature_importances_)
        )

        # Estimate metrics
        predicted_latency = self._estimate_latency(model_name, features)
        predicted_cost = self._estimate_cost(model_name, features)
        predicted_quality = self._estimate_quality(model_name, features)

        metrics = RoutingMetrics(
            model=model_name,
            confidence=confidence,
            predicted_latency_ms=predicted_latency,
            predicted_cost=predicted_cost,
            predicted_quality=predicted_quality,
            feature_importance=feature_importance,
        )

        # Low confidence → use safe default
        if confidence < 0.6:
            logger.warning(f"Low routing confidence ({confidence:.2f}), using Haiku")
            metrics.model = "claude-haiku-4.5"

        return metrics.model, metrics

    def _extract_features(
        self, query: str, context: Dict, user_id: Optional[str]
    ) -> RoutingFeatures:
        """Extract features from query and context"""

        # Query analysis
        words = query.split()
        query_length = len(query)
        word_count = len(words)
        avg_word_length = np.mean([len(w) for w in words]) if words else 0

        # Pattern detection
        has_code = any(
            kw in query.lower()
            for kw in ["```", "def ", "class ", "function", "import"]
        )

        technical_keywords = [
            "api",
            "database",
            "architecture",
            "performance",
            "optimization",
            "아키텍처",
            "최적화",
        ]
        has_technical_terms = any(kw in query.lower() for kw in technical_keywords)

        verification_keywords = ["verify", "test", "검증", "확인", "테스트"]
        has_verification_keywords = any(
            kw in query.lower() for kw in verification_keywords
        )

        system_keywords = [
            "system",
            "architecture",
            "design",
            "시스템",
            "아키텍처",
            "설계",
        ]
        has_system_keywords = any(kw in query.lower() for kw in system_keywords)

        # Context features
        file_count = context.get("file_count", 0)
        has_errors = context.get("has_errors", False)

        # Time features
        now = datetime.now()
        time_of_day = now.hour
        day_of_week = now.weekday()

        # User historical features (from database/cache)
        user_avg_complexity = self._get_user_avg_complexity(user_id)
        recent_sonnet_ratio = self._get_recent_sonnet_ratio(user_id)

        return RoutingFeatures(
            query_length=query_length,
            word_count=word_count,
            avg_word_length=avg_word_length,
            has_code=has_code,
            has_technical_terms=has_technical_terms,
            has_verification_keywords=has_verification_keywords,
            has_system_keywords=has_system_keywords,
            file_count=file_count,
            has_errors=has_errors,
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            user_avg_complexity=user_avg_complexity,
            recent_sonnet_ratio=recent_sonnet_ratio,
        )

    def _fallback_route(self, features: RoutingFeatures) -> Tuple[str, RoutingMetrics]:
        """Rule-based fallback when ML model not available"""

        # Simple heuristic
        if (
            features.has_system_keywords
            or features.has_verification_keywords
            or features.file_count >= 10
        ):
            model = "claude-sonnet-4.5"
        else:
            model = "claude-haiku-4.5"

        metrics = RoutingMetrics(
            model=model,
            confidence=0.5,
            predicted_latency_ms=500,
            predicted_cost=0.01,
            predicted_quality=0.8,
            feature_importance={},
        )

        return model, metrics

    def _estimate_latency(self, model: str, features: RoutingFeatures) -> float:
        """Estimate latency based on model and query complexity"""
        base_latency = {"claude-haiku-4.5": 200, "claude-sonnet-4.5": 500}

        latency = base_latency.get(model, 350)

        # Adjust for query length
        if features.query_length > 500:
            latency *= 1.5
        if features.file_count > 5:
            latency *= 1.2

        return latency

    def _estimate_cost(self, model: str, features: RoutingFeatures) -> float:
        """Estimate cost based on model and query"""
        cost_per_1k_tokens = {"claude-haiku-4.5": 0.0003, "claude-sonnet-4.5": 0.003}

        base_cost = cost_per_1k_tokens.get(model, 0.001)

        # Estimate tokens (rough)
        estimated_tokens = features.query_length * 0.75  # ~0.75 tokens per char

        return (estimated_tokens / 1000) * base_cost

    def _estimate_quality(self, model: str, features: RoutingFeatures) -> float:
        """Estimate quality score"""
        base_quality = {"claude-haiku-4.5": 0.85, "claude-sonnet-4.5": 0.95}

        quality = base_quality.get(model, 0.9)

        # Haiku quality degrades on complex queries
        if model == "claude-haiku-4.5":
            if features.has_system_keywords or features.file_count > 5:
                quality -= 0.1

        return max(0.5, min(1.0, quality))

    def _get_user_avg_complexity(self, user_id: Optional[str]) -> float:
        """Get user's historical average complexity (from DB/cache)"""
        # TODO: Implement database lookup
        return 50.0  # Default

    def _get_recent_sonnet_ratio(self, user_id: Optional[str]) -> float:
        """Get ratio of recent Sonnet uses (from DB/cache)"""
        # TODO: Implement database lookup
        return 0.3  # Default 30%

    def record_feedback(
        self,
        features: RoutingFeatures,
        actual_model: str,
        metrics: Dict,
    ) -> None:
        """
        Record routing feedback for continuous learning

        Args:
            features: Features used for routing
            actual_model: Model that was actually used
            metrics: Actual metrics (latency, cost, quality)
        """
        self.training_buffer.append((features, actual_model, metrics))

        # Retrain when buffer is full
        if len(self.training_buffer) >= self.buffer_size:
            logger.info("Training buffer full, retraining model...")
            self.retrain()

    def retrain(self) -> None:
        """Retrain model with accumulated feedback"""
        if len(self.training_buffer) < 100:
            logger.warning("Not enough training data, skipping retrain")
            return

        # Prepare training data
        X = np.array([features.to_array() for features, _, _ in self.training_buffer])
        y = np.array([model for _, model, _ in self.training_buffer])

        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)

        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
        )

        self.model.fit(X, y_encoded)

        # Save model
        self._save_model()

        # Clear buffer
        self.training_buffer.clear()

        logger.info("Model retrained successfully")

    def _save_model(self) -> None:
        """Save model to disk"""
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(
            {
                "model": self.model,
                "label_encoder": self.label_encoder,
                "feature_names": self.feature_names,
            },
            self.model_path,
        )

        logger.info(f"Model saved to {self.model_path}")

    def _load_model(self) -> None:
        """Load model from disk"""
        if not Path(self.model_path).exists():
            logger.info("No pre-trained model found")
            return

        try:
            data = joblib.load(self.model_path)
            self.model = data["model"]
            self.label_encoder = data["label_encoder"]
            self.feature_names = data["feature_names"]

            logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance for interpretability"""
        if self.model is None:
            return {}

        return dict(zip(self.feature_names, self.model.feature_importances_))


# Global instance
ml_router = MLModelRouter()


# Example usage
if __name__ == "__main__":
    router = MLModelRouter()

    # Test routing
    test_queries = [
        ("간단한 제품 검색", {}),
        ("전체 시스템 아키텍처 설계해줘", {"file_count": 15}),
        ("API 성능 최적화 검증", {"has_errors": True}),
    ]

    for query, context in test_queries:
        model, metrics = router.route(query, context)

        print(f"\nQuery: {query}")
        print(f"Model: {model}")
        print(f"Confidence: {metrics.confidence:.2f}")
        print(f"Predicted Latency: {metrics.predicted_latency_ms:.0f}ms")
        print(f"Predicted Cost: ${metrics.predicted_cost:.4f}")
        print(f"Predicted Quality: {metrics.predicted_quality:.2f}")

        if metrics.feature_importance:
            print("\nTop 3 Important Features:")
            sorted_features = sorted(
                metrics.feature_importance.items(), key=lambda x: x[1], reverse=True
            )[:3]
            for feat, importance in sorted_features:
                print(f"  - {feat}: {importance:.3f}")
