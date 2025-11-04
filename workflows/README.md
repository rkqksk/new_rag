# Workflows Documentation

**End-to-end workflows and comprehensive guides - load on demand.**

---

## 📚 Available Workflows

### Core Workflows
| Workflow | Command | Description |
|----------|---------|-------------|
| **Document Processing** | `/workflow document-processing` | Document ingestion, chunking, embedding |
| **RAG Query** | `/workflow rag-query` | RAG query execution and answer generation |
| **Domain Expert** | `/workflow domain-expert` | Domain expert plugin integration |

### System Documentation
| Document | Command | Description |
|----------|---------|-------------|
| **Architecture** | `/workflow ARCHITECTURE` | System architecture and data flow |
| **Usage Guide** | `/workflow USAGE_GUIDE` | Complete slash command usage guide |

---

## 🎯 Quick Access

### By Task
- **"I want to process documents"** → `/workflow document-processing`
- **"How do I query the RAG system?"** → `/workflow rag-query`
- **"How do domain experts work?"** → `/workflow domain-expert`
- **"Show me system architecture"** → `/workflow ARCHITECTURE`
- **"How do I use slash commands?"** → `/workflow USAGE_GUIDE`

---

## 📖 What's in Each Workflow

### document-processing.md
- Complete ingestion pipeline
- Domain expert enrichment
- Chunking strategies
- Vector storage
- Error handling
- Performance tips

### rag-query.md
- Query execution flow
- Vector search + filtering
- Reranking strategies
- Answer generation
- Performance tuning

### domain-expert.md
- Manufacturing expert details
- Packaging expert details
- Plugin architecture
- Adding new domains

### ARCHITECTURE.md
- System overview
- Component details
- Data flow diagrams
- Token efficiency analysis
- Performance targets

### USAGE_GUIDE.md
- Slash command reference
- Auto-trigger keywords
- Usage scenarios
- Best practices
- Troubleshooting

---

## 💡 Loading Strategy

**Auto-loaded (Always)**:
- CLAUDE.md (~753 tokens)
- README.md (~252 tokens)
- QUICK_START.md (~609 tokens)
- **Total: ~1,614 tokens**

**On-demand (When needed)**:
- Workflows (~1,500-3,000 tokens each)
- Load only what you need
- **79% token savings!**

---

## 🚀 Usage Examples

### Example 1: Document Processing
```
User: "How do I process a PDF?"
Claude: [Auto-loads document-processing.md]
        [Answers with 1,675 tokens of context]
Total: 1,614 + 1,675 = 3,289 tokens
```

### Example 2: System Architecture
```
User: "/workflow ARCHITECTURE"
Claude: [Loads ARCHITECTURE.md]
        [Provides architecture details]
Total: 1,614 + 3,020 = 4,634 tokens
```

### Example 3: Quick Question
```
User: "What's this project about?"
Claude: [Uses only CLAUDE.md]
        [Answers from quick reference]
Total: 1,614 tokens only
```

---

**Last Updated**: 2025-11-03
