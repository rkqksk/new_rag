"""
Integration tests for product loading (in-memory caching)
"""

import pytest
from apps.api.v1.personalization import get_all_products, _product_cache
from apps.api.services.product_loader import load_products


class TestProductLoading:
    """Test product loading and caching"""

    def test_load_products_returns_dict(self):
        """Test that load_products returns a dictionary"""
        products = load_products(categories=["Bottle"])

        assert isinstance(products, dict)
        # Should have product_id as keys
        if products:
            first_key = next(iter(products))
            assert isinstance(first_key, str)
            assert "product_id" in products[first_key]

    def test_get_all_products_returns_list(self):
        """Test that get_all_products returns a list"""
        global _product_cache
        _product_cache = None  # Reset cache

        products = get_all_products()

        assert isinstance(products, list)
        # Each product should be a dict
        if products:
            assert isinstance(products[0], dict)
            assert "product_id" in products[0]

    def test_get_all_products_caching(self):
        """Test that get_all_products uses in-memory cache"""
        global _product_cache
        _product_cache = None  # Reset cache

        # First call should load from files
        products1 = get_all_products()

        # Second call should use cache
        products2 = get_all_products()

        # Should return same data
        assert len(products1) == len(products2)

        # Cache should be populated
        assert _product_cache is not None

    def test_load_products_with_categories(self):
        """Test loading products from specific categories"""
        # Load only Bottle category
        bottle_products = load_products(categories=["Bottle"])

        # All products should be Bottles
        for product in bottle_products.values():
            assert product["category"] == "Bottle"

    def test_product_structure(self):
        """Test that loaded products have expected structure"""
        products = load_products(categories=["Bottle"])

        if not products:
            pytest.skip("No products found")

        first_product = next(iter(products.values()))

        # Check required fields
        required_fields = [
            "product_id",
            "product_name",
            "product_code",
            "capacity",
            "material",
            "category",
        ]

        for field in required_fields:
            assert field in first_product, f"Missing field: {field}"

    def test_product_loading_performance(self):
        """Test that product loading completes in reasonable time"""
        import time

        start = time.time()
        products = load_products()
        end = time.time()

        elapsed = end - start

        # Should load within 5 seconds
        assert elapsed < 5.0, f"Product loading took {elapsed:.2f}s (expected < 5s)"

        # Should have loaded products
        assert len(products) > 0

    def test_cache_reset_and_reload(self):
        """Test cache can be reset and reloaded"""
        global _product_cache

        # Load products
        products1 = get_all_products()
        count1 = len(products1)

        # Reset cache
        _product_cache = None

        # Reload products
        products2 = get_all_products()
        count2 = len(products2)

        # Should have same count
        assert count1 == count2
