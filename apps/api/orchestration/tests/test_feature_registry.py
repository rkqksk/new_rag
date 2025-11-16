"""
Feature Registry Tests
RAG Enterprise v10.0.0

Unit tests for FeatureRegistry class.
"""

import pytest
from apps.api.orchestration import (
    FeatureRegistry,
    FeatureCategory,
    FeatureStatus,
)


class TestFeatureRegistry:
    """Test FeatureRegistry functionality"""

    def test_initialization(self):
        """Test feature registry initialization"""
        registry = FeatureRegistry()

        assert len(registry.features) > 0
        assert "rag_search" in registry.features
        assert "vision_inspection" in registry.features

    def test_activate_feature_success(self):
        """Test successful feature activation"""
        registry = FeatureRegistry()

        # Activate a feature without dependencies
        success, message = registry.activate("web_crawling")

        assert success is True
        assert registry.features["web_crawling"].status == FeatureStatus.ACTIVE
        assert registry.features["web_crawling"].activation_count == 1

    def test_activate_feature_missing_dependency(self):
        """Test activating feature with missing dependencies"""
        registry = FeatureRegistry()

        # OCR depends on rag_search, which is inactive
        # First deactivate rag_search if it's active
        if registry.features["rag_search"].status == FeatureStatus.ACTIVE:
            registry.deactivate("rag_search", force=True)

        success, message = registry.activate("ocr_processing")

        # Should fail due to missing dependency
        assert success is False
        assert "dependencies" in message.lower()

    def test_activate_feature_with_dependencies(self):
        """Test activating feature after activating dependencies"""
        registry = FeatureRegistry()

        # Activate dependency first
        registry.activate("rag_search")

        # Now activate dependent feature
        success, message = registry.activate("ocr_processing")

        assert success is True
        assert registry.features["ocr_processing"].status == FeatureStatus.ACTIVE

    def test_activate_nonexistent_feature(self):
        """Test activating non-existent feature"""
        registry = FeatureRegistry()

        success, message = registry.activate("nonexistent_feature")

        assert success is False
        assert "not found" in message.lower()

    def test_deactivate_feature_success(self):
        """Test successful feature deactivation"""
        registry = FeatureRegistry()

        # Activate then deactivate
        registry.activate("web_crawling")
        success, message = registry.deactivate("web_crawling")

        assert success is True
        assert registry.features["web_crawling"].status == FeatureStatus.INACTIVE

    def test_deactivate_feature_with_dependents(self):
        """Test deactivating feature with active dependents"""
        registry = FeatureRegistry()

        # Activate rag_search and a dependent
        registry.activate("rag_search")
        registry.activate("ocr_processing")

        # Try to deactivate rag_search (should fail)
        success, message = registry.deactivate("rag_search")

        assert success is False
        assert "depend on" in message.lower()

    def test_deactivate_feature_force(self):
        """Test force deactivation"""
        registry = FeatureRegistry()

        # Activate rag_search and a dependent
        registry.activate("rag_search")
        registry.activate("ocr_processing")

        # Force deactivate
        success, message = registry.deactivate("rag_search", force=True)

        assert success is True
        assert registry.features["rag_search"].status == FeatureStatus.INACTIVE

    def test_get_active_features(self):
        """Test getting active features"""
        registry = FeatureRegistry()

        # Activate some features
        registry.activate("web_crawling")
        registry.activate("api_polling")

        active = registry.get_active_features()

        assert "web_crawling" in active
        assert "api_polling" in active

    def test_get_inactive_features(self):
        """Test getting inactive features"""
        registry = FeatureRegistry()

        inactive = registry.get_inactive_features()

        # Should have many inactive features initially
        assert len(inactive) > 0

    def test_get_features_by_category(self):
        """Test getting features by category"""
        registry = FeatureRegistry()

        rag_features = registry.get_features_by_category(FeatureCategory.RAG)

        assert len(rag_features) > 0
        assert "rag_search" in rag_features
        assert "ocr_processing" in rag_features

    def test_suggest_deactivations(self):
        """Test suggesting features for deactivation"""
        registry = FeatureRegistry()

        # Activate a feature without using it much
        registry.activate("web_crawling")
        # It now has 1 activation, should be suggested

        suggestions = registry.suggest_deactivations(min_activations=10)

        # Core features should not be suggested
        assert "rag_search" not in suggestions
        assert "rest_api" not in suggestions

        # Low usage features should be suggested
        assert "web_crawling" in suggestions

    def test_get_feature_info(self):
        """Test getting feature information"""
        registry = FeatureRegistry()

        info = registry.get_feature_info("rag_search")

        assert info is not None
        assert info["name"] == "rag_search"
        assert info["category"] == "rag"
        assert "description" in info
        assert "status" in info

    def test_get_feature_info_nonexistent(self):
        """Test getting info for non-existent feature"""
        registry = FeatureRegistry()

        info = registry.get_feature_info("nonexistent_feature")

        assert info is None

    def test_get_all_features_info(self):
        """Test getting all features info"""
        registry = FeatureRegistry()

        all_info = registry.get_all_features_info()

        assert len(all_info) == len(registry.features)
        assert "rag_search" in all_info
        assert "vision_inspection" in all_info

    def test_get_usage_statistics(self):
        """Test getting usage statistics"""
        registry = FeatureRegistry()

        # Activate some features
        registry.activate("web_crawling")
        registry.activate("api_polling")

        stats = registry.get_usage_statistics()

        assert "total_features" in stats
        assert "active_features" in stats
        assert "inactive_features" in stats
        assert "by_category" in stats

        assert stats["total_features"] > 0
        assert stats["active_features"] >= 2  # At least the ones we activated

    def test_activation_count_increment(self):
        """Test that activation count increments"""
        registry = FeatureRegistry()

        feature = registry.features["web_crawling"]
        initial_count = feature.activation_count

        registry.activate("web_crawling")
        assert feature.activation_count == initial_count + 1

        registry.deactivate("web_crawling")
        registry.activate("web_crawling")
        assert feature.activation_count == initial_count + 2

    def test_last_activated_timestamp(self):
        """Test that last_activated_at is set"""
        registry = FeatureRegistry()

        feature = registry.features["web_crawling"]
        initial_timestamp = feature.last_activated_at

        registry.activate("web_crawling")

        assert feature.last_activated_at is not None
        assert feature.last_activated_at != initial_timestamp


@pytest.fixture
def registry():
    """Provide fresh registry for each test"""
    return FeatureRegistry()
