# RAG Enterprise - System Architecture

**Token-efficient hybrid documentation architecture with on-demand loading.**

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Request                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              SKILL (.claude/skills/)                    │
│  ┌─────────────────────────────────────────────────┐  │
│  │ • Triggers: Auto-activation keywords            │  │
│  │ • Commands: process, query, search, etc.        │  │
│  │ • Documentation: SKILL.md (progressive)         │  │
│  │ • Wrapper: skill.py (executable)                │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Plugin (plugins/)                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │ • Business Logic: plugin.py                     │  │
│  │ • Configuration: config/*.yaml                  │  │
│  │ • Domain Expertise: terminology, patterns       │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│           MCP Server (.mcp.json)                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │ • filesystem: File operations                   │  │
│  │ • qdrant: Vector database                       │  │
│  │ • chrome_devtools: Browser automation           │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                     Result                              │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
rag-enterprise/
├── 📄 Root (Auto-loaded: ~2,750 tokens)
│   ├── CLAUDE.md           ← Quick reference + trigger map
│   ├── QUICK_START.md      ← Getting started guide
│   ├── README.md           ← Project overview
│   ├── ARCHITECTURE.md     ← This file
│   └── USAGE_GUIDE.md      ← Slash command usage
│
├── 📚 workflows/ (On-demand: ~800-1,500 tokens each)
│   ├── README.md
│   ├── document-processing.md   ← Document ingestion
│   ├── rag-query.md            ← RAG query execution
│   ├── domain-expert.md        ← Domain expert integration
│   ├── vector-search.md        ← Vector search
│   └── web-crawling.md         ← Web crawling
│
├── 🧩 components/ (On-demand: ~600-1,000 tokens each)
│   ├── skills/
│   │   └── README.md           ← SKILL system overview
│   ├── plugins/
│   │   └── README.md -> ../../plugins/README.md
│   └── mcp-servers/
│       └── README.md           ← MCP configuration
│
├── 📖 guides/ (On-demand: ~800-1,200 tokens each)
│   ├── development.md          ← Development commands
│   ├── testing.md              ← Testing strategies
│   ├── session-protocol.md     ← Session rules
│   └── contributing.md         ← Contribution guide
│
├── ⚙️ .claude/
│   ├── commands/               ← Slash commands
│   │   ├── workflow.md         ← /workflow command
│   │   ├── component.md        ← /component command
│   │   └── guide.md            ← /guide command
│   └── skills/                 ← SKILL implementations
│       ├── rag-pipeline/
│       ├── manufacturing-expert/
│       ├── packaging-expert/
│       └── web-crawler-pipeline/
│
├── 🔌 plugins/                 ← Plugin business logic
│   ├── base_plugin.py
│   ├── manufacturing_expert/
│   │   ├── plugin.py
│   │   └── config/*.yaml
│   └── packaging_expert/
│       ├── plugin.py
│       └── config/*.yaml
│
└── 🔧 .mcp.json               ← MCP server config (3 servers)
```

---

## 🔄 Data Flow

### Document Processing Flow

```
1. User uploads PDF
   ↓
2. rag-pipeline SKILL (process command)
   ↓
3. filesystem MCP reads file
   ↓
4. Domain plugin enriches metadata
   - manufacturing_expert OR packaging_expert
   - Extract: doc_type, terminology, parameters
   ↓
5. Embed chunks (sentence-transformers)
   ↓
6. qdrant MCP stores vectors + metadata
   ↓
7. Return: {success: true, chunks_created: N}
```

### RAG Query Flow

```
1. User asks question
   ↓
2. rag-pipeline SKILL (query command)
   ↓
3. Embed question → query_vector
   ↓
4. qdrant MCP searches similar vectors
   - Apply filters (doc_type, domain, etc.)
   - Return top_k results
   ↓
5. (Optional) Rerank results
   ↓
6. Assemble context from retrieved chunks
   ↓
7. LLM generates answer from context
   ↓
8. Return: {answer, sources, metadata}
```

---

## 🎨 Component Details

### SKILLs (Interface Layer)

| Component | Location | Purpose |
|-----------|----------|---------|
| **rag-pipeline** | `.claude/skills/rag-pipeline/` | RAG orchestration |
| **manufacturing-expert** | `.claude/skills/manufacturing-expert/` | Manufacturing docs |
| **packaging-expert** | `.claude/skills/packaging-expert/` | Packaging docs |
| **web-crawler-pipeline** | `.claude/skills/web-crawler-pipeline/` | Web crawling |

### Plugins (Business Logic)

| Component | Location | Purpose |
|-----------|----------|---------|
| **base_plugin** | `plugins/base_plugin.py` | Abstract base class |
| **manufacturing_expert** | `plugins/manufacturing_expert/` | Manufacturing domain logic |
| **packaging_expert** | `plugins/packaging_expert/` | Packaging domain logic |

### MCP Servers (External Services)

| Component | Purpose | Token Cost |
|-----------|---------|------------|
| **filesystem** | File operations | ~150 tokens |
| **qdrant** | Vector database | ~200 tokens |
| **chrome_devtools** | Browser automation | ~150 tokens |
| **Total** | | **~500 tokens** |

---

## 💾 Token Efficiency

### Old Architecture
```
CLAUDE.md:        12KB (~3,000 tokens)  ← Always loaded
.mcp.json:        7 servers (~2,100 tokens)
────────────────────────────────────────
Total:            ~5,100 tokens per session
```

### New Architecture (Hybrid)
```
Root files:       ~11KB (~2,750 tokens)  ← Always loaded
  - CLAUDE.md     5KB (~1,300 tokens)
  - README.md     2KB (~500 tokens)
  - Others        4KB (~950 tokens)

.mcp.json:        3 servers (~500 tokens)

On-demand docs:   Load only when needed
  - workflows/    ~800-1,500 tokens each
  - components/   ~600-1,000 tokens each
  - guides/       ~800-1,200 tokens each
────────────────────────────────────────
Per session:      ~3,250 tokens (base)
                  + loaded docs (0-3,000)
Average:          ~3,500 tokens
Savings:          ~31% on average
```

### Efficiency by Scenario

| Scenario | Old | New | Savings |
|----------|-----|-----|---------|
| Quick Q&A | 5,100 | 3,250 | **36%** |
| Single workflow | 5,100 | 4,050 | **21%** |
| Development work | 5,100 | 5,250 | -3% |
| Average (weighted) | 5,100 | 3,500 | **31%** |

---

## 🚀 Activation Mechanisms

### 1. Slash Commands (Explicit)

```bash
/workflow document-processing
/component skills
/guide development
```

**Pros**: Precise, predictable, full control
**Cons**: User needs to know command names

### 2. Auto-Trigger (Implicit)

```
User: "How do I process a PDF?"
Claude: [Auto-loads workflows/document-processing.md]
```

**Triggers**:
- "process document" → document-processing workflow
- "RAG query" → rag-query workflow
- "SKILL development" → skills component

**Pros**: Natural, convenient
**Cons**: Depends on keyword matching

### 3. Direct Mention (Hybrid)

```
User: "Show me the document processing workflow"
Claude: [Reads workflows/document-processing.md]
```

**Pros**: Clear intent
**Cons**: User needs to know structure

---

## 🛡️ Fallback Strategy

Each slash command has built-in validation and fallback:

```
1. Parse command and parameters
   ↓
2. Check if file exists
   ↓
3. If exists:
   → Load file
   → Answer question
   ↓
4. If NOT exists:
   → Show available options
   → Provide usage examples
   → Ask user to choose
```

**Example**:
```
User: /workflow nonexistent

Claude: ❌ Workflow 'nonexistent' not found.

Available workflows:
1. document-processing
2. rag-query
3. domain-expert
4. vector-search
5. web-crawling

Usage: /workflow [name]
```

---

## 📊 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Token efficiency | 75% reduction (MCP) | ✅ 75% (500 vs 2,100) |
| Token efficiency | 30% reduction (docs) | ✅ 31% (3,500 vs 5,100) |
| API response | < 200ms | 🔄 Testing |
| RAG answer | < 2s | 🔄 Testing |
| Doc processing | < 5s (10 pages) | 🔄 Testing |
| Vector search | < 100ms (top-10) | 🔄 Testing |

---

## 🔐 Security Considerations

- API keys in `.env` only
- `.env` in `.gitignore`
- Input validation (Pydantic)
- Rate limiting (TODO)
- SQL injection protection (TODO)
- CORS configuration (TODO)

---

## 📚 Related Documentation

- **Usage Guide**: `USAGE_GUIDE.md` - How to use slash commands
- **Quick Start**: `QUICK_START.md` - Getting started
- **Development**: `/guide development` - Development commands
- **Workflows**: `/workflow [name]` - Detailed workflows

---

**Last Updated**: 2025-11-03
**Architecture Version**: 4.0 (Hybrid Token-Efficient)
