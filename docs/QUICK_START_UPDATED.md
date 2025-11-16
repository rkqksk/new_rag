# Quick Start Guide - new_rag_ubuntu (Updated)

**목적**: main 브랜치 (v9.3.0 + Claude Skills v1.0.0) 빠른 시작

---

## 🚀 3분 시작 가이드

### Step 1: 현재 상태 확인 (30초)

```bash
# 브랜치 확인
git branch  # * main이어야 함

# 최신 커밋 확인
git log --oneline -1
# 687dc96 feat: Enhance Claude Skills System...

# Skills 확인
ls .claude/skills/*/SKILL.md | wc -l  # 9개
```

### Step 2: 환경 시작 (2분)

```bash
# Docker services 시작
docker-compose up -d

# Health check (30초 대기)
sleep 30
curl http://localhost:8001/health/ready
```

### Step 3: 확인 (30초)

```bash
# API 문서
open http://localhost:8001/api/v1/docs

# 또는 브라우저에서
# http://localhost:8001/api/v1/docs
```

---

## ✅ 성공 확인

### 1. Health Check
```bash
$ curl http://localhost:8001/health/ready
{"status":"ok","version":"9.3.0"}
```

### 2. API Docs
브라우저에서 http://localhost:8001/api/v1/docs 접속 시 Swagger UI 표시

### 3. Claude Skills
```bash
$ ls .claude/skills/*/SKILL.md | wc -l
9
```

---

## 🤖 Claude Skills 테스트 (NEW!)

### 자동 발동 테스트

Skills는 키워드로 자동 발동됩니다:

```
"RAG 검색 품질 개선해줘" → rag-optimization 자동 발동
"OneHago 크롤링" → data-collection 자동 발동
"YOLO 불량 검사" → manufacturing-vision 자동 발동
"pytest 테스트 생성" → testing-suite 자동 발동
```

### 스크립트 직접 실행

```bash
# RAG 분석
python .claude/skills/rag-optimization/scripts/analyze_chunks.py \
  --collection products

# 크롤러 생성 (테스트)
python .claude/skills/data-collection/scripts/create_crawler.py \
  --site test \
  --url https://example.com

# 테스트 자동 생성
python .claude/skills/testing-suite/scripts/generate_tests.py \
  --source src/services/ \
  --output tests/unit/

# YOLO 훈련 (데이터 필요)
python .claude/skills/manufacturing-vision/scripts/train_yolo.py \
  --data data/defects/data.yaml \
  --model yolov8n

# Excel 일괄 처리
python .claude/skills/excel-processing/scripts/batch_process.py \
  --input data/*.xlsx \
  --output processed/

# PDF 테이블 추출
python .claude/skills/pdf-processing/scripts/extract_tables.py \
  --pdf document.pdf

# K8s 매니페스트 생성
python .claude/skills/deployment-automation/scripts/generate_k8s.py \
  --app rag-api
```

---

## 📚 다음 단계

### 즉시 (오늘)

1. **Skills 문서 읽기** (30분)
   ```bash
   cat .claude/skills/README.md
   ```

2. **프로젝트 개요** (30분)
   ```bash
   cat README.md
   cat UPDATED_ANALYSIS_AND_ROADMAP.md
   ```

3. **시스템 탐색** (1시간)
   ```bash
   # 파일 구조
   ls -la

   # Skills 확인
   ls .claude/skills/

   # Python agents
   ls agents/

   # 문서
   ls docs/
   ```

4. **서비스 확인** (30분)
   ```bash
   # API
   open http://localhost:8001/api/v1/docs

   # Qdrant (Vector DB)
   open http://localhost:16333/dashboard

   # Grafana (Monitoring)
   open http://localhost:3000  # admin/admin

   # Jaeger (Tracing)
   open http://localhost:16686
   ```

### 이번 주 (Week 0)

- [ ] 환경 검증 완료
- [ ] Skills 모두 테스트
- [ ] 문서 정독
- [ ] 팀과 계획 공유
- [ ] Week 1 준비

### 다음 주 (Week 1 - Discovery)

- [ ] Skills 완전 활용 시작
- [ ] Sub-agent 분석 (필요시)
- [ ] v10.0.0 계획 최종화
- [ ] Week 2 준비

---

## 🔧 Troubleshooting

### Docker가 시작되지 않음

```bash
# Docker daemon 확인
docker ps

# 실패 시 Docker 재시작
sudo service docker restart

# 다시 시도
docker-compose up -d
```

### Port 충돌

```bash
# 사용 중인 포트 확인
sudo lsof -i :8001

# 프로세스 종료
kill -9 <PID>
```

### Skills 스크립트 에러

```bash
# Python 버전 확인
python --version  # 3.11+

# 의존성 설치
pip install -r requirements.txt

# 실행 권한
chmod +x .claude/skills/*/scripts/*.py
```

---

## 📊 현재 상태 확인

### 시스템 상태
```bash
# Services
docker-compose ps

# Health
curl http://localhost:8001/health/ready

# Logs
docker-compose logs -f api
```

### Skills 상태
```bash
# Skills 개수
ls .claude/skills/*/SKILL.md | wc -l  # 9

# Scripts 개수
find .claude/skills -name "*.py" | wc -l  # 8

# Examples
find .claude/skills -name "*.md" -path "*/examples/*" | wc -l  # 3
```

---

## 📞 도움말

### 문서

- **UPDATED_ANALYSIS_AND_ROADMAP.md** - 최신 분석 및 계획 ⭐
- **.claude/skills/README.md** - Skills 사용법 ⭐
- **COMPLETE_INTEGRATION_MASTER_PLAN.md** - v10.0.0 통합 계획
- **README.md** - 프로젝트 개요
- **CLAUDE.md** - Quick reference

### 주요 명령어

```bash
# Services
docker-compose up -d        # 시작
docker-compose down         # 중지
docker-compose restart api  # 재시작
docker-compose logs -f api  # 로그

# Health
curl http://localhost:8001/health/ready

# Skills
python .claude/skills/validate_skills.py  # 검증
```

---

## 🎯 목표 상기

### 현재 (v9.3.0 + Skills v1.0.0)
- ✅ 17 services running
- ✅ 48+ API endpoints
- ✅ **9 Claude Skills** ⭐
- ✅ **8 Automation Scripts** ⭐
- ✅ Production ready (95%+ coverage)
- ⚠️ Code duplication 40-85%
- ⚠️ 35+ top-level directories

### 목표 (v10.0.0)
- ✅ Skills integrated & utilized ⭐
- ✅ Single backend, single frontend
- ✅ Code duplication <5%
- ✅ 12 top-level directories
- ✅ 90% token savings
- ✅ 80%+ test coverage

### 기간
- **12 weeks** (수동 작업)
- **7 weeks** (Sub-agent 활용)
- **5 weeks** (Sub-agent + Skills 활용) ⭐ NEW

---

**시작했습니다! 🚀**

**Next**: UPDATED_ANALYSIS_AND_ROADMAP.md 읽기
**Skills Power**: 반복 작업을 Skills에 위임하세요!
