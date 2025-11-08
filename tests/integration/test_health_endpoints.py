"""Integration tests for health check endpoints"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check endpoints"""

    def test_liveness_probe(self):
        """Test liveness probe endpoint"""
        # Act
        response = client.get("/health/live")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "alive"

    def test_readiness_probe(self):
        """Test readiness probe endpoint"""
        # Act
        response = client.get("/health/ready")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        # In tests, dependencies are mocked so it should be ready

    def test_health_check_format(self):
        """Test health check response format"""
        # Act
        response = client.get("/health/live")

        # Assert
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_api_docs_accessible(self):
        """Test that API documentation is accessible"""
        # Act
        response = client.get("/api/v1/docs")

        # Assert
        assert response.status_code == 200

    def test_openapi_schema_accessible(self):
        """Test that OpenAPI schema is accessible"""
        # Act
        response = client.get("/api/v1/openapi.json")

        # Assert
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
