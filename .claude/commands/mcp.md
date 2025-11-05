---
name: mcp-server
description: Guide for creating high-quality Model Context Protocol (MCP) servers to integrate external APIs and services with Claude
---

# MCP Server Development

Create robust MCP (Model Context Protocol) servers to extend Claude's capabilities by integrating with external APIs, databases, and services.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that enables secure, controlled connections between AI applications and external data sources. MCP servers expose tools, resources, and prompts that Claude can use to interact with external systems.

## Core Concepts

### Tools
Functions that Claude can call to perform actions:
- Query databases
- Make API calls
- Process files
- Execute commands

### Resources
Data sources that Claude can read:
- Files and documents
- Database records
- API responses
- Real-time data streams

### Prompts
Pre-configured prompt templates:
- Common workflows
- Standardized queries
- Best practices

## MCP Server Structure

```
mcp-server/
├── src/
│   ├── index.ts          # Main server entry point
│   ├── tools/            # Tool implementations
│   ├── resources/        # Resource handlers
│   └── prompts/          # Prompt templates
├── package.json
├── tsconfig.json
└── README.md
```

## Basic Server Template

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Create server instance
const server = new Server(
  {
    name: "my-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);

// Register tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "example_tool",
      description: "Description of what this tool does",
      inputSchema: {
        type: "object",
        properties: {
          param1: {
            type: "string",
            description: "Description of parameter",
          },
        },
        required: ["param1"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "example_tool") {
    // Tool implementation
    return {
      content: [
        {
          type: "text",
          text: "Tool response",
        },
      ],
    };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running on stdio");
}

main();
```

## Tool Implementation Best Practices

### 1. Clear Naming
```typescript
{
  name: "search_documents",  // Clear, action-oriented
  description: "Search through uploaded documents using semantic similarity",
  // vs unclear: "doc_search" or "find_stuff"
}
```

### 2. Detailed Input Schema
```typescript
inputSchema: {
  type: "object",
  properties: {
    query: {
      type: "string",
      description: "Natural language search query",
      minLength: 1,
      maxLength: 500
    },
    limit: {
      type: "number",
      description: "Maximum number of results (default: 10)",
      minimum: 1,
      maximum: 100,
      default: 10
    },
    filters: {
      type: "object",
      description: "Optional metadata filters",
      properties: {
        date_range: {
          type: "object",
          properties: {
            start: { type: "string", format: "date" },
            end: { type: "string", format: "date" }
          }
        }
      }
    }
  },
  required: ["query"]
}
```

### 3. Structured Responses
```typescript
return {
  content: [
    {
      type: "text",
      text: JSON.stringify({
        results: [
          {
            id: "doc_123",
            title: "Document Title",
            relevance_score: 0.95,
            excerpt: "Relevant text excerpt...",
            metadata: {
              date: "2025-01-11",
              type: "invoice"
            }
          }
        ],
        total_found: 42,
        query_time_ms: 150
      }, null, 2)
    }
  ],
  isError: false
};
```

### 4. Error Handling
```typescript
try {
  // Tool logic
  return {
    content: [{ type: "text", text: result }],
    isError: false
  };
} catch (error) {
  return {
    content: [{
      type: "text",
      text: `Error: ${error.message}\nStack: ${error.stack}`
    }],
    isError: true
  };
}
```

## RAG Enterprise System Integration

### Document Search Tool
```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "search_rag_documents") {
    const { query, limit = 10, filters = {} } = request.params.arguments;
    
    // Connect to Qdrant
    const qdrantClient = new QdrantClient({ url: QDRANT_URL });
    
    // Generate embedding
    const embedding = await generateEmbedding(query);
    
    // Search
    const results = await qdrantClient.search("documents", {
      vector: embedding,
      limit: limit,
      filter: buildQdrantFilter(filters)
    });
    
    return {
      content: [{
        type: "text",
        text: JSON.stringify(results, null, 2)
      }]
    };
  }
});
```

### Document Upload Tool
```typescript
{
  name: "upload_document",
  description: "Upload and process a document for RAG indexing",
  inputSchema: {
    type: "object",
    properties: {
      file_path: {
        type: "string",
        description: "Path to the document file"
      },
      document_type: {
        type: "string",
        enum: ["invoice", "quote", "msds", "drawing", "defect_photo"],
        description: "Type of document being uploaded"
      },
      metadata: {
        type: "object",
        description: "Additional metadata tags"
      }
    },
    required: ["file_path", "document_type"]
  }
}
```

### Crawler Control Tool
```typescript
{
  name: "trigger_crawl",
  description: "Start a web crawling job for specific sources",
  inputSchema: {
    type: "object",
    properties: {
      source_url: {
        type: "string",
        format: "uri",
        description: "URL to crawl"
      },
      crawl_depth: {
        type: "number",
        minimum: 1,
        maximum: 5,
        default: 2
      },
      follow_links: {
        type: "boolean",
        default: true
      }
    },
    required: ["source_url"]
  }
}
```

## Resource Implementation

### Expose Configuration
```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: "config://system/settings",
      name: "System Configuration",
      description: "Current RAG system settings",
      mimeType: "application/json"
    }
  ]
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri === "config://system/settings") {
    const config = await loadSystemConfig();
    return {
      contents: [{
        uri: request.params.uri,
        mimeType: "application/json",
        text: JSON.stringify(config, null, 2)
      }]
    };
  }
});
```

## Prompt Templates

```typescript
server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: [
    {
      name: "analyze_invoice",
      description: "Extract key information from an invoice",
      arguments: [
        {
          name: "invoice_id",
          description: "ID of the invoice to analyze",
          required: true
        }
      ]
    }
  ]
}));

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  if (request.params.name === "analyze_invoice") {
    const invoiceId = request.params.arguments?.invoice_id;
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Analyze invoice ${invoiceId} and extract:
1. Supplier information
2. Line items with quantities and prices
3. Total amounts (subtotal, tax, grand total)
4. Payment terms
5. Any discrepancies or anomalies

Format the response as structured JSON.`
          }
        }
      ]
    };
  }
});
```

## Testing MCP Servers

### Unit Tests
```typescript
import { describe, test, expect } from 'vitest';

describe('MCP Server Tools', () => {
  test('search_documents returns valid results', async () => {
    const result = await callTool('search_documents', {
      query: 'test query',
      limit: 5
    });
    
    expect(result.isError).toBe(false);
    expect(result.content[0].type).toBe('text');
    
    const data = JSON.parse(result.content[0].text);
    expect(data.results).toBeInstanceOf(Array);
    expect(data.results.length).toBeLessThanOrEqual(5);
  });
});
```

### Integration Tests
```typescript
describe('RAG Integration', () => {
  test('document upload and search workflow', async () => {
    // Upload document
    const uploadResult = await callTool('upload_document', {
      file_path: './test/fixtures/sample.pdf',
      document_type: 'invoice'
    });
    expect(uploadResult.isError).toBe(false);
    
    // Wait for indexing
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Search for document
    const searchResult = await callTool('search_documents', {
      query: 'sample invoice',
      limit: 10
    });
    
    const data = JSON.parse(searchResult.content[0].text);
    expect(data.results.length).toBeGreaterThan(0);
  });
});
```

## Security Considerations

### Input Validation
```typescript
function validateInput(params: any, schema: object): void {
  // Use JSON Schema validation
  const ajv = new Ajv();
  const validate = ajv.compile(schema);
  
  if (!validate(params)) {
    throw new Error(`Invalid input: ${JSON.stringify(validate.errors)}`);
  }
}
```

### Rate Limiting
```typescript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100, // 100 requests per minute
  message: 'Too many requests'
});
```

### Authentication
```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Verify authentication token
  const token = request.params._meta?.authToken;
  if (!await verifyToken(token)) {
    return {
      content: [{ type: "text", text: "Unauthorized" }],
      isError: true
    };
  }
  
  // Process request
});
```

## Deployment

### Configuration
```json
{
  "mcpServers": {
    "rag-enterprise": {
      "command": "node",
      "args": ["dist/index.js"],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "REDIS_URL": "redis://localhost:6379",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

### Monitoring
```typescript
import { Logger } from 'winston';

const logger = new Logger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// Log tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  logger.info('Tool call', {
    tool: request.params.name,
    arguments: request.params.arguments,
    timestamp: new Date().toISOString()
  });
  
  // Handle request
});
```

## Best Practices

1. **Design Tools for Composability**: Tools should be atomic and combinable
2. **Provide Clear Descriptions**: Help Claude understand when to use each tool
3. **Use Structured Data**: Return JSON for complex data
4. **Handle Errors Gracefully**: Always catch and report errors clearly
5. **Implement Timeouts**: Prevent long-running operations
6. **Log Everything**: Track usage and debug issues
7. **Version Your API**: Support backward compatibility
8. **Document Thoroughly**: Include examples and edge cases

## Resources

- **MCP Documentation**: https://modelcontextprotocol.io/
- **MCP TypeScript SDK**: https://github.com/modelcontextprotocol/typescript-sdk
- **Example Servers**: https://github.com/modelcontextprotocol/servers
- **Claude Code MCP Guide**: https://docs.claude.com/en/docs/claude-code/mcp

## Related Skills

- `async-python-patterns`: Async server implementation
- `api-design`: RESTful API design principles
- `security-patterns`: Authentication and authorization
