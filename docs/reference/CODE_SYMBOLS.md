# RAG Enterprise - Code Symbol Reference (Serena MCP)

**Version**: v10.0.0 | **Purpose**: Token-efficient code navigation using Serena MCP

> **Key Benefit**: Read Python code **symbolically** instead of loading entire files
>
> **Token Savings**: 70-80% reduction vs `Read` tool
>
> **Approach**: Use `get_symbols_overview` → `find_symbol` → Read only what you need

---

## 🎯 Quick Comparison

### ❌ Traditional Approach (High Token Cost)
```
Task: "Understand RAGQAService class"
Tool: Read("apps/api/services/rag_qa_service.py")  # 300 lines
Tokens: ~1200 tokens
```

### ✅ Serena Approach (Low Token Cost)
```
Task: "Understand RAGQAService class"
Tool 1: get_symbols_overview("apps/api/services/rag_qa_service.py")
  → Returns: [QARequest, QAResponse, RAGQAService]  # 20 tokens
Tool 2: find_symbol(name_path="RAGQAService", depth=1, include_body=false)
  → Returns: Class with method signatures  # 50 tokens
Tool 3: find_symbol(name_path="RAGQAService/query", include_body=true)
  → Returns: Only the query method  # 80 tokens
Total Tokens: ~150 tokens (87% savings!)
```

---

## 📚 Serena MCP Tools Overview

### Core Tools
| Tool | Purpose | Use When |
|------|---------|----------|
| `get_symbols_overview` | List top-level symbols (classes, functions) | First step: Understand file structure |
| `find_symbol` | Find specific symbol by name path | You know the class/function name |
| `find_referencing_symbols` | Find where symbol is used | Understanding dependencies |
| `search_for_pattern` | Regex search in code | You don't know exact symbol name |
| `replace_symbol_body` | Edit symbol body | Making code changes |

### Symbol Kinds (LSP)
- **5** = Class
- **6** = Method
- **12** = Function
- **13** = Variable
- **14** = Constant

---

## 🗂️ Code Symbol Map

### Core API (`apps/api/`)

#### Main Application
**File**: `apps/api/main.py` (270 lines)
**Symbols**: Use Serena instead of Read!

```python
# Traditional: Read entire file (270 lines)
Read("apps/api/main.py")

# Serena: Get overview first (20 lines)
get_symbols_overview("apps/api/main.py")
→ Returns: [app, liveness, readiness, startup_event, shutdown_event, ...]

# Then read specific symbols
find_symbol(name_path="startup_event", relative_path="apps/api/main.py", include_body=true)
→ Returns: Only startup_event function (~30 lines)
```

#### Routing System
**Directory**: `apps/api/core/routing/`

**ml_router.py** (446 lines) - **USE SERENA!**
```python
# Overview
get_symbols_overview("apps/api/core/routing/ml_router.py")
→ Returns: [MLRouter, ModelSelector, predict_endpoint, ...]

# Read specific class
find_symbol(name_path="MLRouter", depth=1, include_body=false)
→ Returns: MLRouter class with method signatures

# Read specific method
find_symbol(name_path="MLRouter/predict", include_body=true)
→ Returns: Only predict method
```

**llm_router.py** (352 lines) - **USE SERENA!**
```python
# Symbols: ClaudeModel, ComplexityScore, ComplexityAnalyzer, ClaudeRouter
get_symbols_overview("apps/api/core/routing/llm_router.py")

# Read ClaudeRouter class
find_symbol(name_path="ClaudeRouter", depth=1)
```

**intent_router.py** (322 lines) - **USE SERENA!**
**integrated_router.py** (270 lines) - **USE SERENA!**

#### Services (`apps/api/services/`)

**Key Files** (Always use Serena for these):
- `rag_qa_service.py` - RAGQAService class
- `search_service.py` - SearchService class
- `analytics_service.py` - AnalyticsService class
- `personalization_service.py` - PersonalizationService class
- `multi_agent_system.py` - MultiAgentSystem class
- `hybrid_search.py` - HybridSearchService class

**Example Workflow**:
```python
# 1. Overview
get_symbols_overview("apps/api/services/rag_qa_service.py")
→ [logger, QARequest, QAResponse, RAGQAService]

# 2. Class structure
find_symbol(
  name_path="RAGQAService",
  relative_path="apps/api/services/rag_qa_service.py",
  depth=1,
  include_body=false
)
→ Returns: All methods of RAGQAService

# 3. Specific method
find_symbol(
  name_path="RAGQAService/query",
  relative_path="apps/api/services/rag_qa_service.py",
  include_body=true
)
→ Returns: Only the query method implementation
```

#### RAG Consultation (`apps/api/rag_consultation/`)

**Directory Structure**:
```
rag_consultation/
├── classification/
│   ├── query_classifier.py    - QueryClassifier
│   ├── intent_detector.py     - IntentDetector
│   ├── language_detector.py   - LanguageDetector
│   └── tone_analyzer.py       - ToneAnalyzer
├── generation/
│   ├── response_generator.py  - ResponseGenerator
│   ├── prompt_builder.py      - PromptBuilder
│   └── template_system.py     - TemplateSystem
├── retrieval/
│   └── query_expander.py      - QueryExpander
└── context/
    ├── conversation_manager.py - ConversationManager
    └── context_store.py        - ContextStore
```

**Example**: ResponseGenerator
```python
# Overview (saves 90% tokens vs Read)
get_symbols_overview("apps/api/rag_consultation/generation/response_generator.py")
→ [logger, ResponseGenerator]

# Class details
find_symbol(
  name_path="ResponseGenerator",
  relative_path="apps/api/rag_consultation/generation/response_generator.py",
  depth=1
)
```

#### Repositories (`apps/api/repositories/`)

**Files**:
- `postgres_repository.py` - PostgresRepository
- `qdrant_repository.py` - QdrantRepository
- `redis_repository.py` - RedisRepository

#### Realtime (`apps/api/realtime/`)

**Files**:
- `socketio_server.py` - RealtimeServer
- `postgres_notify.py` - PostgresNotifier
- `redis_pubsub.py` - RedisPubSub

---

## 💡 Best Practices

### 1. Always Start with Overview
```python
# ❌ BAD: Reading entire file
Read("apps/api/services/rag_qa_service.py")

# ✅ GOOD: Get overview first
get_symbols_overview("apps/api/services/rag_qa_service.py")
```

### 2. Use `depth` Parameter
```python
# Get class with all method signatures (no bodies)
find_symbol(
  name_path="RAGQAService",
  depth=1,
  include_body=false  # Only signatures, not implementations
)

# Then read only the method you need
find_symbol(
  name_path="RAGQAService/query",
  include_body=true
)
```

### 3. Filter by Symbol Kind
```python
# Only classes (kind=5)
find_symbol(
  name_path="*",
  include_kinds=[5],  # Classes only
  relative_path="apps/api/services/"
)

# Only functions (kind=12)
find_symbol(
  name_path="*",
  include_kinds=[12],  # Functions only
)
```

### 4. Use Pattern Search When Name Unknown
```python
# Don't know exact name? Use pattern search first
search_for_pattern(
  substring_pattern="class.*Router",
  relative_path="apps/api/core/routing/",
  restrict_search_to_code_files=true
)

# Then use find_symbol with discovered name
find_symbol(name_path="ClaudeRouter", ...)
```

### 5. Find References
```python
# Who uses this class/function?
find_referencing_symbols(
  name_path="RAGQAService",
  relative_path="apps/api/services/rag_qa_service.py"
)
```

---

## 🎓 Common Workflows

### Workflow 1: Understand New Service
```python
# Step 1: Overview
get_symbols_overview("apps/api/services/analytics_service.py")

# Step 2: Class structure
find_symbol(name_path="AnalyticsService", depth=1, include_body=false)

# Step 3: Read specific methods
find_symbol(name_path="AnalyticsService/track_event", include_body=true)
find_symbol(name_path="AnalyticsService/get_metrics", include_body=true)

# Total: ~200 tokens vs 1000+ tokens with Read
```

### Workflow 2: Debug Issue in Router
```python
# Step 1: Overview to find relevant classes
get_symbols_overview("apps/api/core/routing/llm_router.py")

# Step 2: Read the problematic class
find_symbol(name_path="ClaudeRouter", depth=1)

# Step 3: Find who uses it
find_referencing_symbols(
  name_path="ClaudeRouter",
  relative_path="apps/api/core/routing/llm_router.py"
)

# Step 4: Read only the broken method
find_symbol(name_path="ClaudeRouter/route_query", include_body=true)
```

### Workflow 3: Refactor Code
```python
# Step 1: Find all references
find_referencing_symbols(name_path="old_function", ...)

# Step 2: Replace symbol body
replace_symbol_body(
  name_path="old_function",
  relative_path="...",
  body="new implementation"
)

# Step 3: Insert new symbol
insert_after_symbol(
  name_path="old_function",
  relative_path="...",
  body="def new_function(): ..."
)
```

---

## 📊 Token Savings Examples

### Example 1: Reading Large Router
| Approach | Tool | Tokens |
|----------|------|--------|
| ❌ Traditional | `Read("apps/api/core/routing/ml_router.py")` | ~1800 |
| ✅ Serena (Overview) | `get_symbols_overview(...)` | ~50 |
| ✅ Serena (Class only) | `find_symbol("MLRouter", depth=1)` | ~200 |
| ✅ Serena (Method only) | `find_symbol("MLRouter/predict")` | ~100 |
| **Savings** | | **89-94%** |

### Example 2: Understanding Service
| Approach | Tool | Tokens |
|----------|------|--------|
| ❌ Traditional | `Read("apps/api/services/rag_qa_service.py")` | ~1200 |
| ✅ Serena | `get_symbols_overview + find_symbol` | ~150 |
| **Savings** | | **87%** |

### Example 3: Finding Usage
| Approach | Tool | Tokens |
|----------|------|--------|
| ❌ Traditional | `Grep("RAGQAService") + Read 10 files` | ~5000 |
| ✅ Serena | `find_referencing_symbols(...)` | ~300 |
| **Savings** | | **94%** |

---

## 🔗 Integration with Existing Symbol System

### Document Symbols (SYMBOLS.md)
For **documentation navigation** (markdown files):
```
§rag.core → docs/RAG_ACTIVATION_STRATEGY.md
§saas.auth → docs/SAAS_ARCHITECTURE.md:50-200
```

### Code Symbols (This Guide)
For **code navigation** (Python files):
```python
get_symbols_overview("apps/api/...")
find_symbol(name_path="ClassName", ...)
```

### Combined Approach
```
User: "Explain RAG pipeline"

1. Read docs: §rag.pipeline (SYMBOLS.md)
   → docs/RAG_ACTIVATION_STRATEGY.md:50-200

2. Read code: Serena (CODE_SYMBOLS.md)
   → get_symbols_overview("apps/api/services/rag_qa_service.py")
   → find_symbol("RAGQAService/query")

Total: ~400 tokens vs 2000+ tokens (80% savings)
```

---

## 🚀 Quick Reference

### Most Common Commands
```python
# 1. Start here (always)
get_symbols_overview("path/to/file.py")

# 2. Get class structure
find_symbol(name_path="ClassName", depth=1, include_body=false)

# 3. Read specific method
find_symbol(name_path="ClassName/method_name", include_body=true)

# 4. Find who uses it
find_referencing_symbols(name_path="ClassName", relative_path="path/to/file.py")

# 5. Search by pattern (if name unknown)
search_for_pattern(substring_pattern="class.*Service", relative_path="apps/api/services/")
```

### Key Files to Always Use Serena
1. **Routers** (300-450 lines each):
   - `apps/api/core/routing/ml_router.py`
   - `apps/api/core/routing/llm_router.py`
   - `apps/api/core/routing/intent_router.py`
   - `apps/api/core/routing/integrated_router.py`

2. **Services** (200-400 lines each):
   - All files in `apps/api/services/`
   - All files in `apps/api/rag_consultation/`

3. **Main App** (270 lines):
   - `apps/api/main.py`

4. **Large Components**:
   - Any file >200 lines
   - Any file with multiple classes

---

## 📈 Impact Summary

**Before Serena** (Traditional `Read` tool):
- Average file: 300 lines = ~1200 tokens
- Large file: 450 lines = ~1800 tokens
- 10 files scanned: ~15,000 tokens

**After Serena** (Symbolic reading):
- Overview: ~50 tokens
- Class structure: ~200 tokens
- Specific method: ~100 tokens
- 10 files scanned: ~3,000 tokens

**Total Savings**: 80% fewer tokens = 5x more efficient!

---

**Version**: v10.0.0
**Status**: Production Ready
**Tool**: Serena MCP
**Savings**: 70-80% token reduction
**Usage**: Always prefer Serena for Python code reading
