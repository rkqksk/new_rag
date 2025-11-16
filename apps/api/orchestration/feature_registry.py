"""
Feature Registry
RAG Enterprise v10.0.0

Tracks active/inactive features and provides usage-based recommendations.
Maintains catalog of backend and frontend features.
"""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class FeatureCategory(str, Enum):
    """Feature categories"""

    RAG = "rag"
    MANUFACTURING = "manufacturing"
    DATA_COLLECTION = "data_collection"
    ANALYTICS = "analytics"
    REALTIME = "realtime"
    SAAS = "saas"
    SECURITY = "security"
    OBSERVABILITY = "observability"
    FRONTEND = "frontend"
    API = "api"


class FeatureStatus(str, Enum):
    """Feature status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


@dataclass
class Feature:
    """Feature definition and tracking"""

    name: str
    category: FeatureCategory
    description: str
    status: FeatureStatus = FeatureStatus.INACTIVE
    activation_count: int = 0
    last_activated_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    dependencies: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, float] = field(default_factory=dict)


class FeatureRegistry:
    """
    Tracks features across the platform with usage statistics.

    Features:
    - Feature catalog (backend + frontend)
    - Usage tracking
    - Status management
    - Usage-based recommendations
    - Dependency tracking
    """

    def __init__(self):
        """Initialize feature registry with default features."""
        self.features: Dict[str, Feature] = {}
        self._initialize_default_features()
        logger.info(f"FeatureRegistry initialized with {len(self.features)} features")

    def _initialize_default_features(self):
        """Initialize catalog with all platform features."""

        # RAG Features
        rag_features = [
            Feature(
                name="rag_search",
                category=FeatureCategory.RAG,
                description="Multi-modal RAG search with hybrid ranking",
                status=FeatureStatus.ACTIVE,
                dependencies=["qdrant", "redis"],
                resource_requirements={"cpu": 2.0, "memory": 2.0},
            ),
            Feature(
                name="ocr_processing",
                category=FeatureCategory.RAG,
                description="OCR for PDF/image documents (PaddleOCR, EasyOCR, Tesseract)",
                dependencies=["rag_search"],
                resource_requirements={"cpu": 1.5, "memory": 1.5},
            ),
            Feature(
                name="query_optimization",
                category=FeatureCategory.RAG,
                description="Query enhancement and rewriting",
                dependencies=["rag_search"],
                resource_requirements={"cpu": 1.0, "memory": 1.0},
            ),
            Feature(
                name="document_ingestion",
                category=FeatureCategory.RAG,
                description="Batch document ingestion and chunking",
                dependencies=["rag_search"],
                resource_requirements={"cpu": 1.0, "memory": 1.0},
            ),
        ]

        # Manufacturing Features
        manufacturing_features = [
            Feature(
                name="vision_inspection",
                category=FeatureCategory.MANUFACTURING,
                description="YOLOv8/v10 vision inspection with defect detection",
                resource_requirements={"cpu": 2.0, "memory": 2.0, "gpu": 0.5},
            ),
            Feature(
                name="lora_finetuning",
                category=FeatureCategory.MANUFACTURING,
                description="LORA adapter fine-tuning for custom models",
                dependencies=["vision_inspection"],
                resource_requirements={"cpu": 2.0, "memory": 3.0, "gpu": 1.0},
            ),
            Feature(
                name="robot_control",
                category=FeatureCategory.MANUFACTURING,
                description="UR10e robot arm control integration",
                dependencies=["vision_inspection"],
                resource_requirements={"cpu": 1.0, "memory": 0.5},
            ),
        ]

        # Data Collection Features
        data_features = [
            Feature(
                name="web_crawling",
                category=FeatureCategory.DATA_COLLECTION,
                description="Distributed web crawling (Playwright, Selenium)",
                resource_requirements={"cpu": 1.0, "memory": 1.0},
            ),
            Feature(
                name="api_polling",
                category=FeatureCategory.DATA_COLLECTION,
                description="Scheduled API data collection",
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="file_parsing",
                category=FeatureCategory.DATA_COLLECTION,
                description="Multi-format file parsing (PDF, Excel, CSV, JSON, XML, TXT)",
                resource_requirements={"cpu": 1.0, "memory": 1.0},
            ),
        ]

        # Analytics Features
        analytics_features = [
            Feature(
                name="clickhouse_analytics",
                category=FeatureCategory.ANALYTICS,
                description="ClickHouse OLAP analytics",
                dependencies=["clickhouse"],
                resource_requirements={"cpu": 1.0, "memory": 1.0},
            ),
            Feature(
                name="kafka_streaming",
                category=FeatureCategory.ANALYTICS,
                description="Kafka event streaming",
                dependencies=["kafka"],
                resource_requirements={"cpu": 1.0, "memory": 1.0},
            ),
            Feature(
                name="graphql_api",
                category=FeatureCategory.ANALYTICS,
                description="GraphQL analytics API",
                dependencies=["clickhouse_analytics"],
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
        ]

        # Realtime Features
        realtime_features = [
            Feature(
                name="socketio_server",
                category=FeatureCategory.REALTIME,
                description="Socket.IO realtime server (Convex-like)",
                status=FeatureStatus.ACTIVE,
                dependencies=["redis", "postgres"],
                resource_requirements={"cpu": 1.0, "memory": 0.5},
            ),
            Feature(
                name="postgres_notify",
                category=FeatureCategory.REALTIME,
                description="PostgreSQL LISTEN/NOTIFY reactive queries",
                dependencies=["postgres"],
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="redis_pubsub",
                category=FeatureCategory.REALTIME,
                description="Redis Pub/Sub messaging",
                dependencies=["redis"],
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
        ]

        # SaaS Features
        saas_features = [
            Feature(
                name="multi_tenancy",
                category=FeatureCategory.SAAS,
                description="Multi-tenant architecture with isolation",
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="stripe_billing",
                category=FeatureCategory.SAAS,
                description="Stripe payment and subscription management",
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="usage_tracking",
                category=FeatureCategory.SAAS,
                description="API usage and quota tracking",
                dependencies=["redis"],
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
        ]

        # Security Features
        security_features = [
            Feature(
                name="keycloak_auth",
                category=FeatureCategory.SECURITY,
                description="Keycloak OAuth2/OIDC authentication",
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="vault_secrets",
                category=FeatureCategory.SECURITY,
                description="HashiCorp Vault secret management",
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="jwt_auth",
                category=FeatureCategory.SECURITY,
                description="JWT token-based authentication",
                status=FeatureStatus.ACTIVE,
                resource_requirements={"cpu": 0.3, "memory": 0.3},
            ),
        ]

        # Observability Features
        observability_features = [
            Feature(
                name="jaeger_tracing",
                category=FeatureCategory.OBSERVABILITY,
                description="Distributed tracing with Jaeger",
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="prometheus_metrics",
                category=FeatureCategory.OBSERVABILITY,
                description="Prometheus metrics collection",
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="grafana_dashboards",
                category=FeatureCategory.OBSERVABILITY,
                description="Grafana visualization dashboards",
                dependencies=["prometheus_metrics"],
                resource_requirements={"cpu": 0.3, "memory": 0.3},
            ),
        ]

        # Frontend Features
        frontend_features = [
            Feature(
                name="chat_interface",
                category=FeatureCategory.FRONTEND,
                description="Chat interface for RAG queries",
                status=FeatureStatus.ACTIVE,
                dependencies=["rag_search"],
            ),
            Feature(
                name="realtime_demo",
                category=FeatureCategory.FRONTEND,
                description="Realtime backend demo page",
                status=FeatureStatus.ACTIVE,
                dependencies=["socketio_server"],
            ),
            Feature(
                name="analytics_dashboard",
                category=FeatureCategory.FRONTEND,
                description="Analytics dashboard",
                dependencies=["clickhouse_analytics"],
            ),
            Feature(
                name="rag_dashboard",
                category=FeatureCategory.FRONTEND,
                description="RAG system dashboard",
                dependencies=["rag_search"],
            ),
        ]

        # API Features
        api_features = [
            Feature(
                name="rest_api",
                category=FeatureCategory.API,
                description="RESTful API endpoints (48+)",
                status=FeatureStatus.ACTIVE,
                resource_requirements={"cpu": 1.0, "memory": 1.0},
            ),
            Feature(
                name="streaming_api",
                category=FeatureCategory.API,
                description="Streaming response API",
                dependencies=["rest_api"],
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
            Feature(
                name="websocket_api",
                category=FeatureCategory.API,
                description="WebSocket API endpoints",
                status=FeatureStatus.ACTIVE,
                dependencies=["socketio_server"],
                resource_requirements={"cpu": 0.5, "memory": 0.5},
            ),
        ]

        # Register all features
        all_features = (
            rag_features
            + manufacturing_features
            + data_features
            + analytics_features
            + realtime_features
            + saas_features
            + security_features
            + observability_features
            + frontend_features
            + api_features
        )

        for feature in all_features:
            self.features[feature.name] = feature

    def activate(self, feature_name: str) -> tuple[bool, str]:
        """
        Activate a feature.

        Args:
            feature_name: Name of the feature

        Returns:
            Tuple of (success, message)
        """
        if feature_name not in self.features:
            return False, f"Feature '{feature_name}' not found"

        feature = self.features[feature_name]

        # Check dependencies
        missing_deps = []
        for dep in feature.dependencies:
            if dep not in self.features:
                missing_deps.append(dep)
            elif self.features[dep].status != FeatureStatus.ACTIVE:
                missing_deps.append(dep)

        if missing_deps:
            return False, f"Missing dependencies: {missing_deps}"

        # Activate
        feature.status = FeatureStatus.ACTIVE
        feature.activation_count += 1
        feature.last_activated_at = datetime.utcnow()

        logger.info(
            f"Activated feature: {feature_name} (total activations: {feature.activation_count})"
        )
        return True, f"Feature '{feature_name}' activated"

    def deactivate(self, feature_name: str, force: bool = False) -> tuple[bool, str]:
        """
        Deactivate a feature.

        Args:
            feature_name: Name of the feature
            force: Force deactivation even if other features depend on it

        Returns:
            Tuple of (success, message)
        """
        if feature_name not in self.features:
            return False, f"Feature '{feature_name}' not found"

        feature = self.features[feature_name]

        # Check for dependent features
        if not force:
            dependents = self._get_dependent_features(feature_name)
            active_dependents = [
                name for name in dependents if self.features[name].status == FeatureStatus.ACTIVE
            ]
            if active_dependents:
                return (
                    False,
                    f"Cannot deactivate: features {active_dependents} depend on '{feature_name}'",
                )

        # Deactivate
        feature.status = FeatureStatus.INACTIVE

        logger.info(f"Deactivated feature: {feature_name}")
        return True, f"Feature '{feature_name}' deactivated"

    def get_active_features(self) -> List[str]:
        """
        Get list of active features.

        Returns:
            List of active feature names
        """
        return [
            name
            for name, feature in self.features.items()
            if feature.status == FeatureStatus.ACTIVE
        ]

    def get_inactive_features(self) -> List[str]:
        """
        Get list of inactive features.

        Returns:
            List of inactive feature names
        """
        return [
            name
            for name, feature in self.features.items()
            if feature.status == FeatureStatus.INACTIVE
        ]

    def get_features_by_category(self, category: FeatureCategory) -> List[str]:
        """
        Get features by category.

        Args:
            category: Feature category

        Returns:
            List of feature names in category
        """
        return [name for name, feature in self.features.items() if feature.category == category]

    def suggest_deactivations(self, min_activations: int = 10) -> List[str]:
        """
        Suggest features for deactivation based on low usage.

        Args:
            min_activations: Minimum activation count to keep active

        Returns:
            List of feature names suggested for deactivation
        """
        suggestions = []

        for name, feature in self.features.items():
            if (
                feature.status == FeatureStatus.ACTIVE
                and feature.activation_count < min_activations
            ):
                # Don't suggest core features
                if name not in ["rag_search", "rest_api", "jwt_auth", "socketio_server"]:
                    suggestions.append(name)

        logger.info(
            f"Suggested {len(suggestions)} features for deactivation (min_activations={min_activations})"
        )
        return suggestions

    def get_feature_info(self, feature_name: str) -> Optional[Dict]:
        """
        Get detailed information about a feature.

        Args:
            feature_name: Name of the feature

        Returns:
            Dictionary with feature information or None
        """
        if feature_name not in self.features:
            return None

        feature = self.features[feature_name]
        return {
            "name": feature.name,
            "category": feature.category.value,
            "description": feature.description,
            "status": feature.status.value,
            "activation_count": feature.activation_count,
            "last_activated_at": (
                feature.last_activated_at.isoformat() if feature.last_activated_at else None
            ),
            "created_at": feature.created_at.isoformat(),
            "dependencies": feature.dependencies,
            "resource_requirements": feature.resource_requirements,
        }

    def get_all_features_info(self) -> Dict[str, Dict]:
        """
        Get information for all features.

        Returns:
            Dictionary mapping feature names to info
        """
        return {name: self.get_feature_info(name) for name in self.features.keys()}

    def get_usage_statistics(self) -> Dict[str, any]:
        """
        Get usage statistics across all features.

        Returns:
            Dictionary with usage statistics
        """
        total_features = len(self.features)
        active_features = len(self.get_active_features())
        inactive_features = len(self.get_inactive_features())

        total_activations = sum(f.activation_count for f in self.features.values())
        avg_activations = total_activations / total_features if total_features > 0 else 0

        by_category = {}
        for category in FeatureCategory:
            category_features = self.get_features_by_category(category)
            active_in_category = sum(
                1
                for name in category_features
                if self.features[name].status == FeatureStatus.ACTIVE
            )
            by_category[category.value] = {
                "total": len(category_features),
                "active": active_in_category,
                "inactive": len(category_features) - active_in_category,
            }

        return {
            "total_features": total_features,
            "active_features": active_features,
            "inactive_features": inactive_features,
            "total_activations": total_activations,
            "avg_activations_per_feature": round(avg_activations, 2),
            "by_category": by_category,
        }

    def _get_dependent_features(self, feature_name: str) -> Set[str]:
        """
        Get features that depend on the given feature.

        Args:
            feature_name: Feature to check dependencies for

        Returns:
            Set of dependent feature names
        """
        dependents = set()
        for name, feature in self.features.items():
            if feature_name in feature.dependencies:
                dependents.add(name)
        return dependents
