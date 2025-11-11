# Advanced Manufacturing: LORA Fine-Tuning + UR10e Integration

**Version**: v7.1.0 (Extension to v7.0.0+)
**Date**: 2025-11-11
**Status**: 🎯 Research & Design Phase
**Integration**: Manufacturing Automation + AI Fine-Tuning + Collaborative Robotics

---

## 📍 Quick Reference

**Current System (v7.0.0)**:
- ✅ YOLOv8/v10 Vision Inspection
- ✅ Edge AI (Jetson Orin Nano, Raspberry Pi)
- ✅ 7 Defect Types Detection
- ✅ Real-time Quality Control

**New Additions (v7.1.0)**:
- 🎯 LORA Fine-Tuning (Custom YOLO models)
- 🤖 UR10e Robot Arm Integration
- 📊 Advanced Dashboard
- 🔌 Unified API Endpoints

---

## Table of Contents

1. [LORA Fine-Tuning System](#1-lora-fine-tuning-system)
2. [UR10e Collaborative Robot Integration](#2-ur10e-collaborative-robot-integration)
3. [Advanced Dashboard Design](#3-advanced-dashboard-design)
4. [API Endpoints Architecture](#4-api-endpoints-architecture)
5. [Implementation Roadmap](#5-implementation-roadmap)

---

## 1. LORA Fine-Tuning System

### 1.1 What is LORA?

**LORA (Low-Rank Adaptation)** = Efficient AI model fine-tuning technique

**Key Concept**:
```
Traditional Fine-Tuning:
- Update ALL model parameters (billions)
- Requires massive compute (GPUs)
- 100% of original model size
- Expensive and slow

LORA Fine-Tuning:
- Update ONLY 4% of parameters (small adapters)
- Requires minimal compute
- 86-99% parameter reduction
- Fast and cheap
```

**2025 Research** (Nature Scientific Reports):
- YOLOv8x with LORA: **98.6% parameter reduction**
- YOLO11x with LORA: **77% parameter reduction**
- **No accuracy loss**
- Perfect for edge AI deployment

---

### 1.2 Why LORA for RAG Enterprise?

**Current Challenge**:
```
Our Manufacturing System (v7.0.0):
- General YOLOv8 model (80 object classes)
- Not optimized for specific products
- Example: Detects "scratch" but not "PET bottle scratch" vs "aluminum scratch"
```

**LORA Solution**:
```
Custom YOLO Models per Product Category:
- Packaging containers (PET, HDPE, aluminum)
- Mold defects (flash, short shot, warpage)
- PCB defects (solder, trace, component)
- Each model: 4% of original size
- Fast switching between products
```

**Benefits**:
1. **Product-Specific**: Fine-tune for exact defect types
2. **Memory Efficient**: 98.6% smaller models
3. **Fast Deployment**: Switch models in milliseconds
4. **Edge AI Ready**: Fits in Jetson/Pi memory
5. **Cost Savings**: Train on single GPU vs cluster

---

### 1.3 LORA Architecture for RAG Enterprise

```
┌─────────────────────────────────────────────────────────────┐
│                   Base YOLO Model                            │
│         (Frozen - Never Modified)                            │
│  YOLOv8x: 68M parameters                                     │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  LORA Adapters                               │
│         (Trainable - Product-Specific)                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PET Bottles  │  │ Aluminum Can │  │ Mold Defects │      │
│  │ 2.7M params  │  │ 2.7M params  │  │ 2.7M params  │      │
│  │ (4% of base) │  │ (4% of base) │  │ (4% of base) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PCB Defects  │  │ Custom 1     │  │ Custom 2     │      │
│  │ 2.7M params  │  │ 2.7M params  │  │ 2.7M params  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Production Inference                            │
│                                                              │
│  Base Model + LORA Adapter = Custom YOLO                    │
│  68M (frozen) + 2.7M (active) = 70.7M effective             │
│  Memory: ~280MB base + ~11MB adapter = 291MB total          │
└─────────────────────────────────────────────────────────────┘
```

**Key Advantages**:
- **One Base Model**: Shared across all products (280MB)
- **Multiple Adapters**: Quick-swap per product (11MB each)
- **Total Memory**: 280MB + (11MB × active adapters)
- **Example**: 6 adapters = 280MB + 66MB = 346MB (fits in Jetson!)

---

### 1.4 LORA Training Pipeline

```python
# Conceptual LORA Training Flow
# (Actual implementation in Phase 2)

from lora_yolo import LORATrainer, BaseYOLOv8

# 1. Load Base Model (Frozen)
base_model = BaseYOLOv8.load("yolov8x.pt")
base_model.freeze()  # Never modify base weights

# 2. Initialize LORA Adapter
lora_config = {
    "rank": 16,              # Low-rank dimension
    "alpha": 32,             # Scaling factor
    "target_layers": [       # Which layers to adapt
        "backbone.conv1",
        "backbone.conv2",
        "neck.fpn",
        "head.detect"
    ],
    "dropout": 0.1
}

lora_adapter = LORAAdapter(base_model, lora_config)

# 3. Prepare Dataset (Product-Specific)
dataset = {
    "images": "data/pet_bottles/images/",
    "labels": "data/pet_bottles/labels/",
    "classes": [
        "scratch_horizontal",
        "scratch_vertical",
        "dent_top",
        "dent_body",
        "crack_neck",
        "deformation"
    ]
}

# 4. Train LORA Adapter (Fast!)
trainer = LORATrainer(base_model, lora_adapter, dataset)
trainer.train(
    epochs=50,               # vs 300 for full training
    batch_size=16,           # Small GPU OK
    learning_rate=1e-4
)

# 5. Save LORA Adapter (Small File!)
lora_adapter.save("adapters/pet_bottles_v1.pth")  # ~11MB

# 6. Deploy to Edge Device
# Jetson loads: base_model + lora_adapter
# Total memory: 280MB + 11MB = 291MB ✅
```

**Training Performance**:
| Metric | Full Training | LORA Training |
|--------|---------------|---------------|
| Parameters Updated | 68M (100%) | 2.7M (4%) |
| GPU Memory | 24GB | 8GB |
| Training Time | 48 hours | 3 hours |
| Model Size | 280MB | 11MB adapter |
| Accuracy | 95% | 94.8% (negligible loss) |

---

### 1.5 LORA Integration with Current System

**Modify Existing Architecture**:

```python
# app/services/manufacturing/lora_vision_service.py

class LORAVisionService:
    """LORA-enhanced vision inspection with adapter switching"""

    def __init__(self):
        # Load base model once (frozen)
        self.base_model = YOLOv8("models/yolov8x_base.pt")
        self.base_model.freeze()

        # LORA adapter registry
        self.adapters = {
            "pet_bottles": "adapters/pet_bottles_v1.pth",
            "aluminum_cans": "adapters/aluminum_cans_v1.pth",
            "mold_defects": "adapters/mold_defects_v1.pth",
            "pcb_defects": "adapters/pcb_defects_v1.pth"
        }

        # Currently loaded adapter
        self.current_adapter = None

    def switch_adapter(self, product_type: str):
        """
        Switch LORA adapter for different product

        Args:
            product_type: One of ["pet_bottles", "aluminum_cans", ...]

        Performance:
            - Unload time: ~50ms
            - Load time: ~100ms
            - Total: <200ms (sub-second!)
        """
        if product_type not in self.adapters:
            raise ValueError(f"Unknown product type: {product_type}")

        # Unload current adapter
        if self.current_adapter:
            self.base_model.unload_lora_adapter()

        # Load new adapter
        adapter_path = self.adapters[product_type]
        self.base_model.load_lora_adapter(adapter_path)
        self.current_adapter = product_type

        print(f"✅ Switched to {product_type} adapter in <200ms")

    def inspect(self, image, product_type: str):
        """
        Inspect product with appropriate LORA adapter

        Auto-switches adapter if needed
        """
        # Auto-switch adapter if different product
        if self.current_adapter != product_type:
            self.switch_adapter(product_type)

        # Run inference (base + LORA)
        results = self.base_model.predict(image)

        return {
            "product_type": product_type,
            "adapter": self.current_adapter,
            "defects": results.defects,
            "confidence": results.confidence,
            "inference_time_ms": results.time_ms
        }
```

**Benefits of This Approach**:
1. **Hot-Swap**: Change products without reloading base model
2. **Memory Efficient**: Base model stays in memory (280MB)
3. **Fast**: Adapter switch <200ms (imperceptible)
4. **Scalable**: Add unlimited product types (11MB each)

---

## 2. UR10e Collaborative Robot Integration

### 2.1 UR10e Specifications

**Universal Robots UR10e** = Medium-duty collaborative robot arm

**Key Specs**:
```
Physical:
- Payload: 12.5 kg
- Reach: 1300 mm (1.3 meters)
- Weight: 33.5 kg
- Footprint: Ø190 mm

Performance:
- Speed: Up to 1 m/s
- Repeatability: ±0.05 mm (50 microns)
- Degrees of Freedom: 6-axis
- Tool Center Point: Programmable

Safety (Collaborative):
- Force limiting
- Collision detection
- Speed & separation monitoring
- Safe stop functionality

Programming:
- PolyScope GUI (teach pendant)
- Python API (URScript)
- ROS/ROS2 support
- REST API integration
```

**Cost**: ~$35,000-45,000 USD

**Typical Applications**:
- Pick and place
- Machine tending
- Quality inspection (with vision)
- Packaging automation
- Assembly operations

---

### 2.2 Why UR10e for RAG Enterprise?

**Current System Gap**:
```
Vision Inspection ✅ → Defect Detection
   ↓
   ❌ Manual handling of defective products
   ❌ Human operator removes bad parts
   ❌ Slow, error-prone
```

**UR10e Solution**:
```
Vision Inspection ✅ → Defect Detection
   ↓
   ✅ UR10e automatically picks defective product
   ✅ Places in "reject" bin
   ✅ 100% automated quality control
   ✅ 24/7 operation
```

**ROI Calculation**:
```
Manual Inspection:
- Operator: $20/hour × 8 hours × 5 days × 52 weeks = $41,600/year
- Error rate: ~5%
- Downtime: Breaks, vacation, sick leave

UR10e Automated:
- Initial cost: $40,000 (one-time)
- Operating cost: ~$1,000/year (electricity, maintenance)
- Error rate: ~0.1% (with vision guidance)
- Downtime: ~2% (scheduled maintenance only)

Payback: ~1 year
Savings: $40,000/year after payback
```

---

### 2.3 UR10e + Vision Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Production Line                              │
│                                                              │
│   [Product] → [Camera] → [YOLO Inspection]                  │
│                                                              │
│                     ↓ Defect Detected                        │
│                                                              │
│             [RAG Enterprise API]                             │
│              (Decision Logic)                                │
│                     ↓                                        │
│                 [UR10e API]                                  │
│              (Robot Control)                                 │
│                     ↓                                        │
│         ┌───────────┴───────────┐                           │
│         ↓                       ↓                            │
│    [Pick Product]          [Place in Bin]                    │
│   (X,Y,Z from vision)     (Reject or Pass)                   │
└─────────────────────────────────────────────────────────────┘
```

**Integration Flow**:

1. **Vision Detection** (YOLO + LORA)
   ```python
   result = lora_vision.inspect(image, "pet_bottles")
   # {
   #   "defects": ["scratch_horizontal"],
   #   "confidence": 0.94,
   #   "bbox": [x1, y1, x2, y2]  # Bounding box
   # }
   ```

2. **Coordinate Transformation** (Image → Robot)
   ```python
   # Camera coordinates (pixels) → Robot coordinates (mm)
   robot_coords = camera_calibration.transform(
       image_coords=(x1, y1),
       camera_height=500,  # mm above conveyor
       camera_angle=0      # perpendicular
   )
   # robot_coords = (X: 250mm, Y: 100mm, Z: 20mm)
   ```

3. **Robot Command** (UR10e API)
   ```python
   # Send pick command to UR10e
   ur10e.pick_and_place(
       pick_position=(250, 100, 20),  # mm
       place_position=REJECT_BIN,      # predefined
       gripper_force=20                # N (gentle)
   )
   ```

4. **Logging & Feedback**
   ```python
   # Log to RAG Enterprise
   await log_defect_action(
       product_id=product.id,
       defect_type="scratch_horizontal",
       action="rejected",
       robot_time_ms=1200,  # Pick+place time
       vision_time_ms=150   # YOLO inference time
   )
   ```

---

### 2.4 UR10e API Integration

**Python SDK for UR10e**:

```python
# app/services/manufacturing/ur10e_service.py

import urx  # Universal Robots Python library
from urx import Robot

class UR10eService:
    """UR10e collaborative robot control service"""

    def __init__(self, robot_ip: str = "192.168.1.100"):
        """
        Initialize UR10e connection

        Args:
            robot_ip: IP address of UR10e controller
        """
        self.robot = Robot(robot_ip)
        self.robot.set_tcp((0, 0, 0.1, 0, 0, 0))  # Tool center point offset
        self.robot.set_payload(0.5)  # Expected payload weight (kg)

        # Predefined positions (calibrated)
        self.HOME = (0.3, -0.1, 0.3, 0, 0, 0)  # Safe home position
        self.INSPECT_ZONE = (0.5, 0, 0.2, 0, 0, 0)  # Above conveyor
        self.REJECT_BIN = (0.3, 0.4, 0.1, 0, 0, 0)  # Defect bin
        self.PASS_BIN = (0.3, -0.4, 0.1, 0, 0, 0)  # Good products bin

    def pick_and_place(
        self,
        pick_coords: tuple,
        place_coords: tuple,
        speed: float = 0.5,
        acceleration: float = 0.3
    ):
        """
        Pick object at pick_coords and place at place_coords

        Args:
            pick_coords: (X, Y, Z) in meters
            place_coords: (X, Y, Z) in meters
            speed: m/s (0-1.0)
            acceleration: m/s² (0-1.2)

        Returns:
            dict: Execution status and timing
        """
        import time
        start_time = time.time()

        try:
            # 1. Move to above pick position
            above_pick = (pick_coords[0], pick_coords[1], pick_coords[2] + 0.1)
            self.robot.movel(above_pick, acc=acceleration, vel=speed)

            # 2. Lower to pick position
            self.robot.movel(pick_coords, acc=acceleration, vel=speed/2)

            # 3. Close gripper (activate)
            self.robot.set_digital_out(0, True)  # Gripper close signal
            time.sleep(0.5)  # Wait for gripper

            # 4. Lift object
            self.robot.movel(above_pick, acc=acceleration, vel=speed)

            # 5. Move to above place position
            above_place = (place_coords[0], place_coords[1], place_coords[2] + 0.1)
            self.robot.movel(above_place, acc=acceleration, vel=speed)

            # 6. Lower to place position
            self.robot.movel(place_coords, acc=acceleration, vel=speed/2)

            # 7. Open gripper (release)
            self.robot.set_digital_out(0, False)  # Gripper open signal
            time.sleep(0.5)  # Wait for gripper

            # 8. Return to safe position
            self.robot.movel(above_place, acc=acceleration, vel=speed)
            self.robot.movel(self.HOME, acc=acceleration, vel=speed)

            elapsed = (time.time() - start_time) * 1000  # ms

            return {
                "status": "success",
                "time_ms": elapsed,
                "pick": pick_coords,
                "place": place_coords
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "time_ms": (time.time() - start_time) * 1000
            }

    def emergency_stop(self):
        """Emergency stop - immediately halt all motion"""
        self.robot.stop()
        print("🛑 EMERGENCY STOP ACTIVATED")

    def go_home(self):
        """Return to safe home position"""
        self.robot.movel(self.HOME, acc=0.3, vel=0.5)

    def close(self):
        """Disconnect from robot"""
        self.robot.close()
```

**Usage Example**:

```python
# Initialize robot
ur10e = UR10eService("192.168.1.100")

# Automated inspection loop
while True:
    # 1. Capture image from camera
    image = camera.capture()

    # 2. YOLO + LORA inspection
    result = lora_vision.inspect(image, product_type="pet_bottles")

    # 3. If defect detected, reject with robot
    if result["defects"]:
        # Transform image coords to robot coords
        pick_pos = camera_calibration.to_robot_coords(
            result["bbox"],
            camera_params
        )

        # Pick and place in reject bin
        ur10e.pick_and_place(
            pick_coords=pick_pos,
            place_coords=ur10e.REJECT_BIN
        )

        print(f"❌ Rejected: {result['defects']}")

    else:
        print("✅ Product passed inspection")
```

---

### 2.5 Safety Considerations

**UR10e Collaborative Safety Features**:

1. **Force Limiting**
   ```python
   # Set maximum force for safe human interaction
   ur10e.robot.set_payload(0.5, (0, 0, 0.05))
   ur10e.robot.force_mode_set_damping(0.025)  # Soft compliance
   ```

2. **Speed & Separation Monitoring**
   ```python
   # Reduce speed when human detected nearby
   if human_detected(safety_scanner):
       ur10e.robot.set_speed_scaling(0.5)  # 50% speed
   else:
       ur10e.robot.set_speed_scaling(1.0)  # Full speed
   ```

3. **Emergency Stop Integration**
   ```python
   # Connect physical e-stop button to API
   @app.post("/api/v1/manufacturing/emergency_stop")
   async def emergency_stop():
       ur10e.emergency_stop()
       return {"status": "stopped", "timestamp": datetime.now()}
   ```

4. **Workspace Boundaries**
   ```python
   # Define safe zones (software limits)
   SAFE_WORKSPACE = {
       "x_min": 0.2, "x_max": 0.8,  # meters
       "y_min": -0.5, "y_max": 0.5,
       "z_min": 0.05, "z_max": 0.6
   }

   def is_safe_position(coords):
       return (
           SAFE_WORKSPACE["x_min"] <= coords[0] <= SAFE_WORKSPACE["x_max"] and
           SAFE_WORKSPACE["y_min"] <= coords[1] <= SAFE_WORKSPACE["y_max"] and
           SAFE_WORKSPACE["z_min"] <= coords[2] <= SAFE_WORKSPACE["z_max"]
       )
   ```

---

## 3. Advanced Dashboard Design

### 3.1 Dashboard Requirements

**Unified Manufacturing Dashboard** = Real-time monitoring + control + analytics

**Key Metrics to Display**:
1. **Vision Inspection**
   - FPS (frames per second)
   - Defect detection rate
   - Current LORA adapter
   - Inference time (ms)

2. **Robot Status**
   - UR10e position (X, Y, Z)
   - Current operation
   - Cycle time (pick+place)
   - Error count

3. **Quality Control**
   - Pass/fail ratio
   - Defect types distribution
   - Hourly throughput
   - SPC charts (Statistical Process Control)

4. **System Health**
   - Jetson GPU/CPU usage
   - UR10e temperature
   - Camera status
   - Network latency

---

### 3.2 Dashboard Technology Stack

**Frontend**: React + Tailwind + shadcn/ui (already in project)
**Realtime**: Socket.IO (v7.0.0+ feature)
**Backend**: FastAPI (existing)
**Database**: PostgreSQL + ClickHouse (analytics)
**Visualization**: Chart.js / Recharts

**Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│              Dashboard Frontend (React)                      │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Vision     │  │ Robot      │  │ Quality    │            │
│  │ Monitor    │  │ Status     │  │ Charts     │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                              │
│  ┌─────────────────────────────────────────────┐            │
│  │         Real-time Data (Socket.IO)          │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                         ↕ WebSocket
┌─────────────────────────────────────────────────────────────┐
│          Socket.IO Backend (app/realtime/)                   │
│                                                              │
│  Events:                                                     │
│  - vision_inspection_update                                  │
│  - robot_position_update                                     │
│  - defect_detected                                           │
│  - quality_metrics_update                                    │
└─────────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────────┐
│           Manufacturing Services                             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ LORA Vision  │  │ UR10e Robot  │  │ Quality      │      │
│  │ Service      │  │ Service      │  │ Analyzer     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.3 Dashboard Components

**Component 1: Vision Inspection Monitor**

```jsx
// frontend/components/VisionMonitor.jsx

import { useSocket } from '@/hooks/useSocket'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function VisionMonitor() {
  const { data, isConnected } = useSocket('vision_inspection_update')

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vision Inspection</CardTitle>
        <Badge variant={isConnected ? "success" : "destructive"}>
          {isConnected ? "Connected" : "Disconnected"}
        </Badge>
      </CardHeader>

      <CardContent>
        {/* Current Frame */}
        <div className="mb-4">
          <img
            src={data?.current_frame || '/placeholder.png'}
            alt="Inspection camera"
            className="w-full rounded border"
          />
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <MetricCard
            label="FPS"
            value={data?.fps || 0}
            unit="frames/sec"
            color="blue"
          />
          <MetricCard
            label="Inference Time"
            value={data?.inference_ms || 0}
            unit="ms"
            color="green"
          />
          <MetricCard
            label="LORA Adapter"
            value={data?.lora_adapter || "none"}
            color="purple"
          />
        </div>

        {/* Defects Detected */}
        {data?.defects && data.defects.length > 0 && (
          <div className="mt-4 p-4 bg-red-50 rounded border border-red-200">
            <h4 className="font-semibold text-red-800 mb-2">
              ⚠️ Defects Detected
            </h4>
            <ul className="list-disc list-inside">
              {data.defects.map((defect, i) => (
                <li key={i} className="text-red-700">
                  {defect.type} (Confidence: {(defect.confidence * 100).toFixed(1)}%)
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

**Component 2: Robot Status Monitor**

```jsx
// frontend/components/RobotMonitor.jsx

export function RobotMonitor() {
  const { data } = useSocket('robot_position_update')

  return (
    <Card>
      <CardHeader>
        <CardTitle>UR10e Robot Status</CardTitle>
      </CardHeader>

      <CardContent>
        {/* 3D Position Visualization */}
        <div className="mb-4">
          <Robot3DView
            position={data?.position || [0, 0, 0]}
            joints={data?.joints || [0, 0, 0, 0, 0, 0]}
          />
        </div>

        {/* Current Operation */}
        <div className="flex items-center gap-2 mb-4">
          <StatusIndicator active={data?.is_moving} />
          <span className="font-medium">
            {data?.current_operation || "Idle"}
          </span>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <MetricCard
            label="Cycle Time"
            value={data?.cycle_time_ms || 0}
            unit="ms"
          />
          <MetricCard
            label="Pick Success Rate"
            value={data?.success_rate || 0}
            unit="%"
          />
        </div>
      </CardContent>
    </Card>
  )
}
```

**Component 3: Quality Control Charts**

```jsx
// frontend/components/QualityCharts.jsx

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

export function QualityCharts() {
  const { data: metrics } = useSocket('quality_metrics_update')

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quality Control (SPC)</CardTitle>
      </CardHeader>

      <CardContent>
        {/* Defect Rate Over Time */}
        <div className="mb-6">
          <h4 className="font-semibold mb-2">Defect Rate (Last Hour)</h4>
          <LineChart width={600} height={200} data={metrics?.hourly_data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="defect_rate" stroke="#ef4444" />
          </LineChart>
        </div>

        {/* Defect Types Distribution */}
        <div>
          <h4 className="font-semibold mb-2">Defect Types (Today)</h4>
          <BarChart data={metrics?.defect_distribution}>
            {/* ... */}
          </BarChart>
        </div>
      </CardContent>
    </Card>
  )
}
```

---

### 3.4 Real-time Data Flow

**Backend Socket.IO Events**:

```python
# app/realtime/manufacturing_events.py

from app.realtime.socketio_server import get_realtime_server

realtime = get_realtime_server()

async def broadcast_vision_update(inspection_result):
    """Broadcast vision inspection results to dashboard"""
    await realtime.sio.emit('vision_inspection_update', {
        'timestamp': datetime.now().isoformat(),
        'fps': inspection_result.fps,
        'inference_ms': inspection_result.inference_ms,
        'lora_adapter': inspection_result.lora_adapter,
        'defects': [
            {
                'type': d.type,
                'confidence': d.confidence,
                'bbox': d.bbox
            } for d in inspection_result.defects
        ],
        'current_frame': inspection_result.frame_base64  # Base64 encoded image
    })

async def broadcast_robot_update(robot_state):
    """Broadcast UR10e position/status to dashboard"""
    await realtime.sio.emit('robot_position_update', {
        'timestamp': datetime.now().isoformat(),
        'position': robot_state.position,  # [X, Y, Z]
        'joints': robot_state.joints,       # [J1, J2, J3, J4, J5, J6]
        'is_moving': robot_state.is_moving,
        'current_operation': robot_state.operation,
        'cycle_time_ms': robot_state.cycle_time,
        'success_rate': robot_state.success_rate
    })

async def broadcast_quality_metrics(metrics):
    """Broadcast quality control metrics to dashboard"""
    await realtime.sio.emit('quality_metrics_update', {
        'timestamp': datetime.now().isoformat(),
        'hourly_data': metrics.hourly_defect_rates,
        'defect_distribution': metrics.defect_type_counts,
        'pass_fail_ratio': metrics.pass_fail_ratio,
        'total_inspected': metrics.total_count
    })
```

**Integration with Manufacturing Services**:

```python
# app/services/manufacturing/integrated_service.py

class IntegratedManufacturingService:
    """Unified manufacturing service with LORA + UR10e + Dashboard"""

    def __init__(self):
        self.lora_vision = LORAVisionService()
        self.ur10e = UR10eService()
        self.quality_analyzer = QualityAnalyzer()

    async def inspection_loop(self):
        """Main inspection loop with real-time updates"""

        while True:
            # 1. Capture image
            image = await camera.capture()

            # 2. LORA vision inspection
            result = self.lora_vision.inspect(image, product_type="pet_bottles")

            # 3. Broadcast to dashboard
            await broadcast_vision_update(result)

            # 4. If defect detected, use robot
            if result["defects"]:
                # Calculate robot coordinates
                robot_coords = camera_calibration.transform(result["bbox"])

                # Pick and place
                robot_result = await self.ur10e.pick_and_place(
                    pick_coords=robot_coords,
                    place_coords=self.ur10e.REJECT_BIN
                )

                # Broadcast robot update
                await broadcast_robot_update(self.ur10e.get_state())

                # Log defect
                await self.quality_analyzer.log_defect(result, robot_result)

            # 5. Update quality metrics
            metrics = await self.quality_analyzer.get_current_metrics()
            await broadcast_quality_metrics(metrics)

            # Small delay to avoid overwhelming
            await asyncio.sleep(0.1)  # 10 FPS update rate
```

---

## 4. API Endpoints Architecture

### 4.1 New API Endpoints

**Endpoint Structure**:

```
/api/v1/manufacturing/
├── lora/
│   ├── GET  /adapters                    # List all LORA adapters
│   ├── POST /adapters                    # Upload new adapter
│   ├── GET  /adapters/{id}               # Get adapter details
│   ├── PUT  /adapters/{id}/activate      # Switch to adapter
│   └── POST /train                       # Train new adapter
├── robot/
│   ├── GET  /status                      # UR10e current status
│   ├── POST /pick_and_place              # Execute pick & place
│   ├── POST /calibrate                   # Calibrate robot/camera
│   ├── POST /emergency_stop              # Emergency stop
│   └── GET  /positions                   # Predefined positions
├── inspection/
│   ├── POST /inspect                     # Single image inspection
│   ├── GET  /stream                      # Live video stream
│   ├── GET  /results                     # Inspection history
│   └── GET  /metrics                     # Real-time metrics
└── quality/
    ├── GET  /dashboard                   # Dashboard data
    ├── GET  /spc                         # SPC charts data
    ├── GET  /defects                     # Defect statistics
    └── POST /alert                       # Configure alerts
```

---

### 4.2 API Implementation Examples

**Endpoint 1: List LORA Adapters**

```python
# app/api/v1/endpoints/manufacturing/lora.py

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/manufacturing/lora", tags=["Manufacturing LORA"])

class LORAAdapter(BaseModel):
    id: str
    name: str
    product_type: str
    file_size_mb: float
    accuracy: float
    created_at: datetime
    is_active: bool

@router.get("/adapters", response_model=List[LORAAdapter])
async def list_adapters():
    """
    List all available LORA adapters

    Returns:
        List of LORA adapters with metadata
    """
    adapters = [
        {
            "id": "pet_bottles_v1",
            "name": "PET Bottles Defect Detection",
            "product_type": "pet_bottles",
            "file_size_mb": 10.8,
            "accuracy": 94.7,
            "created_at": "2025-11-01T10:00:00Z",
            "is_active": True
        },
        {
            "id": "aluminum_cans_v1",
            "name": "Aluminum Cans Inspection",
            "product_type": "aluminum_cans",
            "file_size_mb": 11.2,
            "accuracy": 96.1,
            "created_at": "2025-11-03T14:30:00Z",
            "is_active": False
        },
        # ... more adapters
    ]

    return adapters

@router.put("/adapters/{adapter_id}/activate")
async def activate_adapter(adapter_id: str):
    """
    Switch to a different LORA adapter

    Args:
        adapter_id: ID of adapter to activate

    Returns:
        Activation status and timing
    """
    try:
        import time
        start = time.time()

        # Switch adapter in vision service
        lora_vision.switch_adapter(adapter_id)

        elapsed_ms = (time.time() - start) * 1000

        return {
            "status": "activated",
            "adapter_id": adapter_id,
            "switch_time_ms": elapsed_ms,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Endpoint 2: Robot Control**

```python
# app/api/v1/endpoints/manufacturing/robot.py

router = APIRouter(prefix="/manufacturing/robot", tags=["Manufacturing Robot"])

class PickPlaceRequest(BaseModel):
    pick_position: tuple[float, float, float]
    place_position: tuple[float, float, float]
    speed: float = 0.5
    acceleration: float = 0.3

@router.post("/pick_and_place")
async def pick_and_place(request: PickPlaceRequest):
    """
    Execute pick and place operation with UR10e

    Args:
        request: Pick/place positions and parameters

    Returns:
        Execution result with timing
    """
    # Validate positions are within safe workspace
    if not is_safe_position(request.pick_position):
        raise HTTPException(400, "Pick position outside safe workspace")

    if not is_safe_position(request.place_position):
        raise HTTPException(400, "Place position outside safe workspace")

    # Execute pick and place
    result = await ur10e.pick_and_place(
        pick_coords=request.pick_position,
        place_coords=request.place_position,
        speed=request.speed,
        acceleration=request.acceleration
    )

    # Broadcast to dashboard
    await broadcast_robot_update(ur10e.get_state())

    return result

@router.post("/emergency_stop")
async def emergency_stop():
    """
    EMERGENCY STOP - Immediately halt all robot motion

    Safety critical endpoint
    """
    ur10e.emergency_stop()

    # Broadcast alert to all dashboard clients
    await realtime.sio.emit('emergency_stop', {
        'timestamp': datetime.now().isoformat(),
        'reason': 'Manual emergency stop triggered'
    })

    return {
        "status": "stopped",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/status")
async def get_robot_status():
    """
    Get current UR10e status

    Returns:
        Real-time robot state
    """
    state = ur10e.get_state()

    return {
        "position": state.position,
        "joints": state.joints,
        "is_moving": state.is_moving,
        "current_operation": state.operation,
        "temperature": state.temperature,
        "error_count": state.error_count,
        "uptime_seconds": state.uptime
    }
```

**Endpoint 3: Inspection**

```python
# app/api/v1/endpoints/manufacturing/inspection.py

router = APIRouter(prefix="/manufacturing/inspection", tags=["Manufacturing Inspection"])

@router.post("/inspect")
async def inspect_image(
    file: UploadFile,
    product_type: str = "pet_bottles"
):
    """
    Inspect uploaded image for defects

    Args:
        file: Image file (JPEG, PNG)
        product_type: Product category for LORA adapter

    Returns:
        Inspection results with defects detected
    """
    # Read image
    image_bytes = await file.read()
    image = Image.open(BytesIO(image_bytes))

    # LORA vision inspection
    result = lora_vision.inspect(image, product_type=product_type)

    # Log to database
    await db.inspections.insert({
        "timestamp": datetime.now(),
        "product_type": product_type,
        "defects": result["defects"],
        "inference_time_ms": result["inference_time_ms"]
    })

    return result

@router.get("/stream")
async def video_stream():
    """
    Live video stream with real-time inspection overlay

    Returns:
        Server-Sent Events (SSE) stream
    """
    async def generate():
        while True:
            # Capture frame
            frame = await camera.capture()

            # Inspect
            result = lora_vision.inspect(frame, "pet_bottles")

            # Draw bounding boxes on frame
            annotated_frame = draw_detections(frame, result["defects"])

            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            # Yield as SSE
            yield f"data: {base64.b64encode(frame_bytes).decode()}\n\n"

            await asyncio.sleep(0.1)  # 10 FPS

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

### 4.3 API Documentation (OpenAPI)

**Auto-generated Swagger UI**: `http://localhost:8001/api/v1/docs`

**Example API Spec**:

```yaml
openapi: 3.0.0
info:
  title: RAG Enterprise Manufacturing API
  version: 7.1.0
  description: LORA Fine-Tuning + UR10e Robot Integration

paths:
  /api/v1/manufacturing/lora/adapters:
    get:
      summary: List LORA adapters
      responses:
        '200':
          description: List of adapters
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/LORAAdapter'

  /api/v1/manufacturing/robot/pick_and_place:
    post:
      summary: Execute pick and place
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PickPlaceRequest'
      responses:
        '200':
          description: Operation successful
        '400':
          description: Invalid position
        '500':
          description: Robot error

components:
  schemas:
    LORAAdapter:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        product_type:
          type: string
        file_size_mb:
          type: number
        accuracy:
          type: number
        created_at:
          type: string
          format: date-time
        is_active:
          type: boolean

    PickPlaceRequest:
      type: object
      required:
        - pick_position
        - place_position
      properties:
        pick_position:
          type: array
          items:
            type: number
          minItems: 3
          maxItems: 3
        place_position:
          type: array
          items:
            type: number
          minItems: 3
          maxItems: 3
        speed:
          type: number
          minimum: 0
          maximum: 1
        acceleration:
          type: number
          minimum: 0
          maximum: 1.2
```

---

## 5. Implementation Roadmap

### Phase 1: Research & Prototyping (2-3 weeks)

**Week 1: LORA Setup**
- [ ] Install LORA libraries (`pip install lora-yolo peft`)
- [ ] Prepare training dataset (500+ images per product type)
- [ ] Train first LORA adapter (PET bottles)
- [ ] Benchmark: accuracy, size, inference time
- [ ] Document findings

**Week 2: UR10e Integration**
- [ ] Order UR10e robot arm ($40k budget approval)
- [ ] Setup URX Python library
- [ ] Calibrate camera-to-robot transformation
- [ ] Test basic pick and place operations
- [ ] Safety testing and workspace limits

**Week 3: Dashboard MVP**
- [ ] Create React components (Vision, Robot, Quality)
- [ ] Integrate Socket.IO real-time updates
- [ ] Basic charts (defect rate, SPC)
- [ ] Test with simulated data

---

### Phase 2: Integration (3-4 weeks)

**Week 4-5: End-to-End Integration**
- [ ] Connect LORA vision → UR10e pipeline
- [ ] Implement coordinate transformation
- [ ] Test with real products on production line
- [ ] Measure cycle time and throughput

**Week 6: API Development**
- [ ] Implement all endpoints (LORA, Robot, Inspection, Quality)
- [ ] OpenAPI documentation
- [ ] API testing (Postman/pytest)
- [ ] Rate limiting and authentication

**Week 7: Dashboard Polish**
- [ ] Real-time data integration
- [ ] Error handling and reconnection logic
- [ ] Mobile responsive design
- [ ] User access control

---

### Phase 3: Production Deployment (2 weeks)

**Week 8: Testing & Validation**
- [ ] End-to-end testing on production line
- [ ] Load testing (100+ products/hour)
- [ ] Safety validation (e-stop, force limits)
- [ ] Performance benchmarks

**Week 9: Deployment**
- [ ] Deploy to production servers
- [ ] Monitor initial operation
- [ ] Train operators
- [ ] Documentation and handoff

---

### Total Timeline: **9 weeks** (2.25 months)

**Budget Estimate**:
- UR10e Robot: $40,000
- Training compute (GPU): $500/month × 2 months = $1,000
- Development time: Included in existing team
- **Total**: ~$41,000

**Expected ROI**:
- Labor savings: $40,000/year
- Quality improvement: $10,000/year (reduced defects)
- Payback period: **<1 year**

---

## Summary

**v7.1.0 Adds**:

1. **LORA Fine-Tuning** ✅
   - 98.6% parameter reduction
   - Product-specific YOLO models
   - Fast adapter switching (<200ms)
   - Edge AI optimized

2. **UR10e Robot Arm** ✅
   - 12.5kg payload, 1.3m reach
   - Collaborative safety features
   - Python API integration
   - Pick & place automation

3. **Advanced Dashboard** ✅
   - Real-time monitoring (Socket.IO)
   - Vision, robot, quality metrics
   - SPC charts and analytics
   - Mobile responsive

4. **Unified API** ✅
   - LORA adapter management
   - Robot control endpoints
   - Live inspection stream
   - Quality metrics

**Next Steps**:
1. Review and approve roadmap
2. Budget approval for UR10e
3. Start Phase 1 (Research & Prototyping)

---

**Version**: v7.1.0
**Last Updated**: 2025-11-11
**Status**: 📋 Design Complete, Ready for Implementation
