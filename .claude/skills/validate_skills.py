#!/usr/bin/env python3
"""
Validate Claude Skills format and triggers
"""
import os
import re
from pathlib import Path
import yaml

def validate_skill(skill_path):
    """Validate a single skill"""
    skill_name = skill_path.parent.name
    errors = []
    warnings = []

    # Check SKILL.md exists
    if not skill_path.exists():
        return {
            'skill': skill_name,
            'valid': False,
            'errors': [f'SKILL.md not found in {skill_path.parent}'],
            'warnings': []
        }

    # Read file
    content = skill_path.read_text()

    # Check YAML frontmatter
    yaml_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not yaml_match:
        errors.append('No YAML frontmatter found')
        return {
            'skill': skill_name,
            'valid': False,
            'errors': errors,
            'warnings': warnings
        }

    # Parse YAML
    try:
        frontmatter = yaml.safe_load(yaml_match.group(1))
    except yaml.YAMLError as e:
        errors.append(f'Invalid YAML: {e}')
        return {
            'skill': skill_name,
            'valid': False,
            'errors': errors,
            'warnings': warnings
        }

    # Check required fields
    if 'name' not in frontmatter:
        errors.append('Missing "name" field in frontmatter')
    elif frontmatter['name'] != skill_name:
        errors.append(f'Name mismatch: frontmatter "{frontmatter["name"]}" != directory "{skill_name}"')

    if 'description' not in frontmatter:
        errors.append('Missing "description" field in frontmatter')
    else:
        desc = frontmatter['description']

        # Check description length
        if len(desc) < 50:
            warnings.append(f'Description very short ({len(desc)} chars), may not trigger well')
        elif len(desc) < 100:
            warnings.append(f'Description short ({len(desc)} chars), consider adding more keywords')

        # Check for Korean keywords
        if not re.search(r'[\uac00-\ud7a3]', desc):
            warnings.append('No Korean keywords found in description')

        # Count keywords
        keywords = len(desc.split())
        if keywords < 10:
            warnings.append(f'Only {keywords} keywords, consider adding more')

    # Check content sections
    if '## When to Use' not in content:
        warnings.append('Missing "When to Use" section')

    if '## Core Capabilities' not in content and '## Core Features' not in content:
        warnings.append('Missing "Core Capabilities/Features" section')

    if '## Quick Actions' not in content and '## Usage' not in content:
        warnings.append('Missing "Quick Actions/Usage" section')

    # Check for integration mentions
    if '## Integration' not in content:
        warnings.append('Missing "Integration" section (skill chaining)')

    # Success
    return {
        'skill': skill_name,
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'stats': {
            'name': frontmatter.get('name'),
            'description_length': len(frontmatter.get('description', '')),
            'keyword_count': len(frontmatter.get('description', '').split()),
            'has_korean': bool(re.search(r'[\uac00-\ud7a3]', frontmatter.get('description', ''))),
            'file_size': skill_path.stat().st_size
        }
    }

def main():
    skills_dir = Path('/home/rkqksk/projects/new_rag/.claude/skills')

    print("=" * 80)
    print("Claude Skills Validation Report")
    print("=" * 80)
    print()

    results = []

    # Find all skills
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / 'SKILL.md'
        result = validate_skill(skill_md)
        results.append(result)

    # Print results
    valid_count = sum(1 for r in results if r['valid'])
    total_count = len(results)

    print(f"Found {total_count} skill directories")
    print(f"Valid skills: {valid_count}/{total_count}")
    print()

    # Detailed results
    for result in results:
        print(f"Skill: {result['skill']}")
        print(f"  Valid: {'✅ Yes' if result['valid'] else '❌ No'}")

        if result.get('stats'):
            stats = result['stats']
            print(f"  Name: {stats['name']}")
            print(f"  Description: {stats['description_length']} chars, {stats['keyword_count']} keywords")
            print(f"  Korean: {'✅' if stats['has_korean'] else '❌'}")
            print(f"  File size: {stats['file_size']} bytes")

        if result['errors']:
            print("  Errors:")
            for error in result['errors']:
                print(f"    ❌ {error}")

        if result['warnings']:
            print("  Warnings:")
            for warning in result['warnings']:
                print(f"    ⚠️  {warning}")

        print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total skills: {total_count}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {total_count - valid_count}")
    print(f"Success rate: {valid_count/total_count*100:.1f}%")

    # Exit code
    return 0 if valid_count == total_count else 1

if __name__ == '__main__':
    exit(main())
