"""
Basic Usage Examples
RAG Enterprise v10.0.0

Demonstrates basic usage of the orchestration system.
"""

import asyncio
import logging
from apps.api.orchestration import (
    ServiceRouter,
    ResourceManager,
    TaskDispatcher,
    FeatureRegistry,
    TaskComplexity,
    AgentType,
    FeatureCategory,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_service_routing():
    """Example: Service routing with dynamic activation"""
    logger.info("=" * 60)
    logger.info("Example 1: Service Routing")
    logger.info("=" * 60)

    # Initialize router
    router = ServiceRouter(auto_deactivation=True)
    await router.initialize()

    # List available services
    services = router.list_available_services()
    logger.info(f"Available services: {list(services.keys())}")

    # Route a request (activates service on-demand)
    logger.info("\nRouting request to 'rag' service...")
    success, result = await router.route_request(
        service_name="rag",
        method="search",
        query="50ml PET bottle"
    )

    if not success:
        logger.error(f"Request failed: {result}")
    else:
        logger.info("Request successful (note: service module may not exist in demo)")

    # Check service status
    status = router.get_service_status("rag")
    if status:
        logger.info(f"\nService status: {status['status']}")
        logger.info(f"Request count: {status['request_count']}")

    # Cleanup
    await router.shutdown()


async def example_resource_management():
    """Example: Resource management and monitoring"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 2: Resource Management")
    logger.info("=" * 60)

    # Initialize resource manager
    manager = ResourceManager()

    # Get current usage
    resources = await manager.get_current_usage()
    logger.info(f"\nCurrent System Resources:")
    logger.info(f"  CPU: {resources.cpu_percent:.1f}%")
    logger.info(f"  Memory: {resources.memory_gb_used:.2f}GB / {resources.memory_gb_total:.2f}GB ({resources.memory_percent:.1f}%)")
    logger.info(f"  Disk: {resources.disk_gb_used:.2f}GB / {resources.disk_gb_total:.2f}GB ({resources.disk_percent:.1f}%)")

    # Get resource summary
    summary = await manager.get_resource_summary()
    logger.info(f"\nResource Limits:")
    logger.info(f"  CPU: {summary['limits']['cpu_percent_max']}%")
    logger.info(f"  Memory: {summary['limits']['memory_gb_max']}GB")
    logger.info(f"  GPU: {summary['limits']['gpu_percent_max']}%")

    logger.info(f"\nAllocated Resources:")
    logger.info(f"  Active services: {summary['allocated']['service_count']}")
    logger.info(f"  CPU cores: {summary['allocated']['cpu_cores']}")
    logger.info(f"  Memory: {summary['allocated']['memory_gb']}GB")


async def example_task_dispatch():
    """Example: Task dispatch with agents"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 3: Task Dispatch")
    logger.info("=" * 60)

    # Initialize dispatcher
    dispatcher = TaskDispatcher()

    # Define a simple task handler
    async def simple_task(value: int):
        await asyncio.sleep(0.1)  # Simulate work
        return value * 2

    # Dispatch single task
    logger.info("\nDispatching single task...")
    success, result = await dispatcher.dispatch_task(
        description="Double a number",
        handler=simple_task,
        complexity=TaskComplexity.SIMPLE,
        agent_type=AgentType.GENERAL,
        5  # argument
    )

    if success:
        logger.info(f"Task completed: {result}")

    # Parallel execution
    logger.info("\nExecuting tasks in parallel...")
    tasks = [
        {"description": f"Task {i}", "handler": simple_task, "args": (i,)}
        for i in range(5)
    ]

    results = await dispatcher.execute_parallel(tasks)
    logger.info(f"Parallel results: {[r for _, r in results]}")

    # Check agent pool status
    status = dispatcher.get_agent_pool_status()
    logger.info(f"\nAgent Pool Status:")
    for agent_type, info in status.items():
        logger.info(f"  {agent_type}: {info['busy']}/{info['max_concurrent']} busy, {info['total_tasks']} total tasks")


async def example_feature_registry():
    """Example: Feature registry and tracking"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 4: Feature Registry")
    logger.info("=" * 60)

    # Initialize registry
    registry = FeatureRegistry()

    # Get usage statistics
    stats = registry.get_usage_statistics()
    logger.info(f"\nFeature Statistics:")
    logger.info(f"  Total features: {stats['total_features']}")
    logger.info(f"  Active: {stats['active_features']}")
    logger.info(f"  Inactive: {stats['inactive_features']}")

    # Show features by category
    logger.info(f"\nFeatures by category:")
    for category, counts in stats['by_category'].items():
        logger.info(f"  {category}: {counts['active']}/{counts['total']} active")

    # Activate a feature
    logger.info("\nActivating 'web_crawling' feature...")
    success, message = registry.activate("web_crawling")
    logger.info(f"  Result: {message}")

    # Get active features
    active = registry.get_active_features()
    logger.info(f"\nActive features ({len(active)}): {', '.join(active[:5])}...")

    # Get RAG features
    rag_features = registry.get_features_by_category(FeatureCategory.RAG)
    logger.info(f"\nRAG features: {', '.join(rag_features)}")

    # Get deactivation suggestions
    suggestions = registry.suggest_deactivations(min_activations=5)
    logger.info(f"\nSuggested for deactivation ({len(suggestions)}): {', '.join(suggestions[:3])}...")


async def example_integrated_workflow():
    """Example: Integrated workflow using all components"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 5: Integrated Workflow")
    logger.info("=" * 60)

    # Initialize all components
    resource_manager = ResourceManager()
    router = ServiceRouter(resource_manager=resource_manager)
    dispatcher = TaskDispatcher()
    registry = FeatureRegistry()

    # Start system
    logger.info("\nInitializing orchestration system...")
    await router.initialize()
    await resource_manager.start_monitoring(interval_seconds=60)

    # Activate feature
    logger.info("\nActivating RAG features...")
    registry.activate("rag_search")
    registry.activate("query_optimization")

    # Define task handler
    async def analyze_query(query: str):
        await asyncio.sleep(0.1)
        return f"Analyzed: {query}"

    # Dispatch task
    logger.info("\nDispatching query analysis task...")
    success, result = await dispatcher.dispatch_task(
        description="Analyze user query",
        handler=analyze_query,
        complexity=TaskComplexity.SIMPLE,
        "50ml PET bottle"
    )

    if success:
        logger.info(f"Analysis result: {result}")

    # Get system status
    logger.info("\nSystem Status:")
    logger.info(f"  Active services: {len(router.get_all_services_status())}")
    logger.info(f"  Active features: {len(registry.get_active_features())}")

    resource_summary = await resource_manager.get_resource_summary()
    logger.info(f"  CPU allocated: {resource_summary['allocated']['cpu_cores']} cores")
    logger.info(f"  Memory allocated: {resource_summary['allocated']['memory_gb']}GB")

    agent_status = dispatcher.get_agent_pool_status()
    total_agents = sum(info['current_agents'] for info in agent_status.values())
    logger.info(f"  Active agents: {total_agents}")

    # Cleanup
    logger.info("\nShutting down system...")
    await resource_manager.stop_monitoring()
    await router.shutdown()


async def main():
    """Run all examples"""
    logger.info("\n")
    logger.info("*" * 60)
    logger.info("RAG Enterprise v10.0.0 - Orchestration System Examples")
    logger.info("*" * 60)

    try:
        # Run examples
        await example_service_routing()
        await example_resource_management()
        await example_task_dispatch()
        await example_feature_registry()
        await example_integrated_workflow()

        logger.info("\n" + "=" * 60)
        logger.info("All examples completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
