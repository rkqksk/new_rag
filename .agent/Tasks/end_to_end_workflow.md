# Task: End-to-End RAG Workflow Automation

## Objective
새 제품 데이터를 크롤링부터 RAG 시스템 준비까지 완전 자동화

## Workflow Overview
```
Crawl → Parse → Chunk → Embed → Index → Validate → Ready ✅
```

## Agent Chain

### Stage 1: Data Acquisition
**Agent**: `agents/crawling_agent.py`
**Task**: `Tasks/crawl_products.md`
**SOP**: `SOP/crawling.md`

```bash
python3 agents/crawling_agent.py \
  --site "청진코리아" \
  --categories Bottle,Jar,Cap,Pump \
  --output data/products/crawled/
```

**Success Criteria**:
- [ ] >95% products crawled successfully
- [ ] All JSON files valid
- [ ] crawl_report.csv generated

**Output**: `data/products/crawled/**/*.json`

---

### Stage 2: Data Parsing & Normalization
**Agent**: `agents/file_parser_agent.py`
**Dependencies**: Stage 1 complete

```bash
python3 agents/file_parser_agent.py \
  --input data/products/crawled/ \
  --output data/products/parsed/ \
  --normalize
```

**Success Criteria**:
- [ ] All product codes normalized
- [ ] Capacity values standardized (ml)
- [ ] Material names standardized (PET, PETG, PP, PE)

**Output**: `data/products/parsed/**/*.json`

---

### Stage 3: Text Chunking
**Agent**: `agents/chunking_agent.py`
**Dependencies**: Stage 2 complete

```bash
python3 agents/chunking_agent.py \
  --input data/products/parsed/ \
  --chunk-size 512 \
  --overlap 50
```

**Success Criteria**:
- [ ] Chunks < 512 tokens
- [ ] No information loss
- [ ] Chunk boundaries respect semantic units

**Output**: `data/products/chunks/**/*.json`

---

### Stage 4: Embedding Generation
**Agent**: `agents/embedding_agent.py`
**Task**: `Tasks/generate_embeddings.md`
**SOP**: `SOP/embedding.md`
**Dependencies**: Stage 3 complete

```bash
python3 agents/embedding_agent.py \
  --input data/products/chunks/ \
  --output data/products/embeddings/ \
  --model paraphrase-multilingual-mpnet-base-v2 \
  --batch-size 32
```

**Success Criteria**:
- [ ] All chunks embedded (768-dim vectors)
- [ ] No NaN/Inf values
- [ ] Semantic similarity validation passed

**Output**:
- `data/products/embeddings/embeddings.npy`
- `data/products/embeddings/metadata.json`

---

### Stage 5: Vector Indexing
**Agent**: `agents/vector_db_loader_agent.py`
**Dependencies**: Stage 4 complete

```bash
python3 agents/vector_db_loader_agent.py \
  --embeddings data/products/embeddings/ \
  --collection products \
  --qdrant-url http://localhost:6333
```

**Success Criteria**:
- [ ] All vectors indexed to Qdrant
- [ ] Collection metadata updated
- [ ] Index health check passed

**Output**: Qdrant collection `products` ready

---

### Stage 6: Search Validation
**Agent**: `agents/search_agent.py`
**Dependencies**: Stage 5 complete

```bash
# Run test queries
python3 agents/search_agent.py \
  --query "50ml PET 보틀" \
  --top-k 10 \
  --validate

python3 agents/search_agent.py \
  --query "100ml 크림용기 PP" \
  --top-k 10 \
  --validate
```

**Success Criteria**:
- [ ] Search returns relevant results
- [ ] Top-1 accuracy >80%
- [ ] Response time <100ms

---

## Orchestration Script

### Sequential Execution (Safe)
```bash
#!/bin/bash
# File: scripts/run_e2e_workflow.sh

set -e  # Exit on error

echo "=== RAG E2E Workflow ==="

# Stage 1: Crawl
echo "[1/6] Crawling products..."
python3 agents/crawling_agent.py --site "청진코리아" || exit 1

# Stage 2: Parse
echo "[2/6] Parsing & normalizing..."
python3 agents/file_parser_agent.py --input data/products/crawled/ || exit 1

# Stage 3: Chunk
echo "[3/6] Chunking text..."
python3 agents/chunking_agent.py --input data/products/parsed/ || exit 1

# Stage 4: Embed
echo "[4/6] Generating embeddings..."
python3 agents/embedding_agent.py --input data/products/chunks/ || exit 1

# Stage 5: Index
echo "[5/6] Indexing to Qdrant..."
python3 agents/vector_db_loader_agent.py --embeddings data/products/embeddings/ || exit 1

# Stage 6: Validate
echo "[6/6] Validating search..."
python3 agents/search_agent.py --query "50ml PET 보틀" --validate || exit 1

echo "✅ E2E Workflow Complete!"
```

### Parallel Execution (Fast)
```python
#!/usr/bin/env python3
# File: scripts/run_e2e_workflow_parallel.py

import asyncio
from agents.embedding_agent import EmbeddingAgent
from agents.vector_db_loader_agent import VectorDBLoader

async def parallel_workflow():
    """병렬 처리로 워크플로우 실행"""

    # Stage 1-3: Sequential (dependencies)
    await run_crawl()
    await run_parse()
    await run_chunk()

    # Stage 4: Parallel embedding (by category)
    categories = ["Bottle", "Jar", "Cap", "Pump"]
    embed_tasks = [
        EmbeddingAgent().generate_embeddings(f"data/products/chunks/{cat}/")
        for cat in categories
    ]
    embed_results = await asyncio.gather(*embed_tasks)

    # Stage 5: Sequential indexing (shared Qdrant)
    for result in embed_results:
        await VectorDBLoader().load_embeddings(result.output_path)

    # Stage 6: Validate
    await run_validation()

if __name__ == "__main__":
    asyncio.run(parallel_workflow())
```

## Monitoring

### Real-time Progress
```python
# Progress tracking
import time

class WorkflowMonitor:
    def __init__(self):
        self.stages = {
            "crawl": {"status": "pending", "start": None, "end": None},
            "parse": {"status": "pending", "start": None, "end": None},
            "chunk": {"status": "pending", "start": None, "end": None},
            "embed": {"status": "pending", "start": None, "end": None},
            "index": {"status": "pending", "start": None, "end": None},
            "validate": {"status": "pending", "start": None, "end": None}
        }

    def start_stage(self, stage_name):
        self.stages[stage_name]["status"] = "running"
        self.stages[stage_name]["start"] = time.time()

    def complete_stage(self, stage_name):
        self.stages[stage_name]["status"] = "complete"
        self.stages[stage_name]["end"] = time.time()

    def get_progress(self):
        completed = sum(1 for s in self.stages.values() if s["status"] == "complete")
        return completed / len(self.stages) * 100

    def get_eta(self):
        # Estimate based on completed stages
        pass
```

### Dashboard Output
```
┌──────────────────────────────────────────────────────┐
│  RAG E2E Workflow Status                             │
├──────────────────────────────────────────────────────┤
│  [✅] 1. Crawl       (2m 15s) - 1,245 products       │
│  [✅] 2. Parse       (0m 45s) - 1,245 normalized     │
│  [✅] 3. Chunk       (1m 02s) - 3,680 chunks         │
│  [🔄] 4. Embed       (3m 20s) - 68% complete         │
│  [⏳] 5. Index       - Pending                       │
│  [⏳] 6. Validate    - Pending                       │
├──────────────────────────────────────────────────────┤
│  Overall Progress: 56%                               │
│  Elapsed: 7m 22s | ETA: 5m 18s                       │
└──────────────────────────────────────────────────────┘
```

## Error Recovery

### Checkpoint & Resume
```python
# Save checkpoint after each stage
checkpoint = {
    "workflow_id": "e2e_2025_10_26_10_30",
    "completed_stages": ["crawl", "parse", "chunk"],
    "current_stage": "embed",
    "stage_progress": 0.68,
    "outputs": {
        "crawl": "data/products/crawled/",
        "parse": "data/products/parsed/",
        "chunk": "data/products/chunks/"
    }
}

# Resume from checkpoint
def resume_workflow(checkpoint_path):
    checkpoint = load_checkpoint(checkpoint_path)

    # Skip completed stages
    if "embed" not in checkpoint["completed_stages"]:
        run_embedding(resume_from=checkpoint["stage_progress"])

    # Continue workflow...
```

## Performance Targets

| Stage | Target Time | Parallelizable |
|-------|-------------|----------------|
| Crawl | 2-3 min | ❌ (sequential) |
| Parse | <1 min | ✅ (by category) |
| Chunk | <2 min | ✅ (by category) |
| Embed | 3-5 min | ✅ (by category) |
| Index | 1-2 min | ❌ (shared DB) |
| Validate | <30 sec | ✅ (parallel queries) |
| **Total** | **9-13 min** | **Optimized: 6-8 min** |

## Success Metrics

### Data Quality
- Product coverage: >99%
- Specification completeness: >95%
- Embedding quality: Semantic similarity >0.7 for same-category

### Performance
- End-to-end time: <15 minutes
- Search accuracy: >90% (top-3 relevant)
- System uptime: >99.5%

---

**Task Type**: Workflow Automation
**Priority**: High
**Frequency**: Weekly (or on-demand)
**Last Run**: 2025-10-26
**Owner**: Platform Team
