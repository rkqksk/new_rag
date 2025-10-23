#!/usr/bin/env python3
"""
Note Keeper MCP Server
MCP protocol server for structured documentation management
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

from agents.note_keeper_agent import NoteKeeperAgent

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


class NoteKeeperServer:
    """Note Keeper MCP Server for documentation management"""

    def __init__(self):
        """Initialize Note Keeper Server"""
        project_root_path = os.getenv(
            "PROJECT_ROOT",
            "/Users/oypnus/Project/rag-enterprise"
        )

        self.note_keeper = NoteKeeperAgent(project_root=project_root_path)

        self.server_info = {
            "name": "note_keeper",
            "version": "1.0.0",
            "description": "Structured documentation and progress tracking",
            "capabilities": [
                "progress_tracking",
                "decision_logging",
                "bug_reporting",
                "weekly_summaries",
                "note_review"
            ]
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health status.

        Returns:
            Health status dictionary
        """
        try:
            # Check if note files are accessible using agent's actual paths
            files_status = {}

            file_paths = {
                "progress.md": self.note_keeper.progress_file,
                "decisions.md": self.note_keeper.decisions_file,
                "bugs.md": self.note_keeper.bugs_file,
                "SYSTEM_REVIEW.md": self.note_keeper.system_review_file
            }

            for file_name, file_path in file_paths.items():
                files_status[file_name] = {
                    "exists": file_path.exists(),
                    "readable": os.access(file_path, os.R_OK) if file_path.exists() else False,
                    "writable": os.access(file_path, os.W_OK) if file_path.exists() else False,
                    "path": str(file_path)
                }

            all_accessible = all(
                status["exists"] and status["readable"] and status["writable"]
                for status in files_status.values()
            )

            return {
                "status": "healthy" if all_accessible else "degraded",
                "server": self.server_info["name"],
                "version": self.server_info["version"],
                "files": files_status,
                "project_root": str(self.note_keeper.project_root)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def update_progress(
        self,
        completed_task: str,
        metrics: Optional[Dict[str, Any]] = None,
        blockers: Optional[List[str]] = None,
        next_steps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update progress tracking.

        Args:
            completed_task: Description of completed work
            metrics: Optional metrics
            blockers: Current blockers
            next_steps: Planned next steps

        Returns:
            Update result
        """
        try:
            await self.note_keeper.update_progress(
                completed_task=completed_task,
                metrics=metrics,
                blockers=blockers,
                next_steps=next_steps
            )

            return {
                "success": True,
                "action": "progress_updated",
                "task": completed_task
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def log_decision(
        self,
        decision: str,
        context: str,
        alternatives: Optional[List[str]] = None,
        consequences: Optional[List[str]] = None,
        stakeholders: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Log a technical decision.

        Args:
            decision: The decision made
            context: Why this decision was needed
            alternatives: Alternative options considered
            consequences: Expected consequences
            stakeholders: People involved

        Returns:
            Logging result
        """
        try:
            await self.note_keeper.log_decision(
                decision=decision,
                context=context,
                alternatives=alternatives,
                consequences=consequences,
                stakeholders=stakeholders
            )

            return {
                "success": True,
                "action": "decision_logged",
                "decision": decision
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def report_bug(
        self,
        description: str,
        severity: str = "medium",
        reproduction_steps: Optional[List[str]] = None,
        assignee: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Report a new bug.

        Args:
            description: Bug description
            severity: Bug severity (critical, high, medium, low)
            reproduction_steps: Steps to reproduce
            assignee: Person assigned to fix

        Returns:
            Bug reporting result with bug ID
        """
        try:
            bug_id = await self.note_keeper.report_bug(
                description=description,
                severity=severity,
                reproduction_steps=reproduction_steps,
                assignee=assignee
            )

            return {
                "success": True,
                "action": "bug_reported",
                "bug_id": bug_id,
                "severity": severity
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def update_bug_status(
        self,
        bug_id: str,
        status: str,
        fix_commit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update bug status.

        Args:
            bug_id: Bug identifier
            status: New status (open, investigating, fixed, closed)
            fix_commit: Git commit hash of the fix

        Returns:
            Update result
        """
        try:
            await self.note_keeper.update_bug_status(
                bug_id=bug_id,
                status=status,
                fix_commit=fix_commit
            )

            return {
                "success": True,
                "action": "bug_status_updated",
                "bug_id": bug_id,
                "status": status
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_weekly_summary(self) -> Dict[str, Any]:
        """
        Generate weekly summary.

        Returns:
            Weekly summary with statistics
        """
        try:
            summary = await self.note_keeper.generate_weekly_summary()

            return {
                "success": True,
                "action": "weekly_summary_generated",
                "summary": summary
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def review_all_notes(self) -> Dict[str, Any]:
        """
        Review all notes and generate insights.

        Returns:
            Review insights
        """
        try:
            insights = await self.note_keeper.review_all_notes()

            return {
                "success": True,
                "action": "notes_reviewed",
                "insights": insights
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# MCP Protocol Handler
async def handle_request(server: NoteKeeperServer, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP protocol request.

    Args:
        server: Note Keeper server instance
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
                    "description": "Check note keeper health status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "update_progress",
                    "description": "Update progress tracking",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "completed_task": {"type": "string", "description": "Description of completed work"},
                            "metrics": {"type": "object", "description": "Optional metrics"},
                            "blockers": {"type": "array", "items": {"type": "string"}, "description": "Current blockers"},
                            "next_steps": {"type": "array", "items": {"type": "string"}, "description": "Planned next steps"}
                        },
                        "required": ["completed_task"]
                    }
                },
                {
                    "name": "log_decision",
                    "description": "Log a technical decision",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "decision": {"type": "string"},
                            "context": {"type": "string"},
                            "alternatives": {"type": "array", "items": {"type": "string"}},
                            "consequences": {"type": "array", "items": {"type": "string"}},
                            "stakeholders": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["decision", "context"]
                    }
                },
                {
                    "name": "report_bug",
                    "description": "Report a new bug",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"], "default": "medium"},
                            "reproduction_steps": {"type": "array", "items": {"type": "string"}},
                            "assignee": {"type": "string"}
                        },
                        "required": ["description"]
                    }
                },
                {
                    "name": "generate_weekly_summary",
                    "description": "Generate weekly summary",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "review_all_notes",
                    "description": "Review all notes and generate insights",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ]
        }

    if method == "tools/call":
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})

        tool_handlers = {
            "health_check": server.health_check,
            "update_progress": lambda: server.update_progress(**tool_params),
            "log_decision": lambda: server.log_decision(**tool_params),
            "report_bug": lambda: server.report_bug(**tool_params),
            "update_bug_status": lambda: server.update_bug_status(**tool_params),
            "generate_weekly_summary": server.generate_weekly_summary,
            "review_all_notes": server.review_all_notes,
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
        "update_progress": lambda: server.update_progress(**params),
        "log_decision": lambda: server.log_decision(**params),
        "report_bug": lambda: server.report_bug(**params),
        "update_bug_status": lambda: server.update_bug_status(**params),
        "generate_weekly_summary": server.generate_weekly_summary,
        "review_all_notes": server.review_all_notes,
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
    server = NoteKeeperServer()

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


if __name__ == "__main__":
    asyncio.run(main())
