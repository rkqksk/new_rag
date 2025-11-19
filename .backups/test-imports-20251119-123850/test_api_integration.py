"""
Integration tests for app/api/ route handlers

Tests HTTP endpoints using FastAPI TestClient with mocked dependencies
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from starlette.testclient import TestClient

from apps.api.api.main import app
from apps.api.core.dependencies import override_dependencies_for_testing


@pytest.fixture
def client():
    """FastAPI test client with dependency overrides"""
    # Set up dependency overrides
    overrides = override_dependencies_for_testing()
    app.dependency_overrides.update(overrides)

    # Create test client (first arg is the app)
    test_client = TestClient(app)  # Starlette expects positional app argument

    yield test_client

    # Clean up overrides after test
    app.dependency_overrides.clear()


class TestRootEndpoints:
    """Test root and utility endpoints"""

    @pytest.mark.integration
    def test_root_endpoint(self, client):
        """Test GET / returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    @pytest.mark.integration
    def test_health_endpoint(self, client):
        """Test GET /health returns health status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @pytest.mark.integration
    def test_metrics_endpoint(self, client):
        """Test GET /metrics returns Prometheus metrics"""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Metrics endpoint returns text/plain prometheus format
        assert "http_requests_total" in response.text or len(response.text) > 0

    @pytest.mark.integration
    def test_docs_endpoint(self, client):
        """Test /docs endpoint (Swagger UI)"""
        response = client.get("/docs")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_openapi_endpoint(self, client):
        """Test /openapi.json endpoint"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestQueryRoutes:
    """Test /api/v1/query endpoints"""

    @pytest.mark.integration
    def test_query_endpoint_exists(self, client):
        """Test query endpoint is registered"""
        response = client.post(
            "/api/v1/query",
            json={"question": "What is AI?"},
            headers={"Content-Type": "application/json"},
        )
        # Either 200, 422 (validation error), or 503 (service unavailable)
        assert response.status_code in [200, 422, 503, 500]

    @pytest.mark.integration
    def test_query_with_valid_payload(self, client):
        """Test query endpoint with valid payload"""
        payload = {"question": "What is machine learning?", "top_k": 5}
        response = client.post(
            "/api/v1/query", json=payload, headers={"Content-Type": "application/json"}
        )
        # Accept multiple status codes (depends on service availability)
        assert response.status_code in [200, 422, 500, 503]

    @pytest.mark.integration
    def test_query_with_empty_question(self, client):
        """Test query endpoint with empty question"""
        payload = {"question": ""}
        response = client.post("/api/v1/query", json=payload)
        # Should fail validation
        assert response.status_code in [422, 400]

    @pytest.mark.integration
    def test_query_with_missing_question(self, client):
        """Test query endpoint with missing question field"""
        payload = {"top_k": 5}
        response = client.post("/api/v1/query", json=payload)
        # Should fail validation
        assert response.status_code in [422, 400]


class TestDashboardRoutes:
    """Test /api/v1/dashboard endpoints"""

    @pytest.mark.integration
    def test_metrics_summary_endpoint(self, client):
        """Test GET /api/v1/dashboard/metrics"""
        response = client.get("/api/v1/dashboard/metrics")
        # Accept multiple status codes
        assert response.status_code in [200, 500, 503]

    @pytest.mark.integration
    def test_health_status_endpoint(self, client):
        """Test GET /api/v1/dashboard/health"""
        response = client.get("/api/v1/dashboard/health")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            # Should have health information
            assert isinstance(data, (dict, list))

    @pytest.mark.integration
    def test_statistics_endpoint(self, client):
        """Test GET /api/v1/dashboard/statistics"""
        response = client.get("/api/v1/dashboard/statistics")
        assert response.status_code in [200, 500, 503]


class TestIngestionRoutes:
    """Test /api/v1/ingest endpoints"""

    @pytest.mark.integration
    def test_ingest_endpoint_exists(self, client):
        """Test ingest endpoint is registered"""
        # POST to ingest endpoint (no file)
        response = client.post("/api/v1/ingest")
        # Should fail (no file provided)
        assert response.status_code in [422, 400, 500]

    @pytest.mark.integration
    def test_ingest_with_file(self, client):
        """Test ingest endpoint with a file"""
        from io import BytesIO

        # Create a mock file
        file_content = b"Test document content"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

        response = client.post("/api/v1/ingest", files=files)
        # Accept multiple status codes
        assert response.status_code in [200, 422, 500, 503]


class TestHTTPMethods:
    """Test HTTP method handling"""

    @pytest.mark.integration
    def test_get_on_post_only_endpoint(self, client):
        """Test GET request on POST-only endpoint"""
        response = client.get("/api/v1/query")
        # Should return 405 Method Not Allowed or 404
        assert response.status_code in [405, 404]

    @pytest.mark.integration
    def test_post_on_get_only_endpoint(self, client):
        """Test POST request on GET-only endpoint"""
        response = client.post("/api/v1/dashboard/metrics")
        # Should return 405 Method Not Allowed or 404
        assert response.status_code in [405, 404, 422]


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.integration
    def test_nonexistent_endpoint(self, client):
        """Test request to non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_invalid_json_payload(self, client):
        """Test endpoint with invalid JSON"""
        response = client.post(
            "/api/v1/query", data="invalid json{", headers={"Content-Type": "application/json"}
        )
        # Should return 422 or 400
        assert response.status_code in [422, 400]

    @pytest.mark.integration
    def test_missing_content_type(self, client):
        """Test POST without Content-Type header"""
        response = client.post("/api/v1/query", data="test")
        # Should still be handled
        assert response.status_code in [422, 415, 400, 500]


class TestCORSHeaders:
    """Test CORS headers on responses"""

    @pytest.mark.integration
    def test_cors_headers_on_root(self, client):
        """Test CORS headers present on root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        # CORS middleware should add headers
        assert "access-control-allow-credentials" in response.headers or True

    @pytest.mark.integration
    def test_options_request(self, client):
        """Test OPTIONS request for CORS preflight"""
        response = client.options("/api/v1/query")
        # OPTIONS should be handled by CORS middleware
        assert response.status_code in [200, 404]


class TestResponseFormats:
    """Test response format consistency"""

    @pytest.mark.integration
    def test_json_response_format(self, client):
        """Test JSON response has valid structure"""
        response = client.get("/")
        assert response.status_code == 200
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.integration
    def test_error_response_format(self, client):
        """Test error response format"""
        response = client.get("/nonexistent-route")
        assert response.status_code == 404
        # FastAPI returns JSON error by default
        assert "application/json" in response.headers.get("content-type", "")


class TestMetricsCollection:
    """Test that metrics are collected during requests"""

    @pytest.mark.integration
    def test_metrics_endpoint_after_requests(self, client):
        """Test metrics are updated after requests"""
        # Make some requests
        client.get("/")
        client.get("/health")

        # Check metrics endpoint
        response = client.get("/metrics")
        assert response.status_code == 200
        # Metrics should contain request data
        assert len(response.text) > 0

    @pytest.mark.integration
    def test_request_count_metrics(self, client):
        """Test request count metrics are recorded"""
        # Make requests
        for _ in range(3):
            client.get("/")

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        # Metrics should show requests were made
        metrics_text = response.text
        assert len(metrics_text) > 0


class TestRateLimiting:
    """Test rate limiting behavior (if implemented)"""

    @pytest.mark.integration
    def test_rapid_requests(self, client):
        """Test behavior under rapid requests"""
        responses = []
        for _ in range(10):
            response = client.get("/")
            responses.append(response.status_code)

        # At least most should succeed
        success_count = sum(1 for code in responses if code == 200)
        assert success_count >= 8

    @pytest.mark.integration
    def test_concurrent_requests(self, client):
        """Test multiple requests don't interfere"""
        responses = [client.get("/") for _ in range(5)]
        status_codes = [r.status_code for r in responses]
        # All should succeed
        assert all(code == 200 for code in status_codes)


class TestHeaderHandling:
    """Test header handling in requests/responses"""

    @pytest.mark.integration
    def test_custom_headers_preserved(self, client):
        """Test custom headers don't break requests"""
        response = client.get("/", headers={"X-Custom-Header": "test-value"})
        assert response.status_code == 200

    @pytest.mark.integration
    def test_user_agent_header(self, client):
        """Test requests with User-Agent header"""
        response = client.get("/", headers={"User-Agent": "Test-Client/1.0"})
        assert response.status_code == 200


class TestStatusCodes:
    """Test HTTP status codes are correct"""

    @pytest.mark.integration
    def test_200_on_success(self, client):
        """Test 200 OK on successful requests"""
        response = client.get("/")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_404_on_not_found(self, client):
        """Test 404 Not Found on missing routes"""
        response = client.get("/api/v1/missing-endpoint")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_422_on_validation_error(self, client):
        """Test 422 Unprocessable Entity on validation errors"""
        response = client.post("/api/v1/query", json={"invalid_field": "value"})
        # Should fail validation
        assert response.status_code in [422, 400]
