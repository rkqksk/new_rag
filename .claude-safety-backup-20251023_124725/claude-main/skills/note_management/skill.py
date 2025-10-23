"""
Note Management Skill
Claude Code skill for managing structured documentation
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def execute(command: str, *args) -> dict:
    """
    Execute note management commands.

    Commands:
        progress <task> [metrics_json] - Update progress
        decision <decision> <context> - Log decision
        bug <description> <severity> - Report bug
        summary - Generate weekly summary
        review - Review all notes

    Returns:
        Result dictionary
    """
    try:
        import asyncio
        from agents.note_keeper_agent import NoteKeeperAgent

        async def run_command():
            keeper = NoteKeeperAgent()

            if command == "progress" and len(args) >= 1:
                task = args[0]
                metrics = json.loads(args[1]) if len(args) > 1 and args[1] else None

                await keeper.update_progress(
                    completed_task=task,
                    metrics=metrics
                )

                return {
                    "success": True,
                    "action": "progress_updated",
                    "task": task
                }

            elif command == "decision" and len(args) >= 2:
                decision = args[0]
                context = args[1]
                alternatives = json.loads(args[2]) if len(args) > 2 else None

                await keeper.log_decision(
                    decision=decision,
                    context=context,
                    alternatives=alternatives
                )

                return {
                    "success": True,
                    "action": "decision_logged",
                    "decision": decision
                }

            elif command == "bug" and len(args) >= 1:
                description = args[0]
                severity = args[1] if len(args) > 1 else "medium"
                reproduction_steps = json.loads(args[2]) if len(args) > 2 else None

                bug_id = await keeper.report_bug(
                    description=description,
                    severity=severity,
                    reproduction_steps=reproduction_steps
                )

                return {
                    "success": True,
                    "action": "bug_reported",
                    "bug_id": bug_id
                }

            elif command == "summary":
                summary = await keeper.generate_weekly_summary()
                return {
                    "success": True,
                    "summary": summary
                }

            elif command == "review":
                insights = await keeper.review_all_notes()
                return {
                    "success": True,
                    "insights": insights
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
Note Management Skill

Commands:
  note:progress <task> [metrics] - Update progress tracking
  note:decision <decision> <context> [alternatives] - Log decision
  note:bug <description> [severity] [steps] - Report bug
  note:summary              - Generate weekly summary
  note:review               - Review all notes

Examples:
  note:progress "Implemented Lead Agent" '{"lines": 320}'
  note:decision "Use asyncio" "Need concurrent execution"
  note:bug "Token counter broken" "high"
  note:summary
  note:review
"""


# Skill metadata
SKILL_INFO = {
    "name": "note_management",
    "version": "1.0.0",
    "description": "Manage structured documentation and notes",
    "commands": ["progress", "decision", "bug", "summary", "review"]
}
