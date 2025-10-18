# MCP 설정 수정 완료 보고서

**수정일**: 2025-10-17
**이슈**: .mcp.json 스키마 위반
**상태**: ✅ 해결 완료

---

## 🔧 문제점

### 이전 .mcp.json 구조
```json
{
  "mcpServers": {
    "filesystem": {...},
    "claude_haiku": {
      "command": "python",
      "args": [...],
      "enabled": true,           // ❌ 비표준 필드
      "config": {...},           // ❌ 비표준 필드
      "description": "..."       // ❌ 비표준 필드
    },
    "custom_agents": {           // ❌ 중첩 구조 불가
      "workflow_orchestrator": {...}
    }
  },
  "environment": {...},          // ❌ 비표준 필드
  "health_checks": {...}         // ❌ 비표준 필드
}
```

**에러 메시지**:
```
mcpServers.custom_agents: Does not adhere to MCP server configuration schema
```

---

## ✅ 해결 방법

### 1️⃣ .mcp.json 최소화 (MCP 표준 스키마만)
**위치**: `/Users/oypnus/Project/rag-enterprise/.mcp.json`

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

**허용되는 필드만 사용**:
- ✅ `command`: 실행 명령어
- ✅ `args`: 명령어 인자
- ✅ `env`: 환경변수 (선택)

**제거된 비표준 필드**:
- ❌ `enabled`
- ❌ `config`
- ❌ `description`
- ❌ `managed_by`

---

### 2️⃣ 확장 설정 분리
**위치**: `/Users/oypnus/Project/rag-enterprise/config/mcp_extended_config.json`

복잡한 설정은 별도 파일로 분리:
- MCP 서버별 상세 설정
- Docker 서비스 설정
- Custom Agent 설정
- 환경별 설정
- Health Check 엔드포인트

**용도**: 내부 관리용 (Claude Code에서 로드 안 됨)

---

## 🎯 MCP 서버 목록

### 현재 활성화된 MCP 서버 (4개)

| MCP 서버 | 명령어 | 용도 |
|----------|--------|------|
| **filesystem** | npx @modelcontextprotocol/server-filesystem | 문서 파일 시스템 접근 |
| **claude_haiku** | python -m mcp_servers.claude_haiku_server | Claude Haiku API |
| **qdrant** | python -m mcp_servers.qdrant_server | 벡터 DB 연동 |
| **ollama** | python -m mcp_servers.ollama_server | 로컬 LLM |

---

## 📂 MCP 서버 구현 파일

```
/Users/oypnus/Project/rag-enterprise/mcp_servers/
├── __init__.py
├── claude_haiku_server.py  ✅ 5.2 KB (183줄)
├── qdrant_server.py         ✅ 13 KB (417줄)
└── ollama_server.py         ✅ 17 KB (496줄)
```

---

## 🔍 MCP 서버 동작 확인

### 1. Claude Code에서 확인
```bash
# Claude Code 실행 후
/mcp
```

**예상 결과**:
```
✅ filesystem - running
✅ claude_haiku - running
✅ qdrant - running
✅ ollama - running
```

### 2. 수동 테스트
```bash
# Python 테스트 도구
python tests/test_mcp_servers.py

# Bash 자동화 스크립트
./scripts/test_mcp.sh
```

---

## ⚙️ 환경변수 설정

MCP 서버들이 사용하는 환경변수는 `.env` 파일에서 관리:

```bash
# Claude Haiku
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Qdrant
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_PREFER_GRPC=true

# Ollama
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct-q4_K_M
```

**주의**: MCP 서버는 환경변수를 직접 읽습니다 (.env 파일 자동 로드).

---

## 🚀 사용 방법

### 1️⃣ Docker 서비스 시작
```bash
docker-compose up -d
```

### 2️⃣ MCP 서버 자동 시작
Claude Code를 실행하면 `.mcp.json`에 정의된 MCP 서버들이 자동으로 시작됩니다.

### 3️⃣ MCP 서버 상태 확인
```bash
# Claude Code 내에서
/mcp

# 또는 수동 테스트
python tests/test_mcp_servers.py
```

---

## 📊 MCP vs Custom Agents

### MCP 서버 (Claude Code 통합)
- ✅ **filesystem**: Claude Code에서 바로 사용 가능
- ✅ **claude_haiku**: Claude Code에서 바로 사용 가능
- ✅ **qdrant**: Claude Code에서 바로 사용 가능
- ✅ **ollama**: Claude Code에서 바로 사용 가능

### Custom Agents (별도 실행 필요)
- ⏳ **workflow_orchestrator**: `python -m agents.workflow_orchestrator`
- ⏳ **crawler_scheduler**: `python -m agents.crawler_scheduler`
- ⏳ **quality_monitor**: `python -m agents.quality_monitor`

**차이점**:
- **MCP 서버**: Claude Code가 자동으로 시작/관리
- **Custom Agents**: 수동으로 실행 (별도 프로세스)

---

## 🔧 트러블슈팅

### ❌ "Failed to parse .mcp.json"
**원인**: 비표준 필드 사용
**해결**: 표준 스키마만 사용 (command, args, env만)

### ❌ "MCP server failed to start"
**원인**:
1. Python 모듈을 찾을 수 없음
2. 환경변수 미설정

**해결**:
```bash
# 1. Python 경로 확인
export PYTHONPATH=/Users/oypnus/Project/rag-enterprise:$PYTHONPATH

# 2. 환경변수 확인
cat .env

# 3. 가상환경 활성화
source venv/bin/activate
```

### ❌ "context7 failed"
**원인**: context7 MCP 서버가 사용자 글로벌 설정에 있음

**해결**:
```bash
# 사용자 설정 확인
cat ~/.claude.json

# 또는 프로젝트 .mcp.json에서 관리
```

---

## 📝 주요 변경 사항 요약

### Before (비표준 스키마)
- ❌ 중첩 구조 (`custom_agents`)
- ❌ 비표준 필드 (`enabled`, `config`, `description`)
- ❌ 환경별 설정 (`environment`)
- ❌ Health check 설정

### After (표준 스키마)
- ✅ 평면 구조 (1단계만)
- ✅ 표준 필드만 (`command`, `args`)
- ✅ 복잡한 설정은 별도 파일로 분리
- ✅ Claude Code 호환

---

## 🎉 최종 상태

**MCP 설정**: ✅ **표준 스키마 준수**

**활성 MCP 서버**: 4개
- filesystem (Node.js)
- claude_haiku (Python)
- qdrant (Python)
- ollama (Python)

**다음 단계**:
1. Claude Code 재시작
2. `/mcp` 명령어로 확인
3. MCP 서버 동작 테스트

---

*수정 완료: 2025-10-17*
*참고 문서: https://docs.claude.com/en/docs/claude-code/mcp*
