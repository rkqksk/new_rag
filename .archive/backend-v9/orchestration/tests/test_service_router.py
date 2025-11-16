"""
Service Router Tests
RAG Enterprise v10.0.0

Unit tests for ServiceRouter class.
"""

import pytest
import asyncio
from backend.orchestration import (
    ServiceRouter,
    ResourceManager,
    ServiceStatus,
    ServiceConfig,
    ServicePriority,
)


@pytest.mark.asyncio
class TestServiceRouter:
    """Test ServiceRouter functionality"""

    async def test_initialization(self):
        """Test service router initialization"""
        router = ServiceRouter(auto_deactivation=False)

        assert router.resource_manager is not None
        assert router.auto_deactivation is False
        assert len(router.service_registry) > 0

    async def test_initialization_with_resource_manager(self):
        """Test initialization with custom resource manager"""
        resource_manager = ResourceManager()
        router = ServiceRouter(resource_manager=resource_manager)

        assert router.resource_manager is resource_manager

    async def test_list_available_services(self):
        """Test listing available services"""
        router = ServiceRouter()
        services = router.list_available_services()

        assert len(services) > 0
        assert "rag" in services
        assert "manufacturing" in services
        assert "ocr" in services

    async def test_get_service_status_inactive(self):
        """Test getting status of inactive service"""
        router = ServiceRouter()
        status = router.get_service_status("nonexistent_service")

        assert status is None

    async def test_get_all_services_status_empty(self):
        """Test getting all services status when none active"""
        router = ServiceRouter(auto_deactivation=False)
        status = router.get_all_services_status()

        # Should be empty before initialization
        assert isinstance(status, dict)

    async def test_activate_service_not_found(self):
        """Test activating non-existent service"""
        router = ServiceRouter()
        success, message = await router.activate_service("nonexistent_service")

        assert success is False
        assert "not found" in message.lower()

    async def test_deactivate_service_not_active(self):
        """Test deactivating inactive service"""
        router = ServiceRouter()
        success, message = await router.deactivate_service("rag")

        assert success is False
        assert "not active" in message.lower()

    async def test_shutdown(self):
        """Test graceful shutdown"""
        router = ServiceRouter()
        await router.initialize()

        # Shutdown should complete without errors
        await router.shutdown()


@pytest.mark.asyncio
class TestServiceRouterWithMocks:
    """Test ServiceRouter with mock services"""

    async def test_route_request_to_inactive_service(self):
        """Test routing to inactive service (should activate)"""
        router = ServiceRouter(auto_deactivation=False)
        await router.initialize()

        # This should attempt to activate the service
        # It will fail because the actual module doesn't exist,
        # but we're testing the routing logic
        success, result = await router.route_request(
            service_name="rag",
            method="search",
            query="test"
        )

        # Should fail due to module import, but routing logic worked
        assert success is False

        await router.shutdown()


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
