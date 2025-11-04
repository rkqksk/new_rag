# Symbol System - Document Reference Architecture

**Purpose**: Reduce token consumption by using symbolic references instead of loading full documents.

---

## 📋 Symbol Notation

```
§{category}.{document}.{section}
```

**Examples**:
- `§arch.core.layers` → Architecture > Core > Layers
- `§rag.phase2.vector` → RAG Activation > Phase 2 > VectorSearch
- `§ui.design.colors` → Frontend UI > Design > Colors

---

## 🗂️ Document Symbol Map

### §arch - Architecture (`docs/ARCHITECTURE.md`)

**Size**: 31KB | **Auto-load**: No | **Reference**: As needed

```
§arch.overview          → System overview
§arch.core.layers       → Core architecture layers (SKILL/Plugin/MCP)
§arch.core.skills       → SKILL system details
§arch.core.plugins      → Plugin architecture
§arch.core.mcp          → MCP server integration
§arch.data.flow         → Data flow and processing
§arch.api.endpoints     → API endpoint specs
§arch.ollama.models     → Ollama model management
§arch.frontend.ui       → Frontend UI/UX management
```

**Load when**: System design, architecture discussions, integration work

---

### §rag - RAG Activation Strategy (`docs/RAG_ACTIVATION_STRATEGY.md`)

**Size**: 18KB | **Auto-load**: No | **Reference**: For RAG work

```
§rag.status             → Current status (20% complete)
§rag.strategy           → Overall strategy
§rag.phase1             → Phase 1: Analysis
§rag.phase2             → Phase 2: Core module development
§rag.phase2.vector      → VectorSearch module specs
§rag.phase2.processor   → DocumentProcessor module specs
§rag.phase2.engine      → RAGEngine module specs
§rag.phase3             → Phase 3: Infrastructure setup
§rag.phase4             → Phase 4: Skill integration & testing
§rag.phase5             → Phase 5: Data embedding & deployment
§rag.resources          → Resource requirements (CPU, RAM, disk)
§rag.risks              → Risk assessment and mitigation
```

**Load when**: RAG development, embedding work, vector search implementation

---

### §ui - Frontend UI Policy (`docs/FRONTEND_UI_POLICY.md`)

**Size**: 13KB | **Auto-load**: No | **Reference**: For UI work

```
§ui.overview            → UI/UX policy overview
§ui.design.colors       → Color system (gray tones)
§ui.design.typography   → Typography specs
§ui.design.layout       → Layout constants
§ui.design.spacing      → Spacing system
§ui.components          → Component specifications
§ui.governance          → Change management policy
```

**Load when**: Frontend development, UI updates, design system changes

---

### §ollama - Ollama Model Policy (`docs/OLLAMA_MODEL_POLICY.md`)

**Size**: 6.5KB | **Auto-load**: No | **Reference**: For model management

```
§ollama.production      → Production models (qwen2.5:7b-instruct, nomic-embed-text)
§ollama.approval        → Model change approval process
§ollama.upgrade         → Upgrade procedures
§ollama.rollback        → Rollback procedures
§ollama.monitoring      → Performance monitoring
```

**Load when**: Model updates, performance issues, Ollama configuration

---

### §deploy - Deployment Strategy (`docs/DEPLOYMENT_STRATEGY.md`)

**Size**: 2.6KB | **Auto-load**: No | **Reference**: For deployment

```
§deploy.local           → Local development setup
§deploy.docker          → Docker deployment
§deploy.production      → Production deployment
§deploy.monitoring      → Monitoring and observability
```

**Load when**: Deployment planning, infrastructure setup

---

### §tech - Technology Stack (`docs/TECHNOLOGY_STACK.md`)

**Size**: 858 bytes | **Auto-load**: No | **Reference**: For tech choices

```
§tech.backend           → Backend stack (FastAPI, Python)
§tech.vector            → Vector database (Qdrant)
§tech.models            → ML models (Ollama, Sentence Transformers)
§tech.infra             → Infrastructure (Docker, Redis)
```

**Load when**: Technology decisions, dependency updates

---

### §changelog - Version History (`docs/CHANGELOG.md`)

**Size**: 872 bytes | **Auto-load**: No | **Reference**: For versioning

```
§changelog.v3.1.0       → Current version changes
§changelog.previous     → Previous versions
```

**Load when**: Release planning, version tracking

---

## 🔧 Usage Pattern

### Instead of Loading Full Documents

**Before** (High Token Cost):
```
Read docs/ARCHITECTURE.md (31KB)
Read docs/RAG_ACTIVATION_STRATEGY.md (18KB)
Read docs/FRONTEND_UI_POLICY.md (13KB)
Total: ~62KB = ~15,500 tokens
```

**After** (Low Token Cost):
```
Reference: §arch.core.layers, §rag.phase2.vector, §ui.design.colors
Total: ~100 tokens
```

**Token Savings**: ~99.4% reduction

---

### When to Load Full Documents

1. **Architecture changes**: Load `§arch.*`
2. **RAG development**: Load `§rag.*`
3. **UI redesign**: Load `§ui.*`
4. **Model updates**: Load `§ollama.*`
5. **Initial project onboarding**: Load all relevant symbols

---

## 📝 Symbol Reference Format

When referencing symbols in conversations:

```
User: "RAG 시스템 개발을 시작하고 싶어"
Assistant: "§rag.phase2 참조하여 Phase 2 작업을 진행하겠습니다"

User: "UI 색상을 변경하고 싶어"
Assistant: "§ui.design.colors 확인 후 변경하겠습니다"
```

---

## 🎯 Implementation

### In CLAUDE.md
Replace large sections with symbol references:

```markdown
## Architecture
See: §arch.core.layers for details

## RAG Activation
Current: §rag.status (20% complete)
Next: §rag.phase2.vector
```

### In Conversations
Load symbols on-demand:

```python
# Only when needed
if task == "rag_development":
    load_symbol("§rag.phase2")
elif task == "ui_update":
    load_symbol("§ui.design")
```

---

## 📊 Expected Token Savings

| Document | Original | Symbolized | Savings |
|----------|----------|------------|---------|
| CLAUDE.md | ~500 tokens | ~150 tokens | 70% |
| ARCHITECTURE.md | ~7,750 tokens | ~50 tokens | 99.4% |
| RAG_ACTIVATION_STRATEGY.md | ~4,500 tokens | ~50 tokens | 98.9% |
| FRONTEND_UI_POLICY.md | ~3,250 tokens | ~50 tokens | 98.5% |
| **Total** | **~16,000 tokens** | **~300 tokens** | **98.1%** |

**Per Session Savings**: ~15,700 tokens
**100 Sessions**: ~1.57M tokens saved

---

## 🔄 Maintenance

### Adding New Documents
1. Create symbol map in this document
2. Define symbol hierarchy
3. Update CLAUDE.md references
4. Document symbol usage patterns

### Updating Existing Symbols
1. Maintain symbol stability
2. Version symbol changes if needed
3. Update symbol map documentation
4. Notify in CHANGELOG.md

---

**Version**: 1.0.0
**Last Updated**: 2025-11-04
**Maintained By**: Project Team
