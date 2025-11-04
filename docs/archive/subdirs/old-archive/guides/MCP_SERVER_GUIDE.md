# MCP Server 사용 가이드

## 📍 MCP 서버 위치
```
/Users/oypnus/Project/rag-enterprise/mcp_servers/
├── __init__.py
├── claude_haiku_server.py  ✅ Claude Haiku 4.5 API
├── qdrant_server.py         ✅ Qdrant Vector DB
└── ollama_server.py         ✅ Ollama Local LLM
```

## 🔧 설치 및 설정

### 1. 필수 패키지 설치
```bash
pip install anthropic qdrant-client aiohttp python-dotenv
```

### 2. 환경변수 설정
`.env` 파일에 다음 환경변수 추가:
```bash
# Claude API
ANTHROPIC_API_KEY=your_claude_api_key_here

# Qdrant
QDRANT_HOST=172.28.0.2
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_PREFER_GRPC=true

# Ollama
OLLAMA_HOST=172.28.0.6
OLLAMA_PORT=11434
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct-q4_K_M
```

### 3. Docker 서비스 시작
```bash
# Colima 시작 (macOS)
colima start --cpu 16 --memory 24 --disk 100

# Docker Compose 실행
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

## 🧪 MCP 서버 테스트

### 방법 1: 자동 테스트 스크립트 (권장)
```bash
# 전체 테스트 실행
./scripts/test_mcp.sh
```

### 방법 2: Python 직접 실행
```bash
# 개별 테스트
python tests/test_mcp_servers.py
```

### 방법 3: 수동 테스트
```bash
# Claude Haiku 서버 테스트
echo '{"jsonrpc":"2.0","id":1,"method":"health","params":{}}' | python mcp_servers/claude_haiku_server.py

# Qdrant 서버 테스트
echo '{"jsonrpc":"2.0","id":2,"method":"health","params":{}}' | python mcp_servers/qdrant_server.py

# Ollama 서버 테스트
echo '{"jsonrpc":"2.0","id":3,"method":"health","params":{}}' | python mcp_servers/ollama_server.py
```

## 📖 MCP 서버 사용법

### 1️⃣ Claude Haiku Server

**지원 메서드**:
- `health`: Health check
- `generate`: 텍스트 생성

**예제**:
```json
// Health Check
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "health",
  "params": {}
}

// 텍스트 생성
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "generate",
  "params": {
    "prompt": "Python에서 리스트를 역순으로 정렬하는 방법은?",
    "max_tokens": 4096,
    "temperature": 0.3,
    "system": "You are a helpful coding assistant."
  }
}
```

**응답 예제**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "text": "Python에서 리스트를 역순으로 정렬하는 방법은...",
    "model": "claude-haiku-4-5-20251001"
  }
}
```

### 2️⃣ Qdrant Server

**지원 메서드**:
- `health`: Health check
- `create_collection`: 컬렉션 생성
- `insert_vectors`: 벡터 삽입
- `search_vectors`: 벡터 검색
- `delete_collection`: 컬렉션 삭제
- `list_collections`: 컬렉션 목록
- `get_collection_info`: 컬렉션 정보

**예제**:
```json
// 컬렉션 생성
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "create_collection",
  "params": {
    "collection_name": "documents",
    "vector_size": 768,
    "distance": "Cosine"
  }
}

// 벡터 삽입
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "insert_vectors",
  "params": {
    "collection_name": "documents",
    "points": [
      {
        "id": 1,
        "vector": [0.1, 0.2, ..., 0.768],
        "payload": {
          "text": "문서 내용",
          "source": "example.pdf"
        }
      }
    ]
  }
}

// 벡터 검색
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "search_vectors",
  "params": {
    "collection_name": "documents",
    "query_vector": [0.1, 0.2, ..., 0.768],
    "limit": 10,
    "score_threshold": 0.7
  }
}
```

### 3️⃣ Ollama Server

**지원 메서드**:
- `health`: Health check
- `list_models`: 모델 목록 조회
- `generate`: 텍스트 생성
- `chat`: 채팅 완료
- `pull_model`: 모델 다운로드
- `delete_model`: 모델 삭제
- `embeddings`: 임베딩 생성

**예제**:
```json
// 모델 목록 조회
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "list_models",
  "params": {}
}

// 텍스트 생성
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "generate",
  "params": {
    "prompt": "FastAPI 라우터 작성 방법은?",
    "model": "qwen2.5:7b-instruct-q4_K_M",
    "temperature": 0.7,
    "max_tokens": 2048
  }
}

// 채팅
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "chat",
  "params": {
    "messages": [
      {"role": "user", "content": "안녕하세요"}
    ],
    "model": "qwen2.5:7b-instruct-q4_K_M",
    "temperature": 0.7
  }
}

// 모델 다운로드
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "pull_model",
  "params": {
    "model_name": "llama3.1:8b-instruct-q4_K_M"
  }
}
```

## 🔍 트러블슈팅

### ❌ "ANTHROPIC_API_KEY not found"
**원인**: .env 파일에 API 키가 없음
**해결**:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-api03-xxxxx" >> .env
```

### ❌ "Failed to connect to Qdrant"
**원인**: Qdrant 서비스가 실행되지 않음
**해결**:
```bash
docker-compose up -d qdrant
docker-compose logs qdrant
```

### ❌ Ollama "Connection refused"
**원인**: Ollama 서비스가 실행되지 않음
**해결**:
```bash
docker-compose up -d ollama
docker exec rag-ollama ollama list
```

### ❌ "Module not found"
**원인**: 필수 패키지 미설치
**해결**:
```bash
pip install anthropic qdrant-client aiohttp python-dotenv
```

## 📊 Health Check 결과 예시

### ✅ 정상 상태
```json
// Claude Haiku
{
  "status": "healthy",
  "model": "claude-haiku-4-5-20251001"
}

// Qdrant
{
  "status": "healthy",
  "host": "172.28.0.2",
  "port": 6334,
  "protocol": "gRPC",
  "collections_count": 3
}

// Ollama
{
  "status": "healthy",
  "host": "172.28.0.6",
  "port": 11434,
  "default_model": "qwen2.5:7b-instruct-q4_K_M",
  "available_models": [
    "qwen2.5:7b-instruct-q4_K_M",
    "llama3.1:8b-instruct-q4_K_M"
  ],
  "models_count": 2
}
```

### ❌ 비정상 상태
```json
{
  "status": "unhealthy",
  "error": "Connection refused"
}
```

## 🚀 다음 단계

MCP 서버가 정상 작동하면:

1. **Agent 파이프라인 테스트**
   ```bash
   python -m agents.workflow_orchestrator agents/workflow_config.json
   ```

2. **RAG 파이프라인 구축**
   - 문서 파싱 → 청킹 → 임베딩 → 인덱싱 → 검색 → QA

3. **FastAPI 서버 시작**
   ```bash
   uvicorn api.main:app --reload
   ```

## 📝 참고 문서

- [CLAUDE.md](../CLAUDE.md) - 시스템 아키텍처
- [PRE_DEVELOPMENT_CHECKLIST.md](../PRE_DEVELOPMENT_CHECKLIST.md) - 개발 전 체크리스트
- [ENV_MANAGEMENT_GUIDE.md](../ENV_MANAGEMENT_GUIDE.md) - 환경변수 관리

---
*Last Updated: 2025-10-17*
