"""
Note Keeper Agent - Structured Documentation Manager
Manages progress tracking, decision logging, bug reporting, and weekly summaries
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NoteType(Enum):
    """Types of structured notes"""
    PROGRESS = "progress"
    DECISION = "decision"
    BUG = "bug"
    SYSTEM_REVIEW = "system_review"


@dataclass
class ProgressEntry:
    """Progress tracking entry"""
    timestamp: datetime
    completed_task: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    blockers: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


@dataclass
class DecisionEntry:
    """Technical decision record"""
    timestamp: datetime
    decision: str
    context: str
    alternatives: List[str] = field(default_factory=list)
    consequences: List[str] = field(default_factory=list)
    stakeholders: List[str] = field(default_factory=list)


@dataclass
class BugEntry:
    """Bug tracking entry"""
    timestamp: datetime
    bug_id: str
    severity: str  # critical, high, medium, low
    description: str
    reproduction_steps: List[str] = field(default_factory=list)
    status: str = "open"  # open, investigating, fixed, closed
    assignee: Optional[str] = None
    fix_commit: Optional[str] = None


class NoteKeeperAgent:
    """
    Structured documentation manager for RAG Enterprise.
    Maintains organized notes for progress, decisions, bugs, and reviews.
    """

    def __init__(self, project_root: str = "/Users/oypnus/project/rag-enterprise"):
        self.project_root = Path(project_root)

        # Note file paths
        # Updated document paths - organized structure
        self.progress_file = self.project_root / "docs/progress/progress.md"
        self.decisions_file = self.project_root / "docs/decisions/decisions.md"
        self.bugs_file = self.project_root / "docs/system/bugs.md"
        self.system_review_file = self.project_root / "docs/system/SYSTEM_REVIEW.md"

        # Report directories
        self.daily_reports_dir = self.project_root / "docs/reports/daily"
        self.weekly_reports_dir = self.project_root / "docs/reports/weekly"
        self.analysis_dir = self.project_root / "docs/analysis"

        # In-memory caches
        self.progress_entries: List[ProgressEntry] = []
        self.decision_entries: List[DecisionEntry] = []
        self.bug_entries: List[BugEntry] = []

        logger.info(f"Note Keeper Agent initialized for project: {project_root}")

    async def update_progress(
        self,
        completed_task: str,
        metrics: Optional[Dict[str, Any]] = None,
        blockers: Optional[List[str]] = None,
        next_steps: Optional[List[str]] = None
    ):
        """
        Update progress tracking with completed task.

        Args:
            completed_task: Description of completed work
            metrics: Optional metrics (e.g., test coverage, performance)
            blockers: Current blockers to progress
            next_steps: Planned next steps
        """
        entry = ProgressEntry(
            timestamp=datetime.now(),
            completed_task=completed_task,
            metrics=metrics or {},
            blockers=blockers or [],
            next_steps=next_steps or []
        )

        self.progress_entries.append(entry)

        # Write to file
        await self._write_progress_entry(entry)

        logger.info(f"Progress updated: {completed_task}")

    async def _write_progress_entry(self, entry: ProgressEntry):
        """Write progress entry to progress.md"""
        content = f"\n## {entry.timestamp.strftime('%Y-%m-%d %H:%M')}\n\n"
        content += f"**Completed:** {entry.completed_task}\n\n"

        if entry.metrics:
            content += "**Metrics:**\n"
            for key, value in entry.metrics.items():
                content += f"- {key}: {value}\n"
            content += "\n"

        if entry.blockers:
            content += "**Blockers:**\n"
            for blocker in entry.blockers:
                content += f"- 🚫 {blocker}\n"
            content += "\n"

        if entry.next_steps:
            content += "**Next Steps:**\n"
            for step in entry.next_steps:
                content += f"- [ ] {step}\n"
            content += "\n"

        # Append to file
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(content)

    async def log_decision(
        self,
        decision: str,
        context: str,
        alternatives: Optional[List[str]] = None,
        consequences: Optional[List[str]] = None,
        stakeholders: Optional[List[str]] = None
    ):
        """
        Log a technical decision.

        Args:
            decision: The decision made
            context: Why this decision was needed
            alternatives: Alternative options considered
            consequences: Expected consequences and trade-offs
            stakeholders: People involved in the decision
        """
        entry = DecisionEntry(
            timestamp=datetime.now(),
            decision=decision,
            context=context,
            alternatives=alternatives or [],
            consequences=consequences or [],
            stakeholders=stakeholders or []
        )

        self.decision_entries.append(entry)

        # Write to file
        await self._write_decision_entry(entry)

        logger.info(f"Decision logged: {decision}")

    async def _write_decision_entry(self, entry: DecisionEntry):
        """Write decision entry to decisions.md"""
        content = f"\n## {entry.timestamp.strftime('%Y-%m-%d')} - {entry.decision}\n\n"
        content += f"**Context:** {entry.context}\n\n"

        if entry.alternatives:
            content += "**Alternatives Considered:**\n"
            for alt in entry.alternatives:
                content += f"- {alt}\n"
            content += "\n"

        if entry.consequences:
            content += "**Consequences:**\n"
            for cons in entry.consequences:
                content += f"- {cons}\n"
            content += "\n"

        if entry.stakeholders:
            content += f"**Stakeholders:** {', '.join(entry.stakeholders)}\n\n"

        content += "---\n"

        # Append to file
        with open(self.decisions_file, "a", encoding="utf-8") as f:
            f.write(content)

    async def report_bug(
        self,
        description: str,
        severity: str = "medium",
        reproduction_steps: Optional[List[str]] = None,
        assignee: Optional[str] = None
    ) -> str:
        """
        Report a new bug.

        Args:
            description: Bug description
            severity: Bug severity (critical, high, medium, low)
            reproduction_steps: Steps to reproduce the bug
            assignee: Person assigned to fix

        Returns:
            bug_id: Unique identifier for the bug
        """
        # Generate bug ID
        bug_id = f"BUG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        entry = BugEntry(
            timestamp=datetime.now(),
            bug_id=bug_id,
            severity=severity,
            description=description,
            reproduction_steps=reproduction_steps or [],
            assignee=assignee
        )

        self.bug_entries.append(entry)

        # Write to file
        await self._write_bug_entry(entry)

        logger.info(f"Bug reported: {bug_id} - {description}")

        return bug_id

    async def _write_bug_entry(self, entry: BugEntry):
        """Write bug entry to bugs.md"""
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }

        content = f"\n## {severity_emoji.get(entry.severity, '⚪')} {entry.bug_id}\n\n"
        content += f"**Severity:** {entry.severity.upper()}\n"
        content += f"**Status:** {entry.status}\n"
        content += f"**Reported:** {entry.timestamp.strftime('%Y-%m-%d %H:%M')}\n"

        if entry.assignee:
            content += f"**Assignee:** {entry.assignee}\n"

        content += f"\n**Description:**\n{entry.description}\n\n"

        if entry.reproduction_steps:
            content += "**Reproduction Steps:**\n"
            for i, step in enumerate(entry.reproduction_steps, 1):
                content += f"{i}. {step}\n"
            content += "\n"

        if entry.fix_commit:
            content += f"**Fix Commit:** {entry.fix_commit}\n\n"

        content += "---\n"

        # Append to file
        with open(self.bugs_file, "a", encoding="utf-8") as f:
            f.write(content)

    async def update_bug_status(
        self,
        bug_id: str,
        status: str,
        fix_commit: Optional[str] = None
    ):
        """Update bug status"""
        # Find bug entry
        entry = next((b for b in self.bug_entries if b.bug_id == bug_id), None)

        if not entry:
            raise ValueError(f"Bug not found: {bug_id}")

        entry.status = status

        if fix_commit:
            entry.fix_commit = fix_commit

        logger.info(f"Bug {bug_id} updated: {status}")

        # Rewrite entire bugs.md file
        await self._rewrite_bugs_file()

    async def _rewrite_bugs_file(self):
        """Rewrite bugs.md with all current entries"""
        content = "# Bug Tracking\n\n"
        content += f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        for entry in self.bug_entries:
            await self._write_bug_entry(entry)

    async def generate_weekly_summary(self) -> Dict[str, Any]:
        """
        Generate weekly summary of progress, decisions, and bugs.

        Returns:
            Dictionary with summary statistics and highlights
        """
        now = datetime.now()
        week_start = now - timedelta(days=7)

        # Filter entries from last week
        recent_progress = [
            e for e in self.progress_entries
            if e.timestamp >= week_start
        ]

        recent_decisions = [
            e for e in self.decision_entries
            if e.timestamp >= week_start
        ]

        recent_bugs = [
            e for e in self.bug_entries
            if e.timestamp >= week_start
        ]

        summary = {
            "week": f"{week_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
            "progress": {
                "tasks_completed": len(recent_progress),
                "highlights": [e.completed_task for e in recent_progress[:5]]
            },
            "decisions": {
                "count": len(recent_decisions),
                "highlights": [e.decision for e in recent_decisions[:3]]
            },
            "bugs": {
                "reported": len(recent_bugs),
                "by_severity": self._count_by_severity(recent_bugs),
                "open": len([b for b in recent_bugs if b.status == "open"])
            },
            "generated_at": now.isoformat()
        }

        logger.info(f"Weekly summary generated: {summary['week']}")

        return summary

    def _count_by_severity(self, bugs: List[BugEntry]) -> Dict[str, int]:
        """Count bugs by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for bug in bugs:
            if bug.severity in counts:
                counts[bug.severity] += 1

        return counts

    async def review_all_notes(self) -> Dict[str, Any]:
        """
        Review all notes and generate insights.

        Returns:
            Dictionary with insights and recommendations
        """
        # Read current files
        progress_content = self._read_file(self.progress_file)
        decisions_content = self._read_file(self.decisions_file)
        bugs_content = self._read_file(self.bugs_file)

        insights = {
            "files": {
                "progress.md": {
                    "size": len(progress_content),
                    "entries": len(self.progress_entries)
                },
                "decisions.md": {
                    "size": len(decisions_content),
                    "entries": len(self.decision_entries)
                },
                "bugs.md": {
                    "size": len(bugs_content),
                    "entries": len(self.bug_entries)
                }
            },
            "open_bugs": len([b for b in self.bug_entries if b.status == "open"]),
            "recent_activity": len([
                e for e in self.progress_entries
                if e.timestamp >= datetime.now() - timedelta(days=7)
            ])
        }

        return insights

    async def create_report(
        self,
        report_type: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Create a timestamped report in the appropriate directory.

        Args:
            report_type: Type of report ('daily', 'weekly', 'analysis', 'custom')
            title: Report title (will be slugified for filename)
            content: Report content in markdown format
            metadata: Optional metadata to include in report header

        Returns:
            Path to the created report file
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        date_str = now.strftime("%Y-%m-%d")

        # Slugify title for filename
        slug = title.lower().replace(" ", "_").replace("/", "_")
        filename = f"{timestamp}_{slug}.md"

        # Determine target directory
        if report_type == "daily":
            target_dir = self.daily_reports_dir / date_str
        elif report_type == "weekly":
            target_dir = self.weekly_reports_dir
        elif report_type == "analysis":
            target_dir = self.analysis_dir
        else:
            target_dir = self.project_root / "docs/reports"

        # Ensure directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create report file
        report_path = target_dir / filename

        # Build report content with header
        report_header = f"""# {title}

**Generated**: {now.strftime("%Y-%m-%d %H:%M:%S")}
**Type**: {report_type}
**Location**: `{report_path.relative_to(self.project_root)}`

"""

        if metadata:
            report_header += "## Metadata\n\n"
            for key, value in metadata.items():
                report_header += f"- **{key}**: {value}\n"
            report_header += "\n"

        report_header += "---\n\n"

        full_content = report_header + content

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        logger.info(f"Created {report_type} report: {report_path}")

        return report_path

    async def create_daily_report(
        self,
        tasks_completed: List[str],
        metrics: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Path:
        """
        Create a daily progress report.

        Args:
            tasks_completed: List of tasks completed today
            metrics: Optional metrics (lines of code, test coverage, etc.)
            notes: Optional additional notes

        Returns:
            Path to the created daily report
        """
        today = datetime.now().strftime("%Y-%m-%d")

        content = f"## Tasks Completed\n\n"
        for task in tasks_completed:
            content += f"- ✅ {task}\n"
        content += "\n"

        if metrics:
            content += "## Metrics\n\n"
            for key, value in metrics.items():
                content += f"- **{key}**: {value}\n"
            content += "\n"

        if notes:
            content += f"## Notes\n\n{notes}\n\n"

        # Add recent decisions and bugs
        recent_decisions = [
            d for d in self.decision_entries
            if d.timestamp.date() == datetime.now().date()
        ]

        if recent_decisions:
            content += "## Decisions Made Today\n\n"
            for decision in recent_decisions:
                content += f"- {decision.decision}\n"
            content += "\n"

        return await self.create_report(
            report_type="daily",
            title=f"Daily Progress - {today}",
            content=content,
            metadata={"date": today, "tasks_count": len(tasks_completed)}
        )

    def _read_file(self, file_path: Path) -> str:
        """Read file content"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""


# Example usage
async def main():
    """Example usage of Note Keeper Agent"""
    keeper = NoteKeeperAgent()

    # Update progress
    await keeper.update_progress(
        completed_task="Implemented Lead Agent with task orchestration",
        metrics={"lines_of_code": 320, "test_coverage": "85%"},
        next_steps=[
            "Create Note Keeper Agent",
            "Set up MCP servers",
            "Integration testing"
        ]
    )

    # Log decision
    await keeper.log_decision(
        decision="Use asyncio for agent coordination",
        context="Need concurrent task execution and non-blocking I/O",
        alternatives=[
            "Threading with ThreadPoolExecutor",
            "Multiprocessing with Pool"
        ],
        consequences=[
            "Better performance for I/O-bound tasks",
            "Simpler error handling",
            "Single-threaded execution"
        ]
    )

    # Report bug
    bug_id = await keeper.report_bug(
        description="Token counter not updating correctly",
        severity="medium",
        reproduction_steps=[
            "Execute task with Lead Agent",
            "Check token usage",
            "Notice counter stays at 0"
        ]
    )

    # Generate weekly summary
    summary = await keeper.generate_weekly_summary()
    print(json.dumps(summary, indent=2))

    # Review notes
    insights = await keeper.review_all_notes()
    print(f"\nInsights: {insights}")


if __name__ == "__main__":
    asyncio.run(main())
