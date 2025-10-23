# 🧹 RAG Enterprise - 클린업 계획

**날짜**: 2025-01-11  
**목적**: 프로젝트 폴더 정리 및 최적화

---

## 삭제 대상

### 1. 시스템 파일
- [ ] .DS_Store (macOS 메타데이터)

### 2. 임시/캐시 파일
- [ ] .pytest_cache/ (pytest 캐시)
- [ ] htmlcov/ (커버리지 HTML 리포트)
- [ ] __pycache__/ 디렉토리들
- [ ] *.pyc 파일들

### 3. 로그 파일
- [ ] benchmark_run.log
- [ ] embedding_pipeline.log
- [ ] fastapi_dev.log
- [ ] multi_student_benchmark.log
- [ ] multi_student_benchmark_run.log

### 4. 백업/중복 파일
- [ ] CLAUDE.md.backup

### 5. 임시 리포트 파일
- [ ] embedding_report.json
- [ ] embedding_report_lite.json
- [ ] qa_test_result.json

---

## 보관 대상

### 문서
- ✅ CLAUDE.md (시스템 아키텍처)
- ✅ progress.md (진행상황)
- ✅ decisions.md (결정사항)
- ✅ bugs.md (버그 추적)
- ✅ SYSTEM_REVIEW.md (시스템 리뷰)

### 주요 리포트
- ✅ CI_CD_IMPLEMENTATION_SUMMARY.md
- ✅ EMBEDDING_COMPLETE_REPORT.md
- ✅ MATERIAL_EXTRACTION_REPORT.md
- ✅ PHASE4_5_COMPLETION_REPORT.md (docs/ 이동 필요)

### 설정 파일
- ✅ .mcp.json
- ✅ .env, .env.example, .env.local
- ✅ docker-compose*.yml
- ✅ requirements*.txt
- ✅ pytest.ini

---

## 디렉토리 정리

### archives/
- 오래된 백업 확인 후 압축 또는 삭제

### temp/
- 내용 확인 후 완전 삭제

### data/
- 불필요한 중간 파일 정리

---

## 최적화 후 구조

```
rag-enterprise/
├── .backups/            # 백업 파일 (새로 생성)
├── .claude/             # 프로젝트 설정
├── agents/              # 에이전트 코드
├── app/                 # FastAPI 앱
├── config/              # 설정 파일
├── data/                # 데이터 (정리됨)
├── docs/                # 문서 (정리됨)
├── mcp_servers/         # MCP 서버
├── scripts/             # 스크립트
├── tests/               # 테스트
├── CLAUDE.md            # 시스템 문서
├── progress.md          # 진행상황
├── decisions.md         # 결정사항
├── bugs.md              # 버그 추적
├── SYSTEM_REVIEW.md     # 리뷰
└── .mcp.json            # MCP 설정
```

---

*Created: 2025-01-11*
