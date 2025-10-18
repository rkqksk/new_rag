# Step 2: Data Ingestion System - 완료

## 📋 요약

**Step 2 (Data Ingestion System)가 완전히 구현되었습니다.**

### 구현된 기능
- ✅ 다중 형식 문서 업로드 (PDF, Excel, Images, HTML, Text)
- ✅ 웹 크롤링 시스템 (정기적 데이터 수집)
- ✅ 자동 청킹 및 임베딩
- ✅ Qdrant 벡터 저장소 연동
- ✅ RESTful API 엔드포인트

---

## 🏗️ 구현된 컴포넌트

### 1. DocumentIngestionService (`app/services/document_ingestion_service.py`)

**역할**: 다양한 형식의 문서를 처리하고 벡터화

**주요 기능**:
```python
# 다중 형식 지원
- PDF 파싱: unstructured 라이브러리 기반
- Excel 처리: Pandas 데이터프레임으로 변환
- 이미지 OCR: EasyOCR 기반 텍스트 추출
- HTML 크롤링: BeautifulSoup 파싱
- 텍스트 파일: 고정 크기 청킹

# 핵심 메서드
- ingest_file(): 파일 업로드 및 처리
- search_documents(): 벡터 기반 검색
- get_collection_stats(): 통계 조회
```

**처리 파이프라인**:
```
📄 파일 업로드
    ↓
🔍 형식 감지 (PDF/Excel/Image 등)
    ↓
📚 문서 파싱 (형식별 처리)
    ↓
✂️ 청킹 (512 토큰 단위, 50 토큰 중복)
    ↓
🧠 Embedding (Sentence-Transformers)
    ↓
💾 Qdrant 저장 (384차원 벡터)
    ↓
✅ 완료 (doc_id, chunks_count 반환)
```

### 2. WebCrawlerService (`app/services/web_crawler_service.py`)

**역할**: 웹사이트에서 제조업 관련 데이터 자동 수집

**주요 기능**:
```python
# 크롤링 소스 타입
- product: 제품 카탈로그 정보
- msds: 화학물질 안전정보 (MSDS)
- supplier: 공급업체 정보
- generic: 일반 웹 콘텐츠

# 핵심 메서드
- crawl_source(): 특정 소스 크롤링
- crawl_all_sources(): 모든 소스 크롤링
- add_source(): 새로운 크롤링 소스 추가
- get_crawl_history(): 크롤링 히스토리 조회

# 렌더링 방식
- HTTP: 정적 페이지 (BeautifulSoup)
- Selenium: JavaScript 동적 페이지 (Chrome headless)
```

**기본 크롤링 소스**:
- 제품 카탈로그 (product)
- PubChem MSDS DB (msds)
- 공급업체 디렉토리 (supplier)

### 3. API 엔드포인트 (`app/api/ingestion_routes.py`)

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/v1/ingestion/documents/upload` | 문서 파일 업로드 |
| POST | `/api/v1/ingestion/crawler/source/add` | 크롤링 소스 추가 |
| POST | `/api/v1/ingestion/crawler/start` | 웹 크롤링 시작 |
| GET | `/api/v1/ingestion/crawler/sources` | 크롤링 소스 목록 |
| GET | `/api/v1/ingestion/crawler/history` | 크롤링 히스토리 |
| POST | `/api/v1/ingestion/search` | 문서 검색 |
| GET | `/api/v1/ingestion/stats` | 시스템 통계 |

---

## 📌 API 사용 예시

### 1. 문서 업로드

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/documents/upload \
  -F "file=@product_catalog.pdf" \
  -F "doc_type=pdf" \
  -F "custom_metadata={\"source\": \"catalog\", \"version\": \"2025-01\"}"

# 응답:
{
  "status": "success",
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "doc_type": "pdf",
  "file_name": "product_catalog.pdf",
  "chunks_count": 42,
  "vectors_stored": 42,
  "message": "Document processed successfully: 42 chunks",
  "processed_at": "2025-10-17T08:30:00"
}
```

### 2. 크롤링 소스 추가

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/crawler/source/add \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "msds_pubchem",
    "url": "https://pubchem.ncbi.nlm.nih.gov",
    "name": "PubChem MSDS Database",
    "category": "msds",
    "selectors": {
      "chemical_name": ".compound-title",
      "properties": ".section-content"
    }
  }'

# 응답:
{
  "status": "success",
  "source_id": "msds_pubchem",
  "message": "Source added: PubChem MSDS Database"
}
```

### 3. 웹 크롤링 시작

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/crawler/start \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "product_catalog",
    "use_selenium": false
  }'

# 응답 (백그라운드 작업):
{
  "status": "started",
  "task_id": "crawl_1697536200.123456",
  "source_id": "product_catalog",
  "message": "Crawler started (task_id: crawl_1697536200.123456)"
}
```

### 4. 문서 검색

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "50mm 용기 추천",
    "top_k": 5
  }'

# 응답:
{
  "query": "50mm 용기 추천",
  "results_count": 3,
  "results": [
    {
      "score": 0.87,
      "chunk_id": "chunk-001",
      "doc_id": "550e8400-...",
      "text": "50미리 용기는 소량 상품용으로 인기 있는 제품입니다...",
      "metadata": {...},
      "created_at": "2025-10-17T08:20:00"
    },
    ...
  ],
  "timestamp": "2025-10-17T08:35:00"
}
```

### 5. 시스템 통계

```bash
curl http://localhost:8000/api/v1/ingestion/stats

# 응답:
{
  "status": "success",
  "document_stats": {
    "collection_name": "documents",
    "points_count": 247,
    "vectors_count": 247,
    "vector_size": 384,
    "indexed": 247
  },
  "crawler_stats": {
    "total_sources": 3,
    "crawl_history_count": 5,
    "last_crawl": "2025-10-17T08:30:00"
  },
  "timestamp": "2025-10-17T08:35:00"
}
```

---

## 🔧 기술 세부사항

### 지원되는 문서 형식

| 형식 | 라이브러리 | 처리 방식 |
|------|-----------|---------|
| PDF | unstructured, pdfminer | 텍스트 추출, 테이블 감지 |
| Excel | pandas, openpyxl | 행/열 기반 변환 |
| CSV | pandas | 데이터프레임 변환 |
| 이미지 | unstructured, EasyOCR | OCR 텍스트 추출 |
| HTML | BeautifulSoup | DOM 파싱 |
| 텍스트 | 내장 | 고정 크기 청킹 |

### 청킹 전략

```python
# 청크 설정
chunk_size = 512 토큰 (약 1,000-1,500 문자)
chunk_overlap = 50 토큰 (컨텍스트 중복)

# 청킹 방식
1. 토큰 기반: 단어 * 1.3 계수로 토큰 추정
2. 슬라이딩 윈도우: 청크 간 50 토큰 중복 유지
3. 의미 보존: 문장/테이블 경계 존중

# 결과
→ 각 청크는 독립적으로 임베딩
→ 컨텍스트 보존으로 검색 정확도 향상
```

### 벡터 저장소 (Qdrant)

```
컬렉션: "documents"
├─ 벡터 크기: 384 차원 (Sentence-Transformers)
├─ 거리 메트릭: COSINE 유사도
├─ 인덱싱: HNSW (근사 최근방 그래프)
└─ 페이로드:
    ├─ chunk_id: 청크 고유 ID
    ├─ doc_id: 문서 ID
    ├─ text: 청크 텍스트
    ├─ chunk_index: 청크 순서
    ├─ metadata: 사용자 정의 메타데이터
    └─ created_at: 생성 시각
```

---

## 📊 워크플로우 흐름도

```
┌──────────────────────────────────────────┐
│   Document Ingestion System              │
└────┬─────────────────────────────────────┘
     │
     ├─ 📤 API: POST /documents/upload
     │   ├─ 파일 수신 (PDF, Excel, Image, etc.)
     │   ├─ 형식 감지 자동화
     │   ├─ DocumentIngestionService 호출
     │   └─ 결과 반환 (doc_id, chunks_count)
     │
     ├─ 🕷️ API: POST /crawler/start
     │   ├─ 크롤링 소스 선택
     │   ├─ WebCrawlerService.crawl_source() 호출
     │   ├─ HTTP 또는 Selenium 선택
     │   ├─ 데이터 추출 및 파싱
     │   └─ BackgroundTask 실행
     │
     ├─ 🔍 API: POST /search
     │   ├─ 쿼리 임베딩
     │   ├─ Qdrant 벡터 검색
     │   ├─ 유사도 점수 계산 (COSINE)
     │   └─ Top-K 결과 반환
     │
     └─ 📈 API: GET /stats
         ├─ 저장된 문서 통계
         ├─ 크롤링 히스토리
         └─ 시스템 상태
```

---

## 🚀 다음 단계 (Step 3)

### Web Interface 구현 예정
1. **문서 관리 대시보드**
   - 업로드된 문서 목록
   - 문서별 청크 시각화
   - 통계 및 메트릭

2. **크롤러 관리 UI**
   - 크롤링 소스 CRUD
   - 크롤링 스케줄 설정
   - 실시간 진행 상황

3. **검색 인터페이스**
   - 검색 쿼리 입력
   - 유사도 점수 시각화
   - 결과 상세 보기

4. **모니터링 대시보드**
   - 시스템 상태 모니터링
   - 임베딩 처리 성능
   - 에러 로그 조회

---

## 💡 설계 특징

### 확장성
- 새로운 문서 형식 추가 용이 (`_process_<format>()` 메서드)
- 크롤링 소스 동적 추가
- 임베딩 모델 교체 가능

### 성능
- 배치 임베딩 (다중 청크 동시 처리)
- 비동기 I/O (aiohttp)
- 백그라운드 크롤링 작업
- Qdrant HNSW 인덱싱 (빠른 검색)

### 안정성
- 에러 핸들링 (try-except)
- 로깅 (DEBUG, INFO, ERROR)
- 임시 파일 자동 정리
- 메타데이터 보존

---

## 📝 주요 파일 목록

```
app/services/
├─ document_ingestion_service.py    (450 lines) - 문서 처리 엔진
└─ web_crawler_service.py           (400 lines) - 웹 크롤링 엔진

app/api/
└─ ingestion_routes.py              (350 lines) - REST API 엔드포인트

app/api/
└─ main.py                          (Updated) - 서비스 통합 및 라우터 등록
```

---

## ✅ 테스트 & 검증

### 테스트 방법

```bash
# 1. 문서 업로드 테스트
python tests/test_document_ingestion.py

# 2. 크롤링 테스트
python tests/test_web_crawler.py

# 3. API 통합 테스트
python tests/test_ingestion_api.py

# 4. 실시간 시스템 테스트
curl http://localhost:8000/api/v1/ingestion/stats
```

---

## 📌 관련 문서

- `TEACHER_STUDENT_ARCHITECTURE.md` - Teacher-Student LLM 구조
- `DATA_FLOW_FOR_TRAINING.md` - 훈련 데이터 흐름
- `FINETUNING_DEPLOYMENT_STRATEGY.md` - 배포 전략

---

**Status**: ✅ **COMPLETE**
**Implemented**: 2025-10-17
**Last Updated**: 2025-10-17

---

## 🔗 Ollama 모델 상태

- ✅ **Qwen2.5:7B** - 다운로드 완료 (4.7GB)
- 🔄 **Qwen2.5:3B** - 다운로드 중 (~8% 완료, 1.9GB)

**참고**: 3B 모델 다운로드 완료 후 Teacher 모델로 고품질 데이터 생성 가능
