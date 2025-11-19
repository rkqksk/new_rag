# Manufacturing Vision Service (Planned)

**Status**: 🚧 Scaffold Only - Not Production Ready

## Current State

This is a placeholder directory for future microservice extraction. The Manufacturing Vision service is currently **not functional** and exists only as a structural placeholder.

## Actual Implementation

👉 **All manufacturing/vision functionality currently lives in `apps/api/`**

- YOLO model integration and inference
- Image classification and processing
- Defect detection logic
- Quality metrics calculation
- Edge deployment configurations (ONNX, TensorRT)

## Planned Features (Future Extraction)

When extracted as a microservice, this service will handle:

- YOLO-based defect detection (YOLOv8, YOLOv10)
- Real-time video processing and frame extraction
- Image classification for quality control
- Quality metrics calculation and reporting
- Model serving with ONNX and TensorRT optimization
- Edge deployment support (IoT, on-device inference)
- Batch inspection workflows
- Model fine-tuning and retraining pipelines

## Roadmap

- **Phase 1**: Consolidate vision logic in `apps/api/` (Current)
- **Phase 2**: Extract to standalone service (Post-v10.0.0)
- **Phase 3**: Optimize for edge deployment (ONNX, TensorRT)
- **Phase 4**: Deploy independently with GPU support

Estimated extraction: **Q2 2025** (After v10 stabilization)

See `docs/planning/MICROSERVICES_ROADMAP.md` for complete strategy.

## DO NOT USE

**This service is not functional and will return errors if deployed.**

- No implementation files
- No YOLO integration
- No inference endpoints
- No model serving

## Related Documentation

- **Manufacturing Automation**: `docs/MANUFACTURING_AUTOMATION.md`
- **Vision Inspection**: `packages/manufacturing-vision/` (core implementation)
- **API Endpoints**: `docs/reference/API_DOCUMENTATION.md`

---

**Last Updated**: 2025-11-19  
**Target Extraction**: Post-v10.0.0
