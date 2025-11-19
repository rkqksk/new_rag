"""Unit tests for PersonalizationService"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.services.personalization_service import PersonalizationService


@pytest.mark.unit
class TestPersonalizationService:
    """Test cases for PersonalizationService"""

    @pytest.fixture
    def service(self, mock_redis_repo, mock_postgres_repo):
        """Create service instance with mocked dependencies"""
        with patch(
            "app.services.personalization_service.AdvancedPersonalizationService"
        ) as mock_service_class:
            service = PersonalizationService(
                redis_repo=mock_redis_repo, postgres_repo=mock_postgres_repo
            )

            # Attach mock for assertions
            service.service_mock = mock_service_class.return_value

            yield service

    @pytest.mark.asyncio
    async def test_track_search(self, service, sample_session_id):
        """Test tracking a search event"""
        # Arrange
        query = "50ml PET 용기"
        results_count = 10
        previous_context = None

        service.service_mock.track_search.return_value = True

        # Act
        success = await service.track_search(
            session_id=sample_session_id,
            query=query,
            results_count=results_count,
            previous_context=previous_context,
        )

        # Assert
        assert success is True
        service.service_mock.track_search.assert_called_once_with(
            session_id=sample_session_id,
            query=query,
            results_count=results_count,
            previous_context=previous_context,
        )

    @pytest.mark.asyncio
    async def test_track_interaction_click(self, service, sample_session_id, sample_product):
        """Test tracking a product click"""
        # Arrange
        product_id = sample_product["id"]
        event_type = "click"
        search_context = "50ml 용기"

        service.service_mock.track_interaction.return_value = True

        # Act
        success = await service.track_interaction(
            session_id=sample_session_id,
            product_id=product_id,
            event_type=event_type,
            product_data=sample_product,
            search_context=search_context,
        )

        # Assert
        assert success is True
        service.service_mock.track_interaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_interaction_view(self, service, sample_session_id, sample_product):
        """Test tracking a product view"""
        # Arrange
        event_type = "view"

        service.service_mock.track_interaction.return_value = True

        # Act
        success = await service.track_interaction(
            session_id=sample_session_id,
            product_id=sample_product["id"],
            event_type=event_type,
            product_data=sample_product,
            search_context=None,
        )

        # Assert
        assert success is True

    @pytest.mark.asyncio
    async def test_track_interaction_bookmark(self, service, sample_session_id, sample_product):
        """Test tracking a product bookmark"""
        # Arrange
        event_type = "bookmark"

        service.service_mock.track_interaction.return_value = True

        # Act
        success = await service.track_interaction(
            session_id=sample_session_id,
            product_id=sample_product["id"],
            event_type=event_type,
            product_data=sample_product,
            search_context=None,
        )

        # Assert
        assert success is True

    @pytest.mark.asyncio
    async def test_get_profile_existing_user(self, service, sample_session_id, sample_user_profile):
        """Test retrieving existing user profile"""
        # Arrange
        service.service_mock.get_profile.return_value = sample_user_profile

        # Act
        profile = await service.get_profile(sample_session_id)

        # Assert
        assert profile is not None
        assert profile["session_id"] == sample_session_id
        assert "preferences" in profile
        assert "focus_type" in profile
        service.service_mock.get_profile.assert_called_once_with(sample_session_id)

    @pytest.mark.asyncio
    async def test_get_profile_new_user(self, service, sample_session_id):
        """Test retrieving profile for new user"""
        # Arrange
        # New user has empty profile
        new_user_profile = {
            "session_id": sample_session_id,
            "search_history": [],
            "viewed_products": [],
            "clicked_products": [],
            "preferences": {},
            "focus_type": None,
        }
        service.service_mock.get_profile.return_value = new_user_profile

        # Act
        profile = await service.get_profile(sample_session_id)

        # Assert
        assert profile["session_id"] == sample_session_id
        assert len(profile["search_history"]) == 0

    @pytest.mark.asyncio
    async def test_get_recommendations_with_products(
        self, service, sample_session_id, sample_products
    ):
        """Test getting personalized recommendations"""
        # Arrange
        all_products = sample_products
        top_k = 5

        # Mock returns top products
        recommended = sample_products[:2]
        service.service_mock.get_recommendations.return_value = recommended

        # Act
        recommendations = await service.get_recommendations(
            session_id=sample_session_id,
            all_products=all_products,
            top_k=top_k,
            category_filter=None,
        )

        # Assert
        assert len(recommendations) == 2
        service.service_mock.get_recommendations.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recommendations_with_category_filter(
        self, service, sample_session_id, sample_products
    ):
        """Test recommendations with category filter"""
        # Arrange
        category_filter = "bottle"

        # Mock returns only bottles
        bottle_products = [p for p in sample_products if p.get("category") == "bottle"]
        service.service_mock.get_recommendations.return_value = bottle_products

        # Act
        recommendations = await service.get_recommendations(
            session_id=sample_session_id,
            all_products=sample_products,
            top_k=10,
            category_filter=category_filter,
        )

        # Assert
        assert all(p.get("category") == "bottle" for p in recommendations)

    @pytest.mark.asyncio
    async def test_get_recommendations_empty_products(self, service, sample_session_id):
        """Test recommendations with no products available"""
        # Arrange
        all_products = []
        service.service_mock.get_recommendations.return_value = []

        # Act
        recommendations = await service.get_recommendations(
            session_id=sample_session_id, all_products=all_products, top_k=10, category_filter=None
        )

        # Assert
        assert len(recommendations) == 0

    @pytest.mark.asyncio
    async def test_adaptive_weights_supplier_focused(self, service, sample_session_id):
        """Test that supplier-focused user gets appropriate profile"""
        # Arrange
        # User who searches by supplier names a lot
        supplier_profile = {
            "session_id": sample_session_id,
            "search_history": ["천진코리아 용기", "원하고 캡", "프리몰드 펌프"],
            "focus_type": "supplier",
            "preferences": {"suppliers": {"천진코리아": 0.8, "원하고": 0.6}},
        }
        service.service_mock.get_profile.return_value = supplier_profile

        # Act
        profile = await service.get_profile(sample_session_id)

        # Assert
        assert profile["focus_type"] == "supplier"
        assert "천진코리아" in profile["preferences"]["suppliers"]

    @pytest.mark.asyncio
    async def test_adaptive_weights_compatibility_focused(self, service, sample_session_id):
        """Test that compatibility-focused user gets appropriate profile"""
        # Arrange
        compatibility_profile = {
            "session_id": sample_session_id,
            "search_history": ["20파이 용기", "20파이 캡"],
            "focus_type": "compatibility",
            "preferences": {"neck_sizes": {"20파이": 0.9}},
        }
        service.service_mock.get_profile.return_value = compatibility_profile

        # Act
        profile = await service.get_profile(sample_session_id)

        # Assert
        assert profile["focus_type"] == "compatibility"

    @pytest.mark.asyncio
    async def test_track_interaction_failure(self, service, sample_session_id, sample_product):
        """Test handling of tracking failure"""
        # Arrange
        service.service_mock.track_interaction.return_value = False

        # Act
        success = await service.track_interaction(
            session_id=sample_session_id,
            product_id=sample_product["id"],
            event_type="click",
            product_data=sample_product,
            search_context=None,
        )

        # Assert
        assert success is False
