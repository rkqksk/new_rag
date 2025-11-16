#!/usr/bin/env python3
"""
Installation Validation Script
RAG Enterprise v10.0.0

Quick validation that orchestration system is properly installed.
"""

import sys
import os
import importlib

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def check_import(module_path, description):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_path)
        print(f"✓ {description}")
        return True
    except ImportError as e:
        print(f"✗ {description}: {e}")
        return False


def validate_installation():
    """Validate orchestration system installation"""
    print("=" * 60)
    print("RAG Enterprise v10.0.0 - Orchestration System Validation")
    print("=" * 60)
    print()

    all_passed = True

    # Check core modules
    print("Checking core modules...")
    all_passed &= check_import("backend.orchestration", "Core package")
    all_passed &= check_import("backend.orchestration.config", "Configuration module")
    all_passed &= check_import("backend.orchestration.service_router", "Service router")
    all_passed &= check_import("backend.orchestration.resource_manager", "Resource manager")
    all_passed &= check_import("backend.orchestration.task_dispatcher", "Task dispatcher")
    all_passed &= check_import("backend.orchestration.feature_registry", "Feature registry")
    print()

    # Check classes
    print("Checking exported classes...")
    try:
        from apps.api.orchestration import (
            ServiceRouter,
            ResourceManager,
            TaskDispatcher,
            FeatureRegistry,
            OrchestrationConfig,
        )

        print("✓ All main classes exported")
    except ImportError as e:
        print(f"✗ Class export failed: {e}")
        all_passed = False
    print()

    # Check enums
    print("Checking enums...")
    try:
        from apps.api.orchestration import (
            ServicePriority,
            ServiceStatus,
            AgentType,
            TaskComplexity,
            FeatureCategory,
            FeatureStatus,
        )

        print("✓ All enums exported")
    except ImportError as e:
        print(f"✗ Enum export failed: {e}")
        all_passed = False
    print()

    # Check dependencies
    print("Checking dependencies...")
    dependencies = [
        ("psutil", "System resource monitoring"),
        ("asyncio", "Async/await support"),
        ("logging", "Logging"),
        ("typing", "Type hints"),
    ]

    for module_name, description in dependencies:
        all_passed &= check_import(module_name, description)
    print()

    # Quick instantiation test
    print("Testing instantiation...")
    try:
        from apps.api.orchestration import (
            ResourceManager,
            ServiceRouter,
            TaskDispatcher,
            FeatureRegistry,
        )

        # Create instances
        resource_manager = ResourceManager()
        service_router = ServiceRouter(resource_manager=resource_manager, auto_deactivation=False)
        task_dispatcher = TaskDispatcher()
        feature_registry = FeatureRegistry()

        print("✓ ResourceManager instantiated")
        print("✓ ServiceRouter instantiated")
        print("✓ TaskDispatcher instantiated")
        print("✓ FeatureRegistry instantiated")

        # Check registry
        services = service_router.list_available_services()
        features = feature_registry.get_usage_statistics()

        print(f"✓ Service registry: {len(services)} services configured")
        print(f"✓ Feature registry: {features['total_features']} features catalogued")

    except Exception as e:
        print(f"✗ Instantiation failed: {e}")
        all_passed = False
    print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - Installation is valid!")
        print()
        print("Next steps:")
        print("  1. Run tests: pytest backend/orchestration/tests/ -v")
        print("  2. Run examples: python backend/orchestration/examples/basic_usage.py")
        print("  3. Read docs: backend/orchestration/README.md")
    else:
        print("✗ SOME CHECKS FAILED - Please review errors above")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    validate_installation()
