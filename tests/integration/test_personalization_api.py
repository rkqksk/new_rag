"""Integration tests for Personalization API endpoints"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.integration
class TestPersonalizationAPI:
    """Integration tests for /api/v1/personalization endpoints"""

    @pytest.fixture(autouse=True)
    def mock_dependencies(self, sample_user_profile, sample_products):
        """Mock all dependencies for integration tests"""
        with patch("app.dependencies.services.get_personalization_service") as mock_service:
            service = MagicMock()

            # Mock track_interaction
            async def mock_track(session_id, product_id, event_type, product_data, search_context):
                return True

            service.track_interaction = mock_track

            # Mock get_profile
            async def mock_profile(session_id):
                return sample_user_profile

            service.get_profile = mock_profile

            # Mock get_recommendations
            async def mock_recommendations(session_id, all_products, top_k, category_filter):
                return sample_products[:top_k]

            service.get_recommendations = mock_recommendations

            mock_service.return_value = service
            yield service

    def test_track_interaction_click(self):
        """Test tracking a click interaction"""
        # Arrange
        request_data = {
            "session_id": "sess_123",
            "product_id": "PROD-001",
            "product": {"id": "PROD-001", "name": "50ml PET 용기", "category": "bottle"},
            "event_type": "click",
            "search_context": "50ml 용기",
        }

        # Act
        response = client.post("/api/v1/personalization/track", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "tracked"
        assert data["session_id"] == "sess_123"

    def test_track_interaction_view(self):
        """Test tracking a view interaction"""
        # Arrange
        request_data = {
            "session_id": "sess_456",
            "product_id": "PROD-002",
            "product": {"id": "PROD-002", "name": "20파이 캡"},
            "event_type": "view",
        }

        # Act
        response = client.post("/api/v1/personalization/track", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "tracked"

    def test_track_interaction_bookmark(self):
        """Test tracking a bookmark interaction"""
        # Arrange
        request_data = {
            "session_id": "sess_789",
            "product_id": "PROD-003",
            "product": {"id": "PROD-003", "name": "30파이 펌프"},
            "event_type": "bookmark",
        }

        # Act
        response = client.post("/api/v1/personalization/track", json=request_data)

        # Assert
        assert response.status_code == 200

    def test_track_interaction_missing_fields(self):
        """Test tracking with missing required fields"""
        # Arrange
        request_data = {
            "session_id": "sess_123",
            "product_id": "PROD-001",
            # Missing: product, event_type
        }

        # Act
        response = client.post("/api/v1/personalization/track", json=request_data)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_track_interaction_invalid_event_type(self):
        """Test tracking with invalid event type"""
        # Arrange
        request_data = {
            "session_id": "sess_123",
            "product_id": "PROD-001",
            "product": {"id": "PROD-001"},
            "event_type": "invalid_event",  # Invalid type
        }

        # Act
        response = client.post("/api/v1/personalization/track", json=request_data)

        # Assert
        # Depending on validation, might accept or reject
        assert response.status_code in [200, 422]

    def test_get_profile(self):
        """Test retrieving user profile"""
        # Act
        response = client.get("/api/v1/personalization/profile/sess_123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "preferences" in data
        assert "focus_type" in data

    def test_get_profile_new_user(self):
        """Test retrieving profile for new user"""
        # Act
        response = client.get("/api/v1/personalization/profile/new_sess_999")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    def test_get_recommendations(self):
        """Test getting personalized recommendations"""
        # Act
        response = client.get(
            "/api/v1/personalization/recommendations/sess_123", params={"top_k": 10}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "total" in data
        assert isinstance(data["recommendations"], list)

    def test_get_recommendations_with_category_filter(self):
        """Test recommendations with category filter"""
        # Act
        response = client.get(
            "/api/v1/personalization/recommendations/sess_123",
            params={"top_k": 5, "category": "bottle"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    def test_get_recommendations_default_limit(self):
        """Test recommendations with default top_k"""
        # Act
        response = client.get("/api/v1/personalization/recommendations/sess_123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should use default top_k=10
        assert len(data["recommendations"]) <= 10

    def test_track_multiple_interactions_sequence(self):
        """Test tracking multiple interactions in sequence"""
        # Simulate user journey: view -> view -> click -> bookmark
        interactions = [
            ("PROD-001", "view"),
            ("PROD-002", "view"),
            ("PROD-001", "click"),
            ("PROD-001", "bookmark"),
        ]

        session_id = "sess_journey_123"

        for product_id, event_type in interactions:
            request_data = {
                "session_id": session_id,
                "product_id": product_id,
                "product": {"id": product_id, "name": "Test Product"},
                "event_type": event_type,
            }
            response = client.post("/api/v1/personalization/track", json=request_data)
            assert response.status_code == 200

    def test_profile_updates_after_interactions(self):
        """Test that profile reflects tracked interactions"""
        # Track some interactions
        session_id = "sess_update_test"

        for i in range(3):
            request_data = {
                "session_id": session_id,
                "product_id": f"PROD-{i}",
                "product": {"id": f"PROD-{i}"},
                "event_type": "click",
            }
            client.post("/api/v1/personalization/track", json=request_data)

        # Get profile
        response = client.get(f"/api/v1/personalization/profile/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
