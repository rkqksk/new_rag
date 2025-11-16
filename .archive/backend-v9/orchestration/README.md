# Orchestration System
## RAG Enterprise v10.0.0

Complete orchestration layer for dynamic service management, resource optimization, task dispatch, and feature tracking.

---

## Overview

The orchestration system provides:

1. **Service Router** - Dynamic service activation/deactivation with idle timeout
2. **Resource Manager** - CPU/memory/GPU allocation with priority-based scheduling
3. **Task Dispatcher** - Sub-agent orchestration (Explore, General, Plan)
4. **Feature Registry** - Feature catalog with usage tracking and recommendations

---

## Architecture

```
backend/orchestration/
├── __init__.py              # Package exports
├── config.py                # Configuration (services, agents, limits)
├── service_router.py        # Service lifecycle management
├── resource_manager.py      # Resource allocation
├── task_dispatcher.py       # Task orchestration
├── feature_registry.py      # Feature tracking
├── tests/                   # Unit tests
│   ├── test_resource_manager.py
│   ├── test_service_router.py
│   ├── test_task_dispatcher.py
│   └── test_feature_registry.py
└── README.md               # This file
```

---

## Quick Start

### Basic Usage

```python
from backend.orchestration import (
    ServiceRouter,
    ResourceManager,
    TaskDispatcher,
    FeatureRegistry,
)

# Initialize components
resource_manager = ResourceManager()
service_router = ServiceRouter(resource_manager=resource_manager)
task_dispatcher = TaskDispatcher()
feature_registry = FeatureRegistry()

# Start orchestration
await service_router.initialize()

# Route a request (activates service on-demand)
success, result = await service_router.route_request(
    service_name="rag",
    method="search",
    query="50ml PET bottle"
)

# Dispatch a task to agents
success, result = await task_dispatcher.dispatch_task(
    description="Explore RAG codebase structure",
    handler=my_handler_function,
    complexity=TaskComplexity.MEDIUM,
)

# Activate a feature
success, message = feature_registry.activate("ocr_processing")

# Shutdown gracefully
await service_router.shutdown()
```

---

## Components

### 1. Service Router

Manages service lifecycle with dynamic activation/deactivation.

#### Features
- On-demand service activation
- Automatic deactivation after idle timeout (default: 5 minutes)
- Priority-based activation
- Dependency resolution
- Graceful shutdown

#### Example

```python
from backend.orchestration import ServiceRouter

router = ServiceRouter(auto_deactivation=True)
await router.initialize()

# Route request (activates service if needed)
success, result = await router.route_request(
    service_name="rag",
    method="search",
    query="50ml PET bottle"
)

# Manually activate/deactivate
await router.activate_service("manufacturing")
await router.deactivate_service("manufacturing")

# Get service status
status = router.get_service_status("rag")
print(f"Status: {status['status']}")
print(f"Requests: {status['request_count']}")

# List all services
all_services = router.list_available_services()
```

### 2. Resource Manager

Manages CPU, memory, GPU resources with priority-based allocation.

#### Features
- Real-time resource monitoring (psutil)
- Resource limits enforcement
- Priority-based allocation (high, medium, low)
- Automatic throttling of low-priority services
- Background monitoring

#### Example

```python
from backend.orchestration import ResourceManager, ResourceLimits

# Custom limits
limits = ResourceLimits(
    cpu_percent_max=80.0,
    memory_gb_max=8.0,
    gpu_percent_max=100.0,
)

manager = ResourceManager(limits=limits)

# Start monitoring
await manager.start_monitoring(interval_seconds=30)

# Get current usage
resources = await manager.get_current_usage()
print(f"CPU: {resources.cpu_percent}%")
print(f"Memory: {resources.memory_gb_used}GB")

# Get summary
summary = await manager.get_resource_summary()
print(f"Active services: {summary['allocated']['service_count']}")
print(f"Available CPU: {summary['available']['cpu_cores']}")

# Stop monitoring
await manager.stop_monitoring()
```

### 3. Task Dispatcher

Orchestrates sub-agents for complex tasks.

#### Features
- Agent pools (Explore: 3, General: 5, Plan: 2)
- Complexity-based agent selection
- Parallel task execution
- Task queueing when at capacity
- Automatic timeout handling

#### Example

```python
from backend.orchestration import TaskDispatcher, TaskComplexity, AgentType

dispatcher = TaskDispatcher()

# Simple task dispatch
async def my_task_handler(arg1, arg2):
    # Task logic
    return f"Processed {arg1} and {arg2}"

success, result = await dispatcher.dispatch_task(
    description="Process data",
    handler=my_task_handler,
    complexity=TaskComplexity.SIMPLE,
    agent_type=AgentType.GENERAL,
    "value1", "value2"
)

# Parallel execution
tasks = [
    {"description": "Task 1", "handler": handler1},
    {"description": "Task 2", "handler": handler2},
    {"description": "Task 3", "handler": handler3},
]

results = await dispatcher.execute_parallel(tasks)

# Get agent pool status
status = dispatcher.get_agent_pool_status()
print(f"Explore agents: {status['explore']['current_agents']}")
print(f"General agents: {status['general']['busy']}/{status['general']['max_concurrent']}")
```

### 4. Feature Registry

Tracks features with usage statistics and recommendations.

#### Features
- 40+ platform features catalogued
- Usage tracking (activation count)
- Dependency management
- Usage-based deactivation suggestions
- Category-based organization

#### Example

```python
from backend.orchestration import FeatureRegistry, FeatureCategory

registry = FeatureRegistry()

# Activate feature
success, message = registry.activate("ocr_processing")
if not success:
    print(f"Activation failed: {message}")

# Deactivate feature
success, message = registry.deactivate("ocr_processing")

# Get active features
active = registry.get_active_features()
print(f"Active features: {active}")

# Get features by category
rag_features = registry.get_features_by_category(FeatureCategory.RAG)

# Get usage statistics
stats = registry.get_usage_statistics()
print(f"Total features: {stats['total_features']}")
print(f"Active: {stats['active_features']}")

# Get deactivation suggestions
suggestions = registry.suggest_deactivations(min_activations=10)
print(f"Consider deactivating: {suggestions}")
```

---

## Configuration

### Service Configuration

Defined in `config.py`:

```python
from backend.orchestration import ServiceConfig, ServicePriority

service = ServiceConfig(
    name="my_service",
    module_path="backend.services.my_service",
    priority=ServicePriority.MEDIUM,
    idle_timeout_seconds=300,  # 5 minutes
    cpu_allocation=2.0,         # 2 CPU cores
    memory_allocation_gb=2.0,   # 2GB RAM
    gpu_allocation=0.5,         # 50% GPU
    dependencies=["redis", "postgres"],
    auto_activate=False,        # Don't auto-activate on startup
)
```

### Resource Limits

```python
from backend.orchestration import ResourceLimits

limits = ResourceLimits(
    cpu_percent_max=80.0,   # Max 80% CPU usage
    memory_gb_max=8.0,      # Max 8GB memory
    gpu_percent_max=100.0,  # Max 100% GPU
    disk_gb_max=50.0,       # Max 50GB disk
)
```

### Agent Configuration

```python
from backend.orchestration import AgentConfig, AgentType, TaskComplexity

agent = AgentConfig(
    agent_type=AgentType.EXPLORE,
    max_concurrent=3,           # Max 3 concurrent agents
    timeout_seconds=300,        # 5 minute timeout
    complexity_threshold=TaskComplexity.MEDIUM,
)
```

---

## Service Registry

### Backend Services

| Service | Priority | Auto-Activate | Resources |
|---------|----------|---------------|-----------|
| rag | HIGH | Yes | 2 CPU, 2GB RAM |
| realtime | HIGH | Yes | 1 CPU, 0.5GB RAM |
| manufacturing | MEDIUM | No | 2 CPU, 2GB RAM, 0.5 GPU |
| ocr | MEDIUM | No | 1.5 CPU, 1.5GB RAM |
| data_collection | LOW | No | 1 CPU, 1GB RAM |
| analytics | LOW | No | 1 CPU, 1GB RAM |

### Features Catalog

**40+ features across 10 categories:**

- **RAG** (4): search, ocr, query_optimization, ingestion
- **Manufacturing** (3): vision_inspection, lora_finetuning, robot_control
- **Data Collection** (3): web_crawling, api_polling, file_parsing
- **Analytics** (3): clickhouse, kafka, graphql
- **Realtime** (3): socketio, postgres_notify, redis_pubsub
- **SaaS** (3): multi_tenancy, stripe_billing, usage_tracking
- **Security** (3): keycloak, vault, jwt_auth
- **Observability** (3): jaeger, prometheus, grafana
- **Frontend** (4): chat, realtime_demo, analytics_dashboard, rag_dashboard
- **API** (3): rest, streaming, websocket

---

## Testing

### Run Tests

```bash
# All orchestration tests
pytest backend/orchestration/tests/ -v

# Specific component
pytest backend/orchestration/tests/test_resource_manager.py -v

# With coverage
pytest backend/orchestration/tests/ --cov=backend.orchestration --cov-report=html
```

### Test Coverage

- `test_resource_manager.py` - 12 tests
- `test_service_router.py` - 10 tests
- `test_task_dispatcher.py` - 15 tests
- `test_feature_registry.py` - 18 tests

**Total: 55 unit tests**

---

## Integration with FastAPI

### Example Integration

```python
# main.py
from fastapi import FastAPI
from backend.orchestration import (
    ServiceRouter,
    ResourceManager,
    TaskDispatcher,
    FeatureRegistry,
)

app = FastAPI()

# Global instances
resource_manager = ResourceManager()
service_router = ServiceRouter(resource_manager=resource_manager)
task_dispatcher = TaskDispatcher()
feature_registry = FeatureRegistry()


@app.on_event("startup")
async def startup():
    """Initialize orchestration on startup"""
    await service_router.initialize()
    await resource_manager.start_monitoring()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await service_router.shutdown()
    await resource_manager.stop_monitoring()


@app.get("/orchestration/status")
async def get_orchestration_status():
    """Get orchestration system status"""
    return {
        "services": service_router.get_all_services_status(),
        "resources": await resource_manager.get_resource_summary(),
        "agents": task_dispatcher.get_agent_pool_status(),
        "features": feature_registry.get_usage_statistics(),
    }


@app.post("/orchestration/features/{feature_name}/activate")
async def activate_feature(feature_name: str):
    """Activate a feature"""
    success, message = feature_registry.activate(feature_name)
    return {"success": success, "message": message}
```

---

## Performance

### Resource Optimization

- **Idle Services**: Auto-deactivate after 5 minutes (saves ~2GB RAM per service)
- **Priority Scheduling**: High-priority services get resources first
- **Throttling**: Low-priority services throttled when resources tight
- **Monitoring**: 30-second intervals (low overhead)

### Task Execution

- **Agent Pools**: Up to 10 concurrent agents (3 Explore + 5 General + 2 Plan)
- **Parallel Execution**: Batch processing with `execute_parallel()`
- **Queueing**: Tasks queued when pools full (no rejection)
- **Timeout**: Automatic timeout (5-10 minutes based on complexity)

### Feature Tracking

- **Catalog Size**: 40+ features
- **Lookup**: O(1) dictionary lookup
- **Statistics**: Aggregated in-memory
- **Recommendations**: Based on activation count

---

## Best Practices

### 1. Service Lifecycle

```python
# DO: Let router manage lifecycle
success, result = await router.route_request("rag", "search", query="test")

# DON'T: Manually import and call services
from backend.services.rag import search
result = search("test")
```

### 2. Resource Allocation

```python
# DO: Use priority levels appropriately
high_priority_service = ServiceConfig(
    name="critical_service",
    priority=ServicePriority.HIGH,  # Gets resources first
    # ...
)

# DON'T: Set everything to HIGH
```

### 3. Task Dispatch

```python
# DO: Use parallel execution for independent tasks
tasks = [{"handler": h1}, {"handler": h2}, {"handler": h3}]
results = await dispatcher.execute_parallel(tasks)

# DON'T: Execute sequentially when parallel is possible
result1 = await dispatcher.dispatch_task(handler=h1)
result2 = await dispatcher.dispatch_task(handler=h2)
result3 = await dispatcher.dispatch_task(handler=h3)
```

### 4. Feature Management

```python
# DO: Activate dependencies first
registry.activate("rag_search")  # Dependency
registry.activate("ocr_processing")  # Dependent

# DON'T: Activate without checking dependencies
registry.activate("ocr_processing")  # Will fail if rag_search inactive
```

---

## Troubleshooting

### Service Won't Activate

**Problem**: Service activation fails

**Solutions**:
1. Check dependencies: `service.config.dependencies`
2. Check resource availability: `await manager.get_resource_summary()`
3. Check module path: Verify `module_path` is correct
4. Check logs: Look for import errors

### High Memory Usage

**Problem**: System using too much memory

**Solutions**:
1. Lower limits: `ResourceLimits(memory_gb_max=6.0)`
2. Enable auto-deactivation: `ServiceRouter(auto_deactivation=True)`
3. Deactivate unused services: `router.deactivate_service("service_name")`
4. Check allocations: `manager.get_all_allocations()`

### Tasks Timing Out

**Problem**: Tasks not completing

**Solutions**:
1. Increase timeout: Modify `AgentConfig.timeout_seconds`
2. Check agent pool: `dispatcher.get_agent_pool_status()`
3. Clear queue: `await dispatcher.clear_queue(AgentType.GENERAL)`
4. Reduce complexity: Use simpler tasks

### Features Not Activating

**Problem**: Feature activation fails

**Solutions**:
1. Activate dependencies first
2. Check feature exists: `feature_registry.get_feature_info(name)`
3. Use force deactivate if stuck: `registry.deactivate(name, force=True)`
4. Check logs for errors

---

## API Reference

### ServiceRouter

```python
async def initialize() -> None
async def shutdown() -> None
async def activate_service(service_name: str) -> tuple[bool, str]
async def deactivate_service(service_name: str, force: bool = False) -> tuple[bool, str]
async def route_request(service_name: str, method: str, *args, **kwargs) -> tuple[bool, Any]
def get_service_status(service_name: str) -> Optional[Dict]
def get_all_services_status() -> Dict[str, Dict]
def list_available_services() -> Dict[str, ServiceConfig]
```

### ResourceManager

```python
async def start_monitoring(interval_seconds: int = 30) -> None
async def stop_monitoring() -> None
async def get_current_usage() -> SystemResources
async def allocate_resources(service_name: str, config: ServiceConfig) -> tuple[bool, str]
async def free_resources(service_name: str) -> tuple[bool, str]
async def get_resource_summary() -> Dict[str, Any]
def get_allocation(service_name: str) -> Optional[ResourceAllocation]
def get_all_allocations() -> Dict[str, ResourceAllocation]
```

### TaskDispatcher

```python
async def dispatch_task(description: str, handler: Callable, complexity: Optional[TaskComplexity] = None, agent_type: Optional[AgentType] = None, *args, **kwargs) -> tuple[bool, Any]
async def execute_parallel(tasks: List[Dict], agent_type: Optional[AgentType] = None) -> List[tuple[bool, Any]]
def get_agent_pool_status() -> Dict[str, Any]
def get_task_queue_status() -> Dict[str, int]
async def clear_queue(agent_type: Optional[AgentType] = None) -> None
```

### FeatureRegistry

```python
def activate(feature_name: str) -> tuple[bool, str]
def deactivate(feature_name: str, force: bool = False) -> tuple[bool, str]
def get_active_features() -> List[str]
def get_inactive_features() -> List[str]
def get_features_by_category(category: FeatureCategory) -> List[str]
def suggest_deactivations(min_activations: int = 10) -> List[str]
def get_feature_info(feature_name: str) -> Optional[Dict]
def get_all_features_info() -> Dict[str, Dict]
def get_usage_statistics() -> Dict[str, Any]
```

---

## License

MIT License - RAG Enterprise v10.0.0

---

## Version History

- **v10.0.0** (2025-11-15) - Initial orchestration system
  - Service router with dynamic activation
  - Resource manager with monitoring
  - Task dispatcher with agent pools
  - Feature registry with 40+ features
  - Comprehensive test suite (55 tests)

---

**Documentation**: See individual module docstrings for detailed API docs
**Tests**: Run `pytest backend/orchestration/tests/` for full test suite
**Issues**: Check logs at `DEBUG` level for troubleshooting
