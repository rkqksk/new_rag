---
name: manufacturing-vision
description: YOLO defect detection vision inspection quality control 불량 검사 비전 품질 관리 YOLOv8 YOLOv10 ultralytics OpenCV torch ONNX TensorRT edge deployment 제조 자동화 결함 탐지
---

# Manufacturing Vision Inspection

## When to Use
- 불량 검사 자동화, defect detection automation
- 비전 검사, vision inspection
- 품질 관리, quality control
- YOLO 모델 훈련, YOLO training
- 제품 검사, product inspection
- Edge 디바이스 배포, edge deployment
- 실시간 검사, real-time inspection

## Core Capabilities
1. **Defect Detection** - YOLO v8/v10 for scratches, dents, cracks, discoloration
2. **Model Training** - Dataset preparation, augmentation, training pipeline
3. **Edge Deployment** - ONNX, TensorRT export for edge devices
4. **Quality Reporting** - Excel reports, statistics, dashboards

## Quick Actions

### Prepare Dataset
```python
# Convert to YOLO format
python scripts/prepare_dataset.py \
  --images data/images/ \
  --labels data/labels/ \
  --split 0.8,0.1,0.1 \
  --output data/yolo_dataset/
```

### Train Model
```python
# Train YOLO
python scripts/train_yolo.py \
  --model yolov8n \
  --data data/yolo_dataset/data.yaml \
  --epochs 100 \
  --imgsz 640
```

### Evaluate Performance
```python
# Test model
python scripts/evaluate_model.py \
  --model runs/detect/train/weights/best.pt \
  --data data/yolo_dataset/data.yaml \
  --metrics mAP,precision,recall
```

### Export for Edge
```python
# Export to ONNX
python scripts/export_onnx.py \
  --model best.pt \
  --format onnx \
  --optimize \
  --device cuda
```

## Defect Types
- **Scratch** (긁힘) - Surface scratches
- **Dent** (찌그러짐) - Deformations
- **Crack** (균열) - Cracks and fractures
- **Discoloration** (변색) - Color defects
- **Missing Parts** (부품 누락) - Component absence

## Model Options
- **YOLOv8n** - Fastest, 80 FPS, 37.3 mAP
- **YOLOv8s** - Balanced, 60 FPS, 44.9 mAP
- **YOLOv8m** - Accurate, 45 FPS, 50.2 mAP
- **YOLOv10** - Latest, improved efficiency

## Integration
- **testing-suite**: Validate model accuracy
- **deployment-automation**: Deploy to edge devices
- **excel-processing**: Generate inspection reports
- **rag-optimization**: Index defect knowledge base

## Key Files
- `src/services/vision_service.py` - Vision inspection service
- `scripts/yolo/` - YOLO training scripts
- `models/yolo/` - Trained models

## Hardware Requirements
- **Training**: NVIDIA GPU (8GB+ VRAM)
- **Inference**: Edge devices (Jetson Nano, RPi + Coral)
- **Storage**: 10GB+ for datasets
