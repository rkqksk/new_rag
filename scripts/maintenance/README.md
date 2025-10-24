# 문서 자동 정리 시스템

프로젝트 루트의 문서들을 자동으로 분류하고 아카이빙하는 시스템입니다.

## 📋 개요

- **자동 분류**: 파일명 패턴 기반으로 적절한 디렉토리로 이동
- **날짜 기반 아카이빙**: 30일 이상 수정되지 않은 문서 자동 보관
- **중요 문서 보호**: CLAUDE.md, PROGRESS.md 등 핵심 문서는 루트 유지
- **Git 통합**: pre-commit hook으로 자동 정리

## 🗂️ 디렉토리 구조

```
/Users/oypnus/Project/rag-enterprise/
├── CLAUDE.md                    # 루트 유지 (프로젝트 컨텍스트)
├── PROGRESS.md                  # 루트 유지 (진행상황)
├── README.md                    # 루트 유지
├── QUICK_START.md              # 루트 유지
│
├── docs/
│   ├── guides/                 # CLAUDE_*.md, *_GUIDE.md
│   ├── analysis/              # DISCOUNT_*.md, *_ANALYSIS.md, *_REPORT.md
│   ├── development/           # SKILLS_*.md, 개발 관련 문서
│   └── archived/
│       ├── 2025-10/           # 2025년 10월 문서
│       ├── 2025-09/           # 2025년 9월 문서
│       └── older/             # 그 이전 문서
│
├── tests/                      # test_*.py, *_test.py
├── config/
│   ├── mcp/                   # .mcp.*.json
│   ├── docker/                # docker-compose.*.yml
│   └── requirements/          # requirements-*.txt
│
└── scripts/
    ├── maintenance/
    │   ├── auto_organize_docs.py      # 메인 스크립트
    │   ├── install.sh                 # 설치 스크립트
    │   ├── weekly_organize.sh         # 주간 정리
    │   └── git-pre-commit-hook.sh     # Git hook
    └── *.sh                            # 기타 스크립트
```

## 🚀 설치

```bash
# 1회 설치
./scripts/maintenance/install.sh
```

설치 시 진행되는 작업:
1. 실행 권한 설정
2. 필요한 디렉토리 구조 생성
3. Git pre-commit hook 설치 (선택)
4. cron 설정 안내 (선택)

## 📖 사용법

### 1. 수동 실행 (미리보기)

```bash
# dry-run: 실제 이동 없이 결과만 확인
python3 scripts/maintenance/auto_organize_docs.py
```

### 2. 실제 적용

```bash
# 실제로 파일 이동
python3 scripts/maintenance/auto_organize_docs.py --execute
```

### 3. 주간 정리 (대화형)

```bash
# 주 1회 실행 권장
./scripts/maintenance/weekly_organize.sh
```

### 4. Git hook (자동)

Git hook이 설치되어 있으면, 커밋 시 자동으로:
1. 루트의 새 파일 감지
2. 정리 미리보기 표시
3. 사용자에게 확인 요청
4. 적용 후 커밋

## 🎯 분류 규칙

### 문서 유형별 분류

| 파일 패턴 | 목적지 | 예시 |
|---------|--------|------|
| `CLAUDE_*.md` | docs/guides/ | CLAUDE_SETUP.md |
| `*_GUIDE.md` | docs/guides/ | SETUP_GUIDE.md |
| `DISCOUNT_*.md` | docs/analysis/ | DISCOUNT_ANALYSIS.md |
| `*_ANALYSIS.md` | docs/analysis/ | PRICE_ANALYSIS.md |
| `*_REPORT.md` | docs/analysis/ | INCOMPLETE_DATA_REPORT.md |
| `SKILLS_*.md` | docs/development/ | SKILLS_READY.md |
| `test_*.py` | tests/ | test_api.py |
| `.mcp.*.json` | config/mcp/ | .mcp.minimal.json |
| `docker-compose.*.yml` | config/docker/ | docker-compose.staging.yml |
| `requirements-*.txt` | config/requirements/ | requirements-prod.txt |
| `*.sh` | scripts/ | apply-claude-config.sh |
| `run_*.py` | scripts/ | run_chat_server.py |

### 루트 유지 파일

다음 파일들은 항상 루트에 유지됩니다:
- `CLAUDE.md` - 프로젝트 컨텍스트
- `PROGRESS.md` - 진행 상황
- `README.md` - 프로젝트 개요
- `QUICK_START.md` - 빠른 시작
- `Makefile` - 빌드 스크립트
- `Dockerfile` - 컨테이너 설정
- `.env*` - 환경 변수
- `.gitignore`, `.dockerignore` 등 설정 파일

### 아카이빙 규칙

- **대상**: `.md`, `.txt`, `.py` 파일
- **조건**: 30일 이상 수정되지 않음
- **제외**: 루트 유지 파일
- **위치**: `docs/archived/YYYY-MM/`

## 🔄 주기적 실행

### Cron 설정

매주 일요일 오전 9시에 자동 실행:

```bash
crontab -e

# 다음 줄 추가
0 9 * * 0 cd /Users/oypnus/Project/rag-enterprise && ./scripts/maintenance/weekly_organize.sh
```

### GitHub Actions (선택)

`.github/workflows/organize-docs.yml`:

```yaml
name: 주간 문서 정리

on:
  schedule:
    - cron: '0 0 * * 0'  # 매주 일요일 자정
  workflow_dispatch:  # 수동 실행 가능

jobs:
  organize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: 문서 정리
        run: |
          python3 scripts/maintenance/auto_organize_docs.py --execute
      - name: 커밋
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "chore: 주간 문서 정리" || echo "변경사항 없음"
          git push
```

## 🛠️ 커스터마이징

### 새로운 분류 규칙 추가

`auto_organize_docs.py`의 `self.file_rules`에 패턴 추가:

```python
self.file_rules = [
    # 기존 규칙...
    
    # 새 규칙 추가
    (r'^API_.*\.md$', 'docs/api'),
    (r'^.*_SPEC\.md$', 'docs/specifications'),
]
```

### 아카이빙 기간 변경

```python
# 30일 → 60일로 변경
self.archive_after_days = 60
```

### 루트 유지 파일 추가

```python
self.keep_in_root = {
    'CLAUDE.md',
    'PROGRESS.md',
    # ... 기존 파일들
    
    # 새로 추가
    'IMPORTANT.md',
    'CHANGELOG.md',
}
```

## 📊 실행 예시

```bash
$ python3 scripts/maintenance/auto_organize_docs.py

[DRY RUN] 문서 정리 시작...

루트에서 23개 파일 발견

============================================================
1단계: 파일 분류
============================================================
📁 CLAUDE_CLEANUP_GUIDE.md
   → docs/guides/

📁 DISCOUNT_ANALYSIS_INDEX.md
   → docs/analysis/

📁 test_chat_mvp.py
   → tests/

📁 docker-compose.staging.yml
   → config/docker/

============================================================
2단계: 오래된 문서 아카이빙
============================================================
📦 INCOMPLETE_DATA_REPORT.md
   수정: 2025-09-15 (39일 전)
   → docs/archived/2025-09/

============================================================
총 15개 파일 이동
============================================================

💡 실제 실행하려면: --execute 옵션 사용
```

## ❓ FAQ

**Q: 실수로 중요한 파일이 이동됐어요**
```bash
git checkout HEAD -- <파일명>
```

**Q: 특정 파일을 루트에 계속 두고 싶어요**
`auto_organize_docs.py`의 `self.keep_in_root`에 추가하세요.

**Q: Git hook을 제거하고 싶어요**
```bash
rm .git/hooks/pre-commit
```

**Q: 이미 정리된 파일을 다시 루트로 옮기고 싶어요**
```bash
mv docs/guides/SOME_FILE.md .
```

## 🔐 안전 장치

1. **Dry-run 기본**: `--execute` 없이는 실제 이동 안 함
2. **Git hook 확인**: 커밋 전 사용자에게 확인 요청
3. **중요 파일 보호**: 루트 유지 목록으로 보호
4. **Git 버전 관리**: 언제든 복구 가능

## 📝 라이센스

이 스크립트는 rag-enterprise 프로젝트의 일부입니다.
