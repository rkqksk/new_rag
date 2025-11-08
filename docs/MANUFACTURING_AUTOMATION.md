# Manufacturing Automation & Vision Inspection System

**Edge AI-powered quality control with YOLO + Jetson Orin Nano/Raspberry Pi**

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [YOLO Vision Inspection](#yolo-vision-inspection)
4. [Edge Device Integration](#edge-device-integration)
5. [Quality Control Pipeline](#quality-control-pipeline)
6. [RAG Integration](#rag-integration)
7. [Real-time Monitoring](#real-time-monitoring)
8. [Implementation](#implementation)

---

## Overview

### Manufacturing Automation Stack

```
Edge AI Vision Inspection System
├── Computer Vision
│   ├── YOLOv8/v10 (Defect Detection)
│   ├── Image Classification
│   ├── Object Detection
│   └── Anomaly Detection
├── Edge Devices
│   ├── Jetson Orin Nano (GPU-accelerated)
│   ├── Raspberry Pi 4/5 (CPU)
│   └── Industrial Cameras (USB, CSI, MIPI)
├── Quality Control
│   ├── Real-time Inspection
│   ├── Defect Classification
│   ├── Statistical Process Control (SPC)
│   └── Automated Alerts
├── Data Pipeline
│   ├── Image Capture → Processing → Analysis
│   ├── Results Logging (PostgreSQL)
│   ├── RAG Integration (Product Specs)
│   └── Dashboard (Grafana/Custom)
└── Integration
    ├── Manufacturing Surveillance
    ├── Data Collector
    └── RAG Enterprise
```

---

## System Architecture

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                   Production Line                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │ Station 1│→  │ Station 2│→  │ Station 3│→  │ Station 4│  │
│  │ (Camera) │   │ (Camera) │   │ (Camera) │   │ (Camera) │  │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘  │
└───────┼──────────────┼──────────────┼──────────────┼─────────┘
        │              │              │              │
        ↓              ↓              ↓              ↓
┌───────────────────────────────────────────────────────────────┐
│              Edge Devices (Jetson/Raspberry Pi)                │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │  Device  │   │  Device  │   │  Device  │   │  Device  │  │
│  │    #1    │   │    #2    │   │    #3    │   │    #4    │  │
│  │  YOLOv8  │   │  YOLOv8  │   │  YOLOv8  │   │  YOLOv8  │  │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘  │
└───────┼──────────────┼──────────────┼──────────────┼─────────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                       ↓ MQTT/HTTP
┌───────────────────────────────────────────────────────────────┐
│                    Central Server                              │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  RAG Enterprise + Manufacturing Automation Module      │   │
│  ├────────────────────────────────────────────────────────┤   │
│  │  - Aggregated Analytics                                │   │
│  │  - Product Spec Retrieval (RAG)                        │   │
│  │  - Defect Trend Analysis                               │   │
│  │  - Alert Management                                    │   │
│  │  - Dashboard & Reports                                 │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                       ↓
┌───────────────────────────────────────────────────────────────┐
│                  Database & Storage                            │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                  │
│  │PostgreSQL│   │   Qdrant │   │  MinIO   │                  │
│  │(Metadata)│   │ (Vectors)│   │ (Images) │                  │
│  └──────────┘   └──────────┘   └──────────┘                  │
└───────────────────────────────────────────────────────────────┘
```

---

## YOLO Vision Inspection

### YOLOv8 for Defect Detection

**Why YOLOv8**:
- ✅ State-of-the-art object detection
- ✅ Real-time performance (60+ FPS on Jetson)
- ✅ Easy to train on custom datasets
- ✅ Supports classification + detection + segmentation
- ✅ TensorRT optimization for Jetson

**Alternative**: YOLOv10, YOLO-NAS (even faster)

### Defect Types

#### 1. Packaging Defects
- Scratches
- Cracks
- Deformation
- Color inconsistency
- Label misalignment
- Missing caps/seals

#### 2. Dimensional Defects
- Incorrect size
- Neck size variation
- Wall thickness issues

#### 3. Quality Issues
- Surface defects
- Air bubbles
- Contamination

### Model Training

**Dataset Preparation**:
```python
# data/dataset.yaml

path: /data/packaging_defects
train: images/train
val: images/val
test: images/test

names:
  0: good
  1: scratch
  2: crack
  3: deformation
  4: color_issue
  5: label_misaligned
  6: missing_cap

# Class distribution
# good: 10000 images
# defects: 2000 images each (augmented)
```

**Training Script**:
```python
# scripts/train_yolo.py

from ultralytics import YOLO

# Load pretrained model
model = YOLO('yolov8n.pt')  # Nano model (fastest)
# or: yolov8s.pt (small), yolov8m.pt (medium), yolov8l.pt (large)

# Train
results = model.train(
    data='data/dataset.yaml',
    epochs=100,
    imgsz=640,  # Input size
    batch=16,
    device=0,  # GPU 0
    workers=8,
    project='runs/packaging',
    name='yolov8n_defects',

    # Augmentation
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=10,
    translate=0.1,
    scale=0.5,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.5,
    mosaic=1.0,

    # Advanced
    patience=20,  # Early stopping
    save_period=10,  # Save checkpoint every 10 epochs
    cache=True  # Cache images for faster training
)

# Validate
metrics = model.val()

print(f"mAP50: {metrics.box.map50:.3f}")
print(f"mAP50-95: {metrics.box.map:.3f}")

# Export for deployment
model.export(format='onnx')  # For Jetson/Pi
model.export(format='engine')  # TensorRT for Jetson (fastest)
```

### Inference on Edge Device

**Jetson Orin Nano**:
```python
# edge/yolo_inference_jetson.py

from ultralytics import YOLO
import cv2
import time

# Load model (TensorRT engine for maximum speed)
model = YOLO('yolov8n_defects.engine')

# Open camera
cap = cv2.VideoCapture(0)  # USB camera
# or: cap = cv2.VideoCapture("rtsp://camera_ip/stream")

# Configure
conf_threshold = 0.7  # Confidence threshold
iou_threshold = 0.5  # NMS threshold

# FPS counter
fps_counter = []

while True:
    start_time = time.time()

    # Capture frame
    ret, frame = cap.read()
    if not ret:
        break

    # Run inference
    results = model.predict(
        frame,
        conf=conf_threshold,
        iou=iou_threshold,
        device=0,  # GPU
        verbose=False
    )

    # Parse results
    for result in results:
        boxes = result.boxes

        for box in boxes:
            # Extract info
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Get class name
            class_name = model.names[cls]

            # Check if defect
            if class_name != "good":
                # Defect detected!
                print(f"⚠️  Defect: {class_name} (confidence: {conf:.2f})")

                # Send alert
                send_alert_to_server({
                    "timestamp": time.time(),
                    "defect_type": class_name,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2],
                    "image_path": save_defect_image(frame)
                })

            # Draw bounding box
            color = (0, 255, 0) if class_name == "good" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"{class_name} {conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

    # Calculate FPS
    fps = 1 / (time.time() - start_time)
    fps_counter.append(fps)

    # Display
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Vision Inspection", frame)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

print(f"Average FPS: {sum(fps_counter) / len(fps_counter):.1f}")
```

**Performance Benchmarks**:

| Device | Model | FPS | Latency | Power |
|--------|-------|-----|---------|-------|
| Jetson Orin Nano (TensorRT) | YOLOv8n | 120 | 8ms | 15W |
| Jetson Orin Nano (ONNX) | YOLOv8n | 80 | 12ms | 12W |
| Raspberry Pi 5 (ONNX) | YOLOv8n | 15 | 66ms | 5W |
| Raspberry Pi 4 | YOLOv8n | 8 | 125ms | 4W |

---

## Edge Device Integration

### Jetson Orin Nano Setup

**Specifications**:
- GPU: 1024-core NVIDIA Ampere (32 Tensor Cores)
- CPU: 6-core Arm Cortex-A78AE
- RAM: 8GB LPDDR5
- Storage: MicroSD + NVMe SSD
- Power: 7-15W
- Price: ~$499

**Setup Steps**:

1. **Flash JetPack SDK**:
```bash
# Download JetPack 5.1.2 or later
# Flash to SD card using balenaEtcher or SD Card Formatter

# Boot and update
sudo apt-get update
sudo apt-get upgrade
```

2. **Install CUDA, cuDNN, TensorRT** (included in JetPack):
```bash
# Verify
nvcc --version
dpkg -l | grep TensorRT
```

3. **Install Python Dependencies**:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PyTorch (Jetson-specific wheel)
wget https://nvidia.box.com/shared/static/xxx.whl
pip install torch-*.whl

# Install ultralytics
pip install ultralytics

# Install OpenCV with CUDA
# (Pre-installed in JetPack, or build from source for custom config)
```

4. **Optimize Model for TensorRT**:
```python
from ultralytics import YOLO

# Load PyTorch model
model = YOLO('yolov8n_defects.pt')

# Export to TensorRT
model.export(
    format='engine',
    half=True,  # FP16 precision (2x faster)
    workspace=4,  # GB
    device=0
)

# Result: yolov8n_defects.engine (optimized for Jetson)
```

5. **Setup Camera**:
```bash
# USB camera
ls /dev/video*

# CSI camera (Raspberry Pi Camera Module V2)
# Connect to J13 CSI connector
v4l2-ctl --list-devices
```

---

### Raspberry Pi Setup

**Recommended**: Raspberry Pi 5 (8GB) for better performance

**Setup Steps**:

1. **Flash Raspberry Pi OS**:
```bash
# Use Raspberry Pi Imager
# Choose: Raspberry Pi OS (64-bit)
```

2. **Install Dependencies**:
```bash
# Update
sudo apt-get update
sudo apt-get upgrade

# Install Python
sudo apt-get install python3-pip python3-venv

# Install OpenCV
sudo apt-get install python3-opencv

# Install ultralytics
pip install ultralytics
```

3. **Optimize for CPU Inference**:
```python
# Use ONNX Runtime for faster CPU inference
model.export(format='onnx')

# Run with ONNX Runtime
import onnxruntime as ort

session = ort.InferenceSession('yolov8n_defects.onnx')
```

---

## Quality Control Pipeline

### Inspection Workflow

```
[1] Image Capture
    ↓
[2] Preprocessing
    - Resize (640x640)
    - Normalize
    - Auto-exposure adjustment
    ↓
[3] YOLO Inference
    - Object detection
    - Defect classification
    - Confidence scoring
    ↓
[4] Post-processing
    - NMS (Non-Max Suppression)
    - Threshold filtering
    - ROI extraction
    ↓
[5] Decision Logic
    - Pass/Fail determination
    - Alert triggering
    - Data logging
    ↓
[6] Action
    - Reject defective products
    - Update dashboard
    - Send to RAG for spec lookup
```

### Statistical Process Control (SPC)

```python
# src/services/spc_service.py

import numpy as np
from datetime import datetime, timedelta

class SPCService:
    """Statistical Process Control for quality monitoring"""

    def __init__(self):
        self.control_limits = {
            "defect_rate": {"ucl": 0.05, "lcl": 0.0},  # Upper/Lower Control Limits
            "avg_confidence": {"ucl": 1.0, "lcl": 0.8}
        }

    def check_control_limits(
        self,
        metric_name: str,
        value: float
    ) -> dict:
        """Check if metric is within control limits"""

        limits = self.control_limits.get(metric_name)
        if not limits:
            return {"in_control": True}

        ucl = limits["ucl"]
        lcl = limits["lcl"]

        in_control = lcl <= value <= ucl

        return {
            "in_control": in_control,
            "value": value,
            "ucl": ucl,
            "lcl": lcl,
            "action": "normal" if in_control else "investigate"
        }

    def calculate_defect_rate(
        self,
        defect_count: int,
        total_count: int
    ) -> float:
        """Calculate defect rate"""
        if total_count == 0:
            return 0.0
        return defect_count / total_count

    def get_trend_analysis(
        self,
        time_range_hours: int = 24
    ) -> dict:
        """Analyze defect trends over time"""

        # Query database for recent inspections
        # ... (implementation)

        return {
            "trend": "increasing",  # increasing, stable, decreasing
            "current_rate": 0.03,
            "previous_rate": 0.02,
            "change_percent": 50.0,
            "recommendation": "Investigate process changes"
        }
```

---

## RAG Integration

### Product Spec Retrieval

When a defect is detected, automatically look up product specifications:

```python
# src/services/inspection_rag_service.py

from src.core.rag_pipeline import RAGPipeline

class InspectionRAGService:
    """Integrate vision inspection with RAG"""

    def __init__(self):
        self.rag = RAGPipeline()

    async def lookup_product_spec(
        self,
        product_code: str
    ) -> dict:
        """
        Look up product specifications using RAG

        Args:
            product_code: Product code detected from image/barcode

        Returns:
            Product specifications and quality thresholds
        """

        # Query RAG
        results = await self.rag.search(
            query=f"Product {product_code} specifications quality requirements",
            top_k=3
        )

        if not results:
            return {"found": False}

        # Extract specs
        spec = results[0]

        return {
            "found": True,
            "product_code": spec["product_code"],
            "product_name": spec["product_name"],
            "material": spec["material"],
            "capacity_ml": spec["capacity_ml"],
            "quality_requirements": {
                "max_scratch_size_mm": 2.0,
                "max_crack_length_mm": 0.5,
                "color_tolerance": "±5%",
                "dimensional_tolerance": "±0.5mm"
            },
            "reference_images": spec.get("image_urls", [])
        }

    async def validate_against_spec(
        self,
        defect: dict,
        product_code: str
    ) -> dict:
        """
        Validate detected defect against product specifications

        Args:
            defect: Defect detection result
            product_code: Product code

        Returns:
            Validation result with pass/fail decision
        """

        # Look up spec
        spec = await self.lookup_product_spec(product_code)

        if not spec["found"]:
            return {"validated": False, "reason": "No spec found"}

        # Check against requirements
        defect_type = defect["defect_type"]
        requirements = spec["quality_requirements"]

        # Example: Check scratch size
        if defect_type == "scratch":
            defect_size = defect.get("size_mm", 0)
            max_allowed = requirements.get("max_scratch_size_mm", 0)

            pass_inspection = defect_size <= max_allowed

            return {
                "validated": True,
                "pass": pass_inspection,
                "defect_size": defect_size,
                "max_allowed": max_allowed,
                "severity": "minor" if pass_inspection else "major"
            }

        # Default: fail if defect detected
        return {
            "validated": True,
            "pass": False,
            "severity": "major"
        }
```

---

## Real-time Monitoring

### MQTT Communication

Edge devices → Central server communication:

```python
# edge/mqtt_publisher.py

import paho.mqtt.client as mqtt
import json

class MQTTPublisher:
    """Publish inspection results to MQTT broker"""

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883
    ):
        self.client = mqtt.Client()
        self.client.connect(broker_host, broker_port)

    def publish_inspection_result(
        self,
        device_id: str,
        result: dict
    ):
        """Publish inspection result"""

        topic = f"manufacturing/inspection/{device_id}"

        payload = json.dumps({
            "device_id": device_id,
            "timestamp": result["timestamp"],
            "product_code": result.get("product_code"),
            "defect_type": result.get("defect_type", "none"),
            "confidence": result.get("confidence", 1.0),
            "pass": result["pass"],
            "image_path": result.get("image_path")
        })

        self.client.publish(topic, payload)

# Usage on edge device
publisher = MQTTPublisher(broker_host="central-server.local")

# After inference
if defect_detected:
    publisher.publish_inspection_result(
        device_id="station_01",
        result={
            "timestamp": time.time(),
            "product_code": "A-100",
            "defect_type": "scratch",
            "confidence": 0.92,
            "pass": False,
            "image_path": "/data/defects/20250108_143022.jpg"
        }
    )
```

**Central Server Subscriber**:
```python
# src/services/mqtt_subscriber.py

import paho.mqtt.client as mqtt
import json

class MQTTSubscriber:
    """Subscribe to inspection results from edge devices"""

    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        """Subscribe to all inspection topics"""
        print(f"Connected with result code {rc}")
        client.subscribe("manufacturing/inspection/#")

    def on_message(self, client, userdata, msg):
        """Handle incoming inspection result"""
        data = json.loads(msg.payload.decode())

        print(f"Received from {data['device_id']}: {data['defect_type']}")

        # Store in database
        self.save_to_database(data)

        # Check SPC
        self.check_spc_alerts(data)

        # Update dashboard
        self.update_dashboard(data)

    def save_to_database(self, data: dict):
        """Save inspection result to PostgreSQL"""
        # ... implementation

    def check_spc_alerts(self, data: dict):
        """Check if SPC thresholds exceeded"""
        # ... implementation

    def update_dashboard(self, data: dict):
        """Push update to real-time dashboard"""
        # ... implementation (WebSocket or Server-Sent Events)

# Run subscriber
subscriber = MQTTSubscriber()
subscriber.client.connect("localhost", 1883)
subscriber.client.loop_forever()
```

---

## Implementation

### Deployment Architecture

**Option 1: Centralized (Small Scale)**:
```
1-4 Edge Devices → Central Server (RAG Enterprise)
```

**Option 2: Distributed (Large Scale)**:
```
10+ Edge Devices → Edge Gateway → Central Server
```

**Option 3: Hybrid**:
```
Edge Devices (Real-time inspection) + Cloud (Analytics, ML training)
```

### Setup Steps

1. **Edge Device Setup**:
```bash
# On Jetson/Pi
git clone https://github.com/rkqksk/rag-enterprise.git
cd rag-enterprise/edge

# Install dependencies
pip install -r requirements.txt

# Download model
wget https://your-server.com/models/yolov8n_defects.engine

# Run
python3 yolo_inference_jetson.py --device-id station_01 --mqtt-broker central-server.local
```

2. **Central Server Setup**:
```bash
# Install manufacturing module
pip install -r requirements-manufacturing.txt

# Start MQTT broker
docker run -d -p 1883:1883 eclipse-mosquitto

# Run subscriber
python3 -m src.services.mqtt_subscriber

# Start dashboard
streamlit run dashboard/manufacturing_dashboard.py
```

3. **Integration with RAG**:
```python
# Add manufacturing module to RAG Enterprise
# src/api/app.py

from src.api.v1 import manufacturing

app.include_router(
    manufacturing.router,
    prefix="/api/v1/manufacturing",
    tags=["Manufacturing"]
)
```

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
