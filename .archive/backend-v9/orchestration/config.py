"""
Orchestration Configuration
RAG Enterprise v10.0.0

Configuration for the orchestration system including resource limits,
timeouts, and service definitions.
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass, field


class ServicePriority(str, Enum):
    """Service execution priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ServiceStatus(str, Enum):
    """Service lifecycle status"""
    INACTIVE = "inactive"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    ERROR = "error"


class AgentType(str, Enum):
    """Sub-agent types for task dispatch"""
    EXPLORE = "explore"  # Code exploration and discovery
    GENERAL = "general"  # General-purpose tasks
    PLAN = "plan"  # Planning and architecture


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ResourceLimits:
    """System resource limits configuration"""
    cpu_percent_max: float = 80.0  # Maximum CPU usage (%)
    memory_gb_max: float = 8.0  # Maximum memory usage (GB)
    gpu_percent_max: float = 100.0  # Maximum GPU usage (%)
    disk_gb_max: float = 50.0  # Maximum disk usage (GB)


@dataclass
class ServiceConfig:
    """Configuration for a single service"""
    name: str
    module_path: str
    priority: ServicePriority
    idle_timeout_seconds: int = 300  # 5 minutes default
    cpu_allocation: float = 1.0  # CPU cores
    memory_allocation_gb: float = 1.0  # Memory in GB
    gpu_allocation: float = 0.0  # GPU allocation (0-1)
    dependencies: list = field(default_factory=list)
    auto_activate: bool = False  # Auto-activate on startup


@dataclass
class AgentConfig:
    """Configuration for sub-agent pools"""
    agent_type: AgentType
    max_concurrent: int
    timeout_seconds: int = 300
    complexity_threshold: TaskComplexity = TaskComplexity.SIMPLE


@dataclass
class OrchestrationConfig:
    """Main orchestration system configuration"""
    # Resource limits
    resources: ResourceLimits = field(default_factory=ResourceLimits)

    # Service definitions
    services: Dict[str, ServiceConfig] = field(default_factory=dict)

    # Agent pool configurations
    agents: Dict[AgentType, AgentConfig] = field(default_factory=dict)

    # Global settings
    health_check_interval_seconds: int = 60
    metrics_collection_interval_seconds: int = 30
    auto_deactivation_enabled: bool = True
    min_idle_time_for_suggestions: int = 10  # Minimum activations before suggesting deactivation

    # Logging
    log_level: str = "INFO"
    structured_logging: bool = True


# Default service configurations
DEFAULT_SERVICES = {
    "rag": ServiceConfig(
        name="rag",
        module_path="src.services.rag_service",
        priority=ServicePriority.HIGH,
        idle_timeout_seconds=300,
        cpu_allocation=2.0,
        memory_allocation_gb=2.0,
        dependencies=["qdrant", "redis"],
        auto_activate=True,
    ),
    "manufacturing": ServiceConfig(
        name="manufacturing",
        module_path="src.services.manufacturing_service",
        priority=ServicePriority.MEDIUM,
        idle_timeout_seconds=600,
        cpu_allocation=2.0,
        memory_allocation_gb=2.0,
        gpu_allocation=0.5,
        dependencies=["redis"],
        auto_activate=False,
    ),
    "ocr": ServiceConfig(
        name="ocr",
        module_path="backend.ocr.ocr_service",
        priority=ServicePriority.MEDIUM,
        idle_timeout_seconds=300,
        cpu_allocation=1.5,
        memory_allocation_gb=1.5,
        dependencies=[],
        auto_activate=False,
    ),
    "data_collection": ServiceConfig(
        name="data_collection",
        module_path="backend.services.crawling.crawler_service",
        priority=ServicePriority.LOW,
        idle_timeout_seconds=900,
        cpu_allocation=1.0,
        memory_allocation_gb=1.0,
        dependencies=["redis"],
        auto_activate=False,
    ),
    "analytics": ServiceConfig(
        name="analytics",
        module_path="backend.services.analytics_service",
        priority=ServicePriority.LOW,
        idle_timeout_seconds=600,
        cpu_allocation=1.0,
        memory_allocation_gb=1.0,
        dependencies=["clickhouse", "redis"],
        auto_activate=False,
    ),
    "realtime": ServiceConfig(
        name="realtime",
        module_path="backend.realtime.socketio_server",
        priority=ServicePriority.HIGH,
        idle_timeout_seconds=0,  # Never deactivate
        cpu_allocation=1.0,
        memory_allocation_gb=0.5,
        dependencies=["redis", "postgres"],
        auto_activate=True,
    ),
}


# Default agent pool configurations
DEFAULT_AGENTS = {
    AgentType.EXPLORE: AgentConfig(
        agent_type=AgentType.EXPLORE,
        max_concurrent=3,
        timeout_seconds=300,
        complexity_threshold=TaskComplexity.MEDIUM,
    ),
    AgentType.GENERAL: AgentConfig(
        agent_type=AgentType.GENERAL,
        max_concurrent=5,
        timeout_seconds=180,
        complexity_threshold=TaskComplexity.SIMPLE,
    ),
    AgentType.PLAN: AgentConfig(
        agent_type=AgentType.PLAN,
        max_concurrent=2,
        timeout_seconds=600,
        complexity_threshold=TaskComplexity.HIGH,
    ),
}


def get_default_config() -> OrchestrationConfig:
    """
    Get default orchestration configuration.

    Returns:
        OrchestrationConfig: Default configuration instance
    """
    return OrchestrationConfig(
        resources=ResourceLimits(),
        services=DEFAULT_SERVICES,
        agents=DEFAULT_AGENTS,
    )


def get_service_config(service_name: str) -> ServiceConfig:
    """
    Get configuration for a specific service.

    Args:
        service_name: Name of the service

    Returns:
        ServiceConfig: Service configuration

    Raises:
        KeyError: If service not found
    """
    if service_name not in DEFAULT_SERVICES:
        raise KeyError(f"Service '{service_name}' not found in configuration")
    return DEFAULT_SERVICES[service_name]


def get_agent_config(agent_type: AgentType) -> AgentConfig:
    """
    Get configuration for a specific agent type.

    Args:
        agent_type: Type of agent

    Returns:
        AgentConfig: Agent configuration

    Raises:
        KeyError: If agent type not found
    """
    if agent_type not in DEFAULT_AGENTS:
        raise KeyError(f"Agent type '{agent_type}' not found in configuration")
    return DEFAULT_AGENTS[agent_type]
