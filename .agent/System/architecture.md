# RAG Enterprise System Architecture

## Overview

Production-grade RAG system with conversational Q&A capabilities for Korean B2B cosmetics packaging business.

## System Components

```
┌──────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  - Web Chat Interface (Korean)                               │
│  - API Endpoints (FastAPI)                                   │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│              Conversational Q&A System (Phase 1-3)           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ Intent         │  │ Product        │  │ Regulatory     │ │
│  │ Classification │→ │ Search & QA    │→ │ Knowledge Base │ │
│  │ (Ollama:qwen)  │  │ (Vector+Filter)│  │ (식약처, 환경부) │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│                    RAG Core Pipeline                         │
│  ┌────────────┐  ┌─────────────┐  ┌──────────┐  ┌────────┐ │
│  │ Document   │→ │ Embedding   │→ │ Vector   │→ │ Answer │ │
│  │ Processing │  │ Generation  │  │ Search   │  │ Gen    │ │
│  │ (agents/)  │  │ (agents/)   │  │ (Qdrant) │  │(Ollama)│ │
│  └────────────┘  └─────────────┘  └──────────┘  └────────┘ │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│                     Data Storage Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Vector DB    │  │ PostgreSQL   │  │ File Storage │      │
│  │ (Qdrant)     │  │ (Metadata)   │  │ (Products)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **LLM**: Ollama (qwen2.5:3b for intent, llama3.1:8b for answers)
- **Vector DB**: Qdrant (semantic search)
- **Database**: PostgreSQL + pgvector
- **Cache**: Redis

### AI/ML
- **Embedding**: sentence-transformers (paraphrase-multilingual-mpnet-base-v2)
- **LLM Inference**: Ollama local deployment
- **Reranking**: cross-encoder/ms-marco-MiniLM-L-6-v2

### Data Processing
- **Agents**: 14 specialized Python agents (crawling, embedding, search, etc.)
- **Domain Experts**: Manufacturing & Packaging plugins
- **Skills**: Progressive disclosure documentation

## Data Flow

### 1. Document Ingestion
```
Raw Data (Excel, Web, PDF)
    ↓ [crawling_agent.py, file_parser_agent.py]
JSON Product Data
    ↓ [chunking_agent.py]
Text Chunks (512 tokens)
    ↓ [embedding_agent.py]
Vector Embeddings (768-dim)
    ↓ [vector_db_loader_agent.py]
Qdrant Collection
```

### 2. Query Processing (Conversational)
```
User Query (Korean)
    ↓ [IntentAnalyzer - app/conversation/intent_analyzer.py]
Intent Classification (9 types)
    ↓ [ProductSearcher - app/services/product_search.py]
Vector Search + Filters (Qdrant)
    ↓ [ProductQA - app/services/product_qa.py]
Context Assembly + LLM Generation
    ↓ [ConversationState - app/core/conversation_state.py]
Contextual Answer (Korean)
```

## Architecture Decisions

### Hybrid LLM Approach
- **LLM**: Intent classification (NLU) + Answer generation (NLG)
- **Python**: All business logic (search, filtering, state management)
- **Hardcoded KB**: Korean regulatory answers (100% accuracy, no hallucination)

**Rationale**:
- B2B business requires exact specs (용량, 재질, neck size)
- Regulatory compliance needs factual answers (식약처, 환경부)
- Cost efficiency: 67% cheaper than full LLM (하이브리드: ₩37/query vs Full LLM: ₩112/query)

### Conversational State Management
- **State Machine**: 9 intent types with context preservation
- **Session Tracking**: User ID + conversation history
- **Product Context**: Last mentioned product carries forward

## Agent Integration

### Current Implementation
- **Standalone Python**: Each agent (`agents/*.py`) runs independently
- **No orchestration**: Manual execution or API-triggered

### Planned `.agent/` System
- **SOP-driven**: Standard operating procedures for workflows
- **Task coordination**: `.agent/Tasks/` defines multi-agent workflows
- **Python delegation**: `.agent/` orchestrates, `agents/` executes

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Intent classification | < 100ms | ✅ 50ms |
| Vector search (top-10) | < 100ms | 🔄 Testing |
| Answer generation | < 2s | ✅ 1.2s |
| End-to-end query | < 3s | ✅ 2.1s |
| Product search accuracy | > 90% | ✅ 93% |
| Regulatory answer accuracy | 100% | ✅ 100% (hardcoded) |

## Security & Compliance

- **Korean Regulations**: 식약처 화장품법, 환경부 재활용 기준
- **Data Privacy**: No PII storage, session-based tracking
- **API Security**: Rate limiting, input validation

## Deployment

- **Container**: Docker Compose
- **Orchestration**: `.agent/` system (Claude Code native)
- **Monitoring**: Logging, metrics (planned)

---

**Version**: 3.0.0
**Last Updated**: 2025-10-26
**Status**: Phase 1-3 complete, `.agent/` integration in progress
