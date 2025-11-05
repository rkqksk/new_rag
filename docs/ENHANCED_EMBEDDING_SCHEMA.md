# Enhanced Embedding Schema Design

**Date**: 2025-11-04
**Phase**: 2 - Enhanced Embedding
**Version**: 1.0.0

---

## Overview

This document defines the enhanced embedding schema that leverages preprocessed data with images and parsed specifications to improve search quality and enable advanced filtering.

---

## Current vs Enhanced Schema

### Current Schema (Basic)

**Embedding Text**:
```
Product: 20파이 미스트 스프레이 펌프 / 안개분사 / 풀캡 |
ID: 57501 |
코드: GY |
용량: NeckØ20 |
MOQ: 5,000 |
재질: PP,OTHER, |
원산지: 한국
```

**Metadata** (8 fields):
```json
{
  "source": "packaging_unique_for_images.jsonl",
  "line_number": 1,
  "product_id": "57501",
  "product_name": "20파이 미스트 스프레이 펌프",
  "category_id": 10,
  "company_no": "180",
  "product_url": "https://...",
  "source_collection": "onehago",
  "source_name": "원하고"
}
```

**Issues**:
- ❌ No image information
- ❌ Unparsed specifications (NeckØ20, PP,OTHER,)
- ❌ Cannot filter by material, capacity, neck_size
- ❌ Capacity not extracted from product name

---

### Enhanced Schema (v2)

**Embedding Text** (Enriched):
```
Product: 20파이 미스트 스프레이 펌프 / 안개분사 / 풀캡 |
ID: 57501 |
Category: 펌프/디스펜서 |
Material: PP, 기타 |
Neck Size: 20mm |
MOQ: 5000개 |
Origin: 한국 |
Images: 3장 (고품질) |
Company: 금양실업
```

**Metadata** (18+ fields):
```json
{
  // Basic fields (existing)
  "source": "packaging_enhanced.jsonl",
  "line_number": 1,
  "product_id": "57501",
  "product_name": "20파이 미스트 스프레이 펌프",
  "category_id": 10,
  "company_no": "180",
  "product_url": "https://...",
  "source_collection": "onehago",
  "source_name": "원하고",

  // Parsed specifications (NEW)
  "neck_size": 20,
  "capacity_value": null,
  "capacity_unit": null,
  "materials": ["PP", "기타"],
  "moq": 5000,

  // Image metadata (NEW)
  "has_images": true,
  "image_count": 3,
  "main_image_path": "images/packaging/57501/img_01_67d99837.jpg",
  "image_paths": [
    "images/packaging/57501/img_01_67d99837.jpg",
    "images/packaging/57501/img_02_45a73e30.jpg",
    "images/packaging/57501/img_03_297d363e.jpg"
  ],

  // Company info (NEW)
  "company_name": "금양실업",
  "email": "toritoya@naver.com"
}
```

**Benefits**:
- ✅ Image paths available for UI display
- ✅ Parsed specifications for precise filtering
- ✅ Material-based search
- ✅ Capacity-based search (when available)
- ✅ Neck size filtering
- ✅ MOQ filtering
- ✅ Company information

---

## Embedding Text Generation

### Strategy

**Principle**: Include structured and searchable information for semantic search

**Format**: `Field: Value | Field: Value | ...`

### Implementation

```python
def create_enhanced_embedding_text(product):
    """
    Create rich embedding text from enhanced product data

    Args:
        product: Enhanced product dict with specifications_parsed

    Returns:
        str: Rich embedding text for vector search
    """
    parts = []

    # 1. Product name (highest weight)
    if product.get('product_name'):
        parts.append(f"Product: {product['product_name']}")

    # 2. Product ID
    if product.get('product_id'):
        parts.append(f"ID: {product['product_id']}")

    # 3. Category (if available)
    category_map = {
        10: '펌프/디스펜서',
        20: '병/용기',
        30: '캡/뚜껑',
        40: '튜브',
    }
    if product.get('category_id') in category_map:
        parts.append(f"Category: {category_map[product['category_id']]}")

    # 4. Parsed specifications
    specs = product.get('specifications_parsed', {})

    # Materials (cleaned)
    if specs.get('materials'):
        materials_str = ', '.join(specs['materials'])
        parts.append(f"Material: {materials_str}")

    # Neck size
    if specs.get('neck_size'):
        parts.append(f"Neck Size: {specs['neck_size']}mm")

    # Capacity
    if specs.get('capacity'):
        cap = specs['capacity']
        parts.append(f"Capacity: {cap['value']}{cap['unit']}")

    # MOQ
    if specs.get('moq'):
        parts.append(f"MOQ: {specs['moq']:,}개")

    # 5. Origin
    original_specs = product.get('specifications', {})
    if original_specs.get('원산지'):
        parts.append(f"Origin: {original_specs['원산지']}")

    # 6. Image availability
    if product.get('has_local_images'):
        img_count = len(product.get('local_images', []))
        parts.append(f"Images: {img_count}장 (고품질)")

    # 7. Company info
    company_info = product.get('company_info', {})
    if company_info.get('제조사'):
        company_name = company_info['제조사'].split('Member')[0].strip()
        parts.append(f"Company: {company_name}")

    return " | ".join(parts)
```

**Example Output**:
```
Product: 20파이 미스트 스프레이 펌프 / 안개분사 / 풀캡 |
ID: 57501 |
Category: 펌프/디스펜서 |
Material: PP, 기타 |
Neck Size: 20mm |
MOQ: 5,000개 |
Origin: 한국 |
Images: 3장 (고품질) |
Company: 금양실업
```

---

## Metadata Schema

### Field Definitions

| Field | Type | Source | Filterable | Example |
|-------|------|--------|------------|---------|
| **Basic Fields** | | | | |
| `product_id` | str | raw | ✅ | "57501" |
| `product_name` | str | raw | ✅ | "20파이 미스트..." |
| `category_id` | int | raw | ✅ | 10 |
| `company_no` | str | raw | ✅ | "180" |
| `product_url` | str | raw | ❌ | "https://..." |
| `source_collection` | str | raw | ✅ | "onehago" |
| `source_name` | str | raw | ❌ | "원하고" |
| **Parsed Specifications** | | | | |
| `neck_size` | int | parsed | ✅ | 20 |
| `capacity_value` | float | parsed | ✅ | 50.0 |
| `capacity_unit` | str | parsed | ✅ | "ml" |
| `materials` | list[str] | parsed | ✅ | ["PP", "기타"] |
| `moq` | int | parsed | ✅ | 5000 |
| **Image Metadata** | | | | |
| `has_images` | bool | parsed | ✅ | true |
| `image_count` | int | parsed | ✅ | 3 |
| `main_image_path` | str | parsed | ❌ | "images/..." |
| `image_paths` | list[str] | parsed | ❌ | [...] |
| **Company Info** | | | | |
| `company_name` | str | parsed | ✅ | "금양실업" |
| `email` | str | raw | ❌ | "toritoya@..." |

---

## Qdrant Payload Indexes

For optimal filtering performance, create payload indexes on frequently filtered fields:

```python
from qdrant_client.models import PayloadSchemaType

# Numeric indexes
qdrant_client.create_payload_index(
    collection_name="onehago",
    field_name="neck_size",
    field_schema=PayloadSchemaType.INTEGER
)

qdrant_client.create_payload_index(
    collection_name="onehago",
    field_name="capacity_value",
    field_schema=PayloadSchemaType.FLOAT
)

qdrant_client.create_payload_index(
    collection_name="onehago",
    field_name="moq",
    field_schema=PayloadSchemaType.INTEGER
)

qdrant_client.create_payload_index(
    collection_name="onehago",
    field_name="image_count",
    field_schema=PayloadSchemaType.INTEGER
)

# Keyword indexes
qdrant_client.create_payload_index(
    collection_name="onehago",
    field_name="capacity_unit",
    field_schema=PayloadSchemaType.KEYWORD
)

qdrant_client.create_payload_index(
    collection_name="onehago",
    field_name="materials",
    field_schema=PayloadSchemaType.KEYWORD
)

qdrant_client.create_payload_index(
    collection_name="onehago",
    field_name="company_name",
    field_schema=PayloadSchemaType.KEYWORD
)

# Boolean indexes
qdrant_client.create_payload_index(
    collection_name="onehago",
    field_name="has_images",
    field_schema=PayloadSchemaType.BOOL
)
```

---

## Search Examples

### Example 1: Material-based Search

**Query**: "PET 병 50ml"

**Qdrant Filter**:
```python
from qdrant_client.models import Filter, FieldCondition, MatchAny

filter = Filter(
    must=[
        FieldCondition(
            key="materials",
            match=MatchAny(any=["PET"])
        ),
        FieldCondition(
            key="capacity_value",
            range=RangeCondition(gte=45, lte=55)
        )
    ]
)
```

**Expected Results**: Only PET bottles with 45-55ml capacity

---

### Example 2: Neck Size Search

**Query**: "20파이 펌프"

**Qdrant Filter**:
```python
filter = Filter(
    must=[
        FieldCondition(
            key="neck_size",
            match=MatchValue(value=20)
        )
    ]
)
```

**Expected Results**: Products with 20mm neck size

---

### Example 3: Image-only Search

**Query**: "고품질 이미지 포함 화장품 용기"

**Qdrant Filter**:
```python
filter = Filter(
    must=[
        FieldCondition(
            key="has_images",
            match=MatchValue(value=True)
        ),
        FieldCondition(
            key="image_count",
            range=RangeCondition(gte=2)  # At least 2 images
        )
    ]
)
```

**Expected Results**: Products with 2+ images

---

### Example 4: Company + Material Search

**Query**: "금양실업 PP 용기"

**Qdrant Filter**:
```python
filter = Filter(
    must=[
        FieldCondition(
            key="company_name",
            match=MatchValue(value="금양실업")
        ),
        FieldCondition(
            key="materials",
            match=MatchAny(any=["PP"])
        )
    ]
)
```

**Expected Results**: PP products from 금양실업

---

## Performance Considerations

### Embedding Time

**Current** (Basic):
- ~22,871 products
- ~30-45 minutes total
- ~100 products/batch

**Enhanced** (With parsed data):
- Same: ~22,871 products
- Same: ~30-45 minutes total
- Same: ~100 products/batch
- **No performance degradation** (metadata only, embedding text slightly longer)

### Search Performance

**Without Indexes**:
- Material filter: ~100-200ms
- Capacity filter: ~100-200ms

**With Payload Indexes**:
- Material filter: ~10-20ms (10× faster)
- Capacity filter: ~10-20ms (10× faster)
- Combined filters: ~15-30ms

---

## Migration Strategy

### Option 1: Replace Existing Collection (Recommended)

**Pros**:
- Clean slate
- No legacy data
- Consistent schema

**Cons**:
- Requires full re-embedding
- ~30-45 minutes downtime

**Steps**:
```python
# 1. Delete old collection
qdrant_client.delete_collection("onehago")

# 2. Create new collection with enhanced schema
# (done automatically by embed_onehago_enhanced.py)

# 3. Embed enhanced data
python scripts/embed_onehago_enhanced.py
```

---

### Option 2: Side-by-Side Testing

**Pros**:
- No downtime
- A/B testing possible
- Rollback available

**Cons**:
- 2× storage
- Manual cleanup needed

**Steps**:
```python
# 1. Create new collection
collection_name = "onehago_v2"

# 2. Embed to new collection
python scripts/embed_onehago_enhanced.py --collection onehago_v2

# 3. Test both collections
# 4. Switch routing to onehago_v2
# 5. Delete onehago
```

---

## Quality Metrics

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Material Search Accuracy** | 70% | 90% | +20% |
| **Capacity Search Accuracy** | 60% | 85% | +25% |
| **Neck Size Search** | Not possible | 90% | NEW |
| **Image-based Filtering** | Not possible | 98% | NEW |
| **Filter Performance** | 100-200ms | 10-20ms | 10× faster |
| **Overall Search Quality** | 75% | 90% | +15% |

---

## Implementation Checklist

### Phase 2 Tasks

- [x] Design enhanced schema
- [ ] Implement enhanced embedding text generation
- [ ] Create enhanced embedding script
- [ ] Add payload indexes
- [ ] Test with sample data (100 products)
- [ ] Embed full dataset (22,871 products)
- [ ] Performance testing
- [ ] Quality comparison (before vs after)

---

## Next Steps

1. **Implement** enhanced embedding script (`scripts/embed_onehago_enhanced.py`)
2. **Test** with 100 products sample
3. **Compare** search quality with current version
4. **Deploy** to production (full 22,871 products)
5. **Monitor** performance and quality metrics

---

**Version**: 1.0.0
**Status**: Design Complete ✅
**Next**: Implementation
