# 문서 자동 정리 미리보기

## 📋 현재 루트 파일 분석 결과

### ✅ 루트 유지 (중요 파일)
- CLAUDE.md
- PROGRESS.md (있다면)
- README.md (있다면)
- QUICK_START.md
- Makefile
- Dockerfile
- pytest.ini
- .env, .env.example, .env.local, .envrc
- .gitignore, .dockerignore, .claudeignore
- .coveragerc

### 📁 docs/guides/ 로 이동
- CLAUDE_CLEANUP_GUIDE.md
- CLAUDE_OPTIMIZED.md
- CHAT_MVP_README.md

### 📊 docs/analysis/ 로 이동
- DISCOUNT_ANALYSIS_INDEX.md
- DISCOUNT_PRICE_ANALYSIS.md
- DISCOUNT_PARSING_VISUAL_SUMMARY.md
- INCOMPLETE_DATA_REPORT.md

### 🔧 docs/development/ 로 이동
- DISCOUNT_IMPLEMENTATION_GUIDE.py (개발 가이드)
- SKILLS_READY.md

### 🧪 tests/ 로 이동
- test_api_quick.py
- test_chat_mvp.py
- test_comparison_system.py
- test_frontend.py
- test_frontend_debug.js
- test_recommendation_api.py
- test_server.py
- test_vector_search.py

### ⚙️ config/mcp/ 로 이동
- .mcp.json
- .mcp.max.json
- .mcp.minimal.json
- .mcp.profile.current
- .mcp.zero.json

### 🐳 config/docker/ 로 이동
- docker-compose.ollama-disabled.yml
- docker-compose.production.yml
- docker-compose.staging.yml
- docker-compose.yml (기본 compose 파일은 루트에 유지할지 결정 필요)

### 📦 config/requirements/ 로 이동
- requirements-chat.txt
- requirements-docker.txt
- requirements-prod.txt

### 🔨 scripts/ 로 이동
- apply-claude-config.sh
- run_chat_server.py
- run_comparison_server.py
- run_consolidation.sh
- validate_skills.py

## 📦 30일 이상 수정 안 된 파일 (아카이빙 대상)

파일의 수정 날짜를 확인한 후 `docs/archived/YYYY-MM/` 로 자동 이동됩니다.

## 🚀 실행 방법

### 1. 미리보기 (추천)
```bash
python3 scripts/maintenance/auto_organize_docs.py
```

### 2. 실제 적용
```bash
python3 scripts/maintenance/auto_organize_docs.py --execute
```

### 3. Git hook 설치
```bash
./scripts/maintenance/install.sh
```

## 💡 참고사항

- docker-compose.yml은 기본 파일이므로 루트 유지 여부를 결정하세요
- requirements.txt는 기본 파일이므로 루트에 유지됩니다
- 스크립트 실행 전 항상 Git commit/backup 하세요
