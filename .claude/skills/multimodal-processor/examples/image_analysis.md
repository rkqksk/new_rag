# Image Analysis Examples

## Example 1: Product Photo Analysis

**Input**: `bottle.jpg` (50ml PET bottle)

**Command**: `analyze-image "bottle.jpg"`

**Output**:
```
✓ Image Analysis Complete

Product Description:
  Small cylindrical plastic bottle with transparent body made of PET material.
  Screw-top white cap, appears designed for liquid storage.

Detected Features:
  • Shape: Cylindrical
  • Color: Transparent/Clear
  • Material: PET (85% confidence)
  • Capacity: ~50ml (estimated from proportions)
  • Cap Type: Screw-top, white
  • Neck Size: ~24mm diameter

OCR Text:
  • "50ML" (on label)
  • "PET" (recycling symbol)

Visual Embeddings:
  • CLIP: [0.23, 0.45, -0.12, ...] (1024-dim)
  • Shape: [0.87, 0.23, 0.56, ...] (128-dim)
  • Stored in Qdrant: image_vectors collection

Confidence Score: 0.92

Similar Products:
  1. 50ml PET 투명 용기 (0.94 similarity)
  2. 50ml PET 크리스탈 보틀 (0.91 similarity)
  3. 60ml PET 투명 용기 (0.87 similarity)
```

---

## Example 2: PDF Catalog Processing

**Input**: `product_catalog.pdf` (50 pages)

**Command**: `ocr-document "product_catalog.pdf"`

**Output**:
```
✓ PDF Processing Complete

Document Info:
  • Pages: 50
  • Processing time: 2m 15s
  • Primary OCR: PaddleOCR (GPU)
  • Avg confidence: 0.89

Extracted Data:
  • Products found: 127
  • Product codes: 127 (100%)
  • Specifications: 125 (98%)
  • Images: 64

Entities Detected:
  • Capacity: 89 occurrences
  • Materials: 72 occurrences (PET, PP, HDPE)
  • Neck sizes: 45 occurrences (24파이, 28파이)
  • MOQ: 67 occurrences

RAG Chunks: 635
  • Text: 520 chunks
  • Tables: 85 chunks
  • Images: 30 chunks

Embeddings Stored:
  • Collection: documents_catalog
  • Vectors: 635
  • Dimension: 384

Sample Products:
  1. CODE-001: 50ml PET 투명 용기, 24파이, MOQ 5000개
  2. CODE-002: 100ml PP 반투명 용기, 28파이, MOQ 3000개
  ...
```

---

## Example 3: Hybrid Text + Image Search

**Input**:
- Query: "투명 용기"
- Image: `transparent_bottle.jpg`

**Command**: `hybrid-search "투명 용기" "transparent_bottle.jpg"`

**Output**:
```
✓ Hybrid Search Complete

Search Strategy:
  • Text weight: 60%
  • Image weight: 40%
  • Fusion: Reciprocal Rank Fusion (RRF)

Results (Top 5):

1. 50ml PET 투명 용기
   Text Score: 0.91 (rank #1)
   Image Score: 0.94 (rank #1)
   Fused Score: 0.92
   ★ Perfect match on both modalities

2. 100ml PET 크리스탈 용기
   Text Score: 0.88 (rank #2)
   Image Score: 0.89 (rank #2)
   Fused Score: 0.88

3. 50ml PET 반투명 용기
   Text Score: 0.85 (rank #4)
   Image Score: 0.91 (rank #3)
   Fused Score: 0.87
   → Better visual match than text

4. 투명 스프레이 보틀 50ml
   Text Score: 0.89 (rank #3)
   Image Score: 0.82 (rank #6)
   Fused Score: 0.85

5. 60ml 크리스탈 투명 용기
   Text Score: 0.83 (rank #5)
   Image Score: 0.85 (rank #4)
   Fused Score: 0.84
```
