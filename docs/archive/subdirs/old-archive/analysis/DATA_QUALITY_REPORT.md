# Data Quality Report: Excel vs Crawled Products

**Generated:** 2025-10-22
**Analysis Period:** Complete catalog comparison

---

## Executive Summary

Comprehensive analysis of product data quality between official Excel files (source of truth) and crawled website data revealed significant discrepancies. Out of 118 "missing" products identified, only 18 were valid product codes, and **NONE** of these exist on the chungjinkorea.com website.

### Key Findings

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Crawled Products** | 846 | 100% |
| **Total Excel Products** | 241 | 28.5% |
| **Common Products (matched)** | 90 | 10.6% |
| **Excel-only products** | 118 | 13.9% |
| **Valid product codes (Excel-only)** | 18 | 2.1% |
| **Products found on website** | 0 | 0% |

---

## Detailed Analysis

### 1. Missing Products Investigation

#### 1.1 Excel Products Not in Database (118 total)

Breaking down the 118 "missing" entries:

**Valid Product Codes (18):**
```
BT111-RM09, BT111-RP09
HT015-SP01, HT020-SP01, HT030-RP01, HT030-SP01
HT050-RP01, HT050-SP01, HT080-RP01
HT100-RP01, HT100-SP01
JP111-GM01, JP150-TK01, JP200-TK01
JP270-GK01, JP450-GK01
MH400-G001(24), MH400-G001(28)
```

**Invalid Entries (32):** These are NOT product codes but specs/dimensions:
```
"PET / 200g", "PE / 200g", "pet / 650ml", "pe / 500ml"
"60 x 109(mm)", "31 x 36(mm)", "54 x 52(mm)"
"Ø43", "hdpe / 500ml", etc.
```

**Remaining (68):** Incomplete product code data in Excel

#### 1.2 Website Search Results

Searched chungjinkorea.com for all 18 valid product codes:
- **Found:** 0 products
- **Not Found:** 18 products (100%)

**Conclusion:** These 18 products exist in Excel files but are **NOT available on the website**. Possible reasons:
1. Discontinued products
2. Future/planned products
3. Internal catalog items not published online
4. Typos in Excel files

### 2. Spec Format Mismatches (90 products)

Products with same code but different spec formats between Excel and crawled data:

**Example Mismatches:**

| Code | Crawled Spec | Excel Spec | Issue |
|------|--------------|------------|-------|
| BE500-S007 | 60x60x202(mm)/Ø28 | PE / 500ml | Format: dimensions vs capacity |
| BG400-R010 | 64x182(mm)/Ø28 | PE / 400ml | Format + Material mismatch |
| MH050-G001 | 35x75(mm)/Ø20 | 50ml | Missing material info |
| JP450-GM01 | Ø85x96(mm) | 450g / PP | Weight vs volume units |

**Root Cause:** No standardized spec format across data sources.

### 3. Database Products Not in Excel (661 products)

661 products in crawled database don't appear in Excel files. Analysis:

**Product Code Distribution:**
- Products WITH codes: 751 (88.8%)
- Products WITHOUT codes (N/A): 95 (11.2%)

**Missing in Excel breakdown:**
- Products with valid codes: 661
- Likely categories: Accessories (caps, pumps), Custom molds, Special orders

**Sample Missing Codes:**
```
NP020-GE11, YP086-GM10, PTP024-CP02
QG100-G001, QG080-G001, QG030-G001
SO020-CE22, SO024-CE22, SO028-CG01
```

---

## Data Organization Status

### Folder Structure Verified

**Crawled Products:**
```
data/crawled_products_final/
├── Bottle/[PE|PET|PETG|PP|Other]/products_list.csv
├── CapPump/[PE|PET|PETG|PP|Other]/products_list.csv
├── Jar/[PE|PET|PETG|PP|Other]/products_list.csv
└── master_catalog.csv (846 products)
```

**Excel Products:**
```
data/excel_uploads/
├── raw/ (7 Excel files)
├── processed/
│   ├── PE/products_list.csv (43 products)
│   ├── PET/products_list.csv (45 products)
│   ├── PETG/products_list.csv (30 products)
│   ├── PP/products_list.csv (9 products)
│   ├── Other/products_list.csv (114 products)
│   └── comparison_report.json
├── images/ (1000+ extracted images)
└── master_catalog.csv (241 products)
```

### CSV Standardization Complete

Both sources use identical 17-column format:
```
product_code, product_name, material, spec, dimensions, category,
packaging, mold, cost, price, production, note, images_count,
image_files, has_print_area, source_file, source_type
```

---

## Recommendations

### Priority 1: Spec Format Standardization
**Issue:** 90 products have spec format mismatches
**Action Required:**
1. Define single authoritative spec format
2. Decide: dimensions vs capacity vs combined
3. Update parser to normalize spec extraction
4. Re-generate catalogs with standardized format

### Priority 2: Excel Data Quality
**Issue:** 32 invalid entries using specs as product codes
**Action Required:**
1. Review Excel files for data entry errors
2. Separate spec information from product code field
3. Add validation to prevent spec/code confusion

### Priority 3: Product Code Coverage
**Issue:** 95 crawled products have "N/A" as product code
**Action Required:**
1. Update crawler to extract product codes more reliably
2. Check if these products have codes on detail pages
3. Manually add codes for products without website codes

### Priority 4: Excel Catalog Completeness
**Issue:** 661 products in database not in Excel
**Action Required:**
1. Verify if these are valid active products
2. Add missing products to Excel master catalog
3. Establish process for keeping Excel synchronized

### Priority 5: Missing Products Investigation
**Issue:** 18 Excel product codes don't exist on website
**Action Required:**
1. Confirm with business: are these discontinued?
2. Remove from Excel if obsolete
3. Document reason for discrepancy

---

## Files Generated

1. **Comparison Report:** `data/excel_uploads/processed/comparison_report.json`
2. **Master Catalogs:**
   - Crawled: `data/crawled_products_final/master_catalog.csv`
   - Excel: `data/excel_uploads/master_catalog.csv`
3. **Material-specific CSVs:** In respective material folders
4. **Missing Codes List:** `data/excel_uploads/processed/missing_product_codes.txt`
5. **Search Results:** `data/excel_uploads/processed/search_results.json`

---

## Next Steps

**Completed:**
- ✅ Parser fixed to extract ALL products from Excel (241 products)
- ✅ Folder structure organized by material (both sources)
- ✅ CSV catalogs generated with standardized format
- ✅ Comparison report created with detailed gap analysis
- ✅ Missing products analyzed and searched on website

**Pending User Decision:**
1. Choose authoritative spec format (dimensions vs capacity)
2. Decide how to handle 18 missing product codes
3. Priority order for recommendations implementation

---

## Contact

For questions or clarifications about this report, refer to:
- Comparison report: `data/excel_uploads/processed/comparison_report.json`
- Analysis scripts: `scripts/analyze_missing_products.py`
- Search logs: `search_missing_products.log`
