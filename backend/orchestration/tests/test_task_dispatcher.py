"""
Task Dispatcher Tests
RAG Enterprise v10.0.0

Unit tests for TaskDispatcher class.
"""

import pytest
import asyncio
from backend.orchestration import (
    TaskDispatcher,
    AgentType,
    TaskComplexity,
)


@pytest.mark.asyncio
class TestTaskDispatcher:
    """Test TaskDispatcher functionality"""

    async def test_initialization(self):
        """Test task dispatcher initialization"""
        dispatcher = TaskDispatcher()

        assert len(dispatcher.agent_pools) == len(AgentType)
        assert len(dispatcher.task_queue) == len(AgentType)
        assert dispatcher._task_counter == 0

    async def test_analyze_complexity_simple(self):
        """Test complexity analysis for simple tasks"""
        dispatcher = TaskDispatcher()

        complexity = dispatcher._analyze_complexity("Get the user list")
        assert complexity == TaskComplexity.SIMPLE

        complexity = dispatcher._analyze_complexity("Fetch all products")
        assert complexity == TaskComplexity.SIMPLE

    async def test_analyze_complexity_medium(self):
        """Test complexity analysis for medium tasks"""
        dispatcher = TaskDispatcher()

        complexity = dispatcher._analyze_complexity("Process the data and generate report")
        assert complexity == TaskComplexity.MEDIUM

    async def test_analyze_complexity_high(self):
        """Test complexity analysis for high tasks"""
        dispatcher = TaskDispatcher()

        complexity = dispatcher._analyze_complexity("Design a new architecture")
        assert complexity == TaskComplexity.HIGH

        complexity = dispatcher._analyze_complexity("Plan multi-step migration")
        assert complexity == TaskComplexity.HIGH

    async def test_select_agent_type_explore(self):
        """Test agent selection for explore tasks"""
        dispatcher = TaskDispatcher()

        agent_type = dispatcher._select_agent_type(
            TaskComplexity.MEDIUM,
            "Explore the codebase structure"
        )
        assert agent_type == AgentType.EXPLORE

    async def test_select_agent_type_plan(self):
        """Test agent selection for plan tasks"""
        dispatcher = TaskDispatcher()

        agent_type = dispatcher._select_agent_type(
            TaskComplexity.HIGH,
            "Plan the migration strategy"
        )
        assert agent_type == AgentType.PLAN

    async def test_select_agent_type_general(self):
        """Test agent selection for general tasks"""
        dispatcher = TaskDispatcher()

        agent_type = dispatcher._select_agent_type(
            TaskComplexity.SIMPLE,
            "Process the request"
        )
        assert agent_type == AgentType.GENERAL

    async def test_dispatch_task_simple(self):
        """Test dispatching simple task"""
        dispatcher = TaskDispatcher()

        async def simple_handler():
            return "Task completed"

        success, result = await dispatcher.dispatch_task(
            description="Simple test task",
            handler=simple_handler,
            complexity=TaskComplexity.SIMPLE,
            agent_type=AgentType.GENERAL,
        )

        assert success is True
        assert result == "Task completed"

    async def test_dispatch_task_with_args(self):
        """Test dispatching task with arguments"""
        dispatcher = TaskDispatcher()

        async def handler_with_args(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        success, result = await dispatcher.dispatch_task(
            description="Task with args",
            handler=handler_with_args,
            "value1", "value2",
            kwarg1="value3"
        )

        assert success is True
        assert result == "value1-value2-value3"

    async def test_dispatch_task_error_handling(self):
        """Test error handling in task dispatch"""
        dispatcher = TaskDispatcher()

        async def failing_handler():
            raise ValueError("Test error")

        success, result = await dispatcher.dispatch_task(
            description="Failing task",
            handler=failing_handler,
        )

        assert success is False
        assert "Test error" in result

    async def test_execute_parallel_success(self):
        """Test parallel task execution"""
        dispatcher = TaskDispatcher()

        async def task_handler(value):
            await asyncio.sleep(0.1)
            return value * 2

        tasks = [
            {
                "description": f"Task {i}",
                "handler": task_handler,
                "args": (i,),
            }
            for i in range(5)
        ]

        results = await dispatcher.execute_parallel(tasks)

        assert len(results) == 5
        assert all(success for success, _ in results)
        assert [result for _, result in results] == [0, 2, 4, 6, 8]

    async def test_execute_parallel_mixed_results(self):
        """Test parallel execution with mixed success/failure"""
        dispatcher = TaskDispatcher()

        async def success_handler():
            return "success"

        async def failure_handler():
            raise ValueError("Error")

        tasks = [
            {"description": "Success", "handler": success_handler},
            {"description": "Failure", "handler": failure_handler},
            {"description": "Success", "handler": success_handler},
        ]

        results = await dispatcher.execute_parallel(tasks)

        assert len(results) == 3
        assert results[0][0] is True  # First task succeeded
        assert results[1][0] is False  # Second task failed
        assert results[2][0] is True  # Third task succeeded

    async def test_get_agent_pool_status(self):
        """Test getting agent pool status"""
        dispatcher = TaskDispatcher()

        status = dispatcher.get_agent_pool_status()

        assert len(status) == len(AgentType)
        assert "explore" in status
        assert "general" in status
        assert "plan" in status

        for agent_type, info in status.items():
            assert "max_concurrent" in info
            assert "current_agents" in info
            assert "idle" in info
            assert "busy" in info

    async def test_get_task_queue_status(self):
        """Test getting task queue status"""
        dispatcher = TaskDispatcher()

        status = dispatcher.get_task_queue_status()

        assert len(status) == len(AgentType)
        assert all(count == 0 for count in status.values())

    async def test_clear_queue_specific(self):
        """Test clearing specific agent queue"""
        dispatcher = TaskDispatcher()

        # Add some tasks to queue (by filling agent pool)
        async def long_running_task():
            await asyncio.sleep(10)
            return "done"

        # This should queue tasks once pool is full
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                dispatcher.dispatch_task(
                    description=f"Task {i}",
                    handler=long_running_task,
                    agent_type=AgentType.GENERAL,
                )
            )
            tasks.append(task)

        await asyncio.sleep(0.1)

        # Clear general queue
        await dispatcher.clear_queue(AgentType.GENERAL)

        status = dispatcher.get_task_queue_status()
        assert status["general"] == 0

        # Cancel all tasks
        for task in tasks:
            task.cancel()

    async def test_clear_all_queues(self):
        """Test clearing all queues"""
        dispatcher = TaskDispatcher()

        await dispatcher.clear_queue()

        status = dispatcher.get_task_queue_status()
        assert all(count == 0 for count in status.values())


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
