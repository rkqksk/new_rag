# Manufacturing Vision - Defect Detection Workflow

## Complete Training Pipeline

### Step 1: Prepare Dataset
```bash
# Collect images
mkdir -p data/defects/{train,val,test}/{scratch,dent,crack,ok}

# Organize images by class
# train/scratch/*.jpg
# train/dent/*.jpg
# train/crack/*.jpg
# train/ok/*.jpg (good products)
```

### Step 2: Convert to YOLO Format
```bash
python scripts/convert_to_yolo.py \
  --input data/defects/ \
  --output data/yolo_dataset/
```

### Step 3: Train YOLO Model
```bash
python .claude/skills/manufacturing-vision/scripts/train_yolo.py \
  --data data/yolo_dataset/data.yaml \
  --model yolov8n \
  --epochs 100 \
  --imgsz 640
```

### Step 4: Evaluate Model
```bash
# Test accuracy
python scripts/evaluate_model.py \
  --model runs/detect/train/weights/best.pt \
  --data data/yolo_dataset/data.yaml

# Expected output:
# mAP50: 0.89
# mAP50-95: 0.76
# Precision: 0.91
# Recall: 0.87
```

### Step 5: Deploy to Edge Device
```bash
# Export to ONNX
python scripts/export_onnx.py \
  --model runs/detect/train/weights/best.pt \
  --format onnx

# Deploy to Jetson Nano
scp best.onnx jetson@192.168.1.100:/home/jetson/models/
```

## Real-time Inference

```python
from ultralytics import YOLO
import cv2

model = YOLO('best.onnx')

# Webcam inference
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    results = model(frame)

    # Check for defects
    for result in results:
        if result.boxes:
            print(f"Defect detected: {result.names}")
```
