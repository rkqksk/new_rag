#!/usr/bin/env python3
"""
Skill Creator - Interactive skill creation and validation tool

This executable provides commands for creating, validating, and packaging skills.
"""

import sys
import os
import json
from pathlib import Path

# Add scripts directory to path for imports
SKILL_DIR = Path(__file__).parent
SCRIPTS_DIR = SKILL_DIR / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

# Import validation and packaging utilities
try:
    from quick_validate import validate_skill
    from package_skill import package_skill
except ImportError as e:
    print(f"⚠️  Warning: Could not import utility modules: {e}")
    print(f"   Ensure scripts are in: {SCRIPTS_DIR}")


# Skill metadata
SKILL_INFO = {
    'name': 'skill-creator',
    'version': '2.0.0',
    'description': 'Interactive skill creation tool with comprehensive templates and enhanced validation',
    'commands': ['create', 'validate', 'package', 'help']
}

help_text = """
Skill Creator v2.0 - Create, validate, and package Claude Code skills

✨ NEW in v2.0:
  - Interactive creation mode with guided questions
  - Comprehensive SKILL.md templates (15+ sections)
  - Enhanced validation with detailed recommendations

COMMANDS:
  create <skill-name>           Create a new skill (interactive mode by default)
  validate <skill-path>         Enhanced validation with quality checks
  package <skill-path> [output] Package skill into distributable .zip
  help                          Show this help message

EXAMPLES:
  skill-creator create my-new-skill          # Interactive mode
  skill-creator validate .claude/skills/my-skill
  skill-creator package .claude/skills/my-skill ./dist

SKILL STRUCTURE:
  skill-name/
  ├── SKILL.md (required)       # Comprehensive documentation with YAML frontmatter
  ├── skill.py (optional)       # Executable wrapper for skill logic
  ├── scripts/                  # Executable code (Python/Bash)
  ├── references/               # Documentation loaded as needed
  └── assets/                   # Files used in output

VALIDATION CHECKS:
  ✓ YAML frontmatter format and completeness
  ✓ Required sections (Overview, Commands, Examples)
  ✓ Optional quality sections (Architecture, Best Practices, etc.)
  ✓ Trigger keyword quality (2-10 keywords recommended)
  ✓ Code examples presence
  ✓ skill.py structure (execute function, SKILL_INFO, help text)
  ✓ Directory structure and organization

For detailed guidance, refer to SKILL.md in this directory.
"""


def execute(command, *args):
    """
    Execute a skill-creator command.

    Args:
        command: Command name ('create', 'validate', 'package', 'help')
        *args: Command arguments

    Returns:
        dict: Command execution result
    """
    if command == 'help':
        return {'success': True, 'message': help_text}

    elif command == 'create':
        if not args:
            return {'success': False, 'error': 'Usage: create <skill-name>'}

        skill_name = args[0]
        return create_skill(skill_name)

    elif command == 'validate':
        if not args:
            return {'success': False, 'error': 'Usage: validate <skill-path>'}

        skill_path = args[0]
        return validate_skill_command(skill_path)

    elif command == 'package':
        if not args:
            return {'success': False, 'error': 'Usage: package <skill-path> [output-dir]'}

        skill_path = args[0]
        output_dir = args[1] if len(args) > 1 else None
        return package_skill_command(skill_path, output_dir)

    else:
        return {
            'success': False,
            'error': f'Unknown command: {command}',
            'available_commands': SKILL_INFO['commands'],
            'help': 'Run: skill-creator help'
        }


def create_skill(skill_name, interactive=True):
    """Create a new skill with template structure.

    Args:
        skill_name: Name of the skill (hyphen-case)
        interactive: If True, ask questions for customization
    """
    # Create skill directory
    current_dir = Path.cwd()
    skill_path = current_dir / skill_name

    if skill_path.exists():
        return {'success': False, 'error': f'Directory already exists: {skill_path}'}

    # Interactive mode - gather information
    skill_config = {
        'name': skill_name,
        'description': f'Brief description of {skill_name}',
        'domain': 'general',
        'triggers': ['keyword1', 'keyword2'],
        'commands': ['execute', 'help'],
        'has_authentication': False,
        'has_external_api': False,
        'has_database': False,
        'complexity': 'simple'
    }

    if interactive:
        print(f"\n🎨 Creating skill: {skill_name}")
        print("=" * 60)
        print("\nAnswer the following questions to customize your skill:")
        print("(Press Enter to use defaults shown in brackets)\n")

        # Description
        desc = input(f"1. Brief description [{skill_config['description']}]: ").strip()
        if desc:
            skill_config['description'] = desc

        # Domain
        print("\n2. Domain options: general, data-engineering, web-automation,")
        print("   analysis, security, testing, deployment, other")
        domain = input(f"   Domain [{skill_config['domain']}]: ").strip()
        if domain:
            skill_config['domain'] = domain

        # Triggers
        print("\n3. Trigger keywords (comma-separated)")
        print("   These help Claude Code activate your skill automatically")
        triggers = input(f"   Triggers [{', '.join(skill_config['triggers'])}]: ").strip()
        if triggers:
            skill_config['triggers'] = [t.strip() for t in triggers.split(',')]

        # Commands
        print("\n4. Commands this skill provides (comma-separated)")
        commands = input(f"   Commands [{', '.join(skill_config['commands'])}]: ").strip()
        if commands:
            skill_config['commands'] = [c.strip() for c in commands.split(',')]

        # Features
        print("\n5. Feature flags:")
        auth = input("   Needs authentication? (y/n) [n]: ").strip().lower()
        skill_config['has_authentication'] = auth == 'y'

        api = input("   Uses external APIs? (y/n) [n]: ").strip().lower()
        skill_config['has_external_api'] = api == 'y'

        db = input("   Needs database? (y/n) [n]: ").strip().lower()
        skill_config['has_database'] = db == 'y'

        # Complexity
        print("\n6. Complexity level: simple, moderate, complex")
        complexity = input("   Complexity [simple]: ").strip()
        if complexity in ['moderate', 'complex']:
            skill_config['complexity'] = complexity

        print("\n" + "=" * 60)
        print("✅ Configuration complete! Creating skill structure...\n")

    try:
        # Create directory structure
        skill_path.mkdir(parents=True)
        (skill_path / 'scripts').mkdir()
        (skill_path / 'references').mkdir()
        (skill_path / 'assets').mkdir()

        # Create comprehensive SKILL.md template
        skill_md_content = f"""---
name: {skill_config['name']}
description: {skill_config['description']}
license: MIT
metadata:
  version: "1.0.0"
  domain: "{skill_config['domain']}"
  complexity: "{skill_config['complexity']}"
  triggers:
{chr(10).join(f'    - "{trigger}"' for trigger in skill_config['triggers'])}
  requires_authentication: {str(skill_config['has_authentication']).lower()}
  requires_external_api: {str(skill_config['has_external_api']).lower()}
  requires_database: {str(skill_config['has_database']).lower()}
---

# {skill_config['name'].replace('-', ' ').title()} Skill

## Overview

**Purpose**: {skill_config['description']}

**Domain**: {skill_config['domain'].title()}

**Complexity**: {skill_config['complexity'].title()}

### When to Use

- Describe primary use cases
- Specify scenarios where this skill excels
- Note any prerequisites or dependencies

### When NOT to Use

- List scenarios where this skill is not appropriate
- Mention alternative approaches for those cases

---

## Quick Start

```bash
# Basic usage example
{skill_config['name']} {skill_config['commands'][0]} <args>
```

---

## Commands

{chr(10).join(f'### `{cmd}`' + chr(10) + chr(10) + f'**Description**: What this command does' + chr(10) + chr(10) + f'**Usage**:' + chr(10) + '```bash' + chr(10) + f'{skill_config["name"]} {cmd} <args>' + chr(10) + '```' + chr(10) + chr(10) + f'**Arguments**:' + chr(10) + '- `arg1`: Description' + chr(10) + '- `arg2` (optional): Description' + chr(10) + chr(10) + f'**Returns**: Expected output format' + chr(10) for cmd in skill_config['commands'])}

---

## Configuration

### Environment Variables

```bash
# Add any required environment variables
export SKILL_API_KEY="your-api-key"
export SKILL_CONFIG_PATH="/path/to/config"
```

### Configuration File

```yaml
# config.yaml (if applicable)
setting1: value1
setting2: value2
```

---

## Examples

### Example 1: Basic Usage

```bash
# Description of what this example demonstrates
{skill_config['name']} {skill_config['commands'][0]} --option value
```

**Expected Output**:
```
Expected result shown here
```

### Example 2: Advanced Usage

```bash
# More complex example with multiple options
{skill_config['name']} {skill_config['commands'][0]} \\
  --option1 value1 \\
  --option2 value2
```

**Expected Output**:
```
Advanced result shown here
```

---

## Architecture

### Components

- **Component 1**: Description and responsibility
- **Component 2**: Description and responsibility
- **Component 3**: Description and responsibility

### Data Flow

```
Input → Processing → Validation → Output
```

### Dependencies

- Python 3.11+
- Required libraries (list them)
- External services (if any)

---

## Error Handling

### Common Errors

**Error 1: Missing Configuration**
```
Error: Configuration file not found
```
**Solution**: Create config file at expected location

**Error 2: Authentication Failed**
```
Error: Invalid credentials
```
**Solution**: Check API key and permissions

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| E001 | Configuration error | Check config file |
| E002 | Network error | Verify connectivity |
| E003 | Validation error | Check input format |

---

## Best Practices

### Performance Optimization

- Tip 1: How to optimize performance
- Tip 2: Caching strategies
- Tip 3: Batch processing recommendations

### Security Considerations

- Never commit credentials to version control
- Use environment variables for sensitive data
- Validate all inputs before processing
- Sanitize outputs to prevent injection attacks

### Testing

```bash
# Run skill tests
pytest tests/test_{skill_config['name'].replace('-', '_')}.py -v
```

---

## Troubleshooting

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
{skill_config['name']} {skill_config['commands'][0]} --verbose
```

### Common Issues

**Issue**: Skill not activating automatically
**Cause**: Trigger keywords not matched
**Fix**: Ensure trigger keywords in frontmatter match user intent

**Issue**: Command not found
**Cause**: skill.py not executable
**Fix**: Run `chmod +x skill.py`

---

## Integration

### With Other Skills

- **Skill A**: How this integrates with Skill A
- **Skill B**: Complementary functionality with Skill B

### With MCP Servers

- **filesystem**: File operations integration
- **qdrant**: Vector search integration (if applicable)

### With External Services

- API endpoints used
- Authentication requirements
- Rate limiting considerations

---

## Development

### Adding New Commands

1. Add command to `SKILL_INFO['commands']` in skill.py
2. Implement command handler in `execute()` function
3. Add documentation to SKILL.md Commands section
4. Create tests for new command

### Project Structure

```
{skill_config['name']}/
├── SKILL.md              # This file
├── skill.py              # Executable wrapper
├── scripts/              # Implementation scripts
│   ├── __init__.py
│   └── main_logic.py
├── references/           # Documentation
│   └── API_REFERENCE.md
├── assets/               # Static files
│   └── templates/
└── tests/                # Test suite
    └── test_skill.py
```

---

## Changelog

### Version 1.0.0 (Initial Release)

- Initial skill creation
- Basic command implementation
- Core functionality

---

## License

MIT License - See LICENSE file for details

---

## Support

**Issues**: Report bugs and feature requests
**Documentation**: Additional docs in `references/` directory
**Contributing**: Follow CONTRIBUTING.md guidelines (if applicable)

---

## Related Resources

- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Progressive Disclosure Pattern](https://docs.claude.com/en/docs/claude-code/skills#progressive-disclosure)
- Related skills and tools

---

**Last Updated**: {json.dumps(__import__('datetime').datetime.now().isoformat()[:10])}
**Version**: 1.0.0
**Maintainer**: Your Name/Team
"""

        (skill_path / 'SKILL.md').write_text(skill_md_content)

        # Create optional skill.py template
        skill_py_content = f"""#!/usr/bin/env python3
\"\"\"
{skill_name} - Executable skill wrapper
\"\"\"

import sys
import json

# Skill metadata
SKILL_INFO = {{
    'name': '{skill_name}',
    'version': '1.0.0',
    'commands': ['execute', 'help']
}}

help_text = \"\"\"
{skill_name.replace('-', ' ').title()} Skill

COMMANDS:
  execute <args>  Execute the skill
  help            Show this help message

USAGE:
  {skill_name} execute <args>
\"\"\"


def execute(command, *args):
    \"\"\"
    Execute a skill command.

    Args:
        command: Command name
        *args: Command arguments

    Returns:
        dict: Execution result
    \"\"\"
    if command == 'help':
        return {{'success': True, 'message': help_text}}

    elif command == 'execute':
        # Implement your skill logic here
        return {{
            'success': True,
            'result': 'Skill executed successfully',
            'args': args
        }}

    else:
        return {{
            'success': False,
            'error': f'Unknown command: {{command}}',
            'available_commands': SKILL_INFO['commands']
        }}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(help_text)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    result = execute(command, *args)
    print(json.dumps(result, indent=2))
"""

        (skill_path / 'skill.py').write_text(skill_py_content)
        (skill_path / 'skill.py').chmod(0o755)  # Make executable

        # Create README in subdirectories
        for subdir in ['scripts', 'references', 'assets']:
            readme_path = skill_path / subdir / 'README.md'
            readme_content = {
                'scripts': '# Scripts\n\nExecutable code (Python/Bash/etc.) for deterministic tasks.',
                'references': '# References\n\nDocumentation and reference material loaded as needed.',
                'assets': '# Assets\n\nFiles used in output (templates, images, etc.).'
            }[subdir]
            readme_path.write_text(readme_content)

        return {
            'success': True,
            'message': f'✅ Created skill: {skill_name}',
            'path': str(skill_path),
            'structure': {
                'SKILL.md': 'Skill documentation with YAML frontmatter',
                'skill.py': 'Executable wrapper (optional)',
                'scripts/': 'Executable code directory',
                'references/': 'Documentation directory',
                'assets/': 'Output files directory'
            },
            'next_steps': [
                f'1. Edit {skill_path}/SKILL.md to document your skill',
                f'2. Implement logic in {skill_path}/skill.py',
                f'3. Add scripts, references, and assets as needed',
                f'4. Validate with: skill-creator validate {skill_path}'
            ]
        }

    except Exception as e:
        return {'success': False, 'error': f'Failed to create skill: {e}'}


def validate_skill_command(skill_path):
    """Enhanced validation of a skill structure."""
    skill_path = Path(skill_path)

    # Basic validation first
    try:
        valid, message = validate_skill(skill_path)
        if not valid:
            return {
                'success': False,
                'message': message,
                'path': str(skill_path)
            }
    except Exception as e:
        return {'success': False, 'error': f'Basic validation error: {e}'}

    # Enhanced validation checks
    issues = []
    warnings = []

    try:
        skill_md = skill_path / 'SKILL.md'
        content = skill_md.read_text()

        # Check YAML frontmatter completeness
        if '---' in content:
            frontmatter_match = __import__('re').match(r'^---\n(.*?)\n---', content, __import__('re').DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)

                # Check for recommended fields
                recommended_fields = {
                    'version': 'metadata.version',
                    'domain': 'metadata.domain',
                    'triggers': 'metadata.triggers'
                }

                for field, location in recommended_fields.items():
                    if field not in frontmatter:
                        warnings.append(f"Missing recommended field: {location}")

                # Check trigger keyword quality
                if 'triggers:' in frontmatter:
                    trigger_section = __import__('re').search(r'triggers:\s*(.*?)(?:\n\S|\Z)', frontmatter, __import__('re').DOTALL)
                    if trigger_section:
                        triggers_text = trigger_section.group(1)
                        trigger_count = triggers_text.count('- ')
                        if trigger_count < 2:
                            warnings.append(f"Only {trigger_count} trigger keyword(s) defined - recommend at least 2-3 for better auto-activation")
                        elif trigger_count > 10:
                            warnings.append(f"{trigger_count} trigger keywords may be too many - consider focusing on 3-5 most relevant")

        # Check for required SKILL.md sections
        required_sections = ['Overview', 'Commands', 'Examples']
        optional_sections = ['Configuration', 'Best Practices', 'Troubleshooting', 'Architecture']

        for section in required_sections:
            if f'## {section}' not in content and f'# {section}' not in content:
                issues.append(f"Missing required section: ## {section}")

        missing_optional = []
        for section in optional_sections:
            if f'## {section}' not in content and f'# {section}' not in content:
                missing_optional.append(section)

        if missing_optional:
            warnings.append(f"Missing optional sections that improve quality: {', '.join(missing_optional)}")

        # Check for code examples
        if '```' not in content:
            warnings.append("No code examples found - adding examples greatly improves usability")

        # Check skill.py structure if it exists
        skill_py = skill_path / 'skill.py'
        if skill_py.exists():
            py_content = skill_py.read_text()

            # Check for execute() function
            if 'def execute(' not in py_content:
                issues.append("skill.py missing required execute() function")

            # Check for SKILL_INFO
            if 'SKILL_INFO' not in py_content:
                warnings.append("skill.py missing SKILL_INFO metadata dict")

            # Check for help text
            if 'help_text' not in py_content:
                warnings.append("skill.py missing help_text - recommend adding usage documentation")

            # Check if executable
            import stat
            mode = skill_py.stat().st_mode
            if not (mode & stat.S_IXUSR):
                warnings.append("skill.py is not executable - run: chmod +x skill.py")
        else:
            warnings.append("skill.py not found - consider adding executable wrapper for complex skills")

        # Check directory structure
        expected_dirs = ['scripts', 'references', 'assets']
        for dir_name in expected_dirs:
            dir_path = skill_path / dir_name
            if not dir_path.exists():
                warnings.append(f"Directory '{dir_name}/' not found - consider creating for better organization")

        # Build result message
        if issues:
            return {
                'success': False,
                'message': '❌ Validation failed',
                'path': str(skill_path),
                'issues': issues,
                'warnings': warnings
            }

        if warnings:
            return {
                'success': True,
                'message': '✅ Skill is valid (with recommendations)',
                'path': str(skill_path),
                'warnings': warnings
            }

        return {
            'success': True,
            'message': '✅ Skill is valid and follows best practices!',
            'path': str(skill_path)
        }

    except Exception as e:
        return {'success': False, 'error': f'Enhanced validation error: {e}'}


def package_skill_command(skill_path, output_dir=None):
    """Package a skill into distributable zip."""
    try:
        zip_path = package_skill(skill_path, output_dir)
        if zip_path:
            return {
                'success': True,
                'message': f'✅ Packaged skill successfully',
                'zip_file': str(zip_path)
            }
        else:
            return {'success': False, 'error': 'Packaging failed'}
    except Exception as e:
        return {'success': False, 'error': f'Packaging error: {e}'}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(help_text)
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    result = execute(command, *args)

    if result['success']:
        if 'message' in result:
            print(result['message'])

        # Display path if provided
        if 'path' in result:
            print(f"📂 Path: {result['path']}")

        # Display warnings if any
        if 'warnings' in result and result['warnings']:
            print(f"\n⚠️  Recommendations ({len(result['warnings'])} items):")
            for i, warning in enumerate(result['warnings'], 1):
                print(f"  {i}. {warning}")

        # Display next steps
        if 'next_steps' in result:
            print('\n📋 Next Steps:')
            for step in result['next_steps']:
                print(f'  {step}')
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

        # Display validation issues
        if 'issues' in result and result['issues']:
            print(f"\n🚫 Issues Found ({len(result['issues'])} items):")
            for i, issue in enumerate(result['issues'], 1):
                print(f"  {i}. {issue}")

        # Display warnings even on failure
        if 'warnings' in result and result['warnings']:
            print(f"\n⚠️  Additional Warnings ({len(result['warnings'])} items):")
            for i, warning in enumerate(result['warnings'], 1):
                print(f"  {i}. {warning}")

        if 'help' in result:
            print(f"\n{result['help']}")

        sys.exit(1)
