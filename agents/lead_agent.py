"""
Lead Agent - Central Orchestrator for RAG Enterprise
Coordinates all agents, manages token budget, and tracks task execution
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent operational status"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class AgentCapability:
    """Represents an agent's capability"""
    name: str
    description: str
    agent_class: str
    status: AgentStatus = AgentStatus.IDLE
    last_used: Optional[datetime] = None
    success_rate: float = 1.0
    avg_execution_time: float = 0.0


@dataclass
class TaskExecution:
    """Tracks task execution state"""
    task_id: str
    agent_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    result: Optional[Any] = None
    error: Optional[str] = None
    tokens_used: int = 0


class LeadAgent:
    """
    Central orchestrator for the RAG Enterprise system.
    Manages agent lifecycle, task delegation, and resource allocation.
    """

    def __init__(
        self,
        token_budget: int = 200000,
        max_concurrent_tasks: int = 5
    ):
        self.token_budget = token_budget
        self.tokens_used = 0
        self.max_concurrent_tasks = max_concurrent_tasks

        # Agent registry
        self.capabilities: Dict[str, AgentCapability] = {}
        self.active_agents: Dict[str, Any] = {}

        # Task tracking
        self.task_queue: List[Dict[str, Any]] = []
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.completed_tasks: List[TaskExecution] = []

        # Initialize capabilities
        self._register_capabilities()

        logger.info(f"Lead Agent initialized with {token_budget:,} token budget")

    def _register_capabilities(self):
        """Register available agent capabilities"""
        capabilities = [
            AgentCapability(
                name="crawling",
                description="Web crawling and data extraction",
                agent_class="agents.crawler_agent.CrawlerAgent"
            ),
            AgentCapability(
                name="parsing",
                description="Document parsing (PDF, Excel, Word, etc.)",
                agent_class="agents.file_parser_agent.FileParserAgent"
            ),
            AgentCapability(
                name="chunking",
                description="Text chunking and segmentation",
                agent_class="agents.chunking_agent.ChunkingAgent"
            ),
            AgentCapability(
                name="embedding",
                description="Text embedding generation",
                agent_class="agents.embedding_agent.EmbeddingAgent"
            ),
            AgentCapability(
                name="vector_db",
                description="Vector database operations",
                agent_class="agents.vector_db_loader_agent.VectorDBAgent"
            ),
            AgentCapability(
                name="search",
                description="Semantic search and retrieval",
                agent_class="agents.search_agent.SearchAgent"
            ),
            AgentCapability(
                name="qa",
                description="Question answering",
                agent_class="agents.qa_agent.QAAgent"
            ),
            AgentCapability(
                name="monitoring",
                description="System monitoring and observability",
                agent_class="agents.monitoring_agent.MonitoringAgent"
            ),
        ]

        for cap in capabilities:
            self.capabilities[cap.name] = cap

    async def delegate_task(
        self,
        capability: str,
        task_params: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """
        Delegate a task to an agent with the specified capability.

        Args:
            capability: Name of the required capability
            task_params: Parameters for the task
            priority: Task priority (1-10, higher = more important)

        Returns:
            task_id: Unique identifier for tracking the task
        """
        if capability not in self.capabilities:
            raise ValueError(f"Unknown capability: {capability}")

        # Generate task ID
        task_id = f"{capability}_{datetime.now().timestamp()}"

        # Create task
        task = {
            "task_id": task_id,
            "capability": capability,
            "params": task_params,
            "priority": priority,
            "created_at": datetime.now()
        }

        # Add to queue
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda x: x["priority"], reverse=True)

        logger.info(f"Task {task_id} queued for capability: {capability}")

        return task_id

    async def execute_task(self, task_id: str) -> Any:
        """Execute a queued task"""
        # Find task in queue
        task = next((t for t in self.task_queue if t["task_id"] == task_id), None)

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        capability = task["capability"]
        cap_info = self.capabilities[capability]

        # Create task execution tracker
        execution = TaskExecution(
            task_id=task_id,
            agent_name=capability,
            started_at=datetime.now()
        )

        self.active_tasks[task_id] = execution

        try:
            # Update capability status
            cap_info.status = AgentStatus.ACTIVE
            cap_info.last_used = datetime.now()

            # Execute task (placeholder - actual implementation would load and run the agent)
            logger.info(f"Executing task {task_id} with {capability}")

            # Simulate task execution
            await asyncio.sleep(0.1)
            result = {"status": "completed", "task_id": task_id}

            # Update execution
            execution.completed_at = datetime.now()
            execution.status = "completed"
            execution.result = result

            # Update capability metrics
            execution_time = (execution.completed_at - execution.started_at).total_seconds()
            cap_info.avg_execution_time = (
                (cap_info.avg_execution_time * 0.9) + (execution_time * 0.1)
            )

            # Move to completed
            self.completed_tasks.append(execution)
            del self.active_tasks[task_id]
            self.task_queue.remove(task)

            cap_info.status = AgentStatus.IDLE

            logger.info(f"Task {task_id} completed successfully")

            return result

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            cap_info.status = AgentStatus.ERROR

            logger.error(f"Task {task_id} failed: {e}")
            raise

    async def get_status(self) -> Dict[str, Any]:
        """Get current status of the Lead Agent"""
        return {
            "token_budget": self.token_budget,
            "tokens_used": self.tokens_used,
            "tokens_remaining": self.token_budget - self.tokens_used,
            "utilization": f"{(self.tokens_used / self.token_budget * 100):.1f}%",
            "active_agents": len(self.active_tasks),
            "queued_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "capabilities": {
                name: {
                    "status": cap.status.value,
                    "success_rate": f"{cap.success_rate * 100:.1f}%",
                    "avg_time": f"{cap.avg_execution_time:.2f}s"
                }
                for name, cap in self.capabilities.items()
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all registered capabilities"""
        health_status = {
            "overall": "healthy",
            "timestamp": datetime.now().isoformat(),
            "capabilities": {}
        }

        unhealthy_count = 0

        for name, cap in self.capabilities.items():
            is_healthy = cap.status != AgentStatus.ERROR

            if not is_healthy:
                unhealthy_count += 1

            health_status["capabilities"][name] = {
                "healthy": is_healthy,
                "status": cap.status.value,
                "last_used": cap.last_used.isoformat() if cap.last_used else None
            }

        if unhealthy_count > 0:
            health_status["overall"] = "degraded"

        if unhealthy_count > len(self.capabilities) / 2:
            health_status["overall"] = "critical"

        return health_status

    def update_token_usage(self, tokens: int):
        """Update token usage counter"""
        self.tokens_used += tokens

        if self.tokens_used > self.token_budget * 0.9:
            logger.warning(
                f"Token budget approaching limit: "
                f"{self.tokens_used:,} / {self.token_budget:,}"
            )

    async def shutdown(self):
        """Gracefully shutdown the Lead Agent"""
        logger.info("Shutting down Lead Agent...")

        # Cancel active tasks
        for task_id in list(self.active_tasks.keys()):
            execution = self.active_tasks[task_id]
            execution.status = "cancelled"
            self.completed_tasks.append(execution)
            del self.active_tasks[task_id]

        # Update all capabilities to idle
        for cap in self.capabilities.values():
            cap.status = AgentStatus.IDLE

        logger.info("Lead Agent shutdown complete")


# Example usage
async def main():
    """Example usage of Lead Agent"""
    lead = LeadAgent(token_budget=200000)

    # Delegate a task
    task_id = await lead.delegate_task(
        capability="embedding",
        task_params={"text": "Example document for embedding"}
    )

    # Execute the task
    result = await lead.execute_task(task_id)
    print(f"Task result: {result}")

    # Get status
    status = await lead.get_status()
    print(f"\nLead Agent Status:")
    print(f"  Token usage: {status['utilization']}")
    print(f"  Active tasks: {status['active_agents']}")
    print(f"  Completed: {status['completed_tasks']}")

    # Health check
    health = await lead.health_check()
    print(f"\nHealth: {health['overall']}")

    # Shutdown
    await lead.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
