# Onehago Background Workers System

Complete background worker architecture for autonomous data validation, repair, and image downloads.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 2 Extraction                        │
│     (12 workers extracting product text & image URLs)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │   Validation Daemon (Background)   │
         │  - Monitors Phase 2 output folder  │
         │  - Validates products in real-time │
         │  - Auto-repairs failed products    │
         │  - Runs independently 24/7         │
         └───────────────┬───────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  Image Download Workers (N=4-8)    │
         │  - Download category 2 images      │
         │  - Parallel workers (I/O bound)    │
         │  - Resume capability               │
         │  - Rate limited, respectful        │
         └────────────────────────────────────┘
```

## Components

### 1. Validation Daemon (`onehago_validation_daemon.py`)

**Purpose**: Real-time validation and automatic repair of Phase 2 extracted data

**Features**:
- File system monitoring with `watchdog` library
- Detects new/modified Phase 2 output files
- Validates each product against quality criteria
- Automatically re-crawls failed/incomplete products
- Runs independently in background without blocking Phase 2
- Graceful shutdown handling (Ctrl+C)

**Validation Criteria**:
```python
Required fields: product_id, product_name, specifications, company_info, image_urls, image_count
Min specifications: 2 fields (코드, 용량, 사이즈, MOQ, 재질, 원산지)
Min company info: 1 field (제조사, 담당)
Min images: 1 valid HTTP URL
Image count must match actual image_urls array length
```

**Usage**:
```bash
# Foreground (with logs)
python3 scripts/onehago_validation_daemon.py

# Background (recommended)
nohup python3 scripts/onehago_validation_daemon.py > /dev/null 2>&1 &

# Monitor logs
tail -f /tmp/onehago_validation_daemon.log

# Check progress
cat /tmp/onehago_validation_daemon_state.json

# Stop daemon
pkill -f onehago_validation_daemon
```

**Output**:
- Repaired products: `data/onehago/crawled/production/repaired/repaired_*.jsonl`
- State file: `/tmp/onehago_validation_daemon_state.json`
- Log file: `/tmp/onehago_validation_daemon.log`

---

### 2. Image Download Workers (`onehago_image_worker.py`)

**Purpose**: Parallel image downloads for category 2 (packaging) products

**Features**:
- Worker-based parallelization (4-8 workers recommended)
- Each worker processes different product range
- Resume capability (skip already downloaded)
- Rate limiting (100ms between images, 200ms between products)
- Retry logic with exponential backoff
- Graceful shutdown handling
- Per-worker progress tracking

**Architecture**:
```
Total: 20,464 category 2 products
Worker 0: Products 0-5,116      (25%)
Worker 1: Products 5,116-10,232  (25%)
Worker 2: Products 10,232-15,348 (25%)
Worker 3: Products 15,348-20,464 (25%)
```

**Usage**:
```bash
# Single worker (all products)
python3 scripts/onehago_image_worker.py 0

# Single worker (specific range)
python3 scripts/onehago_image_worker.py 0 0 5116

# Background worker
nohup python3 scripts/onehago_image_worker.py 0 0 5116 > /dev/null 2>&1 &

# Monitor worker logs
tail -f /tmp/onehago_image_worker_0000.log
```

**Output Structure**:
```
data/onehago/images/category_2/
├── {product_id_1}/
│   ├── metadata.json           # Product metadata
│   ├── img_01_abc123.jpg       # Image 1
│   ├── img_02_def456.jpg       # Image 2
│   └── ...
├── {product_id_2}/
│   └── ...
└── worker_XXXX_progress.json   # Worker progress
```

---

### 3. Image Workers Launcher (`launch_image_workers.sh`)

**Purpose**: Easy launch of multiple parallel image workers

**Features**:
- Automatically calculates product ranges
- Launches N workers in background
- Shows progress monitoring commands
- Configurable worker count

**Usage**:
```bash
# Launch 4 workers (default)
bash scripts/launch_image_workers.sh

# Launch 8 workers (faster)
bash scripts/launch_image_workers.sh 8

# Custom worker count
bash scripts/launch_image_workers.sh <N>
```

**Example Output**:
```
🚀 ONEHAGO IMAGE DOWNLOAD WORKERS LAUNCHER
==========================================

📊 Configuration:
   Total category 2 products: 20,464
   Number of workers: 4
   Products per worker: ~5,116

📁 Source: .../products_text_only
📁 Output: .../images/category_2/

🔄 Launching 4 workers in background...

📦 Worker 0: Products 0 - 5116
   ✅ Started (PID: 12345)
   📝 Log: /tmp/onehago_image_worker_0000.log

📦 Worker 1: Products 5116 - 10232
   ✅ Started (PID: 12346)
   📝 Log: /tmp/onehago_image_worker_0001.log
...
```

---

## Complete Workflow

### Step 1: Start Validation Daemon

```bash
# Install watchdog if needed
pip3 install watchdog

# Start daemon in background
nohup python3 scripts/onehago_validation_daemon.py > /dev/null 2>&1 &

# Verify it's running
ps aux | grep onehago_validation_daemon

# Monitor logs
tail -f /tmp/onehago_validation_daemon.log
```

Expected output:
```
[2025-11-02 10:00:00] [INFO] 🚀 ONEHAGO VALIDATION DAEMON STARTED
[2025-11-02 10:00:00] [INFO] Watch directory: .../products_text_only
[2025-11-02 10:00:00] [INFO] 📋 Processing existing files...
[2025-11-02 10:00:05] [INFO] ✅ Processed 150 existing files
[2025-11-02 10:00:05] [INFO] 👀 Starting file system monitor...
[2025-11-02 10:00:05] [INFO] ✅ Daemon running in background
```

### Step 2: Wait for Phase 2 Completion

Monitor Phase 2 extraction:
```bash
# Check Phase 2 progress
tail -f /tmp/onehago_12workers_IMAGES.log

# Check extracted product count
wc -l data/onehago/crawled/production/products_text_only/worker_*.jsonl
wc -l data/onehago/crawled/production/products_text_only/batch_*.jsonl
```

Wait until Phase 2 has extracted sufficient category 2 products.

### Step 3: Verify Category 2 Data

```bash
# Analyze category 2 products
python3 scripts/analyze_category2_images.py
```

Expected output:
```
📊 Analysis Results
====================================
Total products processed: 235,123
Category 2 products: 20,464 (8.7%)

📸 Image Statistics:
   Total images: 316,824
   Average images per product: 15.8
   Max images per product: 45
   Min images per product: 1

💾 Estimated Download Size:
   Total images: 316,824
   Estimated size (100KB/image): 31.68 GB
   Estimated time (1 image/sec): 88 hours
```

### Step 4: Validate Category 2 Data Quality

```bash
# Run comprehensive validation
python3 scripts/validate_category2_data.py
```

Expected output:
```
📊 Validation Summary
====================================
Total products: 20,464
✅ VALID: 20,464 (100.00%)
⚠️  WARNING: 0 (0.00%)
❌ CRITICAL: 0 (0.00%)

📦 Packaging Insights:
   Top materials: PET (4,019), PP (1,172), Glass (748)
   Top capacities: 30ml, 50ml, 100ml
   Origin: 68% Korea, 8.5% China
```

### Step 5: Launch Image Workers

```bash
# Recommended: 4-8 workers for optimal throughput
bash scripts/launch_image_workers.sh 4

# Monitor workers
tail -f /tmp/onehago_image_worker_0000.log
tail -f /tmp/onehago_image_worker_0001.log

# Check download progress
ls -lh data/onehago/images/category_2/ | wc -l
du -sh data/onehago/images/category_2/
```

### Step 6: Monitor Progress

```bash
# Check worker status
ps aux | grep onehago_image_worker

# Check validation daemon
ps aux | grep onehago_validation_daemon

# View worker progress
cat data/onehago/images/category_2/worker_0000_progress.json

# View daemon progress
cat /tmp/onehago_validation_daemon_state.json

# Check download statistics
echo "Products downloaded:"
ls -1 data/onehago/images/category_2/ | wc -l

echo "Images downloaded:"
find data/onehago/images/category_2/ -name "*.jpg" -o -name "*.png" | wc -l

echo "Disk usage:"
du -sh data/onehago/images/category_2/
```

---

## Performance Tuning

### Worker Count Optimization

**4 Workers** (Conservative):
- ~88 hours total (22 hours per worker)
- Lower server load
- Recommended for initial run

**8 Workers** (Aggressive):
- ~44 hours total (5.5 hours per worker)
- Higher server load
- Better network utilization
- Recommended if server handles it well

**Rule of thumb**:
```
Download time = (Total images / (Workers × Images per second))
             = (316,824 / (4 × 1)) = ~88 hours
             = (316,824 / (8 × 1)) = ~44 hours
```

### Rate Limiting

Current settings:
```python
DELAY_BETWEEN_DOWNLOADS = 0.1  # 100ms (10 images/sec per worker)
DELAY_BETWEEN_PRODUCTS = 0.2    # 200ms between products
```

Adjust for server tolerance:
- Lower delays = faster downloads, higher server load
- Higher delays = slower downloads, more respectful

### Retry Settings

```python
MAX_RETRIES = 3                 # 3 attempts per image
TIMEOUT = 30                    # 30 seconds per request
```

---

## Troubleshooting

### Validation Daemon Issues

**Issue**: Daemon not detecting new files
```bash
# Check if watchdog is installed
pip3 list | grep watchdog

# Check daemon logs
tail -100 /tmp/onehago_validation_daemon.log

# Restart daemon
pkill -f onehago_validation_daemon
nohup python3 scripts/onehago_validation_daemon.py > /dev/null 2>&1 &
```

**Issue**: High CPU usage
```bash
# Check file processing rate
grep "Processing file" /tmp/onehago_validation_daemon.log | tail -20

# Reduce processing speed (add delay in daemon code if needed)
```

### Image Worker Issues

**Issue**: Worker stopped unexpectedly
```bash
# Check worker logs
tail -100 /tmp/onehago_image_worker_0000.log

# Resume worker (same command)
nohup python3 scripts/onehago_image_worker.py 0 0 5116 > /dev/null 2>&1 &
```

**Issue**: Download failures
```bash
# Check network connectivity
curl -I https://www.onehago.com

# Check failed images in logs
grep "Failed" /tmp/onehago_image_worker_*.log

# Increase timeout or retries in worker code
```

**Issue**: Disk space full
```bash
# Check disk usage
df -h

# Check image directory size
du -sh data/onehago/images/category_2/

# Clean up if needed (after backup)
```

---

## File Locations

### Scripts
```
scripts/onehago_validation_daemon.py    # Background validation daemon
scripts/onehago_image_worker.py          # Image download worker
scripts/launch_image_workers.sh          # Worker launcher
scripts/analyze_category2_images.py      # Pre-flight analysis
scripts/validate_category2_data.py       # Data quality validation
scripts/onehago_repair_worker.py         # Manual repair tool (batch mode)
```

### Data Directories
```
data/onehago/crawled/production/products_text_only/  # Phase 2 output (watch dir)
data/onehago/crawled/production/repaired/            # Repaired products
data/onehago/images/category_2/                      # Downloaded images
```

### Logs & State
```
/tmp/onehago_validation_daemon.log          # Daemon log
/tmp/onehago_validation_daemon_state.json   # Daemon state
/tmp/onehago_image_worker_XXXX.log          # Worker logs
data/onehago/images/category_2/worker_XXXX_progress.json  # Worker progress
```

---

## Key Features

### 1. Autonomous Operation
- Validation daemon runs 24/7 without intervention
- Automatic detection and repair of data quality issues
- Image workers resume from interruptions

### 2. Parallel Processing
- Validation daemon + N image workers run concurrently
- Each image worker processes different product range
- Maximum network and I/O utilization

### 3. Fault Tolerance
- Resume capability for all components
- Retry logic with exponential backoff
- Graceful shutdown handling
- State persistence across restarts

### 4. Resource Management
- Rate limiting prevents server overload
- Configurable worker count for load balancing
- Independent operation prevents blocking

### 5. Monitoring & Debugging
- Comprehensive logging for all components
- Progress tracking with JSON state files
- Real-time statistics in logs

---

## Estimated Timeline

### Phase 2 Extraction
- **Duration**: ~160 hours (12 workers, 1.92M products)
- **Completion**: Ongoing

### Data Validation & Repair
- **Duration**: Real-time (parallel with Phase 2)
- **Coverage**: 100% of extracted products
- **Repair rate**: ~5 seconds per failed product

### Image Downloads (Category 2 Only)
- **4 workers**: ~88 hours (22 hours per worker)
- **8 workers**: ~44 hours (5.5 hours per worker)
- **Total size**: ~31 GB
- **Total images**: 316,824

### Total Pipeline
```
Phase 2 → Validation → Images
~160h  → Real-time  → ~44-88h (parallel with Phase 2 end)
```

---

## Next Steps

1. ✅ Start validation daemon (already covered above)
2. ✅ Wait for Phase 2 to extract more category 2 products
3. ✅ Validate category 2 data quality
4. ✅ Launch image workers (4-8 workers recommended)
5. ⏳ Monitor progress and handle any issues
6. ⏳ Verify final image downloads (all products downloaded, no failures)

---

**Created**: 2025-11-02
**Author**: Claude Code
**Version**: 1.0
