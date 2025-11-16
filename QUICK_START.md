# Quick Start Guide - new_rag_ubuntu

**목적**: 빈 repository에서 v9.3.0 Production Ready 시스템을 시작하는 최단 경로

---

## 🚀 5분 시작 가이드

### Step 1: 코드 가져오기 (2분)

```bash
# 현재 위치 확인
pwd  # /home/user/new_rag_ubuntu 이어야 함

# claude-code-mac 브랜치 내용 가져오기
git merge origin/claude-code-mac --allow-unrelated-histories

# 또는 직접 체크아웃 (더 간단)
git checkout -b main origin/claude-code-mac
```

### Step 2: 환경 시작 (3분)

```bash
# Docker services 시작
docker-compose up -d

# Health check (30초 대기)
sleep 30
curl http://localhost:8001/health/ready
```

### Step 3: 확인

```bash
# API 문서 열기
open http://localhost:8001/api/v1/docs

# 또는 브라우저에서
# http://localhost:8001/api/v1/docs
```

---

## ✅ 성공 확인

다음이 모두 작동하면 성공:

### 1. Health Check
```bash
$ curl http://localhost:8001/health/ready
{"status":"ok","version":"9.3.0"}
```

### 2. API Docs
브라우저에서 http://localhost:8001/api/v1/docs 접속 시 Swagger UI 표시

### 3. Docker Services
```bash
$ docker-compose ps
# 17개 services가 모두 "Up" 상태
```

---

## 📚 다음 단계

### 즉시 (오늘)

1. **문서 읽기** (3-4시간)
   ```bash
   # 프로젝트 개요
   cat README.md

   # 종합 분석 및 로드맵
   cat REPOSITORY_ANALYSIS_AND_ROADMAP.md

   # v10.0.0 통합 계획
   cat COMPLETE_INTEGRATION_MASTER_PLAN.md
   ```

2. **시스템 탐색** (1-2시간)
   ```bash
   # 파일 구조 확인
   ls -la

   # 주요 디렉토리
   ls apps/        # Frontend apps
   ls backend/     # Python backend
   ls packages/    # Shared packages
   ls docs/        # Documentation
   ```

3. **서비스 확인** (30분)
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

- [ ] 모든 문서 읽기
- [ ] 시스템 탐색
- [ ] 팀과 계획 공유
- [ ] Week 1 준비

### 다음 주 (Week 1 - Discovery)

- [ ] Sub-agent 분석 실행
- [ ] Migration backlog 작성
- [ ] 팀 리뷰 및 승인
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

# 프로세스 종료 (PID는 위 명령어 결과에서 확인)
kill -9 <PID>
```

### Health check 실패

```bash
# 로그 확인
docker-compose logs api

# 특정 서비스 재시작
docker-compose restart api
```

---

## 📞 도움말

### 문서

- **REPOSITORY_ANALYSIS_AND_ROADMAP.md** - 종합 분석 및 발전 계획
- **COMPLETE_INTEGRATION_MASTER_PLAN.md** - v10.0.0 통합 계획
- **README.md** - 프로젝트 개요
- **docs/** - 상세 문서

### 주요 명령어

```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs -f api

# 특정 서비스 재시작
docker-compose restart api

# 전체 재시작
docker-compose restart

# Health check
curl http://localhost:8001/health/ready
```

---

## 🎯 목표 상기

### 현재 (v9.3.0)
- ✅ 17 services running
- ✅ 48+ API endpoints
- ✅ Production ready
- ⚠️ Code duplication 40-85%
- ⚠️ 35+ top-level directories

### 목표 (v10.0.0)
- ✅ Single backend, single frontend
- ✅ Code duplication <5%
- ✅ 12 top-level directories
- ✅ 90% token savings
- ✅ 80%+ test coverage

### 기간
- **12 weeks** (수동 작업)
- **7 weeks** (Sub-agent 활용)

---

**시작했습니다! 🚀**

**Next**: REPOSITORY_ANALYSIS_AND_ROADMAP.md 읽기
