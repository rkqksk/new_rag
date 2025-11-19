# RAG Service (Planned)

**Status**: 🚧 Scaffold Only - Not Production Ready

## Current State

This is a placeholder directory for future microservice extraction. The RAG service is currently **not functional** and exists only as a structural placeholder.

## Actual Implementation

👉 **All RAG functionality currently lives in `apps/api/`**

- Query optimization: `apps/api/services/advanced_query_optimizer.py`
- Semantic search: `apps/api/rag_consultation/retrieval/`
- Response generation: `apps/api/rag_consultation/generation/`
- RAG consultation: `apps/api/rag_consultation/`
- RAG QA service: `apps/api/services/rag_qa_service.py`

## Planned Features (Future Extraction)

When extracted as a microservice, this service will handle:

- Semantic search using vector embeddings (Qdrant)
- Context retrieval from knowledge base
- LLM integration (OpenAI, Claude, Nexa)
- Query optimization and expansion
- Response generation with RAG

## Roadmap

- **Phase 1**: Stabilize core implementation in `apps/api/` (Current)
- **Phase 2**: Extract to standalone service (Post-v10.0.0)
- **Phase 3**: Deploy independently to Kubernetes
- **Phase 4**: Auto-scaling based on load

Estimated extraction: **Q2 2025** (After v10 stabilization)

See `docs/planning/MICROSERVICES_ROADMAP.md` for complete strategy.

## DO NOT USE

**This service is not functional and will return errors if deployed.**

- No implementation files
- No endpoint handlers
- No database connections
- No LLM clients

## Related Documentation

- **RAG Implementation**: `docs/RAG_ACTIVATION_STRATEGY.md`
- **API Endpoints**: `docs/reference/API_DOCUMENTATION.md`
- **Architecture**: `apps/api/rag_consultation/README.md`

---

**Last Updated**: 2025-11-19  
**Target Extraction**: Post-v10.0.0
