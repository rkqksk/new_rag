"""
RAG Pipeline Skill
Claude Code skill for managing RAG pipeline operations
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def execute(command: str, *args) -> dict:
    """
    Execute RAG pipeline commands.

    Commands:
        run <pipeline_type> <input_json> - Run complete pipeline
        stage <stage_name> <params_json> - Run single pipeline stage
        status - Get pipeline status
        help - Show available pipelines

    Returns:
        Result dictionary
    """
    try:
        import asyncio
        from agents.lead_agent import LeadAgent

        async def run_command():
            lead_agent = LeadAgent()

            if command == "run" and len(args) >= 2:
                pipeline_type = args[0]
                input_data = json.loads(args[1]) if isinstance(args[1], str) else args[1]

                # Define pipeline stages
                pipelines = {
                    "full": ["crawling", "parsing", "chunking", "embedding", "vector_db"],
                    "embed": ["parsing", "chunking", "embedding", "vector_db"],
                    "search": ["search", "qa"],
                }

                if pipeline_type not in pipelines:
                    return {
                        "error": f"Unknown pipeline: {pipeline_type}",
                        "available": list(pipelines.keys())
                    }

                stages = pipelines[pipeline_type]
                results = []

                for stage in stages:
                    task_id = await lead_agent.delegate_task(
                        capability=stage,
                        task_params=input_data,
                        priority=8
                    )

                    result = await lead_agent.execute_task(task_id)
                    results.append({
                        "stage": stage,
                        "task_id": task_id,
                        "result": result
                    })

                return {
                    "success": True,
                    "pipeline": pipeline_type,
                    "stages_completed": len(results),
                    "results": results
                }

            elif command == "stage" and len(args) >= 2:
                stage_name = args[0]
                params = json.loads(args[1]) if isinstance(args[1], str) else args[1]

                task_id = await lead_agent.delegate_task(
                    capability=stage_name,
                    task_params=params,
                    priority=7
                )

                result = await lead_agent.execute_task(task_id)

                return {
                    "success": True,
                    "stage": stage_name,
                    "task_id": task_id,
                    "result": result
                }

            elif command == "status":
                status = await lead_agent.get_status()
                return {
                    "success": True,
                    "status": status
                }

            elif command == "help":
                return {
                    "pipelines": {
                        "full": "Complete RAG pipeline: crawl → parse → chunk → embed → index",
                        "embed": "Embedding pipeline: parse → chunk → embed → index",
                        "search": "Search pipeline: search → qa"
                    },
                    "stages": [
                        "crawling", "parsing", "chunking",
                        "embedding", "vector_db", "search", "qa"
                    ]
                }

            else:
                return {
                    "error": f"Unknown command or missing arguments: {command}",
                    "hint": "Use 'rag:pipeline help' for available pipelines"
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
RAG Pipeline Skill

Commands:
  rag:pipeline run <type> <input>   - Run complete pipeline
  rag:pipeline stage <stage> <params> - Run single stage
  rag:pipeline status               - Get pipeline status
  rag:pipeline help                 - Show available pipelines

Pipeline Types:
  full    - Complete RAG: crawl → parse → chunk → embed → index
  embed   - Embedding: parse → chunk → embed → index
  search  - Search: search → qa

Examples:
  rag:pipeline run full '{"url": "https://example.com"}'
  rag:pipeline run embed '{"file": "document.pdf"}'
  rag:pipeline stage embedding '{"text": "Hello world"}'
  rag:pipeline status
"""


# Skill metadata
SKILL_INFO = {
    "name": "rag_pipeline",
    "version": "1.0.0",
    "description": "Manage RAG pipeline operations",
    "commands": ["run", "stage", "status", "help"]
}
