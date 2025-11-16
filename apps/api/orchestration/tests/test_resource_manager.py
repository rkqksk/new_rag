"""
Resource Manager Tests
RAG Enterprise v10.0.0

Unit tests for ResourceManager class.
"""

import pytest
import asyncio
from apps.api.orchestration import (
    ResourceManager,
    ResourceLimits,
    ServiceConfig,
    ServicePriority,
)


@pytest.mark.asyncio
class TestResourceManager:
    """Test ResourceManager functionality"""

    async def test_initialization(self):
        """Test resource manager initialization"""
        limits = ResourceLimits(
            cpu_percent_max=80.0,
            memory_gb_max=8.0,
            gpu_percent_max=100.0,
        )
        manager = ResourceManager(limits=limits)

        assert manager.limits.cpu_percent_max == 80.0
        assert manager.limits.memory_gb_max == 8.0
        assert len(manager.allocations) == 0

    async def test_get_current_usage(self):
        """Test getting current system usage"""
        manager = ResourceManager()
        resources = await manager.get_current_usage()

        assert resources.cpu_percent >= 0
        assert resources.memory_gb_used > 0
        assert resources.memory_gb_total > 0
        assert resources.disk_gb_used > 0

    async def test_allocate_resources_success(self):
        """Test successful resource allocation"""
        manager = ResourceManager()

        service_config = ServiceConfig(
            name="test_service",
            module_path="test.module",
            priority=ServicePriority.MEDIUM,
            cpu_allocation=1.0,
            memory_allocation_gb=1.0,
        )

        success, message = await manager.allocate_resources("test_service", service_config)

        assert success is True
        assert "test_service" in manager.allocations
        assert manager.allocations["test_service"].cpu_cores == 1.0
        assert manager.allocations["test_service"].memory_gb == 1.0

    async def test_allocate_resources_duplicate(self):
        """Test allocating resources for already allocated service"""
        manager = ResourceManager()

        service_config = ServiceConfig(
            name="test_service",
            module_path="test.module",
            priority=ServicePriority.MEDIUM,
            cpu_allocation=1.0,
            memory_allocation_gb=1.0,
        )

        # First allocation
        await manager.allocate_resources("test_service", service_config)

        # Second allocation (should succeed with message)
        success, message = await manager.allocate_resources("test_service", service_config)

        assert success is True
        assert "already allocated" in message.lower()

    async def test_free_resources(self):
        """Test freeing allocated resources"""
        manager = ResourceManager()

        service_config = ServiceConfig(
            name="test_service",
            module_path="test.module",
            priority=ServicePriority.MEDIUM,
            cpu_allocation=1.0,
            memory_allocation_gb=1.0,
        )

        # Allocate
        await manager.allocate_resources("test_service", service_config)

        # Free
        success, message = await manager.free_resources("test_service")

        assert success is True
        assert "test_service" not in manager.allocations

    async def test_free_resources_not_allocated(self):
        """Test freeing non-allocated resources"""
        manager = ResourceManager()

        success, message = await manager.free_resources("nonexistent_service")

        assert success is False
        assert "no resources allocated" in message.lower()

    async def test_get_allocation(self):
        """Test getting specific allocation"""
        manager = ResourceManager()

        service_config = ServiceConfig(
            name="test_service",
            module_path="test.module",
            priority=ServicePriority.MEDIUM,
            cpu_allocation=1.0,
            memory_allocation_gb=1.0,
        )

        await manager.allocate_resources("test_service", service_config)

        allocation = manager.get_allocation("test_service")

        assert allocation is not None
        assert allocation.service_name == "test_service"
        assert allocation.cpu_cores == 1.0

    async def test_get_all_allocations(self):
        """Test getting all allocations"""
        manager = ResourceManager()

        config1 = ServiceConfig(
            name="service1",
            module_path="test.module",
            priority=ServicePriority.HIGH,
            cpu_allocation=2.0,
            memory_allocation_gb=2.0,
        )

        config2 = ServiceConfig(
            name="service2",
            module_path="test.module",
            priority=ServicePriority.LOW,
            cpu_allocation=1.0,
            memory_allocation_gb=1.0,
        )

        await manager.allocate_resources("service1", config1)
        await manager.allocate_resources("service2", config2)

        allocations = manager.get_all_allocations()

        assert len(allocations) == 2
        assert "service1" in allocations
        assert "service2" in allocations

    async def test_resource_summary(self):
        """Test getting resource summary"""
        manager = ResourceManager()

        service_config = ServiceConfig(
            name="test_service",
            module_path="test.module",
            priority=ServicePriority.MEDIUM,
            cpu_allocation=1.0,
            memory_allocation_gb=1.0,
        )

        await manager.allocate_resources("test_service", service_config)

        summary = await manager.get_resource_summary()

        assert "current_usage" in summary
        assert "limits" in summary
        assert "allocated" in summary
        assert "available" in summary
        assert summary["allocated"]["service_count"] == 1

    async def test_start_stop_monitoring(self):
        """Test monitoring lifecycle"""
        manager = ResourceManager()

        # Start monitoring
        await manager.start_monitoring(interval_seconds=1)
        assert manager.monitoring_task is not None
        assert not manager.monitoring_task.done()

        # Give it a moment to run
        await asyncio.sleep(0.1)

        # Stop monitoring
        await manager.stop_monitoring()
        assert manager.monitoring_task.done()


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
