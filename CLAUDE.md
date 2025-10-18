# RAG Enterprise - 제조업 특화 멀티모달 AI 플랫폼

## 🎯 Core Vision
**목적**: 산업 문서(거래명세서, 견적서, MSDS, 도면) 자동 수집·분석·검색
**목표**: LLM 상담 자동화 | 비정형 데이터 검색·추천 | 멀티모달 매칭 | RBAC | 지속 학습(LoRA)

## 🏗️ 5-Layer Architecture

```
L1: UI/UX → 관리자 대시보드 | 사용자 포털(Internal/Client)
L2: Orchestration → Teacher(Qwen2.5-7B) | Student(gemma-1B, Qwen2.5-3B) | 지식 증류
L3: RAG → Qdrant 벡터 검색 | sentence-transformers | Re-ranking
L4: Ingestion → 업로드/크롤링 | 오토라벨링 | CLIP/BLIP-2 특징 추출
L5: Infra → MLX/Ollama(로컬) | Groq/OpenAI/Claude(클라우드) | Docker/K8s
```

**상세**: → `docs/ARCHITECTURE.md`

## 🔧 Tech Stack

```yaml
Runtime: Python 3.11 | FastAPI | asyncio
DB: Qdrant(벡터) | Redis(캐시) | PostgreSQL(메타) | MongoDB(문서)
ML: Transformers | sentence-transformers | OpenCLIP | PEFT/LoRA
Env: direnv (.envrc 자동 활성화) | Docker (Colima)
```

**LLM 라우팅**: 복잡도 기반 자동 선택
- Haiku 4.5: 간단한 작업 (complexity < 0.7) → 비용 절감
- Sonnet 4.5: 복잡한 작업 (complexity ≥ 0.7) → 고품질

**임베딩 모델**: gte-Qwen2-7B-instruct (텍스트), OpenCLIP-ViT-H-14 (이미지)
**파서**: Docling (PDF), Pandas (Excel), EasyOCR (이미지), CLIP/BLIP-2 (멀티모달)
**검색**: 하이브리드 (Dense + Sparse BM25) + Cross-encoder Re-ranking

**상세**: → `docs/TECH_STACK.md`

## 🐳 Docker Services (rag_network 172.28.0.0/16)

| Service | IP | Port | CPU/RAM | Role |
|---------|-----|------|---------|------|
| Qdrant | .2 | 6333/6334 | 2/4G | 벡터 검색 |
| Redis | .3 | 6379 | 1/2G | 캐싱 |
| PostgreSQL | .4 | 5432 | 2/4G | 메타데이터 |
| N8N | .5 | 5678 | 2/3G | 워크플로우 |
| Ollama | .6 | 11434 | 4/8G | 로컬 LLM |
| FastAPI | .7 | 8000 | 2/4G | API 서버 |

**명령**: `docker-compose up -d` | `docker-compose ps` | `docker-compose logs -f [service]`
**상세**: → `DEV_ENVIRONMENT.md`

## 🔌 MCP Servers & Agents

**Docker MCP**: qdrant, redis, postgres, n8n, ollama
**Python MCP (.mcp.json)**: filesystem, claude_haiku, qdrant_server, ollama_server

**Custom Agents**:
```yaml
workflow_orchestrator: 파이프라인 조정 (max_workers:4, batch:10)
crawler_scheduler: 크롤링 (6시간 간격)
quality_monitor: RAG 품질 (1시간 간격, metrics: relevance|accuracy|latency)
```

**상세**: → `docs/MCP_AGENTS.md`

## 🎯 Development Status (Phase 1/5)

**완료** ✅:
- RAG 파이프라인 설계
- Docker 환경 (Qdrant|Redis|Postgres|N8N|Ollama)
- FastAPI 컨테이너화
- 기본 API (업로드|검색|통계)
- Health Check

**진행중** 🔄:
- Teacher-Student LLM 구조
- 워크플로우 오케스트레이션
- 상담 시스템 (제품 추천, 불량 문의)

**상세 로드맵**: → `docs/ROADMAP.md` (5단계 상세 전략 + 체크리스트)

## 🗂️ Project Structure

```
app/         → 메인 애플리케이션
mcp_servers/ → MCP 서버 구현
agents/      → AI 에이전트
config/      → 설정 파일 (system_config.yaml 포함)
tests/       → 테스트 (unit|integration|e2e)
dev/         → 실험/프로토타입 (gitignore)
docs/        → 문서
data/        → Docker 볼륨 (gitignore)
```

**규칙**: 루트 파일 금지 → 적절한 디렉토리 사용
**상세**: → `PROJECT_STRUCTURE_RULES.md`

## 📊 Operations

**모니터링**: Prometheus (documents_processed, embedding_latency, search_accuracy, system_health)
**알림**: Critical (즉시) | Warning (1시간) | Info (일일)
**보안**: JWT + RBAC | AES-256 | TLS 1.3 | Audit 로깅
**배포**: Clean Deploy (clean_deploy.sh) | Blue-Green | 점진적 롤아웃

**상세**: → `docs/OPERATIONS.md`

## 📚 Reference Docs

| 문서 | 내용 |
|------|------|
| `docs/ARCHITECTURE.md` | 5계층 상세 설계, 데이터 플로우, 컴포넌트 인터페이스 |
| `docs/TECH_STACK.md` | 임베딩 모델, 파서, 검색 파이프라인, QA 에이전트 |
| `docs/ROADMAP.md` | Phase 1-5 상세 전략, 체크리스트, 성공 기준 |
| `docs/OPERATIONS.md` | 모니터링, 배포, 보안, 알림 정책 |
| `docs/MCP_AGENTS.md` | MCP 서버 및 커스텀 에이전트 상세 |
| `DEV_ENVIRONMENT.md` | 개발 환경, Docker 명령어, 환경변수 |
| `PROJECT_STRUCTURE_RULES.md` | 디렉토리 구조 및 파일 생성 규칙 |
| `claude12.md` | MOSO / RAG 기반 AI 오케스트레이션 기술 백서 |
| `VALIDATION_REPORT.md` | MCP & Docker 설정 검증 리포트 |

---

**Version**: 2.2 | **Updated**: 2025-10-18 | **Team**: RAG Enterprise
**Config Sync**: Enabled | **System Integration**: Active
