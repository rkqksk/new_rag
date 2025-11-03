# RAG Enterprise Agent System

Claude Code agent orchestration system for RAG pipeline automation.

## Architecture

```
.agent/
├── SOP/                    # Standard Operating Procedures
│   ├── crawling.md         # 웹 크롤링 SOP
│   ├── embedding.md        # 임베딩 생성 SOP
│   ├── search.md           # 벡터 검색 SOP
│   └── orchestration.md    # 전체 워크플로우 조정 SOP
│
├── System/                 # System Context
│   ├── architecture.md     # RAG 시스템 아키텍처
│   ├── tech_stack.md       # 기술 스택 (Qdrant, FastAPI, Ollama)
│   └── data_flow.md        # 데이터 흐름 다이어그램
│
├── Tasks/                  # Agent Task Definitions
│   ├── crawl_products.md   # 제품 크롤링 작업
│   ├── generate_embeddings.md  # 임베딩 생성 작업
│   ├── vector_search.md    # 벡터 검색 작업
│   └── qa_workflow.md      # Q&A 전체 워크플로우
│
└── README.md               # This file
```

## Agent System vs Skills vs Python Scripts

| Component | Purpose | Structure | Execution |
|-----------|---------|-----------|-----------|
| **`.agent/`** | Claude Code agent orchestration | SOP/System/Tasks/README.md | Claude Code native |
| **`.claude/skills/`** | Progressive disclosure docs | SKILL.md | Manual reference |
| **`agents/`** | Standalone Python scripts | .py files | Direct Python execution |

## Integration Strategy

### 1. Agent System (`.agent/`) - Orchestration Layer
- **Role**: High-level workflow coordination
- **Claude Code Integration**: Native agent system
- **Example**: "Crawl new products → Generate embeddings → Index to Qdrant"

### 2. Skills (`.claude/skills/`) - Documentation Layer
- **Role**: Progressive disclosure documentation for domain experts
- **Claude Code Integration**: Reference documentation
- **Example**: Manufacturing defect classification, packaging specs

### 3. Python Scripts (`agents/`) - Execution Layer
- **Role**: Actual implementation logic
- **Called by**: `.agent/` Tasks via Python subprocess
- **Example**: `crawling_agent.py`, `embedding_agent.py`

## Workflow Example

```
User: "새 제품 데이터 크롤링하고 RAG 시스템에 추가해줘"

┌─────────────────────────────────────┐
│  .agent/ (Orchestration)            │
│  SOP/crawling.md → Tasks/crawl_products.md
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  agents/ (Execution)                │
│  Python: crawling_agent.py          │
│  → 크롤링 실행 → CSV 저장            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  .agent/ (Orchestration)            │
│  Tasks/generate_embeddings.md       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  agents/ (Execution)                │
│  Python: embedding_agent.py         │
│  → 임베딩 생성 → Qdrant 저장         │
└─────────────────────────────────────┘
              ↓
✅ Complete: 새 제품 RAG 시스템 추가됨
```

## Current Status

- [x] Python agent scripts created (14 agents, 2,507 lines)
- [x] Skills documentation created (manufacturing, packaging, rag-pipeline)
- [ ] **`.agent/` structure needed** (SOP, System, Tasks)
- [ ] Agent orchestration SOPs
- [ ] Integration with Python scripts

## Next Steps

1. **Create SOP/**: Standard operating procedures for each workflow
2. **Create System/**: System architecture and tech stack documentation
3. **Create Tasks/**: Task definitions that call Python scripts
4. **Test orchestration**: End-to-end workflow validation

---

**Version**: 1.0.0
**Last Updated**: 2025-10-26
**Status**: Initial setup in progress
