# RAG Enterprise 프로젝트 구조 관리 규칙

## 📁 디렉토리 구조 원칙

### 1. 핵심 원칙
- **실행 관련 파일만 루트에 위치**
- **개발/테스트/아카이브는 별도 디렉토리로 격리**
- **데이터와 로그는 자동 생성되는 위치로만**

---

## 🗂️ 표준 디렉토리 구조

```
rag-enterprise/
├── 📦 CORE (실행 필수)
│   ├── app/                    # 메인 애플리케이션 코드
│   │   ├── api/                # API 엔드포인트
│   │   ├── core/               # 핵심 로직
│   │   ├── services/           # 비즈니스 로직
│   │   └── utils/              # 유틸리티
│   ├── mcp_servers/            # MCP 서버 구현
│   ├── agents/                 # AI 에이전트
│   └── config/                 # 설정 파일
│
├── 🔧 DEVELOPMENT (개발 관련)
│   ├── dev/                    # 개발 전용 파일
│   │   ├── experiments/        # 실험적 코드
│   │   ├── prototypes/         # 프로토타입
│   │   ├── notebooks/          # Jupyter notebooks
│   │   └── sandbox/            # 테스트용 샌드박스
│   ├── tests/                  # 테스트 코드
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   └── scripts/                # 개발/배포 스크립트
│
├── 📚 DOCUMENTATION (문서)
│   ├── docs/                   # 프로젝트 문서
│   │   ├── architecture/       # 아키텍처 문서
│   │   ├── api/                # API 문서
│   │   ├── guides/             # 가이드
│   │   └── archive/            # 구버전 문서
│   └── claudedocs/             # Claude 생성 문서
│
├── 🗄️ ARCHIVES (보관)
│   ├── archives/               # 아카이브된 파일
│   │   ├── logs_YYYYMMDD/      # 과거 로그
│   │   ├── backups/            # 백업 파일
│   │   └── deprecated/         # 더 이상 사용 안 함
│   └── temp/                   # 임시 파일 (자동 정리)
│
├── 🎨 ASSETS (정적 자원)
│   ├── images/                 # 이미지 파일
│   │   └── containers/         # Docker 이미지 관련
│   ├── local_models/           # 로컬 ML 모델
│   └── plugins/                # 플러그인
│
├── 💾 DATA (데이터 - Git 제외)
│   ├── data/                   # Docker 볼륨 데이터
│   │   ├── qdrant/
│   │   ├── postgres/
│   │   ├── redis/
│   │   ├── n8n/
│   │   └── ollama/
│   ├── documents/              # 업로드된 문서
│   └── logs/                   # 애플리케이션 로그
│
└── 🔐 CONFIG (설정)
    ├── .env                    # 환경변수 (Git 제외)
    ├── .env.example            # 환경변수 템플릿
    ├── .gitignore
    ├── docker-compose.yml
    ├── requirements.txt
    └── package.json
```

---

## 📋 디렉토리별 생성 규칙

### ✅ 자동 생성 허용 (실행 시)
```yaml
허용:
  - data/*                     # Docker 볼륨
  - logs/*.log                 # 애플리케이션 로그
  - documents/*                # 업로드된 문서
  - temp/*                     # 임시 파일
```

### ⚠️ 수동 생성 필요 (개발자가 직접)
```yaml
필요시_생성:
  - dev/experiments/           # 실험적 코드
  - dev/prototypes/            # 프로토타입
  - archives/deprecated/       # 사용 중단 코드
  - docs/guides/               # 새로운 가이드
```

### ❌ 생성 금지 (루트에 생성 안 됨)
```yaml
금지:
  - rag-enterprise/test_*.py   # 루트 테스트 파일
  - rag-enterprise/temp_*.py   # 루트 임시 파일
  - rag-enterprise/backup_*    # 루트 백업
  - rag-enterprise/old_*       # 루트 구버전 파일
```

---

## 🎯 파일 생성 플로우차트

```
새 파일 생성 요청
    ↓
[1] 파일 유형 판단
    ↓
    ├─ 테스트? → tests/
    ├─ 실험? → dev/experiments/
    ├─ 문서? → docs/ or claudedocs/
    ├─ 아카이브? → archives/
    ├─ 임시? → temp/
    └─ 핵심 코드? → app/ or mcp_servers/
```

---

## 🧹 자동 정리 규칙

### Cron 작업 (권장)
```bash
# 매일 자정 임시 파일 정리
0 0 * * * find /path/to/rag-enterprise/temp -type f -mtime +7 -delete

# 매주 일요일 오래된 로그 아카이브
0 0 * * 0 /path/to/scripts/archive_old_logs.sh

# 매월 1일 아카이브 압축
0 0 1 * * /path/to/scripts/compress_archives.sh
```

### 정리 스크립트
```bash
#!/bin/bash
# scripts/cleanup.sh

# 30일 지난 임시 파일 삭제
find temp/ -type f -mtime +30 -delete

# 90일 지난 로그 아카이브
find logs/ -name "*.log" -mtime +90 -exec mv {} archives/logs_$(date +%Y%m%d)/ \;

# archives 내 1년 지난 파일 압축
find archives/ -type f -mtime +365 -exec gzip {} \;
```

---

## 📝 .gitignore 업데이트

### 추가해야 할 항목
```gitignore
# Development
/dev/experiments/
/dev/prototypes/
/dev/sandbox/

# Claude Code Generated
/claudedocs/
/claude-code/

# Temporary
/temp/
*.tmp
*.bak

# Archives (except directory structure)
/archives/*
!/archives/.gitkeep
```

---

## 🔍 디렉토리 검증 체크리스트

### 매 커밋 전 확인
- [ ] 루트에 테스트 파일 없음 (`test_*.py`)
- [ ] 루트에 임시 파일 없음 (`temp_*`, `*.tmp`)
- [ ] 실행 관련 파일만 `app/`, `mcp_servers/`에 위치
- [ ] 실험적 코드는 `dev/experiments/`에 위치
- [ ] 문서는 `docs/` 또는 `claudedocs/`에 위치
- [ ] 아카이브는 `archives/`에 위치
- [ ] `.env` 파일 커밋 안 됨 (`.env.example`만 커밋)

### 주기적 정리 (월 1회)
- [ ] `temp/` 디렉토리 비우기
- [ ] `logs/` 오래된 로그 아카이브
- [ ] `archives/` 오래된 파일 압축
- [ ] `dev/experiments/` 불필요 파일 삭제
- [ ] `data/` 디렉토리 용량 확인

---

## 🚀 실행 가이드

### 새 디렉토리 구조 적용
```bash
# 1. 새 디렉토리 생성
mkdir -p dev/{experiments,prototypes,notebooks,sandbox}
mkdir -p docs/{architecture,api,guides,archive}
mkdir -p archives/{backups,deprecated}
mkdir -p tests/{unit,integration,e2e}
mkdir -p claudedocs
mkdir -p temp

# 2. .gitkeep 파일 추가 (빈 디렉토리 유지)
touch dev/experiments/.gitkeep
touch archives/backups/.gitkeep
touch temp/.gitkeep

# 3. 기존 파일 이동
mv test_*.py tests/unit/ 2>/dev/null || true
mv *_backup.* archives/backups/ 2>/dev/null || true
mv *.tmp temp/ 2>/dev/null || true

# 4. 정리 스크립트 실행
bash scripts/cleanup.sh
```

### Claude Code에 규칙 적용
```bash
# CLAUDE.md에 프로젝트 구조 규칙 추가
cat PROJECT_STRUCTURE_RULES.md >> CLAUDE.md
```

---

## 📊 모니터링

### 디렉토리 크기 확인
```bash
du -sh * | sort -h
```

### 파일 개수 확인
```bash
find . -type f | wc -l
```

### 오래된 파일 찾기
```bash
find . -type f -mtime +90
```

---

## 🎓 개발자 가이드

### 새 기능 개발 시
1. `dev/experiments/` 에서 프로토타입 작성
2. 검증 완료 후 `app/` 또는 적절한 위치로 이동
3. 테스트 코드는 `tests/`에 작성
4. 문서는 `docs/guides/`에 추가

### 버그 수정 시
1. 재현 테스트를 `tests/integration/`에 작성
2. 수정 후 테스트 통과 확인
3. 관련 문서 업데이트

### 실험적 코드 작성 시
1. `dev/experiments/YYYYMMDD_feature_name/` 형식으로 생성
2. 실험 완료 후 성공/실패 여부 README 작성
3. 성공시 메인 코드로 이동, 실패시 `archives/deprecated/`로 이동

---

**Last Updated**: 2025-10-17
**Version**: 1.0
**Maintainer**: RAG Enterprise Team
