# Claude Haiku 4.5 MCP 서버 설정 가이드

## 📁 생성된 파일들

```
rag-enterprise/
├── mcp_servers/
│   ├── __init__.py                   # 모듈 초기화
│   └── claude_haiku_server.py        # Haiku MCP 서버 (★ 메인)
├── tests/
│   └── test_haiku_mcp.py             # 테스트 스크립트
├── .mcp.json                          # MCP 서버 등록 (수정됨)
└── docs/
    └── HAIKU_MCP_SETUP.md            # 이 파일
```

---

## ✅ 단계별 검증 체크리스트

### 1단계: 환경 변수 확인

```bash
# .env 파일에 API 키가 있는지 확인
cat .env | grep ANTHROPIC_API_KEY

# 출력 예시:
# ANTHROPIC_API_KEY=sk-ant-api...
```

✅ **확인 완료**: API 키가 `.env`에 설정되어 있음

---

### 2단계: 패키지 설치

```bash
# anthropic Python SDK 설치 확인
pip list | grep anthropic

# 없으면 설치
pip install anthropic python-dotenv
```

✅ **확인 완료**: `anthropic` 패키지 설치됨

---

### 3단계: 직접 API 호출 테스트

**위치**: `mcp_servers/claude_haiku_server.py` 라인 1-140

```bash
# 간단한 테스트
python -c "
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
response = client.messages.create(
    model='claude-haiku-4-5-20251001',
    max_tokens=100,
    messages=[{'role': 'user', 'content': '2+2는?'}]
)
print(response.content[0].text)
"
```

**예상 출력**:
```
2+2는 4입니다.
```

✅ **확인 완료**: API 호출 성공

---

### 4단계: MCP 서버 등록 확인

**위치**: `.mcp.json` 라인 9-19

```bash
# MCP 설정 확인
cat .mcp.json | grep -A 10 "claude_haiku"
```

**예상 출력**:
```json
"claude_haiku": {
  "command": "python",
  "args": ["-m", "mcp_servers.claude_haiku_server"],
  "description": "Claude Haiku 4.5 API for lightweight tasks",
  "config": {
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 4096,
    "temperature": 0.3
  },
  "enabled": true
},
```

✅ **확인 완료**: MCP 서버가 `.mcp.json`에 등록됨

---

### 5단계: 통합 테스트 실행

```bash
# 전체 테스트 실행
python tests/test_haiku_mcp.py
```

**예상 출력**:
```
🧪 Claude Haiku MCP Server 테스트 시작

============================================================
테스트 1: 직접 Haiku API 호출
============================================================
✅ Haiku 응답: 2+2는 4입니다.

============================================================
테스트 2: MCP 서버 통신
============================================================
✅ Health check 성공: {'jsonrpc': '2.0', 'id': 1, 'result': {...}}
✅ 생성 성공: Python에서 리스트를 만드는 방법은...

============================================================
테스트 결과
============================================================
직접 API 호출: ✅ PASS
MCP 서버 통신: ✅ PASS

🎉 모든 테스트 통과!
```

✅ **확인 완료**: 모든 테스트 통과

---

## 🔧 블록별 코드 위치 (수정 시 참고)

### BLOCK 1: MCP 서버 초기화
**파일**: `mcp_servers/claude_haiku_server.py`
**위치**: 라인 1-30
**기능**: 환경 변수 로드 및 Anthropic 클라이언트 초기화

```python
# 라인 20-30 근처
def __init__(self):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found")
    self.client = anthropic.Anthropic(api_key=api_key)
    self.model = "claude-haiku-4-5-20251001"
```

**수정 시**: 이 블록 전체를 새 코드로 교체 가능

---

### BLOCK 2: API 호출 함수
**파일**: `mcp_servers/claude_haiku_server.py`
**위치**: 라인 32-60
**기능**: Haiku API 실제 호출

```python
# 라인 32-60 근처
async def call_haiku(self, prompt: str, max_tokens: int = 4096, ...):
    messages = [{"role": "user", "content": prompt}]

    kwargs = {
        "model": self.model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages
    }

    response = self.client.messages.create(**kwargs)
    return response.content[0].text
```

**수정 시**: 이 함수 전체를 새 버전으로 교체 가능

---

### BLOCK 3: MCP 요청 핸들러
**파일**: `mcp_servers/claude_haiku_server.py`
**위치**: 라인 62-105
**기능**: MCP 프로토콜 요청 처리 (generate, health)

```python
# 라인 62-105 근처
async def handle_request(self, request: Dict[str, Any]):
    method = request.get("method")

    if method == "generate":
        # 텍스트 생성
        ...
    elif method == "health":
        # Health check
        ...
```

**수정 시**: 새 method 추가하려면 이 블록에 `elif` 추가

---

### BLOCK 4: 서버 메인 루프
**파일**: `mcp_servers/claude_haiku_server.py`
**위치**: 라인 107-140
**기능**: stdin/stdout 통신 루프

```python
# 라인 107-140 근처
async def run(self):
    while True:
        line = sys.stdin.readline()
        request = json.loads(line.strip())
        response = await self.handle_request(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
```

**수정 시**: 통신 방식 변경 시 이 블록 교체

---

## 🚀 사용 방법

### MCP 서버로 사용 (Claude Code에서 자동)

`.mcp.json`에 등록되어 있으므로, Claude Code가 자동으로 시작합니다.

### 직접 Python 스크립트에서 사용

```python
# 직접 API 호출
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=4096,
    messages=[{"role": "user", "content": "FastAPI 라우터 만들어줘"}]
)

print(response.content[0].text)
```

---

## 🐛 트러블슈팅

### 문제 1: `ANTHROPIC_API_KEY not found`

**원인**: 환경 변수가 설정되지 않음

**해결**:
```bash
# .env 파일 확인
cat .env | grep ANTHROPIC_API_KEY

# 없으면 추가
echo "ANTHROPIC_API_KEY=sk-ant-api..." >> .env
```

---

### 문제 2: `ModuleNotFoundError: No module named 'anthropic'`

**원인**: anthropic 패키지 미설치

**해결**:
```bash
pip install anthropic python-dotenv
```

---

### 문제 3: MCP 서버가 시작되지 않음

**원인**: Python 경로 문제

**해결**:
```bash
# 현재 디렉토리에서 직접 실행
python -m mcp_servers.claude_haiku_server

# 또는 절대 경로로
cd /Users/oypnus/Project/rag-enterprise
python -m mcp_servers.claude_haiku_server
```

---

## 📊 성능 및 비용

| 항목 | 값 |
|------|-----|
| 모델 | claude-haiku-4-5-20251001 |
| 입력 토큰 비용 | $0.25 / 1M tokens |
| 출력 토큰 비용 | $1.25 / 1M tokens |
| 최대 컨텍스트 | 200K tokens |
| 예상 응답 속도 | 1-3초 |

**비용 예시**:
- 1000자 프롬프트 (약 250 tokens) + 500자 응답 (약 125 tokens) = $0.0002 (0.02원)
- 하루 100번 호출 = 약 2원

---

## 🎯 다음 단계

1. ✅ **Haiku MCP 서버 구현 완료**
2. ⏭️ **자동 Tier 라우팅 추가** (선택 사항)
   - 복잡도 자동 분석
   - 간단한 질문 → Haiku
   - 복잡한 질문 → Sonnet 4.5
3. ⏭️ **CLAUDE.md 업데이트**
   - Haiku 활용 전략 추가
   - 아키텍처 다이어그램 업데이트

---

*Last Updated: 2025-01-16*
*Version: 1.0*
