# Multi-Agent System (v6.0.0)

## Overview

Orchestrated multi-agent system for complex RAG tasks with specialized agents for routing, search, reasoning, synthesis, and validation.

**Status**: ✅ Implemented and Tested
**Version**: v6.0.0
**Date**: 2025-11-09

---

## Features

### Specialized Agents

- ✅ **Router Agent**: Query classification and complexity assessment
- ✅ **Search Agent**: Adaptive search strategy (dense/hybrid/re-ranked)
- ✅ **Reasoning Agent**: Chain-of-thought reasoning for complex queries
- ✅ **Synthesis Agent**: Multi-source information synthesis
- ✅ **Validation Agent**: Answer quality assurance

### Capabilities

- ✅ **Intent Detection**: Comparison, recommendation, explanation, search, general
- ✅ **Complexity Assessment**: Simple, medium, complex
- ✅ **Adaptive Search**: Route to appropriate search strategy based on complexity
- ✅ **Chain-of-Thought**: Multi-step reasoning with intermediate conclusions
- ✅ **Confidence Scoring**: Calculate answer confidence based on results and reasoning
- ✅ **Quality Validation**: Check completeness, consistency, relevance

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Query                              │
│  "50ml PET 용기와 100ml PP 용기의 차이점은?"                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               Multi-Agent Orchestrator                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Step 1: Router Agent                                   │ │
│  │  • Classify intent: "comparison"                       │ │
│  │  • Assess complexity: "complex"                        │ │
│  │  • Determine workflow: hybrid + reasoning              │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Step 2: Search Agent                                   │ │
│  │  • Execute dense search (Qdrant)                       │ │
│  │  • Execute hybrid search (BM25 + RRF)                  │ │
│  │  • Apply cross-encoder re-ranking                      │ │
│  │  • Return top 100 results                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Step 3: Reasoning Agent (Complex Only)                 │ │
│  │  • Analyze result distribution                         │ │
│  │  • Extract key attributes (materials, capacities)      │ │
│  │  • Identify patterns and relationships                 │ │
│  │  • Draw intermediate conclusions                       │ │
│  │  • Build reasoning chain                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Step 4: Synthesis Agent                                │ │
│  │  • Select synthesis strategy (comparison/recommend)    │ │
│  │  • Combine search results + reasoning                  │ │
│  │  • Generate coherent answer                            │ │
│  │  • Calculate confidence score                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Step 5: Validation Agent                               │ │
│  │  • Check answer completeness                           │ │
│  │  • Verify result consistency                           │ │
│  │  • Validate confidence threshold                       │ │
│  │  • Check query-answer relevance                        │ │
│  │  • Flag validation issues                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Final Response                            │
│  • Answer: Synthesized comparison                           │
│  • Products: Top-ranked results                             │
│  • Confidence: 0.88                                         │
│  • Validated: true                                          │
│  • Agent Trace: Router → Search → Reasoning → Synthesis     │
│  • Reasoning Steps: [step1, step2, step3...]                │
└─────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Multi-Agent Query

**URL**: `POST /api/v1/agents/query`

**Request Body**:
```json
{
  "query": "50ml PET 용기와 100ml PP 용기의 차이점은?",
  "session_id": "user-session-123",
  "collections": ["chungjinkorea", "onehago"],
  "materials": ["PET", "PP"],
  "enable_reasoning": true,
  "enable_validation": true
}
```

**Response**:
```json
{
  "status": "success",
  "query": "50ml PET 용기와 100ml PP 용기의 차이점은?",
  "answer": "'50ml PET 용기와 100ml PP 용기의 차이점은?' 검색 결과, 45개의 제품을 발견했습니다.\n\n상위 제품 비교:\n1. 50ml PET 용기 - 재질: PET, 용량: 50ml\n2. 100ml PP 용기 - 재질: PP, 용량: 100ml\n3. 50ml PET 병 - 재질: PET, 용량: 50ml",
  "products": [
    {
      "product_id": "001",
      "product_name": "50ml PET 용기",
      "material": "PET",
      "capacity": "50ml",
      "score": 0.92
    }
  ],
  "confidence": 0.88,
  "validated": true,
  "validation_issues": [],
  "agent_trace": [
    "RouterAgent:route",
    "SearchAgent:dense_search",
    "SearchAgent:hybrid_search",
    "ReasoningAgent:chain_of_thought",
    "SynthesisAgent:synthesize",
    "ValidationAgent:validate"
  ],
  "reasoning_steps": [
    "Found 45 relevant products",
    "Key materials: PET, PP, Glass",
    "Capacity range: 50ml, 100ml, 150ml"
  ],
  "intermediate_conclusions": [
    "Top 5 products have high relevance (scores > 0.92)",
    "Comparison query detected - multiple products needed for evaluation"
  ],
  "metadata": {
    "intent": "comparison",
    "complexity": "complex",
    "total_results": 45
  },
  "performance": {
    "total_time_ms": 1234.56,
    "agents_invoked": 6,
    "reasoning_steps": 3
  }
}
```

### Get Agent Trace

**URL**: `GET /api/v1/agents/trace/{session_id}`

**Response**:
```json
{
  "session_id": "user-session-123",
  "query": "50ml PET 용기와 100ml PP 용기의 차이점은?",
  "agent_trace": [
    "RouterAgent:route",
    "SearchAgent:dense_search",
    "SearchAgent:hybrid_search",
    "ReasoningAgent:chain_of_thought",
    "SynthesisAgent:synthesize",
    "ValidationAgent:validate"
  ],
  "reasoning_steps": [
    "Found 45 relevant products",
    "Key materials: PET, PP",
    "Capacity range: 50ml, 100ml"
  ],
  "execution_time_ms": 1234.56,
  "timestamp": "2025-11-09 13:45:23"
}
```

### Health Check

**URL**: `GET /api/v1/agents/health`

**Response**:
```json
{
  "status": "healthy",
  "agents": {
    "router": "RouterAgent",
    "search": "SearchAgent",
    "reasoning": "ReasoningAgent",
    "synthesis": "SynthesisAgent",
    "validation": "ValidationAgent"
  },
  "capabilities": [
    "Intent classification",
    "Complexity assessment",
    "Dense/Hybrid search routing",
    "Chain-of-thought reasoning",
    "Multi-source synthesis",
    "Answer validation"
  ],
  "execution_traces_stored": 42,
  "endpoint": "/api/v1/agents/query"
}
```

### Configuration

**URL**: `GET /api/v1/agents/config`

**Response**:
```json
{
  "agents": [
    {
      "name": "RouterAgent",
      "role": "Query classification and routing",
      "features": ["Intent detection", "Complexity assessment"]
    },
    {
      "name": "SearchAgent",
      "role": "Execute search operations",
      "features": ["Dense search", "Hybrid search", "Adaptive strategy"]
    },
    {
      "name": "ReasoningAgent",
      "role": "Chain-of-thought reasoning",
      "features": ["Multi-step analysis", "Pattern identification", "Conclusions"]
    },
    {
      "name": "SynthesisAgent",
      "role": "Answer generation",
      "features": ["Intent-based synthesis", "Comparison/Recommendation/Explanation", "Confidence scoring"]
    },
    {
      "name": "ValidationAgent",
      "role": "Quality assurance",
      "features": ["Completeness check", "Consistency check", "Confidence threshold", "Relevance check"]
    }
  ],
  "workflow": [
    "1. Router → Classify query",
    "2. Search → Execute search",
    "3. Reasoning → Analyze results (if complex)",
    "4. Synthesis → Generate answer",
    "5. Validation → Validate quality"
  ],
  "complexity_levels": {
    "simple": "Direct search (dense-only)",
    "medium": "Hybrid search (dense + sparse)",
    "complex": "Hybrid search + re-ranking + reasoning"
  }
}
```

---

## Agent Details

### 1. Router Agent

**Purpose**: Query analysis and workflow routing

**Features**:
- Intent classification: comparison, recommendation, explanation, search, general
- Complexity assessment: simple, medium, complex
- Workflow determination

**Intent Detection**:
- **Comparison**: "비교", "차이", "vs", "compare"
- **Recommendation**: "추천", "recommend", "best", "좋은"
- **Explanation**: "어떻게", "how", "방법", "why", "왜"
- **Search**: "찾아", "search", "find", "있나"
- **General**: Default for other queries

**Complexity Heuristics**:
- **Simple**: < 6 words, no conditions
- **Medium**: 6-10 words OR multi-conditions
- **Complex**: > 10 words AND comparisons/multi-conditions

---

### 2. Search Agent

**Purpose**: Execute search with adaptive strategy

**Strategies by Complexity**:
- **Simple**: Dense vector search only (Qdrant)
- **Medium**: Hybrid search (dense + BM25 + RRF)
- **Complex**: Hybrid search + cross-encoder re-ranking

**Search Flow**:
1. Execute dense search (via RAG skill)
2. If medium/complex: Build BM25 index
3. If medium/complex: Execute hybrid search
4. If complex: Apply cross-encoder re-ranking

---

### 3. Reasoning Agent

**Purpose**: Chain-of-thought reasoning for complex queries

**Activated When**: Complexity = "medium" or "complex"

**Reasoning Steps**:
1. Analyze result distribution (count, scores)
2. Extract key attributes (materials, capacities, etc.)
3. Identify patterns and relationships
4. Draw intermediate conclusions
5. Build reasoning chain

**Output**: Reasoning steps + intermediate conclusions

---

### 4. Synthesis Agent

**Purpose**: Generate coherent answer from results + reasoning

**Synthesis Strategies**:
- **Comparison**: Multi-product comparison table
- **Recommendation**: Top product with details
- **Explanation**: Analysis with reasoning steps
- **General**: Result summary with top products

**Confidence Calculation**:
```python
confidence = (result_count_factor * 0.3) + (top_score * 0.5) + (reasoning_factor * 0.2)
```

Where:
- `result_count_factor`: min(len(results) / 50, 1.0)
- `top_score`: First result's score
- `reasoning_factor`: 1.0 if reasoning used, else 0.9

---

### 5. Validation Agent

**Purpose**: Quality assurance and validation

**Validation Checks**:
1. **Completeness**: Answer length > 10 characters
2. **Consistency**: Results support answer
3. **Confidence**: Score > 0.5 threshold
4. **Relevance**: Query-answer keyword overlap

**Output**: Validated (true/false) + validation issues list

---

## Workflow Examples

### Example 1: Simple Query

**Query**: "50ml 용기"

**Workflow**:
1. **Router**: Intent=search, Complexity=simple, Reasoning=false
2. **Search**: Dense-only search (Qdrant) → 100 results
3. **Reasoning**: Skipped (not required)
4. **Synthesis**: General synthesis → "50ml 용기 검색 결과: 100개 제품"
5. **Validation**: Passed (no issues)

**Agent Trace**: `RouterAgent:route → SearchAgent:dense_search → SynthesisAgent:synthesize → ValidationAgent:validate`

**Performance**: ~300ms

---

### Example 2: Medium Query

**Query**: "50ml PET 용기 그리고 PP 재질"

**Workflow**:
1. **Router**: Intent=search, Complexity=medium, Reasoning=true
2. **Search**: Dense + Hybrid search → 80 results
3. **Reasoning**: Extract materials (PET, PP), capacities (50ml)
4. **Synthesis**: General synthesis with reasoning
5. **Validation**: Passed

**Agent Trace**: `RouterAgent:route → SearchAgent:dense_search → SearchAgent:hybrid_search → ReasoningAgent:chain_of_thought → SynthesisAgent:synthesize → ValidationAgent:validate`

**Performance**: ~600ms

---

### Example 3: Complex Query

**Query**: "50ml PET 용기와 100ml PP 용기의 차이점은?"

**Workflow**:
1. **Router**: Intent=comparison, Complexity=complex, Reasoning=true
2. **Search**: Dense + Hybrid + Re-ranking → 45 results
3. **Reasoning**: Analyze distribution, extract attributes, identify patterns
4. **Synthesis**: Comparison synthesis → "상위 제품 비교: 1. ... 2. ... 3. ..."
5. **Validation**: Passed (confidence=0.88)

**Agent Trace**: `RouterAgent:route → SearchAgent:dense_search → SearchAgent:hybrid_search → ReasoningAgent:chain_of_thought → SynthesisAgent:synthesize → ValidationAgent:validate`

**Performance**: ~1200ms

---

## Performance Benchmarks

| Query Type | Agents Invoked | Reasoning Steps | Total Time | Confidence |
|-----------|----------------|-----------------|------------|------------|
| **Simple** | 4 | 0 | ~300ms | 0.75 |
| **Medium** | 6 | 3-5 | ~600ms | 0.82 |
| **Complex** | 6 | 5-10 | ~1200ms | 0.88 |

---

## Configuration

### Environment Variables

```bash
# Enable multi-agent system (default: true)
MULTI_AGENT_ENABLED=true

# Enable reasoning for all queries (override complexity)
MULTI_AGENT_FORCE_REASONING=false

# Confidence threshold for validation
MULTI_AGENT_CONFIDENCE_THRESHOLD=0.5

# Enable validation (default: true)
MULTI_AGENT_ENABLE_VALIDATION=true
```

### Python Configuration

```python
from app.services.multi_agent_system import MultiAgentOrchestrator

# Create orchestrator
orchestrator = MultiAgentOrchestrator()

# Execute query
result = await orchestrator.execute(
    query="50ml PET bottle",
    session_id="user-123",
    collections=None,
    materials=None
)

# Access results
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
print(f"Agent Trace: {result['agent_trace']}")
```

---

## Testing

### Run Tests

```bash
# Run all multi-agent tests
pytest tests/integration/test_multi_agent.py -v

# Run specific test classes
pytest tests/integration/test_multi_agent.py::TestIndividualAgents -v
pytest tests/integration/test_multi_agent.py::TestMultiAgentOrchestrator -v

# Skip slow tests
pytest tests/integration/test_multi_agent.py -v -m "not slow"
```

### Test Coverage

- ✅ Individual agent functionality (Router, Search, Reasoning, Synthesis, Validation)
- ✅ Intent classification (comparison, recommendation, explanation, search)
- ✅ Complexity assessment (simple, medium, complex)
- ✅ Multi-agent orchestration workflow
- ✅ API endpoints (query, trace, health, config)
- ✅ Request validation
- ✅ Confidence scoring
- ✅ Workflow progression

---

## Migration Guide

### From Single-Agent to Multi-Agent

**Before** (Single search):
```python
# Direct search
result = await rag_skill.rag_query({
    "question": query,
    "top_k": 100
})
```

**After** (Multi-agent):
```python
# Intelligent multi-agent workflow
from app.services.multi_agent_system import create_multi_agent_orchestrator

orchestrator = create_multi_agent_orchestrator()
result = await orchestrator.execute(
    query=query,
    session_id=session_id
)

# Richer results
print(result['answer'])  # Synthesized answer
print(result['reasoning_steps'])  # Chain-of-thought
print(result['agent_trace'])  # Execution trace
```

---

## Troubleshooting

### Common Issues

#### 1. Reasoning Not Triggered

**Symptom**: Reasoning agent not invoked for complex queries

**Solution**:
- Check complexity assessment: Use `GET /api/v1/agents/trace/{session_id}`
- Override: Set `MULTI_AGENT_FORCE_REASONING=true`
- Adjust query: Add comparison words ("비교", "차이", "vs")

#### 2. Low Confidence Scores

**Symptom**: Validation fails due to low confidence

**Solution**:
- Improve search results: Use hybrid search
- Add more results: Increase `top_k`
- Lower threshold: Set `MULTI_AGENT_CONFIDENCE_THRESHOLD=0.3`

#### 3. Validation Always Fails

**Symptom**: All queries fail validation

**Solution**:
- Check validation issues: Review `validation_issues` in response
- Disable validation: Set `enable_validation=false` in request
- Review logs: Check validation agent logs

---

## Roadmap

### Completed (v6.0.0)
- ✅ Router agent (intent + complexity)
- ✅ Search agent (adaptive strategy)
- ✅ Reasoning agent (chain-of-thought)
- ✅ Synthesis agent (multi-strategy)
- ✅ Validation agent (quality checks)
- ✅ API endpoints
- ✅ Integration tests
- ✅ Agent tracing

### Planned (v6.1.0)
- ⏳ LangGraph integration (visual workflow editor)
- ⏳ Custom agent plugins
- ⏳ Agent learning from feedback
- ⏳ Multi-turn conversations with memory
- ⏳ Agent performance metrics (Prometheus)
- ⏳ A/B testing framework

---

## References

### Patterns
- **Chain-of-Thought**: Wei et al. (2022) - "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
- **ReAct**: Yao et al. (2023) - "ReAct: Synergizing Reasoning and Acting in Language Models"

### Libraries
- **LangGraph**: [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- **LangChain**: [LangChain Documentation](https://python.langchain.com/)

---

**Last Updated**: 2025-11-09
**Version**: v6.0.0
**Status**: ✅ Production Ready
