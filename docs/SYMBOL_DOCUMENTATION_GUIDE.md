# 심볼화 문서 작성 지침

**목적**: 모든 시스템 문서를 심볼화하여 토큰 효율성 극대화

---

## 🎯 핵심 원칙

### 1. 인라인 확장 우선 (Inline First)
CLAUDE.md에 핵심 정보를 직접 포함

**나쁜 예**:
```markdown
§rag.phase2.vector         # VectorSearch specs
```

**좋은 예**:
```markdown
**§rag.phase2.vector** - VectorSearch 모듈:
- File: `src/core/vector_search.py` (신규)
- Qdrant 연결, 벡터 검색, 메타데이터 필터링
- Main: `VectorSearch(qdrant_url, collection_name)`
- Methods: create_collection(), upsert(), search()
```

---

### 2. 계층적 구조 (3-Level Hierarchy)

```
Level 1: §category                    → 개요 (CLAUDE.md에 인라인)
Level 2: §category.section            → 섹션 요약 (CLAUDE.md 또는 .summary.md)
Level 3: §category.section.detail     → 전체 상세 (원본 문서)
```

**예시**:
```
§rag                    → RAG 전략 개요 + 상태 (CLAUDE.md)
§rag.phase2             → Phase 2 모듈 3개 요약 (CLAUDE.md)
§rag.phase2.full        → 전체 상세 (RAG_ACTIVATION_STRATEGY.md)
```

---

### 3. 수동 요약본 작성 (Manual Summaries)

자동화 의존 X, 수동으로 핵심만 추출

**파일 구조**:
```
docs/
├── ARCHITECTURE.md                    # 전체 (31KB)
├── ARCHITECTURE.summary.md            # 핵심만 (3KB, 수동 작성)
└── RAG_ACTIVATION_STRATEGY.md         # 전체 (18KB)
```

**요약 작성 기준**:
- 원본의 10-20% 길이
- 핵심 개념만 포함
- 코드 예시는 최소화
- 전체 문서 참조 링크 포함

---

## 📝 문서 작성/업데이트 체크리스트

### 새 문서 작성 시

- [ ] **1단계**: 심볼 정의
  ```markdown
  > **Symbol Reference**: §category.section
  > **Quick Access**: See `CLAUDE.md` for quick reference
  ```

- [ ] **2단계**: CLAUDE.md에 인라인 추가
  ```markdown
  #### §category.section - 제목
  **핵심 정보** (3-5줄):
  - 주요 기능
  - 파일 위치
  - 사용법
  **Full Details**: docs/DOCUMENT.md (크기)
  ```

- [ ] **3단계**: SYMBOL_SYSTEM.md에 맵핑 추가
  ```markdown
  ### §category - Category Name
  **Size**: XKB | **Auto-load**: No

  ```
  §category.section          → 섹션 설명
  §category.section.detail   → 상세 설명
  ```
  ```

- [ ] **4단계**: 요약본 작성 (선택, 10KB+ 문서만)
  ```
  docs/DOCUMENT.summary.md (원본의 10-20%)
  ```

---

### 기존 문서 업데이트 시

- [ ] **1단계**: 원본 문서 업데이트

- [ ] **2단계**: CLAUDE.md 인라인 정보 동기화
  - 주요 변경사항 반영
  - 버전/상태 업데이트

- [ ] **3단계**: 요약본 동기화 (있는 경우)

- [ ] **4단계**: CHANGELOG.md 업데이트

---

## 🎨 심볼 네이밍 규칙

### 카테고리 (1단계)
```
§arch      - Architecture
§rag       - RAG system
§ui        - Frontend UI/UX
§ollama    - Model management
§deploy    - Deployment
§tech      - Technology stack
§skill     - Skill system
```

### 섹션 (2단계)
```
§category.overview          → 개요
§category.status            → 현재 상태
§category.core              → 핵심 컴포넌트
§category.phase1            → Phase/단계
§category.design            → 디자인 시스템
```

### 상세 (3단계)
```
§category.section.detail    → 섹션 상세
§category.section.code      → 코드 예시
§category.section.full      → 전체 문서
```

---

## 📊 예시: RAG 시스템 업데이트

### 시나리오: Core 모듈 완성 후 문서 업데이트

**1단계: 원본 업데이트**
```markdown
# docs/RAG_ACTIVATION_STRATEGY.md

## 현재 상태

**Status**: ~~20%~~ → **60% 완성**
- ✅ Phase 1: 분석 완료
- ✅ Phase 2: Core 모듈 개발 완료  ← 업데이트
- ⏳ Phase 3: 인프라 설정 (진행 중)
```

**2단계: CLAUDE.md 동기화**
```markdown
# CLAUDE.md

#### §rag - RAG Activation Strategy
**Status**: ~~20%~~ → **60% complete**  ← 업데이트
**Next**: ~~Phase 2~~ → Phase 3 - Infrastructure  ← 업데이트

**§rag.core** - 완성된 모듈:  ← 새로 추가
- ✅ `src/core/rag_pipeline.py` (완전 구현)
- ✅ `src/core/embedding_service.py` (테스트 완료)
- ✅ Qdrant 연결 (작동 확인)
- ✅ Ollama 답변 생성 (테스트 통과)
```

**3단계: SYMBOL_SYSTEM.md 업데이트**
```markdown
### §rag - RAG Activation Strategy

**Status**: 60% complete  ← 업데이트

```
§rag.status                # 60% (Phase 1-2 완료)  ← 업데이트
§rag.core                  # 완성된 Core 모듈  ← 새로 추가
§rag.core.pipeline         # RAGPipeline 클래스
§rag.core.embedding        # EmbeddingService
§rag.phase3                # Next: Infrastructure
```
```

**4단계: CHANGELOG.md**
```markdown
## [3.3.0] - 2025-11-04

### 완료됨
- **Core RAG 모듈 완성** (§rag.core)
  - `src/core/rag_pipeline.py` 테스트 통과
  - Qdrant 연결 확인
  - 벡터 검색 작동 (Score: 0.7254)
  - Ollama 답변 생성 성공
```

---

## ⚠️ 피해야 할 것들

### ❌ 자동화 도구 의존
```python
# 작동 안 함 - Python 스크립트 자동 실행 불가
python scripts/auto_symbol_generator.py
```

### ❌ 심볼 없는 문서
```markdown
# Bad - 심볼 참조 없음
# RAG Activation Strategy
...
```

### ❌ CLAUDE.md에 심볼만 나열
```markdown
# Bad - 정보 없음
§rag.phase2.vector         # VectorSearch specs
§rag.phase2.processor      # DocumentProcessor specs
```

### ❌ 거대한 단일 문서
```markdown
# Bad - 100KB 문서를 분할하지 않음
MEGA_ARCHITECTURE.md (100KB)
```

---

## ✅ 모범 사례

### 1. CLAUDE.md 인라인 확장
```markdown
#### §rag.core - 완성된 Core 모듈
**Status**: ✅ Production Ready

**Components**:
- `rag_pipeline.py` (256 lines)
  - `RAGPipeline`: 통합 파이프라인
  - `ingest_documents()`: 문서 저장
  - `retrieve()`: 벡터 검색
  - `generate_response()`: Ollama 답변

- `embedding_service.py` (72 lines)
  - Model: all-MiniLM-L6-v2 (384 dim)
  - GPU 지원

**Test Results**: ✅ All passed (Score: 0.7254)
**Full Details**: docs/RAG_ACTIVATION_STRATEGY.md (18KB)
```

### 2. 요약본 작성
```markdown
# docs/RAG_ACTIVATION_STRATEGY.summary.md

# RAG Strategy - Summary

**Goal**: 857개 제품 벡터 검색

**Status**: 60% (Phase 1-2 완료)

**Phase 1**: ✅ 분석
**Phase 2**: ✅ Core 모듈 (rag_pipeline.py, embedding_service.py)
**Phase 3**: ⏳ Infrastructure (Qdrant, Ollama)
**Phase 4**: ⏳ Skill 통합
**Phase 5**: ⏳ 데이터 임베딩

**Core 모듈**: src/core/rag_pipeline.py (완성)
**Test**: ✅ 통과 (Qdrant, Embedding, Search, Generation)

**Full**: docs/RAG_ACTIVATION_STRATEGY.md (18KB)
```

### 3. 큰 문서 분할
```
docs/rag/
├── README.md                    # 개요 + 목차 (§rag)
├── phase1-analysis.md           # Phase 1 (§rag.phase1)
├── phase2-core-modules.md       # Phase 2 (§rag.phase2)
├── phase3-infrastructure.md     # Phase 3 (§rag.phase3)
```

---

## 🚀 빠른 참조

| 작업 | 명령 |
|------|------|
| 새 심볼 추가 | SYMBOL_SYSTEM.md + CLAUDE.md 업데이트 |
| 문서 업데이트 | 1. 원본 → 2. CLAUDE.md → 3. CHANGELOG.md |
| 요약본 작성 | 원본의 10-20%, 핵심만 |
| 큰 문서 분할 | 10KB+ → Phase/섹션별 파일 분리 |

---

**Version**: 1.0.0
**Created**: 2025-11-04
**Compliance**: All future docs must follow this guide
