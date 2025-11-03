# 🎯 Onehago Comprehensive Crawler Strategy

**Date**: 2025-10-31
**Target**: 100,000+ products from www.onehago.com
**Quality Standard**: Match `category_24.json` structure

---

## 📊 **Website Analysis Summary**

### Site Structure
- **URL Format**: `https://www.onehago.com/mall/?mode=view&prod_cd={PRODUCT_ID}`
- **Total Categories**: 153
- **Estimated Products**: ~17,390 (from valid_categories.json)
- **Total Pages**: 592

### Key Findings
✅ **Product Detail Pages Work**: Direct access via `prod_cd` parameter
✅ **Specifications Available**: `box-info` div contains 6 key fields
✅ **Images Accessible**: `/productImages/` URLs work
✅ **Contact Info**: Available in page text
❌ **Category Listings**: Require authentication or JavaScript (empty without login)

### Data Structure (Verified Working)
```
box-info div:
  Line 0: 제조사 (Manufacturer)
  Line 1: 코드 (Code)
  Line 2: 사이즈 (Size)
  Line 3: Neck (Neck type)
  Line 4: Neck Size
  Line 5: 재질 (Material)

company div: Manufacturer name
product div: Product images
```

---

## 🚀 **3-Phase Crawler Strategy**

### **PHASE 1: Collect 100K+ Product URLs** 📋

**Goal**: Generate comprehensive list of product URLs
**Challenge**: Category listings require login/JavaScript
**Solution**: Use existing `valid_categories.json` + sequential product ID scanning

#### Strategy Options:

**Option A: Category-Based URL Construction** (RECOMMENDED)
```python
# For each category in valid_categories.json:
# - Use estimated product count
# - Generate product IDs sequentially
# - Validate URLs exist (HTTP 200)
# - Estimated: 17,390 products x 5 (buffer) = ~85,000 URLs to scan
```

**Option B: Smart Crawler Continuation**
```python
# Continue existing onehago_smart_crawler.py
# - Already collected 5,278 products
# - Let it run for 24-48 hours
# - May collect 50K+ products
```

**Option C: Product ID Range Scanning**
```python
# Scan product ID ranges:
# - Start: 1
# - End: 100,000
# - Check each URL for HTTP 200
# - Collect valid product IDs
```

#### Phase 1 Output
```
File: data/onehago/product_urls_complete.jsonl
Format: One product per line
{
  "product_id": "36834",
  "product_url": "https://www.onehago.com/mall/?mode=view&prod_cd=36834",
  "category_id": "24",
  "discovered_at": "2025-10-31T17:00:00"
}

Target: 100,000+ lines
```

---

### **PHASE 2: Extract Details with JINA/Selenium** 🔍

**Goal**: Extract complete product specifications and images
**Method**: JINA (primary) or Selenium (fallback)
**Quality**: 100% match to category_24.json structure

#### Phase 2A: JINA-based Extraction (Preferred)
```python
# Use JINA for fast, efficient scraping
from jina import Executor, requests as jina_requests

Advantages:
- Fast: 4-8 parallel workers
- Efficient: Lower resource usage
- Reliable: Built-in retry logic

Process:
1. Read product_urls_complete.jsonl
2. Extract details using JINA
3. Download ALL images
4. Save by category: category_{id}.json
```

#### Phase 2B: Selenium Fallback (If JINA fails)
```python
# Use Selenium for JavaScript-heavy pages
from selenium import webdriver

When to use:
- JINA extraction fails
- JavaScript rendering required
- Dynamic content loading
```

#### Extraction Checklist (Per Product)
```python
Required Fields:
✅ product_id
✅ product_name
✅ company
✅ specifications (dict with 6 fields):
   - 제조사 (Manufacturer)
   - 코드 (Code)
   - 사이즈 (Size)
   - Neck
   - Neck Size
   - 재질 (Material)
✅ manufacturer
✅ phone (format: 02-6956-6370)
✅ fax (format: 02-XXXX-XXXX)
✅ email (format: xxx@xxx.com)
✅ full_images[] (array of image objects):
   - url
   - local_path
   - size_bytes
✅ category_id
✅ detail_crawled: true
✅ detail_crawled_at: ISO timestamp
```

#### Phase 2 Output Structure
```
Directory: data/onehago/crawled/categories/
Files: category_1.json, category_2.json, ... category_N.json

Each file contains array of products:
[
  {
    "product_id": "36834",
    "product_name": "Product Name",
    "company": "Company Name",
    "specifications": {
      "제조사": "금양실업",
      "코드": "GY-20-뾰족캡B",
      "사이즈": "Ø23.8 × 51.5",
      "Neck": "neck",
      "Neck Size": "Ø20",
      "재질": "PP"
    },
    "manufacturer": "지코스테크",
    "phone": "02-6956-6370",
    "fax": "",
    "email": "",
    "full_images": [
      {
        "url": "https://www.onehago.com/productImages/...",
        "local_path": "crawled/images/36834.jpg",
        "size_bytes": 29871
      }
    ],
    "category_id": 24,
    "detail_crawled": true,
    "detail_crawled_at": "2025-10-31T17:04:21.335095"
  }
]
```

#### Batch Processing
```
Process in batches of 100 products
After each 100: Manual confirmation prompt
  "✅ Processed 100 products. Continue? (1=Yes, 2=No)"

User can verify quality before continuing
```

---

### **PHASE 3: Quality Verification** ✅

**Goal**: Ensure 100% data quality matching category_24.json
**Method**: Automated validation + manual spot checks

#### Validation Checks

**3.1 Structure Validation**
```python
For each product:
✅ Has all required fields
✅ Specifications dict has 6+ entries
✅ full_images is non-empty array
✅ detail_crawled is true
✅ phone matches pattern: \d{2,4}-\d{3,4}-\d{4}
```

**3.2 Data Quality Checks**
```python
✅ No empty strings in critical fields
✅ Image files actually exist on disk
✅ Image file sizes > 1KB
✅ Product IDs are unique
✅ Category IDs match valid_categories.json
```

**3.3 Completeness Metrics**
```python
Report per category:
- Total products
- Products with specs: X/Total (%)
- Products with images: X/Total (%)
- Products with contact info: X/Total (%)
- Average images per product
```

**3.4 Manual Spot Checks**
```
Random sample: 10 products
Manually verify:
- Specifications accuracy
- Images match product
- Contact info correct
```

#### Phase 3 Output
```
File: data/onehago/quality_report.json
{
  "validation_date": "2025-10-31T18:00:00",
  "total_products": 100000,
  "total_categories": 153,
  "quality_metrics": {
    "products_with_specs": 99850,
    "products_with_images": 99920,
    "products_with_contact": 85000,
    "spec_completeness": "99.85%",
    "image_completeness": "99.92%",
    "contact_completeness": "85.00%"
  },
  "issues_found": [],
  "sample_verification": [
    {
      "product_id": "36834",
      "verified": true,
      "notes": "All fields correct"
    }
  ]
}
```

---

## 🛠️ **Implementation Plan**

### Phase 1 Execution (2-4 hours)
```bash
# Step 1: Product ID Range Scanning
python3 scripts/phase1_collect_urls.py \
  --start-id 1 \
  --end-id 100000 \
  --workers 8 \
  --output product_urls_complete.jsonl

# Expected: 50K-100K valid product URLs
```

### Phase 2 Execution (12-24 hours)
```bash
# Step 2: Detail Extraction with JINA
python3 scripts/phase2_extract_details.py \
  --input product_urls_complete.jsonl \
  --workers 4 \
  --batch-size 100 \
  --manual-confirm \
  --output categories/

# Manual confirmation every 100 products
# Total time: ~24 hours for 100K products
```

### Phase 3 Execution (1-2 hours)
```bash
# Step 3: Quality Validation
python3 scripts/phase3_validate_quality.py \
  --input categories/ \
  --reference category_24.json \
  --output quality_report.json

# Review report and fix any issues
```

---

## 📈 **Success Criteria**

### Phase 1 Success
- [ ] 100,000+ product URLs collected
- [ ] All URLs return HTTP 200
- [ ] URLs use correct format: `mode=view&prod_cd=XXXXX`
- [ ] Saved to `product_urls_complete.jsonl`

### Phase 2 Success
- [ ] 100% of products have specifications
- [ ] 95%+ of products have images
- [ ] 80%+ of products have contact info
- [ ] Organized into category files
- [ ] Manual confirmation worked every 100 products

### Phase 3 Success
- [ ] Structure matches `category_24.json` exactly
- [ ] All validation checks pass
- [ ] Quality report shows >95% completeness
- [ ] Manual spot checks confirm accuracy

---

## ⚠️ **Risk Mitigation**

### Risk 1: Website Blocking
- **Mitigation**: Delays between requests (0.1-0.3s)
- **Fallback**: Use multiple IP addresses / proxies

### Risk 2: JINA Extraction Failures
- **Mitigation**: Retry logic with exponential backoff
- **Fallback**: Switch to Selenium for failed products

### Risk 3: Incomplete Data
- **Mitigation**: Validation in Phase 3
- **Recovery**: Re-crawl failed products

### Risk 4: Storage Space
- **Estimate**: 100K products x 50KB each = ~5GB
- **Mitigation**: Monitor disk space, compress old data

---

## 📊 **Progress Tracking**

### Real-time Monitoring
```bash
# Phase 1 Progress
watch -n 5 'wc -l product_urls_complete.jsonl'

# Phase 2 Progress
watch -n 10 'ls -lh data/onehago/crawled/categories/*.json | wc -l'

# Phase 3 Progress
tail -f data/onehago/crawled/logs/validation.log
```

---

## ✅ **Final Deliverables**

1. **Product URLs**: `product_urls_complete.jsonl` (100K+ lines)
2. **Category Files**: `categories/category_*.json` (153 files)
3. **Images**: `images/*.jpg` (100K+ images)
4. **Quality Report**: `quality_report.json`
5. **Logs**: Complete logs for each phase

---

**Status**: Ready to Execute
**Estimated Total Time**: 24-48 hours
**Expected Output**: 100,000+ high-quality product records
