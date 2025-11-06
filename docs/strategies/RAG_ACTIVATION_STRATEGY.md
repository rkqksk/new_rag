# RAG Pipeline Skill 활성화 전략

> **Symbol Reference**: §rag.*
> **Quick Access**: See `CLAUDE.md` for current status and next steps.
> **Full Map**: `docs/SYMBOL_SYSTEM.md`

## 📊 Executive Summary

**목표**: RAG Pipeline Skill을 완전히 활성화하여 857개 제품 데이터에 대한 벡터 검색 지원

**현재 상태**: ~~20%~~ → **85% 완성** ✅
- ✅ Phase 1: 분석 완료
- ✅ Phase 2: Core 모듈 개발 완료
- ✅ Phase 3: 인프라 설정 완료 (Qdrant + Ollama)
- ✅ Phase 4: Skill 통합 완료
- ✅ Phase 5: 데이터 임베딩 완료 (857/857 products)

**목표 상태**: 100% 작동 (Full RAG Pipeline)
**남은 작업**: Production 배포 최적화 (15%)

**우선순위**: ~~Medium~~ → **High** (벡터 검색 활성화됨)

---

## ✅ 완성 현황 (2025-11-04 업데이트)

### 구현된 Core 모듈

#### 1. `src/core/rag_pipeline.py` (262 lines)
**기능**: 통합 RAG 파이프라인
- `RAGPipeline` 클래스: 문서 수집 → 임베딩 → 검색 → 답변 생성
- `ingest_documents()`: 문서 로딩, 청킹, 임베딩, Qdrant 업로드
- `retrieve()`: 벡터 유사도 검색 (메타데이터 필터링 지원)
- `generate_response()`: Ollama 답변 생성
- `extract_citations()`: 출처 정보 추출

**테스트 결과**: ✅ All passed (Score: 0.7254)

#### 2. `src/core/embedding_service.py` (72 lines)
**기능**: 벡터 임베딩 생성
- Model: `all-MiniLM-L6-v2` (384 dim)
- GPU 지원 (CUDA/MPS)
- Batch embedding 지원

**테스트 결과**: ✅ Passed

#### 3. `src/api/chat.py` (450 lines)
**기능**: API 통합
- Feature flag: `USE_VECTOR_RAG=true` (환경변수)
- `/chat/query` 엔드포인트: 벡터 검색 + RAG 답변
- Backward compatibility: 파일 기반 검색 fallback

**테스트 결과**: ✅ Passed (Score: 0.5678)

### 구현된 Skill 래퍼

#### `.claude/skills/rag-pipeline/scripts/skill.py`
**업데이트 완료**:
- ✅ `process_document()`: Core RAGPipeline 사용
- ✅ `vector_search()`: 실제 벡터 검색
- ✅ `rag_query()`: 검색 + 답변 생성 (시간 측정 포함)
- ✅ Domain Expert 통합

### 데이터 임베딩 현황

#### `scripts/embed_products.py` 실행 완료
- **Total**: 857/857 products (100%)
- **Bottle**: 675
- **Jar**: 42
- **Cap**: 118
- **Pump**: 22

**임베딩 완료 시각**: 2025-11-04
**Collection**: `products` @ Qdrant
**Search Test**: ✅ Passed (Score: 0.6405)

### 인프라 구성

- ✅ **Colima**: 4 CPU, 8GB RAM
- ✅ **Qdrant**: v1.11.3 (http://localhost:6333)
- ✅ **Ollama**: qwen2.5:7b-instruct
- ✅ **Python venv**: .venv (all dependencies installed)

---

## 🎯 전략 개요

### 핵심 접근법: **Incremental Integration**

기존 작동 중인 `contextual_rag.py`를 유지하면서, 단계적으로 벡터 검색을 추가합니다.

```
현재 시스템 (작동 중)
    ↓
+ 벡터 임베딩 레이어
    ↓
+ 하이브리드 검색
    ↓
RAG Skill 통합
```

---

## 📋 Phase별 상세 계획

### Phase 1: 현재 상태 정밀 분석 (0.5일)

**목표**: 재사용 가능한 코드 파악, Gap 정확히 식별

#### 1.1 기존 모듈 분석

존재하는 core 모듈 조사:
- `conversation_manager.py` ✅ 세션 관리 (재사용 가능)
- `embedding_service.py` ✅ 임베딩 생성 (재사용 가능)
- `document_loader.py` ✅ 문서 로딩 (재사용 가능)
- `metadata_filter.py` ✅ 메타데이터 필터링 (재사용 가능)
- `response_generator.py` ✅ 응답 생성 (재사용 가능)

누락된 모듈:
- `rag_engine.py` ❌ 신규 개발 필요
- `document_processor.py` ❌ 신규 개발 필요
- `vector_search.py` ❌ 신규 개발 필요

#### 1.2 의존성 확인

설치 필요:
```bash
pip install qdrant-client sentence-transformers docling ollama pytesseract
```

#### 1.3 데이터 구조 분석

```
data/crawled/chungjinkorea/crawled_products_final/
├── Bottle/ (675개 제품)
├── Jar/ (42개)
├── Cap/ (118개)
└── Pump/ (22개)

Total: 857 JSON files → 임베딩 대상
```

---

### Phase 2: 핵심 모듈 개발 (3-4일)

#### 2.1 VectorSearch 모듈 (1일)

**파일**: `src/core/vector_search.py`

**기능**:
- Qdrant 연결 및 컬렉션 관리
- 벡터 유사도 검색
- 하이브리드 검색 (벡터 + BM25)
- 메타데이터 필터링

**구현 골격**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class VectorSearch:
    def __init__(self, qdrant_url: str, collection_name: str):
        self.client = QdrantClient(qdrant_url)
        self.collection = collection_name

    def create_collection(self, vector_dim: int = 384):
        """컬렉션 생성"""
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(
                size=vector_dim,
                distance=Distance.COSINE
            )
        )

    def upsert(self, points: list):
        """벡터 업로드"""
        self.client.upsert(
            collection_name=self.collection,
            points=points
        )

    def search(self, query_vector: list, top_k: int = 10, filters: dict = None):
        """벡터 유사도 검색"""
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filters
        )
        return results
```

---

#### 2.2 DocumentProcessor 모듈 (1.5일)

**파일**: `src/core/document_processor.py`

**기능**:
- JSON/JSONL 파싱 (skill의 parser 재사용)
- 청킹 (skill의 chunker 재사용)
- 임베딩 생성
- 메타데이터 추출
- Qdrant 업로드

**구현 골격**:
```python
import sys
from pathlib import Path

# Skill 파서 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from .claude.skills.rag_pipeline.scripts.parsers import parse_document
from .claude.skills.rag_pipeline.scripts.chunking import get_chunker

class DocumentProcessor:
    def __init__(self, embedding_service, vector_search):
        self.embedding_service = embedding_service
        self.vector_search = vector_search
        self.chunker = get_chunker('semantic', chunk_size=512, overlap=50)

    def process_document(self, file_path: str, options: dict = None):
        """문서 처리 파이프라인"""
        # 1. Parse
        parse_result = parse_document(file_path, options or {})
        if not parse_result.success:
            return {"error": parse_result.error}

        # 2. Chunk
        chunks = self.chunker.chunk(
            parse_result.content,
            metadata={
                'file_path': file_path,
                **parse_result.metadata
            }
        )

        # 3. Embed
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(texts)

        # 4. Upload to Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append({
                'id': f"{Path(file_path).stem}_{i}",
                'vector': embedding,
                'payload': {
                    'text': chunk['text'],
                    'metadata': chunk['metadata']
                }
            })

        self.vector_search.upsert(points)

        return {
            "status": "success",
            "file_path": file_path,
            "chunks_created": len(chunks)
        }
```

**재사용**:
- `.claude/skills/rag-pipeline/scripts/parsers/` (100%)
- `.claude/skills/rag-pipeline/scripts/chunking/` (100%)
- `src/core/embedding_service.py` (수정 없이)

---

#### 2.3 RAGEngine 모듈 (1.5일)

**파일**: `src/core/rag_engine.py`

**기능**:
- Query → Retrieval → Generation 파이프라인
- 컨텍스트 포맷팅
- LLM 답변 생성 (Ollama)
- 신뢰도 계산

**구현 골격**:
```python
import requests
from typing import List, Dict, Any

class RAGEngine:
    def __init__(self, vector_search, embedding_service, ollama_url: str):
        self.vector_search = vector_search
        self.embedding_service = embedding_service
        self.ollama_url = ollama_url
        self.model = "qwen2.5:7b-instruct"

    def query(self, question: str, top_k: int = 5, use_rerank: bool = False):
        """RAG 쿼리 실행"""
        # 1. Embed query
        query_vector = self.embedding_service.embed(question)

        # 2. Vector search
        results = self.vector_search.search(query_vector, top_k=top_k)

        # 3. (Optional) Rerank
        if use_rerank:
            results = self._rerank(question, results)

        # 4. Generate answer
        context = self._format_context(results)
        answer = self._generate_answer(question, context)

        return {
            "answer": answer,
            "sources": results,
            "confidence": self._calculate_confidence(results)
        }

    def _format_context(self, results: List[Dict]) -> str:
        """검색 결과를 컨텍스트로 포맷"""
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result['payload']['text']}")
        return "\n\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """Ollama로 답변 생성"""
        prompt = f"""Context:
{context}

Question: {question}

Answer based on the context above (in Korean):"""

        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )

        return response.json()['response']

    def _calculate_confidence(self, results: List[Dict]) -> float:
        """신뢰도 계산"""
        if not results:
            return 0.0

        # 상위 결과의 평균 점수
        scores = [r.score for r in results]
        return sum(scores) / len(scores)
```

---

### Phase 3: 인프라 설정 (1일)

#### 3.1 Docker 환경 (0.5일)

**작업**:
1. Colima 실행
2. Qdrant 컨테이너 시작
3. 헬스체크

```bash
# Colima 시작
colima start --cpu 4 --memory 8

# Qdrant 실행
docker-compose up -d qdrant

# 확인
curl http://localhost:6333/
```

#### 3.2 Ollama 설정 (0.5일)

**작업**:
1. Ollama 설치
2. 모델 다운로드
3. 테스트

```bash
# 설치
brew install ollama

# 모델 다운로드 (4.7GB)
ollama pull qwen2.5:7b-instruct

# 테스트
ollama run qwen2.5:7b-instruct "What is PET plastic?"

# 백그라운드 실행
ollama serve &
```

---

### Phase 4: Skill 통합 및 테스트 (2일)

#### 4.1 Skill 코드 업데이트 (1일)

**파일**: `.claude/skills/rag-pipeline/scripts/skill.py`

**변경사항**:

```python
# Import core modules
from src.core.vector_search import VectorSearch
from src.core.document_processor import DocumentProcessor
from src.core.rag_engine import RAGEngine
from src.core.embedding_service import EmbeddingService

# Singletons
_vector_search = None
_document_processor = None
_rag_engine = None

def init_services():
    global _vector_search, _document_processor, _rag_engine

    if _vector_search is None:
        embedding_service = EmbeddingService()
        _vector_search = VectorSearch(
            qdrant_url="http://localhost:6333",
            collection_name="products"
        )
        _document_processor = DocumentProcessor(
            embedding_service,
            _vector_search
        )
        _rag_engine = RAGEngine(
            _vector_search,
            embedding_service,
            ollama_url="http://localhost:11434"
        )

def process_document(params):
    init_services()
    return _document_processor.process_document(
        params['file_path'],
        params.get('options')
    )

def vector_search(params):
    init_services()
    query_vector = _rag_engine.embedding_service.embed(params['query'])
    results = _vector_search.search(query_vector, params.get('top_k', 10))
    return {'results': results, 'query': params['query']}

def rag_query(params):
    init_services()
    return _rag_engine.query(
        params['question'],
        params.get('top_k', 5),
        params.get('use_rerank', False)
    )
```

#### 4.2 E2E 테스트 (1일)

**테스트 스크립트**: `tests/test_rag_skill_integration.py`

```python
import pytest
from pathlib import Path

def test_document_processing():
    """문서 처리 테스트"""
    from .claude.skills.rag_pipeline.scripts.skill import execute

    result = execute('process', {
        'file_path': 'data/crawled/chungjinkorea/crawled_products_final/Bottle/idx_1.json'
    })

    assert result['status'] == 'success'
    assert result['chunks_created'] > 0

def test_vector_search():
    """벡터 검색 테스트"""
    from .claude.skills.rag_pipeline.scripts.skill import execute

    result = execute('search', {
        'query': '50ml PET bottle',
        'top_k': 5
    })

    assert len(result['results']) > 0
    assert result['results'][0].score > 0.5

def test_rag_query():
    """RAG 쿼리 테스트"""
    from .claude.skills.rag_pipeline.scripts.skill import execute

    result = execute('query', {
        'question': 'What 50ml PET bottles are available?',
        'top_k': 5
    })

    assert 'answer' in result
    assert len(result['answer']) > 0
    assert len(result['sources']) > 0
    assert result['confidence'] > 0.3

def test_batch_processing():
    """배치 처리 테스트"""
    from .claude.skills.rag_pipeline.scripts.skill import execute

    product_files = list(
        Path('data/crawled/chungjinkorea/crawled_products_final/Bottle')
        .glob('*.json')
    )[:10]  # 처음 10개만

    result = execute('batch_process', {
        'file_paths': [str(f) for f in product_files],
        'batch_size': 5
    })

    assert result['successful'] == 10
    assert result['failed'] == 0
```

---

### Phase 5: 데이터 임베딩 및 배포 (1-2일)

#### 5.1 전체 데이터 임베딩 (0.5일)

**스크립트**: `scripts/embed_all_products.py`

```python
#!/usr/bin/env python3
from pathlib import Path
from tqdm import tqdm
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from .claude.skills.rag_pipeline.scripts.skill import execute

def embed_all_products():
    product_root = Path('data/crawled/chungjinkorea/crawled_products_final')

    # 모든 JSON 파일 수집
    json_files = []
    for category in ['Bottle', 'Jar', 'Cap', 'Pump']:
        json_files.extend(list((product_root / category).glob('*.json')))

    print(f"Found {len(json_files)} products")

    # 배치 처리
    batch_size = 50
    for i in tqdm(range(0, len(json_files), batch_size)):
        batch = json_files[i:i+batch_size]

        result = execute('batch_process', {
            'file_paths': [str(f) for f in batch],
            'batch_size': batch_size,
            'parallel': True
        })

        print(f"Batch: {result['successful']}/{len(batch)} succeeded")

if __name__ == '__main__':
    embed_all_products()
```

**실행**:
```bash
python3 scripts/embed_all_products.py
```

#### 5.2 Frontend 통합 (0.5일)

**파일 수정**: `src/api/chat.py`

```python
# 환경 변수로 전환 가능
USE_RAG_SKILL = os.getenv('USE_RAG_SKILL', 'false') == 'true'

@router.post("/query")
async def chat_query(request: ChatQueryRequest):
    if USE_RAG_SKILL:
        # 새 RAG Skill 사용
        from .claude.skills.rag_pipeline.scripts.skill import execute

        result = execute('query', {
            'question': request.query,
            'top_k': 10,
            'use_rerank': True
        })

        return ChatQueryResponse(
            session_id=request.session_id,
            query=request.query,
            response=result['answer'],
            products=result['sources'],
            ...
        )
    else:
        # 기존 방식 (파일 기반)
        contextual_rag = get_contextual_rag()
        result = await contextual_rag.query(
            session_id=request.session_id,
            user_query=request.query
        )
        return ChatQueryResponse(**result)
```

**A/B 테스트**:
```bash
# 기존 시스템
USE_RAG_SKILL=false python run_chat_server.py

# 새 RAG Skill
USE_RAG_SKILL=true python run_chat_server.py
```

---

## 📊 리소스 요구사항

### 개발 시간
| Phase | 시간 | 난이도 |
|-------|------|--------|
| Phase 1: 분석 | 0.5일 | Easy |
| Phase 2: 개발 | 3-4일 | Hard |
| Phase 3: 인프라 | 1일 | Medium |
| Phase 4: 통합 | 2일 | Medium |
| Phase 5: 배포 | 1-2일 | Easy |
| **Total** | **7.5-9.5일** | - |

### 시스템 리소스 (MacBook Air M4 24GB)
```
Component                  RAM Usage
─────────────────────────────────────
Embedding Model            500MB
Reranking Model            200MB
Ollama (qwen2.5:7b)        4GB
Qdrant                     2-3GB
Backend Services           1-2GB
System + Buffer            6-8GB
─────────────────────────────────────
Total                      14-15GB (58%)
Free                       9-10GB (42%) ✅
```

### 디스크 용량
```
Component                  Disk Usage
─────────────────────────────────────
Ollama Model               4.7GB
Embeddings (857개)         ~50MB
Qdrant Indexes             ~100MB
Logs & Cache               ~50MB
─────────────────────────────────────
Total                      ~5GB
```

---

## 🎯 우선순위 및 Risk

### Critical Path
```
Phase 2.1 (VectorSearch)
    ↓
Phase 2.2 (DocumentProcessor)
    ↓
Phase 3 (Infrastructure)
    ↓
Phase 4.2 (E2E Test)
```

### Risks

#### High Risk
1. **Qdrant 연결 실패**
   - Mitigation: Docker 환경 사전 테스트
   - Fallback: ChromaDB로 전환

2. **임베딩 품질 낮음**
   - Mitigation: 여러 모델 A/B 테스트
   - Fallback: OpenAI embeddings (유료)

#### Medium Risk
3. **성능 이슈 (검색 > 500ms)**
   - Mitigation: HNSW 파라미터 튜닝
   - Fallback: 캐싱 강화

4. **메모리 부족 (> 24GB)**
   - Mitigation: 모델 양자화 (4-bit)
   - Fallback: 클라우드 배포

---

## 💡 권장 전략: Hybrid Approach

**전략**: 기존 시스템 + 벡터 검색 병행

```python
class HybridSearch:
    def search(self, query, use_vector=True, use_file=True):
        results = []

        # 벡터 검색
        if use_vector:
            vector_results = self.vector_search.search(query)
            results.extend(vector_results)

        # 파일 기반 검색 (기존)
        if use_file:
            file_results = self.contextual_rag._search_products(query)
            results.extend(file_results)

        # 중복 제거 및 점수 병합
        return self._merge_results(results)
```

**장점**:
- ✅ 점진적 마이그레이션
- ✅ 롤백 가능
- ✅ 성능 비교 가능

---

## 🚀 Quick Start

**Phase 1 즉시 시작**:

```bash
# 1. 의존성 설치
pip install qdrant-client sentence-transformers docling pytesseract

# 2. Colima 시작
colima start --cpu 4 --memory 8

# 3. Qdrant 실행
docker-compose up -d qdrant

# 4. Ollama 설치
brew install ollama
ollama pull qwen2.5:7b-instruct

# 5. 모듈 생성
mkdir -p src/core
touch src/core/vector_search.py
touch src/core/document_processor.py
touch src/core/rag_engine.py
```

---

## 📈 성공 기준

### Phase 2 완료
- [ ] VectorSearch: Qdrant 연결 및 검색 작동
- [ ] DocumentProcessor: JSON → 임베딩 → Qdrant 작동
- [ ] RAGEngine: Query → Generation 작동

### Phase 4 완료
- [ ] Skill 통합: `execute('query')` 실제 답변 반환
- [ ] E2E 테스트: 모든 테스트 통과
- [ ] 성능: 검색 < 100ms, 생성 < 2s

### Phase 5 완료
- [ ] 857개 제품 100% 임베딩
- [ ] Frontend 연동 완료
- [ ] A/B 테스트 완료

---

## 📝 Next Actions

**즉시 실행 가능**:

1. **Phase 1 시작** → 의존성 설치 및 인프라 준비
2. **VectorSearch 개발** → src/core/vector_search.py 구현
3. **테스트 작성** → tests/test_vector_search.py 작성

**승인 필요**: 이 전략으로 진행할까요?
