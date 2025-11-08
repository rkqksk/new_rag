# MCP Servers - Model Context Protocol Integration

**Standardized tool exposure for LLM agents in Claude Code**

---

## Table of Contents

1. [Overview](#overview)
2. [What is MCP?](#what-is-mcp)
3. [Server Architecture](#server-architecture)
4. [Available MCP Servers](#available-mcp-servers)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Development](#development)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What are MCP Servers?

**Model Context Protocol (MCP)** servers provide standardized interfaces for Claude Code agents to interact with external tools, databases, and services. They enable safe, controlled access to system resources.

**Current MCP Servers in RAG Enterprise**:
- ✅ **filesystem**: File operations (read, write, search)
- ✅ **qdrant**: Vector database operations
- ✅ **ollama**: Local LLM inference
- ✅ **rag-orchestrator**: RAG pipeline orchestration
- ✅ **query-router**: Intelligent query routing
- ✅ **ocr-processor**: Document OCR processing

**Benefits**:
- 🔒 **Security**: Sandboxed execution with explicit permissions
- 🎯 **Standardization**: Consistent API across tools
- 📊 **Observability**: Built-in logging and monitoring
- 🔌 **Modularity**: Easy to add/remove capabilities
- 🚀 **Performance**: Optimized for token efficiency

---

## What is MCP?

### Architecture

```
Claude Code Agent
    ↓
[MCP Client]
    ↓ (JSON-RPC)
┌──────────────────────────────┐
│  MCP Server (stdio/HTTP)     │
├──────────────────────────────┤
│  Tools:                      │
│  - read_file                 │
│  - write_file                │
│  - search_files              │
│  - execute_command           │
└──────────────────────────────┘
    ↓
[Actual System Resources]
```

### Protocol

**Transport**: stdio (standard input/output) or HTTP
**Format**: JSON-RPC 2.0
**Operations**:
- `initialize`: Establish connection
- `tools/list`: Get available tools
- `tools/call`: Execute tool
- `resources/list`: Get available resources
- `resources/read`: Read resource content

**Example Flow**:
```json
// 1. Agent → MCP Server: List tools
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}

// 2. MCP Server → Agent: Available tools
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "read_file",
        "description": "Read file contents",
        "inputSchema": {
          "type": "object",
          "properties": {
            "path": {"type": "string"}
          },
          "required": ["path"]
        }
      }
    ]
  },
  "id": 1
}

// 3. Agent → MCP Server: Call tool
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {"path": "/path/to/file.txt"}
  },
  "id": 2
}

// 4. MCP Server → Agent: Result
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {"type": "text", "text": "File contents here..."}
    ]
  },
  "id": 2
}
```

---

## Server Architecture

### MCP Server Structure

```python
# Example MCP server structure
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Create server
server = Server("my-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Return available tools"""
    return [
        types.Tool(
            name="my_tool",
            description="Does something useful",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent]:
    """Execute tool"""
    if name == "my_tool":
        result = do_something(arguments["param1"])
        return [types.TextContent(type="text", text=result)]
    else:
        raise ValueError(f"Unknown tool: {name}")

# Run server
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-mcp-server",
                server_version="1.0.0"
            )
        )
```

---

## Available MCP Servers

### 1. Filesystem MCP (`mcp__filesystem`)

**Purpose**: Safe file operations within project directory

**Tools**:
- `read_file`: Read file contents
- `write_file`: Write/create files
- `list_directory`: List directory contents
- `search_files`: Search for files by pattern
- `get_file_info`: Get file metadata

**Configuration**:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${PWD}"],
      "env": {
        "PROJECT_ROOT": "${PWD}"
      }
    }
  }
}
```

**Example Usage**:
```python
# Agent automatically uses this via Claude Code
# No direct code needed - MCP handles it
```

---

### 2. Qdrant MCP (`mcp__qdrant`)

**Purpose**: Vector database operations

**Tools**:
- `search_vectors`: Semantic search
- `upsert_vectors`: Add/update vectors
- `delete_vectors`: Remove vectors
- `list_collections`: List all collections
- `get_collection_info`: Collection statistics

**Configuration**:
```json
{
  "mcpServers": {
    "qdrant": {
      "command": "python3",
      "args": ["-m", "src.mcp.qdrant_server"],
      "env": {
        "PYTHONPATH": "${PWD}",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333"
      }
    }
  }
}
```

**Implementation** (`src/mcp/qdrant_server.py`):
```python
from mcp.server import Server
from qdrant_client import QdrantClient
import mcp.types as types

server = Server("qdrant-mcp")
client = QdrantClient(host="localhost", port=6333)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_vectors",
            description="Search for similar vectors",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string"},
                    "query_vector": {
                        "type": "array",
                        "items": {"type": "number"}
                    },
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["collection", "query_vector"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "search_vectors":
        results = client.search(
            collection_name=arguments["collection"],
            query_vector=arguments["query_vector"],
            limit=arguments.get("limit", 5)
        )
        return [types.TextContent(
            type="text",
            text=str(results)
        )]
```

---

### 3. Ollama MCP (`mcp__ollama`)

**Purpose**: Local LLM inference

**Tools**:
- `generate_text`: Generate text completion
- `chat`: Chat with LLM
- `list_models`: List available models
- `pull_model`: Download model
- `embeddings`: Generate embeddings

**Configuration**:
```json
{
  "mcpServers": {
    "ollama": {
      "command": "python3",
      "args": ["-m", "src.mcp.ollama_server"],
      "env": {
        "PYTHONPATH": "${PWD}",
        "OLLAMA_BASE_URL": "http://localhost:11434"
      }
    }
  }
}
```

---

### 4. RAG Orchestrator MCP (`mcp__rag_orchestrator`)

**Purpose**: High-level RAG pipeline operations

**Tools**:
- `ingest_documents`: Process and index documents
- `semantic_search`: Perform RAG search
- `get_pipeline_status`: Check pipeline status
- `clear_index`: Clear vector index

**Configuration**:
```json
{
  "mcpServers": {
    "rag-orchestrator": {
      "command": "python3",
      "args": ["-m", "src.mcp.rag_orchestrator_server"],
      "env": {
        "PYTHONPATH": "${PWD}"
      }
    }
  }
}
```

**Implementation** (`src/mcp/rag_orchestrator_server.py`):
```python
from mcp.server import Server
from src.core.rag_pipeline import RAGPipeline
import mcp.types as types

server = Server("rag-orchestrator")
rag_pipeline = RAGPipeline()

@server.list_tools()
async def handle_list_tools():
    return [
        types.Tool(
            name="semantic_search",
            description="Perform semantic search on indexed documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                    "filters": {"type": "object"}
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "semantic_search":
        results = await rag_pipeline.search(
            query=arguments["query"],
            top_k=arguments.get("top_k", 5),
            filters=arguments.get("filters")
        )
        return [types.TextContent(
            type="text",
            text=str(results)
        )]
```

---

### 5. Query Router MCP (`mcp__query_router`)

**Purpose**: Intelligent query routing (NexaAI/Ollama)

**Tools**:
- `analyze_query`: Analyze query complexity
- `route_query`: Route to optimal engine
- `get_routing_stats`: View routing statistics

**Configuration**:
```json
{
  "mcpServers": {
    "query-router": {
      "command": "python3",
      "args": ["-m", "src.mcp.query_router_server"],
      "env": {
        "PYTHONPATH": "${PWD}"
      }
    }
  }
}
```

---

### 6. OCR Processor MCP (`mcp__ocr_processor`)

**Purpose**: Document OCR operations

**Tools**:
- `extract_text`: Extract text from image/PDF
- `process_document`: Full OCR pipeline
- `extract_entities`: Extract product entities

**Configuration**:
```json
{
  "mcpServers": {
    "ocr-processor": {
      "command": "python3",
      "args": ["-m", "src.mcp.ocr_processor_server"],
      "env": {
        "PYTHONPATH": "${PWD}",
        "OCR_USE_GPU": "true"
      }
    }
  }
}
```

---

## Configuration

### `.mcp.json` Structure

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python3",           // Executable
      "args": ["-m", "module.path"],  // Arguments
      "env": {                        // Environment variables
        "VAR_NAME": "value",
        "PROJECT_ROOT": "${PWD}"      // Use ${PWD} for dynamic paths
      },
      "disabled": false               // Optional: disable server
    }
  }
}
```

### Environment Variables

**Global**:
```bash
# MCP Configuration
MCP_DEBUG=false
MCP_LOG_LEVEL=INFO
MCP_TIMEOUT=60

# Server-specific
QDRANT_HOST=localhost
QDRANT_PORT=6333
OLLAMA_BASE_URL=http://localhost:11434
```

**Server-specific** (in `.mcp.json`):
```json
{
  "env": {
    "QDRANT_HOST": "localhost",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "PYTHONPATH": "${PWD}"
  }
}
```

---

## Usage Examples

### Example 1: Agent Using MCP Tools

**Scenario**: Agent needs to search vectors

```python
# Agent's perspective (automated by Claude Code)
# 1. List available tools
tools = await mcp_client.list_tools()
# → [{"name": "search_vectors", ...}, ...]

# 2. Call tool
result = await mcp_client.call_tool(
    "search_vectors",
    {
        "collection": "products_text",
        "query_vector": [0.1, 0.2, ...],
        "limit": 5
    }
)
# → Results from Qdrant
```

### Example 2: Restricting Agent Tools

**Problem**: Agent has access to too many tools

**Solution**: Explicit tool declaration in agent definition

```yaml
# .claude/agents/web-crawler.md
---
tools: Bash, Read, Write, Glob, Grep, TodoWrite, mcp__filesystem
---

# Only these tools are accessible to the agent
# MCP tools: mcp__filesystem (read/write files)
# Built-in tools: Bash, Read, Write, Glob, Grep, TodoWrite
```

### Example 3: Creating Custom MCP Server

```python
# custom_mcp_server.py

from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

server = Server("custom-server")

@server.list_tools()
async def handle_list_tools():
    return [
        types.Tool(
            name="custom_tool",
            description="My custom tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "custom_tool":
        result = f"Processed: {arguments['input']}"
        return [types.TextContent(type="text", text=result)]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            mcp.server.models.InitializationOptions(
                server_name="custom-server",
                server_version="1.0.0"
            )
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**Add to `.mcp.json`**:
```json
{
  "mcpServers": {
    "custom-server": {
      "command": "python3",
      "args": ["custom_mcp_server.py"]
    }
  }
}
```

---

## Development

### MCP Server Development Checklist

1. **Define Tools**:
   - Clear names and descriptions
   - JSON schema for inputs
   - Validation logic

2. **Implement Handlers**:
   - `list_tools()`: Return tool definitions
   - `call_tool()`: Execute tool logic
   - Error handling

3. **Testing**:
   - Unit tests for tool logic
   - Integration tests with MCP client
   - Error scenarios

4. **Documentation**:
   - Tool descriptions
   - Input/output examples
   - Configuration guide

### Testing MCP Servers

```bash
# Test MCP server manually
python3 -m src.mcp.qdrant_server

# Send JSON-RPC request
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python3 -m src.mcp.qdrant_server
```

**Expected Output**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "search_vectors",
        "description": "Search for similar vectors",
        "inputSchema": {...}
      }
    ]
  },
  "id": 1
}
```

---

## Troubleshooting

### Issue: MCP Server Not Found

**Error**: `MCP server 'xyz' not found`

**Solutions**:

1. **Check `.mcp.json`**:
```bash
cat .mcp.json | jq '.mcpServers'
```

2. **Verify command path**:
```bash
which python3
```

3. **Test manually**:
```bash
python3 -m src.mcp.xyz_server
```

### Issue: Tool Not Available

**Error**: `Tool 'abc' not found`

**Solutions**:

1. **List available tools**:
```bash
# Via MCP client
tools = await client.list_tools()
print([t.name for t in tools])
```

2. **Check agent restrictions**:
```yaml
# .claude/agents/my-agent.md
tools: Bash, Read, mcp__qdrant  # Only these tools accessible
```

### Issue: Environment Variables Not Set

**Error**: `KeyError: 'PYTHONPATH'`

**Solutions**:

1. **Use `${PWD}` in `.mcp.json`**:
```json
{
  "env": {
    "PYTHONPATH": "${PWD}"  // Not: "/absolute/path"
  }
}
```

2. **Set in shell**:
```bash
export PYTHONPATH=$(pwd)
```

---

## Best Practices

### 1. Tool Design

**Do**:
- ✅ Clear, descriptive tool names (`search_vectors` not `search`)
- ✅ Comprehensive JSON schemas with validation
- ✅ Return structured data (JSON, not plain text)
- ✅ Handle errors gracefully

**Don't**:
- ❌ Generic tool names
- ❌ Missing input validation
- ❌ Return raw exceptions

### 2. Security

**Do**:
- ✅ Validate all inputs
- ✅ Restrict file access to project directory
- ✅ Use environment variables for secrets
- ✅ Log all tool calls

**Don't**:
- ❌ Trust user input blindly
- ❌ Allow arbitrary file access
- ❌ Hardcode credentials

### 3. Performance

**Do**:
- ✅ Cache expensive operations
- ✅ Use async/await
- ✅ Limit result sizes
- ✅ Timeout long operations

**Don't**:
- ❌ Block on I/O
- ❌ Return unbounded results
- ❌ Run synchronous loops

---

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Code MCP Guide](https://docs.claude.com/docs/mcp)

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
