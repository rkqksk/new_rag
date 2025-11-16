"""
Task Dispatcher
RAG Enterprise v10.0.0

Orchestrates sub-agents (Explore, General, Plan) for complex tasks.
Manages agent pools and parallel execution.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .config import (
    AgentType,
    TaskComplexity,
    get_default_config,
)


logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Task definition for agent execution"""

    task_id: str
    description: str
    complexity: TaskComplexity
    agent_type: AgentType
    handler: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AgentInstance:
    """Running agent instance"""

    agent_id: str
    agent_type: AgentType
    status: str  # idle, busy, error
    current_task: Optional[Task] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    task_count: int = 0
    error_count: int = 0


class TaskDispatcher:
    """
    Orchestrates sub-agents for task execution.

    Features:
    - Agent pool management (Explore, General, Plan)
    - Complexity-based agent selection
    - Parallel task execution
    - Task queueing when at capacity
    - Automatic agent allocation
    """

    def __init__(self):
        """Initialize task dispatcher with agent pools."""
        self.config = get_default_config()
        self.agent_pools: Dict[AgentType, List[AgentInstance]] = {
            agent_type: [] for agent_type in AgentType
        }
        self.task_queue: Dict[AgentType, List[Task]] = {agent_type: [] for agent_type in AgentType}
        self._task_counter = 0
        self._lock = asyncio.Lock()

        logger.info(
            f"TaskDispatcher initialized with agent pools: "
            f"{', '.join(f'{t.value}={c.max_concurrent}' for t, c in self.config.agents.items())}"
        )

    async def dispatch_task(
        self,
        description: str,
        handler: Callable,
        complexity: Optional[TaskComplexity] = None,
        agent_type: Optional[AgentType] = None,
        *args,
        **kwargs,
    ) -> tuple[bool, Any]:
        """
        Dispatch a task to an appropriate agent.

        Args:
            description: Task description
            handler: Async function to execute
            complexity: Task complexity (auto-detected if None)
            agent_type: Specific agent type (auto-selected if None)
            *args: Handler arguments
            **kwargs: Handler keyword arguments

        Returns:
            Tuple of (success, result/error)
        """
        # Analyze task if complexity/agent not specified
        if complexity is None:
            complexity = self._analyze_complexity(description)

        if agent_type is None:
            agent_type = self._select_agent_type(complexity, description)

        # Create task
        async with self._lock:
            self._task_counter += 1
            task = Task(
                task_id=f"task_{self._task_counter}",
                description=description,
                complexity=complexity,
                agent_type=agent_type,
                handler=handler,
                args=args,
                kwargs=kwargs,
            )

        logger.info(
            f"Dispatching task {task.task_id}: {description[:50]}... "
            f"(complexity={complexity.value}, agent={agent_type.value})"
        )

        # Try to execute immediately
        agent = await self._get_available_agent(agent_type)

        if agent:
            # Execute immediately
            return await self._execute_task(agent, task)
        else:
            # Queue task
            logger.info(f"No agents available, queueing task {task.task_id}")
            async with self._lock:
                self.task_queue[agent_type].append(task)

            # Wait for task to complete (with timeout)
            agent_config = self.config.agents[agent_type]
            timeout = agent_config.timeout_seconds

            try:
                # Poll for completion
                for _ in range(timeout):
                    await asyncio.sleep(1)
                    if task.completed_at:
                        if task.error:
                            return False, task.error
                        return True, task.result

                return False, f"Task timed out after {timeout}s"

            except asyncio.CancelledError:
                return False, "Task cancelled"

    async def execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        agent_type: Optional[AgentType] = None,
    ) -> List[tuple[bool, Any]]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: List of task dictionaries with keys: description, handler, args, kwargs
            agent_type: Agent type to use (auto-selected if None)

        Returns:
            List of (success, result) tuples
        """
        logger.info(f"Executing {len(tasks)} tasks in parallel")

        # Create coroutines
        coroutines = []
        for task_def in tasks:
            coro = self.dispatch_task(
                description=task_def.get("description", "Parallel task"),
                handler=task_def["handler"],
                complexity=task_def.get("complexity"),
                agent_type=agent_type or task_def.get("agent_type"),
                *task_def.get("args", ()),
                **task_def.get("kwargs", {}),
            )
            coroutines.append(coro)

        # Execute in parallel
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append((False, str(result)))
            else:
                processed_results.append(result)

        successful = sum(1 for success, _ in processed_results if success)
        logger.info(f"Parallel execution complete: {successful}/{len(tasks)} successful")

        return processed_results

    async def _get_available_agent(self, agent_type: AgentType) -> Optional[AgentInstance]:
        """
        Get an available agent from the pool or create new if under limit.

        Args:
            agent_type: Type of agent needed

        Returns:
            AgentInstance or None if at capacity
        """
        async with self._lock:
            pool = self.agent_pools[agent_type]
            config = self.config.agents[agent_type]

            # Check for idle agents
            for agent in pool:
                if agent.status == "idle":
                    return agent

            # Create new agent if under limit
            if len(pool) < config.max_concurrent:
                agent_id = f"{agent_type.value}_{len(pool) + 1}"
                agent = AgentInstance(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    status="idle",
                )
                pool.append(agent)
                logger.info(f"Created new agent: {agent_id}")
                return agent

            return None

    async def _execute_task(self, agent: AgentInstance, task: Task) -> tuple[bool, Any]:
        """
        Execute a task with the given agent.

        Args:
            agent: Agent instance
            task: Task to execute

        Returns:
            Tuple of (success, result/error)
        """
        logger.info(f"Agent {agent.agent_id} executing task {task.task_id}")

        agent.status = "busy"
        agent.current_task = task
        task.started_at = datetime.utcnow()

        try:
            # Execute handler
            if asyncio.iscoroutinefunction(task.handler):
                result = await task.handler(*task.args, **task.kwargs)
            else:
                result = task.handler(*task.args, **task.kwargs)

            # Mark complete
            task.completed_at = datetime.utcnow()
            task.result = result

            agent.task_count += 1
            logger.info(f"Task {task.task_id} completed successfully by {agent.agent_id}")

            return True, result

        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
            task.completed_at = datetime.utcnow()
            task.error = str(e)
            agent.error_count += 1
            return False, str(e)

        finally:
            # Mark agent idle and process queue
            agent.status = "idle"
            agent.current_task = None
            await self._process_queue(task.agent_type)

    async def _process_queue(self, agent_type: AgentType):
        """
        Process queued tasks for an agent type.

        Args:
            agent_type: Agent type to process queue for
        """
        async with self._lock:
            queue = self.task_queue[agent_type]
            if not queue:
                return

            # Get next task
            task = queue.pop(0)

        # Get available agent
        agent = await self._get_available_agent(agent_type)
        if agent:
            # Execute task in background
            asyncio.create_task(self._execute_task(agent, task))

    def _analyze_complexity(self, description: str) -> TaskComplexity:
        """
        Analyze task complexity from description.

        Args:
            description: Task description

        Returns:
            TaskComplexity level
        """
        description_lower = description.lower()

        # Simple task indicators
        simple_keywords = [
            "get",
            "fetch",
            "read",
            "list",
            "show",
            "display",
            "view",
            "check",
            "status",
        ]

        # High complexity indicators
        high_keywords = [
            "design",
            "architect",
            "plan",
            "strategy",
            "optimize",
            "refactor",
            "migrate",
            "implement",
            "multi-step",
            "complex",
            "advanced",
        ]

        # Check for high complexity
        if any(keyword in description_lower for keyword in high_keywords):
            return TaskComplexity.HIGH

        # Check for simple complexity
        if any(keyword in description_lower for keyword in simple_keywords):
            return TaskComplexity.SIMPLE

        # Default to medium
        return TaskComplexity.MEDIUM

    def _select_agent_type(self, complexity: TaskComplexity, description: str) -> AgentType:
        """
        Select appropriate agent type based on complexity and description.

        Args:
            complexity: Task complexity
            description: Task description

        Returns:
            AgentType to use
        """
        description_lower = description.lower()

        # Explore agent keywords
        explore_keywords = [
            "explore",
            "discover",
            "find",
            "search",
            "investigate",
            "analyze",
            "understand",
            "codebase",
            "code",
            "structure",
        ]

        # Plan agent keywords
        plan_keywords = [
            "plan",
            "design",
            "architect",
            "strategy",
            "roadmap",
            "organize",
            "structure",
            "multi-step",
            "workflow",
        ]

        # Check for explore tasks
        if any(keyword in description_lower for keyword in explore_keywords):
            return AgentType.EXPLORE

        # Check for plan tasks
        if any(keyword in description_lower for keyword in plan_keywords):
            return AgentType.PLAN

        # High complexity → Plan agent
        if complexity == TaskComplexity.HIGH:
            return AgentType.PLAN

        # Default to General agent
        return AgentType.GENERAL

    def get_agent_pool_status(self) -> Dict[str, Any]:
        """
        Get status of all agent pools.

        Returns:
            Dictionary with agent pool statistics
        """
        status = {}

        for agent_type in AgentType:
            pool = self.agent_pools[agent_type]
            config = self.config.agents[agent_type]
            queue = self.task_queue[agent_type]

            idle_count = sum(1 for a in pool if a.status == "idle")
            busy_count = sum(1 for a in pool if a.status == "busy")
            error_count = sum(1 for a in pool if a.status == "error")

            status[agent_type.value] = {
                "max_concurrent": config.max_concurrent,
                "current_agents": len(pool),
                "idle": idle_count,
                "busy": busy_count,
                "error": error_count,
                "queued_tasks": len(queue),
                "total_tasks": sum(a.task_count for a in pool),
                "total_errors": sum(a.error_count for a in pool),
            }

        return status

    def get_task_queue_status(self) -> Dict[str, int]:
        """
        Get queued task counts by agent type.

        Returns:
            Dictionary mapping agent type to queue length
        """
        return {agent_type.value: len(queue) for agent_type, queue in self.task_queue.items()}

    async def clear_queue(self, agent_type: Optional[AgentType] = None):
        """
        Clear task queue for an agent type or all types.

        Args:
            agent_type: Agent type to clear (all if None)
        """
        async with self._lock:
            if agent_type:
                cleared = len(self.task_queue[agent_type])
                self.task_queue[agent_type].clear()
                logger.info(f"Cleared {cleared} tasks from {agent_type.value} queue")
            else:
                total_cleared = sum(len(q) for q in self.task_queue.values())
                for queue in self.task_queue.values():
                    queue.clear()
                logger.info(f"Cleared {total_cleared} tasks from all queues")
