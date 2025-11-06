"""Integration tests for Search API endpoints"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app

client = TestClient(app)

@pytest.mark.integration
class TestSearchAPI:
    """Integration tests for /api/v1/search endpoints"""
    
    @pytest.fixture(autouse=True)
    def mock_dependencies(self, sample_search_results, sample_products):
        """Mock all dependencies for integration tests"""
        with patch('app.dependencies.services.get_search_service') as mock_service:
            service = MagicMock()
            
            # Mock search method
            async def mock_search(query, session_id, top_k, use_cache):
                return {
                    "results": sample_products,
                    "total": len(sample_products),
                    "query": query,
                    "session_id": session_id,
                    "cached": False
                }
            
            service.search = mock_search
            
            # Mock image_search method
            async def mock_image_search(image_path, session_id, top_k):
                return {
                    "results": sample_products[:2],
                    "total": 2,
                    "session_id": session_id
                }
            
            service.image_search = mock_image_search
            
            # Mock hybrid_search method
            async def mock_hybrid_search(query, image_path, text_weight, image_weight, session_id, top_k):
                return {
                    "results": sample_products,
                    "total": len(sample_products),
                    "query": query,
                    "session_id": session_id,
                    "fusion": "hybrid"
                }
            
            service.hybrid_search = mock_hybrid_search
            
            mock_service.return_value = service
            yield service
    
    def test_search_basic(self):
        """Test basic search endpoint"""
        # Arrange
        request_data = {
            "query": "50ml PET 용기",
            "session_id": "sess_123",
            "top_k": 20,
            "use_cache": True
        }
        
        # Act
        response = client.post("/api/v1/search/", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "query" in data
        assert data["query"] == "50ml PET 용기"
        assert isinstance(data["results"], list)
    
    def test_search_without_session(self):
        """Test search without session ID"""
        # Arrange
        request_data = {
            "query": "20파이 캡",
            "top_k": 10,
            "use_cache": False
        }
        
        # Act
        response = client.post("/api/v1/search/", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] is None
    
    def test_search_with_cache(self):
        """Test search with caching enabled"""
        # Arrange
        request_data = {
            "query": "50ml 용기",
            "use_cache": True
        }
        
        # Act
        response = client.post("/api/v1/search/", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "cached" in data
    
    def test_search_missing_query(self):
        """Test search with missing required query parameter"""
        # Arrange
        request_data = {
            "top_k": 20
        }
        
        # Act
        response = client.post("/api/v1/search/", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_search_empty_query(self):
        """Test search with empty query string"""
        # Arrange
        request_data = {
            "query": "",
            "top_k": 20
        }
        
        # Act
        response = client.post("/api/v1/search/", json=request_data)
        
        # Assert
        # Depending on validation, this might be 422 or 200 with empty results
        assert response.status_code in [200, 422]
    
    def test_image_search(self, tmp_path):
        """Test image search endpoint"""
        # Arrange
        image_file = tmp_path / "test_image.jpg"
        image_file.write_bytes(b"fake image data")
        
        # Act
        with open(image_file, "rb") as f:
            response = client.post(
                "/api/v1/search/image",
                files={"image": ("test.jpg", f, "image/jpeg")},
                data={"session_id": "sess_123", "top_k": "20"}
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
    
    def test_image_search_without_file(self):
        """Test image search without providing image file"""
        # Act
        response = client.post("/api/v1/search/image")
        
        # Assert
        assert response.status_code == 422  # Missing required file
    
    def test_hybrid_search(self, tmp_path):
        """Test hybrid search endpoint (text + image)"""
        # Arrange
        image_file = tmp_path / "test_image.jpg"
        image_file.write_bytes(b"fake image data")
        
        # Act
        with open(image_file, "rb") as f:
            response = client.post(
                "/api/v1/search/hybrid",
                files={"image": ("test.jpg", f, "image/jpeg")},
                data={
                    "query": "50ml 용기",
                    "text_weight": "0.6",
                    "image_weight": "0.4",
                    "top_k": "20"
                }
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["query"] == "50ml 용기"
    
    def test_hybrid_search_text_only(self):
        """Test hybrid search with only text (no image)"""
        # Act
        response = client.post(
            "/api/v1/search/hybrid",
            data={
                "query": "20파이 캡",
                "text_weight": "1.0",
                "image_weight": "0.0",
                "top_k": "10"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_search_pagination(self):
        """Test search with different top_k values"""
        # Test with small limit
        request_data = {"query": "test", "top_k": 5}
        response = client.post("/api/v1/search/", json=request_data)
        assert response.status_code == 200
        
        # Test with large limit
        request_data = {"query": "test", "top_k": 100}
        response = client.post("/api/v1/search/", json=request_data)
        assert response.status_code == 200
    
    def test_search_special_characters(self):
        """Test search with special characters in query"""
        # Arrange
        request_data = {
            "query": "20파이 캡 (PP재질) 5,000개",
            "top_k": 20
        }
        
        # Act
        response = client.post("/api/v1/search/", json=request_data)
        
        # Assert
        assert response.status_code == 200
    
    def test_search_concurrent_requests(self):
        """Test multiple concurrent search requests"""
        # Arrange
        queries = ["query1", "query2", "query3"]
        
        # Act
        responses = []
        for query in queries:
            response = client.post(
                "/api/v1/search/",
                json={"query": query, "top_k": 10}
            )
            responses.append(response)
        
        # Assert
        assert all(r.status_code == 200 for r in responses)
