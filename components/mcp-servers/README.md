# MCP Servers Documentation

**MCP (Model Context Protocol) Servers** provide external service integration for Claude Code.

---

## Overview

MCP servers handle:
- **File system operations** (filesystem)
- **Vector database** (qdrant)
- **Browser automation** (chrome_devtools)

---

## Active MCP Servers

### 1. filesystem
**Command**: `npx -y @modelcontextprotocol/server-filesystem`
**Purpose**: File system access for reading/writing project files
**Auto-enabled**: Yes

**Operations**:
- Read files
- Write files
- List directories
- Create directories
- Move/delete files

**Usage in Code**:
```python
# Read file
content = read_file('/path/to/file.txt')

# Write file
write_file('/path/to/file.txt', content)
```

---

### 2. qdrant
**Command**: `python3 -m mcp_servers.qdrant_server`
**Purpose**: Vector database operations for semantic search
**Location**: `mcp_servers/qdrant_server.py`

**Operations**:
- Create collections
- Upsert vectors
- Search vectors
- Filter by metadata
- Get collection info

**Usage in Code**:
```python
import qdrant_client

# Connect
client = qdrant_client.QdrantClient(url="http://localhost:6333")

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config={"size": 384, "distance": "Cosine"}
)

# Upsert vectors
client.upsert(
    collection_name="documents",
    points=[{
        "id": 1,
        "vector": [0.1, 0.2, ...],
        "payload": {"content": "...", "metadata": {...}}
    }]
)

# Search
results = client.search(
    collection_name="documents",
    query_vector=[0.1, 0.2, ...],
    limit=10,
    query_filter={
        "must": [
            {"key": "doc_type", "match": {"value": "sop"}}
        ]
    }
)
```

---

### 3. chrome_devtools
**Command**: `npx -y chrome-devtools-mcp@latest`
**Purpose**: Browser automation and debugging via Chrome DevTools Protocol

**Operations**:
- Navigate pages
- Click elements
- Fill forms
- Take screenshots
- Execute JavaScript
- Monitor network requests

**Usage**:
Used by web-crawler-pipeline SKILL for automated crawling.

---

## Configuration

MCP servers are configured in `.mcp.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/oypnus/Project/rag-enterprise"
      ]
    },
    "qdrant": {
      "command": "/path/to/python3",
      "args": ["-m", "mcp_servers.qdrant_server"]
    },
    "chrome_devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

---

## Token Efficiency

### Before (7 MCP servers, ~2100 tokens)
```
❌ claude_api
❌ ollama
❌ rag_orchestrator
❌ rag_document_processor
❌ rag_vector_search
❌ note_keeper
❌ + filesystem, chrome_devtools, qdrant
```

### After (3 MCP servers, ~500 tokens - 75% reduction)
```
✅ filesystem - File operations
✅ qdrant - Vector database
✅ chrome_devtools - Browser automation

Functionality moved to:
- claude_api → Direct API calls in SKILLs
- ollama → Direct ollama calls in SKILLs
- rag_orchestrator → rag-pipeline SKILL
- rag_document_processor → rag-pipeline SKILL
- rag_vector_search → rag-pipeline SKILL
- note_keeper → Direct file writing
```

---

## Adding New MCP Servers

### 1. Create MCP Server
```python
# mcp_servers/my_server.py
from mcp import Server

app = Server("my-server")

@app.tool()
async def my_operation(param: str):
    """My operation description"""
    # Implementation
    return {"result": "success"}

if __name__ == "__main__":
    app.run()
```

### 2. Update .mcp.json
```json
{
  "mcpServers": {
    "my-server": {
      "command": "python3",
      "args": ["-m", "mcp_servers.my_server"],
      "description": "My server description"
    }
  }
}
```

### 3. Restart Claude Code
MCP servers are loaded at startup.

---

## Troubleshooting

### Qdrant Connection Error
```bash
# Check if Qdrant is running
docker-compose ps

# Start Qdrant
docker-compose up -d qdrant

# Check logs
docker-compose logs qdrant
```

### MCP Server Not Loading
```bash
# Check .mcp.json syntax
cat .mcp.json | python3 -m json.tool

# Check server executable
python3 -m mcp_servers.qdrant_server --help
```

---

## Related Documentation

- **RAG workflows**: `/workflow rag-query`, `/workflow document-processing`
- **SKILL integration**: `/component skills`
- **Vector search**: `/workflow vector-search`

---

**Last Updated**: 2025-11-03
