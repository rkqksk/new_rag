# RAG Enterprise System Architecture Document
## 한국제조 엔터프라이즈 RAG/상담 시스템 v2.1
*MOSO / RAG 기반 AI 오케스트레이션 플랫폼*

## 🎯 프로젝트 비전

### 전체 비전
**RAG 기반 멀티모달 AI 오케스트레이션 플랫폼**으로, 텍스트·이미지·영상·산업 데이터를 통합 학습하여 기업 내부 데이터와 외부 지식을 결합한 **하이브리드 AI 에이전트 생태계**를 구축

### 시스템 목적
제조업 특화 지능형 문서 처리 및 검색 시스템으로, 거래명세서, 견적서, 세금계산서, 불량사진, 도면, MSDS 등의 복잡한 산업 문서를 자동으로 수집, 분석, 검색하여 즉각적인 비즈니스 인사이트를 제공

### 핵심 목표
- **대규모 언어 모델(LLM)을 통한 고객 상담 자동화**
- **비정형 데이터 기반 검색·추천 시스템 구축**
- **멀티모달 이미지 매칭 및 제품 자동 추천 서비스**
- **계층적 접근 제어 시스템** (Admin, Internal, Client)
- **지속적 지식 업데이트 및 미세조정 체계 확립** (LoRA, QLoRA)

### 핵심 가치
- **자동화**: 24/7 무중단 크롤링 및 처리, 자동 페이지 생성
- **정확성**: 멀티모달 AI 기반 정확한 문서 이해 및 Teacher-Student 구조
- **확장성**: 마이크로서비스 아키텍처로 유연한 확장
- **보안성**: RBAC 기반 세밀한 권한 관리
- **지능화**: Teacher 모델 기반 지식 증류 및 지속 학습

## 🏗️ 5계층 시스템 아키텍처

```
┌─────────────────────────────────────────────────┐
│         Layer 1: UI/UX Layer                    │
│  - 관리자 대시보드 (React + FastAPI)            │
│  - 사용자 포털 (Internal/Client 분리)           │
│  - 프롬프트 템플릿 편집 UI                      │
├─────────────────────────────────────────────────┤
│         Layer 2: Orchestration Layer            │
│  - Teacher-Student LLM 구조                     │
│  - Prompt Chain / Agent Flow                    │
│  - Knowledge Distillation Pipeline              │
├─────────────────────────────────────────────────┤
│         Layer 3: RAG Retrieval Layer            │
│  - Vector DB (Qdrant) + Semantic Search         │
│  - Embedding (sentence-transformers)            │
│  - Re-ranking (Cross-encoder)                   │
├─────────────────────────────────────────────────┤
│         Layer 4: Data Ingestion Layer           │
│  - 업로드/크롤링/전처리/오토라벨링              │
│  - 제품 코드 기반 자동 페이지 생성              │
│  - 멀티모달 특징 추출 (CLIP, BLIP-2)           │
├─────────────────────────────────────────────────┤
│         Layer 5: Infrastructure & API Layer     │
│  - LLM API (Local: MLX, Cloud: Groq/OpenAI)     │
│  - Web 검색 API (MSDS, PubChem, arXiv)         │
│  - Docker 기반 컨테이너 오케스트레이션          │
└─────────────────────────────────────────────────┘
```

### 계층별 상세 설계

#### Layer 1: UI/UX Layer
```yaml
관리자 대시보드:
  - 데이터 업로드 / 벡터화 / 모델 관리 UI
  - 프롬프트 템플릿 및 파이프라인 편집
  - 사용자 권한 관리 (RBAC)

사용자 포털:
  - Super Admin: 전체 시스템 제어
  - Internal: 부서별 권한 분리 (인사, 생산, 물류)
  - Client: 제품/물류 정보 및 품질 이력 제한 조회
```

#### Layer 2: Orchestration Layer - Teacher-Student 구조
| 역할 | 모델 | 백엔드 | 주요 기능 |
|------|------|--------|------------|
| **Teacher** | Qwen 2.5 - 7B | MLX | 고품질 응답 생성, 지식 증류 |
| **Student** | gemma-3 - 1B | Transformers | 경량화 모델, 실시간 서비스 |
| **Student** | Qwen 2.5 - 3B | MLX | 중간급 성능, 추천/검색용 |

**지식 증류 전략**:
- Teacher 모델이 생성한 정답, 근거, 이유를 포함한 고품질 데이터를 Student 모델 학습용으로 사용
- LoRA / QLoRA 기반 경량 파인튜닝 파이프라인

#### Layer 3: RAG Retrieval Layer
```yaml
데이터 수집:
  직접 업로드:
    - 텍스트, 이미지, HTML, CSV, Markdown, 동영상
    - FastAPI 비동기 업로드 엔드포인트

  웹 크롤링:
    - 제품 페이지, 논문, 화학 성분 DB, 블로그
    - Requests/aiohttp: REST API 크롤링
    - Selenium/Playwright: 동적 웹페이지 처리
    - N8N: 워크플로우 자동화

  자동 라벨링:
    - 제품 코드, 품목, 카테고리, 스펙 자동 태깅

전처리 및 임베딩:
  - 문서 → 청크(chunk) 분할 및 토큰화
  - sentence-transformers 기반 벡터화
  - Qdrant 벡터DB 저장

검색 및 생성:
  - 사용자 질의 → 벡터 검색 → Top-K 추출
  - LLM 입력 프롬프트로 병합 → 답변 생성
```

#### Layer 4: Data Ingestion Layer
```yaml
크롤러 에이전트:
  - Schedule: Cron 기반 정기 실행
  - 실시간 유효성 검증

파일 업로드:
  - 지원 형식: PDF, XLSX, DOCX, PNG, JPG, DWG

자동 페이지 생성:
  - 제품 코드별 자동 페이지: 이미지, 스펙, 인쇄 영역, MSDS
  - 고객용 링크 자동 생성 → 이메일/채팅 전송
```

#### Layer 5: Infrastructure & API Layer
```yaml
로컬 LLM 호스팅:
  - Hugging Face + MLX 기반 경량 LLM
  - Ollama: qwen2.5:7b, llama3.1:8b

클라우드 LLM API:
  - Groq (빠른 추론)
  - OpenAI API (고급 작업)
  - Claude API (복잡한 추론)

외부 검색 API:
  - MSDS 데이터베이스
  - PubChem (화학 성분)
  - arXiv (논문 검색)

컨테이너 오케스트레이션:
  - Docker Compose (개발)
  - Kubernetes (프로덕션)
  - CI/CD: GitHub Actions / Jenkins
```

### 주요 기능 모듈

#### 1. 텍스트 기반 상담 시스템
```yaml
제품 추천:
  input: "50미리 용기 추천해줘"
  process: RAG 검색 → Top-K 추출
  output: 제품명, 링크, 설명

불량 문의:
  input: 사진/문서 업로드
  process: 멀티모달 분석 → 원인 진단
  output: 진단 결과 및 조치 안내

거래/물류 문의:
  process: 사전 정의 워크플로우
  output: 자동 처리 및 답변
```

#### 2. 멀티모달 이미지 매칭 시스템
```yaml
파서 에이전트:
  PDF:
    - Docling: 구조화된 텍스트/표/이미지 추출
    - TableTransformer: 표 구조 분석
    - Camelot/Tabula: 레거시 PDF 표 처리

  Excel:
    - Pandas: 데이터프레임 변환
    - SQLite: 구조화 저장
    - Text2SQL: 자연어 쿼리 변환

  이미지 매칭:
    - EasyOCR: 다국어 텍스트 추출
    - CLIP, BLIP-2: 시각적 특징 임베딩
    - OpenCV: 전처리 및 품질 개선
    - 벡터 DB 비교 → 유사 제품 자동 추천

청킹 에이전트:
  - Semantic Chunking: 의미 단위 분할
  - Table-aware Chunking: 표 구조 보존
  - Hierarchical Chunking: 문서 계층 유지
  - Sliding Window: 컨텍스트 중첩
```

#### 3. 임베딩 및 검색 시스템
```yaml
임베딩 모델:
  텍스트:
    Primary: gte-Qwen2-7B-instruct
    Fallback: multilingual-e5-large
    Korean: KoE5-base

  이미지:
    Primary: OpenCLIP-ViT-H-14
    Fallback: CLIP-ViT-L-14

벡터 저장:
  Qdrant:
    - Collection 분리: text/image/table
    - HNSW 인덱싱
    - 메타데이터 필터링

하이브리드 검색:
  - Dense: 벡터 유사도
  - Sparse: BM25 키워드 매칭
  - Re-ranking: Cross-encoder

검색 파이프라인:
  1. Query Understanding: 의도 분석
  2. Multi-stage Retrieval:
     - Initial: Fast approximate search
     - Refinement: Precise re-ranking
  3. Context Assembly: 관련 문서 조합
  4. Answer Generation: Teacher/Student LLM 응답

QA 에이전트:
  - Chain-of-Thought 추론
  - Citation 자동 생성
  - Confidence 스코어링
  - Fallback 답변 전략
```

## 🔧 기술 스택 상세

### Core Framework
```toml
[runtime]
python = "3.11"
framework = "FastAPI"
async = "asyncio + uvloop"

[databases]
vector_db = "Qdrant 1.7"
cache = "Redis 7.2"
metadata = "PostgreSQL 15"
document = "MongoDB 7.0"

[ml_frameworks]
nlp = "Transformers 4.36"
embedding = "sentence-transformers 2.2"
vision = "OpenCLIP 2.0"
finetuning = "PEFT + LoRA"
```

## 🔌 MCP Servers & Agents Configuration

### 활성화된 MCP 서버
**인프라 서비스 (docker-compose 관리)**
- **Qdrant** (172.28.0.2): 벡터 검색 - HTTP:6333, gRPC:6334
- **Redis** (172.28.0.3): 캐싱 및 세션 - 6379
- **PostgreSQL** (172.28.0.4): 메타데이터 저장 - 5432
- **N8N** (172.28.0.5): 워크플로우 자동화 - 5678
- **Ollama** (172.28.0.6): 로컬 LLM 추론 - 11434

**Python MCP 서버 (.mcp.json 관리)**
- **filesystem**: 문서 파일시스템 접근
- **claude_haiku**: 경량 LLM 작업 (claude-haiku-4-5-20251001)
- **qdrant_server**: Qdrant 벡터DB 연동
- **ollama_server**: Ollama 로컬 LLM 연동

### 커스텀 에이전트
```yaml
workflow_orchestrator:
  role: 중앙 파이프라인 조정
  config:
    max_workers: 4
    batch_size: 10
    retry_attempts: 3

crawler_scheduler:
  role: 자동 크롤링 스케줄러
  config:
    schedule: "0 */6 * * *"  # 6시간마다
    targets: "./config/crawl_targets.json"

quality_monitor:
  role: RAG 품질 모니터링
  config:
    evaluation_interval: 3600  # 1시간
    metrics: [relevance, accuracy, latency]
```

### 네트워크 아키텍처
```
rag_network (172.28.0.0/16)
├─ qdrant      172.28.0.2 → 벡터 검색
├─ redis       172.28.0.3 → 캐싱
├─ postgres    172.28.0.4 → 메타데이터
├─ n8n         172.28.0.5 → 워크플로우
└─ ollama      172.28.0.6 → 로컬 LLM
```

### 포트 매핑
| 서비스 | 호스트 포트 | 컨테이너 포트 | 용도 |
|--------|------------|--------------|------|
| Qdrant | 6333 | 6333 | HTTP API |
| Qdrant | 6334 | 6334 | gRPC |
| Redis | 6379 | 6379 | Cache |
| PostgreSQL | 5432 | 5432 | Database |
| N8N | 5678 | 5678 | Workflow UI |
| Ollama | 11434 | 11434 | LLM API |

### Colima 환경 최적화
```yaml
리소스 할당:
  qdrant:
    cpu: 1-2 cores
    memory: 2-4GB

  redis:
    cpu: 1 core
    memory: 2GB

  postgres:
    cpu: 2 cores
    memory: 4GB

  n8n:
    cpu: 2 cores
    memory: 3GB

  ollama:
    cpu: 2-4 cores
    memory: 4-8GB

healthcheck:
  interval: 30s
  timeout: 10s
  retries: 3

volumes:
  - qdrant_data: 벡터 저장소
  - redis_data: 캐시 데이터
  - postgres_data: 메타데이터
  - n8n_data: 워크플로우
  - ollama_models: LLM 모델
```

### 설정 검증 체크리스트
- [x] .mcp.json과 docker-compose.yml 포트 일관성
- [x] 환경변수 .env 파일 생성 (보안)
- [x] 서비스 간 네트워크 연결성 (172.28.0.0/16)
- [x] Health check 엔드포인트 정상 응답
- [x] 리소스 제한으로 Colima 과부하 방지
- [ ] MCP 서버 실제 구현 검증 (mcp_servers/*.py)
- [ ] Custom agents 실제 구현 검증 (agents/*.py)

### 환경 시작 명령어
```bash
# 전체 서비스 시작 (Colima 환경, FastAPI 포함)
docker-compose up -d

# FastAPI 이미지 재빌드 후 시작
docker-compose up -d --build fastapi

# 개별 서비스 시작
docker-compose up -d qdrant redis postgres fastapi

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f [service_name]
# 예: docker-compose logs -f fastapi

# 전체 종료
docker-compose down

# 볼륨 포함 완전 삭제
docker-compose down -v

# FastAPI 헬스체크
curl http://localhost:8000/health
```

### 환경변수 관리
```bash
# .env.example을 .env로 복사
cp .env.example .env

# 필수 환경변수 설정
POSTGRES_PASSWORD=your_secure_password
N8N_PASSWORD=your_n8n_password
ANTHROPIC_API_KEY=your_claude_api_key

# 환경변수 검증
docker-compose config
```

### 보안 및 권한 관리
```yaml
인증/인가:
  - JWT 토큰 기반 인증
  - RBAC 권한 모델
  - API Rate Limiting
  - IP Whitelist

데이터 보안:
  - AES-256 암호화
  - TLS 1.3 통신
  - 민감 데이터 마스킹
  - Audit 로깅
```

## 📊 모니터링 및 운영

### 메트릭 수집
```python
# Prometheus 메트릭 정의
document_processed = Counter('documents_processed_total')
embedding_latency = Histogram('embedding_duration_seconds')
search_accuracy = Gauge('search_relevance_score')
system_health = Gauge('system_health_status')
```

### 알림 정책
```yaml
Critical:
  - 시스템 다운타임
  - 데이터 손실
  - 보안 침해 시도
  
Warning:
  - 처리 지연 (>5분)
  - 메모리 사용률 >80%
  - 에러율 >5%
  
Info:
  - 일일 처리 통계
  - 모델 성능 리포트
```

## 🚀 배포 전략

### Clean Deploy Policy
```bash
# clean_deploy.py 실행 시
1. 개발 전용 코드 제거
2. 테스트 데이터 삭제
3. 디버그 로그 비활성화
4. 프로덕션 설정 적용
5. 보안 검증 실행
```

### 환경별 설정
```ini
# .env.production
ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_MONITORING=true
ENABLE_MCP=false
ENABLE_DEBUG=false

# .env.development  
ENVIRONMENT=development
LOG_LEVEL=DEBUG
ENABLE_MONITORING=false
ENABLE_MCP=true
ENABLE_DEBUG=true
```

## 📈 성능 목표 및 SLA

### 처리 성능
- 문서 인제스트: <30초/문서
- 임베딩 생성: <100ms/청크
- 검색 응답: <500ms (p95)
- 동시 처리: 1000+ 문서/시간

### 정확도 목표
- OCR 정확도: >95%
- 검색 정밀도: >90%
- 답변 관련성: >85%

## 🔄 지속적 개선

### 모델 업데이트 정책
```yaml
실험:
  - A/B 테스트 (최소 1주일)
  - RAGAS 평가 (임계값: 0.85)
  - 사용자 피드백 수집
  
배포:
  - Blue-Green 배포
  - 점진적 롤아웃 (10% → 50% → 100%)
  - 자동 롤백 (에러율 >10%)
```

### 데이터 파이프라인 최적화
```python
# 병렬 처리 최적화
async def parallel_pipeline():
    tasks = []
    for document in documents:
        task = asyncio.create_task(
            process_document(document)
        )
        tasks.append(task)
    
    results = await asyncio.gather(
        *tasks, 
        return_exceptions=True
    )
    return results
```

## 🎯 단계별 개발 로드맵

| 단계 | 내용 | 기간 | 상태 |
|------|------|------|------|
| **1단계** | 텍스트 기반 RAG 상담 구축 | ~3개월 | 🔄 진행중 |
| **2단계** | 이미지 매칭/추천 시스템 추가 | ~6개월 | ⏳ 대기 |
| **3단계** | 오토라벨링 + 자동 페이지 생성 | ~9개월 | ⏳ 대기 |
| **4단계** | 미세조정 파이프라인 및 관리 UI 고도화 | ~12개월 | ⏳ 대기 |
| **5단계** | 전사 ERP/CRM 시스템과 통합 | ~15개월 | ⏳ 대기 |

### Phase 1: 텍스트 기반 RAG 구축 (~3개월)
- [x] 기본 RAG 파이프라인 설계
- [x] 멀티모달 지원 (텍스트, 이미지) - 설계 완료
- [x] Docker 환경 구축 (Qdrant, Redis, PostgreSQL, N8N, Ollama)
- [x] FastAPI 서비스 Docker 컨테이너화
- [x] 기본 RAG API 엔드포인트 구현 (업로드, 검색, 통계)
- [x] Health Check 및 서비스 검증
- [ ] Teacher-Student LLM 구조 구현
- [ ] 워크플로우 오케스트레이션
- [ ] 기본 상담 시스템 (제품 추천, 불량 문의)

### Phase 2: 이미지 매칭 시스템 (~6개월)
- [ ] CLIP/BLIP-2 기반 이미지 임베딩
- [ ] 멀티모달 벡터 검색
- [ ] 유사 제품 자동 추천 UI
- [ ] GraphRAG 구현
- [ ] 실시간 스트리밍 처리

### Phase 3: 자동화 고도화 (~9개월)
- [ ] 오토라벨링 파이프라인
- [ ] 제품 코드 기반 자동 페이지 생성
- [ ] 고객 링크 자동 전송 (이메일/채팅)
- [ ] AutoML 파이프라인
- [ ] 연합학습 지원

### Phase 4: 미세조정 및 UI 고도화 (~12개월)
- [ ] LoRA/QLoRA 파인튜닝 파이프라인
- [ ] Teacher → Student 지식 증류 자동화
- [ ] 관리자 대시보드 고도화
- [ ] 프롬프트 템플릿 편집 UI
- [ ] A/B 테스트 시스템

### Phase 5: 전사 시스템 통합 (~15개월)
- [ ] ERP/CRM 시스템 연동
- [ ] 엣지 배포
- [ ] 다국어 확장
- [ ] 음성 인터페이스
- [ ] AR/VR 통합

## 📝 참고사항

### 필수 준수사항
1. 모든 API 키는 환경변수로 관리
2. 민감 데이터는 암호화 저장
3. 로그에 개인정보 포함 금지
4. 정기적인 보안 감사 실시

### 문서 관리
- 이 문서는 시스템의 Single Source of Truth
- 모든 변경사항은 즉시 반영
- 버전 관리 및 변경 이력 유지

---

## 📚 참고 문서

- **기술 백서**: `claude12.md` - MOSO / RAG 기반 AI 오케스트레이션 기술 백서 v1.0
- **검증 리포트**: `VALIDATION_REPORT.md` - MCP & Docker 설정 검증 리포트
- **환경 설정**: `.env.example` - 환경변수 보안 템플릿

---
*Last Updated: 2025-01-11*
*Version: 2.1*
*Maintainer: RAG Enterprise Team*
## 🗂️ 프로젝트 구조 관리 규칙

### 디렉토리 구조 원칙
1. **실행 관련 파일만 루트 및 핵심 디렉토리에 위치**
2. **개발/테스트/아카이브는 별도 격리**
3. **데이터와 로그는 자동 생성 위치로만**

### 표준 디렉토리 구조
```
rag-enterprise/
├── app/                    # 메인 애플리케이션 (실행 필수)
├── mcp_servers/            # MCP 서버 구현
├── agents/                 # AI 에이전트
├── config/                 # 설정 파일
├── dev/                    # 개발 전용 (Git 제외)
│   ├── experiments/        # 실험적 코드
│   ├── prototypes/         # 프로토타입
│   ├── notebooks/          # Jupyter notebooks
│   └── sandbox/            # 테스트 샌드박스
├── tests/                  # 테스트 코드
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                   # 프로젝트 문서
├── claudedocs/             # Claude 생성 문서 (Git 제외)
├── archives/               # 보관 (Git 제외)
│   ├── logs/               # 과거 로그
│   ├── backups/            # 백업
│   └── deprecated/         # 사용 중단 코드
├── temp/                   # 임시 파일 (Git 제외, 자동 정리)
├── data/                   # Docker 볼륨 (Git 제외)
├── documents/              # 업로드 문서 (Git 제외)
└── logs/                   # 애플리케이션 로그 (Git 제외)
```

### 파일 생성 규칙

**✅ 허용 위치:**
- **핵심 코드**: `app/`, `mcp_servers/`, `agents/`
- **테스트**: `tests/unit/`, `tests/integration/`, `tests/e2e/`
- **실험**: `dev/experiments/YYYYMMDD_feature_name/`
- **문서**: `docs/`, `claudedocs/`
- **아카이브**: `archives/`

**❌ 금지 위치:**
- ❌ 루트에 `test_*.py` (→ `tests/unit/`)
- ❌ 루트에 `temp_*.py` (→ `temp/`)
- ❌ 루트에 `*_backup.*` (→ `archives/backups/`)
- ❌ 루트에 `*.tmp` (→ `temp/`)

### 자동 정리 규칙
- **임시 파일**: 7일 이상 자동 삭제
- **로그**: 90일 이상 아카이브로 이동
- **아카이브**: 1년 이상 자동 압축

### 관리 스크립트
```bash
# 프로젝트 구조 초기화
bash scripts/setup_project_structure.sh

# 정리 (임시 파일, 로그 아카이브, Python 캐시)
bash scripts/cleanup.sh

# Docker 볼륨 포함 정리
bash scripts/cleanup.sh --docker
```

### 상세 규칙
- 전체 규칙: `PROJECT_STRUCTURE_RULES.md` 참조
- `.gitignore`에 자동 적용됨

---
*Project Structure Version: 1.0 (2025-10-17)*
