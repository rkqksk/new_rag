"""
A/B Testing Framework for Fusion Strategies
Tests different search fusion methods and strategies
"""

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment lifecycle status"""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class FusionStrategy(Enum):
    """Fusion strategy variants"""

    RRF = "rrf"  # Reciprocal Rank Fusion
    WEIGHTED = "weighted"  # Weighted linear combination
    LEARNED = "learned"  # ML-based learned fusion


@dataclass
class Variant:
    """
    A/B test variant configuration

    Represents a specific fusion strategy configuration
    """

    id: str
    name: str
    strategy: FusionStrategy
    config: Dict[str, Any]
    traffic_allocation: float = 0.5  # % of users assigned to this variant

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["strategy"] = self.strategy.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Variant":
        """Create from dictionary"""
        data["strategy"] = FusionStrategy(data["strategy"])
        return cls(**data)


@dataclass
class Metric:
    """
    Metrics tracked per variant
    """

    clicks: int = 0
    impressions: int = 0
    relevance_scores: List[float] = field(default_factory=list)
    user_satisfaction: List[int] = field(default_factory=list)  # 1-5 rating
    query_count: int = 0
    avg_latency_ms: float = 0.0
    error_count: int = 0

    def get_ctr(self) -> float:
        """Calculate click-through rate"""
        return self.clicks / self.impressions if self.impressions > 0 else 0.0

    def get_avg_relevance(self) -> float:
        """Calculate average relevance score"""
        return float(np.mean(self.relevance_scores)) if self.relevance_scores else 0.0

    def get_avg_satisfaction(self) -> float:
        """Calculate average user satisfaction"""
        return float(np.mean(self.user_satisfaction)) if self.user_satisfaction else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "clicks": self.clicks,
            "impressions": self.impressions,
            "ctr": self.get_ctr(),
            "query_count": self.query_count,
            "avg_relevance": self.get_avg_relevance(),
            "avg_satisfaction": self.get_avg_satisfaction(),
            "avg_latency_ms": self.avg_latency_ms,
            "error_count": self.error_count,
            "sample_sizes": {
                "relevance": len(self.relevance_scores),
                "satisfaction": len(self.user_satisfaction),
            },
        }


@dataclass
class Experiment:
    """
    A/B Test Experiment

    Represents a complete A/B test comparing different fusion strategies
    """

    id: str
    name: str
    description: str
    variants: List[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metrics: Dict[str, Metric] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize metrics for each variant"""
        if not self.metrics:
            self.metrics = {variant.id: Metric() for variant in self.variants}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "variants": [v.to_dict() for v in self.variants],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experiment":
        """Create from dictionary"""
        data["variants"] = [Variant.from_dict(v) for v in data["variants"]]
        data["status"] = ExperimentStatus(data["status"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("ended_at"):
            data["ended_at"] = datetime.fromisoformat(data["ended_at"])

        # Reconstruct metrics
        metrics_data = data.pop("metrics", {})
        experiment = cls(**data)
        for variant_id, metric_dict in metrics_data.items():
            experiment.metrics[variant_id] = Metric(**metric_dict)

        return experiment


class ABTestingFramework:
    """
    A/B Testing Framework

    Features:
    - Experiment management (create, start, stop)
    - Consistent user assignment to variants
    - Metrics tracking (CTR, relevance, satisfaction)
    - Statistical analysis (significance testing)
    - Results reporting
    """

    def __init__(self, redis_client: Optional[Any] = None):
        """
        Initialize A/B testing framework

        Args:
            redis_client: Optional Redis client for persistence
        """
        self.redis_client = redis_client
        self.experiments: Dict[str, Experiment] = {}

        logger.info("✅ A/B Testing Framework initialized")

    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Experiment:
        """
        Create a new A/B test experiment

        Args:
            name: Experiment name
            description: Experiment description
            variants: List of variant configurations
            metadata: Optional metadata

        Returns:
            Created experiment

        Example:
            >>> variants = [
            ...     {
            ...         'name': 'RRF Fusion',
            ...         'strategy': 'rrf',
            ...         'config': {'k': 60},
            ...         'traffic_allocation': 0.5
            ...     },
            ...     {
            ...         'name': 'Weighted Fusion',
            ...         'strategy': 'weighted',
            ...         'config': {'text_weight': 0.6, 'image_weight': 0.4},
            ...         'traffic_allocation': 0.5
            ...     }
            ... ]
            >>> exp = framework.create_experiment('Fusion Test', 'Test RRF vs Weighted', variants)
        """
        import uuid

        experiment_id = str(uuid.uuid4())

        # Create variant objects
        variant_objects = []
        for i, variant_config in enumerate(variants):
            variant_id = f"{experiment_id}_variant_{i}"
            variant = Variant(
                id=variant_id,
                name=variant_config["name"],
                strategy=FusionStrategy(variant_config["strategy"]),
                config=variant_config["config"],
                traffic_allocation=variant_config.get("traffic_allocation", 1.0 / len(variants)),
            )
            variant_objects.append(variant)

        # Create experiment
        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            variants=variant_objects,
            metadata=metadata or {},
        )

        self.experiments[experiment_id] = experiment

        # Persist to Redis
        if self.redis_client:
            self._persist_experiment(experiment)

        logger.info(
            f"✅ Created experiment '{name}' ({experiment_id}) with {len(variants)} variants"
        )

        return experiment

    def start_experiment(self, experiment_id: str):
        """Start an experiment"""
        experiment = self.experiments.get(experiment_id)

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"Cannot start experiment in status: {experiment.status.value}")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now()

        if self.redis_client:
            self._persist_experiment(experiment)

        logger.info(f"▶️  Started experiment '{experiment.name}' ({experiment_id})")

    def stop_experiment(self, experiment_id: str):
        """Stop an experiment"""
        experiment = self.experiments.get(experiment_id)

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.now()

        if self.redis_client:
            self._persist_experiment(experiment)

        logger.info(f"⏹️  Stopped experiment '{experiment.name}' ({experiment_id})")

    def assign_variant(self, experiment_id: str, user_id: str) -> Variant:
        """
        Assign user to a variant consistently

        Uses hash-based assignment for consistency

        Args:
            experiment_id: Experiment ID
            user_id: User identifier (session ID, user ID, etc.)

        Returns:
            Assigned variant
        """
        experiment = self.experiments.get(experiment_id)

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        if experiment.status != ExperimentStatus.RUNNING:
            # Return control variant (first variant)
            return experiment.variants[0]

        # Hash-based assignment for consistency
        hash_input = f"{experiment_id}:{user_id}".encode("utf-8")
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        assignment_value = (hash_value % 100) / 100.0  # 0.0-1.0

        # Assign based on traffic allocation
        cumulative_allocation = 0.0
        for variant in experiment.variants:
            cumulative_allocation += variant.traffic_allocation
            if assignment_value < cumulative_allocation:
                return variant

        # Fallback to last variant
        return experiment.variants[-1]

    def track_impression(self, experiment_id: str, variant_id: str):
        """Track impression (search result shown)"""
        experiment = self.experiments.get(experiment_id)

        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return

        if variant_id in experiment.metrics:
            experiment.metrics[variant_id].impressions += 1

    def track_click(self, experiment_id: str, variant_id: str):
        """Track click (user clicked on a result)"""
        experiment = self.experiments.get(experiment_id)

        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return

        if variant_id in experiment.metrics:
            experiment.metrics[variant_id].clicks += 1

    def track_query(
        self,
        experiment_id: str,
        variant_id: str,
        relevance_score: Optional[float] = None,
        latency_ms: Optional[float] = None,
    ):
        """Track query execution"""
        experiment = self.experiments.get(experiment_id)

        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return

        if variant_id in experiment.metrics:
            metric = experiment.metrics[variant_id]
            metric.query_count += 1

            if relevance_score is not None:
                metric.relevance_scores.append(relevance_score)

            if latency_ms is not None:
                # Update running average
                total_queries = metric.query_count
                metric.avg_latency_ms = (
                    metric.avg_latency_ms * (total_queries - 1) + latency_ms
                ) / total_queries

    def track_satisfaction(self, experiment_id: str, variant_id: str, rating: int):
        """
        Track user satisfaction rating

        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID
            rating: User rating (1-5)
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        experiment = self.experiments.get(experiment_id)

        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return

        if variant_id in experiment.metrics:
            experiment.metrics[variant_id].user_satisfaction.append(rating)

    def track_error(self, experiment_id: str, variant_id: str):
        """Track error occurrence"""
        experiment = self.experiments.get(experiment_id)

        if not experiment:
            return

        if variant_id in experiment.metrics:
            experiment.metrics[variant_id].error_count += 1

    def get_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get experiment results

        Returns:
            Results dictionary with metrics and analysis
        """
        experiment = self.experiments.get(experiment_id)

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        results = {
            "experiment": {
                "id": experiment.id,
                "name": experiment.name,
                "status": experiment.status.value,
                "duration_hours": self._get_duration_hours(experiment),
            },
            "variants": [],
            "winner": None,
            "statistical_analysis": None,
        }

        # Collect variant results
        for variant in experiment.variants:
            metric = experiment.metrics[variant.id]

            variant_result = {
                "id": variant.id,
                "name": variant.name,
                "strategy": variant.strategy.value,
                "config": variant.config,
                "metrics": metric.to_dict(),
            }

            results["variants"].append(variant_result)

        # Determine winner
        if len(experiment.variants) == 2:
            results["winner"] = self._determine_winner(experiment)
            results["statistical_analysis"] = self._statistical_analysis(experiment)

        return results

    def _determine_winner(self, experiment: Experiment) -> Optional[Dict[str, Any]]:
        """
        Determine winning variant based on primary metric (CTR)

        Returns:
            Winner information or None if inconclusive
        """
        if len(experiment.variants) != 2:
            return None

        variant_a, variant_b = experiment.variants
        metric_a = experiment.metrics[variant_a.id]
        metric_b = experiment.metrics[variant_b.id]

        ctr_a = metric_a.get_ctr()
        ctr_b = metric_b.get_ctr()

        # Check if difference is statistically significant
        is_significant, p_value = self._chi_square_test(
            metric_a.clicks, metric_a.impressions, metric_b.clicks, metric_b.impressions
        )

        if not is_significant:
            return {
                "status": "inconclusive",
                "message": "No statistically significant difference",
                "p_value": p_value,
            }

        winner = variant_a if ctr_a > ctr_b else variant_b
        loser = variant_b if ctr_a > ctr_b else variant_a

        improvement = abs(ctr_a - ctr_b) / min(ctr_a, ctr_b) * 100 if min(ctr_a, ctr_b) > 0 else 0

        return {
            "status": "significant",
            "winner_id": winner.id,
            "winner_name": winner.name,
            "winner_ctr": metric_a.get_ctr() if winner == variant_a else metric_b.get_ctr(),
            "loser_ctr": metric_b.get_ctr() if winner == variant_a else metric_a.get_ctr(),
            "improvement_percent": improvement,
            "p_value": p_value,
        }

    def _statistical_analysis(self, experiment: Experiment) -> Dict[str, Any]:
        """
        Perform statistical analysis on experiment results

        Returns:
            Analysis results
        """
        if len(experiment.variants) != 2:
            return {"error": "Statistical analysis only supported for 2 variants"}

        variant_a, variant_b = experiment.variants
        metric_a = experiment.metrics[variant_a.id]
        metric_b = experiment.metrics[variant_b.id]

        analysis = {}

        # CTR analysis (chi-square test)
        is_sig_ctr, p_value_ctr = self._chi_square_test(
            metric_a.clicks, metric_a.impressions, metric_b.clicks, metric_b.impressions
        )

        analysis["ctr"] = {
            "is_significant": is_sig_ctr,
            "p_value": p_value_ctr,
            "alpha": 0.05,
            "test": "chi_square",
        }

        # Relevance score analysis (t-test)
        if metric_a.relevance_scores and metric_b.relevance_scores:
            is_sig_rel, p_value_rel = self._t_test(
                metric_a.relevance_scores, metric_b.relevance_scores
            )

            analysis["relevance"] = {
                "is_significant": is_sig_rel,
                "p_value": p_value_rel,
                "alpha": 0.05,
                "test": "t_test",
            }

        # Satisfaction analysis (t-test)
        if metric_a.user_satisfaction and metric_b.user_satisfaction:
            is_sig_sat, p_value_sat = self._t_test(
                metric_a.user_satisfaction, metric_b.user_satisfaction
            )

            analysis["satisfaction"] = {
                "is_significant": is_sig_sat,
                "p_value": p_value_sat,
                "alpha": 0.05,
                "test": "t_test",
            }

        return analysis

    def _chi_square_test(
        self,
        clicks_a: int,
        impressions_a: int,
        clicks_b: int,
        impressions_b: int,
        alpha: float = 0.05,
    ) -> Tuple[bool, float]:
        """
        Chi-square test for CTR comparison

        Returns:
            (is_significant, p_value)
        """
        from scipy import stats

        # Observed frequencies
        observed = np.array(
            [[clicks_a, impressions_a - clicks_a], [clicks_b, impressions_b - clicks_b]]
        )

        # Chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(observed)

        is_significant = p_value < alpha

        return is_significant, float(p_value)

    def _t_test(
        self, sample_a: List[float], sample_b: List[float], alpha: float = 0.05
    ) -> Tuple[bool, float]:
        """
        Independent t-test for comparing means

        Returns:
            (is_significant, p_value)
        """
        from scipy import stats

        if len(sample_a) < 2 or len(sample_b) < 2:
            return False, 1.0

        # Independent t-test
        t_stat, p_value = stats.ttest_ind(sample_a, sample_b)

        is_significant = p_value < alpha

        return is_significant, float(p_value)

    def _get_duration_hours(self, experiment: Experiment) -> float:
        """Calculate experiment duration in hours"""
        if not experiment.started_at:
            return 0.0

        end_time = experiment.ended_at or datetime.now()
        duration = end_time - experiment.started_at

        return duration.total_seconds() / 3600.0

    def list_experiments(self, status: Optional[ExperimentStatus] = None) -> List[Dict[str, Any]]:
        """
        List all experiments

        Args:
            status: Optional filter by status

        Returns:
            List of experiment summaries
        """
        experiments = []

        for exp in self.experiments.values():
            if status and exp.status != status:
                continue

            experiments.append(
                {
                    "id": exp.id,
                    "name": exp.name,
                    "status": exp.status.value,
                    "variants_count": len(exp.variants),
                    "created_at": exp.created_at.isoformat(),
                    "duration_hours": self._get_duration_hours(exp),
                }
            )

        return experiments

    def delete_experiment(self, experiment_id: str):
        """Delete an experiment"""
        if experiment_id in self.experiments:
            del self.experiments[experiment_id]

            if self.redis_client:
                key = f"experiment:{experiment_id}"
                self.redis_client.delete(key)

            logger.info(f"🗑️  Deleted experiment {experiment_id}")

    def _persist_experiment(self, experiment: Experiment):
        """Persist experiment to Redis"""
        if not self.redis_client:
            return

        try:
            key = f"experiment:{experiment.id}"
            data = json.dumps(experiment.to_dict())
            self.redis_client.set(key, data)

        except Exception as e:
            logger.error(f"Failed to persist experiment: {e}")

    def _load_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Load experiment from Redis"""
        if not self.redis_client:
            return None

        try:
            key = f"experiment:{experiment_id}"
            data = self.redis_client.get(key)

            if data:
                experiment_dict = json.loads(data)
                return Experiment.from_dict(experiment_dict)

        except Exception as e:
            logger.error(f"Failed to load experiment: {e}")

        return None

    def __repr__(self):
        running = len(
            [e for e in self.experiments.values() if e.status == ExperimentStatus.RUNNING]
        )
        total = len(self.experiments)

        return f"ABTestingFramework(experiments={total}, running={running})"


# Usage example
"""
# Initialize framework
framework = ABTestingFramework(redis_client=redis)

# Create experiment
variants = [
    {
        'name': 'RRF Fusion',
        'strategy': 'rrf',
        'config': {'k': 60},
        'traffic_allocation': 0.5
    },
    {
        'name': 'Weighted Fusion',
        'strategy': 'weighted',
        'config': {'text_weight': 0.6, 'image_weight': 0.4},
        'traffic_allocation': 0.5
    }
]

experiment = framework.create_experiment(
    name='Fusion Strategy Test',
    description='Compare RRF vs Weighted fusion',
    variants=variants
)

# Start experiment
framework.start_experiment(experiment.id)

# In your search handler
user_id = session_id
variant = framework.assign_variant(experiment.id, user_id)

# Use variant configuration
if variant.strategy == FusionStrategy.RRF:
    results = search_engine.search_rrf(query, k=variant.config['k'])
elif variant.strategy == FusionStrategy.WEIGHTED:
    results = search_engine.search_weighted(
        query,
        text_weight=variant.config['text_weight'],
        image_weight=variant.config['image_weight']
    )

# Track metrics
framework.track_impression(experiment.id, variant.id)
framework.track_query(experiment.id, variant.id, relevance_score=0.85, latency_ms=120)

# When user clicks result
framework.track_click(experiment.id, variant.id)

# Get results
results = framework.get_results(experiment.id)
print(f"Winner: {results['winner']['winner_name']}")
print(f"Improvement: {results['winner']['improvement_percent']:.2f}%")

# Stop experiment
framework.stop_experiment(experiment.id)
"""
