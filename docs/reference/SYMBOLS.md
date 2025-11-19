# RAG Enterprise - Symbol Reference

**Version**: v7.0.0+ | **Purpose**: Token-efficient navigation map

> **Format**: `§domain.component` → Load specific docs only
>
> **Benefit**: 50-200 lines vs 500-1000 lines per load

---

## 📖 Quick Symbol Index

### Core Systems
- **§rag.*** - RAG system (chunking, search, OCR)
- **§saas.*** - SaaS platform (auth, billing, tenants)
- **§collector.*** - Data collection pipeline
- **§manufacturing.*** - Vision inspection & quality
- **§realtime.*** - Realtime backend (v7.0.0+)

### Infrastructure (v7.0.0)
- **§security.*** - Keycloak + Vault
- **§observe.*** - Jaeger + Prometheus + Grafana
- **§data.*** - MinIO + Airflow + Metabase

### Development
- **§api.*** - API endpoints (48+)
- **§debug.*** - Debug system
- **§deploy.*** - Deployment guides

---

## 🎯 Core Symbols

### §rag - RAG System

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§rag.status** | CLAUDE.md:30-61 | 30 |
| **§rag.core** | docs/RAG_ACTIVATION_STRATEGY.md | 500+ |
| **§rag.engines** | docs/NEXA_SDK_INTEGRATION_PLAN.md | 400+ |
| **§rag.pipeline** | docs/RAG_ACTIVATION_STRATEGY.md:50-200 | 150 |

### §rag.advancement - RAG Advancement Plan (v10.5.0 → v11.0.0) ⭐ NEW

**Full Document**: `docs/planning/RAG_ADVANCEMENT_PLAN.md` (1642 lines)

**Quick Access Symbols** (80% token savings):

| Symbol | Load This | Lines | Content |
|--------|-----------|-------|---------|
| **§rag.advancement.overview** | RAG_ADVANCEMENT_PLAN.md:1-66 | 66 | Executive summary + Zero-cost strategy |
| **§rag.advancement.current** | RAG_ADVANCEMENT_PLAN.md:67-313 | 247 | Current implementation status (7/10) |
| **§rag.advancement.phase1** | RAG_ADVANCEMENT_PLAN.md:316-495 | 180 | Phase 1: Parent-Child + HyDE (Week 1-2) |
| **§rag.advancement.phase2** | RAG_ADVANCEMENT_PLAN.md:496-830 | 335 | Phase 2: Corrective + Self-RAG (Week 3-6) |
| **§rag.advancement.phase3** | RAG_ADVANCEMENT_PLAN.md:831-1141 | 311 | Phase 3: Graph + Agentic RAG (Week 7-10) |
| **§rag.advancement.metrics** | RAG_ADVANCEMENT_PLAN.md:1142-1249 | 108 | Performance targets + KPIs |
| **§rag.advancement.implementation** | RAG_ADVANCEMENT_PLAN.md:1250-1398 | 149 | File structure + Testing strategy |
| **§rag.advancement.risk** | RAG_ADVANCEMENT_PLAN.md:1399-1509 | 111 | Risk analysis + Timeline |
| **§rag.advancement.references** | RAG_ADVANCEMENT_PLAN.md:1510-1642 | 133 | Comparisons + References + Next steps |

**Token Efficiency**:
- Full load: 1642 lines ≈ 6500 tokens
- Symbol load: 66-335 lines ≈ 250-1300 tokens
- **Savings: 75-96% tokens**

**Usage Examples**:
```
Task: "Phase 1 어떻게 구현해?"
→ Load §rag.advancement.phase1 (180 lines)
   Instead of full doc (1642 lines)
   Savings: 89% tokens

Task: "현재 상태 확인"
→ Load §rag.advancement.current (247 lines)
   Savings: 85% tokens

Task: "전체 계획 개요"
→ Load §rag.advancement.overview (66 lines)
   Savings: 96% tokens
```

### §ocr - OCR Pipeline

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§ocr.pipeline** | docs/OCR_PARSING_STRATEGY.md | 300+ |
| **§ocr.engines** | docs/OCR_PARSING_STRATEGY.md:50-150 | 100 |

### §saas - SaaS Platform

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§saas.overview** | docs/SAAS_ARCHITECTURE.md | 800+ |
| **§saas.auth** | docs/SAAS_ARCHITECTURE.md:50-200 | 150 |
| **§saas.billing** | docs/SAAS_ARCHITECTURE.md:201-400 | 200 |

### §collector - Data Collector

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§collector.overview** | docs/DATA_COLLECTOR_ARCHITECTURE.md | 600+ |
| **§collector.pipeline** | docs/DATA_COLLECTOR_ARCHITECTURE.md:50-200 | 150 |

### §manufacturing - Manufacturing

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§manufacturing.overview** | docs/MANUFACTURING_AUTOMATION.md | 500+ |
| **§manufacturing.vision** | docs/MANUFACTURING_AUTOMATION.md:50-200 | 150 |

### §realtime - Realtime Backend ⭐ v7.0.0+

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§realtime.overview** | docs/REALTIME_BACKEND_GUIDE.md | 500+ |
| **§realtime.socketio** | docs/REALTIME_BACKEND_GUIDE.md:50-200 | 150 |
| **§realtime.postgres** | docs/REALTIME_BACKEND_GUIDE.md:201-350 | 150 |

---

## 🔧 Infrastructure Symbols (v7.0.0)

### §security - Security & Auth

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§security.keycloak** | docs/V7_COMPLETE_GUIDE.md:100-250 | 150 |
| **§security.vault** | docs/V7_COMPLETE_GUIDE.md:251-350 | 100 |

### §observe - Observability

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§observe.tracing** | docs/V7_COMPLETE_GUIDE.md:351-450 | 100 |
| **§observe.metrics** | docs/V7_COMPLETE_GUIDE.md:451-550 | 100 |

### §data - Data Platform

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§data.minio** | docs/V7_COMPLETE_GUIDE.md:701-800 | 100 |
| **§data.airflow** | docs/V7_COMPLETE_GUIDE.md:801-950 | 150 |

---

## 📡 API & Development

### §api - API Endpoints

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§api.overview** | docs/reference/API_DOCUMENTATION.md | 1000+ |
| **§api.rag** | docs/reference/API_DOCUMENTATION.md:50-200 | 150 |
| **§api.saas** | docs/reference/API_DOCUMENTATION.md:201-350 | 150 |

### §debug - Debug System

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§debug.overview** | docs/reference/DEBUG_SYSTEM.md | 400+ |
| **§debug.endpoints** | docs/reference/DEBUG_SYSTEM.md:50-200 | 150 |

### §deploy - Deployment

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§deploy.quick** | docs/DEPLOYMENT_GUIDE.md:1-100 | 100 |
| **§deploy.docker** | docs/DEPLOYMENT_GUIDE.md:101-300 | 200 |
| **§deploy.k8s** | docs/DEPLOYMENT_GUIDE.md:301-600 | 300 |

---

## 🏗️ Architecture

### §arch - System Architecture

| Symbol | Load This | Lines |
|--------|-----------|-------|
| **§arch.overview** | docs/ARCHITECTURE.md | 600+ |
| **§arch.services** | CLAUDE.md:557-603 | 46 |
| **§arch.opensource** | docs/OPEN_SOURCE_ARCHITECTURE.md | 400+ |

---

## 💡 Usage Examples

### Example 1: RAG Development
```
Task: "Understand RAG pipeline"
Load: §rag.pipeline (150 lines)
Instead of: Loading entire RAG_ACTIVATION_STRATEGY.md (500+ lines)
Savings: 70% tokens
```

### Example 2: SaaS Integration
```
Task: "Setup billing"
Load: §saas.billing (200 lines)
Instead of: Loading entire SAAS_ARCHITECTURE.md (800+ lines)
Savings: 75% tokens
```

### Example 3: Realtime Backend
```
Task: "Setup Socket.IO"
Load: §realtime.socketio (150 lines)
Instead of: Loading entire REALTIME_BACKEND_GUIDE.md (500+ lines)
Savings: 70% tokens
```

---

## 🔗 Document Hierarchy

```
Quick Reference (always loaded)
└─ CLAUDE.md (~300 lines)

Symbol Map (load to find docs)
└─ docs/reference/SYMBOLS.md (~200 lines)

Guides (load for tasks)
├─ docs/guides/QUICK_REFERENCE.md
├─ docs/guides/LOCAL_SETUP.md
└─ docs/guides/TROUBLESHOOTING.md

References (load for specific info)
├─ docs/reference/API_DOCUMENTATION.md
└─ docs/reference/DEBUG_SYSTEM.md

Deep Dives (load for full understanding)
├─ docs/V7_COMPLETE_GUIDE.md
├─ docs/REALTIME_BACKEND_GUIDE.md
├─ docs/SAAS_ARCHITECTURE.md
└─ docs/RAG_ACTIVATION_STRATEGY.md
```

---

## 📊 Token Optimization Impact

| Approach | Lines Loaded | Tokens Used | Efficiency |
|----------|--------------|-------------|-----------|
| ❌ Load full file | 500-1000 | ~2000-4000 | Low |
| ✅ Load symbol section | 50-200 | ~200-800 | High |
| **Savings** | **70-80%** | **70-80%** | **4-5x better** |

---

**Version**: v7.0.0+
**Lines**: 200 (vs 1011 before = 80% reduction)
**Purpose**: Fast symbol lookup
**Usage**: `§symbol` → load specific section only
