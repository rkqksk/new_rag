# NexaAI RAG Optimizer Skill

**Purpose**: Optimize RAG queries and improve search relevance using NexaAI SDK

**Version**: 1.0.0

---

## 🎯 What This Skill Does

This skill helps optimize RAG (Retrieval-Augmented Generation) queries by:

1. **Query Analysis**: Analyze user queries for complexity and intent
2. **Search Optimization**: Suggest better search strategies
3. **Result Enhancement**: Improve result ranking and relevance
4. **Performance Tuning**: Optimize model routing and caching

---

## 📋 When to Use This Skill

Use this skill when:
- User asks about search results quality
- Query returns poor results
- Need to improve search performance
- Want to analyze query patterns
- Need to tune model routing thresholds

---

## 🔧 Available Commands

### `analyze <query>`

Analyze a query and suggest optimizations.

**Example**:
```
/skill nexa-rag-optimizer analyze "50ml PET 용기"
```

**Output**:
- Query complexity score
- Suggested model (NexaAI vs Ollama)
- Entity extraction results
- Optimization suggestions

---

### `optimize-search <query>`

Run an optimized search with enhanced parameters.

**Example**:
```
/skill nexa-rag-optimizer optimize-search "투명 용기"
```

**Actions**:
1. Analyze query complexity
2. Extract entities (capacity, material, etc.)
3. Build optimized filters
4. Execute enhanced search
5. Re-rank results

---

### `tune-routing`

Analyze recent queries and suggest router threshold adjustments.

**Example**:
```
/skill nexa-rag-optimizer tune-routing
```

**Actions**:
1. Fetch recent query statistics
2. Analyze routing decisions
3. Calculate optimal thresholds
4. Suggest configuration changes

---

### `benchmark <query>`

Benchmark query performance across both engines.

**Example**:
```
/skill nexa-rag-optimizer benchmark "100ml PP 용기"
```

**Output**:
- NexaAI response time & quality
- Ollama response time & quality
- Recommendation for this query type

---

## 🔄 Workflow

### Query Optimization Workflow

```
User Query
    ↓
[Analyze Complexity]
    ↓
[Extract Entities] → capacity, material, neck, moq, etc.
    ↓
[Build Filters] → Qdrant metadata filters
    ↓
[Route to Engine] → NexaAI (fast) or Ollama (quality)
    ↓
[Execute Search]
    ↓
[Re-rank Results] → semantic + entity matching
    ↓
Optimized Results
```

---

## 💡 Examples

### Example 1: Simple Query Analysis

**Input**:
```
User: "50ml 용기"
```

**Skill Action**:
```python
# Analyze query
complexity = analyze_complexity("50ml 용기")
# → score: 0.2 (simple)
# → entities: ['capacity']
# → recommendation: NexaAI Qwen3-1.7B
```

**Output**:
```
✓ Query Analysis:
  • Complexity: 0.20 (Simple)
  • Entities: capacity (50ml)
  • Recommended Engine: NexaAI
  • Recommended Model: Qwen3-1.7B
  • Expected Response Time: < 500ms

Optimization Suggestions:
  1. Add material filter for better precision
  2. Consider related queries: "50ml PET", "50ml PP"
```

### Example 2: Complex Query Optimization

**Input**:
```
User: "100ml 투명 PET 용기와 PP 용기의 차이점 비교"
```

**Skill Action**:
```python
# Analyze
complexity = analyze_complexity(query)
# → score: 0.85 (complex - reasoning required)
# → entities: ['capacity', 'material', 'material']
# → recommendation: Ollama qwen2.5:7b

# Enhanced search
filters = {
    "capacity": "100ml",
    "material": ["PET", "PP"]
}
results = search_with_filters(query, filters)
```

**Output**:
```
✓ Query Analysis:
  • Complexity: 0.85 (Complex - Reasoning)
  • Entities: capacity (100ml), materials (PET, PP)
  • Recommended Engine: Ollama
  • Recommended Model: qwen2.5:7b-instruct
  • Expected Response Time: ~2s

✓ Optimization Applied:
  • Material filter: PET, PP
  • Capacity filter: 100ml
  • Re-ranking: semantic + entity boost
  • Results found: 12 products

Top Results:
  1. 100ml PET 투명 용기 (score: 0.92)
  2. 100ml PP 반투명 용기 (score: 0.89)
  3. 100ml PET 크리스탈 용기 (score: 0.87)
```

### Example 3: Router Tuning

**Input**:
```
/skill nexa-rag-optimizer tune-routing
```

**Skill Action**:
```python
# Analyze last 100 queries
stats = analyze_routing_stats(limit=100)

# Calculate optimal thresholds
optimal = calculate_optimal_thresholds(stats)
```

**Output**:
```
✓ Routing Analysis (last 100 queries):

  Current Configuration:
    • Simple threshold: 0.30
    • Complex threshold: 0.70

  Query Distribution:
    • Simple (< 0.3): 45 queries → NexaAI
    • Medium (0.3-0.7): 30 queries → NexaAI
    • Complex (> 0.7): 25 queries → Ollama

  Performance:
    • Avg NexaAI time: 420ms
    • Avg Ollama time: 1.8s
    • Error rate: 0.5%

  Recommendations:
    ✓ Current thresholds are optimal
    • 75% of queries use fast model (good)
    • 25% use quality model (appropriate)
    • No threshold adjustment needed
```

---

## 🚀 Implementation

This skill uses the following components:

```python
# src/skills/nexa_rag_optimizer.py

from src.core.model_router import ModelRouter
from src.services.unified_llm_service import get_unified_llm
from src.core.query_parser import QueryParser
from src.core.search_engine import SearchEngine

class NexaRAGOptimizer:
    """RAG Optimization Skill"""

    def __init__(self):
        self.router = ModelRouter()
        self.llm = get_unified_llm()
        self.parser = QueryParser()
        self.search = SearchEngine()

    def analyze(self, query: str) -> dict:
        """Analyze query and return optimization suggestions"""
        complexity = self.router.analyze_complexity(query)
        routing = self.router.route(query)
        entities = self.parser.extract_entities(query)

        return {
            "complexity": complexity,
            "routing": routing,
            "entities": entities,
            "suggestions": self._generate_suggestions(query, entities)
        }

    def optimize_search(self, query: str, top_k: int = 10) -> dict:
        """Execute optimized search"""
        # Analyze
        analysis = self.analyze(query)

        # Build filters
        filters = self.parser.build_filters(analysis['entities'])

        # Search
        results = self.search.search(
            query=query,
            top_k=top_k,
            filters=filters
        )

        # Re-rank with entity boosting
        results = self._rerank_with_entities(results, analysis['entities'])

        return {
            "query": query,
            "analysis": analysis,
            "results": results,
            "optimization_applied": True
        }

    def tune_routing(self, limit: int = 100) -> dict:
        """Analyze routing stats and suggest tuning"""
        # Get recent queries
        stats = self.llm.get_stats()

        # Analyze distribution
        distribution = self._analyze_distribution(stats)

        # Calculate optimal thresholds
        optimal = self._calculate_optimal_thresholds(distribution)

        return {
            "current": {
                "simple_threshold": self.router.simple_threshold,
                "complex_threshold": self.router.complex_threshold
            },
            "stats": stats,
            "distribution": distribution,
            "recommended": optimal
        }
```

---

## 📊 Metrics

The skill tracks:
- Query complexity distribution
- Entity extraction accuracy
- Search relevance scores
- Response times by engine
- Cache hit rates

---

## 🎓 Learning

The skill learns from:
- User feedback on results
- Click-through rates
- Query reformulations
- Successful vs failed searches

---

**Skill Owner**: RAG Enterprise Team
**Last Updated**: 2025-11-07
**Version**: 1.0.0
