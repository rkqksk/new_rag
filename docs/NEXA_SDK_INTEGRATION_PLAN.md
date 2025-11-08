# NexaAI SDK Integration Plan - Complete RAG System

**Version**: 1.0
**Date**: 2025-11-07
**Status**: Implementation Ready
**Target**: Production-Grade Multi-Modal RAG with NexaAI SDK

---

## Executive Summary

현재 Production-Ready 상태인 RAG Enterprise 시스템에 **NexaAI SDK**를 통합하여 완벽한 Multi-Modal RAG 시스템을 구축합니다. 기존 Qdrant 벡터 DB와 Multi-Modal 인프라를 활용하면서, NexaAI SDK의 강력한 로컬 AI 기능을 추가하여 성능과 비용 효율성을 극대화합니다.

### Key Objectives

1. ✅ **NexaAI SDK 통합**: Ollama와 병행하여 듀얼 엔진 구성
2. ✅ **Qdrant 유지**: 기존 벡터 DB 인프라 활용
3. ✅ **Multi-Modal 강화**: 텍스트 + 이미지 + 오디오 + 비디오
4. ✅ **Localhost 개발**: 로컬 환경 최적화
5. ✅ **Cloudflare 배포**: Workers + Pages + Vectorize
6. ✅ **서버리스 옵션**: Edge Computing 지원
7. ✅ **CI/CD 파이프라인**: GitHub Actions 자동화

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [NexaAI SDK Integration](#nexaai-sdk-integration)
3. [Multi-Modal Pipeline](#multi-modal-pipeline)
4. [Local Development Setup](#local-development-setup)
5. [Cloudflare Deployment Strategy](#cloudflare-deployment-strategy)
6. [Serverless Architecture](#serverless-architecture)
7. [Development Pipeline](#development-pipeline)
8. [Implementation Roadmap](#implementation-roadmap)

---

## Architecture Overview

### Dual-Engine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│  • Next.js/React (Cloudflare Pages)                        │
│  • Chat Interface, Product Cards, Real-time Streaming      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway Layer                       │
│  • Cloudflare Workers (Edge) OR FastAPI (Self-hosted)      │
│  • Rate Limiting, Authentication, Request Routing          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Orchestration Layer                       │
│  ┌─────────────────┐         ┌──────────────────┐          │
│  │  NexaAI Engine  │         │   Ollama Engine  │          │
│  │  • Qwen3-VL-4B  │    +    │ • qwen2.5:7b     │          │
│  │  • Gemma3n      │         │ • nomic-embed    │          │
│  │  • DeepSeek-R1  │         │                  │          │
│  └─────────────────┘         └──────────────────┘          │
│           ↓                           ↓                     │
│  [Intelligent Router: Complexity-based Model Selection]    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Data Processing Layer                     │
│  • Document Processor (OCR: PaddleOCR/EasyOCR/Tesseract)   │
│  • Image Processor (CLIP, Shape Embeddings)                │
│  • Audio Processor (NEW: NexaAI Parakeet v3)               │
│  • Video Processor (NEW: Multi-frame extraction)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Vector Storage Layer                     │
│  ┌──────────────────┐        ┌───────────────────┐         │
│  │  Qdrant (Local)  │   OR   │ Cloudflare        │         │
│  │  • Products: 3K  │        │ Vectorize (Edge)  │         │
│  │  • Documents     │        │ • Global CDN      │         │
│  │  • Images        │        │ • Sub-50ms        │         │
│  └──────────────────┘        └───────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Caching & Metadata                       │
│  • Redis (Local) OR Cloudflare KV (Edge)                   │
│  • PostgreSQL (Local) OR D1 (Edge)                         │
└─────────────────────────────────────────────────────────────┘
```

### Decision Matrix: When to Use Each Engine

| Scenario | Engine | Model | Reason |
|----------|--------|-------|--------|
| 간단한 검색 쿼리 | NexaAI | Qwen3-1.7B | 빠른 응답 (<500ms) |
| 복잡한 추론 | Ollama | qwen2.5:7b-instruct | 높은 품질 |
| 이미지 분석 | NexaAI | Qwen3-VL-4B | Vision-Language 특화 |
| 대량 임베딩 | NexaAI | EmbeddingGemma | 배치 처리 최적화 |
| 음성 처리 | NexaAI | Parakeet v3 | 음성 인식 |
| 코드 생성 | NexaAI | DeepSeek-R1 | 코딩 특화 |

---

## NexaAI SDK Integration

### 1. Installation & Setup

#### Step 1: Install NexaAI CLI

```bash
# Linux (x86_64)
curl -fsSL https://github.com/NexaAI/nexa-sdk/releases/latest/download/nexa-cli_linux_x86_64.sh -o install.sh
chmod +x install.sh
./install.sh

# Verify installation
nexa --version
```

#### Step 2: Pull Required Models

```bash
# Text Generation (Primary)
nexa pull NexaAI/Qwen3-1.7B-GGUF                    # 빠른 응답용
nexa pull NexaAI/Qwen3-VL-4B-Instruct-GGUF          # Vision-Language

# Embeddings
nexa pull NexaAI/EmbeddingGemma-GGUF                # 임베딩 생성

# Specialized Models (Optional)
nexa pull NexaAI/DeepSeek-R1-Distill-Qwen-1.5B-GGUF # 코드/추론
nexa pull NexaAI/Parakeet-v3-GGUF                   # 음성 인식

# List cached models
nexa list
```

#### Step 3: Start NexaAI Server

```bash
# Start server with OpenAI-compatible API
nexa serve --host 0.0.0.0:8080

# Server endpoints
# http://localhost:8080/v1/completions
# http://localhost:8080/v1/chat/completions
# http://localhost:8080/v1/embeddings
```

### 2. Python Integration

#### Add Dependencies

```python
# requirements-nexa.txt
nexa-sdk>=0.1.0          # NexaAI SDK
openai>=1.0.0            # OpenAI-compatible client
```

#### NexaAI Service Wrapper

```python
# src/services/nexa_service.py

from typing import List, Dict, Optional, Union
import httpx
from openai import OpenAI
from pydantic import BaseModel

class NexaConfig(BaseModel):
    """NexaAI configuration"""
    base_url: str = "http://localhost:8080/v1"
    api_key: str = "not-needed"  # Local server
    timeout: int = 30
    max_retries: int = 3

class NexaService:
    """NexaAI SDK Service"""

    def __init__(self, config: Optional[NexaConfig] = None):
        self.config = config or NexaConfig()
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )

    async def generate_text(
        self,
        prompt: str,
        model: str = "Qwen3-1.7B",
        max_tokens: int = 500,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Union[str, AsyncIterator[str]]:
        """Generate text completion"""

        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream
        )

        if stream:
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            return response.choices[0].message.content

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "EmbeddingGemma"
    ) -> List[List[float]]:
        """Generate embeddings for texts"""

        response = self.client.embeddings.create(
            model=model,
            input=texts
        )

        return [item.embedding for item in response.data]

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: str = "Qwen3-VL-4B-Instruct"
    ) -> str:
        """Analyze image with vision-language model"""

        import base64

        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
        )

        return response.choices[0].message.content

    async def health_check(self) -> Dict[str, bool]:
        """Check NexaAI server health"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url.replace('/v1', '')}/health"
                )
                return {"healthy": response.status_code == 200}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
```

### 3. Intelligent Model Router

```python
# src/core/model_router.py

from enum import Enum
from typing import Dict, Literal
from pydantic import BaseModel

class ModelEngine(str, Enum):
    """Available model engines"""
    NEXA = "nexa"
    OLLAMA = "ollama"

class QueryComplexity(BaseModel):
    """Query complexity analysis"""
    score: float  # 0-1
    has_multimodal: bool
    has_reasoning: bool
    entity_count: int
    token_count: int

class ModelRouter:
    """Intelligent model selection router"""

    def __init__(self):
        self.routing_rules = {
            # Simple queries → NexaAI (fast)
            "simple": {
                "engine": ModelEngine.NEXA,
                "model": "Qwen3-1.7B",
                "threshold": 0.3
            },
            # Medium queries → NexaAI (balanced)
            "medium": {
                "engine": ModelEngine.NEXA,
                "model": "Qwen3-VL-4B-Instruct",
                "threshold": 0.7
            },
            # Complex queries → Ollama (quality)
            "complex": {
                "engine": ModelEngine.OLLAMA,
                "model": "qwen2.5:7b-instruct",
                "threshold": 1.0
            }
        }

    def analyze_complexity(self, query: str) -> QueryComplexity:
        """Analyze query complexity"""

        # Token count
        token_count = len(query.split())

        # Entity detection (simplified)
        entities = self._extract_entities(query)

        # Reasoning keywords
        reasoning_keywords = ["왜", "어떻게", "분석", "비교", "설명"]
        has_reasoning = any(kw in query for kw in reasoning_keywords)

        # Multimodal indicators
        multimodal_keywords = ["이미지", "사진", "그림", "영상"]
        has_multimodal = any(kw in query for kw in multimodal_keywords)

        # Calculate complexity score
        score = (
            0.2 * min(token_count / 100, 1.0) +
            0.3 * min(len(entities) / 10, 1.0) +
            0.3 * (1.0 if has_reasoning else 0.0) +
            0.2 * (1.0 if has_multimodal else 0.0)
        )

        return QueryComplexity(
            score=score,
            has_multimodal=has_multimodal,
            has_reasoning=has_reasoning,
            entity_count=len(entities),
            token_count=token_count
        )

    def route(self, query: str) -> Dict[str, str]:
        """Route query to appropriate engine"""

        complexity = self.analyze_complexity(query)

        # Force NexaAI for multimodal
        if complexity.has_multimodal:
            return {
                "engine": ModelEngine.NEXA,
                "model": "Qwen3-VL-4B-Instruct",
                "reason": "multimodal_required"
            }

        # Route based on complexity
        if complexity.score < 0.3:
            rule = self.routing_rules["simple"]
            reason = "simple_query"
        elif complexity.score < 0.7:
            rule = self.routing_rules["medium"]
            reason = "medium_complexity"
        else:
            rule = self.routing_rules["complex"]
            reason = "complex_reasoning"

        return {
            "engine": rule["engine"],
            "model": rule["model"],
            "reason": reason,
            "complexity_score": complexity.score
        }

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query (simplified)"""
        import re

        entities = []

        # Capacity
        if re.search(r'\d+\s*(ml|ML|L)', query):
            entities.append("capacity")

        # Neck
        if re.search(r'\d+\s*(파이|Φ|ø)', query):
            entities.append("neck")

        # Material
        materials = ["PP", "PE", "PET", "PETG", "PS"]
        if any(m in query.upper() for m in materials):
            entities.append("material")

        # MOQ
        if re.search(r'\d+\s*(개|ea)', query):
            entities.append("moq")

        return entities
```

### 4. Dual-Engine Integration

```python
# src/services/unified_llm_service.py

from typing import Union, AsyncIterator
from src.services.nexa_service import NexaService
from src.services.ollama_service import OllamaService  # Existing
from src.core.model_router import ModelRouter, ModelEngine

class UnifiedLLMService:
    """Unified LLM service supporting both NexaAI and Ollama"""

    def __init__(self):
        self.nexa = NexaService()
        self.ollama = OllamaService()
        self.router = ModelRouter()

    async def generate(
        self,
        prompt: str,
        stream: bool = False,
        force_engine: Optional[ModelEngine] = None
    ) -> Union[str, AsyncIterator[str]]:
        """Generate response with automatic routing"""

        # Route to appropriate engine
        if force_engine:
            engine = force_engine
            model = self._get_default_model(engine)
        else:
            routing = self.router.route(prompt)
            engine = routing["engine"]
            model = routing["model"]

        # Generate response
        if engine == ModelEngine.NEXA:
            return await self.nexa.generate_text(
                prompt=prompt,
                model=model,
                stream=stream
            )
        else:
            return await self.ollama.generate(
                prompt=prompt,
                model=model,
                stream=stream
            )

    async def embed(
        self,
        texts: List[str],
        engine: ModelEngine = ModelEngine.NEXA
    ) -> List[List[float]]:
        """Generate embeddings"""

        if engine == ModelEngine.NEXA:
            return await self.nexa.generate_embeddings(texts)
        else:
            return await self.ollama.embed(texts)

    def _get_default_model(self, engine: ModelEngine) -> str:
        """Get default model for engine"""

        defaults = {
            ModelEngine.NEXA: "Qwen3-1.7B",
            ModelEngine.OLLAMA: "qwen2.5:7b-instruct"
        }
        return defaults[engine]
```

---

## Multi-Modal Pipeline

### Enhanced Multi-Modal Architecture

```python
# src/services/multimodal_rag_service.py

from typing import List, Dict, Optional, Union
from pathlib import Path
from src.services.unified_llm_service import UnifiedLLMService
from src.core.ocr.document_processor import DocumentProcessor
from src.core.image_matching.visual_embedder import VisualEmbedder

class MultiModalRAGService:
    """Complete multi-modal RAG pipeline"""

    def __init__(self):
        self.llm = UnifiedLLMService()
        self.doc_processor = DocumentProcessor()
        self.visual_embedder = VisualEmbedder()

    async def process_document(
        self,
        file_path: Union[str, Path],
        extract_images: bool = True
    ) -> Dict:
        """Process document (PDF/Image/Excel) with NexaAI"""

        file_path = Path(file_path)

        # 1. Extract text and images
        if file_path.suffix.lower() == '.pdf':
            result = await self.doc_processor.process_pdf(file_path)
        elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            result = await self.doc_processor.process_image(file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.csv']:
            result = await self.doc_processor.process_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # 2. Analyze images with NexaAI Vision-Language model
        if extract_images and result.get("images"):
            for img_data in result["images"]:
                img_path = img_data["path"]

                # Analyze image
                analysis = await self.llm.nexa.analyze_image(
                    image_path=img_path,
                    prompt="Describe this product image in detail, including shape, color, material, and any visible text or labels.",
                    model="Qwen3-VL-4B-Instruct"
                )

                img_data["analysis"] = analysis

        # 3. Generate embeddings for all text chunks
        if result.get("chunks"):
            texts = [chunk["text"] for chunk in result["chunks"]]
            embeddings = await self.llm.embed(texts)

            for chunk, embedding in zip(result["chunks"], embeddings):
                chunk["embedding"] = embedding

        return result

    async def search_multimodal(
        self,
        query: str,
        image_path: Optional[str] = None,
        top_k: int = 10,
        modality_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """Multi-modal search (text + image + shape)"""

        weights = modality_weights or {
            "text": 0.5,
            "image": 0.3,
            "shape": 0.2
        }

        results = []

        # 1. Text search
        if query:
            query_embedding = await self.llm.embed([query])
            text_results = await self._search_text(
                query_embedding[0],
                top_k=top_k * 2
            )
            results.append(("text", text_results))

        # 2. Image search (if image provided)
        if image_path:
            # Extract visual features
            visual_embedding = await self.visual_embedder.embed(image_path)

            # Analyze image with NexaAI
            image_description = await self.llm.nexa.analyze_image(
                image_path=image_path,
                prompt="Describe the shape, color, and features of this product."
            )

            # Search by visual features
            visual_results = await self._search_image(
                visual_embedding,
                top_k=top_k * 2
            )
            results.append(("image", visual_results))

        # 3. Fuse results
        fused_results = self._fuse_multimodal_results(
            results,
            weights=weights,
            top_k=top_k
        )

        return fused_results

    def _fuse_multimodal_results(
        self,
        results: List[tuple],
        weights: Dict[str, float],
        top_k: int
    ) -> List[Dict]:
        """Fuse multi-modal search results"""

        # Reciprocal Rank Fusion (RRF)
        scores = {}
        k = 60  # RRF constant

        for modality, items in results:
            weight = weights.get(modality, 1.0)

            for rank, item in enumerate(items, 1):
                item_id = item["id"]

                if item_id not in scores:
                    scores[item_id] = {
                        "id": item_id,
                        "data": item,
                        "score": 0.0,
                        "modalities": []
                    }

                # RRF score
                rrf_score = weight / (k + rank)
                scores[item_id]["score"] += rrf_score
                scores[item_id]["modalities"].append(modality)

        # Sort by fused score
        ranked = sorted(
            scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return ranked[:top_k]
```

---

## Local Development Setup

### Complete localhost Configuration

#### 1. Docker Compose Enhancement

```yaml
# docker-compose.nexa.yml

version: '3.8'

services:
  # NexaAI Server
  nexa:
    image: nexaai/nexa-server:latest
    container_name: rag-nexa
    ports:
      - "8080:8080"
    volumes:
      - ./models/nexa:/root/.cache/nexa
    environment:
      - NEXA_MODEL=Qwen3-VL-4B-Instruct
      - NEXA_HOST=0.0.0.0
      - NEXA_PORT=8080
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - rag-network

  # FastAPI Backend (Enhanced)
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rag-api
    ports:
      - "8001:8001"
    volumes:
      - ./src:/app/src
      - ./data:/app/data
    environment:
      # Existing
      - QDRANT_HOST=qdrant
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      # NexaAI Integration
      - NEXA_BASE_URL=http://nexa:8080/v1
      - NEXA_ENABLED=true
      - MODEL_ROUTER_ENABLED=true
    depends_on:
      - qdrant
      - redis
      - postgres
      - nexa
    restart: unless-stopped
    networks:
      - rag-network

  # Existing services (Qdrant, Redis, PostgreSQL)
  qdrant:
    image: qdrant/qdrant:v1.7.0
    container_name: rag-qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./data/qdrant:/qdrant/storage
    restart: unless-stopped
    networks:
      - rag-network

  redis:
    image: redis:7-alpine
    container_name: rag-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    restart: unless-stopped
    networks:
      - rag-network

  postgres:
    image: postgres:16-alpine
    container_name: rag-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=rag
      - POSTGRES_USER=rag
      - POSTGRES_PASSWORD=rag123
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - rag-network

networks:
  rag-network:
    driver: bridge
```

#### 2. Environment Configuration

```bash
# .env.nexa

# NexaAI Configuration
NEXA_ENABLED=true
NEXA_BASE_URL=http://localhost:8080/v1
NEXA_DEFAULT_MODEL=Qwen3-1.7B
NEXA_VISION_MODEL=Qwen3-VL-4B-Instruct
NEXA_EMBEDDING_MODEL=EmbeddingGemma

# Model Router
MODEL_ROUTER_ENABLED=true
MODEL_ROUTER_SIMPLE_THRESHOLD=0.3
MODEL_ROUTER_COMPLEX_THRESHOLD=0.7

# Existing Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_HOST=localhost
POSTGRES_HOST=localhost
API_PORT=8001
```

#### 3. Quick Start Script

```bash
#!/bin/bash
# scripts/start-nexa.sh

set -e

echo "🚀 Starting RAG Enterprise with NexaAI SDK..."

# Step 1: Install NexaAI (if not installed)
if ! command -v nexa &> /dev/null; then
    echo "📦 Installing NexaAI SDK..."
    curl -fsSL https://github.com/NexaAI/nexa-sdk/releases/latest/download/nexa-cli_linux_x86_64.sh -o /tmp/install.sh
    chmod +x /tmp/install.sh
    /tmp/install.sh
fi

# Step 2: Pull required models
echo "📥 Pulling NexaAI models..."
nexa pull NexaAI/Qwen3-1.7B-GGUF
nexa pull NexaAI/Qwen3-VL-4B-Instruct-GGUF
nexa pull NexaAI/EmbeddingGemma-GGUF

# Step 3: Start Docker services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.yml -f docker-compose.nexa.yml up -d

# Step 4: Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# Step 5: Health check
echo "🏥 Health check..."
curl -f http://localhost:8001/health/ready || exit 1
curl -f http://localhost:8080/health || exit 1

echo "✅ All services running!"
echo ""
echo "🌐 Services:"
echo "  • API:       http://localhost:8001"
echo "  • API Docs:  http://localhost:8001/api/v1/docs"
echo "  • NexaAI:    http://localhost:8080"
echo "  • Qdrant:    http://localhost:6333/dashboard"
echo "  • Frontend:  http://localhost:8080 (run: cd frontend && python3 -m http.server 8080)"
echo ""
echo "🎯 Try: curl -X POST http://localhost:8001/api/v1/search/ -H 'Content-Type: application/json' -d '{\"query\":\"50ml PET 용기\"}'"
```

---

## Cloudflare Deployment Strategy

### Overview

Cloudflare 플랫폼을 활용한 글로벌 엣지 배포로 **< 50ms 응답 시간** 달성

### Architecture Components

```
┌──────────────────────────────────────────────────────────┐
│              Cloudflare Edge Network                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐        ┌──────────────────┐        │
│  │ Cloudflare     │        │  Cloudflare      │        │
│  │ Pages          │   →    │  Workers         │        │
│  │ (Frontend)     │        │  (API Gateway)   │        │
│  └────────────────┘        └──────────────────┘        │
│         ↓                           ↓                    │
│  ┌────────────────┐        ┌──────────────────┐        │
│  │ Vectorize      │   ←    │  Workers AI      │        │
│  │ (Vector DB)    │        │  (LLM Inference) │        │
│  └────────────────┘        └──────────────────┘        │
│         ↓                           ↓                    │
│  ┌────────────────┐        ┌──────────────────┐        │
│  │ D1 Database    │   ←    │  KV Storage      │        │
│  │ (Metadata)     │        │  (Cache)         │        │
│  └────────────────┘        └──────────────────┘        │
│                                                          │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│           Origin Server (Optional Fallback)              │
│  • Self-hosted Qdrant (Full vector store)               │
│  • NexaAI Server (Heavy models)                         │
│  • PostgreSQL (Full metadata)                           │
└──────────────────────────────────────────────────────────┘
```

### Implementation

#### 1. Cloudflare Workers (API)

```typescript
// workers/api/src/index.ts

import { Hono } from 'hono';
import { cors } from 'hono/cors';

type Bindings = {
  VECTORIZE: VectorizeIndex;
  DB: D1Database;
  KV: KVNamespace;
  AI: any; // Cloudflare Workers AI
};

const app = new Hono<{ Bindings: Bindings }>();

app.use('/*', cors());

// Search endpoint
app.post('/api/v1/search', async (c) => {
  const { query, top_k = 10 } = await c.req.json();

  // 1. Check cache
  const cacheKey = `search:${query}`;
  const cached = await c.env.KV.get(cacheKey, 'json');

  if (cached) {
    return c.json({
      results: cached,
      cached: true,
      latency_ms: 5
    });
  }

  const startTime = Date.now();

  // 2. Generate embedding with Workers AI
  const embedding = await c.env.AI.run('@cf/baai/bge-base-en-v1.5', {
    text: [query]
  });

  // 3. Search Vectorize
  const results = await c.env.VECTORIZE.query(embedding.data[0], {
    topK: top_k,
    returnMetadata: true
  });

  // 4. Enrich with metadata from D1
  const productIds = results.matches.map(m => m.id);
  const products = await c.env.DB.prepare(
    `SELECT * FROM products WHERE id IN (${productIds.join(',')})`
  ).all();

  const enriched = results.matches.map(match => ({
    ...match,
    product: products.results.find(p => p.id === match.id)
  }));

  // 5. Cache result
  await c.env.KV.put(cacheKey, JSON.stringify(enriched), {
    expirationTtl: 3600 // 1 hour
  });

  const latency = Date.now() - startTime;

  return c.json({
    results: enriched,
    cached: false,
    latency_ms: latency
  });
});

// RAG generation endpoint
app.post('/api/v1/generate', async (c) => {
  const { query, context } = await c.req.json();

  // Generate with Workers AI
  const response = await c.env.AI.run('@cf/meta/llama-2-7b-chat-int8', {
    messages: [
      {
        role: 'system',
        content: 'You are a helpful product recommendation assistant.'
      },
      {
        role: 'user',
        content: `Context: ${context}\n\nQuestion: ${query}`
      }
    ]
  });

  return c.json({
    answer: response.response,
    model: 'llama-2-7b-chat-int8'
  });
});

export default app;
```

#### 2. Cloudflare Pages (Frontend)

```typescript
// frontend-next/pages/index.tsx

import { useState } from 'react';

const WORKER_API = 'https://api.your-domain.workers.dev';

export default function ChatPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);

    try {
      const response = await fetch(`${WORKER_API}/api/v1/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 10 })
      });

      const data = await response.json();
      setResults(data.results);

      console.log(`Latency: ${data.latency_ms}ms (cached: ${data.cached})`);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>RAG Enterprise</h1>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="제품 검색..."
      />

      <button onClick={handleSearch} disabled={loading}>
        {loading ? '검색 중...' : '검색'}
      </button>

      <div className="results">
        {results.map((result, i) => (
          <div key={i} className="result-card">
            <h3>{result.product.name}</h3>
            <p>Similarity: {result.score.toFixed(3)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### 3. Vectorize Setup

```bash
# Create Vectorize index
npx wrangler vectorize create rag-products \
  --dimensions=384 \
  --metric=cosine

# Upload vectors
npx wrangler vectorize insert rag-products \
  --file=./data/vectors.ndjson
```

#### 4. D1 Database

```sql
-- schema.sql

CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  code TEXT UNIQUE,
  capacity TEXT,
  material TEXT,
  metadata TEXT, -- JSON
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_code ON products(code);
CREATE INDEX idx_products_material ON products(material);
```

```bash
# Create D1 database
npx wrangler d1 create rag-metadata

# Execute schema
npx wrangler d1 execute rag-metadata --file=./schema.sql
```

#### 5. Deployment

```bash
# Deploy Workers
cd workers/api
npx wrangler deploy

# Deploy Pages
cd frontend-next
npx wrangler pages deploy ./out
```

### Hybrid Architecture (Edge + Origin)

```typescript
// workers/api/src/hybrid.ts

export async function hybridSearch(
  query: string,
  env: Bindings
): Promise<SearchResults> {

  // Try edge-first (Cloudflare Vectorize)
  try {
    const edgeResults = await searchEdge(query, env);

    // If good enough, return immediately
    if (edgeResults.length >= 5 && edgeResults[0].score > 0.8) {
      return {
        source: 'edge',
        results: edgeResults,
        latency_ms: edgeResults.latency
      };
    }
  } catch (error) {
    console.error('Edge search failed, falling back to origin', error);
  }

  // Fallback to origin (full Qdrant)
  const originResults = await searchOrigin(query);

  return {
    source: 'origin',
    results: originResults,
    latency_ms: originResults.latency
  };
}

async function searchEdge(query: string, env: Bindings) {
  // Use Cloudflare Vectorize (subset of vectors)
  const embedding = await env.AI.run('@cf/baai/bge-base-en-v1.5', {
    text: [query]
  });

  return await env.VECTORIZE.query(embedding.data[0], { topK: 10 });
}

async function searchOrigin(query: string) {
  // Call self-hosted Qdrant (full dataset)
  const response = await fetch('https://origin.your-domain.com/api/v1/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });

  return await response.json();
}
```

---

## Serverless Architecture

### Complete Serverless Stack

#### Option 1: Cloudflare-Only (Full Serverless)

```
User → Cloudflare Pages (Frontend)
     → Cloudflare Workers (API)
     → Vectorize (Vector DB)
     → Workers AI (LLM)
     → D1 (Metadata)
     → KV (Cache)
```

**Pros**:
- ✅ Zero server management
- ✅ Global CDN (< 50ms worldwide)
- ✅ Pay-per-use pricing
- ✅ Auto-scaling

**Cons**:
- ❌ Limited vector storage (Vectorize beta)
- ❌ Smaller LLM models
- ❌ Cold start latency

#### Option 2: Hybrid (Edge + Serverless Functions)

```
User → Cloudflare Pages
     → Cloudflare Workers (Routing)
     ├─→ Vercel Functions (Complex queries)
     │   └─→ NexaAI API (Heavy models)
     └─→ Workers AI (Simple queries)
```

```typescript
// workers/hybrid-router.ts

export async function routeQuery(query: string, env: Bindings) {
  // Analyze complexity
  const complexity = analyzeComplexity(query);

  if (complexity < 0.3) {
    // Simple → Cloudflare Workers AI
    return await env.AI.run('@cf/meta/llama-2-7b-chat-int8', {
      messages: [{ role: 'user', content: query }]
    });
  } else {
    // Complex → Vercel Function → NexaAI
    const response = await fetch('https://api.vercel.app/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${env.VERCEL_TOKEN}`
      },
      body: JSON.stringify({
        query,
        model: 'Qwen3-VL-4B-Instruct'
      })
    });

    return await response.json();
  }
}
```

#### Option 3: Serverless Containers (AWS Lambda + Fargate)

```yaml
# serverless.yml

service: rag-enterprise

provider:
  name: aws
  runtime: python3.11
  region: ap-northeast-2

functions:
  search:
    handler: src/handlers/search.handler
    events:
      - http:
          path: /search
          method: post
    environment:
      QDRANT_URL: ${env:QDRANT_URL}
      NEXA_API_URL: ${env:NEXA_API_URL}
    timeout: 30
    memorySize: 2048

  generate:
    handler: src/handlers/generate.handler
    events:
      - http:
          path: /generate
          method: post
    environment:
      NEXA_API_URL: ${env:NEXA_API_URL}
    timeout: 60
    memorySize: 4096

resources:
  Resources:
    VectorDB:
      Type: AWS::ECS::Service
      Properties:
        ServiceName: qdrant
        TaskDefinition: !Ref QdrantTask
        LaunchType: FARGATE
```

---

## Development Pipeline

### Complete CI/CD with GitHub Actions

```yaml
# .github/workflows/deploy.yml

name: Deploy RAG Enterprise

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-nexa.txt

      - name: Run tests
        run: |
          pytest tests/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

  deploy-cloudflare:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Deploy Workers
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          command: deploy
          workingDirectory: workers/api

      - name: Deploy Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          command: pages deploy ./frontend-next/out

  deploy-kubernetes:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-2

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name rag-cluster --region ap-northeast-2

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/rag-api \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

          kubectl rollout status deployment/rag-api
```

### Local Development Workflow

```bash
# Makefile

.PHONY: install dev test build deploy

install:
	pip install -r requirements.txt
	pip install -r requirements-nexa.txt
	nexa pull NexaAI/Qwen3-1.7B-GGUF
	nexa pull NexaAI/Qwen3-VL-4B-Instruct-GGUF

dev:
	docker-compose -f docker-compose.yml -f docker-compose.nexa.yml up

test:
	pytest tests/ -v --cov=src

lint:
	black src/
	ruff check src/
	mypy src/

build:
	docker build -t rag-enterprise:latest .

deploy-local:
	./scripts/deploy-optimized.sh development

deploy-prod:
	./scripts/deploy-optimized.sh production
	kubectl apply -f k8s/
```

---

## Implementation Roadmap

### Phase 1: NexaAI Integration (Week 1-2)

**Tasks**:
1. ✅ Install NexaAI SDK
2. ✅ Create NexaService wrapper
3. ✅ Implement ModelRouter
4. ✅ Create UnifiedLLMService
5. ✅ Update API endpoints
6. ✅ Write integration tests

**Deliverables**:
- NexaAI working alongside Ollama
- Automatic model routing
- 30% faster responses for simple queries

### Phase 2: Multi-Modal Enhancement (Week 3-4)

**Tasks**:
1. ✅ Integrate Qwen3-VL for image analysis
2. ✅ Add audio processing (Parakeet v3)
3. ✅ Enhance document processor
4. ✅ Update multi-modal search
5. ✅ Test end-to-end workflows

**Deliverables**:
- Complete multi-modal pipeline
- Image + Audio + Text processing
- 90% accuracy in multi-modal search

### Phase 3: Cloudflare Setup (Week 5-6)

**Tasks**:
1. ✅ Set up Cloudflare Workers
2. ✅ Create Vectorize index
3. ✅ Set up D1 database
4. ✅ Deploy Pages frontend
5. ✅ Configure KV cache
6. ✅ Implement hybrid routing

**Deliverables**:
- Cloudflare Workers API
- < 50ms global latency
- 99.9% uptime

### Phase 4: CI/CD Pipeline (Week 7-8)

**Tasks**:
1. ✅ GitHub Actions workflows
2. ✅ Automated testing
3. ✅ Docker builds
4. ✅ Cloudflare deployments
5. ✅ Kubernetes rollouts
6. ✅ Monitoring integration

**Deliverables**:
- Fully automated deployments
- 100% test coverage
- Zero-downtime updates

---

## Success Metrics

### Performance Targets

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Simple Query Response | 3-5s | < 500ms | **90% faster** |
| Complex Query Response | 5-10s | < 2s | **80% faster** |
| Image Analysis | N/A | < 1s | **NEW** |
| Global Latency (Cloudflare) | N/A | < 50ms | **NEW** |
| Concurrent Users | 10 | 10,000 | **1000x** |
| Vector Search Recall@10 | 0.85 | 0.95 | **+12%** |

### Cost Efficiency

| Deployment | Monthly Cost | Requests/Month | Cost per 1M |
|------------|--------------|----------------|-------------|
| Current (Self-hosted) | $700 | 100K | $7,000 |
| **Cloudflare Edge** | **$200** | **10M** | **$20** |
| Hybrid (Edge + Origin) | $500 | 5M | $100 |

---

## Conclusion

이 계획은 NexaAI SDK를 기반으로 한 **완벽한 Production-Grade RAG 시스템**을 구축합니다:

✅ **듀얼 엔진**: NexaAI (빠름) + Ollama (고품질)
✅ **Multi-Modal**: 텍스트 + 이미지 + 오디오 + 비디오
✅ **Global Edge**: Cloudflare 배포로 < 50ms 응답
✅ **Serverless 옵션**: 제로 서버 관리
✅ **자동화**: 완벽한 CI/CD 파이프라인
✅ **비용 효율**: 350% 비용 절감

**다음 단계**: Phase 1 구현 시작 (NexaAI 통합)

---

**Document Owner**: RAG Enterprise Team
**Last Updated**: 2025-11-07
**Next Review**: 2025-11-14
