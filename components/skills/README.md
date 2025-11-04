# SKILLs Component Documentation

**SKILLs** are Claude Code's interface layer - they define triggers, commands, and documentation that Claude can access.

---

## Overview

SKILLs provide:
- **Triggers** - Keywords that auto-activate the SKILL
- **Commands** - Available operations (process, query, search, etc.)
- **Documentation** - Progressive disclosure documentation in SKILL.md
- **Executable wrappers** - skill.py that connects to plugins

---

## Architecture

```
User Request
    ↓
Claude recognizes trigger keyword
    ↓
.claude/skills/{skill-name}/
    ├── SKILL.md        ← Progressive disclosure docs
    └── skill.py        ← Executable wrapper
    ↓
Calls Plugin (plugins/)
    ↓
Returns Result
```

---

## Active SKILLs

### 1. rag-pipeline
**Location**: `.claude/skills/rag-pipeline/`
**Purpose**: Unified RAG orchestration - document processing, vector search, answer generation
**Commands**: `process`, `query`, `search`, `batch_process`, `optimize_index`, `evaluate`, `stats`
**Triggers**: "RAG query", "document upload", "vector search", "semantic search"

**Usage**:
```python
from .claude.skills.rag_pipeline import skill

# Process document
skill.execute('process', {'file_path': 'doc.pdf'})

# RAG query
skill.execute('query', {'question': 'What are the requirements?'})

# Vector search
skill.execute('search', {'query': '50ml bottle', 'top_k': 10})
```

### 2. manufacturing-expert
**Location**: `.claude/skills/manufacturing-expert/`
**Purpose**: Manufacturing document classification and terminology extraction
**Commands**: `process`, `classify`, `extract`
**Triggers**: "manufacturing", "SOP", "FMEA", "quality control"

**Extracted Data**:
- Document types: SOP, equipment specs, quality plans, FMEA, batch records
- Terminology: Cpk, OEE, PPM, MTBF, Six Sigma
- Standards: ISO 9001, FDA 21 CFR Part 11, GMP

### 3. packaging-expert
**Location**: `.claude/skills/packaging-expert/`
**Purpose**: Packaging material identification and regulatory compliance
**Commands**: `process`, `classify`, `extract`
**Triggers**: "packaging", "material spec", "container", "bottle"

**Extracted Data**:
- Materials: PET, HDPE, PP, LDPE, PS
- Regulatory: FDA 21 CFR 177, EU 10/2011, REACH
- Dimensions: capacity, neck size, barrier properties

### 4. web-crawler-pipeline
**Location**: `.claude/skills/web-crawler-pipeline/`
**Purpose**: Web crawling automation with monitoring and restart
**Commands**: `crawl`, `monitor`, `restart`, `status`
**Triggers**: "crawl", "scrape", "web data"

---

## SKILL Development

### Creating a New SKILL

1. **Create directory structure**:
```bash
mkdir -p .claude/skills/my-skill
touch .claude/skills/my-skill/SKILL.md
touch .claude/skills/my-skill/skill.py
```

2. **Write SKILL.md** (Progressive Disclosure format):
```markdown
---
name: my-skill
description: Brief description
triggers:
  - "keyword1"
  - "keyword2"
---

# My Skill

## When to Activate
[Description of when this SKILL should be used]

## Commands
### command_name
[Description and usage]
```

3. **Write skill.py** (Executable wrapper):
```python
#!/usr/bin/env python3
"""My Skill - Description"""

def execute(command, params):
    """Execute skill command"""
    if command == 'my_command':
        # Call plugin or implement logic
        return {'success': True}

if __name__ == '__main__':
    # Test code
    result = execute('my_command', {})
    print(result)
```

4. **Register in __init__.py**:
```python
# .claude/skills/__init__.py
AVAILABLE_SKILLS = {
    'rag-pipeline': 'rag_pipeline',
    'manufacturing-expert': 'manufacturing_expert',
    'my-skill': 'my_skill'  # Add new skill
}
```

---

## SKILL vs Plugin

| Aspect | SKILL | Plugin |
|--------|-------|--------|
| **Purpose** | Claude Code interface | Business logic |
| **Location** | `.claude/skills/` | `plugins/` |
| **Contains** | Triggers, docs, wrapper | Logic, config, processing |
| **Used by** | Claude Code | SKILLs |
| **Format** | SKILL.md + skill.py | plugin.py + config/*.yaml |

---

## Related Documentation

- **Full SKILL details**: Read `.claude/skills/{skill-name}/SKILL.md`
- **Plugin architecture**: `/component plugins`
- **Workflow integration**: `/workflow document-processing`

---

**Last Updated**: 2025-11-03
