# Skills & Sub-Agents Reference

**Version**: 2.0.0
**Last Updated**: 2025-11-08
**Architecture**: Token-optimized with specialized sub-agents

---

## 📋 Overview

Complete reference for all skills and sub-agents in the RAG Enterprise system.

### Architecture Principles

1. **Token Efficiency**: Main project uses only 2 MCPs (filesystem + git)
2. **Parallel Processing**: 8 specialized sub-agents for concurrent tasks
3. **Skill-Agent Mapping**: Clear delegation of responsibilities
4. **100% Open-Source**: Zero SaaS dependencies

---

## 🤖 Sub-Agents (8 Total)

Specialized agents for parallel task execution and token optimization.

### 1. Crawling Agent

**Path**: `.claude/agents/crawling-agent`

**Purpose**: Web scraping, data acquisition, anti-bot evasion

**MCP Servers**:
- puppeteer (browser automation)
- fetch (HTTP requests)
- chrome-devtools (live debugging)
- tavily (AI search, optional - 1000 free/month)

**Skills**:
- web-scraping-expert
- web-crawler-pipeline
- advanced-data-acquisition

**Use Cases**:
- Scrape product data from websites
- Bypass anti-bot protections
- Manual 2FA login handling
- Real-time content extraction

**Example**:
```python
Task(
    subagent_type="crawling-agent",
    prompt="Scrape all product listings from example.com with pagination"
)
```

---

### 2. Frontend Agent

**Path**: `.claude/agents/frontend-agent`

**Purpose**: React/Tailwind development with UI components

**MCP Servers**:
- shadcn-ui (50+ React components)
- chrome-devtools (live debugging)

**Skills**:
- frontend-platform
- debugging-expert

**Use Cases**:
- Create React components
- Design responsive layouts
- Debug browser issues
- Implement UI/UX features

**Example**:
```python
Task(
    subagent_type="frontend-agent",
    prompt="Create a dashboard with product cards using shadcn/ui"
)
```

---

### 3. Data Agent

**Path**: `.claude/agents/data-agent`

**Purpose**: Database operations and data management

**MCP Servers**:
- postgres (production database)
- sqlite (local cache)

**Skills**:
- saas-platform
- data-collector

**Use Cases**:
- Execute SQL queries
- Data migration
- Schema management
- Analytics queries

**Example**:
```python
Task(
    subagent_type="data-agent",
    prompt="Analyze user activity patterns from PostgreSQL"
)
```

---

### 4. Code Review Agent

**Path**: `.claude/agents/code-review-agent`

**Purpose**: GitHub integration and code review

**MCP Servers**:
- github (API integration)

**Skills**:
- pcb-expert
- mold-expert

**Use Cases**:
- Review pull requests
- Create GitHub issues
- Manage repositories
- Code quality checks

**Example**:
```python
Task(
    subagent_type="code-review-agent",
    prompt="Review PR #123 and suggest improvements"
)
```

---

### 5. RAG Agent

**Path**: `.claude/agents/rag-agent`

**Purpose**: RAG system optimization and tuning

**MCP Servers**: None (pure Python tools)

**Skills**:
- rag-pipeline
- embedding-expert
- chunking-expert
- nexa-rag-optimizer
- multimodal-processor

**Use Cases**:
- Optimize embedding models
- Improve chunking strategies
- Tune search parameters
- Evaluate RAG performance

**Example**:
```python
Task(
    subagent_type="rag-agent",
    prompt="Optimize embedding model for Korean + English text"
)
```

---

### 6. Testing Agent

**Path**: `.claude/agents/testing-agent`

**Purpose**: Automated testing and quality assurance

**MCP Servers**: None (pytest framework)

**Skills**: None (framework-based)

**Use Cases**:
- Run unit tests
- Generate test cases
- Coverage analysis
- Integration testing

**Example**:
```python
Task(
    subagent_type="testing-agent",
    prompt="Run all tests and generate coverage report"
)
```

---

### 7. Deployment Agent

**Path**: `.claude/agents/deployment-agent`

**Purpose**: DevOps automation and deployment

**MCP Servers**: None (Docker/K8s CLI)

**Skills**: None (CLI-based)

**Use Cases**:
- Docker deployment
- Kubernetes orchestration
- CI/CD pipelines
- Infrastructure as code

**Example**:
```python
Task(
    subagent_type="deployment-agent",
    prompt="Deploy to production with zero downtime"
)
```

---

### 8. Monitoring Agent

**Path**: `.claude/agents/monitoring-agent`

**Purpose**: Performance monitoring and profiling

**MCP Servers**: None (Prometheus/Grafana)

**Skills**: None (monitoring stack)

**Use Cases**:
- Performance analysis
- Log aggregation
- Metrics collection
- Alert management

**Example**:
```python
Task(
    subagent_type="monitoring-agent",
    prompt="Analyze system performance and identify bottlenecks"
)
```

---

## 🎯 Skills (22 Total)

Domain-specific expertise modules.

### Core RAG Skills

| Skill | Status | Purpose | Sub-Agent |
|-------|--------|---------|-----------|
| **rag-pipeline** | ✅ | RAG orchestration | rag-agent |
| **embedding-expert** | ✅ | Embedding optimization | rag-agent |
| **chunking-expert** | ✅ | Advanced chunking | rag-agent |
| **nexa-rag-optimizer** | ✅ | Query optimization | rag-agent |
| **multimodal-processor** | ✅ | Multi-modal processing | rag-agent |

### Data Acquisition Skills

| Skill | Status | Purpose | Sub-Agent |
|-------|--------|---------|-----------|
| **web-scraping-expert** | ✅ | Advanced scraping | crawling-agent |
| **web-crawler-pipeline** | ✅ | Crawling automation | crawling-agent |
| **advanced-data-acquisition** | ✅ | Data collection | crawling-agent |
| **data-collector** | ✅ | Universal collector | data-agent |

### Platform Skills

| Skill | Status | Purpose | Sub-Agent |
|-------|--------|---------|-----------|
| **saas-platform** | ✅ | SaaS management | data-agent |
| **frontend-platform** | ✅ | React/Tailwind dev | frontend-agent |
| **debugging-expert** | ✅ | Browser debugging | frontend-agent |

### Domain Expert Skills

| Skill | Status | Purpose | Sub-Agent |
|-------|--------|---------|-----------|
| **manufacturing-expert** | ✅ | Manufacturing docs | None |
| **packaging-expert** | ✅ | Packaging docs | None |
| **pcb-expert** | ✅ | PCB design | code-review-agent |
| **mold-expert** | ✅ | Mold design | code-review-agent |
| **production-expert** | ✅ | Production engineering | None |
| **business-expert** | ✅ | Business analysis | None |
| **marketing-expert** | ✅ | Marketing content | None |
| **sales-expert** | ✅ | Sales processes | None |

### Utility Skills

| Skill | Status | Purpose | Sub-Agent |
|-------|--------|---------|-----------|
| **skill-creator** | ✅ | Create new skills | None |
| **architecture-optimizer** | ✅ | System optimization | None |

---

## 🗺️ Skill-to-Agent Mapping

### Crawling Agent Skills

**Skills**: web-scraping-expert, web-crawler-pipeline, advanced-data-acquisition

**Use When**:
- Need to scrape websites
- Handle JavaScript-heavy sites
- Bypass anti-bot measures
- Manage authentication

**Example**:
```bash
# Via crawling agent
Task(subagent_type="crawling-agent", prompt="Scrape products")

# Or directly via skill (delegates to agent)
/web-scraping-expert scrape --url=example.com
```

---

### Frontend Agent Skills

**Skills**: frontend-platform, debugging-expert

**Use When**:
- Building React components
- Styling with Tailwind
- Debugging browser issues
- Implementing UI features

**Example**:
```bash
# Via frontend agent
Task(subagent_type="frontend-agent", prompt="Create dashboard")

# Or directly via skill
/frontend-platform create-page --name=Dashboard
```

---

### Data Agent Skills

**Skills**: saas-platform, data-collector

**Use When**:
- Database operations
- Data migrations
- SQL queries
- Analytics

**Example**:
```bash
# Via data agent
Task(subagent_type="data-agent", prompt="Query user data")

# Or directly via skill
/saas-platform manage-tenants
```

---

### RAG Agent Skills

**Skills**: rag-pipeline, embedding-expert, chunking-expert, nexa-rag-optimizer, multimodal-processor

**Use When**:
- Optimizing RAG system
- Tuning embeddings
- Improving chunking
- Evaluating performance

**Example**:
```bash
# Via RAG agent
Task(subagent_type="rag-agent", prompt="Optimize embeddings")

# Or directly via skill
/rag-pipeline optimize-search
```

---

## 🔄 Parallel Processing Examples

### Sequential Tasks

```python
# Traditional approach (slow)
result1 = Task(subagent_type="testing-agent", prompt="Run tests")
result2 = Task(subagent_type="monitoring-agent", prompt="Check performance")
result3 = Task(subagent_type="deployment-agent", prompt="Deploy")
```

### Parallel Tasks

```python
# Parallel approach (fast) - Single message with multiple tasks
Task(subagent_type="testing-agent", prompt="Run all tests")
Task(subagent_type="monitoring-agent", prompt="Analyze performance")
Task(subagent_type="deployment-agent", prompt="Prepare deployment")
# All 3 execute in parallel!
```

---

## 📊 Token Usage Comparison

### Before Sub-Agents

**Main Context**:
- 10+ MCP servers loaded
- All skills in context
- ~50K tokens baseline
- Limited parallelization

### After Sub-Agents

**Main Context**:
- 2 MCP servers (filesystem + git)
- No skills loaded
- ~5K tokens baseline
- Full parallelization

**Savings**: 90% token reduction in main context

---

## 🛠️ Creating New Skills

Use the `skill-creator` skill:

```bash
/skill-creator create --name=my-new-skill --type=domain-expert
```

**Best Practices**:
1. Define clear purpose
2. Map to appropriate sub-agent
3. Document examples
4. Add progressive disclosure
5. Write tests

---

## 🧪 Creating New Sub-Agents

1. **Create directory**:
```bash
mkdir -p .claude/agents/my-agent
```

2. **Create agent.json**:
```json
{
  "name": "my-agent",
  "description": "Purpose of agent",
  "mcpServers": {...},
  "tools": [...],
  "config": {...}
}
```

3. **Create README.md**:
Document usage, examples, and configuration.

4. **Register in .claude/mcp.json**:
```json
"subAgents": {
  "my-agent": {
    "path": ".claude/agents/my-agent",
    "mcpServers": [...],
    "skills": [...]
  }
}
```

---

## 📚 Related Documentation

- **CLAUDE.md** - Quick reference guide
- **OPEN_SOURCE_ARCHITECTURE.md** - 100% open-source architecture
- **docs/guides/LOCAL_SETUP.md** - Local setup guide
- **.claude/mcp.json** - MCP configuration

---

## 🎯 Decision Matrix

**When to use Sub-Agent**:
- ✅ Task requires specialized MCP servers
- ✅ Need parallel execution
- ✅ Want to minimize token usage
- ✅ Complex multi-step workflow

**When to use Skill directly**:
- ✅ Simple task
- ✅ Already in context
- ✅ No MCP dependencies
- ✅ Quick one-off command

**When to use neither**:
- ✅ Built-in Claude Code functionality
- ✅ Simple file operations
- ✅ Basic git commands

---

## 📈 Statistics

**Sub-Agents**: 8
**Skills**: 22
**MCP Servers**:
- Main: 2 (filesystem, git)
- Sub-agents: 6 unique (puppeteer, fetch, shadcn-ui, chrome-devtools, postgres, github)

**Cost**: $0/month (100% open-source)

**Token Efficiency**: 90% reduction in baseline context

---

**Version**: 2.0.0
**Status**: ✅ Production-Ready
**Architecture**: Token-Optimized Sub-Agents
**Last Updated**: 2025-11-08
