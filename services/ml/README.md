# ML Service (Planned)

**Status**: 🚧 Scaffold Only - Not Production Ready

## Current State

This is a placeholder directory for future microservice extraction. The ML service is currently **not functional** and exists only as a structural placeholder.

## Actual Implementation

👉 **All ML functionality currently lives in `apps/api/`**

- Text embeddings generation via Sentence Transformers
- LLM inference and text generation
- Model management and serving (PyTorch, ONNX)
- Batch processing for embeddings
- Model caching and optimization

## Planned Features (Future Extraction)

When extracted as a microservice, this service will handle:

- Text embeddings generation (Sentence Transformers, OpenAI, Cohere)
- LLM inference (OpenAI, Claude, local models via Ollama)
- Model serving and management (PyTorch, ONNX, TensorRT)
- Batch embedding processing for scalability
- Model fine-tuning and custom training
- GPU-accelerated inference
- Model caching and optimization

## Roadmap

- **Phase 1**: Consolidate ML logic in `apps/api/` (Current)
- **Phase 2**: Extract to standalone service (Post-v10.0.0)
- **Phase 3**: Scale with distributed model serving
- **Phase 4**: Deploy independently with GPU support

Estimated extraction: **Q2 2025** (After v10 stabilization)

See `docs/planning/MICROSERVICES_ROADMAP.md` for complete strategy.

## DO NOT USE

**This service is not functional and will return errors if deployed.**

- No implementation files
- No embedding endpoints
- No LLM clients
- No model serving

## Related Documentation

- **LLM Router**: `apps/api/core/routing/llm_router.py`
- **API Endpoints**: `docs/reference/API_DOCUMENTATION.md`
- **Services Architecture**: `docs/reference/ARCHITECTURE.md`

---

**Last Updated**: 2025-11-19  
**Target Extraction**: Post-v10.0.0
