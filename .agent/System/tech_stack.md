# Tech Stack

## Core Technologies

### Backend Framework
- **FastAPI** (0.109+)
  - Async/await support
  - Automatic API documentation (OpenAPI/Swagger)
  - Type hints + Pydantic validation
  - WebSocket support for real-time updates

### Python Version
- **Python 3.11+**
  - Performance improvements
  - Better error messages
  - asyncio enhancements

## AI/ML Stack

### LLM Inference
- **Ollama** (local deployment)
  - **qwen2.5:3b**: Intent classification (fast, accurate for Korean)
  - **llama3.1:8b**: Answer generation (high quality, contextual)
  - Local inference (no API costs, data privacy)
  - GGUF quantization (reduced memory usage)

### Embedding Models
- **sentence-transformers**
  - Primary: `paraphrase-multilingual-mpnet-base-v2`
    - 768-dim vectors
    - Multilingual (Korean + English)
    - Good semantic understanding
  - Alternative: `multilingual-e5-large`
    - 1024-dim vectors
    - Higher quality, slower

### Reranking (Optional)
- **cross-encoder/ms-marco-MiniLM-L-6-v2**
  - Rerank top-K search results
  - Improve relevance by 10-15%
  - Used for critical queries only (cost optimization)

## Vector Database

### Primary: Qdrant
- **Version**: 1.7+
- **Features**:
  - Fast similarity search (HNSW index)
  - Filtering support (metadata)
  - Hybrid search (vector + keyword)
  - Payload storage (no separate DB needed)
  - Snapshots & backups
- **Deployment**: Docker container
- **Scalability**: Horizontal scaling with sharding

### Alternative: PostgreSQL + pgvector
- **Use Case**: If already using PostgreSQL
- **Extension**: pgvector (vector similarity search)
- **Performance**: Good for <100K vectors
- **Integration**: Same SQL database as app data

## Data Storage

### File Storage
- **Local filesystem**: Product JSON, images
- **Structure**: Organized by category (Bottle, Jar, etc.)
- **Format**: JSON (easy to read, version control friendly)

### Metadata Database (Optional)
- **PostgreSQL**: User sessions, conversation history, analytics
- **Redis**: Caching, session management, rate limiting

## Agent System

### Python Agents
- **14 specialized agents** (2,507 lines total)
  - `crawling_agent.py`: Web scraping
  - `embedding_agent.py`: Vector generation
  - `search_agent.py`: Similarity search
  - `qa_agent.py`: Answer generation
  - `vector_db_loader_agent.py`: Qdrant indexing
  - 9 more supporting agents

### Orchestration
- **`.agent/` system** (Claude Code native)
  - SOP-driven workflows
  - Task coordination
  - Python agent delegation

## Frontend (Current)

### Web Chat Interface
- **Framework**: HTML + CSS + JavaScript (vanilla)
- **Location**: `frontend/index.html`
- **Features**:
  - Real-time chat (WebSocket)
  - Markdown rendering
  - Korean language support
  - Product cards (images, specs, pricing)

### Future: React/Vue
- **Planned**: React + TypeScript
- **Features**:
  - Component library (shadcn/ui)
  - State management (Zustand)
  - Build tool (Vite)

## Deployment

### Containerization
- **Docker Compose**
  - Services: API, Qdrant, Redis, PostgreSQL
  - Volumes: Data persistence
  - Networks: Service isolation

### Orchestration (Future)
- **Kubernetes** (for production scale)
  - Auto-scaling
  - Load balancing
  - Health checks

## Development Tools

### Code Quality
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **pytest**: Testing framework
- **coverage**: Test coverage

### Documentation
- **OpenAPI/Swagger**: Auto-generated API docs
- **Markdown**: READMEs, SOPs, architecture docs

### Monitoring
- **Logging**: Python `logging` module
- **Metrics**: Prometheus (future)
- **Tracing**: OpenTelemetry (future)

## Dependencies

### Core
```
fastapi==0.109.0
uvicorn[standard]==0.25.0
pydantic==2.5.0
httpx==0.26.0
```

### AI/ML
```
sentence-transformers==2.3.0
qdrant-client==1.7.0
transformers==4.36.0
torch==2.1.0
```

### Data Processing
```
beautifulsoup4==4.12.0
requests==2.31.0
pandas==2.1.0
openpyxl==3.1.0
```

### Full List
See `requirements.txt` for complete dependencies

## Environment Variables

### Required
```bash
# Ollama
OLLAMA_URL=http://localhost:11434

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=<optional>

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/ragdb
REDIS_URL=redis://localhost:6379
```

### Optional
```bash
# Model selection
INTENT_MODEL=qwen2.5:3b
ANSWER_MODEL=llama3.1:8b
EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2

# Performance tuning
EMBEDDING_BATCH_SIZE=32
SEARCH_TOP_K=10
RERANK_ENABLED=false
```

## Performance Benchmarks

### Hardware Requirements

#### Minimum (Development)
- CPU: 4 cores
- RAM: 8GB
- Disk: 20GB SSD

#### Recommended (Production)
- CPU: 8 cores (for Ollama inference)
- RAM: 16GB (8GB for Ollama, 4GB for embeddings, 4GB for system)
- Disk: 100GB SSD
- GPU: Optional (NVIDIA for faster inference)

### Performance Metrics

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Intent classification | 50ms | 20 req/s |
| Vector search (top-10) | 30ms | 33 req/s |
| Embedding generation | 8ms/item | 125 items/s |
| Answer generation | 1.2s | 0.8 req/s |
| End-to-end query | 2.1s | 0.5 req/s |

### Scaling Limits

- **Single instance**: 100 concurrent users
- **Qdrant**: 10M+ vectors (with HNSW)
- **PostgreSQL**: 1M+ sessions (with indexing)

## Security

### Authentication & Authorization
- **API Keys**: For external access
- **Rate Limiting**: Redis-based
- **CORS**: Configured for frontend origin

### Data Privacy
- **No PII storage**: Session-based tracking only
- **Local LLM**: No data sent to external APIs
- **Encrypted storage**: Optional for sensitive data

---

**Last Updated**: 2025-10-26
**Version**: 3.0.0
