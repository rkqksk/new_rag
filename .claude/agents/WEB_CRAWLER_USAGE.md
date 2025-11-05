# Universal Web Crawler Agent - Usage Guide

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Agent**: web-crawler (universal configuration-based crawler)

This guide provides practical examples for using the universal web-crawler agent to manage all 4 production crawlers.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Commands](#basic-commands)
3. [Site-Specific Examples](#site-specific-examples)
4. [Status Monitoring](#status-monitoring)
5. [Error Recovery](#error-recovery)
6. [Automated Scheduling](#automated-scheduling)
7. [Advanced Operations](#advanced-operations)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Python 3.11+
- Selenium, BeautifulSoup4, requests
- Chrome/ChromeDriver (for Selenium sites)
- Authenticated cookies.json (for freemold only)

### Basic Workflow
```bash
# 1. Activate the web-crawler agent
# (In Claude Code, just say: "Use web-crawler agent")

# 2. Start a crawler
"Crawl chunjinkorea"

# 3. Check status
"Status"

# 4. Stop if needed
"Stop chunjinkorea"
```

---

## Basic Commands

### Starting Crawlers

**Natural Language Commands** (agent understands these):
```
"Crawl chunjinkorea"
"Start onehago crawler"
"Begin freemold extraction"
"Launch jangup crawler"
"Start all crawlers"
```

**Site Keywords** (agent detects):
- Chunjinkorea: `chunjin`, `천진`
- Onehago: `onehago`, `원하고`, `one hago`
- Freemold: `freemold`, `프리몰드`, `free mold`
- Jangup: `jangup`, `장업`, `jang up`

### Stopping Crawlers

```
"Stop chunjinkorea"
"Kill onehago crawler"
"Stop all crawlers"
```

### Status Checks

```
"Status"                    # All 4 crawlers
"Chunjinkorea status"       # Single crawler
"Progress report"           # Detailed progress
"Check errors"              # Error summary
```

---

## Site-Specific Examples

### 1. Chunjinkorea (5,000 products)

**Characteristics**:
- Pattern: Single-pass (simple structure)
- Scale: 5,000 products
- Time: ~2 hours
- Error Policy: Strict (1 error = restart)

**Example Session**:
```
User: "Crawl chunjinkorea"

Agent:
✅ Starting chunjinkorea crawler...
📊 Configuration:
   - Pattern: Single-pass
   - Scale: 5,000 products
   - Time: ~2 hours
   - Error policy: Strict (1 error → restart)

[Executes crawl_chunjin_universal.py]

✅ Chunjinkorea crawler started
📝 Log: /tmp/chunjin_crawl.log
📁 Output: data/chunjinkorea/crawled/products_complete.jsonl
```

**Check Progress**:
```
User: "Chunjinkorea status"

Agent:
🌐 CHUNJINKOREA STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ● RUNNING
Progress: [2,345/5,000] (46.9%)
Rate: 0.7 products/second
ETA: 1.1 hours
Errors: 0
Last Activity: 3 seconds ago
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Output Format**:
```jsonl
{"product_id": "CH12345", "product_name": "50ml PET 병", "category": "CAP",
 "specifications": {"용량": "50ml", "재질": "PET"},
 "company": "천진코리아", "crawled_at": "2025-01-26T10:30:15"}
```

---

### 2. Onehago (2,011,553 products)

**Characteristics**:
- Pattern: Phase-based + Multi-worker (12 workers)
- Scale: 2,011,553 products
- Time: ~120 hours (5 days)
- Error Policy: Rate-based (>50% error rate → restart)

**Example Session**:
```
User: "Start onehago crawler"

Agent:
✅ Starting onehago crawler (Phase-based extraction)...

📊 ONEHAGO CONFIGURATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1 (URL Discovery):
   - Collect all product URLs
   - Output: product_urls_complete.jsonl
   - Time: ~3 hours

Phase 2 (Data Extraction):
   - Extract product details + images
   - Workers: 12 concurrent
   - Output: worker_XXXX_output.jsonl
   - Time: ~117 hours (5 days)

⚠️  NOTE: This is a LARGE-SCALE operation (2M+ products)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Starting Phase 1...

[Executes phase1_production_full.py]

✅ Onehago Phase 1 (URL discovery) started
📝 Log: /tmp/onehago_phase1.log
```

**Check Progress During Phase 1**:
```
User: "Onehago Phase 1 status"

Agent:
🌐 ONEHAGO - PHASE 1 (URL DISCOVERY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ● RUNNING
Progress: [1,234,567 / 2,011,553] (61.4%)
Rate: 114 URLs/second
ETA: 1.9 hours
Output: product_urls_complete.jsonl
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Start Phase 2 (after Phase 1 completes)**:
```
User: "Start onehago Phase 2"

Agent:
✅ Starting onehago Phase 2 (Multi-worker extraction)...

📊 PHASE 2 CONFIGURATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workers: 12 (optimal tested)
Batch Size: 1000 products/worker
Timeout: 30 seconds/product
Total Products: 2,011,553
Estimated Time: ~117 hours

[Executes onehago_orchestrator_continuous.py]

✅ 12-worker orchestrator started
📝 Log: /tmp/onehago_12workers_IMAGES.log
📁 Output: data/onehago/crawled/production/products_text_only/
```

**Monitor Worker Progress**:
```
User: "Onehago worker status"

Agent:
🌐 ONEHAGO - PHASE 2 (12-WORKER EXTRACTION)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Active Workers: 12/12

Worker 0090: [RUNNING] Batch 90 (90,000-91,000) → 456/1000 extracted
Worker 0091: [RUNNING] Batch 91 (91,000-92,000) → 723/1000 extracted
Worker 0092: [RUNNING] Batch 92 (92,000-93,000) → 201/1000 extracted
...
Worker 0101: [RUNNING] Batch 101 (101,000-102,000) → 889/1000 extracted

Overall Progress: [95,230 / 2,011,553] (4.7%)
Rate: 4.6 products/second
ETA: 115.2 hours
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Output Format**:
```jsonl
{
  "product_name": "50ml PET 원형병",
  "product_code": "WH-PET-50R",
  "specifications": {
    "코드": "WH-PET-50R",
    "용량": "50ml",
    "사이즈": "Ø40 x H100mm",
    "MOQ": "10,000개",
    "재질": "PET",
    "원산지": "한국"
  },
  "company_info": {
    "제조사": "주식회사 ABC",
    "담당": "홍길동"
  },
  "phone": "02-1234-5678",
  "fax": "02-1234-5679",
  "email": "contact@abc.com",
  "image_urls": [
    "https://cdn.onehago.com/products/WH-PET-50R_1.jpg",
    "https://cdn.onehago.com/products/WH-PET-50R_2.jpg"
  ],
  "image_count": 2,
  "detail_crawled": true,
  "detail_crawled_at": "2025-01-26T14:23:45",
  "crawl_metadata": {
    "worker_id": "worker_0090",
    "batch_id": "batch_00090",
    "extraction_time_ms": 8450
  }
}
```

---

### 3. Freemold (1,964 products)

**Characteristics**:
- Pattern: Phase-based + Cookie Authentication
- Scale: 1,964 products (A003 category)
- Time: ~3.3 hours
- Error Policy: Rate-based (>50% error rate → restart)

**Prerequisites**:
```bash
# Export cookies from authenticated browser session
# Save to: /Users/oypnus/Project/rag-enterprise/cookies.json

# Cookies expire weekly - refresh as needed
```

**Example Session**:
```
User: "Crawl freemold"

Agent:
✅ Starting freemold crawler (Phase-based + Auth)...

⚠️  AUTHENTICATION CHECK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cookie file: cookies.json
Status: ✅ Found (valid)
Last updated: 2025-01-26 (fresh)
Note: Refresh cookies weekly to prevent expiration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 FREEMOLD CONFIGURATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Category: A003 (Packaging/Wrapping)
Scale: 1,964 products
Pattern: Two-phase with authentication

Phase 1: URL discovery (~1 hour)
Phase 2: Detail extraction (~2.3 hours)

Total time: ~3.3 hours

Starting Phase 1...

[Executes freemold_cat2_phase1_discovery.py]

✅ Freemold Phase 1 (URL discovery) started
📝 Log: /tmp/freemold_phase1_A003_discovery.log
```

**Check Progress**:
```
User: "Freemold status"

Agent:
🌐 FREEMOLD - PHASE 1 (URL DISCOVERY A003)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ● RUNNING
Progress: [1,245 / 1,964] (63.4%)
Rate: 0.54 URLs/second
ETA: 22 minutes
Output: product_urls_A003_complete.jsonl
Authentication: ✅ Cookie-based (valid)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Start Phase 2**:
```
User: "Start freemold Phase 2"

Agent:
✅ Starting freemold Phase 2 (Detail extraction)...

[Executes freemold_phase2_hybrid.py]

📊 Extracting product details with images...
Rate: 0.16 products/second (6 sec/product)
ETA: ~2.3 hours

✅ Phase 2 started
📝 Log: /tmp/freemold_phase2_A003_extraction.log
📁 Output: data/freemold/crawled/products_text_A003_complete.jsonl
```

**Output Format**:
```jsonl
{
  "product_id": "FM12345",
  "product_name": "자동 포장기 - 롤형",
  "category": "A003",
  "specifications": {
    "모델": "APM-2000",
    "속도": "60포/분",
    "포장크기": "폭 100-300mm"
  },
  "company": "프리몰드",
  "images": {
    "image_urls": ["https://freemold.net/img/FM12345_1.jpg"],
    "image_count": 1
  },
  "detail_crawled": true,
  "detail_crawled_at": "2025-01-26T16:45:23"
}
```

---

### 4. Jangup (81,000 products)

**Characteristics**:
- Pattern: Single-pass
- Scale: 81,000 products
- Time: ~12 hours
- Error Policy: Strict (1 error = restart)

**Example Session**:
```
User: "Crawl jangup"

Agent:
✅ Starting jangup crawler...

📊 JANGUP CONFIGURATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pattern: Single-pass (stable structure)
Scale: 81,000 products
Rate: 1.9 products/second
Time: ~12 hours
Error Policy: Strict (1 error → restart)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Executes crawl_jangup_full_81k.py]

✅ Jangup crawler started
📝 Log: /tmp/jangup_full.log
📁 Output: data/jangup/crawled/products_complete.jsonl
```

**Check Progress**:
```
User: "Jangup status"

Agent:
🌐 JANGUP STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ● RUNNING
Progress: [45,230 / 81,000] (55.8%)
Rate: 1.9 products/second
ETA: 5.2 hours
Errors: 0 (strict policy)
Last Activity: 1 second ago
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Output Format**:
```jsonl
{
  "product_id": "JU81234",
  "product_name": "200ml HDPE 용기",
  "category": "BOTTLE",
  "specifications": {
    "용량": "200ml",
    "재질": "HDPE",
    "크기": "Ø55 x H120mm"
  },
  "company": "장업플라스틱",
  "crawled_at": "2025-01-26T18:12:34"
}
```

---

## Status Monitoring

### Unified Dashboard

**Command**: `"Status"` or `"Show all crawler status"`

**Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 UNIFIED CRAWLER STATUS DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 CHUNJINKOREA (천진코리아)
   Status: ● RUNNING
   Progress: [2,345/5,000] (46.9%)
   Rate: 0.7 products/sec | ETA: 1.1h
   Output: data/chunjinkorea/crawled/products_complete.jsonl

🌐 ONEHAGO (원하고)
   Phase 1: ✅ COMPLETED (2,011,553 URLs discovered)
   Phase 2: ● RUNNING
   Workers: 12/12 active
   Progress: [95,230 / 2,011,553] (4.7%)
   Rate: 4.6 products/sec | ETA: 115.2h
   Output: data/onehago/crawled/production/products_text_only/

🌐 FREEMOLD (프리몰드)
   Status: ● RUNNING (Phase 2 - Extraction)
   Progress: [1,234 / 1,964] (62.8%)
   Rate: 0.16 products/sec | ETA: 1.3h
   Output: data/freemold/crawled/products_text_A003_complete.jsonl
   Auth: ✅ Cookie-based (valid)

🌐 JANGUP (장업)
   Status: ● RUNNING
   Progress: [45,230 / 81,000] (55.8%)
   Rate: 1.9 products/sec | ETA: 5.2h
   Output: data/jangup/crawled/products_complete.jsonl

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 OVERALL SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Active Crawlers: 4/4
Total Progress: [144,039 / 2,098,517] (6.9%)
Total Target: 2,098,517 products
Estimated Completion: 2025-02-01 10:15:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Error Recovery

### Chunjinkorea & Jangup (Strict Policy)

**Behavior**: 1 error = immediate restart

**Example**:
```
[2025-01-26 10:30:45] [ERROR] Navigation failed: timeout on page 45
[2025-01-26 10:30:46] [ALERT] Error detected - initiating restart
[2025-01-26 10:30:46] [ACTION] Killing process: crawl_chunjin_universal.py
[2025-01-26 10:30:56] [ACTION] Process terminated, waiting 10 seconds
[2025-01-26 10:31:06] [ACTION] Restarting from checkpoint (progress.json)
[2025-01-26 10:31:07] [INFO] Crawler restarted - resuming from item 2,345
```

**User Action**: None required (auto-restart handles recovery)

### Onehago & Freemold (Rate-Based Policy)

**Behavior**: >50% error rate in last 100 operations → restart

**Example**:
```
[2025-01-26 14:23:15] [WARNING] Timeout on product 95,456 (attempt 1/3)
[2025-01-26 14:23:30] [WARNING] Timeout on product 95,456 (attempt 2/3)
[2025-01-26 14:23:45] [ERROR] Timeout on product 95,456 (attempt 3/3) - FAILED
[2025-01-26 14:23:45] [INFO] Error rate: 45/100 operations (45%) - WITHIN THRESHOLD
[2025-01-26 14:23:46] [INFO] Continuing... (threshold: 50%)
[2025-01-26 14:24:15] [INFO] Error rate improved: 25/100 operations (25%)
```

**Threshold Breach**:
```
[2025-01-26 15:45:23] [ERROR] Error rate: 52/100 operations (52%) - THRESHOLD BREACHED
[2025-01-26 15:45:24] [ALERT] Rate-based policy triggered - initiating restart
[2025-01-26 15:45:25] [ACTION] Saving checkpoint: progress.json
[2025-01-26 15:45:26] [ACTION] Killing processes: Python + Chrome
[2025-01-26 15:45:56] [ACTION] Cleanup complete (30s wait)
[2025-01-26 15:45:57] [ACTION] Restarting from checkpoint
[2025-01-26 15:46:02] [INFO] Crawler restarted - error rate reset
```

**User Commands**:
```
"Force restart onehago"        # Manual restart
"Reset error counter"          # Clear error tracking
"Continue despite errors"      # Override policy temporarily
```

---

## Automated Scheduling

### Install Cron Jobs

**One-Time Setup**:
```bash
cd /Users/oypnus/Project/rag-enterprise
bash scripts/install_crawler_cron.sh
```

**Output**:
```
══════════════════════════════════════════
🤖 Automated Crawler Cron Installation
══════════════════════════════════════════

📁 Project Directory: /Users/oypnus/Project/rag-enterprise

📝 Creating cron configuration...

✅ Cron jobs installed successfully!

══════════════════════════════════════════
📅 WEEKLY CRAWL SCHEDULE
══════════════════════════════════════════

Sunday:
  2:00 AM - Onehago Phase 1 starts (URL discovery)
  4:00 AM - Chunjinkorea crawler
  5:00 AM - Jangup crawler

Monday:
  2:00 AM - Onehago Phase 2 starts (data extraction)
  3:00 AM - Freemold Phase 1 (bi-weekly, even weeks)
  4:00 AM - Freemold Phase 2 (bi-weekly, even weeks)

══════════════════════════════════════════
📊 TOTAL WEEKLY PRODUCTS: 2,098,517
══════════════════════════════════════════

✅ Automated crawling is now active!

💡 Commands:
   View jobs:   crontab -l
   Remove jobs: crontab -r
   Edit jobs:   crontab -e

📝 Log files location: /tmp/*_weekly.log
```

### View Scheduled Jobs

```bash
crontab -l
```

### Monitor Cron Logs

```bash
# Chunjinkorea
tail -f /tmp/chunjin_weekly.log

# Onehago
tail -f /tmp/onehago_phase1_weekly.log
tail -f /tmp/onehago_phase2_weekly.log

# Freemold
tail -f /tmp/freemold_phase1_weekly.log
tail -f /tmp/freemold_phase2_weekly.log

# Jangup
tail -f /tmp/jangup_weekly.log
```

---

## Advanced Operations

### Start All Crawlers Simultaneously

**Command**: `"Start all crawlers"`

**Agent Behavior**:
```
✅ STARTING ALL 4 CRAWLERS (PARALLEL LAUNCH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/4] Chunjinkorea...
✅ Launched (PID: 12345) | Log: /tmp/chunjin_crawl.log

[2/4] Onehago Phase 1...
✅ Launched (PID: 12346) | Log: /tmp/onehago_phase1.log

[3/4] Freemold Phase 1...
✅ Launched (PID: 12347) | Log: /tmp/freemold_phase1_A003_discovery.log

[4/4] Jangup...
✅ Launched (PID: 12348) | Log: /tmp/jangup_full.log

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL CRAWLERS ACTIVE
Total Target: 2,098,517 products
Estimated Completion: 5-7 days
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Stop All Crawlers

**Command**: `"Stop all crawlers"`

### Resume Interrupted Crawlers

**Scenario**: Crawler stopped unexpectedly

**Command**: `"Resume chunjinkorea"` or `"Crawl chunjinkorea"`

### Validate Output Data

**Command**: `"Validate onehago data"`

---

## Troubleshooting

### Issue 1: Crawler Won't Start

**Symptoms**: Python process exits immediately

**Solution**:
```bash
pip3 install selenium beautifulsoup4 requests lxml
```

### Issue 2: Freemold Authentication Failure

**Symptoms**: Session expired (401 Unauthorized)

**Solution**: Refresh cookies.json from authenticated browser session

### Issue 3: Onehago Worker Crashes

**Diagnosis**: Connection refused when >15 workers active

**Solution**: Orchestrator auto-reduces to 12 workers

### Issue 4: Slow Crawl Performance

**Solution**: Restart crawler to clear Chrome memory

### Issue 5: Disk Space Running Out

**Solution**: Archive old data, compress images, clean logs

---

## Summary

### Key Takeaways

1. **Universal Agent**: One agent manages all 4 crawlers
2. **Natural Language**: Simple commands like "Crawl onehago"
3. **Auto-Recovery**: Error policies handle failures automatically
4. **Checkpointing**: Resume from last saved state
5. **Automated Scheduling**: Weekly cron jobs
6. **Unified Monitoring**: Single dashboard

### Quick Reference

| Command | Action |
|---------|--------|
| `"Crawl {site}"` | Start crawler |
| `"Status"` | Show all status |
| `"Stop {site}"` | Stop crawler |
| `"Start all"` | Launch all 4 |
| `"Validate {site} data"` | Check quality |

### Total Scale

- **Total Products**: 2,098,517
- **Total Sites**: 4
- **Total Time**: 5-7 days (first run), weekly updates
- **Storage**: ~500 GB (with images)

---

**For more details, see**:
- [AGENT_TEMPLATE.md](AGENT_TEMPLATE.md) - Pattern documentation
- [web-crawler.md](web-crawler.md) - Universal agent source
- [install_crawler_cron.sh](../scripts/install_crawler_cron.sh) - Cron setup

**Last Updated**: 2025-01-26
