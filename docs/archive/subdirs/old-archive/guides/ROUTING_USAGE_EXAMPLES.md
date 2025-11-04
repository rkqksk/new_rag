# RAG Enterprise - 자동 라우팅 시스템 사용 가이드

## 개요

이 시스템은 사용자 질의를 자동으로 분석하여:
1. **MCP 도구 선택** - filesystem, qdrant, claude_haiku, ollama 중 필요한 도구 자동 선택
2. **Claude 모델 선택** - Haiku 4.5 (API deposit) vs Sonnet 4.5 (Max 무제한)
3. **Agent 추천** - 작업 유형에 맞는 전문 에이전트 자동 매칭
4. **실행 전략 결정** - MCP만, Claude만, 또는 MCP+Claude 조합

## 시스템 구성

```
app/core/routing/
├── intent_router.py       # MCP 도구 자동 선택
├── llm_router.py          # Claude Haiku/Sonnet 자동 선택
├── integrated_router.py   # 통합 라우팅 + 투명성 메시지
└── __init__.py            # 패키지 export
```

## 사용 예제

### 예제 1: 단순 질문 → Haiku 4.5 (API deposit)

**질의**:
```python
"Python 리스트 만드는 법?"
```

**라우팅 결과**:
```
======================================================================
🎯 자동 라우팅 분석 결과
======================================================================
💡 [Claude Haiku 4.5] 일반 작업 (API deposit 사용)
   사유: 일반 작업 (복잡도: 20/100)

🤖 [Agent] 불필요 (단순 작업)

💬 [실행 전략] claude_only

📊 [복잡도] 20/100
   - 길이: 5/20
   - 기술: 5/25
   - 범위: 5/20
   - 추론: 5/20
   - 생성: 0/15

💰 [비용] DEPOSIT
======================================================================
```

**설명**:
- 복잡도 20/100 → 단순 질문
- Haiku 4.5 사용 → API deposit에서 차감
- Agent 불필요
- MCP 도구 불필요
- 비용 효율적

---

### 예제 2: 파일 작업 → Haiku 4.5 + filesystem MCP

**질의**:
```python
"vault 폴더에 있는 파일들 개수는?"
```

**라우팅 결과**:
```
======================================================================
🎯 자동 라우팅 분석 결과
======================================================================
💡 [Claude Haiku 4.5] 일반 작업 (API deposit 사용)
   사유: 일반 작업 (복잡도: 25/100)

📂 [MCP Tool] filesystem
   의도: file_operation
   신뢰도: 0.95

🤖 [Agent] 불필요 (단순 작업)

📂 [실행 전략] mcp_only

📊 [복잡도] 25/100
   - 길이: 5/20
   - 기술: 5/25
   - 범위: 5/20
   - 추론: 5/20
   - 생성: 5/15

💰 [비용] DEPOSIT
======================================================================
```

**실행 흐름**:
1. Intent Detection: "파일", "폴더", "개수" → FILE_OPERATION
2. MCP 선택: filesystem
3. 실행: `mcp__filesystem__list_directory("/vault")`
4. 응답: "27개 파일이 있습니다"

**설명**:
- MCP filesystem 자동 선택
- 파일 조회는 단순 작업 → Haiku 4.5 (deposit)
- Agent 불필요
- mcp_only 전략 (MCP 결과만으로 충분)

---

### 예제 3: 중급 코드 작성 → Haiku 4.5 + Agents

**질의**:
```python
"FastAPI 인증 라우터 3개 만들어줘"
```

**라우팅 결과**:
```
======================================================================
🎯 자동 라우팅 분석 결과
======================================================================
💡 [Claude Haiku 4.5] 일반 작업 (API deposit 사용)
   사유: 일반 작업 (복잡도: 44/100)

🤖 [Agent] backend-architect, security-engineer

💬 [실행 전략] claude_only

📊 [복잡도] 44/100
   - 길이: 10/20
   - 기술: 10/25
   - 범위: 12/20
   - 추론: 10/20
   - 생성: 12/15

💰 [비용] DEPOSIT
======================================================================
```

**실행 흐름**:
1. Intent Detection: "만들어줘" → 생성 작업
2. 복잡도 분석: 44/100 → 중급 작업
3. Agent 추천: backend-architect (API 작업), security-engineer (인증)
4. Claude Haiku 4.5로 코드 생성

**설명**:
- 중급 코드 작성이지만 복잡도 50 이하 → Haiku 4.5 사용 (비용 효율)
- backend-architect, security-engineer 에이전트 추천
- MCP 도구 불필요 (코드 생성만)
- API deposit에서 차감

---

### 예제 4: 복잡한 검색 → Sonnet 4.5 + Agents + MCP

**질의**:
```python
"RAG 시스템 설계 문서 검색해줘"
```

**라우팅 결과**:
```
======================================================================
🎯 자동 라우팅 분석 결과
======================================================================
🧠 [Claude Sonnet 4.5] 복잡한 작업/검증/시스템 (Max 무제한)
   사유: 복잡한 작업 (복잡도: 70/100)

📂 [MCP Tool] qdrant
   의도: vector_search
   신뢰도: 0.90

🤖 [Agent] deep-research-agent, ai-integrator, system-architect

📂 → 💬 [실행 전략] mcp_then_claude

📊 [복잡도] 70/100
   - 길이: 10/20
   - 기술: 18/25
   - 범위: 12/20
   - 추론: 15/20
   - 생성: 15/15

🎯 [비용] MAX
======================================================================
```

**실행 흐름**:
1. Intent Detection: "검색" → VECTOR_SEARCH
2. MCP 선택: qdrant (벡터 검색)
3. 복잡도 분석: 70/100 → 복잡한 작업 → Sonnet 4.5
4. Agent 추천: deep-research-agent, ai-integrator, system-architect
5. 실행 전략: mcp_then_claude
   - Step 1: qdrant 벡터 검색
   - Step 2: Sonnet 4.5로 결과 분석 및 정리

**설명**:
- 복잡도 70/100 → Sonnet 4.5 (Max 무제한 사용)
- MCP qdrant로 벡터 검색
- 3개 전문 에이전트 추천
- mcp_then_claude 전략 (검색 후 분석)

---

### 예제 5: 시스템 최적화 → Sonnet 4.5 (검증 필수)

**질의**:
```python
"전체 시스템 성능 최적화 및 검증"
```

**라우팅 결과**:
```
======================================================================
🎯 자동 라우팅 분석 결과
======================================================================
🧠 [Claude Sonnet 4.5] 복잡한 작업/검증/시스템 (Max 무제한)
   사유: 시스템 구축/검증/대규모 작업 - Sonnet 필수

📂 [MCP Tool] claude_haiku
   의도: complex_analysis
   신뢰도: 0.85

🤖 [Agent] performance-engineer, system-architect

💬 [실행 전략] mcp_then_claude

📊 [복잡도] 55/100
   - 길이: 10/20
   - 기술: 25/25 (시스템 + 최적화)
   - 범위: 20/20 (전체)
   - 추론: 15/20
   - 생성: 10/15

🎯 [비용] MAX
======================================================================
```

**실행 흐름**:
1. 키워드 감지: "전체 시스템", "검증", "최적화" → Sonnet 필수
2. MCP 선택: claude_haiku (멀티 LLM 분석)
3. Agent 추천: performance-engineer, system-architect
4. Sonnet 4.5 강제 사용 (검증 필수 작업)

**설명**:
- 복잡도 55이지만 **"검증", "시스템", "최적화"** 키워드 → Sonnet 4.5 강제
- Max 무제한 사용 (비용 걱정 없이 고품질 작업)
- claude_haiku MCP로 보조 LLM 활용
- 전문 에이전트 2개 추천

---

## 복잡도 점수 시스템

### 점수 구성 (0-100점)

| 요소 | 배점 | 설명 |
|------|------|------|
| **길이** | 0-20 | 질의 단어 수 (짧을수록 낮음) |
| **기술 복잡도** | 0-25 | 기술 키워드 (간단/중간/복잡/고급) |
| **범위** | 0-20 | 단일/여러/프로젝트 전체 |
| **추론 깊이** | 0-20 | 단순/중간/깊이/전략적 사고 |
| **창의성** | 0-15 | 생성/작성/디자인 요구 여부 |

### 임계값

- **0-30점**: Tier 1 - Haiku 4.5 (deposit)
- **31-50점**: Tier 2 - Haiku 4.5 (deposit, 중급 작업)
- **51-100점**: Tier 3 - Sonnet 4.5 (Max 무제한)

### Sonnet 4.5 강제 사용 조건

복잡도 점수와 무관하게 다음 키워드 감지 시 Sonnet 4.5 강제:
- **검증**: "검증", "verify", "validation"
- **아키텍처**: "아키텍처", "architecture", "설계", "design system"
- **시스템**: "전체 시스템", "entire system", "마이그레이션"
- **성능 최적화**: "성능" + "최적화"
- **대규모 작업**: "대규모", "전체", "리팩토링"
- **다중 파일**: 10개 이상 파일 작업

---

## MCP 도구 자동 선택

### 1. filesystem
**트리거**:
- 파일/폴더 관련: "파일", "file", "폴더", "folder", "directory"
- 작업: "보여줘", "show", "list", "읽어", "read", "찾아", "find"

**신뢰도**: 0.95

**예시**:
```python
"vault 폴더에 있는 파일들 개수는?"
→ filesystem.list_directory("/vault")
```

### 2. qdrant
**트리거**:
- 검색 관련: "검색", "search", "찾아줘", "유사한", "similar"
- 문서: "문서", "document", "관련", "related"

**신뢰도**: 0.90

**예시**:
```python
"RAG 시스템 설계 문서 검색해줘"
→ qdrant.search(query="RAG 시스템 설계", top_k=5)
```

### 3. claude_haiku
**트리거**:
- 복잡한 분석: "분석", "analyze", "왜", "why", "설계", "design"
- 아키텍처: "아키텍처", "architecture", "최적화", "optimize"

**신뢰도**: 0.85

**예시**:
```python
"전체 시스템 성능 분석해줘"
→ claude_haiku.analyze(prompt="시스템 성능 분석")
```

### 4. ollama
**트리거**:
- 단순 질문: "뭐야", "what", "간단히", "짧게", "요약"
- 설명: "설명", "explain", "의미"

**신뢰도**: 0.75

**예시**:
```python
"Python 리스트 컴프리헨션 뭐야?"
→ ollama.query(model="qwen2.5:7b", prompt="...")
```

---

## Agent 자동 추천

### 1. backend-architect
**트리거 키워드**:
- "backend", "api", "fastapi", "라우터", "router"

**예시**:
```python
"FastAPI 인증 라우터 3개 만들어줘"
→ backend-architect 추천
```

### 2. system-architect
**트리거 키워드**:
- "시스템", "아키텍처", "architecture", "system", "설계"

**예시**:
```python
"전체 RAG 시스템 아키텍처 설계"
→ system-architect 추천
```

### 3. performance-engineer
**트리거 키워드**:
- "성능", "performance", "최적화", "optimize"

**예시**:
```python
"전체 시스템 성능 최적화 및 검증"
→ performance-engineer 추천
```

### 4. security-engineer
**트리거 키워드**:
- "보안", "security", "인증", "auth"

**예시**:
```python
"FastAPI 인증 라우터 만들어줘"
→ security-engineer 추천
```

### 5. ai-integrator
**트리거 키워드**:
- "ai", "llm", "rag", "임베딩", "embedding"

**예시**:
```python
"RAG 시스템 설계 문서 검색해줘"
→ ai-integrator 추천
```

### 6. deep-research-agent
**트리거 키워드**:
- "검색", "조사", "research", "찾아"

**예시**:
```python
"RAG 시스템 설계 문서 검색해줘"
→ deep-research-agent 추천
```

### 7. python-expert
**트리거 키워드**:
- "python", "파이썬"

**예시**:
```python
"Python 비동기 함수 작성해줘"
→ python-expert 추천
```

---

## 실행 전략

### 1. mcp_only
**조건**:
- MCP 필요 + 복잡도 ≤30
- 파일 조회 등 단순 작업

**예시**:
```python
"vault 폴더에 있는 파일들 개수는?"
→ filesystem만 실행, LLM 불필요
```

### 2. claude_only
**조건**:
- MCP 불필요
- 코드 생성, 설명, 분석 등

**예시**:
```python
"FastAPI 라우터 3개 만들어줘"
→ Claude만 사용
```

### 3. mcp_then_claude
**조건**:
- MCP 필요 + 복잡도 >30
- 검색 후 분석, 파일 읽고 처리 등

**예시**:
```python
"RAG 시스템 설계 문서 검색해줘"
→ qdrant 검색 → Sonnet 4.5 분석
```

---

## 비용 구조

### Haiku 4.5 (API deposit)
- **용도**: 일반 작업, 중급 작업
- **복잡도**: 0-50점
- **비용**: API deposit에서 차감
- **사용 시기**: 단순 질문, 파일 조회, 중급 코드 작성

### Sonnet 4.5 (Max 무제한)
- **용도**: 복잡한 작업, 검증, 시스템 구축
- **복잡도**: 51-100점 또는 강제 조건
- **비용**: Max 구독 무제한 사용
- **사용 시기**: 아키텍처 설계, 성능 최적화, 검증 필수 작업

**비용 효율 전략**:
- 단순 작업 → Haiku (deposit 절약)
- 복잡한 작업 → Sonnet (Max 활용)
- 50% 이상 deposit 절약 목표

---

## 프로그래밍 방식 사용

### 기본 사용법

```python
from app.core.routing import integrated_router

# 질의 입력
query = "FastAPI 인증 라우터 3개 만들어줘"

# 라우팅 결정
decision = integrated_router.route(query)

# 투명성 메시지 출력
explanation = integrated_router.explain_decision(decision)
print(explanation)

# 결정 내용 확인
print(f"Claude Model: {decision.model_name}")
print(f"Cost Type: {decision.cost_type}")
print(f"MCP Tool: {decision.mcp_tool}")
print(f"Agents: {decision.recommended_agents}")
print(f"Strategy: {decision.execution_strategy}")
```

### 컨텍스트 추가

```python
# 파일 개수, 에러 여부 등 컨텍스트 제공
context = {
    "file_count": 15,
    "error_debugging": True
}

decision = integrated_router.route(query, context)
```

### 결정 내용 접근

```python
# MCP 필요 여부
if decision.requires_mcp:
    mcp_tool = decision.mcp_tool
    intent = decision.mcp_intent
    print(f"MCP: {mcp_tool} (신뢰도: {intent.confidence:.2f})")

# Claude 모델
if decision.claude_model == ClaudeModel.HAIKU_4_5:
    print("Haiku 4.5 사용 (API deposit)")
else:
    print("Sonnet 4.5 사용 (Max 무제한)")

# Agent 추천
if decision.recommended_agents:
    print(f"추천 Agent: {', '.join(decision.recommended_agents)}")

# 복잡도 점수
complexity = decision.model_selection.complexity_score
print(f"복잡도: {complexity.total}/100")
```

---

## 테스트 실행

### 명령어

```bash
# 통합 라우터 테스트
cd /Users/oypnus/Project/rag-enterprise
python3 -m app.core.routing.integrated_router

# Intent 라우터 테스트
python3 -m app.core.routing.intent_router

# Claude 라우터 테스트
python3 -m app.core.routing.llm_router
```

### 예상 출력

```
질의: Python 리스트 만드는 법?
======================================================================
🎯 자동 라우팅 분석 결과
======================================================================
💡 [Claude Haiku 4.5] 일반 작업 (API deposit 사용)
   사유: 일반 작업 (복잡도: 20/100)
...
```

---

## 트러블슈팅

### 1. MCP 서버 연결 실패
**문제**: MCP 도구 선택되었지만 실행 실패

**해결**:
```bash
# MCP 서버 상태 확인
docker-compose ps

# 서비스 재시작
docker-compose restart qdrant filesystem
```

### 2. Agent 추천 안됨
**문제**: 복잡한 작업인데 Agent 추천 없음

**원인**: 복잡도 점수 ≤30

**해결**: 질의에 구체적인 키워드 추가
```python
# Before: "라우터 만들어줘"
# After: "FastAPI 인증 라우터 3개 만들어줘" (backend-architect 추천됨)
```

### 3. Sonnet이 필요한데 Haiku 선택됨
**문제**: 복잡한 작업인데 Haiku 4.5 선택

**해결**: 검증 키워드 명시
```python
# Before: "시스템 성능 개선"
# After: "시스템 성능 최적화 및 검증" (Sonnet 4.5 강제)
```

---

## 설정 커스터마이징

### 복잡도 임계값 조정

`app/core/routing/llm_router.py`:
```python
class ClaudeRouter:
    def __init__(self):
        self.haiku_threshold = 50  # 기본값
        # 더 보수적: self.haiku_threshold = 40
        # 더 공격적: self.haiku_threshold = 60
```

### Agent 매핑 추가

`app/core/routing/integrated_router.py`:
```python
self.agent_mapping = {
    "simple": [],
    "backend": ["backend-architect"],
    "system": ["system-architect"],
    "performance": ["performance-engineer"],
    "security": ["security-engineer"],
    "ai": ["ai-integrator"],
    "research": ["deep-research-agent"],
    "python": ["python-expert"],
    # 커스텀 추가:
    "database": ["database-architect"],
    "frontend": ["frontend-architect"]
}
```

---

## 추가 리소스

- **아키텍처 문서**: `docs/GLOBAL_CLEANUP_PLAN.md`
- **프로젝트 설정**: `CLAUDE.md`
- **소스 코드**: `app/core/routing/`

---

*Last Updated: 2025-10-17*
*Version: 1.0*
