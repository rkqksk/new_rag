"""
Claude Code Skills Loader
Automatically loads and registers all available skills
"""

import sys
from pathlib import Path
from typing import Dict, Any, Callable

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class SkillManager:
    """Manages Claude Code skills"""

    def __init__(self):
        self.loaded_skills: Dict[str, Any] = {}
        self.skill_directory = Path(__file__).parent

        # Auto-load all skills
        self._load_skills()

    def _load_skills(self):
        """Load all skills from skill directories"""
        skill_dirs = [
            d for d in self.skill_directory.iterdir()
            if d.is_dir() and not d.name.startswith('_')
        ]

        for skill_dir in skill_dirs:
            skill_file = skill_dir / 'skill.py'

            if skill_file.exists():
                try:
                    # Import skill module dynamically
                    import importlib.util
                    skill_name = skill_dir.name

                    spec = importlib.util.spec_from_file_location(
                        f"skill_{skill_name}",
                        skill_file
                    )
                    skill_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(skill_module)

                    self.loaded_skills[skill_name] = {
                        'execute': skill_module.execute,
                        'help': skill_module.help_text,
                        'info': getattr(skill_module, 'SKILL_INFO', {})
                    }

                    print(f"✅ Loaded skill: {skill_name}")

                except Exception as e:
                    print(f"❌ Failed to load skill {skill_name}: {e}")

    def execute(self, skill_name: str, command: str, *args) -> dict:
        """
        Execute a skill command.

        Args:
            skill_name: Name of the skill
            command: Command to execute
            *args: Command arguments

        Returns:
            Result dictionary
        """
        if skill_name not in self.loaded_skills:
            return {
                "error": f"Skill not found: {skill_name}",
                "available_skills": list(self.loaded_skills.keys())
            }

        skill = self.loaded_skills[skill_name]

        try:
            return skill['execute'](command, *args)
        except Exception as e:
            return {
                "error": str(e),
                "skill": skill_name,
                "command": command
            }

    def get_help(self, skill_name: str = None) -> str:
        """Get help text for a skill or all skills"""
        if skill_name:
            if skill_name in self.loaded_skills:
                return self.loaded_skills[skill_name]['help']()
            else:
                return f"Skill not found: {skill_name}"
        else:
            # Return help for all skills
            help_text = "Available Skills:\n\n"

            for name, skill in self.loaded_skills.items():
                info = skill['info']
                help_text += f"**{name}** (v{info.get('version', '1.0.0')})\n"
                help_text += f"{info.get('description', 'No description')}\n"
                help_text += f"Commands: {', '.join(info.get('commands', []))}\n\n"

            return help_text

    def list_skills(self) -> Dict[str, Dict[str, Any]]:
        """List all loaded skills with their info"""
        return {
            name: skill['info']
            for name, skill in self.loaded_skills.items()
        }


# Global skill manager instance
manager = SkillManager()


def execute(skill_name: str, command: str, *args) -> dict:
    """Execute a skill command (convenience function)"""
    return manager.execute(skill_name, command, *args)


def help(skill_name: str = None) -> str:
    """Get help text (convenience function)"""
    return manager.get_help(skill_name)


def commands() -> list:
    """List all available commands across all skills"""
    all_commands = []

    for name, skill in manager.loaded_skills.items():
        info = skill['info']
        for cmd in info.get('commands', []):
            all_commands.append(f"{name}:{cmd}")

    return all_commands


# Print loaded skills on import
if __name__ != "__main__":
    print(f"\nClaude Code Skills: {len(manager.loaded_skills)} skills loaded")
    for skill_name in manager.loaded_skills.keys():
        print(f"  • {skill_name}")
