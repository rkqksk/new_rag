# Manufacturing System Operator Guide

**v7.1.0 - Advanced Manufacturing**
**LORA Vision + UR10e Robot Integration**

---

## 🎯 Quick Start (30 seconds)

```bash
# 1. Start manufacturing system
docker-compose -f docker-compose.manufacturing.yml up -d

# 2. Open dashboard
open http://localhost:8080/manufacturing

# 3. Check system health
curl http://localhost:8001/api/v1/manufacturing/health
```

**Status**: ✅ System Ready

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Daily Operations](#daily-operations)
3. [Vision Inspection](#vision-inspection)
4. [Robot Control](#robot-control)
5. [Safety Procedures](#safety-procedures)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## 1. System Overview

### Components

| Component | Purpose | Status Check |
|-----------|---------|--------------|
| LORA Vision | Defect detection | `GET /manufacturing/lora/metrics` |
| UR10e Robot | Pick and place | `GET /manufacturing/robot/status` |
| API Server | Control interface | `GET /manufacturing/health` |
| Dashboard | Real-time monitoring | http://localhost:8080 |

### Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Vision Inference | <50ms | <100ms |
| Robot Cycle Time | ~1.2s | <2.0s |
| Defect Accuracy | >95% | >90% |
| System Uptime | >99% | >95% |

---

## 2. Daily Operations

### Startup Procedure (5 minutes)

#### Step 1: System Check
```bash
# Check Docker services
docker-compose ps

# Expected: All services "Up"
```

#### Step 2: Connect Robot
```bash
# Connect to UR10e (simulation or physical)
curl -X POST http://localhost:8001/api/v1/manufacturing/robot/connect?simulation_mode=true

# Expected: {"success": true, "connected": true}
```

#### Step 3: Load LORA Adapter
```bash
# Switch to production adapter (e.g., PET bottles)
curl -X PUT http://localhost:8001/api/v1/manufacturing/lora/adapters/pet_bottles/activate

# Expected: {"success": true, "switch_time_ms": <200}
```

#### Step 4: Verify System Health
```bash
# Check all components
curl http://localhost:8001/api/v1/manufacturing/health

# Expected: {"status": "healthy"}
```

---

### Production Workflow

```
┌─────────────┐
│   Start     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Capture     │ ← Camera (30 FPS)
│ Image       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ LORA Vision │ ← Defect Detection (<50ms)
│ Inspection  │
└──────┬──────┘
       │
    Has Defect?
    │        │
   YES       NO
    │        │
    ▼        ▼
 Reject    Accept
  Bin       Bin
    │        │
    └────┬───┘
         │
         ▼
   Next Product
```

**Throughput**: ~3,000 products/hour (1.2s/product)

---

## 3. Vision Inspection

### Adapter Management

#### List Available Adapters
```bash
curl http://localhost:8001/api/v1/manufacturing/lora/adapters
```

**Response**:
```json
[
  {
    "product_type": "pet_bottles",
    "is_trained": true,
    "is_active": true,
    "file_size_mb": 10.8
  }
]
```

#### Switch Adapter (Product Change)
```bash
# Switch to aluminum cans
curl -X PUT http://localhost:8001/api/v1/manufacturing/lora/adapters/aluminum_cans/activate

# Expected switch time: <200ms
```

### Manual Inspection

#### Inspect Single Image
```bash
curl -X POST http://localhost:8001/api/v1/manufacturing/lora/inspect \
  -F "file=@test_bottle.jpg" \
  -F "product_type=pet_bottles" \
  -F "confidence_threshold=0.5"
```

**Response**:
```json
{
  "defects": [
    {
      "defect_type": "scratch",
      "confidence": 0.87,
      "bbox": {"x1": 120, "y1": 150, "x2": 180, "y2": 200}
    }
  ],
  "defect_count": 1,
  "inference_time_ms": 42
}
```

### Performance Metrics

```bash
# Get vision metrics
curl http://localhost:8001/api/v1/manufacturing/lora/metrics
```

**Key Metrics**:
- `total_inspections`: Total images processed
- `total_defects`: Total defects detected
- `avg_inference_ms`: Average inference time
- `current_product`: Currently loaded adapter

---

## 4. Robot Control

### Robot Status

```bash
# Get current status
curl http://localhost:8001/api/v1/manufacturing/robot/status
```

**Response**:
```json
{
  "state": "idle",
  "current_pose": [0.3, -0.1, 0.3, 0, 0, 0],
  "emergency_stop_active": false,
  "metrics": {
    "successful_cycles": 1250,
    "avg_cycle_time_ms": 1180
  }
}
```

### Manual Movement

#### Move to Position
```bash
curl -X POST http://localhost:8001/api/v1/manufacturing/robot/move \
  -H "Content-Type: application/json" \
  -d '{
    "x": 0.4,
    "y": 0.0,
    "z": 0.3,
    "rx": 0,
    "ry": 0,
    "rz": 0
  }'
```

#### Pick and Place
```bash
curl -X POST http://localhost:8001/api/v1/manufacturing/robot/pick_and_place \
  -H "Content-Type: application/json" \
  -d '{
    "pick_position": {"x": 0.4, "y": 0.1, "z": 0.05},
    "place_position": {"x": 0.3, "y": 0.4, "z": 0.1},
    "approach_height": 0.1
  }'
```

**Expected**: Cycle time ~1.2s

---

## 5. Safety Procedures

### Emergency Stop

#### Activate Emergency Stop
```bash
# IMMEDIATE STOP - ALL MOVEMENT HALTED
curl -X POST http://localhost:8001/api/v1/manufacturing/robot/emergency_stop
```

**Result**: Robot stops within <100ms

#### Reset Emergency Stop (After Verification)
```bash
# ONLY reset after manual safety verification
curl -X POST http://localhost:8001/api/v1/manufacturing/robot/reset_emergency_stop
```

⚠️ **IMPORTANT**: Always verify workspace is clear before resetting

### Position Validation

```bash
# Validate position before movement
curl -X POST http://localhost:8001/api/v1/manufacturing/safety/validate_position \
  -H "Content-Type: application/json" \
  -d '{"x": 0.5, "y": 0.0, "z": 0.3}'
```

**Safety Levels**:
- ✅ `SAFE`: Position safe, normal speed
- ⚠️ `WARNING`: Near boundary, reduced speed (50%)
- ⛔ `DANGER`: Very close to boundary, slow speed (25%)
- 🚫 `CRITICAL`: Out of bounds, movement blocked

### Safety Zones

| Zone | X Range (m) | Y Range (m) | Z Range (m) |
|------|-------------|-------------|-------------|
| **Safe** | 0.2 - 1.0 | -0.5 - 0.5 | 0.0 - 0.5 |
| **Warning** | ±50mm from bounds | ±50mm from bounds | ±50mm from min |
| **Danger** | ±20mm from bounds | ±20mm from bounds | ±20mm from min |

---

## 6. Troubleshooting

### Common Issues

#### Issue: Vision Inference Slow (>100ms)

**Symptoms**:
- Inference time > 100ms
- Throughput < 1000 products/hour

**Solutions**:
1. Check GPU utilization: `nvidia-smi`
2. Verify adapter is trained: `GET /lora/adapters`
3. Reduce image resolution (if acceptable)
4. Check system load: `docker stats`

---

#### Issue: Robot Not Responding

**Symptoms**:
- Robot state: `error` or `disconnected`
- Movement commands fail

**Solutions**:
1. Check connection:
   ```bash
   curl http://localhost:8001/api/v1/manufacturing/robot/status
   ```

2. Reconnect robot:
   ```bash
   curl -X POST http://localhost:8001/api/v1/manufacturing/robot/connect
   ```

3. Check UR10e IP address:
   ```bash
   ping 192.168.1.100  # Default IP
   ```

4. Verify emergency stop not active:
   ```bash
   # If emergency_stop_active: true
   curl -X POST .../reset_emergency_stop
   ```

---

#### Issue: Defects Not Detected

**Symptoms**:
- Known defects not detected
- Accuracy < 90%

**Solutions**:
1. Check correct adapter loaded:
   ```bash
   curl http://localhost:8001/api/v1/manufacturing/lora/metrics
   # Verify "current_product" matches
   ```

2. Verify confidence threshold:
   ```bash
   # Try lower threshold (e.g., 0.3)
   -F "confidence_threshold=0.3"
   ```

3. Check lighting conditions:
   - Consistent bright lighting
   - No shadows or glare

4. Retrain adapter:
   ```bash
   docker-compose exec lora-trainer \
     python scripts/train_lora_adapter.py --product pet_bottles
   ```

---

#### Issue: High False Positive Rate

**Symptoms**:
- Good products rejected
- Defect rate > 15%

**Solutions**:
1. Increase confidence threshold:
   ```bash
   -F "confidence_threshold=0.7"  # Increase from 0.5
   ```

2. Review training dataset:
   - Add more non-defect images
   - Balance defect/non-defect ratio (60:40)

3. Check camera focus and positioning

---

### Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Invalid position | Check coordinates within workspace |
| 500 | Robot error | Check robot connection and status |
| 503 | Service unavailable | Check Docker services running |

---

## 7. Maintenance

### Daily Maintenance (5 minutes)

- [ ] Check system health endpoint
- [ ] Review defect detection accuracy
- [ ] Verify robot cycle time < 2s
- [ ] Check error logs

```bash
# Daily health check script
./scripts/daily_health_check.sh
```

### Weekly Maintenance (30 minutes)

- [ ] Review performance metrics
- [ ] Check adapter file sizes
- [ ] Verify calibration accuracy
- [ ] Clean workspace and camera lens
- [ ] Review safety violations

```bash
# Weekly report
curl http://localhost:8001/api/v1/manufacturing/safety/report
```

### Monthly Maintenance (2 hours)

- [ ] Retrain adapters with new data
- [ ] Re-calibrate camera-robot transformation
- [ ] Update system software
- [ ] Full system backup

```bash
# Backup manufacturing data
./scripts/backup_manufacturing.sh
```

### LORA Adapter Training

#### Prepare Dataset
```bash
# Organize images and annotations
python scripts/prepare_dataset.py --product pet_bottles

# Verify dataset structure
ls data/manufacturing/datasets/pet_bottles/
# Expected:
# - train/images/ (500+ images)
# - train/labels/ (YOLO format)
# - val/images/ (100+ images)
# - val/labels/
```

#### Train Adapter
```bash
# Train new adapter (2-4 hours on GPU)
docker-compose exec lora-trainer \
  python scripts/train_lora_adapter.py \
  --product pet_bottles \
  --epochs 50 \
  --batch 16

# Expected output:
# - Adapter saved: data/manufacturing/models/lora_adapters/pet_bottles_v2.pth
# - Size: ~11MB
# - Training time: ~3 hours
```

#### Deploy Adapter
```bash
# Activate new adapter
curl -X PUT http://localhost:8001/api/v1/manufacturing/lora/adapters/pet_bottles/activate

# Test with sample images
curl -X POST .../lora/inspect -F "file=@test_image.jpg"
```

---

## 📊 Performance Dashboard

### Key Metrics to Monitor

| Metric | Monitor | Alert Threshold |
|--------|---------|-----------------|
| Vision FPS | Real-time | <10 FPS |
| Inference Time | Per inspection | >100ms |
| Defect Rate | Hourly | >10% |
| Robot Cycle Time | Per cycle | >2.0s |
| Emergency Stops | Daily | >3 per day |
| System Uptime | 24/7 | <99% |

### Log Files

```bash
# API logs
docker logs rag-api-manufacturing

# Robot logs
docker logs ur10e-simulator

# Training logs
ls data/manufacturing/training_logs/
```

---

## 📞 Support

### Contact Information

- **Technical Support**: manufacturing-support@company.com
- **Emergency**: +1-XXX-XXX-XXXX (24/7)
- **Documentation**: http://docs.company.com/manufacturing

### Report Issues

```bash
# Generate diagnostic report
./scripts/generate_diagnostics.sh

# Email report to support
```

---

## ✅ Checklist

### Before Production Run
- [ ] System health check passed
- [ ] Robot connected and calibrated
- [ ] Correct LORA adapter loaded
- [ ] Workspace clear and safe
- [ ] Emergency stop tested
- [ ] Lighting conditions optimal

### After Production Run
- [ ] Review metrics and performance
- [ ] Check for error logs
- [ ] Backup inspection data
- [ ] Clean workspace
- [ ] Disconnect robot (if needed)

---

**Version**: v7.1.0
**Last Updated**: 2025-11-11
**Next Review**: Monthly

**Safety First**: Always prioritize safety over production speed.
**When in doubt, STOP**: Activate emergency stop and contact support.
