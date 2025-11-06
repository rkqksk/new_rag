# 로컬 테스트 가이드

**목적**: Phase 0-9 모든 기능을 로컬 환경에서 테스트
**소요 시간**: 15-30분
**난이도**: ⭐ (초급)

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [빠른 시작](#빠른-시작)
3. [단계별 테스트](#단계별-테스트)
4. [Phase별 기능 테스트](#phase별-기능-테스트)
5. [문제 해결](#문제-해결)

---

## 사전 요구사항

### 필수 소프트웨어

- **Docker Desktop**: [다운로드](https://www.docker.com/products/docker-desktop/)
- **Git**: [다운로드](https://git-scm.com/downloads)
- **Python 3.11+** (선택, 로컬 개발용): [다운로드](https://www.python.org/downloads/)

### 시스템 요구사항

- **OS**: Windows 10/11, macOS, Linux
- **RAM**: 최소 8GB (권장 16GB)
- **디스크**: 20GB 여유 공간
- **CPU**: 4코어 이상 권장

---

## 빠른 시작

### 1. 프로젝트 Clone

```bash
# 프로젝트 clone
git clone https://github.com/YOUR_USERNAME/rag-enterprise.git
cd rag-enterprise

# 또는 특정 브랜치
git clone -b claude/update-roadmap-docs-011CUrG78orz1eVFXPNVyige \
  https://github.com/YOUR_USERNAME/rag-enterprise.git
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# Windows
copy .env.example .env
```

**기본 설정으로 충분합니다!** (필요시 수정)

### 3. Docker Compose 실행

```bash
# 전체 시스템 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 상태 확인
docker-compose ps
```

**예상 출력**:
```
NAME                COMMAND                  SERVICE    STATUS
rag-api-1           "uvicorn app.main:ap…"   api        Up
rag-postgres-1      "docker-entrypoint.s…"   postgres   Up
rag-qdrant-1        "./qdrant"               qdrant     Up
rag-redis-1         "docker-entrypoint.s…"   redis      Up
```

### 4. 헬스 체크

```bash
# API 헬스 체크
curl http://localhost:8001/health/ready

# 또는 브라우저에서
# http://localhost:8001/health/ready
```

**성공 응답**:
```json
{
  "status": "healthy",
  "qdrant": "connected",
  "postgres": "connected",
  "redis": "connected"
}
```

### 5. 프론트엔드 접속

#### 옵션 1: 간단한 HTTP 서버 (Python)

```bash
cd frontend
python3 -m http.server 8080

# 또는 Python 2
python -m SimpleHTTPServer 8080
```

브라우저에서 접속:
```
http://localhost:8080/chat.html
```

#### 옵션 2: VS Code Live Server

1. VS Code에서 `frontend/chat.html` 열기
2. 우클릭 → "Open with Live Server"

#### 옵션 3: 직접 파일 열기

브라우저에서 직접 열기:
```
file:///path/to/rag-enterprise/frontend/chat.html
```

**⚠️ CORS 문제가 발생할 수 있습니다. 옵션 1이나 2를 권장합니다.**

---

## 단계별 테스트

### Step 1: API 문서 확인

브라우저에서 접속:
```
http://localhost:8001/api/v1/docs
```

**Swagger UI**에서 모든 API 엔드포인트 확인 가능:
- `/api/v1/search/` - 검색
- `/api/v1/stream/subscribe` - SSE 스트리밍
- `/api/v1/debug/*` - 디버그 엔드포인트

### Step 2: 기본 검색 테스트

#### cURL 사용:

```bash
# 기본 검색
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "100ml PET 병",
    "top_k": 5
  }'
```

#### Python 사용:

```python
import requests

response = requests.post(
    "http://localhost:8001/api/v1/search/",
    json={
        "query": "100ml PET 병",
        "top_k": 5
    }
)

print(response.json())
```

#### Swagger UI 사용:

1. `http://localhost:8001/api/v1/docs` 접속
2. `/api/v1/search/` 클릭
3. "Try it out" 버튼 클릭
4. 쿼리 입력 후 "Execute"

### Step 3: 데이터 로드 (처음 한 번만)

```bash
# 제품 데이터 임베딩 생성
docker-compose exec api python scripts/embed_all_products.py

# 또는 로컬에서 (Python 설치 필요)
python scripts/embed_all_products.py
```

**진행 상황**:
```
Processing products: 100%|████████| 471/471
Created 3,246 chunks
Uploaded to Qdrant
✅ Complete!
```

### Step 4: 프론트엔드 테스트

1. `http://localhost:8080/chat.html` 접속
2. 검색어 입력: "100ml PET 병"
3. 결과 확인

**테스트 쿼리**:
- "100ml PET 병"
- "50ml PP 용기"
- "펌프 디스펜서"
- "200ml 화장품 용기"

---

## Phase별 기능 테스트

### Phase 0-4: 기본 RAG 시스템 ✅

#### 1. 제품 검색
```bash
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "100ml PET 병", "top_k": 5}'
```

#### 2. 원자적 청킹 확인
```bash
# 청크 정보 조회
curl http://localhost:8001/api/v1/debug/chunks/stats
```

#### 3. OCR 처리 (Phase 4)
```python
from src.core.ocr import DocumentProcessor

processor = DocumentProcessor(use_gpu=False)

# PDF 처리
result = processor.process_file('path/to/catalog.pdf')
print(result.text)

# 이미지 처리
result = processor.process_file('path/to/product.jpg')
print(result.entities)
```

---

### Phase 5: Advanced RAG Integration ✅

#### 1. Multi-Source Search 테스트

**Python 코드**:
```python
from src.core.advanced_rag import IntegratedRAGPipeline

# Pipeline 초기화
pipeline = IntegratedRAGPipeline(
    vector_store=vector_store,
    embedder=embedder
)

# Multi-source 검색
response = await pipeline.search(
    query="100ml PET 병 사용설명서",
    top_k=20
)

print(f"Found {len(response.results)} results")
print(f"Sources used: {response.sources_used}")
print(f"Search time: {response.total_time_ms}ms")
```

#### 2. Query Router 테스트

```python
from src.core.advanced_rag import AdvancedQueryRouter

router = AdvancedQueryRouter()

# 쿼리 분석
intent = router.analyze_query("100ml PET 병 MOQ 1000개")

print(f"Query type: {intent.query_type}")
print(f"Entities: {intent.entities}")
print(f"Target collections: {intent.target_collections}")
```

#### 3. Score Fusion 테스트

```python
from src.core.advanced_rag import ScoreFusion, FusionStrategy

fusion = ScoreFusion()

# 여러 소스의 결과 융합
fused = fusion.fuse_scores(
    search_results={
        'products': product_results,
        'documents': doc_results
    },
    weights={'products': 0.7, 'documents': 0.3},
    strategy=FusionStrategy.RRF
)

print(f"Fused {len(fused.items)} results")
```

---

### Phase 6: Multi-Modal Search ✅

#### 1. Shape Embedding 테스트

```python
from src.core.shape_processors import ShapeEmbedder
from PIL import Image

embedder = ShapeEmbedder(embedding_dim=128)

# 이미지에서 형상 임베딩 추출
image = Image.open('product.jpg')
shape_embedding = embedder.encode_shape(image)

print(f"Shape embedding: {shape_embedding.shape}")  # (128,)
print(f"Features: Hu Moments(7) + Fourier(32) + Metrics(3)")
```

#### 2. Image Matching 테스트

```python
from src.core.multimodal import ImageMatchingService

service = ImageMatchingService(
    qdrant_client=client,
    image_embedder=image_embedder,
    shape_embedder=shape_embedder
)

# 유사 이미지 검색
query_image = Image.open('query.jpg')
matches = await service.find_similar(query_image, top_k=10)

for match in matches:
    print(f"Product: {match.product_id}")
    print(f"Visual score: {match.visual_score:.3f}")
    print(f"Shape score: {match.shape_score:.3f}")
    print(f"Combined: {match.combined_score:.3f}")
```

#### 3. Tri-Modal Search 테스트

```python
from src.core.multimodal import TriModalSearchService, SearchQuery

service = TriModalSearchService(
    qdrant_client=client,
    text_embedder=text_embedder,
    image_embedder=image_embedder,
    shape_embedder=shape_embedder
)

# 텍스트 + 이미지 검색
query = SearchQuery(
    text="100ml PET 병",
    image=Image.open('product.jpg'),
    use_shape=True
)

results = await service.search(query, top_k=10)

for result in results:
    print(f"Product: {result.product_id}")
    print(f"Text: {result.text_score:.3f}")
    print(f"Visual: {result.visual_score:.3f}")
    print(f"Shape: {result.shape_score:.3f}")
    print(f"Combined: {result.combined_score:.3f}")
```

---

### Phase 7: Cloud Data Integration ✅

#### 1. Google Drive Integration

```python
from src.integrations import GoogleDriveIntegration

# 초기화
drive = GoogleDriveIntegration(
    credentials_path="credentials.json"
)

# 인증 (브라우저에서 OAuth 진행)
await drive.authenticate()

# 파일 목록
files = await drive.list_files(
    folder_id="your-folder-id",
    mime_type="application/pdf"
)

print(f"Found {len(files)} PDF files")

# 파일 다운로드
results = await drive.download_files(
    files,
    output_dir="./downloads"
)
```

#### 2. S3 Integration

```python
from src.integrations import S3Integration

# 초기화
s3 = S3Integration(
    aws_access_key_id="YOUR_KEY",
    aws_secret_access_key="YOUR_SECRET",
    region="us-east-1"
)

# 객체 목록
objects = await s3.list_objects(
    bucket="my-bucket",
    prefix="products/",
    suffix=".pdf"
)

print(f"Found {len(objects)} objects")

# 다운로드
results = await s3.download_objects(
    objects,
    output_dir="./downloads"
)
```

#### 3. Automated Pipeline

```python
from src.integrations import AutomatedDataPipeline, PipelineConfig

# Pipeline 설정
pipeline = AutomatedDataPipeline(
    google_drive=drive,
    s3=s3,
    processor=processor,
    vector_store=vector_store
)

# 설정
config = PipelineConfig(
    source_type='google_drive',
    source_params={'folder_id': 'abc123'},
    file_types=['pdf', 'image'],
    output_dir='/data/pipeline',
    collection_name='products_multimodal',
    incremental=True
)

# 실행
result = await pipeline.run(config)

print(f"Downloaded: {result.download_success} files")
print(f"Processed: {result.processing_success} files")
print(f"Vectors: {result.vectors_uploaded}")
```

---

### Phase 8: Real-Time Streaming ✅

#### 1. SSE (Server-Sent Events) 테스트

**JavaScript (브라우저)**:
```javascript
// SSE 연결
const eventSource = new EventSource(
    'http://localhost:8001/api/v1/stream/subscribe?channels=search,analytics'
);

// 검색 결과 이벤트
eventSource.addEventListener('search_result', (event) => {
    const data = JSON.parse(event.data);
    console.log('Search result:', data);
});

// 분석 업데이트 이벤트
eventSource.addEventListener('analytics_update', (event) => {
    const data = JSON.parse(event.data);
    console.log('Analytics:', data);
    updateDashboard(data);
});

// 킵얼라이브
eventSource.addEventListener('keepalive', (event) => {
    console.log('Connection alive');
});
```

**cURL 테스트**:
```bash
# SSE 스트림 수신 (Ctrl+C로 중단)
curl -N http://localhost:8001/api/v1/stream/subscribe?channels=search
```

#### 2. Analytics Dashboard

```python
from src.streaming import RealTimeAnalytics

# 초기화
analytics = RealTimeAnalytics(sse_manager=sse_manager)

# 메트릭 기록
await analytics.record('search_latency', 45.2)
await analytics.increment('search_count')

# 타이머 사용
from src.streaming import Timer

async with Timer(analytics, 'search_duration'):
    results = await search(query)

# 스트리밍 시작
await analytics.start_streaming(interval=5)

# 대시보드 데이터 조회
dashboard = await analytics.get_dashboard()
print(dashboard)
```

#### 3. SSE Manager

```python
from src.streaming import SSEManager

manager = SSEManager()

# 이벤트 전송
await manager.emit(
    channel="search",
    event="search_result",
    data={
        "query": "100ml PET",
        "results": [...],
        "timestamp": "2025-11-06T10:30:00"
    }
)

# 통계 확인
stats = manager.get_stats()
print(f"Active connections: {stats['active_connections']}")
```

---

### Phase 9: Enterprise Deployment (로컬에서는 일부만) ✅

#### 1. CI/CD 워크플로우 확인

```bash
# GitHub Actions 워크플로우 파일 확인
cat .github/workflows/ci.yaml
cat .github/workflows/cd.yaml
```

#### 2. Kubernetes 매니페스트 확인

```bash
# K8s 매니페스트 검증
ls k8s/

# ConfigMap 확인
cat k8s/configmap.yaml

# Deployment 확인
cat k8s/api-deployment.yaml
```

#### 3. Prometheus 메트릭 (Docker Compose로 테스트 가능)

API에 메트릭 추가:
```python
from prometheus_client import Counter, Histogram

# Counter
search_queries = Counter(
    'search_queries_total',
    'Total search queries'
)

# Histogram
search_latency = Histogram(
    'search_latency_seconds',
    'Search latency'
)

# 사용
search_queries.inc()
with search_latency.time():
    results = search(query)
```

메트릭 확인:
```bash
curl http://localhost:8001/metrics
```

---

## 통합 테스트 시나리오

### 시나리오 1: 전체 검색 파이프라인

```python
import asyncio
from src.core.advanced_rag import IntegratedRAGPipeline
from src.core.multimodal import TriModalSearchService, SearchQuery
from PIL import Image

async def test_full_pipeline():
    # 1. 텍스트 검색
    print("=== Text Search ===")
    response = await rag_pipeline.search(
        query="100ml PET 병",
        top_k=10
    )
    print(f"Found {len(response.results)} results")

    # 2. 이미지 검색
    print("\n=== Image Search ===")
    query = SearchQuery(
        image=Image.open('product.jpg'),
        use_shape=True
    )
    results = await trimodal_service.search(query, top_k=10)
    print(f"Found {len(results)} visual matches")

    # 3. 하이브리드 검색
    print("\n=== Hybrid Search ===")
    query = SearchQuery(
        text="100ml PET 병",
        image=Image.open('product.jpg')
    )
    results = await trimodal_service.search(query, top_k=10)
    print(f"Found {len(results)} hybrid matches")

asyncio.run(test_full_pipeline())
```

### 시나리오 2: 실시간 분석 대시보드

```python
import asyncio
from src.streaming import RealTimeAnalytics, SSEManager

async def test_analytics():
    # SSE Manager 및 Analytics 초기화
    sse_manager = SSEManager()
    analytics = RealTimeAnalytics(sse_manager=sse_manager)

    # 스트리밍 시작
    await analytics.start_streaming(interval=5)

    # 메트릭 시뮬레이션
    for i in range(100):
        await analytics.record('search_latency', 40 + i * 0.5)
        await analytics.increment('search_count')
        await asyncio.sleep(0.1)

    # 대시보드 데이터
    dashboard = await analytics.get_dashboard()
    print(f"Total searches: {dashboard['counters']['search_count']}")
    print(f"Avg latency: {dashboard['timers']['search_latency']['avg']:.2f}ms")
    print(f"P95 latency: {dashboard['timers']['search_latency']['p95']:.2f}ms")

asyncio.run(test_analytics())
```

### 시나리오 3: 클라우드 → RAG 파이프라인

```python
import asyncio
from src.integrations import AutomatedDataPipeline, PipelineConfig

async def test_cloud_pipeline():
    # Pipeline 초기화
    pipeline = AutomatedDataPipeline(
        google_drive=drive,
        s3=s3,
        processor=ocr_processor,
        vector_store=qdrant_uploader,
        embedder=embedder
    )

    # 설정
    config = PipelineConfig(
        source_type='s3',
        source_params={
            'bucket': 'my-bucket',
            'prefix': 'products/'
        },
        file_types=['pdf', 'image'],
        output_dir='/tmp/pipeline',
        collection_name='products_multimodal',
        incremental=True
    )

    # 실행
    result = await pipeline.run(config)

    print(f"Pipeline Results:")
    print(f"  Downloaded: {result.download_success}/{result.files_downloaded}")
    print(f"  Processed: {result.processing_success}/{result.files_processed}")
    print(f"  Chunks: {result.chunks_created}")
    print(f"  Vectors: {result.vectors_uploaded}")
    print(f"  Duration: {result.duration_seconds:.1f}s")

asyncio.run(test_cloud_pipeline())
```

---

## 성능 벤치마크

### 검색 성능 테스트

```python
import time
import asyncio

async def benchmark_search(queries, iterations=100):
    times = []

    for _ in range(iterations):
        query = random.choice(queries)
        start = time.time()

        await rag_pipeline.search(query, top_k=10)

        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

    print(f"Search Performance:")
    print(f"  Mean: {sum(times) / len(times):.2f}ms")
    print(f"  P50: {sorted(times)[len(times)//2]:.2f}ms")
    print(f"  P95: {sorted(times)[int(len(times)*0.95)]:.2f}ms")
    print(f"  P99: {sorted(times)[int(len(times)*0.99)]:.2f}ms")

queries = [
    "100ml PET 병",
    "50ml PP 용기",
    "펌프 디스펜서",
    "200ml 화장품 용기"
]

asyncio.run(benchmark_search(queries))
```

---

## 문제 해결

### 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker-compose logs api

# 재시작
docker-compose restart api

# 완전 재시작
docker-compose down
docker-compose up -d
```

### 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
# Linux/Mac
lsof -i :8001
lsof -i :6333

# Windows
netstat -ano | findstr :8001

# 프로세스 종료 후 재시작
docker-compose down
docker-compose up -d
```

### 메모리 부족

```bash
# Docker 메모리 할당 증가
# Docker Desktop → Settings → Resources → Memory: 8GB

# 불필요한 컨테이너 정리
docker system prune -a
```

### CORS 에러

프론트엔드에서 API 호출 시 CORS 에러가 발생하면:

1. `.env` 파일에 추가:
```bash
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
CORS_ENABLED=true
```

2. 재시작:
```bash
docker-compose restart api
```

### 데이터가 없을 때

```bash
# 제품 데이터 임베딩
docker-compose exec api python scripts/embed_all_products.py

# 또는 샘플 데이터 로드
docker-compose exec api python scripts/load_sample_data.py
```

---

## 다음 단계

로컬 테스트가 완료되었다면:

1. **자체 데이터 추가**: 제품 데이터를 추가하여 시스템 확장
2. **커스터마이징**: 검색 가중치, 임베딩 모델 등 조정
3. **프로덕션 배포**: `docs/SELF_HOSTED_DEPLOYMENT.md` 참조
4. **모니터링 설정**: Prometheus + Grafana 구성

---

## 유용한 명령어 모음

```bash
# 전체 시스템 시작
docker-compose up -d

# 로그 실시간 확인
docker-compose logs -f api

# 특정 컨테이너 재시작
docker-compose restart api

# 전체 시스템 중지
docker-compose down

# 볼륨 포함 완전 삭제
docker-compose down -v

# 컨테이너 상태 확인
docker-compose ps

# 리소스 사용량
docker stats

# API 컨테이너 접속
docker-compose exec api bash

# PostgreSQL 접속
docker-compose exec postgres psql -U rag_user rag_enterprise

# Redis 접속
docker-compose exec redis redis-cli
```

---

## 체크리스트

- [ ] Docker Desktop 실행
- [ ] 프로젝트 clone
- [ ] `.env` 파일 생성
- [ ] `docker-compose up -d` 실행
- [ ] 헬스 체크 통과
- [ ] 데이터 로드 (embed_all_products.py)
- [ ] 프론트엔드 접속 확인
- [ ] API 검색 테스트
- [ ] SSE 스트리밍 테스트
- [ ] Phase별 기능 테스트

---

**모든 기능이 정상 작동하면 로컬 테스트 완료! 🎉**

문제가 있으면 GitHub Issues에 문의하거나 로그를 확인하세요.
