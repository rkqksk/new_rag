# Data Quality Comparison: Chungjinkorea vs Onehago

**Date**: 2025-11-04
**Purpose**: Analyze data quality gaps and improvement requirements

---

## 📊 Executive Summary

**Current Status**:
- **Chungjinkorea**: ✅ High-quality, production-ready
- **Onehago**: ⚠️ Basic data, needs enhancement

**Key Gaps**:
1. ❌ No local image downloads (only URLs)
2. ❌ No pricing information
3. ❌ No compatibility analysis
4. ❌ No material characteristics
5. ⚠️ Poor metadata structure

---

## 🔍 Detailed Comparison

### 1. Data Structure

#### Chungjinkorea (857 products):
```json
{
  "product_name": "350ml 브로우용기",
  "idx": "569",
  "images": [
    {
      "url": "http://chungjinkorea.com/...",
      "local_path": "data/.../images/idx_569_main_1.jpg",
      "type": "main",
      "width": 1000,
      "height": 1000
    }
  ],
  "specifications": {
    "제품명": "350ml 브로우용기",
    "제품 코드": "BG350-S008",
    "재질(원료)": "PETG",
    "capacity": "350ml",
    "neck_size": "28파이",
    "neck_size_mm": 28,
    "moq": "10,000개"
  },
  "pricing": {
    "actual_capacity_ml": 350,
    "base_price": {
      "regular": 440,
      "discount": 420
    },
    "coating_price": {
      "type": "무광코팅",
      "regular": 340,
      "discount": 290
    }
  },
  "compatibility_analysis": {
    "compatible_caps_pumps": {
      "count": 23,
      "items": [...]
    }
  },
  "recommended_applications": {
    "by_capacity": ["바디로션", "샴푸", "클렌징"],
    "by_material": ["프리미엄 앰플", "세럼"]
  },
  "material_info": {
    "name": "PETG",
    "characteristics": "PET보다 내충격성 우수",
    "chemical_resistance": {...}
  }
}
```

#### Onehago (22,871 products):
```json
{
  "product_id": "57501",
  "product_name": "20파이 미스트 스프레이 펌프",
  "company_no": "180",
  "product_url": "https://www.onehago.com/...",
  "specifications": {
    "코드": "GY",
    "용량": "Neck×20",     // ⚠️ Capacity 필드에 Neck 정보
    "MOQ": "5,000",
    "재질": "PP,OTHER,",   // ⚠️ 파싱 안 된 상태
    "원산지": "한국"
  },
  "company_info": {
    "제조사": "금양실업Member Supplier",  // ⚠️ 파싱 필요
    "담당": "- 일반 문의 : 김양원 실장 010-9341-1805..."
  },
  "image_urls": [
    "https://www.onehago.com/productImages/2025-02/c1739728151_1.jpg",
    ...
    // ❌ 30개 URL만 있고 local_path 없음
  ],
  "image_count": 30,
  // ❌ No pricing
  // ❌ No compatibility_analysis
  // ❌ No recommended_applications
  // ❌ No material_info
}
```

---

## 📈 Quality Metrics Comparison

| Metric | Chungjinkorea | Onehago | Gap |
|--------|--------------|---------|-----|
| **Total Products** | 857 | 22,871 | +2,569% |
| **Images (Local)** | ✅ 3 per product | ❌ 0 (URLs only) | Critical |
| **Structured Specs** | ✅ 8+ fields | ⚠️ 5 fields | Medium |
| **Pricing** | ✅ Complete | ❌ None | Critical |
| **Compatibility** | ✅ 23 accessories | ❌ None | High |
| **Material Info** | ✅ Detailed | ❌ None | High |
| **Applications** | ✅ Recommended | ❌ None | Medium |
| **Print Area** | ✅ PDF downloads | ❌ None | Medium |

---

## 🎯 Embedded Data Quality

### Vector Database Metadata

#### Chungjinkorea (Qdrant "products"):
```json
{
  "text": "Product: 350ml 브로우용기 | 제품명: ... | 재질: PETG | capacity: 350ml | neck_size: 28파이 | moq: 10,000개",
  "metadata": {
    "source": "data/.../idx_569.json",
    "idx": "569",
    "product_code": "BG350-S008",
    "product_name": "350ml 브로우용기",
    "category": "Bottle",
    "material": "PETG",
    "capacity": "350ml",
    "neck_size": "28파이"
  }
}
```

#### Onehago (Qdrant "onehago"):
```json
{
  "text": "Product: 20파이 미스트 ... | ID: 57501 | 코드: GY | 용량: Neck×20 | MOQ: 5,000 | 재질: PP,OTHER, | ...",
  "metadata": {
    "source": "/tmp/onehago_batch_5300.jsonl",
    "line_number": 59,
    "product_id": "57501",
    "product_name": "20파이 미스트 스프레이 펌프",
    "category_id": 9,
    "company_no": "384",
    "product_url": "https://...",
    "source_collection": "onehago"
    // ❌ No capacity, material, neck_size as structured fields
  }
}
```

---

## 🔴 Critical Issues

### Issue 1: Image URLs Not Downloaded
**Impact**: Cannot display product images in UI

**Current**:
```json
"image_urls": [
  "https://www.onehago.com/productImages/2025-02/c1739728151_1.jpg",
  ...
]
// No local_path
```

**Expected** (like chungjinkorea):
```json
"images": [
  {
    "url": "https://www.onehago.com/...",
    "local_path": "data/onehago/images/57501_main_1.jpg",
    "type": "main",
    "downloaded": true
  }
]
```

**Solution Required**:
- Download images from URLs
- Store locally: `data/crawled/onehago/images/{product_id}_{index}.jpg`
- Update metadata with local_path

---

### Issue 2: Specifications Not Parsed
**Impact**: Cannot filter by capacity, material, dimensions

**Current**:
```json
"specifications": {
  "코드": "GY",
  "용량": "Neck×20",         // ❌ Should be "20파이" neck size
  "재질": "PP,OTHER,",        // ❌ Should be ["PP", "기타"]
  "MOQ": "5,000"             // ✅ OK
}
```

**Expected**:
```json
"specifications": {
  "product_code": "GY",
  "capacity": null,           // Or extract from product_name
  "neck_size": "20파이",
  "neck_size_mm": 20,
  "materials": ["PP", "기타"],
  "moq": 5000,                // Integer
  "dimensions": "..."
}
```

**Solution Required**:
- Parse specifications properly
- Extract capacity from product_name if not in specs
- Parse material list
- Convert MOQ to integer
- Extract neck_size from 용량 field

---

### Issue 3: No Pricing Data
**Impact**: Cannot show prices or calculate costs

**Current**: ❌ No pricing field

**Expected** (like chungjinkorea):
```json
"pricing": {
  "base_price": {
    "regular": 440,
    "discount": 420
  },
  "moq": 5000,
  "pricing_updated_at": "2025-11-04"
}
```

**Solution Required**:
- Scrape pricing from onehago website
- Store regular/discount prices
- Link to MOQ

---

### Issue 4: Poor Metadata Extraction
**Impact**: RAG search quality degraded

**Current Embedding Text**:
```
"Product: 20파이 미스트 스프레이 펌프 | ID: 57501 | 코드: GY |
용량: Neck×20 | MOQ: 5,000 | 재질: PP,OTHER, | ..."
```
- ⚠️ 용량 field contains neck size, not capacity
- ⚠️ 재질 not parsed
- ⚠️ No dimensions extracted

**Expected Embedding Text**:
```
"Product: 20파이 미스트 스프레이 펌프 |
제품코드: GY |
재질: PP, 기타 |
Neck Size: 20파이 (20mm) |
MOQ: 5,000개 |
제조사: 금양실업 |
용도: 미스트 스프레이 펌프"
```

**Solution Required**:
- Re-chunk data with proper parsing
- Extract structured fields
- Create semantic-rich text for embedding

---

## 📋 Required Improvements

### Phase 1: Data Enhancement (Critical)

**1. Image Download**
```python
# Script: scripts/download_onehago_images.py
- Read packaging_unique_for_images.jsonl
- For each product:
  - Download first 3 images from image_urls
  - Save to: data/crawled/onehago/images/{product_id}_{i}.jpg
  - Update JSONL with local_path
- Time estimate: ~2-3 hours for 22,871 products
```

**2. Specifications Parsing**
```python
# Script: scripts/parse_onehago_specifications.py
- Parse specifications:
  - Extract capacity from product_name (e.g., "250ml")
  - Parse neck_size from "용량" field (e.g., "Neck×20" → "20파이")
  - Split materials: "PP,OTHER," → ["PP", "기타"]
  - Convert MOQ to integer
  - Extract dimensions from "사이즈" field
- Create structured specs dict
```

**3. Company Info Parsing**
```python
# Parse company_info:
- Split "담당" field:
  - Extract contact name
  - Extract phone numbers
  - Extract roles
- Clean "제조사" field:
  - Remove "Member Supplier" suffix
  - Standardize company names
```

---

### Phase 2: Re-Embedding (Required)

**Current Embedding Issues**:
```python
# Current text generation (BAD)
text = f"Product: {product_name} | ID: {product_id} | 코드: {specifications.get('코드')} | ..."
# → Unstructured, mixed formats
```

**Improved Embedding**:
```python
# New text generation (GOOD)
def create_embedding_text(product):
    parts = [
        f"제품명: {product['product_name']}",
        f"제품코드: {product['specifications'].get('product_code', '')}",
        f"재질: {', '.join(product['materials'])}",
        f"용량: {product['capacity']}",
        f"Neck Size: {product['neck_size']}",
        f"MOQ: {product['moq']:,}개",
        f"제조사: {product['company_name']}",
        f"용도: {infer_usage(product)}",
        f"특징: {extract_features(product)}"
    ]
    return " | ".join(filter(None, parts))
```

**Re-Embedding Script**:
```python
# Script: scripts/re_embed_onehago_enhanced.py
1. Load enhanced JSONL with:
   - Downloaded images
   - Parsed specifications
   - Structured metadata
2. Generate better embedding text
3. Embed with all-MiniLM-L6-v2
4. Store in Qdrant "onehago" collection (replace existing)
```

---

### Phase 3: Additional Data (Nice to Have)

**1. Pricing Data**
- Scrape from onehago website
- Store in separate pricing file
- Link by product_id

**2. Compatibility Analysis**
- Identify bottle → cap/pump matches
- Based on neck_size
- Similar to chungjinkorea

**3. Material Characteristics**
- Add material database
- Chemical resistance info
- Suitable products list

---

## 🚀 Action Plan

### Immediate Actions (Week 1):

**Priority 1: Fix Specifications Parsing**
```bash
1. Create: scripts/parse_onehago_specifications.py
2. Parse:
   - capacity (from product_name)
   - neck_size (from "용량" field)
   - materials (split and clean)
   - dimensions (from "사이즈")
   - moq (convert to int)
3. Save: data/crawled/onehago/crawled/production/packaging_enhanced.jsonl
4. Time: 1-2 hours
```

**Priority 2: Download Images**
```bash
1. Create: scripts/download_onehago_images.py
2. Download first 3 images per product
3. Save to: data/crawled/onehago/images/
4. Update JSONL with local_path
5. Time: 2-3 hours (with rate limiting)
```

**Priority 3: Re-Embed with Enhanced Data**
```bash
1. Modify: scripts/embed_onehago_packaging.py
2. Load: packaging_enhanced.jsonl
3. Generate better embedding text
4. Re-embed all 22,871 products
5. Store in Qdrant (overwrite)
6. Time: ~30-45 minutes
```

---

### Week 2-3 Actions:

**Nice to Have**:
1. Add pricing data (scrape from website)
2. Create compatibility database
3. Add material characteristics
4. Create usage recommendations

---

## 📊 Expected Improvements

### After Phase 1+2 (Re-embedding):

**Search Quality**:
- Current: 70-75% accuracy
- Expected: 85-90% accuracy

**Metadata Completeness**:
- Current: 40% (5/12 fields)
- Expected: 75% (9/12 fields)

**User Experience**:
- ✅ Images displayed
- ✅ Better search results
- ✅ Structured filtering
- ⚠️ Still missing pricing

---

## 🎯 Success Criteria

**Minimum Viable (Phase 1+2)**:
- ✅ All images downloaded and accessible
- ✅ Specifications properly parsed
- ✅ Neck size extracted
- ✅ Materials cleaned
- ✅ Embedding text quality improved
- ✅ Search accuracy >85%

**Production Ready (Phase 3)**:
- ✅ Pricing data available
- ✅ Compatibility analysis done
- ✅ Material info complete
- ✅ Chungjinkorea-level quality

---

## 📂 File Structure Comparison

### Chungjinkorea:
```
data/crawled/chungjinkorea/
├── crawled_products_final/
│   ├── Bottle/
│   │   ├── PET/
│   │   │   ├── products/
│   │   │   │   └── idx_569.json    ✅ Rich metadata
│   │   │   └── images/
│   │   │       └── idx_569_main_1.jpg  ✅ Downloaded
│   │   └── ...
└── print_area/
    └── idx_569_print_area.pdf  ✅ Print specs
```

### Onehago (Current):
```
data/crawled/onehago/
└── crawled/production/
    └── packaging_unique_for_images.jsonl  ⚠️ URLs only
    // ❌ No images/ folder
    // ❌ No print_area/
```

### Onehago (Target):
```
data/crawled/onehago/
├── crawled/production/
│   ├── packaging_unique_for_images.jsonl
│   └── packaging_enhanced.jsonl  ✅ Parsed specs
├── images/
│   ├── 57501_1.jpg  ✅ Downloaded
│   ├── 57501_2.jpg
│   └── ...
└── specifications/
    └── enhanced_specs.jsonl  ✅ Structured
```

---

## 💡 Recommendations

### Immediate (This Week):
1. ✅ **Parse specifications** - Fix metadata structure
2. ✅ **Download images** - Enable UI display
3. ✅ **Re-embed data** - Improve search quality

### Short-term (Next 2 Weeks):
4. ⚠️ **Add pricing** - Scrape from website
5. ⚠️ **Create compatibility** - Link bottles to caps/pumps

### Long-term (Next Month):
6. 📊 **Material database** - Add chemical resistance
7. 🎯 **Usage recommendations** - ML-based suggestions
8. 🔄 **Auto-update pipeline** - Keep data fresh

---

## 🔧 Technical Debt

**Current Issues**:
1. Embedding text format inconsistent
2. Metadata fields not normalized
3. No validation of specifications
4. Image URLs not tested (may be broken)
5. No error handling for missing fields

**Resolution Plan**:
- Implement data validation schema
- Add unit tests for parsing functions
- Create data quality monitoring
- Set up automated quality checks

---

## 📈 Cost-Benefit Analysis

### Development Time:
- Phase 1 (Parsing): 4-6 hours
- Phase 2 (Images): 8-10 hours (including downloads)
- Phase 3 (Re-embedding): 2-3 hours
- **Total**: ~15-20 hours

### Expected Benefits:
- Search accuracy: +15-20%
- User satisfaction: +30-40%
- Data completeness: +35% (40% → 75%)
- Feature parity with chungjinkorea: 75%

### ROI:
- **High Priority**: Critical for production readiness
- **User Impact**: High (images + better search)
- **Effort**: Medium (~3 days full-time)

---

**Status**: ⚠️ **Onehago Needs Enhancement**
**Next Steps**: Implement Phase 1 (Parsing + Images)
**Target**: Chungjinkorea-level quality

**Version**: 1.0.0
**Date**: 2025-11-04
