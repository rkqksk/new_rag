# RAG Enterprise Agents

## 개요

RAG 시스템의 다양한 작업을 담당하는 특화된 에이전트 컬렉션입니다.
각 에이전트는 독립적으로 실행 가능하며, RAG 시스템과 자동으로 연동됩니다.

---

## 에이전트 목록

### 1. 크롤링 에이전트 (crawling_agent.py)
**역할**: 웹 사이트 데이터 수집 및 RAG 시스템 자동 연동

**주요 기능**:
- 다중 사이트 크롤링 관리
- 실시간 진행 상황 모니터링
- 자동 CSV 리포트 생성
- RAG 시스템 자동 연동
- 스케줄링 지원 (정기 실행)

**사용 예시**:
```python
from agents.crawling_agent import CrawlingAgent, CrawlCategory, CrawlConfig
from agents.crawling_agent import ChungjinCrawler

# 에이전트 생성
agent = CrawlingAgent()

# 크롤러 등록
config = CrawlConfig(
    site_name="청진코리아",
    site_url="http://chungjinkorea.com",
    output_dir="data/crawled_products"
)
crawler = ChungjinCrawler(config)
agent.register_crawler("청진코리아", crawler)

# 크롤링 실행
categories = [
    CrawlCategory(name="Bottle", url="...", pages=68),
    CrawlCategory(name="Jar", url="...", pages=4)
]
results = await agent.crawl_site("청진코리아", categories)
```

**API 엔드포인트** (FastAPI 통합):
```
POST /api/agents/crawling/start
POST /api/agents/crawling/schedule
GET  /api/agents/crawling/status
GET  /api/agents/crawling/results
```

---

## 에이전트 아키텍처

### 계층 구조
```
┌─────────────────────────────────────────┐
│        Agent Orchestrator               │  ← 중앙 조정
│  (다중 에이전트 관리 및 워크플로우)     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│        Specialized Agents               │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Crawling │  │Ingestion │  │ Query  ││
│  │  Agent   │  │  Agent   │  │ Agent  ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│         RAG Core System                 │
│  (Qdrant, LLM, Embeddings)             │
└─────────────────────────────────────────┘
```

### 에이전트 간 통신
```python
# 메시지 큐 기반 비동기 통신 (향후 구현)
class AgentMessage(BaseModel):
    from_agent: str
    to_agent: str
    action: str
    payload: Dict[str, Any]

# 예: 크롤링 완료 후 자동 Ingestion
message = AgentMessage(
    from_agent="crawling_agent",
    to_agent="ingestion_agent",
    action="ingest_new_data",
    payload={
        "data_path": "data/crawled_products/",
        "category": "Bottle"
    }
)
```

---

## 에이전트 개발 가이드

### 새 에이전트 생성

#### Step 1: 기본 구조
```python
# agents/my_agent.py

from abc import ABC, abstractmethod
from pydantic import BaseModel

class MyAgentConfig(BaseModel):
    """에이전트 설정"""
    param1: str
    param2: int = 10

class MyAgent:
    """새로운 에이전트"""

    def __init__(self, config: MyAgentConfig):
        self.config = config

    async def execute(self, **kwargs):
        """메인 실행 로직"""
        pass

    async def get_status(self):
        """현재 상태 반환"""
        pass
```

#### Step 2: FastAPI 라우터 추가
```python
# app/api/agent_routes.py

from fastapi import APIRouter
from agents.my_agent import MyAgent, MyAgentConfig

router = APIRouter(prefix="/agents/my-agent")

@router.post("/execute")
async def execute_my_agent(config: MyAgentConfig):
    agent = MyAgent(config)
    result = await agent.execute()
    return result
```

#### Step 3: 문서화
- `agents/README.md`에 에이전트 추가
- 사용 예시 작성
- API 엔드포인트 문서화

---

## 계획된 에이전트 목록

### Phase 1 (현재)
- [x] **Crawling Agent**: 웹 크롤링 및 데이터 수집

### Phase 2 (다음 단계)
- [ ] **Ingestion Agent**: 데이터 정제 및 RAG 시스템 수집
  - 멀티모달 데이터 처리 (텍스트, 이미지, PDF)
  - 자동 임베딩 생성
  - Qdrant 벡터 저장

- [ ] **Query Agent**: 지능형 검색 및 추천
  - 하이브리드 검색 (벡터 + 키워드)
  - Re-ranking
  - 컨텍스트 조립

- [ ] **Report Agent**: 자동 리포트 생성
  - CSV/Excel 리포트
  - 통계 및 인사이트
  - 시각화 (차트, 그래프)

### Phase 3 (향후)
- [ ] **Quality Agent**: 데이터 품질 모니터링
  - 크롤링 데이터 검증
  - 임베딩 품질 체크
  - 이상 감지

- [ ] **Scheduler Agent**: 작업 스케줄링
  - 정기 크롤링
  - 자동 업데이트
  - 리소스 관리

- [ ] **Alert Agent**: 알림 및 모니터링
  - 시스템 상태 모니터링
  - 에러 알림
  - 성능 메트릭

---

## RAG 시스템 통합

### 자동 워크플로우
```
1. Crawling Agent → 데이터 수집
2. Ingestion Agent → 데이터 정제 및 임베딩
3. Query Agent → 검색 서비스 제공
4. Report Agent → 주기적 리포트 생성
```

### 설정 파일 (`config/agents.yaml`)
```yaml
agents:
  crawling:
    enabled: true
    schedule: "0 2 * * *"  # 매일 새벽 2시
    sites:
      - name: "청진코리아"
        categories: ["Bottle", "Jar", "Cap&Pump"]

  ingestion:
    enabled: true
    auto_ingest_on_crawl: true
    embedding_model: "gte-Qwen2-7B-instruct"

  query:
    enabled: true
    default_top_k: 10
    enable_reranking: true

  report:
    enabled: true
    schedule: "0 9 * * 1"  # 매주 월요일 오전 9시
    output_format: ["csv", "excel", "pdf"]
```

---

## 모니터링 및 로깅

### 로그 구조
```
logs/
├── agents/
│   ├── crawling_agent_20251018.log
│   ├── ingestion_agent_20251018.log
│   └── query_agent_20251018.log
├── system/
│   └── agent_orchestrator.log
└── errors/
    └── agent_errors.log
```

### 메트릭 수집
```python
from prometheus_client import Counter, Histogram

# 크롤링 메트릭
crawl_requests = Counter('crawl_requests_total', 'Total crawl requests')
crawl_duration = Histogram('crawl_duration_seconds', 'Crawl duration')

# 사용 예시
with crawl_duration.time():
    result = await crawler.crawl_category(...)
crawl_requests.inc()
```

---

## 보안 및 권한 관리

### 에이전트 권한
```yaml
permissions:
  crawling_agent:
    - read: data/crawled_products
    - write: data/crawled_products
    - execute: web_scraping

  ingestion_agent:
    - read: data/crawled_products
    - write: qdrant://localhost:6333
    - execute: embedding_generation

  query_agent:
    - read: qdrant://localhost:6333
    - execute: llm_query
```

### API 인증
```python
from fastapi import Depends, HTTPException
from app.core.auth import get_current_user

@router.post("/agents/crawling/start")
async def start_crawling(
    config: CrawlConfig,
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission("execute_crawling"):
        raise HTTPException(status_code=403, detail="Permission denied")

    agent = CrawlingAgent()
    result = await agent.crawl_site(...)
    return result
```

---

## 테스트 전략

### 단위 테스트
```python
# tests/agents/test_crawling_agent.py

import pytest
from agents.crawling_agent import CrawlingAgent, CrawlConfig

@pytest.mark.asyncio
async def test_crawling_agent_initialization():
    agent = CrawlingAgent()
    assert agent is not None

@pytest.mark.asyncio
async def test_crawl_category():
    config = CrawlConfig(site_name="test", site_url="http://example.com")
    crawler = MockCrawler(config)
    agent = CrawlingAgent()
    agent.register_crawler("test", crawler)

    result = await agent.crawl_site("test", [mock_category])
    assert result[0].success > 0
```

### 통합 테스트
```python
@pytest.mark.integration
async def test_crawl_and_ingest_workflow():
    """크롤링 → Ingestion 워크플로우 테스트"""
    agent = CrawlingAgent()
    rag_system = MockRAGSystem()

    result = await agent.crawl_and_ingest(
        site_name="test",
        categories=[...],
        rag_system=rag_system
    )

    assert len(result['crawl_results']) > 0
    assert result['rag_ingestion']['status'] == 'success'
```

---

## 문의 및 기여

새로운 에이전트 아이디어나 개선 사항이 있으시면:
1. Issue 생성 또는
2. Pull Request 제출

**작성자**: RAG Enterprise Team
**버전**: 1.0.0
**최종 업데이트**: 2025-10-18
