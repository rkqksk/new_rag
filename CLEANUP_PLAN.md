# 프로젝트 파일 정리 계획

## 현재 상태 분석

### 디렉토리 구조
```
rag-enterprise/
├── dev/                          # 개발 실험 파일들
│   ├── check_*.py                # 페이지네이션 조사 스크립트
│   ├── test_*.py                 # 테스트 스크립트
│   └── ...
├── data/
│   ├── crawled_products/         # 현재 크롤링 결과 (비구조화)
│   ├── test_jar_category/        # 테스트 데이터
│   ├── test_cap_pump_category/   # 테스트 데이터
│   └── ...
├── scripts/                      # 유틸리티 스크립트들
├── *.log                         # 크롤링 로그 파일들
├── *.py (루트)                   # 실행 스크립트들
└── ...
```

---

## 정리 전략 (4단계)

### 🟢 Phase 1: 안전한 정리 (즉시 실행 가능)
**목표**: 명확히 불필요한 파일 제거

#### 1-1. 테스트 데이터 디렉토리
- [x] `data/test_jar_category/` → **삭제**
  - 이유: 이미 `data/crawled_products/`에 복사됨
  - 백업: 불필요 (프로덕션 데이터로 대체됨)

- [x] `data/test_cap_pump_category/` → **삭제**
  - 이유: 이미 `data/crawled_products/`에 복사됨
  - 백업: 불필요

- [x] `data/test_bottle_category/` → **삭제** (Bottle 크롤링 완료 후)
  - 이유: 이미 `data/crawled_products/`에 복사될 예정
  - 백업: 불필요

#### 1-2. Dev 디렉토리 실험 스크립트
- [x] `dev/check_cap_pump_pagination.py` → **삭제**
  - 이유: 조사 목적 완료, chungjin_crawler.py에 통합됨
  - 백업: Git 히스토리에 남음

- [x] `dev/test_paging_next.py` → **삭제**
  - 이유: 조사 목적 완료

- [x] `dev/` 전체 → **삭제** (확인 후)
  - 조건: 실험 완료 및 프로덕션 코드 통합 완료

#### 1-3. 임시 로그 파일
- [x] `crawl_all_categories.log` → **삭제**
  - 이유: 중단된 크롤링 로그

- [x] `crawl_bottle.log.old` (있다면) → **삭제**

#### 1-4. 루트 디렉토리 테스트 스크립트
- [x] `test_jar_category.py` → `scripts/tests/` 이동 또는 삭제
  - 판단 기준: 향후 재사용 가능성
  - 권장: 삭제 (chungjin_crawler.py로 대체)

- [x] `test_cap_pump_category.py` → 삭제
- [x] `test_bottle_category.py` → 삭제

### 🟡 Phase 2: 아카이브 후 정리 (검토 필요)

#### 2-1. 크롤링 로그 압축
- [ ] `crawl_bottle.log` → `archives/logs/crawl_bottle_20251018.log.gz`
  - 조건: Bottle 크롤링 완료 및 검증 완료 후
  - 보관 기간: 6개월

#### 2-2. 요약 JSON 파일 아카이브
- [ ] `data/crawled_products/category_*.json` → `archives/summaries/`
  - 이유: CSV 리포트로 대체됨
  - 보관: 원본 데이터로 보관

#### 2-3. 구버전 스크립트 아카이브
- [ ] 만약 `chungjin_crawler_v1.py` 같은 파일이 있다면 → `archives/code/`

### 🔵 Phase 3: 데이터 재구조화 (Bottle 완료 후)

#### 3-1. 기존 데이터 재구성
```bash
# 실행 스크립트
python scripts/reorganize_crawled_data.py

# 결과
data/crawled_products/           # 기존 (비구조화)
↓
data/crawled_products_organized/  # 신규 (구조화)
├── Bottle/
│   ├── products/
│   ├── images/
│   ├── print_area/
│   └── Bottle_report.csv
├── Jar/
│   └── ...
├── Cap_Pump/
│   └── ...
└── master_report.csv
```

#### 3-2. 검증 후 교체
```bash
# 1. 검증
ls -R data/crawled_products_organized/
cat data/crawled_products_organized/master_report.csv

# 2. 백업
mv data/crawled_products data/crawled_products_backup

# 3. 교체
mv data/crawled_products_organized data/crawled_products

# 4. 확인 후 백업 삭제 (1주일 후)
rm -rf data/crawled_products_backup
```

### 🟣 Phase 4: 최종 프로덕션 정리

#### 4-1. 유지할 파일
**프로덕션 크롤러**:
- `chungjin_crawler.py` ✅
- `crawl_bottle_only.py` ✅
- `crawl_all_categories.py` ✅

**유틸리티**:
- `scripts/generate_crawl_report.py` ✅
- `scripts/reorganize_crawled_data.py` ✅

**문서**:
- `docs/CRAWLING_FRAMEWORK.md` ✅
- `CRAWL_DATA_STRUCTURE.md` ✅
- `CLEANUP_PLAN.md` (이 파일) ✅

**데이터**:
- `data/crawled_products/` ✅ (재구조화 완료 후)
- 최신 `crawl_bottle.log` 1개만 ✅

#### 4-2. .gitignore 업데이트
```gitignore
# 크롤링 데이터
data/crawled_products/
data/test_*/
data/chungjin_final_crawl/

# 로그
*.log
!crawl_latest.log  # 최신 1개만 유지

# 백업
*_backup/
*_old/
*.bak

# 개발 임시
dev/
temp/
tmp/

# 아카이브 (로컬 보관, Git 제외)
archives/
```

---

## 실행 체크리스트

### Before Cleanup (사전 확인)
- [x] Bottle 크롤링 완료 확인
- [x] 크롤링 결과 CSV 리포트 생성 완료
- [x] 데이터 재구조화 스크립트 테스트 완료
- [ ] 중요 파일 백업 (Git commit 완료)

### During Cleanup (정리 실행)
**Phase 1: 안전한 삭제**
```bash
# 1. 테스트 데이터 삭제
rm -rf data/test_jar_category/
rm -rf data/test_cap_pump_category/
rm -rf data/test_bottle_category/

# 2. 실험 스크립트 삭제
rm -rf dev/

# 3. 루트 테스트 스크립트 삭제
rm test_jar_category.py test_cap_pump_category.py test_bottle_category.py

# 4. 임시 로그 삭제
rm crawl_all_categories.log
```

**Phase 2: 아카이브**
```bash
# 아카이브 디렉토리 생성
mkdir -p archives/{logs,summaries,code}

# 로그 압축
gzip -c crawl_bottle.log > archives/logs/crawl_bottle_20251018.log.gz

# 요약 JSON 아카이브
mv data/crawled_products/category_*.json archives/summaries/
```

**Phase 3: 데이터 재구조화**
```bash
# 실행
python scripts/reorganize_crawled_data.py

# 검증
ls -R data/crawled_products_organized/
python scripts/generate_crawl_report.py

# 교체
mv data/crawled_products data/crawled_products_backup
mv data/crawled_products_organized data/crawled_products
```

**Phase 4: 최종 정리**
```bash
# .gitignore 업데이트
git add .gitignore
git commit -m "chore: update .gitignore for crawling data"

# Git 상태 확인
git status

# 정리 완료 커밋
git add .
git commit -m "chore: cleanup project structure after crawling completion"
```

### After Cleanup (사후 검증)
- [ ] 프로덕션 스크립트 실행 테스트
- [ ] CSV 리포트 확인
- [ ] Git 저장소 크기 확인
- [ ] README 업데이트

---

## 예상 공간 절약

| 항목 | 예상 크기 | 정리 후 |
|------|----------|---------|
| dev/ | ~100KB | 0KB |
| data/test_* | ~500MB | 0KB |
| *.log (중복) | ~50MB | ~5MB |
| data/crawled_products (비구조화) | ~2GB | ~2GB (구조화) |
| **총계** | ~2.65GB | ~2.01GB |

**예상 절약**: ~640MB (24%)

---

## 위험 완화 전략

### Backup Plan
1. **Git Commit**: 정리 전 현재 상태 커밋
   ```bash
   git add .
   git commit -m "checkpoint: before cleanup"
   git tag cleanup-checkpoint
   ```

2. **압축 백업**: 전체 프로젝트 tar.gz 생성
   ```bash
   tar -czf ../rag-enterprise-backup-20251018.tar.gz .
   ```

3. **단계별 실행**: 한 번에 모두 삭제하지 말고 Phase별로 실행
4. **검증 후 진행**: 각 Phase 완료 후 테스트 실행

### Rollback Plan
만약 문제 발생 시:
```bash
# Git으로 복구
git reset --hard cleanup-checkpoint

# 또는 백업에서 복구
cd ..
tar -xzf rag-enterprise-backup-20251018.tar.gz
```

---

## 정리 후 프로젝트 구조 (최종)

```
rag-enterprise/
├── app/                       # FastAPI 애플리케이션
├── mcp_servers/               # MCP 서버 구현
├── config/                    # 설정 파일
├── scripts/                   # 유틸리티 스크립트
│   ├── generate_crawl_report.py
│   ├── reorganize_crawled_data.py
│   └── cleanup.sh
├── docs/                      # 문서
│   └── CRAWLING_FRAMEWORK.md
├── data/                      # 데이터 (Git 제외)
│   └── crawled_products/      # 구조화된 크롤링 결과
│       ├── Bottle/
│       ├── Jar/
│       ├── Cap_Pump/
│       └── master_report.csv
├── archives/                  # 아카이브 (Git 제외)
│   ├── logs/
│   ├── summaries/
│   └── code/
├── chungjin_crawler.py        # 프로덕션 크롤러
├── crawl_bottle_only.py       # 실행 스크립트
├── crawl_all_categories.py    # 실행 스크립트
├── CRAWL_DATA_STRUCTURE.md
├── CLEANUP_PLAN.md
└── README.md
```

**특징**:
- ✅ 깔끔한 루트 디렉토리
- ✅ 명확한 역할 분리
- ✅ Git 저장소 경량화
- ✅ 프로덕션 실행 가능

---

## 실행 타이밍

### 즉시 실행 가능 (Phase 1)
- ✅ 테스트 데이터 삭제
- ✅ dev/ 디렉토리 삭제
- ✅ 임시 로그 삭제

### Bottle 완료 후 (Phase 2-4)
- ⏳ Bottle 크롤링 완료 대기 중
- ⏳ CSV 리포트 생성
- ⏳ 데이터 재구조화
- ⏳ 최종 정리

**예상 실행 시간**: Bottle 완료 후 +30분

---
*Version: 1.0 | Created: 2025-10-18 | Approved: Pending*
