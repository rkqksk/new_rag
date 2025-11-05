# Component Documentation Loader

**Purpose**: Load specific component documentation (SKILLs, Plugins, MCP servers) with validation.

## Execution Protocol

### Step 1: Validate Request
```
User input: /component [component-type] [optional: specific component name]
Example: /component skills
Example: /component plugins manufacturing-expert
Example: /component mcp qdrant
```

### Step 2: Check Available Components

**Component Types**:
- `skills` → components/skills/README.md
  - Sub-components: rag-pipeline, manufacturing-expert, packaging-expert, web-crawler-pipeline
- `plugins` → components/plugins/README.md
  - Sub-components: manufacturing-expert, packaging-expert
- `mcp` or `mcp-servers` → components/mcp-servers/README.md
  - Sub-components: filesystem, qdrant, chrome-devtools

### Step 3: Load with Validation

```
1. Parse component type and optional name
2. Build file path based on input
3. Check if file exists using Read tool
4. If exists:
   - Load the component documentation
   - Answer user's question using loaded context
5. If NOT exists:
   - Show available components for that type
   - Ask user to choose from available options
```

### Step 4: Fallback Response Template

If component not found:

```
❌ Component '[component-type]' or '[component-name]' not found.

Available component types:
1. skills - SKILL system and individual SKILLs
   - rag-pipeline
   - manufacturing-expert
   - packaging-expert
   - web-crawler-pipeline

2. plugins - Plugin architecture and domain plugins
   - manufacturing-expert
   - packaging-expert

3. mcp - MCP server configurations
   - filesystem
   - qdrant
   - chrome-devtools

Usage: /component [type] [optional: name]
Examples:
  /component skills
  /component plugins manufacturing-expert
  /component mcp qdrant
```

## Nested Loading

If user specifies a sub-component:
```
/component skills rag-pipeline
→ Load components/skills/README.md
→ Then load .claude/skills/rag-pipeline/SKILL.md
→ Combine context to answer
```

## Success Response

```
✅ Loaded: [Component Type] > [Component Name]
[Answer user's question based on loaded documentation]

💡 Related:
- /workflow [name] - See how this component is used in workflows
- /guide development - Development guide for this component
```
