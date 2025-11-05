# Workflow Documentation Loader

**Purpose**: Load specific workflow documentation on demand with fallback validation.

## Execution Protocol

When this command is invoked, follow this EXACT sequence:

### Step 1: Validate Request
```
User input: /workflow [workflow-name] [optional: specific question]
Example: /workflow document-processing
Example: /workflow rag-query How do I add filters?
```

### Step 2: Check Available Workflows
Available workflows (check existence before loading):
- `document-processing` → workflows/document-processing.md
- `rag-query` → workflows/rag-query.md
- `domain-expert` → workflows/domain-expert.md
- `vector-search` → workflows/vector-search.md
- `web-crawling` → workflows/web-crawling.md
- `ARCHITECTURE` → workflows/ARCHITECTURE.md
- `USAGE_GUIDE` → workflows/USAGE_GUIDE.md

### Step 3: Load with Validation

```
1. Check if file exists using Read tool
2. If exists:
   - Load the workflow documentation
   - Answer user's question using loaded context
3. If NOT exists:
   - Show available workflows list
   - Ask user to choose from available options
```

### Step 4: Fallback Response Template

If workflow not found, respond EXACTLY like this:

```
❌ Workflow '[workflow-name]' not found.

Available workflows:
1. document-processing - Document ingestion and processing
2. rag-query - RAG query and answer generation
3. domain-expert - Domain expert integration
4. vector-search - Vector search operations
5. web-crawling - Web crawling workflows
6. ARCHITECTURE - System architecture details
7. USAGE_GUIDE - Complete usage guide

Usage: /workflow [workflow-name]
Example: /workflow document-processing
Example: /workflow ARCHITECTURE
```

## Error Handling

- Invalid syntax → Show usage help
- Missing workflow name → Show available workflows list
- File not found → Use fallback response template above
- Permission error → Report to user and suggest checking file permissions

## Success Response

After loading workflow, respond:
```
✅ Loaded: [Workflow Name]
[Answer user's question based on loaded documentation]

💡 Tip: You can also explore related docs:
- /component [skills|plugins|mcp]
- /guide [development|testing|deployment]
```
