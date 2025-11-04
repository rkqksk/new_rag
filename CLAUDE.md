# RAG Enterprise - Quick Reference

**Production-grade RAG with SKILL-based architecture, multi-model support, vector search.**

---

## 🎯 Slash Commands

```bash
/workflow document-processing  # Document ingestion
/workflow rag-query           # RAG queries
/workflow domain-expert       # Domain experts
/component skills             # SKILL system
/component plugins            # Plugin architecture
/component mcp                # MCP servers
/guide development            # Dev commands
```

**Full usage**: `/workflow USAGE_GUIDE`

---

## 🏗️ Architecture

```
User → SKILL (.claude/skills/) → Plugin (plugins/) → MCP (.mcp.json) → Result
```

| Layer | Location | Purpose |
|-------|----------|---------|
| SKILL | `.claude/skills/` | Interface, triggers |
| Plugin | `plugins/` | Business logic |
| MCP | `.mcp.json` | External services |

**Details**: `/workflow ARCHITECTURE`

---

## 📚 Documentation

### Workflows (End-to-end flows)
- `document-processing` - Document ingestion pipeline
- `rag-query` - RAG query execution
- `domain-expert` - Domain expert integration
- `ARCHITECTURE` - System architecture
- `USAGE_GUIDE` - Complete usage guide

### Components (Details)
- `skills` - SKILL system
- `plugins` - Plugin architecture
- `mcp` - MCP configuration

### Guides (Development)
- `development` - Commands, scenarios
- `testing` - Test strategies
- `session-protocol` - Session rules

---

## 🎨 Active SKILLs

| Skill | Commands | Triggers |
|-------|----------|----------|
| rag-pipeline | process, query, search | "process document", "RAG query" |
| manufacturing-expert | process, classify | "manufacturing", "SOP" |
| packaging-expert | process, classify | "packaging", "container" |
| web-crawler-pipeline | crawl, monitor | "crawl", "scrape" |

---

## 🚀 Quick Start

```python
# Process document
from .claude.skills.rag_pipeline import skill
skill.execute('process', {'file_path': 'doc.pdf'})

# RAG query
skill.execute('query', {'question': 'What are requirements?'})

# Vector search
skill.execute('search', {'query': '50ml bottle', 'top_k': 10})
```

---

## 🔄 Session Protocol

### Start
```bash
git status && git branch
```

### Changes
1. Classify: Feature/Bug/Config/Docs
2. TodoWrite if >2 steps
3. Update CHANGELOG.md after completion
4. Run tests

### End
- Todos resolved/documented
- Docs updated
- Background processes killed
- Git status clean

**Full protocol**: `/guide session-protocol`

---

## 🎨 Frontend

**Location**: `frontend/chat.html`
**Type**: Single-page application (SPA)
**Design**: White/minimal design (#f3f4f6 background)

### API Endpoints
```
http://localhost:8001/chat/create_session  # Create chat session
http://localhost:8001/chat/query          # Query with context
```

### Run Frontend
```bash
# Simple HTTP server
cd frontend && python3 -m http.server 8080

# Open in browser
open http://localhost:8080/chat.html
```

### Features
- 💬 Context-aware chat interface
- 📦 Product recommendations panel
- 🔍 Smart search with RAG integration
- 📊 Session management

---

## 🔧 Common Commands

```bash
# Dev
python run_chat_server.py
pytest tests/ -v --cov=src

# Docker
docker-compose up -d

# SKILL test
python3 .claude/skills/rag-pipeline/skill.py

# Frontend
cd frontend && python3 -m http.server 8080
```

---

## 📊 Tech Stack

- FastAPI (Python 3.11+)
- Qdrant + PostgreSQL/pgvector
- Redis, Docker Compose
- pytest (80%+ coverage target)

---

## 📖 Resources

- **Architecture**: `/workflow ARCHITECTURE`
- **Usage Guide**: `/workflow USAGE_GUIDE`
- **Quick Start**: `docs/QUICK_START.md`
- **Project Info**: `README.md`

---

## 📁 Documentation Structure

### **docs/** - Current Project Documentation
- `docs/README.md` - Documentation index
- `docs/ARCHITECTURE.md` - System architecture
- `docs/QUICK_START.md` - Getting started guide
- `docs/DEPLOYMENT_STRATEGY.md` - Deployment guide
- `docs/TECHNOLOGY_STACK.md` - Tech stack details
- `docs/CHANGELOG.md` - Version history
- `docs/archive/` - Historical documentation (140+ files)

### **claudedocs/** - Development History
- Session logs, feature implementations, bug reports
- Development progress, planning documents
- Design decisions and architecture evolution
- **For developers/maintainers tracking project evolution**

### **mcp_servers/** - MCP Server Implementations
- `qdrant_server.py` - Vector DB MCP server (active)
- `rag_orchestrator.py` - RAG pipeline orchestrator (active)
- `note_keeper_server.py` - Session notes (active)
- Other optional MCP servers (claude_api, ollama, etc.)

---

**v3.1.0** | **2025-11-03** | **MIT**
