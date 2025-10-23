"""
Agent Orchestration Skill
Claude Code skill for managing and orchestrating agents
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def execute(command: str, *args) -> dict:
    """
    Execute agent orchestration commands.

    Commands:
        status - Get agent status
        delegate <capability> <params_json> - Delegate task to agent
        health - Check agent health
        capabilities - List all capabilities

    Returns:
        Result dictionary
    """
    try:
        import asyncio
        from agents.lead_agent import LeadAgent

        async def run_command():
            lead_agent = LeadAgent()

            if command == "status":
                return await lead_agent.get_status()

            elif command == "health":
                return await lead_agent.health_check()

            elif command == "capabilities":
                return {
                    name: {
                        "description": cap.description,
                        "status": cap.status.value,
                        "agent_class": cap.agent_class
                    }
                    for name, cap in lead_agent.capabilities.items()
                }

            elif command == "delegate" and len(args) >= 2:
                capability = args[0]
                params = json.loads(args[1]) if isinstance(args[1], str) else args[1]
                priority = int(args[2]) if len(args) > 2 else 5

                task_id = await lead_agent.delegate_task(
                    capability=capability,
                    task_params=params,
                    priority=priority
                )

                return {
                    "success": True,
                    "task_id": task_id,
                    "capability": capability
                }

            else:
                return {
                    "error": f"Unknown command or missing arguments: {command}"
                }

        # Run async command
        return asyncio.run(run_command())

    except Exception as e:
        return {
            "error": str(e),
            "command": command,
            "args": args
        }


def help_text() -> str:
    """Return help text for this skill"""
    return """
Agent Orchestration Skill

Commands:
  agent:status              - Get current agent status
  agent:health              - Check agent health
  agent:capabilities        - List all available capabilities
  agent:delegate <cap> <params> [priority] - Delegate task to agent

Examples:
  agent:status
  agent:capabilities
  agent:delegate embedding '{"text": "Hello world"}' 8
"""


# Skill metadata
SKILL_INFO = {
    "name": "agent_orchestration",
    "version": "1.0.0",
    "description": "Manage and orchestrate agents",
    "commands": ["status", "health", "capabilities", "delegate"]
}
