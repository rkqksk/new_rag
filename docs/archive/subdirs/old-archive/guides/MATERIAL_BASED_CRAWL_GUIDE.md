# Material-Based Organization & Crawl Guide

**New Organization**: Products organized by MATERIAL (PE, PET, PETG, PP, Other)
**Location**: `data/crawled_products_final/`
**Complete Dataset**: 398 existing + ~560 missing = ~900 total products

---

## 📁 New Directory Structure

```
data/crawled_products_final/
├── PE/                    # Polyethylene (안전, 경량)
│   ├── products/
│   │   ├── idx_13.json   # 40ml 브로우용기
│   │   ├── idx_30.json   # 65ml 브로우용기
│   │   └── ...
│   ├── images/
│   └── print_area/
├── PET/                   # Polyethylene Terephthalate (투명, 프리미엄)
│   ├── products/
│   │   ├── idx_308.json  # 70ml 브로우용기
│   │   ├── idx_417.json  # 220g 크림용기
│   │   └── ...
│   ├── images/
│   └── print_area/
├── PETG/                  # PET + Glycol (내구성)
│   ├── products/
│   ├── images/
│   └── print_area/
├── PP/                    # Polypropylene (내열성)
│   ├── products/
│   ├── images/
│   └── print_area/
└── Other/                 # Unknown or mixed materials
    ├── products/
    ├── images/
    └── print_area/
```

---

## 🚀 Two-Step Process

### Step 1: Reorganize Existing 398 Products

**Purpose**: Move existing products from Bottle/Jar/CapPump to PE/PET/PETG/PP/Other

```bash
# Preview changes (dry run)
python scripts/reorganize_by_material.py --dry-run

# Execute reorganization
python scripts/reorganize_by_material.py

# With cleanup (removes old Bottle/Jar/CapPump folders)
python scripts/reorganize_by_material.py --cleanup
```

**Expected Output**:
```
Material Distribution:
PE    : ~180 products
PET   : ~150 products
PETG  :  ~30 products
PP    :  ~20 products
Other :  ~18 products
TOTAL :  398 products
```

**Duration**: ~2 minutes

---

### Step 2: Crawl Missing 560 Products

**Purpose**: Crawl ALL products (idx 13-970) and organize by material automatically

```bash
# Full crawl with material organization
python scripts/crawlers/material_based_crawler.py

# Resume if interrupted
python scripts/crawlers/material_based_crawler.py --resume

# Custom delay
python scripts/crawlers/material_based_crawler.py --delay 1.5
```

**Expected Output**:
```
Products by Material:
PE    : ~350 products total (180 existing + 170 new)
PET   : ~300 products total (150 existing + 150 new)
PETG  :  ~80 products total ( 30 existing +  50 new)
PP    :  ~90 products total ( 20 existing +  70 new)
Other : ~80 products total ( 18 existing +  62 new)
TOTAL : ~900 products (398 existing + ~500 new)
```

**Duration**: ~32 minutes (958 products × 2s delay)

---

## 📋 Complete Execution Workflow

### Option A: Step-by-Step (Recommended)

```bash
# 1. Preview reorganization
python scripts/reorganize_by_material.py --dry-run

# 2. Execute reorganization
python scripts/reorganize_by_material.py

# 3. Verify existing products moved
ls -l data/crawled_products_final/PE/products/*.json | wc -l
ls -l data/crawled_products_final/PET/products/*.json | wc -l

# 4. Crawl missing products
python scripts/crawlers/material_based_crawler.py

# 5. Verify complete dataset
for material in PE PET PETG PP Other; do
  echo "$material: $(ls -1 data/crawled_products_final/$material/products/*.json 2>/dev/null | wc -l | tr -d ' ') products"
done

# 6. Cleanup old structure
python scripts/reorganize_by_material.py --cleanup
```

### Option B: All-in-One (Advanced)

```bash
# Reorganize + Crawl in sequence
python scripts/reorganize_by_material.py && \
python scripts/crawlers/material_based_crawler.py && \
python scripts/reorganize_by_material.py --cleanup
```

---

## 🔍 Verification After Completion

### Check Product Counts

```bash
# Total products
find data/crawled_products_final -name "idx_*.json" | wc -l
# Expected: ~900

# By material
for material in PE PET PETG PP Other; do
  count=$(ls -1 data/crawled_products_final/$material/products/*.json 2>/dev/null | wc -l | tr -d ' ')
  echo "$material: $count products"
done
```

### Verify Material Distribution

```bash
# Sample products from each material
for material in PE PET PETG PP Other; do
  echo "\n=== $material Samples ==="
  ls data/crawled_products_final/$material/products/ | head -3 | while read file; do
    echo "  - $file: $(cat data/crawled_products_final/$material/products/$file | jq -r '.product_name')"
  done
done
```

### Check Data Quality

```bash
# Verify all products have material info
python3 << 'EOF'
import json
from pathlib import Path

materials = ["PE", "PET", "PETG", "PP", "Other"]
base_dir = Path("data/crawled_products_final")

for material in materials:
    products_dir = base_dir / material / "products"
    if not products_dir.exists():
        continue

    json_files = list(products_dir.glob("*.json"))

    # Check material consistency
    mismatched = 0
    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)

        specs = data.get("specifications", {})
        material_value = None

        for key, value in specs.items():
            if '재질' in key or '원료' in key:
                material_value = str(value).upper()
                break

        if material_value:
            # Simple check
            if material == "PE" and "PE" not in material_value:
                mismatched += 1
            elif material == "PET" and "PET" not in material_value and "PE" in material_value:
                mismatched += 1

    print(f"{material}: {len(json_files)} products, {mismatched} potential mismatches")
EOF
```

---

## 💡 Material Categories Explained

| Material | Korean | Characteristics | Typical Products |
|----------|--------|-----------------|------------------|
| **PE** | 폴리에틸렌 | 안전, 경량, 내충격성 | 브로우용기, 튜브 |
| **PET** | 폴리에틸렌 테레프탈레이트 | 투명, 고급스러움, 가벼움 | 프리미엄 브로우용기, 크림용기 |
| **PETG** | PET + Glycol | 내구성, 투명도 높음 | 고급 용기 |
| **PP** | 폴리프로필렌 | 내열성, 화학 안정성 | 캡, 펌프, 고온용 용기 |
| **Other** | 기타/혼합 | 미표기 또는 복합재질 | - |

---

## 🎯 Benefits of Material-Based Organization

### For Manufacturing
- ✅ **Material sourcing**: Easy to find all PE products for bulk orders
- ✅ **Production planning**: Group products by material type
- ✅ **Supplier management**: Material-specific supplier catalogs

### For Customers
- ✅ **Safety requirements**: Find food-safe PE products easily
- ✅ **Aesthetic preferences**: Browse transparent PET products
- ✅ **Technical specs**: Filter by material properties

### For RAG System
- ✅ **Better filtering**: `"PE 제품 중 50ml 용기 찾아줘"`
- ✅ **Material-based recommendations**: Suggest alternatives in same material
- ✅ **Semantic search**: "투명한 용기" → PET/PETG products

---

## 🔄 Re-Embedding After Reorganization

After complete reorganization, update embeddings:

```bash
# 1. Update embedding pipeline configuration
# Edit agents/product_embedding_pipeline.py

# Old:
# categories = ["Bottle", "Jar", "CapPump"]

# New:
# categories = ["PE", "PET", "PETG", "PP", "Other"]

# 2. Re-run embedding pipeline
python agents/product_embedding_pipeline.py

# 3. Verify Qdrant collections
curl -s http://localhost:6333/collections | jq '.result.collections[].name'

# Should see:
# - products_pe
# - products_pet
# - products_petg
# - products_pp
# - products_other
# - products_all (combined)

# 4. Check product count
curl -s http://localhost:6333/collections/products_all | jq '.result.points_count'
# Expected: ~900 (vs current 398)
```

---

## 🚨 Troubleshooting

### Issue: Reorganization finds no products

**Check**:
```bash
ls -l data/crawled_products_final/Bottle/products/ | head
ls -l data/crawled_products_final/Jar/products/ | head
ls -l data/crawled_products_final/CapPump/products/ | head
```

**Solution**: Verify current directory structure matches expected

### Issue: Material extraction fails (all go to "Other")

**Check sample product**:
```bash
cat data/crawled_products_final/Bottle/products/idx_13.json | jq '.specifications'
```

**Expected**: Should have `"재질(원료)": "PE"` field

### Issue: Crawler skips already-crawled products

**This is normal**: Crawler checks progress and skips existing products

**To force re-crawl**:
```bash
rm material_crawl_progress.json
python scripts/crawlers/material_based_crawler.py
```

---

## ✅ Success Criteria

After complete execution:

- [ ] ✅ ~900 total products (398 existing + ~500 new)
- [ ] ✅ Products organized in PE/PET/PETG/PP/Other folders
- [ ] ✅ Each material folder has products/images/print_area subdirectories
- [ ] ✅ No products remaining in Bottle/Jar/CapPump (if cleanup ran)
- [ ] ✅ Material distribution roughly: PE (40%), PET (35%), PETG (10%), PP (10%), Other (5%)
- [ ] ✅ All products have specifications with material info
- [ ] ✅ Images and PDFs moved to corresponding material folders

---

## 📊 Expected Timeline

| Task | Duration | Command |
|------|----------|---------|
| **Reorganize existing** | 2 min | `python scripts/reorganize_by_material.py` |
| **Crawl missing products** | 32 min | `python scripts/crawlers/material_based_crawler.py` |
| **Verify & cleanup** | 2 min | Manual verification |
| **Re-embedding** | 60 min | `python agents/product_embedding_pipeline.py` |
| **Total** | **~96 min** | - |

---

## 🔗 Related Documents

- **Data Audit**: `/docs/DATA_AUDIT_REPORT.md`
- **Material Crawler**: `/scripts/crawlers/material_based_crawler.py`
- **Reorganization Script**: `/scripts/reorganize_by_material.py`
- **Embedding Pipeline**: `/agents/product_embedding_pipeline.py`

---

**Ready to start?**

```bash
# Step 1: Reorganize existing products
python scripts/reorganize_by_material.py

# Step 2: Crawl missing products
python scripts/crawlers/material_based_crawler.py
```
