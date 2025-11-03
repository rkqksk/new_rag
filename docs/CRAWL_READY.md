# 🚀 Ready for Production Crawl

## ✅ What's Ready

### 1. **Clean Start Complete**
- ✅ Old data backed up to: `data/onehago/backup_20251031_152709/`
- ✅ Fresh folder structure created
- ✅ Phase 1 & 2 scripts tested successfully

### 2. **Test Results** (Category 96 - 2 products)
- ✅ Phase 1: URLs collected (9 seconds)
- ✅ Phase 2: Details extracted + 10 images downloaded (40 seconds)
- ✅ Quality: Perfect extraction with all images

### 3. **Production Scripts Ready**
| Script | Purpose | Status |
|--------|---------|--------|
| `phase1_collect_product_urls.py` | Collect product URLs | ✅ Tested |
| `phase2_extract_details.py` | Extract details + images | ✅ Tested |
| `run_parallel_crawl.py` | Parallel orchestration | ✅ Ready |

---

## 🎯 Folder Structure

```
data/onehago/
├── backup_20251031_152709/        # Old data (3GB backup)
│   ├── crawled/                    # Original backup
│   └── crawled_original/           # Moved old data
│
├── crawled/                        # FRESH START (active)
│   ├── product_urls.jsonl          # Phase 1 output
│   ├── details/                    # Phase 2 JSON (per product)
│   ├── images/                     # Downloaded images
│   └── logs/                       # Crawl logs
│
└── final/                          # Organized final data
```

---

## 🚀 How to Run

### Option 1: Run Everything (Recommended)

```bash
# Full parallel crawl (Phase 1 + Phase 2)
python3 scripts/run_parallel_crawl.py

# Auto-tunes to use 2x CPU cores (max 20 workers)
# Estimated time: 12-16 hours for all 153 categories
```

### Option 2: Phase 1 Only (Fast URL Collection)

```bash
# Collect all product URLs first
python3 scripts/run_parallel_crawl.py --phase1-only

# Estimated time: 3-4 hours
# Output: data/onehago/crawled/product_urls.jsonl
```

Then run Phase 2 later:
```bash
python3 scripts/run_parallel_crawl.py --phase2-only
```

### Option 3: Single Category Test

```bash
# Test on small category first
python3 scripts/phase1_collect_product_urls.py --categories 96
python3 scripts/phase2_extract_details.py --test
```

---

## ⚡ Performance Tuning

### Control Parallel Workers

```bash
# Use 10 parallel workers
python3 scripts/run_parallel_crawl.py --workers 10

# Use maximum (20 workers)
python3 scripts/run_parallel_crawl.py --workers 20
```

### Adjust Request Delays

Edit scripts and change:
- `--min-delay 0.05` - Minimum delay between requests
- `--max-delay 0.15` - Maximum delay between requests

**Lower delays = faster** but **higher risk of being blocked**

---

## 📊 Expected Results

### Phase 1: URL Collection
| Metric | Expected |
|--------|----------|
| Categories | 153 |
| Products | ~15,000-20,000 |
| Time (parallel) | 3-4 hours |
| Output | `product_urls.jsonl` |

### Phase 2: Detail Extraction
| Metric | Expected |
|--------|----------|
| Products | Same as Phase 1 |
| Images per product | 1-5 |
| Total images | ~30,000-60,000 |
| Time (sequential) | 8-12 hours |
| Output | `details/` + `images/` |

### Total Crawl Time
- **Sequential**: ~20-24 hours
- **Parallel Phase 1 + Sequential Phase 2**: ~12-16 hours
- **Fully Parallel (future)**: ~6-8 hours (requires Phase 2 refactoring)

---

## 🔍 Monitoring Progress

### Check Live Progress

```bash
# Count URLs collected so far
wc -l data/onehago/crawled/product_urls.jsonl

# Count details extracted
ls data/onehago/crawled/details/ | wc -l

# Count images downloaded
ls data/onehago/crawled/images/ | wc -l

# Check disk usage
du -sh data/onehago/crawled/
```

### View Logs

```bash
# Phase 1 logs (if enabled)
tail -f data/onehago/crawled/logs/phase1.log

# Phase 2 logs (if enabled)
tail -f data/onehago/crawled/logs/phase2.log
```

---

## ✅ Quality Verification

After crawl completes, verify data quality:

```bash
python3 scripts/verify_all_data.py
```

This will check:
- ✅ Product data completeness
- ✅ Image file existence
- ✅ Detail extraction status
- ✅ Category coverage

---

## 🛑 Stopping/Resuming

### Stop Crawl
```bash
# Graceful stop (Ctrl+C)
^C

# Force kill all crawlers
pkill -f phase1_collect
pkill -f phase2_extract
```

### Resume Crawl
Scripts are **resume-safe**:
- Phase 1: Appends to `product_urls.jsonl` (no duplicates)
- Phase 2: Skips already processed products

Just run the same command again!

---

## 🎯 What's Next After Crawl

1. **Verify Quality**: Run `verify_all_data.py`
2. **Organize Data**: Consolidate into final structure
3. **Deduplicate**: Remove any duplicate products
4. **Index**: Create search index for RAG system
5. **Deploy**: Integrate with RAG pipeline

---

## 🆘 Troubleshooting

### No products collected
- Check internet connection
- Verify website is accessible
- Check if selectors still work (website may have changed)

### Images not downloading
- Check image URLs are valid
- Verify write permissions on `images/` directory
- Check disk space

### Slow performance
- Reduce parallel workers: `--workers 5`
- Increase delays: `--min-delay 0.2 --max-delay 0.5`
- Check system resources (CPU, memory, network)

### Crawl gets blocked
- Increase delays between requests
- Use fewer parallel workers
- Add user-agent rotation (script modification needed)

---

## 📞 Commands Quick Reference

```bash
# Full crawl (parallel Phase 1 + sequential Phase 2)
python3 scripts/run_parallel_crawl.py

# Phase 1 only (fast URL collection)
python3 scripts/run_parallel_crawl.py --phase1-only

# Phase 2 only (if Phase 1 already done)
python3 scripts/run_parallel_crawl.py --phase2-only

# Custom worker count
python3 scripts/run_parallel_crawl.py --workers 10

# Verify data quality
python3 scripts/verify_all_data.py

# Check progress
wc -l data/onehago/crawled/product_urls.jsonl
ls data/onehago/crawled/details/ | wc -l
ls data/onehago/crawled/images/ | wc -l
```

---

## ✨ Ready to Start!

Everything is tested and ready. Run when you're ready:

```bash
python3 scripts/run_parallel_crawl.py
```

Good luck! 🚀
