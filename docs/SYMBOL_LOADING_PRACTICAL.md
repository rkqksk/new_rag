# 실용적인 심볼 로딩 전략

**목표**: Claude Code 환경에서 **실제로 작동**하는 토큰 절감 방법

---

## ❌ 작동하지 않는 것들 (제외)

1. **자동 섹션 추출 스크립트**: Python 스크립트가 세션 중 자동 실행 안 됨
2. **Ollama 자동 요약**: 매번 Ollama 호출은 비효율적
3. **동적 청킹**: 런타임 처리 불가능

---

## ✅ 실제로 작동하는 방법

### 1. CLAUDE.md 인라인 확장 (즉시 적용 가능)

**현재**:
```markdown
## 📖 Symbol References

§rag.phase2.vector         # VectorSearch specs
```

**개선안**:
```markdown
## 📖 Symbol References

### §rag.phase2.vector (VectorSearch 모듈)
- **파일**: `src/core/vector_search.py` (신규 개발 필요)
- **기능**: Qdrant 연결, 벡터 검색, 하이브리드 검색
- **클래스**: `VectorSearch(qdrant_url, collection_name)`
- **주요 메서드**:
  - `create_collection(vector_dim=384)`: 컬렉션 생성
  - `upsert(points)`: 벡터 업로드
  - `search(query_vector, top_k=10)`: 검색
- **상세**: §rag.phase2.vector.full → docs/RAG_ACTIVATION_STRATEGY.md:77-123

### §rag.phase2.processor (DocumentProcessor 모듈)
- **파일**: `src/core/document_processor.py` (신규 개발 필요)
- **기능**: JSON 파싱, 청킹, 임베딩, Qdrant 업로드
- **재사용**: `.claude/skills/rag-pipeline/scripts/parsers/`
- **상세**: §rag.phase2.processor.full → docs/RAG_ACTIVATION_STRATEGY.md:126-193
```

**효과**:
- 기본 정보는 CLAUDE.md에서 확인 (50 tokens)
- 상세 필요시만 전체 문서 로드 (4,500 tokens)

---

### 2. 주요 문서 수동 요약본 작성

**디렉토리 구조**:
```
docs/
├── ARCHITECTURE.md                          # 31KB (전체)
├── ARCHITECTURE.summary.md                  # 3KB (핵심만 수동 작성)
├── RAG_ACTIVATION_STRATEGY.md               # 18KB (전체)
├── RAG_ACTIVATION_STRATEGY.summary.md       # 2KB (핵심만)
└── FRONTEND_UI_POLICY.md                    # 13KB (전체)
```

**ARCHITECTURE.summary.md 예시**:
```markdown
# Architecture Summary (토큰 절약용)

## 핵심 구조
- 5계층: UI → API → Service → Core → Data
- SKILL → Plugin → MCP 파이프라인
- Vector DB: Qdrant, Ollama: qwen2.5:7b-instruct

## 주요 컴포넌트
- `src/core/rag_pipeline.py`: 이미 구현됨 ✅
- `src/core/embedding_service.py`: 이미 구현됨 ✅
- `src/core/vector_search.py`: 개발 필요 ❌

## 데이터 플로우
1. User query → API (/chat/query)
2. Embedding → Qdrant search
3. Context → Ollama → Response

**전체 문서**: docs/ARCHITECTURE.md (31KB)
```

**효과**:
- 요약: ~500 tokens (vs 7,750 tokens)
- 절감: 93.5%

---

### 3. Skill README 간소화

**현재**:
```
.claude/skills/rag-pipeline/README.md (5KB)
```

**분리**:
```
.claude/skills/rag-pipeline/
├── README.md                    # 500 bytes (핵심만)
├── USAGE.md                     # 2KB (사용법 상세)
├── ARCHITECTURE.md              # 2KB (아키텍처 상세)
```

**README.md (간소화)**:
```markdown
# RAG Pipeline Skill

**Status**: 20% (코드 구조만, 벡터 검색 미구현)

## Commands
- `process`: 문서 처리 (개발 중)
- `query`: RAG 쿼리 (개발 중)
- `search`: 벡터 검색 (개발 중)

## Quick Start
상세: USAGE.md, ARCHITECTURE.md
전략: docs/RAG_ACTIVATION_STRATEGY.md
```

**효과**:
- 핵심 README: ~100 tokens (vs 1,250 tokens)
- 상세 필요시만 USAGE.md, ARCHITECTURE.md 로드

---

### 4. 큰 문서 분할

**RAG_ACTIVATION_STRATEGY.md** 분할:
```
docs/rag/
├── README.md                    # 개요 + 목차 (500 tokens)
├── phase1-analysis.md           # Phase 1 (800 tokens)
├── phase2-development.md        # Phase 2 (2,000 tokens)
├── phase3-infrastructure.md     # Phase 3 (500 tokens)
├── phase4-integration.md        # Phase 4 (800 tokens)
└── phase5-deployment.md         # Phase 5 (400 tokens)
```

**효과**:
- 전체 로드 불필요
- 필요한 Phase만 로드 (500-2,000 tokens)

---

## 📊 실제 적용 계획

### Immediate (오늘)

1. **CLAUDE.md 인라인 확장**:
   - §rag.* 심볼에 핵심 정보 추가 (1-5줄)
   - §arch.* 심볼에 핵심 정보 추가
   - §ui.*, §ollama.* 동일 적용

2. **수동 요약본 작성** (3개만):
   - `ARCHITECTURE.summary.md` (3KB)
   - `RAG_ACTIVATION_STRATEGY.summary.md` (2KB)
   - `FRONTEND_UI_POLICY.summary.md` (2KB)

### This Week

3. **Skill README 간소화**:
   - rag-pipeline/README.md 500 bytes로 축소
   - USAGE.md, ARCHITECTURE.md 분리

4. **문서 분할 검토**:
   - 18KB+ 문서만 분할
   - Phase별, 섹션별 파일 분리

---

## 📈 예상 효과

### 시나리오: RAG 개발 작업

**Before**:
```
1. CLAUDE.md (symbolized): 150 tokens
2. "§rag.phase2 확인" → RAG_ACTIVATION_STRATEGY.md 전체 로드: 4,500 tokens
──────────────────
Total: 4,650 tokens
```

**After** (인라인 확장):
```
1. CLAUDE.md (expanded): 300 tokens
2. §rag.phase2 인라인 정보로 충분: 0 tokens
3. 상세 필요시만: RAG_ACTIVATION_STRATEGY.summary.md: 500 tokens
──────────────────
Total: 300-800 tokens
```

**절감**: 83-93% (4,650 → 300-800 tokens)

---

## 🎯 핵심 원칙

1. **수동 작성**: 자동화 스크립트 의존 X
2. **인라인 우선**: CLAUDE.md에 핵심 내용 직접 포함
3. **선택적 로드**: 필요할 때만 상세 문서 읽기
4. **실용성**: 실제 Claude Code 워크플로우에 맞춤

---

**Version**: 1.0.0 (Practical)
**Created**: 2025-11-04
**Next**: CLAUDE.md 인라인 확장 작업
