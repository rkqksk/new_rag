# RAG Enterprise - Claude Project Context

**Production-grade RAG system with multi-model support, vector search, and monitoring.**

---

## 🎯 프로젝트 개요

### 핵심 목표
- **고품질 RAG**: 문서 기반 정확한 답변 생성
- **확장 가능**: 플러그인 아키텍처로 기능 확장
- **프로덕션 준비**: 모니터링, 로깅, 에러 처리 완비
- **멀티 모델**: OpenAI, Anthropic, 로컬 LLM 지원

### 기술 스택
- **Backend**: FastAPI (Python 3.11+)
- **Vector DB**: Qdrant + PostgreSQL/pgvector
- **Cache**: Redis
- **Container**: Docker Compose
- **Testing**: pytest (80%+ coverage)
- **Monitoring**: Structlog + Prometheus

---

## 📁 프로젝트 구조

```
rag-enterprise/
├── src/
│   ├── api/              # FastAPI 엔드포인트
│   │   ├── routes/       # API 라우트
│   │   └── dependencies/ # 의존성 주입
│   ├── core/             # 비즈니스 로직
│   │   ├── rag_engine.py      # RAG 메인 엔진
│   │   ├── embeddings.py      # 임베딩 생성
│   │   ├── retrieval.py       # 문서 검색
│   │   └── document_processor.py
│   ├── models/           # Pydantic 스키마
│   ├── services/         # 외부 서비스
│   │   ├── openai_service.py
│   │   ├── anthropic_service.py
│   │   └── qdrant_service.py
│   └── utils/            # 유틸리티
│       ├── logging.py
│       ├── config.py
│       └── validators.py
├── tests/                # 테스트 스위트
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/               # 환경 설정
│   ├── dev.env
│   ├── staging.env
│   └── production.env
├── docs/                 # 문서
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── DEPLOYMENT.md
│   └── MONITORING.md
├── scripts/              # 유틸리티 스크립트
│   ├── setup.sh
│   ├── benchmark.py
│   └── maintenance/
│       └── auto_organize_docs.py  # 문서 자동 정리
├── plugins/              # 플러그인 시스템
├── .claude/              # Claude 설정
│   ├── commands/         # 커스텀 명령어 (17개)
│   └── skills/           # 프로젝트 스킬 (6개)
│       ├── rag-master/              # 통합 orchestration
│       ├── rag-document-processor/  # 문서 처리
│       ├── rag-vector-search/       # 벡터 검색
│       ├── rag_pipeline/            # RAG 파이프라인
│       ├── agent_orchestration/     # 에이전트 관리
│       └── note_management/         # Obsidian 연동
├── docker-compose.yml    # 서비스 정의
├── .mcp.json            # MCP 서버 설정
├── CLAUDE.md            # ← 이 파일
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repo-url>
cd rag-enterprise

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집: API 키, DB 정보 입력

# Docker 서비스 시작
docker-compose up -d

# 의존성 설치
pip install -r requirements.txt --break-system-packages
```

### 2. 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v --cov=src

# 특정 테스트
pytest tests/test_rag_engine.py -v
```

### 3. API 서버 실행

```bash
# 개발 모드
python run_chat_server.py

# 또는 uvicorn
uvicorn src.api.main:app --reload --port 8000
```

### 4. 문서 추가 & 검색

```python
# 문서 업로드
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@document.pdf"

# RAG 쿼리
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "사용자 인증 방법은?"}'
```

---

## 🛠️ 개발 규칙

### 코드 스타일
1. **Python 3.11+**: Type hints 필수
2. **Async/Await**: I/O 작업은 비동기
3. **Pydantic**: 모든 데이터 검증
4. **Logging**: Structlog JSON 형식
5. **에러 처리**: 커스텀 예외 + HTTP 상태 코드

### 테스트 규칙
- **Coverage**: 최소 80%
- **Fixtures**: pytest fixtures 활용
- **Mocking**: 외부 API는 mock
- **CI/CD**: PR마다 자동 테스트

### 문서화
- **Docstrings**: Google style
- **API Docs**: OpenAPI 자동 생성
- **README**: 각 모듈별 README.md

---

## 🎨 스킬 시스템

이 프로젝트는 **6개의 전문 스킬**을 사용합니다:

### 1. **rag-master** 🎯
통합 orchestration 스킬. 모든 작업의 진입점.

**활성화**: 프로젝트 전반적인 작업 시
- 새 기능 추가
- 배포 준비
- 전체 시스템 디버깅

**주요 기능**:
- 워크플로우 관리
- 다른 스킬 coordinating
- 프로젝트 표준 설정

**파일 위치**: `.claude/skills/rag-master/SKILL.md`

---

### 2. **rag-document-processor** 📄
문서 파싱 및 전처리 전문 스킬

**활성화**: 문서 처리 시
- PDF, DOCX, XLSX 업로드
- 문서 청킹
- OCR, 표 추출

**주요 기능**:
```python
# 문서 처리
from src.core.document_processor import process_document
result = process_document("file.pdf")
# → {text, tables, metadata, chunks}
```

**파일 위치**: `.claude/skills/rag-document-processor/SKILL.md`

---

### 3. **rag-vector-search** 🔍
벡터 검색 및 유사도 계산 스킬

**활성화**: 검색 관련 작업 시
- 벡터 검색 최적화
- 하이브리드 검색 구현
- 재순위 알고리즘

**주요 기능**:
```python
# 벡터 검색
from src.core.vector_search import search
results = search(query="...", top_k=10)
```

**파일 위치**: `.claude/skills/rag-vector-search/SKILL.md`

---

### 4. **rag_pipeline** 🔄
전체 RAG 파이프라인 관리 스킬

**활성화**: RAG 플로우 전체 작업 시
- 쿼리 → 검색 → 생성
- 프롬프트 엔지니어링
- 응답 후처리

**주요 기능**:
```python
# RAG 파이프라인
from src.core.rag_engine import RAGEngine
engine = RAGEngine()
answer = engine.query("질문")
```

**파일 위치**: `.claude/skills/rag_pipeline/SKILL.md`

---

### 5. **agent_orchestration** 🤖
멀티 에이전트 시스템 관리 스킬

**활성화**: 복잡한 작업 분해 시
- 작업 분배
- 에이전트 간 통신
- 결과 통합

**파일 위치**: `.claude/skills/agent_orchestration/SKILL.md`

---

### 6. **note_management** 📝
Obsidian 연동 및 노트 관리 스킬

**활성화**: 문서 관리 작업 시
- Obsidian 볼트 연동
- 마크다운 처리
- 지식 그래프 생성

**파일 위치**: `.claude/skills/note_management/SKILL.md`

---

## 🔌 MCP (Model Context Protocol)

**현재 프로필**: `max` (모든 기능 활성화)
**총 서버**: 7개
**토큰 사용량**: ~2,100 tokens

### 서버 목록 및 사용법

#### 1. filesystem
**기능**: 프로젝트 파일 시스템 접근
```bash
# 자동 활성화 - 파일 읽기/쓰기 자동화
```

#### 2. claude_api
**기능**: Claude API 통합 (Haiku 4.5 + Sonnet 4.5)
```python
# Python에서 Claude API 호출
response = await call_claude_api({
    "model": "claude-sonnet-4.5",
    "prompt": "Analyze this document..."
})
```

#### 3. chrome_devtools
**기능**: 브라우저 자동화 (Chrome DevTools Protocol)
```python
# 웹 스크래핑, UI 테스트
await browser.navigate("https://example.com")
```

#### 4. qdrant
**기능**: 벡터 데이터베이스 (의미 기반 검색)
```python
# 임베딩 저장
await qdrant.upsert(
    collection="documents",
    points=[{
        "vector": embedding,
        "payload": metadata
    }]
)

# 유사도 검색
results = await qdrant.search(
    collection="documents",
    query_vector=query_embedding,
    limit=10
)
```

#### 5. ollama
**기능**: 로컬 LLM (Ollama)
```python
# 로컬 모델 실행 (비용 없음)
response = await ollama.generate(
    model="llama3.1",
    prompt="Summarize..."
)
```

#### 6. rag_orchestrator
**기능**: RAG 파이프라인 오케스트레이션
```python
# 문서 처리
result = await rag_orchestrator.process_document(
    file_path="document.pdf",
    options={
        "use_domain_expert": True,
        "chunk_strategy": "semantic"
    }
)

# RAG 쿼리
answer = await rag_orchestrator.query(
    query="What are the specs?",
    collection="tech_docs"
)
```

#### 7. note_keeper
**기능**: 문서 관리 및 진행상황 추적
```python
# 노트 생성
await note_keeper.create_note(
    title="Sprint 1 Progress",
    content="...",
    tags=["sprint", "dev"]
)
```

### MCP 서버 관리

```bash
# 서버 추가
# .mcp.json 편집 후 Claude 재시작

# 현재 활성 서버 확인
cat .mcp.json

# 프로필 전환 (필요시)
# dev: 최소 기능
# standard: 일반 개발
# max: 모든 기능 (현재)
```

---

## 🧩 도메인 전문가 플러그인

**위치**: `plugins/`
**타입**: Python 패키지 (직접 실행 가능)
**상태**: ✅ 2개 설치 및 테스트 완료

### 1. Manufacturing Expert Plugin

**경로**: `plugins/manufacturing_expert/`

#### 핵심 기능
- ✅ **문서 자동 분류**: SOP, FMEA, 배치 기록, 결함 분석 등 8가지 타입
- ✅ **용어 추출**: Cpk, OEE, PPM, MTBF 등 150+ 제조 용어
- ✅ **파라미터 인식**: 온도, 압력, 시간, 속도, 유량 등
- ✅ **품질 지표**: Cpk, OEE, Yield, 결함률 자동 추출
- ✅ **규격 참조**: ISO 9001, FDA 21 CFR Part 11, GMP 등

#### 사용법
```python
from plugins.manufacturing_expert import ManufacturingExpertPlugin

plugin = ManufacturingExpertPlugin()

document = {
    'filename': 'SOP-001.pdf',
    'content': '...',
    'metadata': {}
}

result = plugin.process_document(document)

if result.success:
    print(f"Document Type: {result.metadata.doc_type}")
    print(f"Terminology: {result.metadata.terminology}")
    print(f"Quality Metrics: {result.metadata.extracted_entities['quality_metrics']}")
```

---

### 2. Packaging Expert Plugin

**경로**: `plugins/packaging_expert/`

#### 핵심 기능
- ✅ **문서 분류**: 재질 사양, 컨테이너 도면, 규제 문서 등 6가지 타입
- ✅ **재질 인식**: PET, HDPE, PP, PS, PVC 등 40+ 재질
- ✅ **치수 추출**: 높이, 직경, 두께, 용량, 무게
- ✅ **차단 특성**: 산소 투과율, 수분 투과율
- ✅ **규제 준수**: FDA, EU, REACH, RoHS 등

#### 사용법
```python
from plugins.packaging_expert import PackagingExpertPlugin

plugin = PackagingExpertPlugin()
result = plugin.process_document(document)

if result.success:
    materials = result.metadata.extracted_entities['materials']
    dimensions = result.metadata.extracted_entities['dimensions']
    standards = result.metadata.extracted_entities['standards']
```

---

### 플러그인 매니저

**파일**: `plugins/test_plugins.py`

#### 기능
- 모든 플러그인 자동 로드
- 문서에 맞는 플러그인 자동 선택 (신뢰도 기반)
- RAG 파이프라인 통합 지원

#### 사용법
```python
from plugins.test_plugins import PluginManager

# 자동 로드
manager = PluginManager()

# 자동 매칭 및 처리
result = manager.process_document(document)

# RAG 파이프라인 통합
enriched_data = {
    'content': result.enriched_content,
    'chunks': result.chunks,
    'metadata': {
        'doc_type': result.metadata.doc_type,
        'domain': result.metadata.domain,
        'terminology': result.metadata.terminology,
        'entities': result.metadata.extracted_entities
    }
}
```

---

## 🔄 통합 워크플로우

### 시나리오: 제조 문서 RAG 파이프라인

```python
# Step 1: 문서 로드
document = load_pdf("manufacturing_sop.pdf")

# Step 2: 도메인 전문가 플러그인 처리
from plugins.test_plugins import PluginManager
manager = PluginManager()
result = manager.process_document(document)

# Step 3: 강화된 메타데이터 생성
enriched_doc = {
    'content': result.enriched_content,
    'metadata': {
        'doc_type': result.metadata.doc_type,
        'domain': result.metadata.domain,
        'terminology': result.metadata.terminology,
        'quality_metrics': result.metadata.extracted_entities['quality_metrics'],
        'parameters': result.metadata.extracted_entities['parameters']
    }
}

# Step 4: 벡터 DB 저장 (MCP 서버 사용)
await qdrant.upsert(
    collection="manufacturing_docs",
    points=[{
        'id': doc_id,
        'vector': embed(enriched_doc['content']),
        'payload': enriched_doc['metadata']
    }]
)

# Step 5: 검색 및 응답 생성
query = "What are the temperature requirements for calibration?"
results = await qdrant.search(
    collection="manufacturing_docs",
    query_vector=embed(query),
    limit=5,
    filter={
        'doc_type': 'sop',
        'terminology': {'$contains': 'calibration'}
    }
)

# Step 6: Claude API로 답변 생성
answer = await claude_api.generate(
    model="claude-sonnet-4.5",
    context=results,
    query=query
)
```

---

## 📚 Task References

작업별 참고 문서:

| 작업 | 참고 문서 |
|------|----------|
| **아키텍처 설계** | `docs/ARCHITECTURE.md` |
| **API 개발** | `docs/API_REFERENCE.md`, `src/api/README.md` |
| **RAG 엔진** | `src/core/rag_engine.py`, `.claude/skills/rag_pipeline/` |
| **문서 처리** | `.claude/skills/rag-document-processor/` |
| **벡터 검색** | `.claude/skills/rag-vector-search/` |
| **테스트** | `tests/README.md`, `pytest.ini` |
| **배포** | `docs/DEPLOYMENT.md`, `docker-compose.yml` |
| **모니터링** | `docs/MONITORING.md`, `src/utils/logging.py` |
| **데이터베이스** | `src/models/`, `alembic/` (migration) |
| **Docker** | `Dockerfile`, `docker-compose.yml` |

---

## 🔧 자주 사용하는 명령어

### 개발
```bash
# 개발 서버 시작
python run_chat_server.py

# 테스트 (coverage 포함)
pytest tests/ -v --cov=src --cov-report=html

# 코드 포맷팅
black src/ tests/
isort src/ tests/

# 타입 체크
mypy src/

# 린팅
flake8 src/ tests/
```

### Docker
```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api

# 재시작
docker-compose restart api

# 정리
docker-compose down -v
```

### 문서 관리
```bash
# 문서 자동 정리 (미리보기)
python3 scripts/maintenance/auto_organize_docs.py

# 실제 정리 실행
python3 scripts/maintenance/auto_organize_docs.py --execute

# 주간 정리
./scripts/maintenance/weekly_organize.sh
```

### 데이터베이스
```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "Add new table"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

---

## 🎯 작업 시나리오별 가이드

### 새 API 엔드포인트 추가

1. **스킬 활성화**: `rag-master`
2. **라우트 정의**: `src/api/routes/new_route.py`
3. **비즈니스 로직**: `src/core/new_feature.py`
4. **스키마 정의**: `src/models/schemas.py`
5. **테스트 작성**: `tests/test_new_route.py`
6. **문서 업데이트**: `docs/API_REFERENCE.md`

### 문서 처리 개선

1. **스킬 활성화**: `rag-document-processor`
2. **파서 추가**: `src/core/document_processor.py`
3. **테스트**: `tests/test_document_processor.py`
4. **벤치마크**: `scripts/benchmark.py`

### 검색 성능 최적화

1. **스킬 활성화**: `rag-vector-search`
2. **인덱스 최적화**: Qdrant/pgvector 설정
3. **재순위 알고리즘**: `src/core/retrieval.py`
4. **성능 측정**: `scripts/benchmark.py`

### 배포 준비

1. **스킬 활성화**: `rag-master`
2. **환경 설정**: `config/production.env`
3. **Docker 빌드**: `docker-compose -f docker-compose.production.yml build`
4. **스모크 테스트**: `pytest tests/smoke/`
5. **배포**: `docker-compose -f docker-compose.production.yml up -d`

---

## 🐛 트러블슈팅

### 문제: API 응답 느림
**해결**:
1. 로그 확인: `docker-compose logs api`
2. 병목 지점 찾기: `scripts/benchmark.py`
3. 캐시 확인: Redis 연결 상태
4. 인덱스 최적화: Qdrant 인덱스 재구성

### 문제: 문서 파싱 실패
**해결**:
1. 스킬 활성화: `rag-document-processor`
2. 로그 확인: 에러 메시지 분석
3. Docling 재설치: `pip install --upgrade docling`
4. OCR 언어팩: `tesseract --list-langs`

### 문제: 벡터 검색 정확도 낮음
**해결**:
1. 스킬 활성화: `rag-vector-search`
2. 임베딩 모델 확인: 현재 사용 중인 모델
3. 청킹 전략 조정: 청크 크기 & 오버랩
4. 재순위 알고리즘: 하이브리드 검색 적용

---

## 📊 성능 목표

| 메트릭 | 목표 | 현재 | 상태 |
|--------|------|------|------|
| API 응답 시간 | < 200ms | - | 🔄 |
| RAG 답변 생성 | < 2초 | - | 🔄 |
| 문서 처리 (10p PDF) | < 5초 | - | 🔄 |
| 벡터 검색 (top-10) | < 100ms | - | 🔄 |
| API 처리량 | > 100 req/s | - | 🔄 |
| 테스트 커버리지 | > 80% | - | 🔄 |

### 벤치마크 실행
```bash
python scripts/benchmark.py --test=all --output=report.json
```

---

## 🔐 보안

### 체크리스트
- [ ] API 키는 `.env`에만 저장
- [ ] `.env`는 `.gitignore`에 포함
- [ ] Input validation (Pydantic)
- [ ] Rate limiting 설정
- [ ] SQL injection 방어
- [ ] XSS 방어
- [ ] CORS 설정
- [ ] HTTPS 인증서 (프로덕션)

### 민감 정보 관리
```bash
# .env 예시
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_PASSWORD=<strong_password>

# Git에 절대 커밋하지 않기!
```

---

## 📖 학습 리소스

### 내부 문서
- [시스템 아키텍처](docs/ARCHITECTURE.md)
- [API 레퍼런스](docs/API_REFERENCE.md)
- [배포 가이드](docs/DEPLOYMENT.md)
- [모니터링 설정](docs/MONITORING.md)

### 외부 리소스
- [FastAPI 공식 문서](https://fastapi.tiangolo.com)
- [Qdrant 가이드](https://qdrant.tech/documentation/)
- [Pgvector 튜토리얼](https://github.com/pgvector/pgvector)
- [Pydantic 문서](https://docs.pydantic.dev/)

---

## 🔄 Dynamic Loading

**컨텍스트가 필요한 경우 동적으로 로드**:

- **API 라우트 수정** → `src/api/README.md` + `docs/API_REFERENCE.md`
- **RAG 엔진 변경** → `src/core/rag_engine.py` + `.claude/skills/rag_pipeline/`
- **문서 처리 개선** → `.claude/skills/rag-document-processor/`
- **벡터 검색 최적화** → `.claude/skills/rag-vector-search/`
- **테스트 추가** → `tests/README.md` + `pytest.ini`
- **Docker 문제** → `docker-compose.yml` + `Dockerfile`
- **DB 스키마 변경** → `src/models/` + `alembic/`

---

## 📝 버전 정보

- **Version**: 2.0.0
- **Python**: 3.11+
- **FastAPI**: 0.109+
- **Qdrant**: 1.7+
- **PostgreSQL**: 15+ (pgvector)
- **Redis**: 7.0+

---

## 📞 지원 & 기여

### 버그 리포트
GitHub Issues에 버그 리포트 작성

### 기능 요청
GitHub Discussions에 제안

### 기여 가이드
1. Fork 저장소
2. Feature branch 생성
3. 변경사항 커밋
4. PR 생성
5. 코드 리뷰 대기

---

**Last Updated**: 2025-01-24  
**Maintained By**: RAG Enterprise Team  
**License**: MIT
