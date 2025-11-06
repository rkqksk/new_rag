"""Integration tests for Analytics API endpoints"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app

client = TestClient(app)

@pytest.mark.integration
class TestAnalyticsAPI:
    """Integration tests for /api/v1/analytics endpoints"""
    
    @pytest.fixture(autouse=True)
    def mock_dependencies(self):
        """Mock all dependencies for integration tests"""
        with patch('app.dependencies.services.get_analytics_service') as mock_service:
            service = MagicMock()
            
            # Mock get_top_keywords
            async def mock_keywords(limit):
                return [
                    {"keyword": "50ml", "search_count": 120},
                    {"keyword": "PET", "search_count": 95},
                    {"keyword": "20파이", "search_count": 85}
                ][:limit]
            
            service.get_top_keywords = mock_keywords
            
            # Mock get_top_products
            async def mock_products(limit, metric):
                return [
                    {
                        "product_id": "PROD-001",
                        "product_name": "50ml PET 용기",
                        "click_count": 50,
                        "view_count": 200
                    },
                    {
                        "product_id": "PROD-002",
                        "product_name": "20파이 캡",
                        "click_count": 45,
                        "view_count": 180
                    }
                ][:limit]
            
            service.get_top_products = mock_products
            
            # Mock get_trending_queries
            async def mock_trending(limit):
                return [
                    {"query": "20파이 캡", "growth_rate": 2.5, "trend": "up"},
                    {"query": "50ml 용기", "growth_rate": 1.8, "trend": "up"}
                ][:limit]
            
            service.get_trending_queries = mock_trending
            
            # Mock get_search_patterns
            async def mock_patterns(limit):
                return [
                    {
                        "pattern": "bottle_then_cap",
                        "first_category": "bottle",
                        "second_category": "cap",
                        "frequency": 85
                    }
                ][:limit]
            
            service.get_search_patterns = mock_patterns
            
            # Mock get_analytics_summary
            async def mock_summary():
                return {
                    "top_keywords": await mock_keywords(5),
                    "top_products": await mock_products(5, "click"),
                    "trending_queries": await mock_trending(5),
                    "search_patterns": await mock_patterns(5),
                    "total_searches": 1500,
                    "total_clicks": 450,
                    "unique_sessions": 320,
                    "avg_results_per_search": 12.5
                }
            
            service.get_analytics_summary = mock_summary
            
            mock_service.return_value = service
            yield service
    
    def test_get_top_keywords_default(self):
        """Test getting top keywords with default limit"""
        # Act
        response = client.get("/api/v1/analytics/keywords")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
        assert "total" in data
        assert isinstance(data["keywords"], list)
        assert len(data["keywords"]) <= 20  # Default limit
    
    def test_get_top_keywords_custom_limit(self):
        """Test getting top keywords with custom limit"""
        # Act
        response = client.get("/api/v1/analytics/keywords?limit=2")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["keywords"]) <= 2
    
    def test_get_top_keywords_large_limit(self):
        """Test getting top keywords with large limit"""
        # Act
        response = client.get("/api/v1/analytics/keywords?limit=100")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
    
    def test_get_trending_queries(self):
        """Test getting trending queries"""
        # Act
        response = client.get("/api/v1/analytics/trending")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "queries" in data
        assert "total" in data
        assert isinstance(data["queries"], list)
    
    def test_get_trending_queries_custom_limit(self):
        """Test trending queries with custom limit"""
        # Act
        response = client.get("/api/v1/analytics/trending?limit=5")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["queries"]) <= 5
    
    def test_get_popular_products_default_metric(self):
        """Test getting popular products with default metric (click)"""
        # Act
        response = client.get("/api/v1/analytics/products/popular")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert isinstance(data["products"], list)
    
    def test_get_popular_products_click_metric(self):
        """Test getting popular products by click count"""
        # Act
        response = client.get("/api/v1/analytics/products/popular?metric=click")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should include click_count in results
        if data["products"]:
            assert "click_count" in data["products"][0]
    
    def test_get_popular_products_view_metric(self):
        """Test getting popular products by view count"""
        # Act
        response = client.get("/api/v1/analytics/products/popular?metric=view")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
    
    def test_get_popular_products_custom_limit(self):
        """Test popular products with custom limit"""
        # Act
        response = client.get("/api/v1/analytics/products/popular?limit=5")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) <= 5
    
    def test_get_search_patterns(self):
        """Test getting common search patterns"""
        # Act
        response = client.get("/api/v1/analytics/patterns")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert "total" in data
        assert isinstance(data["patterns"], list)
    
    def test_get_search_patterns_custom_limit(self):
        """Test search patterns with custom limit"""
        # Act
        response = client.get("/api/v1/analytics/patterns?limit=10")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["patterns"]) <= 10
    
    def test_get_analytics_summary(self):
        """Test getting comprehensive analytics summary"""
        # Act
        response = client.get("/api/v1/analytics/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should include all major metrics
        assert "top_keywords" in data
        assert "top_products" in data
        assert "trending_queries" in data
        assert "search_patterns" in data
        assert "total_searches" in data
        assert "total_clicks" in data
        assert "unique_sessions" in data
    
    def test_analytics_endpoints_return_json(self):
        """Test that all analytics endpoints return valid JSON"""
        endpoints = [
            "/api/v1/analytics/keywords",
            "/api/v1/analytics/trending",
            "/api/v1/analytics/products/popular",
            "/api/v1/analytics/patterns",
            "/api/v1/analytics/summary"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)
    
    def test_analytics_negative_limit(self):
        """Test analytics with negative limit"""
        # Act
        response = client.get("/api/v1/analytics/keywords?limit=-1")
        
        # Assert
        # Should handle gracefully (422 validation error or use default)
        assert response.status_code in [200, 422]
    
    def test_analytics_zero_limit(self):
        """Test analytics with zero limit"""
        # Act
        response = client.get("/api/v1/analytics/keywords?limit=0")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["keywords"]) == 0
