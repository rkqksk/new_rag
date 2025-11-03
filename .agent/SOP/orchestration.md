# SOP: Multi-Agent Orchestration

## Purpose
여러 agent를 조정하여 end-to-end RAG 워크플로우 실행

## Scope
- **Workflow**: Crawling → Embedding → Indexing → Search → QA
- **Agents**: 14 specialized agents (crawling, embedding, search, qa, etc.)
- **Coordination**: Sequential + parallel execution

## Orchestration Patterns

### Pattern 1: Sequential Workflow
```
Crawl → Embed → Index → Ready for Search
```

**Use Case**: 신규 데이터 초기 로딩

**Execution**:
```bash
# Step 1: Crawl products
python3 agents/crawling_agent.py --site "청진코리아"

# Step 2: Generate embeddings (wait for crawl completion)
python3 agents/embedding_agent.py --input data/products/crawled/

# Step 3: Index to Qdrant (wait for embedding completion)
python3 agents/vector_db_loader_agent.py --embeddings data/products/embeddings/

# Step 4: Verify search works
python3 agents/search_agent.py --query "50ml PET 보틀"
```

### Pattern 2: Parallel Workflow
```
     ┌──> Embed Batch 1 ──┐
Crawl┼──> Embed Batch 2 ──┼──> Index to Qdrant
     └──> Embed Batch 3 ──┘
```

**Use Case**: 대량 데이터 고속 처리

**Execution**:
```python
import asyncio
from agents.embedding_agent import EmbeddingAgent

async def parallel_embedding():
    """병렬 임베딩 생성"""

    # Split products into batches
    batches = [
        "data/products/crawled/Bottle/",
        "data/products/crawled/Jar/",
        "data/products/crawled/Cap/"
    ]

    # Run embedding agents in parallel
    tasks = [
        EmbeddingAgent().generate_embeddings(batch)
        for batch in batches
    ]

    results = await asyncio.gather(*tasks)
    return results

# Execute
results = asyncio.run(parallel_embedding())
```

### Pattern 3: Event-Driven Workflow
```
Event: New Products Crawled
  → Trigger: Embedding Agent
  → Trigger: Vector DB Loader
  → Trigger: Search Index Update
```

**Use Case**: 실시간 데이터 업데이트

**Implementation** (향후):
```python
# Event-driven orchestration (future)
class AgentOrchestrator:
    async def on_crawl_complete(self, event):
        """크롤링 완료 이벤트 핸들러"""

        # Auto-trigger embedding
        embedding_result = await self.trigger_agent(
            "embedding_agent",
            input=event.output_path
        )

        # Auto-trigger indexing
        await self.trigger_agent(
            "vector_db_loader_agent",
            input=embedding_result.output_path
        )
```

## Agent Coordination Matrix

| Workflow Stage | Primary Agent | Dependencies | Output |
|----------------|---------------|--------------|--------|
| 1. Crawl | crawling_agent.py | None | JSON products |
| 2. Parse | file_parser_agent.py | Crawl complete | Normalized JSON |
| 3. Chunk | chunking_agent.py | Parse complete | Text chunks |
| 4. Embed | embedding_agent.py | Chunk complete | Vectors (768-dim) |
| 5. Index | vector_db_loader_agent.py | Embed complete | Qdrant collection |
| 6. Search | search_agent.py | Index complete | Search results |
| 7. QA | qa_agent.py | Search complete | Answers |

## Orchestration Logic

### `.agent/` System Role
```
┌────────────────────────────────────────┐
│  .agent/ (Orchestration Layer)        │
│  - SOP: 작업 표준 절차 정의            │
│  - Tasks: 워크플로우 조정               │
│  - System: 아키텍처 컨텍스트            │
└────────────────────────────────────────┘
              ↓ (calls)
┌────────────────────────────────────────┐
│  agents/ (Execution Layer)             │
│  - Python scripts: 실제 작업 실행       │
│  - 14 specialized agents               │
└────────────────────────────────────────┘
```

### Example: Orchestrated Workflow
```markdown
User: "새 제품 데이터 크롤링하고 RAG 시스템에 추가해줘"

.agent/ orchestration:
  1. Read SOP/crawling.md → Understand procedure
  2. Read Tasks/crawl_products.md → Get execution details
  3. Execute: python3 agents/crawling_agent.py
  4. Monitor progress (logs, metrics)
  5. Validate output (data quality checks)
  6. Trigger next: Tasks/generate_embeddings.md
  7. Repeat until workflow complete
```

## Parallel Execution Strategy

### When to Parallelize
- ✅ **Independent batches**: Different product categories
- ✅ **I/O-bound tasks**: Network requests, file reads
- ✅ **Large datasets**: >1,000 products

### When to Sequence
- ❌ **Dependencies**: Embedding requires crawl completion
- ❌ **Shared resources**: Single Qdrant instance writes
- ❌ **Rate limits**: API throttling

### Optimal Parallelization
```python
# Good: Parallel embedding of independent categories
async def optimal_parallel():
    tasks = [
        embed_category("Bottle"),   # 1,000 products
        embed_category("Jar"),      # 500 products
        embed_category("Cap")       # 800 products
    ]
    await asyncio.gather(*tasks)  # 2.3x faster than sequential

# Bad: Parallel writes to same Qdrant collection (race conditions)
# Use sequential writes or batch API
```

## Error Recovery

### Checkpoint System
```python
# Save progress at each stage
checkpoint = {
    "workflow_id": "crawl_2025_10_26",
    "stages": {
        "crawl": {"status": "complete", "output": "data/products/crawled/"},
        "embed": {"status": "in_progress", "progress": 0.45},
        "index": {"status": "pending"}
    }
}

# Resume from checkpoint
if checkpoint["stages"]["embed"]["status"] == "in_progress":
    resume_embedding(checkpoint["stages"]["embed"]["progress"])
```

### Retry Logic
```python
# Exponential backoff for transient failures
async def retry_with_backoff(agent_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await agent_func()
        except TransientError:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait_time)
    raise PermanentError("Max retries exceeded")
```

## Monitoring Dashboard

### Real-time Metrics
```
┌────────────────────────────────────────┐
│  RAG Workflow Status                   │
├────────────────────────────────────────┤
│  Crawl:     ✅ Complete (1,245 products)│
│  Embed:     🔄 In Progress (45%)       │
│  Index:     ⏳ Pending                 │
│  Search:    ⏳ Pending                 │
├────────────────────────────────────────┤
│  Overall Progress: 56%                 │
│  ETA: 8 minutes                        │
└────────────────────────────────────────┘
```

### Alert Conditions
- Any stage fails 3+ times → Manual intervention
- Workflow duration > 2x expected → Performance issue
- Data quality < 95% → Review and reprocess

## Best Practices

### 1. Modular Design
- Each agent does ONE thing well
- Clear input/output contracts
- No tight coupling between agents

### 2. Observability
- Log all agent executions
- Track metrics (time, throughput, quality)
- Save intermediate outputs for debugging

### 3. Idempotency
- Re-running same workflow produces same result
- Safe to retry failed stages
- No duplicate data in final output

### 4. Resource Management
- Parallel tasks share resource pool
- Respect rate limits (external APIs)
- Clean up temporary files

---

**Owner**: Platform Engineering Team
**Last Updated**: 2025-10-26
**Version**: 1.0
