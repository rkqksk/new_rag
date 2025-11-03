# Onehago Pipeline Real-Time Monitor - Usage Guide

**Real-time dashboard for monitoring all Onehago pipeline components**

---

## Quick Start

Open a new terminal tab and run:

```bash
cd /Users/oypnus/Project/rag-enterprise
bash scripts/monitor_onehago_pipeline.sh
```

**Default refresh**: 5 seconds
**Custom refresh**: `bash scripts/monitor_onehago_pipeline.sh 10` (for 10 seconds)

---

## What It Monitors

### 1. **Validation Daemon** 🔵
- Running status (PID)
- Total validated products
- Pass/fail statistics
- Repair success rate
- Recent activity log

### 2. **Phase 2 Crawling** 🟣
- Total products extracted
- Category 2 (packaging) count
- Success/failure rates
- `detail_crawled` status
- Disk usage

### 3. **Image Download Workers** 🟡
- Active worker count
- Products processed
- Images downloaded/failed
- Progress percentage
- Disk usage and file counts

### 4. **System Resources** 🟢
- Disk space available
- Memory usage (macOS vm_stat)
- Overall system health

---

## Display Features

### Color-Coded Sections
- **Blue** = Validation Daemon
- **Magenta** = Phase 2 Crawling
- **Yellow** = Image Workers
- **Green** = System Resources

### Status Indicators
- ✅ Success/Completed
- ❌ Failed
- ⚠️ Warning
- 🔄 In Progress
- ⏳ Pending
- 🔧 Repaired

### Auto-Refresh
- Updates every N seconds (default: 5)
- Shows last update timestamp
- Press **Ctrl+C** to exit

---

## Sample Output

```
╔════════════════════════════════════════════════════════════════════════════════╗
║             ONEHAGO PIPELINE REAL-TIME MONITOR                                 ║
╚════════════════════════════════════════════════════════════════════════════════╝
Last Update: 2025-11-02 14:30:45 | Refresh: 5s | Press Ctrl+C to exit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  VALIDATION DAEMON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Status: ● RUNNING
  PID: 12345

  Statistics:
    Total Validated:  150,234
    ✓ Passed:         148,012
    ✗ Failed:         2,222
    🔧 Repaired:      1,998
    ⚠  Repair Failed: 224

  Rates:
    Pass Rate:        98.5%
    Repair Success:   89.9%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 2 CRAWLING (Text Extraction)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Output Directory: .../products_text_only
  Worker Files:     90
  Batch Files:      232

  Products Extracted:
    Total:            235,123
    Category 2:       20,464 (packaging)

  Extraction Status:
    ✓ Success:        217,968
    ✗ Failed:         17,155
    Success Rate:     92.7%

  Storage:
    Disk Usage:       1.2GB

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  IMAGE DOWNLOAD WORKERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Active Workers:   4
  PIDs:             23456 23457 23458 23459

  Overall Progress:
    Products:         5,116 / 20,464
    ✓ Downloaded:     78,432
    ✗ Failed:         234
    ⊘ Skipped:        1,234
    Progress:         25.0%

  Storage:
    Disk Usage:       8.2GB
    Product Folders:  5,116
    Image Files:      78,432

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SYSTEM RESOURCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Disk Available:   450GB
  Disk Usage:       65%

Refreshing in 5 seconds... (Ctrl+C to exit)
```

---

## Troubleshooting

### Monitor Not Updating
```bash
# Check if script is executable
ls -l scripts/monitor_onehago_pipeline.sh

# Make executable if needed
chmod +x scripts/monitor_onehago_pipeline.sh
```

### Missing Validation Daemon
If you see "Status: ● STOPPED", start the daemon:
```bash
nohup python3 scripts/onehago_validation_daemon.py > /dev/null 2>&1 &
```

### No Image Workers Running
Launch workers:
```bash
bash scripts/launch_image_workers.sh 4
```

### Permission Errors
```bash
# Fix permissions
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

---

## Integration with Other Tools

### Monitor Specific Logs
While monitoring dashboard is running, open another terminal:

```bash
# Validation daemon log
tail -f /tmp/onehago_validation_daemon.log

# Image worker logs
tail -f /tmp/onehago_image_worker_0000.log
tail -f /tmp/onehago_image_worker_0001.log

# Phase 2 crawling log
tail -f /tmp/onehago_12workers_IMAGES.log
```

### Check Worker Progress Files
```bash
# Validation daemon state
cat /tmp/onehago_validation_daemon_state.json | python3 -m json.tool

# Image worker progress
cat data/onehago/images/category_2/worker_0000_progress.json | python3 -m json.tool
```

### Quick Status Checks
```bash
# Check all running processes
ps aux | grep -E "validation_daemon|image_worker|orchestrator"

# Count extracted products
wc -l data/onehago/crawled/production/products_text_only/*.jsonl

# Count category 2 products
grep -r '"category_id": 2' data/onehago/crawled/production/products_text_only/ | wc -l

# Count downloaded images
find data/onehago/images/category_2 -type f -name "*.jpg" | wc -l
```

---

## Performance Tuning

### Refresh Interval Optimization

**Fast Update (3 seconds)** - High system load
```bash
bash scripts/monitor_onehago_pipeline.sh 3
```

**Normal (5 seconds)** - Balanced (default)
```bash
bash scripts/monitor_onehago_pipeline.sh
```

**Relaxed (10 seconds)** - Low system impact
```bash
bash scripts/monitor_onehago_pipeline.sh 10
```

**Very Relaxed (30 seconds)** - Minimal load
```bash
bash scripts/monitor_onehago_pipeline.sh 30
```

---

## Exit and Cleanup

### Stop Monitoring
- Press **Ctrl+C** in the monitor terminal
- Monitor stops, background workers continue running

### Stop All Workers
```bash
# Stop validation daemon
pkill -f onehago_validation_daemon

# Stop image workers
pkill -f onehago_image_worker

# Stop Phase 2 crawling
pkill -f onehago_orchestrator_continuous
```

---

## Tips for Efficient Monitoring

1. **Use multiple tabs**:
   - Tab 1: Real-time monitor
   - Tab 2: Specific log tailing
   - Tab 3: Manual commands

2. **Adjust refresh based on phase**:
   - Active crawling: 5 seconds
   - Validation only: 10 seconds
   - Overnight monitoring: 30 seconds

3. **Monitor disk space**:
   - Category 2 images: ~31 GB total
   - Keep at least 50 GB free

4. **Check for stuck workers**:
   - If progress stops for >5 minutes
   - Check specific worker logs
   - Restart if needed

---

## Related Documentation

- **Background Workers**: `scripts/README_BACKGROUND_WORKERS.md`
- **Validation Daemon**: Source in `scripts/onehago_validation_daemon.py`
- **Image Workers**: Source in `scripts/onehago_image_worker.py`
- **Worker Launcher**: Source in `scripts/launch_image_workers.sh`

---

**Created**: 2025-11-02
**Version**: 1.0
**Refresh**: Auto-updates every N seconds
