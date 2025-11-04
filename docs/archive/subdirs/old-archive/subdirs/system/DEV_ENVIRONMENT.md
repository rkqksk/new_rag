# RAG Enterprise 개발 환경 설정
*마지막 업데이트: 2025-10-18*

## 🎯 개발 환경 개요

이 프로젝트는 **direnv 기반 Python 개발 환경**과 **Docker 컨테이너 오케스트레이션**을 조합한 하이브리드 인프라를 사용합니다.

## 📦 로컬 개발 환경

### 1. direnv 기반 Python 환경 관리

**왜 direnv를 사용하는가?**
- 프로젝트 디렉토리 진입 시 자동으로 환경 활성화
- `.envrc` 파일로 환경변수 및 가상환경을 중앙 관리
- `venv/`, `.venv/` 수동 관리 불필요

**설정 파일**: `.envrc`

```bash
# Python 버전
export PYTHON_VERSION=3.11

# direnv로 가상환경 자동 관리
layout python python${PYTHON_VERSION}

# UV 캐시 (선택)
export UV_CACHE_DIR="$HOME/.cache/uv/"
```

**환경변수 구조**:
```bash
# API Keys
export CLAUDE_API_KEY="sk-ant-api03-..."
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export GROQ_API_KEY="gsk_..."
export OPENAI_API_KEY="sk-proj-..."
export OLLAMA_API_KEY="e0a9b..."

# Claude SDK 설정
export ANTHROPIC_MODEL="claude-3-opus-20240229"
export CLAUDE_SDK_TIMEOUT=45

# Database Credentials
export POSTGRES_USER="rkqksk"
export POSTGRES_PASSWORD="rkqksk"
export MONGO_USER="rkqksk"
export MONGO_PASSWORD="rkqksk"

# N8N & Monitoring
export N8N_USER="rkqksk@gmail.com"
export N8N_PASSWORD='!Wlsdk1989'
export GRAFANA_PASSWORD="rkqksk"

# PATH에 로컬 bin 추가
PATH_add node_modules/.bin
```

**가상환경 위치**:
- direnv 관리: `.direnv/python-3.11/`
- ⚠️ `venv/`, `.venv/`는 **사용하지 않음** (삭제 가능)

### 2. 환경 활성화 방법

```bash
# 프로젝트 디렉토리 진입 시 자동 활성화
cd /Users/oypnus/Project/rag-enterprise

# direnv 허용 (최초 1회)
direnv allow

# 환경변수 확인
echo $ANTHROPIC_API_KEY
```

---

## 🐳 Docker 인프라 스택

### Docker Compose 아키텍처

**네트워크**: `rag_network` (172.28.0.0/16)
**관리 도구**: Colima (macOS Docker Desktop 대체)

### 서비스 구성

| 서비스 | 컨테이너명 | IP | 포트 | 용도 | 리소스 |
|--------|-----------|-----|------|------|--------|
| **Qdrant** | rag-qdrant | 172.28.0.2 | 6333 (HTTP), 6334 (gRPC) | 벡터 검색 | CPU 2, RAM 4GB |
| **Redis** | rag-redis | 172.28.0.3 | 6379 | 캐싱 & 세션 | CPU 1, RAM 2GB |
| **PostgreSQL** | rag-postgres | 172.28.0.4 | 5432 | 메타데이터 저장 | CPU 2, RAM 4GB |
| **N8N** | rag-n8n | 172.28.0.5 | 5678 | 워크플로우 자동화 | CPU 2, RAM 3GB |
| **Ollama** | rag-ollama | 172.28.0.6 | 11434 | 로컬 LLM 추론 | CPU 4, RAM 8GB |
| **FastAPI** | rag-fastapi | 172.28.0.7 | 8000 | API 서버 | CPU 2, RAM 4GB |

### 볼륨 관리

```yaml
volumes:
  qdrant_data:    # 벡터 저장소
  redis_data:     # 캐시 데이터
  postgres_data:  # 메타데이터
  n8n_data:       # 워크플로우
  ollama_models:  # LLM 모델
```

### Docker 명령어

```bash
# 전체 스택 시작
docker-compose up -d

# 특정 서비스 재시작
docker-compose restart fastapi

# FastAPI 재빌드
docker-compose up -d --build fastapi

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f fastapi
docker-compose logs -f qdrant

# 전체 종료
docker-compose down

# 볼륨 포함 완전 삭제
docker-compose down -v

# 개별 컨테이너 접속
docker exec -it rag-postgres psql -U postgres -d rag_enterprise
docker exec -it rag-redis redis-cli
docker exec -it rag-ollama ollama list
```

### Health Check 엔드포인트

```bash
# Qdrant
curl http://localhost:6333/collections

# Redis
docker exec rag-redis redis-cli ping

# PostgreSQL
docker exec rag-postgres pg_isready

# FastAPI
curl http://localhost:8000/health

# N8N
curl http://localhost:5678/healthz

# Ollama
curl http://localhost:11434/api/tags
```

---

## 🔌 MCP (Model Context Protocol) 서버

### 설정 파일: `.mcp.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./documents"]
    },
    "claude_haiku": {
      "command": "python",
      "args": ["-m", "mcp_servers.claude_haiku_server"]
    },
    "google_devtools": {
      "command": "python",
      "args": ["-m", "mcp_servers.google_devtools.server"]
    },
    "qdrant": {
      "command": "python",
      "args": ["-m", "mcp_servers.qdrant_server"]
    },
    "ollama": {
      "command": "python",
      "args": ["-m", "mcp_servers.ollama_server"]
    }
  }
}
```

### MCP 서버 설명

| 서버 | 용도 | 구현 위치 |
|------|------|-----------|
| **filesystem** | 문서 파일시스템 접근 | NPM 패키지 |
| **claude_haiku** | 경량 LLM 작업 (claude-haiku-4-5) | `mcp_servers/claude_haiku_server.py` |
| **google_devtools** | 브라우저 디버깅 | `mcp_servers/google_devtools/server.py` |
| **qdrant** | Qdrant 벡터DB 연동 | `mcp_servers/qdrant_server.py` |
| **ollama** | Ollama 로컬 LLM 연동 | `mcp_servers/ollama_server.py` |

---

## 🗂️ 프로젝트 구조 (개발 환경 관점)

```
rag-enterprise/
├── .direnv/                # direnv 가상환경 (자동 생성)
│   └── python-3.11/        # Python 3.11 환경
├── .envrc                  # direnv 설정 파일 ⭐
├── .env                    # 환경변수 (Git 제외)
├── .env.example            # 환경변수 템플릿
├── .mcp.json              # MCP 서버 설정 ⭐
├── docker-compose.yml      # Docker 인프라 정의 ⭐
├── Dockerfile              # FastAPI 컨테이너 빌드
├── requirements.txt        # Python 의존성
│
├── app/                    # FastAPI 애플리케이션
│   └── api/
│       └── main.py         # API 엔트리포인트
│
├── agents/                 # AI 에이전트
│   ├── clean_deploy_agent_v2.py
│   ├── debugging_agent.py
│   └── workflow_orchestrator_v3.py
│
├── mcp_servers/            # MCP 서버 구현
│   ├── claude_haiku_server.py
│   ├── qdrant_server.py
│   ├── ollama_server.py
│   └── google_devtools/
│
├── config/                 # 설정 파일
│   ├── clean_deploy_config.json
│   ├── pipeline_config.json
│   └── mcp_extended_config.json
│
├── data/                   # 데이터 (Git 제외)
│   ├── crawled_products_organized/
│   └── rag_embeddings/
│
├── temp/                   # 임시 파일 (Git 제외, 자동 정리)
├── logs/                   # 로그 (Git 제외)
├── archives/               # 백업 & 보관 (Git 제외)
└── claudedocs/             # Claude 생성 문서 (Git 제외)
```

---

## 🛠️ 개발 워크플로우

### 1. 환경 초기 설정

```bash
# 1. direnv 설치 (macOS)
brew install direnv

# 2. 셸 설정 (zsh)
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# 3. 프로젝트 클론 후 direnv 허용
cd /Users/oypnus/Project/rag-enterprise
direnv allow

# 4. Python 의존성 설치
pip install -r requirements.txt

# 5. Docker 인프라 시작
docker-compose up -d

# 6. Ollama 모델 다운로드
docker exec rag-ollama ollama pull qwen2.5:7b
docker exec rag-ollama ollama pull qwen2.5:3b
```

### 2. 일상적인 개발

```bash
# 프로젝트 디렉토리 진입 → 자동 환경 활성화
cd /Users/oypnus/Project/rag-enterprise

# FastAPI 개발 서버 (로컬)
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Docker 서비스 확인
docker-compose ps

# 특정 서비스 로그 모니터링
docker-compose logs -f fastapi
```

### 3. 코드 변경 후

```bash
# FastAPI 변경 시 → Docker 재빌드
docker-compose up -d --build fastapi

# Agent 코드 변경 시 → 로컬 테스트
python agents/workflow_orchestrator_v3.py

# 환경변수 변경 시
direnv allow  # .envrc 수정 후
docker-compose restart  # Docker 환경변수 반영
```

---

## 🚨 주의사항 및 베스트 프랙티스

### ✅ DO (권장)

1. **direnv 사용**
   - `.direnv/` 디렉토리는 자동 생성되므로 Git 제외
   - 환경변수 변경 시 `.envrc` 수정 후 `direnv allow`

2. **Docker 우선**
   - Qdrant, Redis, PostgreSQL 등 인프라는 Docker로만 관리
   - 로컬 설치 금지 (포트 충돌 방지)

3. **환경변수 보안**
   - `.env` 파일은 절대 커밋 금지
   - `.env.example`만 Git 추적

4. **볼륨 백업**
   ```bash
   # 중요 데이터 백업
   docker run --rm -v rag_enterprise_qdrant_data:/data \
     -v $(pwd)/backups:/backup alpine \
     tar czf /backup/qdrant_backup.tar.gz /data
   ```

### ❌ DON'T (금지)

1. **venv/virtualenv 수동 생성 금지**
   - ❌ `python -m venv venv`
   - ❌ `virtualenv .venv`
   - ✅ direnv가 `.direnv/`에 자동 관리

2. **Docker 컨테이너 직접 수정 금지**
   - ❌ 컨테이너 내부 파일 수정
   - ✅ Dockerfile 수정 후 재빌드

3. **포트 충돌 방지**
   - 6333, 6379, 5432, 11434, 8000 포트 로컬 사용 금지

4. **환경변수 하드코딩 금지**
   - ❌ 코드에 API 키 직접 작성
   - ✅ `.envrc` 또는 `.env`에서 관리

---

## 🔧 트러블슈팅

### 문제: direnv가 환경을 로드하지 않음

```bash
# 해결: direnv 재허용
direnv allow

# 강제 리로드
direnv reload
```

### 문제: Docker 컨테이너가 시작하지 않음

```bash
# 1. 로그 확인
docker-compose logs [service_name]

# 2. 컨테이너 완전 재시작
docker-compose down
docker-compose up -d --force-recreate

# 3. 볼륨 초기화 (주의!)
docker-compose down -v
docker-compose up -d
```

### 문제: Qdrant 연결 실패

```bash
# Health check
curl http://localhost:6333/collections

# 컨테이너 내부 확인
docker exec -it rag-qdrant ls /qdrant/storage

# 재시작
docker-compose restart qdrant
```

### 문제: Ollama 모델 로딩 실패

```bash
# 모델 목록 확인
docker exec rag-ollama ollama list

# 모델 재다운로드
docker exec rag-ollama ollama pull qwen2.5:7b

# 볼륨 확인
docker volume inspect rag_enterprise_ollama_models
```

---

## 📊 개발 환경 모니터링

### 리소스 사용량 확인

```bash
# Docker 리소스 사용량
docker stats

# 개별 컨테이너
docker stats rag-qdrant rag-ollama rag-fastapi
```

### 디스크 사용량

```bash
# Docker 전체 디스크 사용량
docker system df

# 볼륨 사이즈
docker volume ls
du -sh $(docker volume inspect rag_enterprise_qdrant_data -f '{{.Mountpoint}}')
```

---

## 🎓 참고 자료

- **direnv 공식 문서**: https://direnv.net/
- **Docker Compose**: https://docs.docker.com/compose/
- **Qdrant**: https://qdrant.tech/documentation/
- **Ollama**: https://ollama.ai/
- **MCP (Model Context Protocol)**: https://modelcontextprotocol.io/

---

*이 문서는 프로젝트 개발 환경의 Single Source of Truth입니다. 환경 변경 시 반드시 업데이트하세요.*
