# 컨텍스트 인식 대화 시스템 MVP

**B. 컨텍스트 인식 대화** 기능의 MVP 구현입니다.

## 🎯 주요 기능

- ✅ **세션 관리**: Redis 기반 대화 컨텍스트 유지 (1시간 TTL)
- ✅ **의도 분류**: 규칙 기반 사용자 의도 감지 (10가지 인텐트)
- ✅ **참조 해결**: "그 용기", "첫 번째", "이전 제품" 등 자동 해결
- ✅ **컨텍스트 기반 검색**: 대화 이력을 활용한 지능형 검색
- ✅ **HTTP API + WebSocket**: REST API와 실시간 채팅 지원

## 📋 사전 요구사항

### 1. Redis 설치 및 실행

**macOS**:
\`\`\`bash
brew install redis
redis-server
\`\`\`

**Linux**:
\`\`\`bash
sudo apt-get install redis-server
redis-server
\`\`\`

**Docker**:
\`\`\`bash
docker run -d -p 6379:6379 redis:7-alpine
\`\`\`

### 2. Python 의존성 설치

\`\`\`bash
pip install -r requirements-chat.txt
\`\`\`

## 🚀 빠른 시작

### 1. 서버 실행

\`\`\`bash
python run_chat_server.py
\`\`\`

서버가 **http://localhost:8001** 에서 실행됩니다.

### 2. API 문서 확인

브라우저에서 http://localhost:8001/docs 접속

### 3. 테스트 시나리오

#### 시나리오 1: HTTP API 테스트

\`\`\`bash
# 1. 세션 생성
curl -X POST http://localhost:8001/chat/create_session \\
  -H "Content-Type: application/json" \\
  -d '{"user_id": "test_user"}'

# 응답 예시:
# {"session_id": "chat_session:xxx-xxx-xxx", "created_at": "2025-..."}

# 2. 첫 번째 쿼리 (검색)
curl -X POST http://localhost:8001/chat/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "session_id": "chat_session:xxx-xxx-xxx",
    "query": "100ml 에센스 용기 추천해줘"
  }'

# 3. 참조 쿼리 (컨텍스트 유지)
curl -X POST http://localhost:8001/chat/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "session_id": "chat_session:xxx-xxx-xxx",
    "query": "첫 번째 제품에 맞는 펌프는?"
  }'

# 4. 필터 쿼리 (컨텍스트 유지)
curl -X POST http://localhost:8001/chat/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "session_id": "chat_session:xxx-xxx-xxx",
    "query": "더 저렴한 옵션 있어?"
  }'
\`\`\`

#### 시나리오 2: Python 클라이언트 테스트

\`\`\`python
import requests

BASE_URL = "http://localhost:8001"

# 1. 세션 생성
response = requests.post(f"{BASE_URL}/chat/create_session", json={
    "user_id": "test_user"
})
session_id = response.json()["session_id"]
print(f"세션 생성: {session_id}")

# 2. 대화 시작
queries = [
    "100ml 에센스 용기 추천해줘",
    "첫 번째 제품 상세 정보",
    "그 용기에 맞는 펌프는?",
    "가격은 얼마야?",
    "더 저렴한 거 없어?"
]

for query in queries:
    print(f"\\n👤 사용자: {query}")

    response = requests.post(f"{BASE_URL}/chat/query", json={
        "session_id": session_id,
        "query": query
    })

    result = response.json()
    print(f"🤖 봇: {result['response']}")
    print(f"   의도: {result['intent']['intent']}")
    print(f"   참조 해결: {result['reference_resolved']}")
    print(f"   제품 수: {result['total_count']}")
\`\`\`

#### 시나리오 3: WebSocket 테스트

**JavaScript (Node.js)**:
\`\`\`javascript
const WebSocket = require('ws');

// 1. 먼저 HTTP로 세션 생성
const createSession = async () => {
  const response = await fetch('http://localhost:8001/chat/create_session', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: 'test_user'})
  });
  const data = await response.json();
  return data.session_id;
};

// 2. WebSocket 연결
const testWebSocket = async () => {
  const sessionId = await createSession();
  const ws = new WebSocket(\`ws://localhost:8001/chat/ws/\${sessionId}\`);

  ws.on('open', () => {
    console.log('WebSocket 연결됨');

    // 쿼리 전송
    ws.send(JSON.stringify({
      query: "100ml 에센스 용기 추천해줘"
    }));
  });

  ws.on('message', (data) => {
    const message = JSON.parse(data);
    console.log('응답:', message);

    // 참조 쿼리 테스트
    setTimeout(() => {
      ws.send(JSON.stringify({
        query: "첫 번째 제품에 맞는 펌프는?"
      }));
    }, 1000);
  });
};

testWebSocket();
\`\`\`

## 📊 테스트 가능한 시나리오

### 1. 기본 검색
\`\`\`
👤: "100ml 에센스 용기 찾아줘"
🤖: 검색 결과 + 제품 목록

👤: "PE 재질로 찾아줘"
🤖: 필터 적용된 결과
\`\`\`

### 2. 참조 해결
\`\`\`
👤: "100ml 용기 추천해줘"
🤖: [제품 A, B, C 표시]

👤: "첫 번째 제품 상세 정보"
🤖: 제품 A의 상세 정보

👤: "그 용기에 맞는 펌프는?"
🤖: 제품 A와 호환되는 펌프 목록
\`\`\`

### 3. 컨텍스트 유지
\`\`\`
👤: "클렌징 오일 용기"
🤖: 오일 호환 재질 (PE) 우선 추천

👤: "더 저렴한 옵션"
🤖: 같은 조건에서 가격 낮은 제품

👤: "투명한 걸로"
🤖: 투명 + 오일 호환 + 저렴 조건 적용
\`\`\`

### 4. 호환성 확인
\`\`\`
👤: "100ml PE 용기 추천"
🤖: [제품 목록]

👤: "첫 번째 제품 호환 펌프"
🤖: 네크 사이즈 기반 호환 펌프 목록

👤: "가격은?"
🤖: 용기 + 펌프 패키지 가격
\`\`\`

## 🏗️ 아키텍처

\`\`\`
┌─────────────────────────────────────────┐
│         FastAPI Server (8001)           │
│  ┌────────────┐  ┌──────────────────┐  │
│  │ HTTP API   │  │ WebSocket        │  │
│  │ /chat/*    │  │ /chat/ws/{id}    │  │
│  └────────────┘  └──────────────────┘  │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│        ContextualRAG Service            │
│  ┌──────────────┐  ┌────────────────┐  │
│  │ Conversation │  │ Intent         │  │
│  │ Manager      │  │ Classifier     │  │
│  └──────────────┘  └────────────────┘  │
│  ┌──────────────┐  ┌────────────────┐  │
│  │ Reference    │  │ Product Search │  │
│  │ Resolver     │  │ Engine         │  │
│  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Data Layer                      │
│  ┌──────────────┐  ┌────────────────┐  │
│  │ Redis        │  │ Product JSON   │  │
│  │ (Sessions)   │  │ Files (846개)  │  │
│  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────┘
\`\`\`

## 🧪 의도 분류 테스트

시스템이 감지할 수 있는 의도 유형:

| 의도 | 키워드 예시 | 설명 |
|------|-----------|------|
| **SEARCH** | 찾아줘, 추천, 있어 | 제품 검색 |
| **COMPARE** | 비교, 차이, 어떤 게 나아 | 제품 비교 |
| **DETAIL** | 상세, 자세히, 스펙 | 상세 정보 |
| **FILTER** | 제외, 말고, 저렴한 | 필터 적용 |
| **COMPATIBILITY** | 맞는, 호환, 쓸 수 있 | 호환성 확인 |
| **PRICE** | 가격, 얼마, 비용 | 가격 정보 |
| **REFERENCE** | 그거, 첫 번째, 이전 | 이전 대화 참조 |
| **RECOMMENDATION** | 추천, 좋은, 괜찮은 | 추천 요청 |

## 📈 성능 목표

- **세션 생성**: < 10ms
- **쿼리 응답**: < 500ms (검색 10개 제품 기준)
- **참조 해결**: < 50ms
- **동시 세션**: 1000+ (Redis 기반)

## 🔧 개발 & 디버깅

### 로그 확인

서버 실행 시 상세 로그가 출력됩니다:
- 의도 분류 결과
- 참조 해결 과정
- 검색 쿼리 및 결과
- 세션 상태 변화

### Redis 데이터 확인

\`\`\`bash
redis-cli

# 모든 세션 조회
KEYS chat_session:*

# 특정 세션 데이터 확인
GET chat_session:xxx-xxx-xxx

# 세션 TTL 확인
TTL chat_session:xxx-xxx-xxx
\`\`\`

### API 테스트 도구

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Postman**: 제공된 curl 명령어 import

## 🐛 문제 해결

### Redis 연결 오류
\`\`\`bash
# Redis 실행 확인
redis-cli ping
# 응답: PONG

# Redis 프로세스 확인
ps aux | grep redis
\`\`\`

### 의존성 오류
\`\`\`bash
# 재설치
pip install --upgrade -r requirements-chat.txt
\`\`\`

### 세션 만료 문제
- 기본 TTL: 1시간
- 연장 API: `POST /chat/session/{id}/extend`

## 📝 다음 단계

### Phase 2 (완성도 향상)
- [ ] KoBERT 모델 통합 (더 정확한 의도 분류)
- [ ] Qdrant 벡터 검색 통합 (현재는 파일 기반)
- [ ] 대화 이력 요약 기능
- [ ] 멀티턴 대화 최적화

### Phase 3 (프론트엔드)
- [ ] React 채팅 UI
- [ ] 실시간 제품 프리뷰
- [ ] 대화 이력 시각화
- [ ] 모바일 반응형 디자인

## 💡 사용 팁

1. **긴 대화**: 세션 TTL 자동 연장됨 (매 쿼리마다)
2. **참조 해결**: "그거", "첫 번째" 등 자연스러운 표현 사용 가능
3. **필터 누적**: 대화 중 필터가 누적되어 점점 정교한 검색 가능
4. **컨텍스트 초기화**: 새로운 검색 시작 시 새 세션 생성 권장

## 🤝 기여

문제 발견 시:
1. GitHub Issues에 버그 리포트
2. 재현 가능한 테스트 케이스 제공
3. 기대 동작 vs 실제 동작 설명

## 📄 라이선스

Open Source (MIT)
