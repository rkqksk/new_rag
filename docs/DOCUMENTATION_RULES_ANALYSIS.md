# Documentation Rules Analysis - CLI vs Web

**Created**: 2025-11-16
**Issue**: 최상위 디렉토리에 문서가 22개 - 규칙 없이 생성되고 있음

---

## 🔍 문제 발견

### 현재 상태
```bash
# 최상위 마크다운 문서: 22개
BACKEND_MIGRATION_PLAN.md
CLAUDE.md
COMPLETE_INTEGRATION_MASTER_PLAN.md
CONTRIBUTING.md
DEPLOYMENT.md
DEVELOPMENT_ENVIRONMENT_EXECUTION_PLAN.md
FINAL_DIAGNOSIS.md
FRONTEND_FILE_STRUCTURE_PLAN.md
FRONTEND_INTEGRATION_SUMMARY.md
INTEGRATION_PLAN_V10.md
MIGRATION_CHECKLIST.md
PHASE1_DEPLOYMENT_CHECKLIST.md
PROGRESS.md
QUICK_START_UPDATED.md
README.md
READY_TO_EXECUTE_SUMMARY.md
SESSION_SUMMARY_20251115.md
SESSION_SUMMARY_FRONTEND_PLANNING_20251115.md
SUB_AGENTS_COLLABORATION_PLAN.md
UPDATED_ANALYSIS_AND_ROADMAP.md
V10_MAXIMAL_UPGRADE_PLAN.md
V10_READY_TO_EXECUTE.md
```

### 문제점
1. **최상위 디렉토리 오염**: 22개 문서가 루트에 있음
2. **일관성 없음**: 명명 규칙이 제각각
3. **구조 없음**: 분류/정리되지 않음
4. **중복 가능성**: 비슷한 내용의 문서들

---

## 📋 Claude Code 문서 생성 규칙 분석

### CLAUDE.md 규칙 확인

**Session Protocol (CLAUDE.md:358-373)**:
```bash
# During
1. Use TodoWrite for >2 steps
2. Run tests before commit
3. Update docs if API/arch changes  # ← 유일한 문서 관련 언급
```

**발견**:
- ❌ 문서를 어디에 만들어야 하는지 명시 없음
- ❌ 문서 명명 규칙 없음
- ❌ 문서 위치 규칙 없음
- ❌ hooks 디렉토리 없음 (`.claude/hooks/` 없음)

### CLI vs Web 차이

#### Claude Desktop/CLI
- **자동화 가능**: Session hooks, pre-commit hooks
- **파일 시스템 접근**: 제한 없음
- **규칙 강제**: Git hooks로 강제 가능

#### Claude Code Web (현재 환경)
- **자동화 제한**: Session hooks 없음
- **파일 시스템**: 샌드박스 환경
- **규칙 강제**: ❌ 없음 → **사람이 직접 관리 필요**

---

## 🎯 올바른 문서 구조 (v10.0.0 제안)

### 원칙

#### 1. 최상위는 필수 문서만
```
new_rag_ubuntu/
├── README.md              # ✅ 프로젝트 개요
├── CLAUDE.md              # ✅ Claude Code 빠른 참조
├── CHANGELOG.md           # ✅ 변경 이력
├── LICENSE                # ✅ 라이선스
├── CONTRIBUTING.md        # ✅ 기여 가이드
└── .gitignore             # ✅ Git 설정
```

**총 5개 문서만** (현재 22개 → 5개)

#### 2. 나머지는 docs/로 이동

```
docs/
├── guides/                # 📘 How-to 가이드
│   ├── QUICK_START.md
│   ├── DEPLOYMENT.md
│   ├── MIGRATION_V9_TO_V10.md
│   └── TROUBLESHOOTING.md
│
├── reference/             # 📖 레퍼런스
│   ├── API_DOCUMENTATION.md
│   ├── SYMBOLS.md
│   └── openapi-v10.json
│
├── architecture/          # 🏗️ 아키텍처
│   ├── ARCHITECTURE.md
│   ├── SERVICES.md
│   ├── DATABASE_SCHEMA.md
│   └── DESIGN_SYSTEM.md
│
├── planning/              # 📋 계획 문서 (아카이브)
│   ├── v10/
│   │   ├── MAXIMAL_UPGRADE_PLAN.md
│   │   ├── READY_TO_EXECUTE.md
│   │   └── SKILLS_UTILIZATION.md
│   ├── v9/
│   │   ├── COMPLETE_INTEGRATION_MASTER_PLAN.md
│   │   ├── BACKEND_MIGRATION_PLAN.md
│   │   └── FRONTEND_FILE_STRUCTURE_PLAN.md
│   └── sessions/
│       ├── 20251115_frontend_planning.md
│       └── 20251115_analysis.md
│
├── adr/                   # 🔖 Architecture Decision Records
│   ├── 001-backend-unification.md
│   ├── 002-package-extraction.md
│   └── 003-pure-black-design.md
│
└── design/                # 🎨 디자인 시스템
    ├── DESIGN_SYSTEM.md
    ├── PURE_BLACK_THEME.md
    └── COMPONENT_LIBRARY.md
```

---

## 🔧 문서 생성 규칙 (v10.0.0)

### Rule 1: 위치 규칙

| 문서 유형 | 위치 | 예시 |
|----------|------|------|
| 프로젝트 필수 | `/` (root) | README.md, LICENSE |
| Quick Reference | `/` (root) | CLAUDE.md |
| How-to 가이드 | `docs/guides/` | DEPLOYMENT.md |
| API/기술 레퍼런스 | `docs/reference/` | API_DOCUMENTATION.md |
| 아키텍처 | `docs/architecture/` | ARCHITECTURE.md |
| 계획/세션 | `docs/planning/` | V10_PLAN.md |
| ADR | `docs/adr/` | 001-decision.md |
| 디자인 | `docs/design/` | DESIGN_SYSTEM.md |

### Rule 2: 명명 규칙

```bash
# ✅ GOOD
docs/guides/deployment.md
docs/reference/api-v1.md
docs/adr/001-backend-unification.md
docs/planning/v10/maximal-upgrade-plan.md

# ❌ BAD (현재 상태)
BACKEND_MIGRATION_PLAN.md  # 최상위에 있음
SESSION_SUMMARY_20251115.md  # 세션 문서가 최상위
READY_TO_EXECUTE_SUMMARY.md  # 임시 문서가 최상위
```

### Rule 3: 생성 규칙

#### CLI에서 작업 시
```bash
# ✅ 올바른 방법
# 1. 문서 유형 결정
# 2. 적절한 디렉토리에 생성
echo "## Deployment Guide" > docs/guides/deployment.md

# ❌ 잘못된 방법
echo "## Deployment" > DEPLOYMENT.md  # 최상위에 생성
```

#### Web에서 작업 시
```markdown
**주의**: Web 환경에서는 자동 규칙 강제 불가능

**해결책**:
1. 파일 생성 전에 위치 먼저 결정
2. CLAUDE.md 규칙 참조
3. 기존 docs/ 구조 참조
4. 세션 종료 시 정리
```

### Rule 4: 정리 규칙

#### 세션 종료 시
```bash
# 1. 최상위 확인
ls -1 *.md | wc -l  # 5개 이하여야 함

# 2. 초과 시 이동
mv SESSION_*.md docs/planning/sessions/
mv *_PLAN.md docs/planning/v10/
mv BACKEND_*.md docs/planning/v9/

# 3. 중복 체크
find docs/ -name "*.md" -type f | sort | uniq -d

# 4. 커밋
git add docs/
git commit -m "docs: Organize documentation structure"
```

---

## 🔄 v10.0.0 문서 정리 계획

### Phase 1: 분류
```bash
# 필수 (최상위 유지)
README.md
CLAUDE.md
CHANGELOG.md (v10에서 생성)
LICENSE
CONTRIBUTING.md

# 가이드 → docs/guides/
DEPLOYMENT.md
QUICK_START_UPDATED.md

# 계획 → docs/planning/v9/
BACKEND_MIGRATION_PLAN.md
COMPLETE_INTEGRATION_MASTER_PLAN.md
FRONTEND_FILE_STRUCTURE_PLAN.md
FRONTEND_INTEGRATION_SUMMARY.md
INTEGRATION_PLAN_V10.md
MIGRATION_CHECKLIST.md
SUB_AGENTS_COLLABORATION_PLAN.md

# 계획 → docs/planning/v10/
V10_MAXIMAL_UPGRADE_PLAN.md
V10_READY_TO_EXECUTE.md

# 세션 → docs/planning/sessions/
SESSION_SUMMARY_20251115.md
SESSION_SUMMARY_FRONTEND_PLANNING_20251115.md
READY_TO_EXECUTE_SUMMARY.md
UPDATED_ANALYSIS_AND_ROADMAP.md

# 체크리스트 → docs/planning/checklists/
PHASE1_DEPLOYMENT_CHECKLIST.md
MIGRATION_CHECKLIST.md

# 아키텍처 → docs/architecture/
DEVELOPMENT_ENVIRONMENT_EXECUTION_PLAN.md

# 진단 → docs/planning/diagnostics/
FINAL_DIAGNOSIS.md

# 이력 (최상위 유지)
PROGRESS.md
```

### Phase 2: 이동 스크립트
```bash
# scripts/v10/organize_docs.sh

#!/bin/bash
mkdir -p docs/{guides,planning/{v9,v10,sessions,checklists,diagnostics},architecture}

# 가이드
mv DEPLOYMENT.md docs/guides/ 2>/dev/null
mv QUICK_START_UPDATED.md docs/guides/quick-start.md 2>/dev/null

# v9 계획
mv BACKEND_MIGRATION_PLAN.md docs/planning/v9/ 2>/dev/null
mv COMPLETE_INTEGRATION_MASTER_PLAN.md docs/planning/v9/ 2>/dev/null
mv FRONTEND_FILE_STRUCTURE_PLAN.md docs/planning/v9/ 2>/dev/null
mv FRONTEND_INTEGRATION_SUMMARY.md docs/planning/v9/ 2>/dev/null
mv SUB_AGENTS_COLLABORATION_PLAN.md docs/planning/v9/ 2>/dev/null

# v10 계획
mv V10_MAXIMAL_UPGRADE_PLAN.md docs/planning/v10/ 2>/dev/null
mv V10_READY_TO_EXECUTE.md docs/planning/v10/ 2>/dev/null
mv INTEGRATION_PLAN_V10.md docs/planning/v10/ 2>/dev/null

# 세션
mv SESSION_*.md docs/planning/sessions/ 2>/dev/null
mv READY_TO_EXECUTE_SUMMARY.md docs/planning/sessions/ 2>/dev/null
mv UPDATED_ANALYSIS_AND_ROADMAP.md docs/planning/sessions/ 2>/dev/null

# 체크리스트
mv PHASE1_DEPLOYMENT_CHECKLIST.md docs/planning/checklists/ 2>/dev/null
mv MIGRATION_CHECKLIST.md docs/planning/checklists/ 2>/dev/null

# 진단
mv FINAL_DIAGNOSIS.md docs/planning/diagnostics/ 2>/dev/null

echo "✅ Documentation organized"
ls -1 *.md  # 5개만 남아야 함
```

### Phase 3: 검증
```bash
# 최상위 문서 5개 확인
ls -1 *.md | wc -l  # 5

# 최상위 문서 목록
ls -1 *.md
# README.md
# CLAUDE.md
# CHANGELOG.md
# LICENSE
# CONTRIBUTING.md
# PROGRESS.md (선택적)
```

---

## 📊 Before & After

### Before (현재)
```
/ (root)
├── README.md
├── CLAUDE.md
├── ... 20 more .md files ⚠️ (너무 많음)
└── docs/
    ├── guides/
    └── reference/
```

### After (v10.0.0)
```
/ (root)
├── README.md                    # 필수
├── CLAUDE.md                    # 필수
├── CHANGELOG.md                 # 필수
├── LICENSE                      # 필수
├── CONTRIBUTING.md              # 필수
└── docs/                        # 모든 문서
    ├── guides/                  # How-to
    ├── reference/               # API 문서
    ├── architecture/            # 아키텍처
    ├── planning/                # 계획 (아카이브)
    │   ├── v9/                 # v9 계획들
    │   ├── v10/                # v10 계획들
    │   ├── sessions/           # 세션 기록
    │   └── checklists/         # 체크리스트
    ├── adr/                     # ADR
    └── design/                  # 디자인
```

**결과**: 22개 → 5개 (최상위), 나머지는 `docs/` 하위로 정리

---

## ✅ 권장사항

### 1. 즉시 적용 (지금)
```bash
# 문서 정리 스크립트 실행 (v10 실행 전에)
# 선택 사항: 수동으로 하나씩 이동해도 됨
```

### 2. v10 실행 시 자동 포함
```bash
# phase2_backend_trimming.sh에 포함
# 또는 phase4_final_trimming.sh에 포함
```

### 3. 앞으로 규칙
```markdown
**문서 생성 시 체크리스트**:
- [ ] 문서 유형 결정 (guide? reference? planning?)
- [ ] 적절한 디렉토리 확인 (docs/guides/, docs/planning/v10/, etc.)
- [ ] 명명 규칙 준수 (kebab-case.md)
- [ ] 최상위는 필수 문서만 (5개)
- [ ] 세션 종료 시 정리
```

---

## 🎯 결론

### 문제 원인
1. **Web 환경**: 자동 규칙 강제 불가능
2. **hooks 없음**: `.claude/hooks/` 디렉토리 없음
3. **명시적 규칙 없음**: CLAUDE.md에 문서 위치 규칙 없음

### 해결책
1. **수동 정리**: `organize_docs.sh` 스크립트 실행
2. **v10에 포함**: Phase 2 또는 4에서 자동 정리
3. **규칙 문서화**: 이 문서를 `docs/guides/documentation-rules.md`로 이동
4. **CLAUDE.md 업데이트**: 문서 생성 규칙 추가

### 다음 단계
```bash
# Option 1: 지금 정리
./scripts/v10/organize_docs.sh

# Option 2: v10 실행 시 자동 정리
./scripts/v10/run_v10_upgrade.sh  # phase2에 포함됨

# Option 3: 수동 정리
# 하나씩 mv 명령어로 이동
```

---

**Created**: 2025-11-16
**Status**: Analysis complete, awaiting user decision
**Next**: 문서 정리 스크립트 실행 또는 v10에 포함
