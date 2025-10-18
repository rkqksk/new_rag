# MCP 서버 설정 및 사용 가이드

## 개요

RAG Enterprise 시스템에 3개의 MCP 서버가 통합되었습니다:

1. **Haiku 4.5 MCP** - API 키 라우팅, 재시도 로직, 캐싱
2. **Google DevTools MCP** - 자동 크롤링, 디버깅, 성능 모니터링
3. **Query Router** - 질문 난이도 분석 → Haiku/Sonnet 자동 선택

---

## 1. Haiku 4.5 MCP Server

### 기능

- ✅ **API 키 라우팅**: Primary/Backup 키 자동 전환
- ✅ **응답 캐싱**: 300초 TTL, MD5 기반 키 생성
- ✅ **재시도 로직**: 3회 자동 재시도 (지수 백오프)
- ✅ **API 키 에러 처리**: 401 에러 시 백업 키 자동 전환
- ✅ **사용량 추적**: 토큰별, API 키별 통계

### 환경 변수

```bash
# .env 파일
ANTHROPIC_API_KEY=sk-ant-your-primary-key-here
ANTHROPIC_API_KEY_BACKUP=sk-ant-your-backup-key-here  # 선택사항
```

### MCP 요청 예시

```json
{
  "method": "generate",
  "params": {
    "prompt": "Python 리스트 정렬하기",
    "max_tokens": 1024,
    "temperature": 0.3,
    "system": "You are a Python expert",
    "use_cache": true
  }
}
```

### 응답 예시

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "text": "Python에서 list를 정렬하는 방법...",
    "model": "claude-haiku-4-5-20251001",
    "tokens": {
      "input": 12,
      "output": 256,
      "total": 268
    },
    "cached": false
  }
}
```

---

## 2. Google DevTools MCP Server

### 기능

- ✅ **자동 크롤링**: 다중 깊이 크롤링, 링크 추출
- ✅ **워크플로우**: crawl, debug, performance_monitor
- ✅ **성능 메트릭**: FCP, LCP, 메모리 사용량
- ✅ **자동 디버깅**: JS 에러, 콘솔 로그 수집
- ✅ **회귀 테스트**: 기준점 비교

### 워크플로우 유형

#### 1. Crawl 워크플로우

```json
{
  "name": "execute_workflow",
  "arguments": {
    "workflow_type": "crawl",
    "config": {
      "url": "http://localhost:8000/dashboard",
      "depth": 2,
      "max_pages": 10,
      "extract_data": true
    }
  }
}
```

#### 2. Debug 워크플로우

```json
{
  "name": "execute_workflow",
  "arguments": {
    "workflow_type": "debug",
    "config": {
      "url": "http://localhost:8000",
      "check_js_errors": true,
      "check_console": true,
      "take_screenshot": true
    }
  }
}
```

#### 3. Performance Monitor 워크플로우

```json
{
  "name": "execute_workflow",
  "arguments": {
    "workflow_type": "performance_monitor",
    "config": {
      "urls": [
        "http://localhost:8000/dashboard",
        "http://localhost:8000/api/v1/search"
      ],
      "sample_count": 5
    }
  }
}
```

---

## 3. Query Router (FastAPI 엔드포인트)

### 작동 원리

```
질문 입력
    ↓
[QueryAnalyzer] 난이도 분석
    ↓
┌─────────────────┬──────────────────┬─────────────────┐
│    SIMPLE       │    MODERATE      │    COMPLEX      │
│  (신뢰도 > 80%) │  (신뢰도 50-80%) │  (신뢰도 > 70%) │
├─────────────────┼──────────────────┼─────────────────┤
│ Haiku 직접 처리  │ Haiku → 생성     │ Sonnet 직접 처리 │
│ ✓ 빠름          │ ✓ 빠름 + 검증    │ ✓ 정확함        │
│ 예상: 50-100ms  │ Sonnet 검증 추가 │ 예상: 100-200ms │
│                 │ 예상: 1-2초      │                 │
└─────────────────┴──────────────────┴─────────────────┘
    ↓
최종 응답 반환
```

### API 엔드포인트

#### 1. `/api/v1/query/route` (POST)

**요청:**
```json
{
  "query": "Python에서 list를 역순으로 정렬하는 방법?",
  "system_prompt": "You are a Python expert",
  "max_tokens": 4096
}
```

**응답:**
```json
{
  "query": "Python에서 list를 역순으로 정렬하는 방법?",
  "complexity": "simple",
  "response": "Python에서 list를 역순으로...",
  "model_used": "claude-haiku-4-5-20251001",
  "tokens": {
    "total": 268
  },
  "review_passed": true,
  "thinking": ["Query analysis: simple (confidence: 0.95)"]
}
```

#### 2. `/api/v1/query/analyze` (POST)

**요청:**
```json
{
  "query": "마이크로서비스 아키텍처 설계"
}
```

**응답:**
```json
{
  "query": "마이크로서비스 아키텍처 설계",
  "complexity": "complex",
  "confidence": 0.85,
  "recommendation": "Will use Sonnet model for best results"
}
```

#### 3. `/api/v1/query/stats` (GET)

**응답:**
```json
{
  "summary": {
    "total_calls": 150,
    "teacher_reviews": 45,
    "corrections_made": 8,
    "efficiency": "65.3% Haiku / 34.7% Sonnet"
  },
  "haiku": {
    "calls": 105,
    "tokens": 45000,
    "percentage": 65.3
  },
  "sonnet": {
    "calls": 45,
    "tokens": 25000,
    "percentage": 34.7
  }
}
```

#### 4. `/api/v1/query/batch` (POST)

**요청:**
```json
[
  {"query": "Python 기초?"},
  {"query": "마이크로서비스 설계"},
  {"query": "REST API 구현?"}
]
```

**응답:**
```json
{
  "batch_size": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "index": 0,
      "query": "Python 기초?",
      "complexity": "simple",
      "model_used": "claude-haiku-4-5-20251001",
      "tokens": 150
    }
  ]
}
```

#### 5. `/api/v1/query/health` (GET)

**응답:**
```json
{
  "status": "healthy",
  "models": {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-3-5-sonnet-20241022"
  }
}
```

---

## 설정 및 실행

### 1. 환경 변수 설정

```bash
# .env 파일
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_API_KEY_BACKUP=sk-ant-your-backup-key

# Qdrant
QDRANT_HOST=172.28.0.2
QDRANT_HTTP_PORT=6333

# Redis
REDIS_HOST=172.28.0.3
REDIS_PORT=6379

# PostgreSQL
POSTGRES_HOST=172.28.0.4
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=rag_enterprise
```

### 2. Docker 서비스 시작

```bash
# 전체 서비스 시작
docker-compose up -d

# FastAPI 서버만 재구성
docker-compose up -d --build fastapi

# 로그 확인
docker-compose logs -f fastapi
```

### 3. FastAPI 로컬 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# FastAPI 실행
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

# 또는 Python 모듈로 실행
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### 4. 테스트 실행

```bash
# Query Router 통합 테스트
python tests/test_mcp_integration.py

# FastAPI 엔드포인트 테스트
curl -X POST http://localhost:8000/api/v1/query/route \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python에서 list를 정렬하는 방법?",
    "analyze_only": false
  }'

# 라우팅 통계 조회
curl http://localhost:8000/api/v1/query/stats
```

---

## 성능 최적화 팁

### 1. Haiku 캐싱 활용

동일한 쿼리가 반복되는 경우 캐시를 활용하여 응답 시간을 대폭 단축:

```python
# 캐싱 활성화 (기본값: true)
{
  "query": "Same query",
  "use_cache": true
}
```

### 2. 배치 처리로 토큰 절약

여러 질문을 한 번에 처리하여 오버헤드 감소:

```python
# 배치 처리 (권장)
POST /api/v1/query/batch
[
  {"query": "Q1"},
  {"query": "Q2"},
  {"query": "Q3"}
]

# 개별 처리 (비효율)
POST /api/v1/query/route {"query": "Q1"}
POST /api/v1/query/route {"query": "Q2"}
POST /api/v1/query/route {"query": "Q3"}
```

### 3. 토큰 사용량 모니터링

```bash
# 통계 확인
curl http://localhost:8000/api/v1/query/stats | jq

# 결과
{
  "haiku": {"percentage": 65.3, "tokens": 45000},
  "sonnet": {"percentage": 34.7, "tokens": 25000}
}
```

### 4. 시스템 프롬프트 최적화

```python
# 좋은 예: 명확하고 간결
system_prompt = "You are a Python expert. Answer questions concisely."

# 피해야 할 예: 장황함
system_prompt = "You are an AI assistant that specializes in Python programming. Please provide detailed and comprehensive answers to all Python-related questions, including examples and edge cases..."
```

---

## 트러블슈팅

### 문제 1: API 키 에러

```
Error: 401 Unauthorized
```

**해결:**
```bash
# 1. .env 파일 확인
cat .env | grep ANTHROPIC_API_KEY

# 2. API 키 형식 검증
# 올바른 형식: sk-ant-xxxxx
```

### 문제 2: 캐시 관련 이슈

```bash
# 캐시 초기화
curl -X POST http://localhost:8000/api/v1/query/cache/clear

# 또는 클라이언트 코드에서
{
  "query": "your query",
  "use_cache": false
}
```

### 문제 3: Google DevTools 크롤링 실패

```bash
# Playwright 설치 확인
python -c "import playwright; print(playwright.__version__)"

# Chromium 브라우저 설치
playwright install chromium
```

### 문제 4: 성능 저하

```bash
# 토큰 사용량 확인
curl http://localhost:8000/api/v1/query/stats

# Haiku 비율이 낮으면 쿼리 분석 개선 필요
# (복잡한 쿼리를 단순하게 분해)
```

---

## 모범 사례

### ✅ DO (권장)

- 📊 배치 처리로 여러 쿼리 한 번에 처리
- 🔍 `analyze_only` 먼저 사용해서 복잡도 확인
- 💾 캐싱 활성화 (기본값)
- 📈 정기적으로 통계 모니터링
- 🔄 간단한 질문은 Haiku 활용

### ❌ DON'T (피해야 할 사항)

- ❌ 모든 쿼리를 개별로 처리
- ❌ 캐싱 비활성화
- ❌ 장황한 시스템 프롬프트
- ❌ API 키 하드코딩
- ❌ 너무 긴 max_tokens (기본: 4096)

---

## 문서 및 참고

- 📘 [Claude API 문서](https://docs.anthropic.com)
- 📗 [MCP 프로토콜 문서](https://modelcontextprotocol.io)
- 📙 [FastAPI 문서](https://fastapi.tiangolo.com)
- 🔗 MCP 서버 구현: `mcp_servers/`
- 🔗 라우터 구현: `app/api/query_routes.py`
- 🔗 테스트: `tests/test_mcp_integration.py`

---

## 지원

문제가 발생하면:

1. 로그 확인: `docker-compose logs fastapi`
2. 상태 확인: `curl http://localhost:8000/health`
3. 쿼리 라우터 확인: `curl http://localhost:8000/api/v1/query/health`
4. 테스트 실행: `python tests/test_mcp_integration.py`

---

*Last Updated: 2025-10-17*
*Version: 1.0.0*
