#!/usr/bin/env python3
"""
RAG Orchestrator MCP Server
MCP protocol server for coordinating RAG pipeline operations
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.lead_agent import LeadAgent

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


class RAGOrchestratorServer:
    """RAG Orchestrator MCP Server for pipeline coordination"""

    def __init__(self):
        """Initialize RAG Orchestrator Server"""
        self.lead_agent = LeadAgent(
            token_budget=int(os.getenv("TOKEN_BUDGET", "200000")),
            max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
        )

        self.server_info = {
            "name": "rag_orchestrator",
            "version": "1.0.0",
            "description": "RAG pipeline orchestration and coordination",
            "capabilities": [
                "task_delegation",
                "agent_management",
                "status_monitoring",
                "health_checks"
            ]
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health status.

        Returns:
            Health status dictionary
        """
        try:
            agent_health = await self.lead_agent.health_check()

            return {
                "status": "healthy",
                "server": self.server_info["name"],
                "version": self.server_info["version"],
                "agent_health": agent_health,
                "uptime": "running"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def delegate_task(
        self,
        capability: str,
        task_params: Dict[str, Any],
        priority: int = 5
    ) -> Dict[str, Any]:
        """
        Delegate a task to an agent.

        Args:
            capability: Required agent capability
            task_params: Task parameters
            priority: Task priority (1-10)

        Returns:
            Task delegation result
        """
        try:
            task_id = await self.lead_agent.delegate_task(
                capability=capability,
                task_params=task_params,
                priority=priority
            )

            return {
                "success": True,
                "task_id": task_id,
                "capability": capability,
                "status": "queued"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a queued task.

        Args:
            task_id: Task identifier

        Returns:
            Execution result
        """
        try:
            result = await self.lead_agent.execute_task(task_id)

            return {
                "success": True,
                "task_id": task_id,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }

    async def get_status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status.

        Returns:
            Status dictionary
        """
        try:
            status = await self.lead_agent.get_status()

            return {
                "success": True,
                "status": status,
                "server_info": self.server_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def list_capabilities(self) -> Dict[str, Any]:
        """
        List all available agent capabilities.

        Returns:
            Capabilities dictionary
        """
        try:
            capabilities = {
                name: {
                    "description": cap.description,
                    "agent_class": cap.agent_class,
                    "status": cap.status.value
                }
                for name, cap in self.lead_agent.capabilities.items()
            }

            return {
                "success": True,
                "capabilities": capabilities
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def run_pipeline(
        self,
        pipeline_type: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a complete RAG pipeline.

        Args:
            pipeline_type: Type of pipeline (crawl, parse, embed, search, qa)
            input_data: Pipeline input data

        Returns:
            Pipeline execution result
        """
        try:
            # Define pipeline stages based on type
            pipelines = {
                "full": ["crawling", "parsing", "chunking", "embedding", "vector_db"],
                "embed": ["parsing", "chunking", "embedding", "vector_db"],
                "search": ["search", "qa"],
            }

            if pipeline_type not in pipelines:
                return {
                    "success": False,
                    "error": f"Unknown pipeline type: {pipeline_type}"
                }

            stages = pipelines[pipeline_type]
            results = []

            # Execute pipeline stages sequentially
            for stage in stages:
                task_id = await self.lead_agent.delegate_task(
                    capability=stage,
                    task_params=input_data,
                    priority=8
                )

                result = await self.lead_agent.execute_task(task_id)
                results.append({
                    "stage": stage,
                    "task_id": task_id,
                    "result": result
                })

            return {
                "success": True,
                "pipeline_type": pipeline_type,
                "stages_completed": len(results),
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def shutdown(self):
        """Gracefully shutdown the server"""
        await self.lead_agent.shutdown()


# MCP Protocol Handler
async def handle_request(server: RAGOrchestratorServer, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP protocol request.

    Args:
        server: RAG Orchestrator server instance
        request: MCP request dictionary

    Returns:
        MCP response dictionary
    """
    method = request.get("method")
    params = request.get("params", {})

    # Standard MCP protocol handlers
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "health_check",
                    "description": "Check RAG orchestrator health status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "delegate_task",
                    "description": "Delegate a task to an agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "capability": {"type": "string", "description": "Required agent capability"},
                            "task_params": {"type": "object", "description": "Task parameters"},
                            "priority": {"type": "integer", "description": "Task priority (1-10)", "default": 5}
                        },
                        "required": ["capability", "task_params"]
                    }
                },
                {
                    "name": "get_status",
                    "description": "Get current orchestrator status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "list_capabilities",
                    "description": "List all available agent capabilities",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "run_pipeline",
                    "description": "Run a complete RAG pipeline",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "pipeline_type": {"type": "string", "enum": ["full", "embed", "search"]},
                            "input_data": {"type": "object"}
                        },
                        "required": ["pipeline_type", "input_data"]
                    }
                }
            ]
        }

    if method == "tools/call":
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})

        tool_handlers = {
            "health_check": server.health_check,
            "delegate_task": lambda: server.delegate_task(**tool_params),
            "execute_task": lambda: server.execute_task(**tool_params),
            "get_status": server.get_status,
            "list_capabilities": server.list_capabilities,
            "run_pipeline": lambda: server.run_pipeline(**tool_params),
        }

        if tool_name not in tool_handlers:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

        result = await tool_handlers[tool_name]()
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    # Legacy handlers for backward compatibility
    handlers = {
        "health_check": server.health_check,
        "delegate_task": lambda: server.delegate_task(**params),
        "execute_task": lambda: server.execute_task(**params),
        "get_status": server.get_status,
        "list_capabilities": server.list_capabilities,
        "run_pipeline": lambda: server.run_pipeline(**params),
    }

    if method not in handlers:
        return {
            "success": False,
            "error": f"Unknown method: {method}"
        }

    try:
        result = await handlers[method]()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def main():
    """Main server entry point"""
    server = RAGOrchestratorServer()

    print(json.dumps({
        "status": "ready",
        "server": server.server_info
    }), flush=True)

    # Read requests from stdin
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )

            if not line:
                break

            try:
                request = json.loads(line)
                response = await handle_request(server, request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                print(json.dumps({
                    "success": False,
                    "error": f"Invalid JSON: {str(e)}"
                }), flush=True)
            except Exception as e:
                print(json.dumps({
                    "success": False,
                    "error": str(e)
                }), flush=True)

    except KeyboardInterrupt:
        pass
    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
