# Global Configuration Cleanup Plan

## 목표
`~/.claude` 전역 설정을 최소화하고 프로젝트별 설정으로 이관

## 현재 상태 분석

### 1. 중복/불필요한 SuperClaude 파일들
다음 파일들은 프로젝트 내에서 이미 구현했거나 불필요:

#### 🔄 **중복 파일 (삭제 대상)**:
- `LLM_ROUTER_AUTO.md` (15k) - 프로젝트에 `llm_router.py`로 구현됨
- `LLM_ROUTER_LOCAL.md` (15k) - Local Ollama 사용 안함 (사용자 확인)
- `MCP_AUTO_TRIGGER.md` (11k) - 프로젝트에 `intent_router.py`로 구현됨
- `MCP_INTENT_ROUTER.md` (13k) - 프로젝트에 `intent_router.py`로 구현됨
- `MCP_HEALTH_MONITOR.md` (18k) - 프로젝트별 health check로 이관 가능

**예상 절감**: ~72k 불필요한 글로벌 설정

#### ❌ **RAG 프로젝트 불필요 파일 (삭제 대상)**:
- `BUSINESS_PANEL_EXAMPLES.md` (8.3k) - 비즈니스 패널, RAG 프로젝트 무관
- `BUSINESS_SYMBOLS.md` (7.7k) - 비즈니스 심볼, RAG 프로젝트 무관

**예상 절감**: ~16k

#### ✅ **유지해야 할 파일**:
- `claude.md` - 전역 시스템 프롬프트 (최소화 필요)
- `PRINCIPLES.md` - 코딩 원칙
- `RULES.md` - 행동 규칙
- `FLAGS.md` - 플래그 시스템
- `MODE_*.md` - 동작 모드들 (7개 파일)
- `RESEARCH_CONFIG.md` - 리서치 설정

### 2. SuperClaude 메타데이터 수정

#### `.superclaude-metadata.json` 문제점:
```json
{
  "components": {
    "agents": {
      "agents_count": 16,  // ❌ 실제는 7개로 정리됨
      ...
    },
    "mcp": {
      "installed_servers": ["context7"],  // ❌ 전역 MCP 서버
      ...
    }
  }
}
```

**수정 사항**:
1. `agents_count`: 16 → 7
2. `installed_servers`: context7 제거 (프로젝트 레벨로 이관)

### 3. 전역 MCP 서버 제거

#### 현재 전역 MCP 상태:
- SuperClaude metadata에 "context7" 전역 설치됨
- `settings.local.json`의 `enabledMcpjsonServers: []` (이미 비움 ✅)

#### 조치사항:
- `.superclaude-metadata.json`에서 context7 제거
- 프로젝트 `.mcp.json`에서만 MCP 서버 관리

### 4. claude.md 최소화

#### 현재 claude.md 구조:
```markdown
# claude.md (전역용)

## 역할
...

## 출력 규칙
...

# SuperClaude Framework Components
@BUSINESS_PANEL_EXAMPLES.md  ❌ 삭제할 파일 참조
@BUSINESS_SYMBOLS.md          ❌ 삭제할 파일 참조
...
@LLM_ROUTER_AUTO.md           ❌ 삭제할 파일 참조
@LLM_ROUTER_LOCAL.md          ❌ 삭제할 파일 참조
@MCP_AUTO_TRIGGER.md          ❌ 삭제할 파일 참조
@MCP_INTENT_ROUTER.md         ❌ 삭제할 파일 참조
@MCP_HEALTH_MONITOR.md        ❌ 삭제할 파일 참조
```

**수정 계획**:
1. 삭제할 파일 참조 제거
2. RAG 프로젝트 관련 설정은 프로젝트 CLAUDE.md에만 유지
3. 전역 claude.md는 일반적인 원칙만 유지

## 실행 계획

### Step 1: 백업 생성
```bash
cd ~/.claude
mkdir -p .backup/$(date +%Y%m%d_%H%M%S)
cp -r *.md .superclaude-metadata.json settings*.json .backup/$(date +%Y%m%d_%H%M%S)/
```

### Step 2: 중복 파일 삭제
```bash
cd ~/.claude
rm -f LLM_ROUTER_AUTO.md
rm -f LLM_ROUTER_LOCAL.md
rm -f MCP_AUTO_TRIGGER.md
rm -f MCP_INTENT_ROUTER.md
rm -f MCP_HEALTH_MONITOR.md
rm -f BUSINESS_PANEL_EXAMPLES.md
rm -f BUSINESS_SYMBOLS.md
```

### Step 3: claude.md 수정
전역 claude.md에서 삭제할 파일 참조 제거:
- 불필요한 @참조 제거
- 필수 원칙만 유지 (PRINCIPLES, RULES, FLAGS, MODE_*)

### Step 4: SuperClaude 메타데이터 업데이트
```json
{
  "components": {
    "agents": {
      "agents_count": 7,  // 수정
      "agents_list": [  // 실제 7개로 업데이트
        "ai-integrator.md",
        "backend-architect.md",
        "deep-research-agent.md",
        "performance-engineer.md",
        "python-expert.md",
        "security-engineer.md",
        "system-architect.md"
      ]
    },
    "mcp": {
      "installed_servers": []  // context7 제거
    }
  }
}
```

### Step 5: 검증
1. Claude Code 재시작
2. MCP 서버가 프로젝트 `.mcp.json`에서만 로드되는지 확인
3. 전역 설정이 프로젝트 설정과 충돌하지 않는지 확인

## 기대 효과

### 용량 절감:
- **삭제 전**: ~88k 중복/불필요 파일
- **삭제 후**: 필수 파일만 유지
- **절감률**: ~50% 전역 설정 최소화

### 관리 효율성:
- ✅ 프로젝트별 설정 완전 분리
- ✅ MCP 서버 충돌 방지
- ✅ 설정 일관성 향상
- ✅ 유지보수 간소화

### 명확한 책임 분리:
```
전역 (~/.claude):
  - 일반적인 코딩 원칙
  - 동작 모드 정의
  - 플래그 시스템

프로젝트 (~/project/rag-enterprise):
  - RAG 시스템 아키텍처
  - MCP 서버 설정
  - LLM 라우팅 로직
  - Agent 설정
  - 프로젝트별 규칙
```

## 실행 시점
사용자 승인 후 즉시 실행 가능

---
*Generated: 2025-10-17*
*Status: Ready for execution*
