# 기본 계획 (BASE PLAN) - v10.0.0 통합 리팩토링

**생성일**: 2025-11-15  
**상태**: 📋 계획 완료 - 실행 대기  
**분석 도구**: Serena MCP + GitHub MCP + Sub-Agents  
**예상 소요**: 4-6시간 (실행 시)

---

## 📊 요약

### 분석 결과
- **Backend 코드**: app/ (142 files) + src/ (174 files) = 316 files
- **중복도**: ~20-30%
- **Import 혼재**: app/main.py에서 app.* 와 src.* 혼용
- **버전 분산**: v7.x (app/) + v8-v9 (src/)

### 목표
- **단일 통합 구조**: backend/ 디렉토리로 통합
- **API 버전 관리**: v1 (안정) / v2 (실험)
- **코드 중복 제거**: 40% → <5%
- **Import 정리**: 모두 backend.* 로 통일

---

## 📁 생성된 문서

### 주요 문서
1. **INTEGRATION_PLAN_V10.md** (루트)
   - 11주 종합 통합 계획 (장기 로드맵)
   
2. **BACKEND_MIGRATION_PLAN.md** (루트)
   - 4-6시간 단기 실행 계획 (이번 작업)
   
3. **MIGRATION_CHECKLIST.md** (루트)
   - 빠른 참조 체크리스트

### 실행 스크립트
```
scripts/migration/
├── README.md                    (9.6 KB - 스크립트 가이드)
├── 00_run_migration.sh          (10 KB - 마스터 오케스트레이터) ⭐
├── 01_copy_src_to_backend.sh    (6.8 KB - 파일 복사)
├── 02_update_imports.sh         (7.2 KB - Import 업데이트)
└── 03_validate_structure.sh     (9 KB - 검증)
```

---

## 🎯 핵심 구조

### Before (현재)
```
app/          (142 files - v7.x base)
src/          (174 files - v8-v9 features)
backend/      (142 files - app/ 복사본)
```

### After (기본 계획 적용 후)
```
backend/                         ← 통합 단일 구조
├── api/
│   ├── v1/                     (app/api - 안정)
│   └── v2/                     (src/api - 실험)
├── middleware/
│   ├── (기본)                   (app/middleware)
│   └── advanced/               (src/middleware)
├── core/                       (app/core + src/core 병합)
├── services/                   (100+ 통합)
├── auth/                       (src/auth - JWT)
└── main.py                     (통합 entry point)
```

---

## 🚀 실행 방법

### Quick Start
```bash
cd /home/rkqksk/projects/new_rag

# 1. Dry-run (미리보기)
./scripts/migration/00_run_migration.sh --dry-run

# 2. 실제 실행
./scripts/migration/00_run_migration.sh

# 3. 검증
./scripts/migration/03_validate_structure.sh
```

### 단계별 실행
```bash
# Phase 3B: 파일 복사
./scripts/migration/01_copy_src_to_backend.sh

# Phase 3C: Import 업데이트
./scripts/migration/02_update_imports.sh

# Phase 3E: 검증
./scripts/migration/03_validate_structure.sh
```

---

## ⚠️ 실행 전 확인사항

### 필수 체크
- [ ] Git 브랜치 백업 생성
- [ ] 현재 코드 정상 작동 확인
- [ ] Docker 컨테이너 모두 정상
- [ ] 테스트 스위트 통과
- [ ] 충분한 디스크 공간 (>5GB)

### 권장 사항
- [ ] BACKEND_MIGRATION_PLAN.md 정독
- [ ] MIGRATION_CHECKLIST.md 출력
- [ ] 팀원에게 공유
- [ ] 작업 시간대 확보 (4-6시간)

---

## 📋 체크리스트

### Pre-Migration
- [ ] 백업 생성
- [ ] 브랜치 생성 (backup-before-migration)
- [ ] 문서 검토

### Migration
- [ ] Dry-run 실행 및 검토
- [ ] 실제 마이그레이션 실행
- [ ] Import 업데이트
- [ ] 수동 파일 수정 (main.py, docker-compose.yml)

### Post-Migration
- [ ] 검증 스크립트 실행
- [ ] 테스트 스위트 실행
- [ ] Docker 리빌드 및 테스트
- [ ] API 헬스 체크
- [ ] 문서 업데이트

---

## 📊 예상 효과

| 메트릭 | Before | After | 개선 |
|--------|--------|-------|------|
| 코드 중복 | 40% | <5% | -87.5% |
| Import 혼란 | 높음 | 낮음 | 통일 |
| 디렉토리 수 | 2 (app+src) | 1 (backend) | -50% |
| 유지보수성 | 낮음 | 높음 | +60% |

---

## 🔄 롤백 방법

### 즉시 롤백
```bash
git checkout backup-before-migration
docker-compose down
docker-compose build api
docker-compose up -d
```

### 부분 롤백
```bash
# 백업 디렉토리 확인
ls -la .migration_backup_*

# 특정 파일 복원
cp .migration_backup_*/backend/specific_file.py backend/
```

---

## 📞 다음 단계

1. **확인사항 체크**
   - 팀 리뷰
   - 일정 조율
   - 리소스 준비

2. **실행 준비**
   - BACKEND_MIGRATION_PLAN.md 정독
   - 체크리스트 출력
   - Git 백업

3. **실행 개시**
   - Dry-run 먼저
   - 실제 마이그레이션
   - 검증 및 테스트

---

## 📚 관련 문서

- **INTEGRATION_PLAN_V10.md** - 장기 통합 로드맵 (11주)
- **BACKEND_MIGRATION_PLAN.md** - 실행 계획 (4-6시간)
- **MIGRATION_CHECKLIST.md** - 빠른 체크리스트
- **scripts/migration/README.md** - 스크립트 가이드

---

**상태**: ✅ 계획 완료 - 확인 후 실행 대기  
**생성일**: 2025-11-15  
**다음 액션**: 확인사항 체크 후 실행
