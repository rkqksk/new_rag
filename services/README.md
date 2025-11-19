# Microservices Architecture

This directory contains independent microservices for the RAG Enterprise platform.

## Services

### 1. RAG Service (Port 8002)
**Tech**: Node.js + TypeScript + Fastify
**Purpose**: Retrieval-Augmented Generation
- Semantic search
- Context retrieval
- LLM integration

### 2. Collector Service (Port 8004)
**Tech**: Python + FastAPI + Scrapy
**Purpose**: Automated data collection
- Web scraping
- API polling
- File parsing
- Scheduled jobs

### 3. Manufacturing Service (Port 8005)
**Tech**: Python + FastAPI + YOLO
**Purpose**: Vision inspection & quality control
- Defect detection
- Image classification
- Quality metrics

### 4. Realtime Service (Port 8003)
**Tech**: Node.js + Socket.IO + Redis
**Purpose**: Real-time updates
- WebSocket connections
- Pub/Sub messaging
- Event broadcasting

### 5. ML Service (Port 8006)
**Tech**: Python + FastAPI + Transformers
**Purpose**: Machine learning operations
- Text embeddings
- Model inference
- LLM serving

## Inter-Service Communication

Services communicate via:
- **REST APIs** - Synchronous requests
- **Redis Pub/Sub** - Asynchronous events
- **Kafka** - Event streaming (future)

## Development

Each service can be run independently:

```bash
# RAG Service
cd services/rag
pnpm install && pnpm dev

# Collector Service
cd services/collector
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8004

# Manufacturing Service
cd services/manufacturing
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8005

# Realtime Service
cd services/realtime
pnpm install && pnpm dev

# ML Service
cd services/ml
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8006
```

## Deployment

Each service has its own Dockerfile and can be deployed independently to Kubernetes.

## Status

All services are currently **scaffolds** with basic structure and placeholders.
Implementation is planned for future phases.
