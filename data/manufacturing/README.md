# Manufacturing Data Directory

**v7.1.0 - LORA Fine-Tuning + UR10e Robot Integration**

---

## Directory Structure

```
manufacturing/
├── datasets/               # Training datasets for LORA adapters
│   ├── pet_bottles/       # PET bottle defect detection
│   │   ├── train/
│   │   │   ├── images/    # Training images (500+)
│   │   │   └── labels/    # YOLO format annotations (.txt)
│   │   └── val/
│   │       ├── images/    # Validation images (100+)
│   │       └── labels/
│   ├── aluminum_cans/     # Aluminum can defect detection
│   ├── mold_defects/      # Injection molding defects
│   └── pcb_defects/       # PCB assembly defects
│
├── models/                 # Trained models
│   └── lora_adapters/     # Product-specific LORA adapters (11MB each)
│       ├── pet_bottles_v1.pth
│       ├── aluminum_cans_v1.pth
│       ├── mold_defects_v1.pth
│       └── pcb_defects_v1.pth
│
└── training_logs/          # Training metrics and logs
    ├── pet_bottles/
    ├── aluminum_cans/
    ├── mold_defects/
    └── pcb_defects/
```

---

## Dataset Requirements

### Image Format
- **Format**: JPEG or PNG
- **Resolution**: 640x640 (YOLO standard) or higher
- **Quantity**:
  - Train: 500+ images per product type
  - Val: 100+ images per product type
  - Test: 50+ images per product type

### Annotation Format (YOLO)

Each image requires a corresponding `.txt` file with the same name:

```
# Format: class_id center_x center_y width height (normalized 0-1)
0 0.5 0.5 0.3 0.4  # defect_scratch at center
1 0.2 0.3 0.1 0.15 # defect_dent at top-left
```

**Class Mapping** (example for PET bottles):
```
0: scratch
1: dent
2: crack
3: contamination
4: deformation
```

---

## Data Collection Guidelines

### 1. Image Capture
- **Lighting**: Consistent, bright, no shadows
- **Angle**: Standardized (e.g., top-down, 45°)
- **Background**: Plain, contrasting color
- **Focus**: Sharp, in-focus images only

### 2. Defect Coverage
- Capture variety of defect sizes (small, medium, large)
- Include edge cases (partial defects, multiple defects)
- Balance defect vs. non-defect images (60:40 ratio)

### 3. Quality Control
- Remove blurry or poorly lit images
- Verify all annotations are accurate
- Check label file format (YOLO format)
- Validate normalized coordinates (0-1 range)

---

## LORA Adapter Training

### Training Process

1. **Prepare Dataset**
   ```bash
   # Organize images and labels
   python scripts/prepare_dataset.py --product pet_bottles
   ```

2. **Train LORA Adapter**
   ```bash
   # Train with base YOLOv8x model
   python scripts/train_lora_adapter.py \
     --product pet_bottles \
     --base-model models/yolov8x_base.pt \
     --epochs 50 \
     --batch 16
   ```

3. **Validate Performance**
   ```bash
   # Test adapter on validation set
   python scripts/validate_adapter.py \
     --adapter models/lora_adapters/pet_bottles_v1.pth \
     --dataset datasets/pet_bottles/val
   ```

### Expected Results

| Metric | Target | Acceptable |
|--------|--------|------------|
| Accuracy | > 95% | > 90% |
| Precision | > 94% | > 88% |
| Recall | > 92% | > 85% |
| Inference Time | < 50ms | < 100ms |
| Adapter Size | ~11MB | < 20MB |

---

## Usage Example

```python
from src.services.lora_vision_service import LORAVisionService

# Initialize service
lora_vision = LORAVisionService()

# Switch to PET bottles adapter
lora_vision.switch_adapter("pet_bottles")

# Inspect image
image = cv2.imread("test_bottle.jpg")
result = lora_vision.inspect(image, product_type="pet_bottles")

print(f"Defects: {result['defects']}")
print(f"Inference: {result['inference_time_ms']}ms")
```

---

## Current Status

**Phase 1, Week 1**: Dataset structure created ✅

**Next Steps**:
1. Collect/generate sample images (500+ per product)
2. Annotate images with YOLO format
3. Train first LORA adapter (PET bottles)
4. Benchmark performance

---

**Version**: v7.1.0
**Updated**: 2025-11-11
**Owner**: Manufacturing Engineering Team
