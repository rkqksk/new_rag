"""
Orchestration System
RAG Enterprise v10.0.0

Dynamic service orchestration with resource management, task dispatch,
and feature tracking for optimized hardware usage.

Usage:
    from apps.api.orchestration import (
        ServiceRouter,
        ResourceManager,
        TaskDispatcher,
        FeatureRegistry,
        OrchestrationConfig,
    )

    # Initialize orchestration system
    resource_manager = ResourceManager()
    service_router = ServiceRouter(resource_manager=resource_manager)
    task_dispatcher = TaskDispatcher()
    feature_registry = FeatureRegistry()

    # Start system
    await service_router.initialize()

    # Route a request
    success, result = await service_router.route_request(
        service_name="rag",
        method="search",
        query="50ml PET bottle"
    )

    # Dispatch a task
    success, result = await task_dispatcher.dispatch_task(
        description="Explore RAG codebase",
        handler=my_handler_function,
        complexity=TaskComplexity.MEDIUM,
    )

    # Activate a feature
    success, message = feature_registry.activate("ocr_processing")

    # Shutdown
    await service_router.shutdown()
"""

from .config import (
    OrchestrationConfig,
    ServiceConfig,
    AgentConfig,
    ResourceLimits,
    ServicePriority,
    ServiceStatus,
    AgentType,
    TaskComplexity,
    get_default_config,
    get_service_config,
    get_agent_config,
)

from .feature_registry import (
    FeatureRegistry,
    Feature,
    FeatureCategory,
    FeatureStatus,
)

from .resource_manager import (
    ResourceManager,
    ResourceAllocation,
    SystemResources,
)

from .service_router import (
    ServiceRouter,
    ServiceInstance,
)

from .task_dispatcher import (
    TaskDispatcher,
    Task,
    AgentInstance,
)


__all__ = [
    # Configuration
    "OrchestrationConfig",
    "ServiceConfig",
    "AgentConfig",
    "ResourceLimits",
    "ServicePriority",
    "ServiceStatus",
    "AgentType",
    "TaskComplexity",
    "FeatureCategory",
    "FeatureStatus",
    "get_default_config",
    "get_service_config",
    "get_agent_config",
    # Resource Management
    "ResourceManager",
    "ResourceAllocation",
    "SystemResources",
    # Service Routing
    "ServiceRouter",
    "ServiceInstance",
    # Task Dispatch
    "TaskDispatcher",
    "Task",
    "AgentInstance",
    # Feature Registry
    "FeatureRegistry",
    "Feature",
]

__version__ = "10.0.0"
__author__ = "RAG Enterprise Team"
__description__ = "Dynamic orchestration system for RAG Enterprise v10.0.0"
