# RAG Enterprise - Quick Start Guide

**Status**: ✅ Operational | **Version**: 1.0.1 | **Last Updated**: 2025-11-03

---

## 🚀 1-Minute Setup

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Start the server
uvicorn src.api.app:app --reload

# 3. Open browser
# http://localhost:8000/docs
```

That's it! The system is ready.

---

## 📝 Common Commands

### Development

```bash
# Run tests
.venv/bin/pytest tests/test_rag_pipeline.py -v

# Format code
.venv/bin/black src/ tests/
.venv/bin/isort src/ tests/

# Type check (optional)
.venv/bin/mypy src/
```

### Using the RAG System

```python
from src.core.rag_pipeline import RAGPipeline
from src.core.document_loader import FlexibleDocumentLoader
from src.core.embedding_service import EmbeddingService
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

# Setup
loader = FlexibleDocumentLoader()
splitter = RecursiveCharacterTextSplitter(chunk_size=512)
embeddings = EmbeddingService()
db = QdrantClient(":memory:")

# Create pipeline
rag = RAGPipeline(
    loader=loader,
    text_splitter=splitter,
    embedding_model=embeddings,
    vector_db=db
)

# Ingest
rag.ingest_documents(["doc.pdf", "data.txt"])

# Query
results = rag.retrieve("your question here", top_k=5)
print(results)
```

---

## 🔧 Troubleshooting

### Application won't start?
```bash
.venv/bin/python -c "from src.api.app import create_app; create_app()"
# Check error message
```

### Dependencies issue?
```bash
.venv/bin/pip install --upgrade -r requirements.txt
```

### Tests failing?
```bash
.venv/bin/pytest tests/test_rag_pipeline.py -v --tb=short
```

---

## 📚 Documentation

- **Full Summary**: `claudedocs/SESSION_COMPLETE_SUMMARY.md`
- **Architecture**: `docs/ARCHITECTURE_FINAL.md`
- **API Docs**: `docs/API_REFERENCE.md`
- **Deployment**: `docs/DEPLOYMENT_STRATEGY.md`

---

## ✅ What's Working

- ✅ Document ingestion (PDF, TXT, CSV, MD)
- ✅ Semantic search
- ✅ Metadata filtering
- ✅ REST API
- ✅ Error handling
- ✅ Multiple embedding models

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Start server | `uvicorn src.api.app:app --reload` |
| Run tests | `.venv/bin/pytest tests/ -v` |
| Format code | `.venv/bin/black src/` |
| Check types | `.venv/bin/mypy src/` |

---

**Need Help?** Check `claudedocs/SESSION_COMPLETE_SUMMARY.md` for comprehensive guide.
