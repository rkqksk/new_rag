# RAG Enterprise v5.8.0 로컬 구현 가이드

**목적**: v5.8.0의 모든 기능을 로컬에서 실행하고 테스트하기
**소요 시간**: 약 1시간
**난이도**: 중급

---

## 📋 사전 요구사항

### 필수 소프트웨어
```bash
# 1. Docker & Docker Compose
docker --version  # Docker version 24.0.0+
docker-compose --version  # v2.0.0+

# 2. Python (선택 - 로컬 개발용)
python --version  # Python 3.11+

# 3. Git
git --version
```

### 시스템 요구사항
- **RAM**: 최소 8GB (권장 16GB)
- **디스크**: 최소 10GB 여유 공간
- **OS**: macOS, Linux, Windows (WSL2)

---

## 🚀 Step 1: 라우터 연결 (핵심 작업)

### 1.1 현재 상태 확인

현재 **app/main.py**에는 6개 라우터만 등록되어 있습니다:
```python
# 현재 등록된 라우터 (Line 104-124)
- search
- personalization
- analytics
- image_processing
- debug
- admin
```

하지만 실제로는 **15개 이상의 라우터**가 구현되어 있습니다!

### 1.2 app/main.py 수정

**파일 위치**: `/Users/oypnus/rag-enterprise/app/main.py`

#### 수정 1: Import 추가 (Line 10-11 다음)

```python
# 기존 imports (Line 10-11)
from app.api.routes import image_processing
from app.api.v1 import admin, analytics, debug, personalization, search

# 🆕 추가 imports
from app.api import workflow_routes, consultation, dashboard_routes, ingestion_routes, query_routes
from app.api.routes import excel, health, async_qa
from app.routes import products, qa, inquiries, tracking
from src.api.v1 import saas
```

#### 수정 2: Router 등록 추가 (Line 125 다음)

```python
# 기존 routers (Line 104-124)
app.include_router(search.router, prefix=f"{settings.api_prefix}/search", tags=["search"])
app.include_router(personalization.router, prefix=f"{settings.api_prefix}/personalization", tags=["personalization"])
app.include_router(analytics.router, prefix=f"{settings.api_prefix}/analytics", tags=["analytics"])
app.include_router(image_processing.router)
if settings.debug_enabled:
    app.include_router(debug.router, prefix=f"{settings.api_prefix}/debug", tags=["debug"])
app.include_router(admin.router, prefix=settings.api_prefix, tags=["admin"])

# 🆕 추가 routers (Line 125 이후)

# ============================================================================
# SaaS Platform - Multi-Tenancy, Authentication, Billing
# ============================================================================
app.include_router(
    saas.router,
    prefix=f"{settings.api_prefix}/saas",
    tags=["SaaS Platform"]
)

# ============================================================================
# Product Management - Search, Recommendations, Q&A
# ============================================================================
app.include_router(products.router, tags=["Products"])
app.include_router(qa.router, tags=["Q&A"])
app.include_router(
    async_qa.router,
    prefix=f"{settings.api_prefix}/async-qa",
    tags=["Async Q&A"]
)
app.include_router(inquiries.router, tags=["Inquiries"])

# ============================================================================
# Workflow & Orchestration
# ============================================================================
app.include_router(workflow_routes.router, tags=["Workflow"])

# ============================================================================
# Data Management
# ============================================================================
app.include_router(
    excel.router,
    prefix=f"{settings.api_prefix}/excel",
    tags=["Excel Processing"]
)
app.include_router(ingestion_routes.router, tags=["Data Ingestion"])

# ============================================================================
# Dashboard & Analytics
# ============================================================================
app.include_router(dashboard_routes.router, tags=["Dashboard"])
app.include_router(consultation.router, tags=["Consultation"])

# ============================================================================
# System Health & Monitoring
# ============================================================================
app.include_router(
    health.router,
    prefix=f"{settings.api_prefix}/health",
    tags=["Health Checks"]
)
app.include_router(tracking.router, tags=["Tracking"])
app.include_router(query_routes.router, tags=["Query Management"])
```

### 1.3 수정된 파일 확인

```bash
# app/main.py 라인 수 확인
wc -l app/main.py
# Before: ~130 lines
# After:  ~200 lines

# Import 확인
grep "^from" app/main.py | wc -l
# Before: ~10 imports
# After:  ~15 imports

# Router 확인
grep "include_router" app/main.py | wc -l
# Before: 6 routers
# After:  18 routers
```

---

## 🔧 Step 2: 환경 설정

### 2.1 .env 파일 생성

```bash
# 1. .env.example 복사
cp .env.example .env

# 2. .env 파일 편집
nano .env  # 또는 code .env (VS Code)
```

### 2.2 필수 환경 변수 설정

**.env 파일 내용:**

```bash
# ============================================================================
# Database Configuration
# ============================================================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=rag_enterprise_2024_secure  # 🔐 변경 필수!
POSTGRES_DB=rag_enterprise

# ============================================================================
# Redis Cache
# ============================================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=  # 선택 사항

# ============================================================================
# Qdrant Vector Database
# ============================================================================
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=  # 선택 사항

# ============================================================================
# API Server
# ============================================================================
API_PORT=8001
API_HOST=0.0.0.0
API_PREFIX=/api/v1

# ============================================================================
# Authentication & Security
# ============================================================================
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production  # 🔐 변경 필수!
JWT_ALGORITHM=HS256
JWT_EXPIRATION=24  # hours
API_KEY_SALT=your_api_key_salt_change_this  # 🔐 변경 필수!

# ============================================================================
# SaaS Platform
# ============================================================================
# Stripe (결제 기능 사용 시)
STRIPE_API_KEY=sk_test_your_stripe_key  # 선택 사항
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret  # 선택 사항

# ============================================================================
# AI/ML Services
# ============================================================================
# NexaAI (선택 - 빠른 응답용)
NEXA_API_KEY=your_nexa_api_key  # 선택 사항
NEXA_MODEL=qwen2.5:7b-instruct
NEXA_TIMEOUT=30

# Ollama (로컬 LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# ============================================================================
# Debug & Development
# ============================================================================
DEBUG_ENABLED=true
DEBUG_PROFILE_REQUESTS=true
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/rag-enterprise.log

# ============================================================================
# CORS (프론트엔드)
# ============================================================================
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000
```

### 2.3 보안 키 생성 (선택)

Python으로 안전한 키 생성:

```bash
python3 -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(64)}')"
python3 -c "import secrets; print(f'API_KEY_SALT={secrets.token_urlsafe(32)}')"
```

---

## 🐳 Step 3: Docker 환경 실행

### 3.1 Docker Compose 확인

```bash
# docker-compose.yml 검증
docker-compose config

# 출력 예시:
# services:
#   postgres:
#     ...
#   redis:
#     ...
#   qdrant:
#     ...
#   api:
#     ...
```

### 3.2 Docker 이미지 빌드 및 실행

**방법 1: 스크립트 사용 (권장)**

```bash
# 개발 모드로 전체 스택 배포
./scripts/deploy-optimized.sh development

# 출력:
# ✅ Building Docker images...
# ✅ Starting services...
# ✅ Waiting for services to be ready...
# ✅ All services are running!
```

**방법 2: 직접 실행**

```bash
# 1. 이미지 빌드
docker-compose build

# 2. 백그라운드로 실행
docker-compose up -d

# 3. 로그 확인
docker-compose logs -f api
```

### 3.3 서비스 상태 확인

```bash
# 모든 서비스 상태
docker-compose ps

# 출력 예시:
# NAME       IMAGE                STATUS        PORTS
# postgres   postgres:15-alpine   Up 2 minutes  0.0.0.0:5432->5432/tcp
# redis      redis:7-alpine       Up 2 minutes  0.0.0.0:6379->6379/tcp
# qdrant     qdrant/qdrant:v1.7   Up 2 minutes  0.0.0.0:6333->6333/tcp
# api        rag-enterprise-api   Up 2 minutes  0.0.0.0:8001->8001/tcp
```

### 3.4 헬스 체크

```bash
# API 헬스 체크
curl http://localhost:8001/health/ready

# 출력:
# {
#   "status": "ready",
#   "services": {
#     "postgres": "healthy",
#     "redis": "healthy",
#     "qdrant": "healthy"
#   }
# }
```

---

## 🧪 Step 4: API 테스트

### 4.1 API 문서 확인

브라우저에서 열기:

```
http://localhost:8001/api/v1/docs
```

**확인 사항:**
- ✅ 18개 태그 (API 그룹) 표시됨
- ✅ "SaaS Platform" 태그 존재
- ✅ "Products", "Q&A", "Workflow" 태그 존재
- ✅ "Excel Processing", "Data Ingestion" 태그 존재

### 4.2 기본 API 테스트

#### Test 1: Search API (기존)
```bash
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "50ml PET 용기",
    "top_k": 5
  }'
```

#### Test 2: Image Processing (v5.8.0 신기능)
```bash
# 테스트 이미지 다운로드
curl -o test_watermark.jpg https://picsum.photos/800/600

# 워터마크 제거 테스트
curl -X POST http://localhost:8001/api/v1/image/remove-watermark \
  -F "image=@test_watermark.jpg" \
  -F "method=auto"
```

#### Test 3: SaaS API (v5.8.0 신기능)
```bash
# 테넌트 생성
curl -X POST http://localhost:8001/api/v1/saas/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "email": "admin@testcompany.com",
    "plan": "free"
  }'

# 출력:
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "name": "Test Company",
#   "status": "active",
#   "plan": "free",
#   "created_at": "2025-11-09T..."
# }
```

#### Test 4: Workflow API (v5.8.0 신기능)
```bash
# 워크플로우 실행
curl -X POST http://localhost:8001/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "data_ingestion",
    "parameters": {
      "source": "excel",
      "file_path": "/data/sample.xlsx"
    }
  }'
```

### 4.3 Python 클라이언트 테스트

**test_client.py:**

```python
#!/usr/bin/env python3
"""RAG Enterprise v5.8.0 API 테스트 클라이언트"""

import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_search():
    """검색 API 테스트"""
    response = requests.post(
        f"{BASE_URL}/search/",
        json={"query": "50ml 용기", "top_k": 3}
    )
    print("🔍 Search API:", response.status_code)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_saas():
    """SaaS API 테스트"""
    # 테넌트 생성
    response = requests.post(
        f"{BASE_URL}/saas/tenants",
        json={
            "name": "Python Test Tenant",
            "email": "python@test.com",
            "plan": "free"
        }
    )
    print("\n🏢 SaaS API (Tenant):", response.status_code)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_health():
    """헬스 체크"""
    response = requests.get(f"{BASE_URL}/health/ready")
    print("\n❤️ Health Check:", response.status_code)
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    print("=" * 60)
    print("RAG Enterprise v5.8.0 API 테스트")
    print("=" * 60)

    test_health()
    test_search()
    test_saas()

    print("\n✅ 모든 테스트 완료!")
```

실행:

```bash
python3 test_client.py
```

---

## 📊 Step 5: 전체 기능 검증

### 5.1 등록된 엔드포인트 확인

```bash
# API 문서에서 모든 엔드포인트 추출
curl -s http://localhost:8001/api/v1/docs | grep -o '"url":"[^"]*"' | wc -l

# Before (라우터 연결 전): ~20 endpoints
# After (라우터 연결 후):  ~50+ endpoints
```

### 5.2 새로운 엔드포인트 목록

**SaaS Platform (`/api/v1/saas`):**
- `POST /saas/tenants` - 테넌트 생성
- `GET /saas/tenants/{id}` - 테넌트 조회
- `POST /saas/users` - 사용자 생성
- `POST /saas/auth/login` - 로그인
- `POST /saas/api-keys` - API 키 생성
- `GET /saas/billing/usage` - 사용량 조회

**Product Management (`/api/v1`):**
- `POST /products/search` - 제품 검색
- `GET /products/{id}` - 제품 상세
- `POST /qa/ask` - Q&A 질문
- `POST /async-qa/submit` - 비동기 Q&A
- `GET /inquiries` - 문의 목록

**Workflow (`/api/v1/workflow`):**
- `POST /workflow/execute` - 워크플로우 실행
- `GET /workflow/status/{id}` - 워크플로우 상태
- `POST /workflow/cancel/{id}` - 워크플로우 취소

**Data Management (`/api/v1`):**
- `POST /excel/upload` - Excel 업로드
- `POST /excel/parse` - Excel 파싱
- `POST /ingestion/start` - 데이터 수집 시작

**Dashboard (`/api/v1`):**
- `GET /dashboard/stats` - 대시보드 통계
- `GET /consultation/sessions` - 상담 세션

**System (`/api/v1`):**
- `GET /health/live` - Liveness 체크
- `GET /health/ready` - Readiness 체크
- `GET /tracking/events` - 이벤트 추적

### 5.3 자동화 테스트 실행

```bash
# Python 테스트 스위트
pytest tests/ -v --cov=app --cov=src

# 출력:
# tests/test_saas.py::test_create_tenant PASSED
# tests/test_workflow.py::test_execute_workflow PASSED
# tests/test_image.py::test_watermark_removal PASSED
# ...
# ==================== 122 passed ====================
# Coverage: 95%
```

---

## 🎨 Step 6: 프론트엔드 실행

### 6.1 프론트엔드 서버 시작

```bash
# 1. frontend 디렉터리로 이동
cd frontend

# 2. HTTP 서버 시작
python3 -m http.server 8080

# 출력:
# Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

### 6.2 브라우저에서 열기

```
http://localhost:8080/chat.html
```

**테스트:**
1. "50ml PET 용기" 검색
2. 이미지 업로드 및 워터마크 제거 테스트
3. 대화형 Q&A 테스트

---

## 🔍 Step 7: 모니터링 및 디버깅

### 7.1 로그 확인

**실시간 로그:**
```bash
# API 로그
docker-compose logs -f api

# 모든 서비스 로그
docker-compose logs -f
```

**로그 파일:**
```bash
# 로그 디렉터리 확인
ls -lh logs/

# 최근 로그 확인
tail -f logs/rag-enterprise.log
```

### 7.2 성능 모니터링

```bash
# 성능 통계
curl http://localhost:8001/api/v1/debug/performance/summary

# 출력:
# {
#   "total_requests": 1234,
#   "avg_response_time": 0.234,
#   "slow_queries": 5,
#   "error_rate": 0.01
# }

# 느린 쿼리 확인
curl http://localhost:8001/api/v1/debug/queries/recent?slow_only=true
```

### 7.3 데이터베이스 상태

```bash
# PostgreSQL
docker-compose exec postgres psql -U postgres -d rag_enterprise -c "\dt"

# Qdrant
curl http://localhost:6333/collections

# Redis
docker-compose exec redis redis-cli INFO stats
```

---

## 🐛 트러블슈팅

### 문제 1: 라우터 Import 에러

**증상:**
```
ImportError: cannot import name 'saas' from 'src.api.v1'
```

**해결:**
```bash
# 1. 파일 존재 확인
ls -la src/api/v1/saas.py

# 2. Python 경로 확인
export PYTHONPATH=/Users/oypnus/rag-enterprise:$PYTHONPATH

# 3. Docker 재빌드
docker-compose build --no-cache api
```

### 문제 2: Docker 서비스 시작 실패

**증상:**
```
ERROR: for postgres  Cannot start service postgres: port is already allocated
```

**해결:**
```bash
# 1. 포트 사용 확인
lsof -i :5432
lsof -i :6379
lsof -i :6333

# 2. 기존 프로세스 종료 또는 포트 변경
# .env에서 포트 변경:
# POSTGRES_PORT=5433
# REDIS_PORT=6380
# QDRANT_PORT=6334

# 3. docker-compose.yml도 함께 수정
```

### 문제 3: API 응답 느림

**증상:**
```
Response time > 5 seconds
```

**해결:**
```bash
# 1. 프로파일링 활성화
echo "DEBUG_PROFILE_REQUESTS=true" >> .env
docker-compose restart api

# 2. 느린 엔드포인트 확인
curl http://localhost:8001/api/v1/debug/performance/summary

# 3. 로그 분석
grep "SLOW" logs/rag-enterprise.log
```

### 문제 4: SaaS API 인증 오류

**증상:**
```
401 Unauthorized: Invalid API key
```

**해결:**
```bash
# 1. API 키 생성
curl -X POST http://localhost:8001/api/v1/saas/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Key","tenant_id":"YOUR_TENANT_ID"}'

# 2. 생성된 키로 재시도
curl -X GET http://localhost:8001/api/v1/search/ \
  -H "X-API-Key: YOUR_GENERATED_KEY"
```

---

## ✅ 검증 체크리스트

### 코드 수정
- [ ] app/main.py에 imports 추가됨
- [ ] app/main.py에 18개 라우터 등록됨
- [ ] 문법 오류 없음 (python -m py_compile app/main.py)

### 환경 설정
- [ ] .env 파일 생성됨
- [ ] 모든 필수 환경 변수 설정됨
- [ ] JWT_SECRET_KEY 변경됨 (보안)
- [ ] POSTGRES_PASSWORD 변경됨 (보안)

### Docker 실행
- [ ] docker-compose config 성공
- [ ] docker-compose up -d 성공
- [ ] 모든 서비스 Running 상태
- [ ] http://localhost:8001/health/ready 응답 OK

### API 테스트
- [ ] Swagger UI 접속 가능 (http://localhost:8001/api/v1/docs)
- [ ] 18개 API 태그 표시됨
- [ ] Search API 테스트 성공
- [ ] SaaS API 테스트 성공
- [ ] Image Processing API 테스트 성공
- [ ] Workflow API 테스트 성공

### 프론트엔드
- [ ] frontend 서버 실행됨 (http://localhost:8080)
- [ ] chat.html 로드 성공
- [ ] 검색 기능 작동
- [ ] 이미지 업로드 작동

### 모니터링
- [ ] 로그 정상 출력
- [ ] 성능 통계 조회 가능
- [ ] 에러 없음 (또는 처리됨)

---

## 🎉 완료!

모든 단계를 완료하셨다면 **RAG Enterprise v5.8.0**이 완전히 로컬에서 실행 중입니다!

### 다음 단계

1. **개발 시작**:
   - 새로운 API 엔드포인트 추가
   - 프론트엔드 커스터마이징
   - 비즈니스 로직 구현

2. **배포 준비**:
   - Kubernetes 배포 설정 (docs/k8s/)
   - CI/CD 파이프라인 구성
   - 프로덕션 환경 설정

3. **최적화**:
   - 성능 벤치마크
   - 캐싱 전략 개선
   - 데이터베이스 인덱스 최적화

### 참고 문서

- **기술 문서**: `docs/V5.8.0_VERIFICATION_REPORT.md`
- **API 문서**: http://localhost:8001/api/v1/docs
- **로컬 설정**: `docs/guides/LOCAL_SETUP.md`
- **심볼 참조**: `CLAUDE.md` (§rag.*, §api.*, §deploy.*)

---

**작성일**: 2025-11-09
**버전**: v5.8.0
**작성자**: Claude Code (Sonnet 4.5)
