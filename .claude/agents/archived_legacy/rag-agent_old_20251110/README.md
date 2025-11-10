# RAG Agent

**Purpose**: RAG system optimization - embeddings, chunking, search, and retrieval

**Version**: 1.0.0
**Status**: ✅ Production-Ready

---

## 🎯 Overview

Specialized sub-agent for RAG system development and optimization.

### Key Features

- ✅ **Embedding optimization** (Sentence Transformers, OpenCLIP, SigLIP)
- ✅ **Advanced chunking** (atomic, semantic, hierarchical)
- ✅ **Vector search** (Qdrant hybrid search)
- ✅ **Retrieval tuning** (re-ranking, filtering)
- ✅ **RAG evaluation** (metrics, A/B testing)

---

## 🚀 Usage

### Via Task Tool

```python
# Launch RAG agent for system optimization
Task(
    subagent_type="rag-agent",
    prompt="Optimize embedding model for Korean + English text"
)
```

### Tools Available

- `EmbeddingService` - Embedding generation
- `ChunkingService` - Text chunking strategies
- `SearchService` - Vector search
- `PersonalizationService` - User-specific search

---

## 🔧 Configuration

Located in `agent.json`:

```json
{
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "chunking_strategy": "atomic",
  "vector_db": "qdrant",
  "search_algorithm": "hybrid"
}
```

---

## 📊 Performance

- ✅ **122+ tests passing**
- ✅ **3,246 vectors indexed**
- ✅ **0.79-0.82 similarity scores**
- ✅ **< 500ms search latency**

---

## 📚 Related

- Skills: `rag-pipeline`, `embedding-expert`, `chunking-expert`, `nexa-rag-optimizer`
- Docs: `docs/RAG_ACTIVATION_STRATEGY.md`
- Architecture: `docs/OPEN_SOURCE_ARCHITECTURE.md`

---

**Created**: 2025-11-08
**Last Updated**: 2025-11-08
