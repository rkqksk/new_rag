"""
Service Router
RAG Enterprise v10.0.0

Routes requests to appropriate services with dynamic activation/deactivation.
Manages service lifecycle and idle timeout.
"""

import asyncio
import importlib
import logging
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from .config import (
    ServiceStatus,
    ServiceConfig,
    get_default_config,
)
from .resource_manager import ResourceManager


logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    """Running service instance metadata"""

    name: str
    config: ServiceConfig
    status: ServiceStatus
    instance: Optional[Any] = None
    activated_at: Optional[datetime] = None
    last_request_at: Optional[datetime] = None
    request_count: int = 0
    error_count: int = 0
    deactivation_task: Optional[asyncio.Task] = None


class ServiceRouter:
    """
    Routes requests to services with dynamic activation/deactivation.

    Features:
    - On-demand service activation
    - Automatic deactivation after idle timeout
    - Priority-based activation
    - Graceful shutdown
    - Error handling and recovery
    """

    def __init__(
        self,
        resource_manager: Optional[ResourceManager] = None,
        auto_deactivation: bool = True,
    ):
        """
        Initialize service router.

        Args:
            resource_manager: Resource manager instance (creates new if None)
            auto_deactivation: Enable automatic deactivation on idle
        """
        self.config = get_default_config()
        self.resource_manager = resource_manager or ResourceManager()
        self.auto_deactivation = auto_deactivation

        self.services: Dict[str, ServiceInstance] = {}
        self.service_registry: Dict[str, ServiceConfig] = self.config.services.copy()
        self._lock = asyncio.Lock()

        logger.info(
            f"ServiceRouter initialized with {len(self.service_registry)} services, "
            f"auto_deactivation={auto_deactivation}"
        )

    async def initialize(self):
        """Initialize router and start monitoring."""
        await self.resource_manager.start_monitoring()

        # Auto-activate services with auto_activate=True
        auto_activate_services = [
            name for name, config in self.service_registry.items() if config.auto_activate
        ]

        if auto_activate_services:
            logger.info(f"Auto-activating services: {auto_activate_services}")
            for service_name in auto_activate_services:
                try:
                    await self.activate_service(service_name)
                except Exception as e:
                    logger.error(f"Failed to auto-activate {service_name}: {e}")

    async def shutdown(self):
        """Gracefully shutdown all services."""
        logger.info("Shutting down ServiceRouter")

        # Deactivate all services
        service_names = list(self.services.keys())
        for service_name in service_names:
            try:
                await self.deactivate_service(service_name)
            except Exception as e:
                logger.error(f"Error deactivating {service_name}: {e}")

        # Stop resource monitoring
        await self.resource_manager.stop_monitoring()

        logger.info("ServiceRouter shutdown complete")

    async def activate_service(self, service_name: str) -> tuple[bool, str]:
        """
        Activate a service dynamically.

        Args:
            service_name: Name of the service to activate

        Returns:
            Tuple of (success, message)
        """
        async with self._lock:
            # Check if service exists in registry
            if service_name not in self.service_registry:
                return False, f"Service '{service_name}' not found in registry"

            # Check if already active
            if service_name in self.services:
                service = self.services[service_name]
                if service.status == ServiceStatus.ACTIVE:
                    return True, f"Service '{service_name}' already active"
                elif service.status == ServiceStatus.ACTIVATING:
                    return True, f"Service '{service_name}' is activating"

            config = self.service_registry[service_name]

            # Create service instance
            service = ServiceInstance(
                name=service_name,
                config=config,
                status=ServiceStatus.ACTIVATING,
            )
            self.services[service_name] = service

            logger.info(f"Activating service: {service_name} (priority={config.priority})")

            try:
                # Allocate resources
                success, message = await self.resource_manager.allocate_resources(
                    service_name, config
                )
                if not success:
                    service.status = ServiceStatus.ERROR
                    return False, f"Resource allocation failed: {message}"

                # Check dependencies
                for dep in config.dependencies:
                    if (
                        dep not in self.services
                        or self.services[dep].status != ServiceStatus.ACTIVE
                    ):
                        logger.warning(f"Dependency '{dep}' not active, attempting to activate")
                        dep_success, dep_message = await self.activate_service(dep)
                        if not dep_success:
                            service.status = ServiceStatus.ERROR
                            await self.resource_manager.free_resources(service_name)
                            return False, f"Failed to activate dependency '{dep}': {dep_message}"

                # Import and initialize service
                try:
                    module = importlib.import_module(config.module_path)
                    # Try common initialization patterns
                    if hasattr(module, "get_service"):
                        service.instance = await module.get_service()
                    elif hasattr(module, "Service"):
                        service.instance = module.Service()
                    elif hasattr(module, "initialize"):
                        service.instance = await module.initialize()
                    else:
                        service.instance = module
                except ImportError as e:
                    logger.error(f"Failed to import module '{config.module_path}': {e}")
                    service.status = ServiceStatus.ERROR
                    await self.resource_manager.free_resources(service_name)
                    return False, f"Module import failed: {e}"
                except Exception as e:
                    logger.error(f"Failed to initialize service '{service_name}': {e}")
                    service.status = ServiceStatus.ERROR
                    await self.resource_manager.free_resources(service_name)
                    return False, f"Service initialization failed: {e}"

                # Mark as active
                service.status = ServiceStatus.ACTIVE
                service.activated_at = datetime.utcnow()

                logger.info(f"Service '{service_name}' activated successfully")
                return True, f"Service '{service_name}' activated"

            except Exception as e:
                logger.error(f"Unexpected error activating '{service_name}': {e}", exc_info=True)
                service.status = ServiceStatus.ERROR
                await self.resource_manager.free_resources(service_name)
                return False, f"Activation failed: {e}"

    async def deactivate_service(self, service_name: str, force: bool = False) -> tuple[bool, str]:
        """
        Deactivate a service gracefully.

        Args:
            service_name: Name of the service to deactivate
            force: Force deactivation even if dependencies exist

        Returns:
            Tuple of (success, message)
        """
        async with self._lock:
            if service_name not in self.services:
                return False, f"Service '{service_name}' not active"

            service = self.services[service_name]

            if service.status == ServiceStatus.DEACTIVATING:
                return True, f"Service '{service_name}' is already deactivating"

            # Check for dependent services
            if not force:
                dependents = self._get_dependent_services(service_name)
                if dependents:
                    return (
                        False,
                        f"Cannot deactivate: services {dependents} depend on '{service_name}'",
                    )

            logger.info(f"Deactivating service: {service_name}")
            service.status = ServiceStatus.DEACTIVATING

            try:
                # Cancel deactivation timer if exists
                if service.deactivation_task:
                    service.deactivation_task.cancel()
                    service.deactivation_task = None

                # Graceful shutdown
                if service.instance:
                    if hasattr(service.instance, "shutdown"):
                        try:
                            await service.instance.shutdown()
                        except Exception as e:
                            logger.warning(f"Error during service shutdown: {e}")
                    elif hasattr(service.instance, "close"):
                        try:
                            await service.instance.close()
                        except Exception as e:
                            logger.warning(f"Error during service close: {e}")

                # Free resources
                await self.resource_manager.free_resources(service_name)

                # Remove from active services
                del self.services[service_name]

                logger.info(f"Service '{service_name}' deactivated successfully")
                return True, f"Service '{service_name}' deactivated"

            except Exception as e:
                logger.error(f"Error deactivating '{service_name}': {e}", exc_info=True)
                service.status = ServiceStatus.ERROR
                return False, f"Deactivation failed: {e}"

    async def route_request(
        self, service_name: str, method: str, *args, **kwargs
    ) -> tuple[bool, Any]:
        """
        Route a request to the appropriate service.

        Args:
            service_name: Target service name
            method: Method name to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tuple of (success, result/error)
        """
        # Activate service if not active
        if (
            service_name not in self.services
            or self.services[service_name].status != ServiceStatus.ACTIVE
        ):
            success, message = await self.activate_service(service_name)
            if not success:
                logger.error(f"Failed to activate service for request: {message}")
                return False, message

        service = self.services[service_name]

        # Update request tracking
        service.last_request_at = datetime.utcnow()
        service.request_count += 1

        # Cancel pending deactivation
        if service.deactivation_task:
            service.deactivation_task.cancel()
            service.deactivation_task = None

        try:
            # Call the method
            if not hasattr(service.instance, method):
                return False, f"Method '{method}' not found on service '{service_name}'"

            method_func = getattr(service.instance, method)
            result = (
                await method_func(*args, **kwargs)
                if asyncio.iscoroutinefunction(method_func)
                else method_func(*args, **kwargs)
            )

            logger.debug(f"Request routed to {service_name}.{method} successfully")

            # Schedule deactivation if auto-deactivation enabled
            if self.auto_deactivation and service.config.idle_timeout_seconds > 0:
                service.deactivation_task = asyncio.create_task(
                    self._schedule_deactivation(service_name, service.config.idle_timeout_seconds)
                )

            return True, result

        except Exception as e:
            logger.error(f"Error executing {service_name}.{method}: {e}", exc_info=True)
            service.error_count += 1
            return False, str(e)

    async def _schedule_deactivation(self, service_name: str, timeout_seconds: int):
        """
        Schedule automatic deactivation after idle timeout.

        Args:
            service_name: Service to deactivate
            timeout_seconds: Idle timeout in seconds
        """
        try:
            await asyncio.sleep(timeout_seconds)

            # Check if still idle
            if service_name in self.services:
                service = self.services[service_name]
                if service.last_request_at:
                    idle_time = (datetime.utcnow() - service.last_request_at).total_seconds()
                    if idle_time >= timeout_seconds:
                        logger.info(f"Auto-deactivating idle service: {service_name}")
                        await self.deactivate_service(service_name)
        except asyncio.CancelledError:
            # Deactivation cancelled (new request came in)
            pass
        except Exception as e:
            logger.error(f"Error in scheduled deactivation: {e}", exc_info=True)

    def _get_dependent_services(self, service_name: str) -> Set[str]:
        """
        Get services that depend on the given service.

        Args:
            service_name: Service to check dependencies for

        Returns:
            Set of dependent service names
        """
        dependents = set()
        for name, service in self.services.items():
            if service_name in service.config.dependencies:
                dependents.add(name)
        return dependents

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a service.

        Args:
            service_name: Name of the service

        Returns:
            Dictionary with service status or None if not found
        """
        if service_name not in self.services:
            return None

        service = self.services[service_name]
        return {
            "name": service.name,
            "status": service.status.value,
            "priority": service.config.priority.value,
            "activated_at": service.activated_at.isoformat() if service.activated_at else None,
            "last_request_at": (
                service.last_request_at.isoformat() if service.last_request_at else None
            ),
            "request_count": service.request_count,
            "error_count": service.error_count,
            "idle_timeout_seconds": service.config.idle_timeout_seconds,
        }

    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status for all services.

        Returns:
            Dictionary mapping service names to status info
        """
        return {name: self.get_service_status(name) for name in self.services.keys()}

    def list_available_services(self) -> Dict[str, ServiceConfig]:
        """
        List all available services in the registry.

        Returns:
            Dictionary of service configurations
        """
        return self.service_registry.copy()
