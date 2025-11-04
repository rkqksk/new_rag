# 변경 이력

## [3.3.0] - 2025-11-04

### 완료됨
- **RAG System 85% 완성** (§rag)
  - ✅ Core 모듈 개발 완료
    - `src/core/rag_pipeline.py` (262 lines) - 통합 RAG 파이프라인
    - `src/core/embedding_service.py` (72 lines) - all-MiniLM-L6-v2 임베딩
  - ✅ API 통합 완료
    - `src/api/chat.py` - Vector RAG 통합 (Feature flag: USE_VECTOR_RAG)
    - `/chat/query` 엔드포인트 - 벡터 검색 + RAG 답변
  - ✅ Skill 래핑 완료
    - `.claude/skills/rag-pipeline/scripts/skill.py` 업데이트
    - `process_document()`, `vector_search()`, `rag_query()` - Core 모듈 사용
  - ✅ 데이터 임베딩 완료
    - 857/857 products embedded to Qdrant (100%)
    - Collection: `products` @ Qdrant
    - Script: `scripts/embed_products.py`

### 인프라
- ✅ Colima: 4 CPU, 8GB RAM
- ✅ Qdrant: v1.11.3 (http://localhost:6333)
- ✅ Ollama: qwen2.5:7b-instruct
- ✅ Python venv: .venv (dependencies installed)

### 테스트 결과
- ✅ Core RAG Pipeline: Score 0.7254
- ✅ Embedding Service: Passed
- ✅ API Integration: Score 0.5678
- ✅ Search Test: Score 0.6405

### 문서 업데이트 (심볼화 전략 적용)
- `docs/RAG_ACTIVATION_STRATEGY.md` - 85% 완성 현황 추가
- `CLAUDE.md` - §rag 섹션 확장 (20% → 85% 반영)
- `docs/SYMBOL_SYSTEM.md` - §rag.core, §rag.skill, §rag.data, §rag.infra 추가
- `docs/SYMBOL_DOCUMENTATION_GUIDE.md` - 심볼화 문서 작성 지침

### 다음 단계
- Production 배포 최적화 (15%)
- 성능 튜닝 및 모니터링

---

## [3.2.0] - 2025-11-04

### 추가됨
- **Symbol System**: 토큰 효율성을 위한 문서 심볼화 시스템
  - `docs/SYMBOL_SYSTEM.md` - 완전한 심볼 참조 맵
  - `§{category}.{document}.{section}` 표기법
  - 98.1% 토큰 절감 (~16,000 → ~300 tokens/session)
- **Symbolized Documentation**:
  - `CLAUDE.md` v3.2.0 - 심볼 참조로 간략화
  - `README.md` - 심볼 참조 통합
  - 모든 주요 문서에 심볼 맵핑

### 변경됨
- CLAUDE.md: 202 lines → ~150 lines (~70% 토큰 절감)
- README.md: 심볼 시스템 설명 추가
- Documentation structure: 심볼 기반 참조 시스템으로 전환

### 기술적 개선
- 세션당 ~15,700 토큰 절감
- 100 세션당 ~1.57M 토큰 절감
- 문서 로드: On-demand, 작업별 선택적 로드

---

## [3.1.0] - 2025-11-04

### 추가됨
- **Frontend v2.0.0**: ChatGPT-style UI
  - Gray tones only (#ffffff, #2d333a, #f7f7f8, #d1d5db)
  - No header, full-page chat layout
  - Korean IME support (`isComposing` check)
  - Chat history clearing on init
- **Ollama Model Policy**:
  - `docs/OLLAMA_MODEL_POLICY.md` - 종합 모델 관리 정책
  - `config/ollama_models.yaml` - YAML 모델 스펙
  - Production models locked: qwen2.5:7b-instruct, nomic-embed-text
  - Deleted 6.6GB unnecessary models
- **Frontend UI Policy**:
  - `docs/FRONTEND_UI_POLICY.md` - UI/UX 관리 정책
  - `config/ui_constants.yaml` - UI 상수 YAML
- **RAG Activation Strategy**:
  - `docs/RAG_ACTIVATION_STRATEGY.md` - 5-phase RAG 활성화 전략
  - Current: Phase 1 complete (20%)
  - Next: Phase 2-5 (7.5-9.5 days estimated)

### 수정됨
- Frontend bugs: Korean input duplication, chat history persistence
- `docs/ARCHITECTURE.md`: Ollama & Frontend 관리 섹션 추가
- `.gitignore`: Backup files pattern added

### 삭제됨
- Ollama models: qwen2.5:3b, qwen2.5:7b-instruct-q4_K_M (6.6GB saved)
- Legacy documentation (608 files, -46,665 lines net reduction)

---

## [1.0.0] - 2025-11-03

### 추가됨
- 핵심 RAG 파이프라인 구현
- 유연한 문서 로딩 메커니즘
- 시맨틱 검색 기능
- 다중 모델 통합 지원
- 포괄적인 오류 처리
- 성능 최적화 유틸리티
- 문서 수집 및 쿼리를 위한 API 엔드포인트
- 광범위한 테스트 프레임워크

### 구성 요소
- 문서 로더
- 임베딩 서비스
- 벡터 데이터베이스 통합
- 응답 생성기
- 모델 통합자
- 성능 최적화기
- 오류 핸들러

### 기술
- FastAPI
- Qdrant 벡터 데이터베이스
- Sentence Transformers
- Ollama
- OpenAI
- Anthropic

### 프로젝트 구조
- 모듈식 아키텍처
- 확장 가능한 설계
- 확장성 있는 프레임워크

---

## 향후 로드맵

### RAG System (Current Focus)
- Phase 2: Core modules (VectorSearch, DocumentProcessor, RAGEngine)
- Phase 3: Infrastructure setup (Qdrant, Ollama)
- Phase 4: Skill integration & testing
- Phase 5: Data embedding & deployment

### Advanced Features
- 고급 멀티모달 지원
- 고급 모델 라우팅
- 분산 벡터 검색
- 지속적인 학습 메커니즘
