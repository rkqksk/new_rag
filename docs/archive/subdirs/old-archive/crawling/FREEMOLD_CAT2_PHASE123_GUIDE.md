# Freemold Category 2 (A003) - Complete Phase 1, 2, 3 Pipeline Guide

**Date**: November 2, 2025
**Version**: 1.0
**Status**: Ready for Execution
**Target**: Extract ALL products in Category 2 (패키징/포장재 - Packaging/Packing Materials)

---

## 📋 Overview

Complete extraction and processing pipeline for **Category 2 (A003)** products across all 1,592 pagination pages, resulting in a complete, optimized dataset for RAG integration.

```
PHASE 1 (Discover URLs)
    ↓
PHASE 2 (Extract Text & Images)
    ↓
PHASE 3 (Filter & Optimize)
    ↓
PRODUCTION-READY CATEGORY 2 DATASET
```

---

## 🎯 Current Status

| Phase | Task | Status | Expected Output |
|-------|------|--------|-----------------|
| **Phase 1** | Discover all A003 product URLs | ⏳ Ready | product_urls_A003_complete.jsonl (~2000-3000 URLs) |
| **Phase 2** | Extract text & images from URLs | ⏳ Ready | products_text_A003_complete.jsonl (full text) |
| **Phase 3** | Filter, optimize & finalize | ⏳ Ready | A003.jsonl (production-ready dataset) |

**Key Context**:
- Current discovered Category 2 URLs: **1,705 in product_urls.jsonl**
- Expected after full pagination: **~2,000-3,000 unique products**
- Current extracted: **0 products** (Phase 2 hasn't run yet)

---

## 📊 Three-Phase Pipeline Details

### Phase 1: URL Discovery ⏳ READY

**Status**: Script ready, execution pending

**Purpose**: Discover ALL product URLs in Category 2 through comprehensive pagination crawling

**Script**: `scripts/freemold_cat2_phase1_discovery.py` (250 lines)

**Approach**:
- Connect to Chrome at `localhost:9222` (Remote Debugging)
- Crawl all 1,592 pages of category A003 pagination
- Extract product IDs from pagination links
- Deduplicate using Python sets
- Track progress in JSON file for resumable crawling

**Input**: None (pagination-based discovery)

**Output**:
```
data/freemold/crawled/product_urls_A003_complete.jsonl

Record structure:
{
  "product_id": "20745",
  "category": "A003",
  "category_name": "패키징/포장재",
  "url": "https://www.freemold.net/Front/Product/?tp=vi&pIdx=20745",
  "discovered_at": "2025-11-02T...",
  "page_source": 1
}
```

**Performance**:
- Rate limiting: 1.5 seconds per page
- Expected time: ~40 minutes for all 1,592 pages
- Output size: ~0.5-1.0 MB (product URLs only)

**Progress Tracking**:
```
data/freemold/crawled/phase1_A003_progress.json

{
  "category": "A003",
  "total_pages": 1592,
  "pages_processed": 601,
  "unique_products": 1205,
  "current_page": 602,
  "last_updated": "2025-11-02T10:30:45..."
}
```

**Resume Capability**: Can restart and continue from last page processed

---

### Phase 2: Text & Image Extraction ⏳ READY

**Status**: Script ready, awaits Phase 1 completion

**Purpose**: Extract text content and images from all discovered Category 2 product pages

**Script**: `scripts/freemold_cat2_phase2_extraction.py` (380 lines)

**Workflow**:
1. Read `product_urls_A003_complete.jsonl` (input from Phase 1)
2. Visit each product page with Selenium
3. Extract text content:
   - Product name
   - Description
   - Specifications
   - Manufacturer/contact info
4. Collect product images (max 10)
5. Parse contact info (phone, fax, email) using regex
6. Write complete records to output file

**Input**: `product_urls_A003_complete.jsonl` (~2,000-3,000 URLs)

**Output**:
```
data/freemold/crawled/products_text_A003_complete.jsonl

Record structure:
{
  "product_id": "20745",
  "category": "A003",
  "category_name": "패키징/포장재",
  "url": "https://...",
  "extracted_at": "2025-11-02T...",
  "name": "PET bottle 500ml",
  "description": "High-quality plastic containers...",
  "specs": {
    "material": "PET",
    "capacity": "500ml",
    "neck_size": "28/410"
  },
  "manufacturer": null,
  "contact": {
    "phone": "070-1234-5678",
    "fax": "031-8888-8888",
    "email": "info@company.com"
  },
  "images": [
    "https://www.freemold.net/data/product/20745_1.jpg",
    "https://www.freemold.net/data/product/20745_2.jpg",
    ...
  ],
  "extraction_success": true
}
```

**Performance**:
- Per-page timeout: 15 seconds
- Rate limiting: 0.5 seconds between requests
- Expected time: 5-8 hours for 2,000-3,000 products
- Output size: ~10-15 MB (with text + image URLs)

**Progress Tracking**:
```
data/freemold/crawled/phase2_A003_progress.json

{
  "total_urls": 2145,
  "processed": 500,
  "successful": 480,
  "failed": 20,
  "last_product_id": "20801"
}
```

**Resume Capability**: Progress saved every 100 products, can restart

---

### Phase 3: Optimization & Finalization ⏳ READY

**Status**: Script ready, awaits Phase 2 completion

**Purpose**: Filter, validate, and optimize all extracted Category 2 data for RAG system

**Script**: `scripts/freemold_cat2_phase3_optimization.py` (220 lines)

**Processing Steps**:
1. Read `products_text_A003_complete.jsonl`
2. Filter by category (A003 only)
3. Validate images:
   - Check for valid HTTP URLs
   - Verify image extensions (.jpg, .png, .gif, .webp)
   - Prioritize product images over navigation images
   - Select max 3 best images per product
4. Clean contact information:
   - Remove empty/null values
   - Normalize phone numbers
5. Ensure specs and contact are proper dictionaries
6. Output optimized records

**Input**: `products_text_A003_complete.jsonl` (full extraction)

**Output**:
```
data/freemold/crawled/products_by_category/A003.jsonl

Optimized record:
{
  "product_id": "20745",
  "category": "A003",
  "category_name": "패키징/포장재",
  "url": "https://...",
  "name": "PET bottle 500ml",
  "description": "High-quality plastic containers...",
  "specs": {
    "material": "PET",
    "capacity": "500ml"
  },
  "contact": {
    "phone": "070-1234-5678",
    "email": "info@company.com"
  },
  "images": [
    "https://www.freemold.net/data/product/20745_1.jpg",
    "https://www.freemold.net/data/product/20745_2.jpg",
    "https://www.freemold.net/data/product/20745_3.jpg"
  ],
  "extracted_at": "2025-11-02T...",
  "extraction_success": true
}
```

**Summary Output**:
```
data/freemold/crawled/a003_summary.json

{
  "processed_at": "2025-11-02T...",
  "category": "A003",
  "category_name": "패키징/포장재",
  "total_products": 2145,
  "successful": 2100,
  "failed": 45,
  "with_images": 1950,
  "with_contact": 1800,
  "with_specs": 1900,
  "processing_time": "00:02:15",
  "output_file": "data/freemold/crawled/products_by_category/A003.jsonl"
}
```

**Performance**:
- Processing speed: Very fast (in-memory processing)
- Expected time: 2-3 minutes for 2,000-3,000 products
- Output size: ~8-10 MB (optimized data)

---

## 🚀 Execution Workflow

### **Step 1: Phase 1 - URL Discovery**

**Command**:
```bash
cd /Users/oypnus/Project/rag-enterprise
chmod +x scripts/freemold_cat2_phase1_discovery.py
python3 scripts/freemold_cat2_phase1_discovery.py 2>&1 | tee /tmp/freemold_phase1_A003_discovery.log &
```

**Monitor Progress**:
```bash
tail -f /tmp/freemold_phase1_A003_discovery.log
# or check every 5 minutes
while sleep 300; do tail -5 /tmp/freemold_phase1_A003_discovery.log; done
```

**Expected Duration**: ~40 minutes for 1,592 pages

**Success Indicators**:
- Log shows "Progress: 1550/1592 pages | 2145 unique products found"
- Output file created: `data/freemold/crawled/product_urls_A003_complete.jsonl`
- Progress file updated: `data/freemold/crawled/phase1_A003_progress.json`

**If Interrupted**: Run the same command again to resume from last page

---

### **Step 2: Phase 2 - Text & Image Extraction**

**Prerequisites**: Phase 1 complete

**Command**:
```bash
chmod +x scripts/freemold_cat2_phase2_extraction.py
python3 scripts/freemold_cat2_phase2_extraction.py 2>&1 | tee /tmp/freemold_phase2_A003_extraction.log &
```

**Monitor Progress**:
```bash
tail -f /tmp/freemold_phase2_A003_extraction.log
```

**Expected Duration**: 5-8 hours for 2,000-3,000 products

**Progress Checkpoints** (should see these lines):
- "Total URLs to process: 2145"
- "Progress: 500/2145 (450 successful, 50 failed)"
- "Progress: 1000/2145 (900 successful, 100 failed)"
- "Progress: 1500/2145 (1350 successful, 150 failed)"
- "Progress: 2000/2145 ..."

**Success Indicators**:
- Output file created: `data/freemold/crawled/products_text_A003_complete.jsonl`
- Progress file shows: `"processed": 2145, "successful": ~2000, "failed": ~100`
- Log ends with: "✅ EXTRACTION COMPLETE FOR CATEGORY A003"

**If Interrupted**: Run the same command again to resume from last processed product

---

### **Step 3: Phase 3 - Optimization & Finalization**

**Prerequisites**: Phase 2 complete

**Command**:
```bash
chmod +x scripts/freemold_cat2_phase3_optimization.py
python3 scripts/freemold_cat2_phase3_optimization.py 2>&1 | tee /tmp/freemold_phase3_A003_optimization.log
```

**Monitor Progress**:
```bash
tail -f /tmp/freemold_phase3_A003_optimization.log
```

**Expected Duration**: 2-3 minutes

**Success Indicators**:
- Log shows: "Total products processed: 2145"
- Output file created: `data/freemold/crawled/products_by_category/A003.jsonl`
- Summary file created: `data/freemold/crawled/a003_summary.json`
- Log ends with: "✨ Phase 3 optimization complete!"

---

## 📈 Expected Results

### Data Growth Trajectory

```
Phase 1 (Discovery):
  Input:  None
  Output: ~2,145 unique product URLs
  Time:   ~40 minutes

Phase 2 (Extraction):
  Input:  2,145 URLs
  Output: ~2,100 products with text + images
  Time:   ~5-8 hours

Phase 3 (Optimization):
  Input:  ~2,100 extracted products
  Output: ~2,100 optimized, production-ready products
  Time:   ~2-3 minutes

Final Category 2 Dataset:
  Total Products: ~2,100
  With Images: ~1,950 (93%)
  With Contact: ~1,800 (86%)
  With Specs: ~1,900 (90%)
  File Size: ~8-10 MB
```

### Quality Metrics (Expected)

```
Successful Extractions: ~98% (2,050/2,100)
Failed Extractions: ~2% (50/2,100)
Images per Product: avg 2.5
Specs Coverage: ~90%
Contact Info Coverage: ~86%
Description Coverage: ~95%
```

---

## 🔧 Troubleshooting

### Phase 1 Issues

**Problem**: Chrome connection fails
```
Error: ❌ Failed to connect to remote Chrome: [error message]
```
**Solution**:
- Make sure Chrome is running with remote debugging:
  ```bash
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9222
  ```
- Or create new Chrome instance (script will do this automatically)

**Problem**: Slow crawling speed
**Solution**: Check network connection, verify site isn't rate-limiting

**Problem**: Script stops without completing
**Solution**: Check log for errors, run again to resume from last page

---

### Phase 2 Issues

**Problem**: "Page timeout" errors
**Solution**: Normal for some products, script retries automatically

**Problem**: Low extraction success rate
**Solution**:
- Check if product pages require authentication
- Verify URL format is correct
- Some products may have minimal/no data

**Problem**: Out of memory
**Solution**:
- Reduce Chrome cache: Add `--no-sandbox --disable-dev-shm-usage` flags
- Run Phase 2 in batches if needed

---

### Phase 3 Issues

**Problem**: "Input file not found"
**Solution**: Phase 2 hasn't completed yet, wait for it to finish

**Problem**: Wrong category products in output
**Solution**: This shouldn't happen if Phase 2 is correct, but Phase 3 filters by category A003

**Problem**: Zero products in output
**Solution**: Phase 2 extraction may have failed, check Phase 2 output file

---

## 📁 Files & Locations

### Scripts
```
scripts/freemold_cat2_phase1_discovery.py      (250 lines)
scripts/freemold_cat2_phase2_extraction.py     (380 lines)
scripts/freemold_cat2_phase3_optimization.py   (220 lines)
```

### Data Files
```
Input/Output:
  data/freemold/crawled/product_urls_A003_complete.jsonl        (Phase 1 output)
  data/freemold/crawled/products_text_A003_complete.jsonl       (Phase 2 output)
  data/freemold/crawled/products_by_category/A003.jsonl         (Phase 3 output - FINAL)

Progress:
  data/freemold/crawled/phase1_A003_progress.json
  data/freemold/crawled/phase2_A003_progress.json

Summary:
  data/freemold/crawled/a003_summary.json
```

### Log Files
```
/tmp/freemold_phase1_A003_discovery.log
/tmp/freemold_phase2_A003_extraction.log
/tmp/freemold_phase3_A003_optimization.log
```

---

## 🎯 Success Criteria

### Phase 1 Success
- ✅ `product_urls_A003_complete.jsonl` created with 1,500+ products
- ✅ `phase1_A003_progress.json` shows 1592 pages processed
- ✅ 0 errors in final summary
- ✅ Log ends with "✅ DISCOVERY COMPLETE FOR CATEGORY A003"

### Phase 2 Success
- ✅ `products_text_A003_complete.jsonl` created
- ✅ Product count matches URL count (or slightly less due to failures)
- ✅ Success rate >= 95%
- ✅ Sample records contain text, specs, contact info
- ✅ Log ends with "✅ EXTRACTION COMPLETE FOR CATEGORY A003"

### Phase 3 Success
- ✅ `products_by_category/A003.jsonl` created
- ✅ Product count = Phase 2 processed count
- ✅ Sample records have optimized images (max 3)
- ✅ Contact info cleaned (no null values)
- ✅ `a003_summary.json` generated with statistics
- ✅ Log ends with "✨ Phase 3 optimization complete!"

---

## ⏱️ Timeline Summary

```
Phase 1 Duration:      ~40 minutes
Phase 2 Duration:      ~5-8 hours
Phase 3 Duration:      ~2-3 minutes
                       ───────────
Total Time:            ~6-9 hours

Recommended Schedule:
  9:00 AM  - Start Phase 1 (discovery)
  9:45 AM  - Phase 1 complete
  9:50 AM  - Start Phase 2 (extraction)
  2:00 PM  - Phase 2 complete (assuming 5hr extraction)
  2:05 PM  - Start Phase 3 (optimization)
  2:10 PM  - Phase 3 complete
  2:10 PM  - Category 2 dataset READY FOR PRODUCTION
```

---

## 📊 After Completion

Once Category 2 (A003) is complete:

1. **Verify Quality**:
   ```bash
   wc -l data/freemold/crawled/products_by_category/A003.jsonl
   # Should show ~2,100 products

   head -1 data/freemold/crawled/products_by_category/A003.jsonl | python3 -m json.tool
   # Should show complete product record with images, contact, specs
   ```

2. **Check Statistics**:
   ```bash
   cat data/freemold/crawled/a003_summary.json | python3 -m json.tool
   ```

3. **Proceed to Next Category**:
   - Repeat Phase 1, 2, 3 for Category 4 (A004)
   - Or run all categories in sequence

---

## 🔗 Related Documentation

- `FREEMOLD_3PHASE_PIPELINE_GUIDE.md` - Generic pipeline (for all categories)
- `CURRENT_STATUS_SUMMARY.md` - Overall project status
- `FREEMOLD_DATA_REORGANIZATION_SUMMARY.md` - Data reorganization reference

---

## 📝 Version & Updates

**Version**: 1.0
**Created**: November 2, 2025
**Status**: ✅ **Ready for Execution**

**Next Phase**: Begin Phase 1 URL discovery for Category 2

---

**Good luck! Category 2 extraction is about to begin. 🚀**
