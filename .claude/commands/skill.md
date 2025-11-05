---
name: skill-creator
description: Guide for creating effective Agent Skills that extend Claude's capabilities with progressive disclosure architecture
---

# Skill Creator

This command helps you create high-quality Agent Skills following Anthropic's Agent Skills specification and best practices.

## What are Agent Skills?

Agent Skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks. They use progressive disclosure to load knowledge only when needed, optimizing token usage.

## Skill Structure

Every skill must contain a `SKILL.md` file with:

### Required YAML Frontmatter
```yaml
---
name: my-skill-name          # lowercase, hyphen-separated
description: Clear description of what the skill does and when to use it
---
```

### Optional Frontmatter Fields
- `license`: The license applied to the skill
- `allowed-tools`: List of pre-approved tools (Claude Code only)
- `metadata`: Map of additional properties

### Markdown Body
- Instructions Claude should follow
- Examples and use cases
- Guidelines and best practices
- Additional resources (loaded on demand)

## Progressive Disclosure Architecture

Skills use a three-tier architecture for token efficiency:

1. **Metadata** (Always loaded)
   - Name and description
   - Activation criteria

2. **Instructions** (Loaded when activated)
   - Core guidance and procedures
   - Key concepts and patterns

3. **Resources** (Loaded on demand)
   - Detailed examples
   - Templates and boilerplate
   - Extended documentation

## Best Practices

### Naming
- Use lowercase with hyphens: `async-python-patterns`
- Be specific and descriptive
- Match directory name to skill name

### Description
- Clear statement of purpose
- When Claude should activate the skill
- Key capabilities provided

### Content Organization
- Start with overview and key concepts
- Provide concrete examples
- Include troubleshooting guidance
- Reference related skills

### Token Efficiency
- Front-load critical information
- Use clear section headers
- Avoid redundant content
- Link to resources instead of embedding

## Example Skill Template

```markdown
---
name: example-skill
description: Brief description of what this skill does and when to use it
---

# Example Skill

## Overview
What this skill helps with and why it's useful.

## Key Concepts
Core ideas and patterns.

## Usage
How to apply this skill effectively.

## Examples
Concrete use cases and code samples.

## Guidelines
- Best practice 1
- Best practice 2
- Common pitfall to avoid

## Related Skills
- Link to complementary skills
```

## Skill Categories

Common skill types in RAG/Enterprise systems:

### Development Skills
- Language-specific patterns (Python, TypeScript, etc.)
- Framework expertise (FastAPI, React, etc.)
- Testing and debugging approaches

### Infrastructure Skills
- Cloud platform specifics (AWS, Azure, GCP)
- Container orchestration (Kubernetes, Docker)
- CI/CD pipeline patterns

### Architecture Skills
- System design patterns
- API design principles
- Database schema design

### Domain Skills
- RAG pipeline optimization
- Document processing patterns
- Vector search strategies

## Creating Your Skill

1. **Identify the Need**
   - What specialized knowledge is needed?
   - When should Claude activate this skill?
   - What existing skills could this complement?

2. **Design the Structure**
   - Outline key concepts
   - Identify essential vs. optional content
   - Plan progressive disclosure tiers

3. **Write Clear Instructions**
   - Use active voice
   - Provide concrete examples
   - Include decision criteria

4. **Test and Refine**
   - Verify activation conditions
   - Ensure instructions are clear
   - Optimize token usage

## Integration with RAG System

For this project's RAG enterprise system, consider:

- **Document Processing Skills**: OCR, PDF parsing, table extraction
- **Embedding Skills**: Model selection, chunking strategies, dimension reduction
- **Retrieval Skills**: Hybrid search, re-ranking, query understanding
- **LLM Skills**: Prompt engineering, citation generation, response formatting
- **Infrastructure Skills**: Qdrant operations, Redis caching, PostgreSQL queries

## Resources

- [Agent Skills Spec](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- [Creating Custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
