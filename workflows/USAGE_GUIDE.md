# RAG Enterprise - Usage Guide

**Complete guide to using slash commands and loading documentation on-demand.**

---

## 🎯 Quick Start

### Slash Commands (가장 추천!)

Claude Code에서 다음과 같이 slash command를 사용하세요:

```bash
/workflow document-processing    # 문서 처리 워크플로우
/workflow rag-query             # RAG 쿼리 워크플로우
/workflow domain-expert         # 도메인 전문가 통합
/workflow vector-search         # 벡터 검색
/workflow web-crawling          # 웹 크롤링

/component skills               # SKILL 시스템 개요
/component plugins              # 플러그인 아키텍처
/component mcp                  # MCP 서버 설정

/guide development              # 개발 가이드
/guide testing                  # 테스트 가이드
/guide session-protocol         # 세션 프로토콜
/guide contributing             # 기여 가이드
```

---

## 📋 Slash Command 상세 설명

### /workflow [workflow-name]

**목적**: 특정 워크플로우 문서를 로드합니다.

**사용법**:
```bash
/workflow document-processing
/workflow rag-query
/workflow domain-expert
/workflow vector-search
/workflow web-crawling
```

**예시**:
```
당신: /workflow document-processing
Claude: ✅ Loaded: Document Processing Workflow
         [문서 처리 워크플로우 전체 내용 로드됨]

당신: How do I process a PDF with OCR?
Claude: [로드된 워크플로우 문서를 참고하여 답변]
```

**실패 시 (Fallback)**:
```
당신: /workflow nonexistent-workflow
Claude: ❌ Workflow 'nonexistent-workflow' not found.

        Available workflows:
        1. document-processing - Document ingestion and processing
        2. rag-query - RAG query and answer generation
        3. domain-expert - Domain expert integration
        4. vector-search - Vector search operations
        5. web-crawling - Web crawling workflows

        Usage: /workflow [workflow-name]
        Example: /workflow document-processing
```

---

### /component [component-type] [optional: component-name]

**목적**: 특정 컴포넌트 문서를 로드합니다.

**사용법**:
```bash
# 컴포넌트 타입 전체
/component skills
/component plugins
/component mcp

# 특정 컴포넌트
/component skills rag-pipeline
/component plugins manufacturing-expert
/component mcp qdrant
```

**예시**:
```
당신: /component skills
Claude: ✅ Loaded: Skills Component Documentation
         [SKILL 시스템 전체 개요 로드됨]

당신: /component plugins manufacturing-expert
Claude: ✅ Loaded: Plugins > Manufacturing Expert
         [Manufacturing expert plugin 상세 정보 로드됨]
```

**실패 시 (Fallback)**:
```
당신: /component unknown
Claude: ❌ Component 'unknown' not found.

        Available component types:
        1. skills - SKILL system and individual SKILLs
           - rag-pipeline
           - manufacturing-expert
           - packaging-expert
           - web-crawler-pipeline

        2. plugins - Plugin architecture and domain plugins
           - manufacturing-expert
           - packaging-expert

        3. mcp - MCP server configurations
           - filesystem
           - qdrant
           - chrome-devtools

        Usage: /component [type] [optional: name]
        Examples:
          /component skills
          /component plugins manufacturing-expert
          /component mcp qdrant
```

---

### /guide [guide-name]

**목적**: 개발 가이드를 로드합니다.

**사용법**:
```bash
/guide development      # 개발 명령어 및 시나리오
/guide testing          # 테스트 전략
/guide session-protocol # 세션 관리 규칙
/guide contributing     # 기여 가이드
```

**예시**:
```
당신: /guide development
Claude: ✅ Loaded: Development Guide
         [개발 가이드 전체 내용 로드됨]

당신: What's the command to run tests?
Claude: [로드된 가이드를 참고하여]
        pytest tests/ -v --cov=src
```

**실패 시 (Fallback)**:
```
당신: /guide unknown
Claude: ❌ Guide 'unknown' not found.

        Available guides:
        1. development - Commands, scenarios, development tools
        2. testing - Testing strategies and pytest guide
        3. session-protocol - Session start/end protocols
        4. contributing - Contribution guidelines and standards

        Usage: /guide [guide-name]
        Example: /guide development
```

---

## 🔄 Auto-Trigger (자동 트리거)

Slash command 없이도 특정 키워드를 언급하면 자동으로 관련 문서를 로드합니다:

### 워크플로우 키워드

| 키워드 | 로드되는 문서 |
|--------|--------------|
| "process document", "upload PDF", "ingest" | document-processing.md |
| "RAG query", "semantic search", "ask question" | rag-query.md |
| "domain expert", "manufacturing", "packaging" | domain-expert.md |
| "vector search", "similarity search" | vector-search.md |
| "crawl", "scrape", "web data" | web-crawling.md |

### 예시

```
당신: How do I process a PDF document?
Claude: [자동으로 workflows/document-processing.md 로드]
        To process a PDF document, use the rag-pipeline SKILL...

당신: I need help with RAG queries
Claude: [자동으로 workflows/rag-query.md 로드]
        For RAG queries, you can use the query command...
```

---

## 💡 사용 시나리오별 가이드

### 시나리오 1: 문서 처리 방법 알고 싶을 때

**Option A: Slash Command (명확함)**
```bash
/workflow document-processing
```

**Option B: 자연어 질문 (편리함)**
```
"How do I process a PDF with OCR enabled?"
```

Claude가 자동으로 `workflows/document-processing.md`를 읽고 답변합니다.

---

### 시나리오 2: SKILL 개발 방법 알고 싶을 때

**Option A: Slash Command**
```bash
/component skills
```

**Option B: 자연어 질문**
```
"How do I create a new SKILL?"
"What's the SKILL architecture?"
```

---

### 시나리오 3: 플러그인 상세 정보 필요할 때

**Option A: Slash Command (정확함)**
```bash
/component plugins manufacturing-expert
```

**Option B: 자연어 질문**
```
"Tell me about the manufacturing expert plugin"
"How does the packaging plugin work?"
```

---

### 시나리오 4: 테스트 실행 방법 알고 싶을 때

**Option A: Slash Command**
```bash
/guide testing
```

**Option B: 자연어 질문**
```
"How do I run tests?"
"What's the testing strategy?"
```

---

## 🎯 Best Practices

### 1. 처음 사용 시
먼저 CLAUDE.md를 읽으세요 (자동 로드됨). Quick reference가 모두 들어있습니다.

### 2. 상세 정보 필요 시
Slash command를 사용하세요:
```bash
/workflow [name]
/component [type]
/guide [name]
```

### 3. 빠른 질문
자연어로 물어보세요. Claude가 자동으로 관련 문서를 찾아 읽습니다:
```
"How do I process documents?"
"What's the RAG query workflow?"
```

### 4. 여러 문서 필요 시
명시적으로 요청하세요:
```
"Show me the document processing workflow and the domain expert integration"
```

Claude가 두 문서를 모두 읽고 통합된 답변을 제공합니다.

---

## 🔍 문서 구조 이해하기

```
프로젝트 루트 (자동 로드)
├── CLAUDE.md          ← Quick reference (항상 로드됨)
├── README.md          ← 프로젝트 개요
└── QUICK_START.md     ← 빠른 시작

workflows/ (필요시 로드)
├── document-processing.md
├── rag-query.md
├── domain-expert.md
├── vector-search.md
└── web-crawling.md

components/ (필요시 로드)
├── skills/
├── plugins/
└── mcp-servers/

guides/ (필요시 로드)
├── development.md
├── testing.md
├── session-protocol.md
└── contributing.md
```

---

## ⚡ Token 효율성

### 기존 방식
- CLAUDE.md 전체 로드: ~3,000 tokens (항상)
- 모든 정보가 한 파일에: 필요 없는 정보도 로드

### 새로운 방식 (Hybrid)
- CLAUDE.md: ~1,300 tokens (필수만)
- 필요한 workflow만 로드: +800-1,500 tokens (필요시)
- **평균 60% token 절약!**

### 예시

**시나리오 1: 간단한 질문**
```
질문: "What's the project about?"
로드: CLAUDE.md만 (1,300 tokens)
절약: 1,700 tokens (57%)
```

**시나리오 2: 문서 처리 질문**
```
질문: "How do I process a PDF?"
로드: CLAUDE.md (1,300) + document-processing.md (800) = 2,100 tokens
절약: 900 tokens (30%)
```

**시나리오 3: 깊이 있는 질문**
```
질문: "Explain the full RAG architecture"
로드: CLAUDE.md + 2-3 workflows = ~3,500 tokens
절약: 적지만, 더 상세한 정보 제공!
```

---

## 🛠️ Troubleshooting

### 문서가 로드되지 않을 때

**증상**: Slash command가 작동하지 않음

**해결**:
1. `.claude/commands/` 디렉토리 확인
2. `workflow.md`, `component.md`, `guide.md` 파일 존재 확인
3. Claude Code 재시작

---

### 자동 트리거가 작동하지 않을 때

**증상**: 키워드를 언급했는데 문서가 로드되지 않음

**해결**:
명시적으로 slash command 사용:
```bash
/workflow document-processing
```

---

### Fallback이 표시될 때

**증상**:
```
❌ Workflow 'xyz' not found.
Available workflows: ...
```

**이유**: 올바른 이유입니다! 존재하지 않는 문서를 요청했습니다.

**해결**: Fallback 메시지의 available list에서 올바른 이름 선택

---

## 📚 추가 자료

- **전체 문서 구조**: `workflows/README.md`
- **컴포넌트 개요**: `components/*/README.md`
- **개발 가이드**: `guides/development.md`

---

**Last Updated**: 2025-11-03
