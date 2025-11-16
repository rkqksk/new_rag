"""
Resource Manager
RAG Enterprise v10.0.0

Manages CPU, memory, GPU resources optimally with priority-based allocation.
Monitors system resources and prevents overload.
"""

import asyncio
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import psutil

from .config import (
    ServicePriority,
    ServiceConfig,
    ResourceLimits,
    get_default_config,
)


logger = logging.getLogger(__name__)


@dataclass
class ResourceAllocation:
    """Resource allocation for a service"""
    service_name: str
    cpu_cores: float
    memory_gb: float
    gpu_allocation: float
    priority: ServicePriority
    allocated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SystemResources:
    """Current system resource usage"""
    cpu_percent: float
    memory_gb_used: float
    memory_gb_total: float
    memory_percent: float
    disk_gb_used: float
    disk_gb_total: float
    disk_percent: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ResourceManager:
    """
    Manages system resources for services with priority-based allocation.

    Features:
    - Real-time resource monitoring
    - Priority-based allocation
    - Automatic throttling
    - Resource limit enforcement
    """

    def __init__(self, limits: Optional[ResourceLimits] = None):
        """
        Initialize resource manager.

        Args:
            limits: Resource limits configuration (uses defaults if None)
        """
        config = get_default_config()
        self.limits = limits or config.resources
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self._current_resources: Optional[SystemResources] = None
        self._lock = asyncio.Lock()

        logger.info(
            f"ResourceManager initialized with limits: "
            f"CPU={self.limits.cpu_percent_max}%, "
            f"Memory={self.limits.memory_gb_max}GB, "
            f"GPU={self.limits.gpu_percent_max}%"
        )

    async def start_monitoring(self, interval_seconds: int = 30):
        """
        Start background resource monitoring.

        Args:
            interval_seconds: Monitoring interval in seconds
        """
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("Monitoring already running")
            return

        logger.info(f"Starting resource monitoring (interval={interval_seconds}s)")
        self.monitoring_task = asyncio.create_task(
            self._monitor_loop(interval_seconds)
        )

    async def stop_monitoring(self):
        """Stop background resource monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Resource monitoring stopped")

    async def _monitor_loop(self, interval_seconds: int):
        """
        Background monitoring loop.

        Args:
            interval_seconds: Monitoring interval
        """
        while True:
            try:
                self._current_resources = await self.get_current_usage()
                await self._check_resource_pressure()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(interval_seconds)

    async def get_current_usage(self) -> SystemResources:
        """
        Get current system resource usage.

        Returns:
            SystemResources: Current resource usage snapshot
        """
        # Run blocking psutil calls in executor
        loop = asyncio.get_event_loop()

        cpu_percent = await loop.run_in_executor(
            None, psutil.cpu_percent, 0.1
        )

        memory = await loop.run_in_executor(None, psutil.virtual_memory)
        disk = await loop.run_in_executor(None, psutil.disk_usage, '/')

        resources = SystemResources(
            cpu_percent=cpu_percent,
            memory_gb_used=memory.used / (1024 ** 3),
            memory_gb_total=memory.total / (1024 ** 3),
            memory_percent=memory.percent,
            disk_gb_used=disk.used / (1024 ** 3),
            disk_gb_total=disk.total / (1024 ** 3),
            disk_percent=disk.percent,
        )

        return resources

    async def allocate_resources(
        self,
        service_name: str,
        service_config: ServiceConfig,
    ) -> Tuple[bool, str]:
        """
        Allocate resources for a service.

        Args:
            service_name: Name of the service
            service_config: Service configuration

        Returns:
            Tuple of (success, message)
        """
        async with self._lock:
            # Check if already allocated
            if service_name in self.allocations:
                return True, f"Resources already allocated for {service_name}"

            # Get current usage
            current = await self.get_current_usage()

            # Calculate total allocated resources
            total_cpu = sum(a.cpu_cores for a in self.allocations.values())
            total_memory = sum(a.memory_gb for a in self.allocations.values())
            total_gpu = sum(a.gpu_allocation for a in self.allocations.values())

            # Check if we can allocate
            cpu_cores_available = psutil.cpu_count() * (self.limits.cpu_percent_max / 100.0)
            requested_cpu = service_config.cpu_allocation

            if total_cpu + requested_cpu > cpu_cores_available:
                # Try throttling low priority services
                await self._throttle_low_priority_services(service_config.priority)

                # Recalculate
                total_cpu = sum(a.cpu_cores for a in self.allocations.values())
                if total_cpu + requested_cpu > cpu_cores_available:
                    return False, f"Insufficient CPU resources (need {requested_cpu}, available {cpu_cores_available - total_cpu})"

            if total_memory + service_config.memory_allocation_gb > self.limits.memory_gb_max:
                return False, f"Insufficient memory (need {service_config.memory_allocation_gb}GB, max {self.limits.memory_gb_max}GB)"

            if total_gpu + service_config.gpu_allocation > self.limits.gpu_percent_max / 100.0:
                return False, f"Insufficient GPU resources (need {service_config.gpu_allocation}, max {self.limits.gpu_percent_max / 100.0})"

            # Allocate resources
            allocation = ResourceAllocation(
                service_name=service_name,
                cpu_cores=requested_cpu,
                memory_gb=service_config.memory_allocation_gb,
                gpu_allocation=service_config.gpu_allocation,
                priority=service_config.priority,
            )

            self.allocations[service_name] = allocation

            logger.info(
                f"Allocated resources for {service_name}: "
                f"CPU={requested_cpu} cores, "
                f"Memory={service_config.memory_allocation_gb}GB, "
                f"GPU={service_config.gpu_allocation}, "
                f"Priority={service_config.priority}"
            )

            return True, "Resources allocated successfully"

    async def free_resources(self, service_name: str) -> Tuple[bool, str]:
        """
        Free resources allocated to a service.

        Args:
            service_name: Name of the service

        Returns:
            Tuple of (success, message)
        """
        async with self._lock:
            if service_name not in self.allocations:
                return False, f"No resources allocated for {service_name}"

            allocation = self.allocations.pop(service_name)

            logger.info(
                f"Freed resources for {service_name}: "
                f"CPU={allocation.cpu_cores} cores, "
                f"Memory={allocation.memory_gb}GB, "
                f"GPU={allocation.gpu_allocation}"
            )

            return True, "Resources freed successfully"

    async def _throttle_low_priority_services(self, requesting_priority: ServicePriority):
        """
        Throttle low priority services to make room for higher priority.

        Args:
            requesting_priority: Priority of the requesting service
        """
        priority_order = {
            ServicePriority.LOW: 0,
            ServicePriority.MEDIUM: 1,
            ServicePriority.HIGH: 2,
        }

        requesting_level = priority_order[requesting_priority]

        # Find services with lower priority
        to_throttle = [
            (name, alloc) for name, alloc in self.allocations.items()
            if priority_order[alloc.priority] < requesting_level
        ]

        if not to_throttle:
            return

        logger.warning(
            f"Throttling {len(to_throttle)} low-priority services to make room for {requesting_priority} priority service"
        )

        for service_name, allocation in to_throttle:
            # Reduce allocation by 50%
            allocation.cpu_cores *= 0.5
            allocation.memory_gb *= 0.5
            logger.info(f"Throttled {service_name} to 50% resources")

    async def _check_resource_pressure(self):
        """Check for resource pressure and log warnings."""
        if not self._current_resources:
            return

        resources = self._current_resources

        if resources.cpu_percent > self.limits.cpu_percent_max:
            logger.warning(
                f"CPU usage ({resources.cpu_percent:.1f}%) exceeds limit ({self.limits.cpu_percent_max}%)"
            )

        if resources.memory_gb_used > self.limits.memory_gb_max:
            logger.warning(
                f"Memory usage ({resources.memory_gb_used:.1f}GB) exceeds limit ({self.limits.memory_gb_max}GB)"
            )

        if resources.disk_gb_used > self.limits.disk_gb_max:
            logger.warning(
                f"Disk usage ({resources.disk_gb_used:.1f}GB) exceeds limit ({self.limits.disk_gb_max}GB)"
            )

    def get_allocation(self, service_name: str) -> Optional[ResourceAllocation]:
        """
        Get resource allocation for a service.

        Args:
            service_name: Name of the service

        Returns:
            ResourceAllocation or None if not allocated
        """
        return self.allocations.get(service_name)

    def get_all_allocations(self) -> Dict[str, ResourceAllocation]:
        """
        Get all current resource allocations.

        Returns:
            Dictionary of service name to allocation
        """
        return self.allocations.copy()

    async def get_resource_summary(self) -> Dict[str, any]:
        """
        Get a summary of resource usage and allocations.

        Returns:
            Dictionary with resource summary
        """
        current = await self.get_current_usage()

        total_allocated_cpu = sum(a.cpu_cores for a in self.allocations.values())
        total_allocated_memory = sum(a.memory_gb for a in self.allocations.values())
        total_allocated_gpu = sum(a.gpu_allocation for a in self.allocations.values())

        return {
            "current_usage": {
                "cpu_percent": current.cpu_percent,
                "memory_gb": current.memory_gb_used,
                "memory_percent": current.memory_percent,
                "disk_gb": current.disk_gb_used,
                "disk_percent": current.disk_percent,
            },
            "limits": {
                "cpu_percent_max": self.limits.cpu_percent_max,
                "memory_gb_max": self.limits.memory_gb_max,
                "gpu_percent_max": self.limits.gpu_percent_max,
                "disk_gb_max": self.limits.disk_gb_max,
            },
            "allocated": {
                "cpu_cores": total_allocated_cpu,
                "memory_gb": total_allocated_memory,
                "gpu_allocation": total_allocated_gpu,
                "service_count": len(self.allocations),
            },
            "available": {
                "cpu_cores": psutil.cpu_count() * (self.limits.cpu_percent_max / 100.0) - total_allocated_cpu,
                "memory_gb": self.limits.memory_gb_max - total_allocated_memory,
                "gpu_allocation": (self.limits.gpu_percent_max / 100.0) - total_allocated_gpu,
            },
        }
