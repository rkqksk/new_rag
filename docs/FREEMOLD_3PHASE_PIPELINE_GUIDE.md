# Freemold 3-Phase Data Extraction Pipeline Guide

**Date**: November 2, 2025
**Version**: 1.0
**Status**: Ready for Execution

---

## 📋 Overview

Complete extraction and processing pipeline for Freemold product data across all 7 categories (~329,000 products expected).

```
PHASE 1 (Extract URLs)
    ↓
PHASE 2 (Extract Text & Images)
    ↓
PHASE 3 (Filter by Category & Optimize)
    ↓
PRODUCTION-READY CATEGORY DATASETS
```

---

## 🎯 Current Status

| Phase | Task | Status | Records | Size |
|-------|------|--------|---------|------|
| **Phase 1** | Extract product URLs | ✅ Complete | 16,303 URLs | 3.1 MB |
| **Phase 2a** | Extract text from URLs | ⏳ **In Progress** | 7,550 (46%) | 8.3 MB |
| **Phase 2b** | Reorganize & validate data | ✅ Complete | 7,272 | 8.1 MB |
| **Phase 3** | Filter by category | ⏳ Ready | - | - |
| **Pagination** | Discover all products | 🔄 Running | A001: ~47K | - |

**Key Gap**: 16,303 URLs discovered but only 7,550 texts extracted. Need to extract remaining ~9,000 products.

---

## 📊 Three-Phase Pipeline

### Phase 1: Extract URLs ✅ COMPLETE
**Status**: Done
**Input**: Manual discovery or crawler
**Output**: `product_urls.jsonl` (16,303 URLs)
**Data**: `{ product_id, category, category_name, url, discovered_at }`

```
Files:
  Input:  Web crawling
  Output: product_urls.jsonl (3.1 MB, 16,303 records)
```

---

### Phase 2: Extract Text & Images ⏳ IN PROGRESS

#### What it does:
1. Reads URLs from `product_urls.jsonl`
2. Visits each product page with Selenium
3. Extracts text content (name, specs, description, contact)
4. Collects product images
5. Outputs complete product records

#### Key Features:
- ✅ Selenium browser automation (avoids blocking)
- ✅ HTML parsing with BeautifulSoup
- ✅ Text extraction & regex parsing
- ✅ Image collection & validation
- ✅ Contact info parsing (phone, fax, email)
- ✅ Progress tracking & resumable extraction
- ✅ Error recovery with logging

#### Script
```bash
python3 scripts/freemold_phase2_universal_extractor.py
```

#### Input/Output
```
Input:  product_urls.jsonl (16,303 URLs)
Output: products_text_complete.jsonl (text + specs + images + contact)

Data Structure:
{
  "product_id": "89299",
  "category": "A001",
  "category_name": "프리몰드",
  "url": "https://...",
  "name": "스킨/로션/에센스용기",
  "description": "...",
  "specs": {
    "specification": "용량 : 60㎖",
    "material": "유리"
  },
  "contact": {
    "phone": "070-7014-7321/",
    "fax": "/",
    "email": "cosmepack@naver.com"
  },
  "images": ["https://...", ...],
  "extracted_at": "2025-11-02T...",
  "extraction_success": true
}
```

#### Performance
- Rate limiting: 0.5 seconds between requests
- Timeout per page: 15 seconds
- Expected time for 16,303 products: ~2-3 hours (with optimization)

#### Resume Capability
Progress tracked in: `phase2_extraction_progress.json`
```json
{
  "total_urls": 16303,
  "processed": 7550,
  "successful": 7272,
  "failed": 278,
  "last_product_id": "..."
}
```

Can restart and resume from last successful extraction.

---

### Phase 3: Filter by Category & Optimize Images ⏳ READY

#### What it does:
1. Reads all extracted products from Phase 2
2. Filters by category (A001-A009)
3. Selects best images (product images first, then nav images)
4. Optimizes data structure for RAG system
5. Creates category-specific output files

#### Key Features:
- ✅ Category-based filtering (7 categories)
- ✅ Smart image selection (max 3 best images per product)
- ✅ Contact info validation & cleaning
- ✅ Specifications validation
- ✅ Category statistics generation
- ✅ Batch processing with progress tracking

#### Script
```bash
python3 scripts/freemold_phase3_category_processor.py
```

#### Input/Output
```
Input:  products_text_complete.jsonl (all extracted products)
Output: products_by_category/{CATEGORY_CODE}.jsonl (7 files)
        category_summary.json (statistics)

Structure:
  products_by_category/
    ├── A001.jsonl (프리몰드)
    ├── A003.jsonl (패키징/포장재)
    ├── A004.jsonl (후가공/임가공)
    ├── A006.jsonl (원료)
    ├── A007.jsonl (인증/임상기관)
    ├── A008.jsonl (금형/기계/시공)
    └── A009.jsonl (디자인/마케팅)

Optimized Data:
{
  "product_id": "89299",
  "category": "A001",
  "category_name": "프리몰드",
  "url": "https://...",
  "name": "스킨/로션/에센스용기",
  "description": "...",
  "specs": {...},
  "contact": {...},
  "images": ["best_image_1", "best_image_2", "best_image_3"],
  "extracted_at": "...",
  "extraction_success": true
}
```

#### Performance
- Processing: ~1-2 minutes for all 16,303 products
- Output size: ~8-10 MB total across all categories

---

## 🚀 Execution Workflow

### Step 1: Run Phase 2 (Extract Text & Images)

**Command**:
```bash
cd /Users/oypnus/Project/rag-enterprise
chmod +x scripts/freemold_phase2_universal_extractor.py
python3 scripts/freemold_phase2_universal_extractor.py 2>&1 | tee /tmp/freemold_phase2_extractor.log &
```

**Monitor Progress**:
```bash
tail -f /tmp/freemold_phase2_extractor.log
```

**Expected Output**:
- `products_text_complete.jsonl` - Updated with all extracted products
- `phase2_extraction_progress.json` - Progress tracking
- Log file - Processing details

**Expected Time**: 2-3 hours for ~16,303 products

---

### Step 2: Run Phase 3 (Filter by Category)

**Prerequisites**: Phase 2 complete
**Trigger**: After Phase 2 finishes

**Command**:
```bash
python3 scripts/freemold_phase3_category_processor.py 2>&1 | tee /tmp/freemold_phase3_processor.log
```

**Monitor Progress**:
```bash
tail -f /tmp/freemold_phase3_processor.log
```

**Expected Output**:
- `products_by_category/A001.jsonl` - 6,000-8,000 products
- `products_by_category/A003.jsonl` - Category data
- `products_by_category/A004.jsonl` - Category data
- ... (7 files total)
- `category_summary.json` - Statistics

**Expected Time**: 1-2 minutes

---

## 📈 Expected Results

### Phase 2 Output Statistics

After extracting all 16,303 products:

```
Total Products: 16,303
├── Successful Extractions: ~15,000-15,500 (92%)
├── Failed Extractions: ~500-1,000 (3-8%)
├── Average Images per Product: 2-3
└── Average Text Length: 200-500 chars per product
```

### Phase 3 Category Distribution

After filtering by category:

```
A001 (프리몰드): ~3,000-4,000 products
A003 (패키징/포장재): ~2,000-3,000 products
A004 (후가공/임가공): ~1,500-2,000 products
A006 (원료): ~1,500-2,000 products
A007 (인증/임상기관): ~1,000-1,500 products
A008 (금형/기계/시공): ~2,000-3,000 products
A009 (디자인/마케팅): ~1,000-1,500 products

Total across all categories: ~16,303
```

---

## 🔄 Scaling to All Categories

After Phase 2 & 3 work for existing 16K products:

### Next Step: Pagination Discovery

The pagination crawler (`freemold_remote_chrome_crawler.py`) will:
1. Discover all products in each category (1,592 pages each)
2. Expected total: ~329,000 products (47K × 7 categories)
3. Output: URLs discovered for all products

### Then Repeat Phase 2 & 3

For each category's discovered products:
```
A001: 47,000 → Phase 2 extract → Phase 3 optimize → A001.jsonl (47K records)
A003: 47,000 → Phase 2 extract → Phase 3 optimize → A003.jsonl (47K records)
... (repeat for all 7 categories)
```

**Total workflow**:
```
Pagination (all categories) → Extract (all products) → Filter (by category) → Production datasets
329,000 URLs                → 329,000 texts          → 7 category files      → RAG-ready
```

---

## 🛠️ Troubleshooting

### Phase 2 Issues

**Problem**: Slow extraction rate
**Solution**: Ensure Chrome remote debugging is available at `localhost:9222`

**Problem**: Extraction failures
**Solution**: Check network connectivity, verify URLs are valid

**Problem**: Out of memory
**Solution**: Reduce batch size or process in smaller chunks

### Phase 3 Issues

**Problem**: Missing images in output
**Solution**: Check if images were extracted in Phase 2

**Problem**: Empty categories
**Solution**: Verify category codes (A001, A003, etc.) in product data

---

## 📋 Files & Locations

```
Scripts:
  scripts/freemold_phase2_universal_extractor.py (400 lines)
  scripts/freemold_phase3_category_processor.py (200 lines)

Input Data:
  data/freemold/crawled/product_urls.jsonl (16,303 URLs)

Output Data:
  data/freemold/crawled/products_text_complete.jsonl (Phase 2)
  data/freemold/crawled/products_by_category/ (Phase 3)
    ├── A001.jsonl
    ├── A003.jsonl
    ├── ... (7 files total)
    └── category_summary.json

Progress:
  data/freemold/crawled/phase2_extraction_progress.json
  /tmp/freemold_phase2_extractor.log
  /tmp/freemold_phase3_processor.log
```

---

## 🎯 Success Criteria

**Phase 2 Complete When**:
- ✅ All 16,303 products extracted (or processed)
- ✅ `products_text_complete.jsonl` contains all product data
- ✅ Each product has: id, name, specs, contact, images
- ✅ Error rate < 10%

**Phase 3 Complete When**:
- ✅ All 7 category files created
- ✅ Each category file contains valid products
- ✅ Images optimized (max 3 per product)
- ✅ Contact info cleaned and validated
- ✅ `category_summary.json` generated

---

## 📊 Performance Notes

### Optimization Tips

1. **Parallel Processing**: Can run Phase 2 for different categories in parallel
2. **Batch Size**: Adjust rate limiting based on site tolerance
3. **Image Selection**: Phase 3 uses heuristics to pick best images
4. **Progress Tracking**: Phase 2 progress saved every 100 products for recovery

### Expected Hardware Requirements

- **CPU**: Multi-core (4+ cores recommended)
- **Memory**: 4GB+ (for browser + JSON processing)
- **Disk**: 50GB+ (for intermediate files and results)
- **Network**: High speed (for rapid page downloads)

---

## 🔗 Related Documentation

- `FREEMOLD_DATA_REORGANIZATION_SUMMARY.md` - Contact info parsing
- `FREEMOLD_DATA_VALIDATION_REPORT.md` - Data quality metrics
- `CURRENT_STATUS_SUMMARY.md` - Overall project status

---

## 📝 Version History

**v1.0** - 2025-11-02
- Initial 3-phase pipeline
- Phase 2: Text & image extraction
- Phase 3: Category filtering & optimization
- Ready for execution

---

**Status**: ✅ **Ready for Execution**
**Next Step**: Run Phase 2 extraction for remaining 9,000 products
**Timeline**: Phase 2 (2-3 hrs) → Phase 3 (2 mins) → Category datasets ready

