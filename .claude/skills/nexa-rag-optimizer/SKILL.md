---
name: nexa-rag-optimizer
description: Optimize RAG queries and improve search relevance using NexaAI SDK
license: MIT
metadata:
  version: "1.0.0"
  domain: "rag"
  triggers:
    - "optimize query"
    - "analyze search"
    - "tune routing"
    - "benchmark model"
---

# NexaAI RAG Optimizer Skill

**Purpose**: Optimize RAG queries and improve search relevance using NexaAI SDK

## 🎯 Overview

Analyzes query complexity, routes to optimal model (NexaAI/Ollama), and enhances search results with entity extraction and re-ranking.

## 📋 When to Use

- Poor search results quality
- Need performance tuning
- Query pattern analysis
- Model routing optimization

## 🔧 Commands

### `analyze <query>`
Analyze query complexity and suggest optimizations.

**Output**: Complexity score, routing decision, entities, suggestions

### `optimize-search <query>`
Execute optimized search with enhanced parameters.

**Actions**: Analyze → Extract entities → Build filters → Search → Re-rank

### `tune-routing`
Analyze recent queries and suggest router threshold adjustments.

### `benchmark <query>`
Benchmark query performance across both engines.

## 🔄 Quick Workflow

```
User Query → Analyze Complexity → Extract Entities → Route to Engine → Enhanced Search → Optimized Results
```

## 📚 Progressive Disclosure

**For detailed information, see:**
- `references/detailed_workflow.md` - Complete workflow documentation
- `references/complexity_algorithm.md` - Complexity scoring details
- `references/routing_strategy.md` - Routing decision logic
- `examples/query_analysis.md` - Real-world examples

## 🚀 Quick Example

```bash
# Simple query (routes to NexaAI)
analyze "50ml 용기"
→ Score: 0.2, Engine: NexaAI, Model: Qwen3-1.7B

# Complex query (routes to Ollama)
analyze "100ml PET와 PP의 화학적 구조 비교"
→ Score: 0.85, Engine: Ollama, Model: qwen2.5:7b-instruct
```

---

**Version**: 1.0.0 | **Updated**: 2025-11-08
