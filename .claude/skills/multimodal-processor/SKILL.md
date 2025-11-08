---
name: multimodal-processor
description: Process and analyze multi-modal data (text + images + documents) using NexaAI Vision-Language models
license: MIT
metadata:
  version: "1.0.0"
  domain: "multimodal"
  triggers:
    - "analyze image"
    - "visual search"
    - "ocr document"
    - "hybrid search"
---

# Multi-Modal Processor Skill

**Purpose**: Process and analyze multi-modal data (text + images + documents) using NexaAI Vision-Language models

## 🎯 What This Skill Does

This skill handles multi-modal processing:

1. **Image Analysis**: Analyze product images with Qwen3-VL
2. **Document OCR**: Extract text from PDFs and images
3. **Visual Search**: Find products by image similarity
4. **Combined Search**: Text + Image hybrid search

## 📋 When to Use This Skill

Use this skill when:
- User uploads an image
- Need to analyze product photos
- Processing PDF catalogs
- Visual similarity search required
- Multi-modal data ingestion

## 🔧 Available Commands

### `analyze-image <path>`

Analyze a product image and extract information.

**Example**:
```
analyze-image "./product.jpg"
```

**Output**:
- Product description
- Detected features (shape, color, material)
- Extracted text (if any)
- Confidence scores

---

### `ocr-document <path>`

Extract text from PDF or image document.

**Example**:
```
ocr-document "./catalog.pdf"
```

**Actions**:
1. Detect document type
2. Apply preprocessing (deskew, denoise)
3. Run multi-engine OCR (PaddleOCR → EasyOCR → Tesseract)
4. Extract entities (product codes, specs)
5. Return structured data

---

### `visual-search <image_path>`

Find similar products by image.

**Example**:
```
visual-search "./bottle.jpg"
```

**Actions**:
1. Extract visual features (CLIP embeddings)
2. Extract shape features (Hu Moments, Fourier)
3. Search Qdrant by visual similarity
4. Analyze with Qwen3-VL for details
5. Return ranked results

---

### `hybrid-search <query> <image_path>`

Combined text + image search.

**Example**:
```
hybrid-search "투명 용기" "./transparent-bottle.jpg"
```

**Actions**:
1. Text search (semantic embeddings)
2. Image search (visual + shape features)
3. Fusion (RRF or weighted combination)
4. Return unified results

---

## 🔄 Workflow

### Image Analysis Workflow

```
Input Image
    ↓
[Preprocessing]
  • Resize to 512x512
  • Normalize colors
  • Remove background (optional)
    ↓
[Feature Extraction]
  ├─ Visual: CLIP embeddings (1024-dim)
  ├─ Shape: Hu Moments + Fourier (128-dim)
  └─ Text: OCR with PaddleOCR
    ↓
[NexaAI Analysis]
  • Qwen3-VL-4B-Instruct
  • Detailed description
  • Feature detection
    ↓
[Structured Output]
{
  "description": "50ml transparent PET bottle",
  "features": {
    "shape": "cylindrical",
    "color": "transparent",
    "material": "PET (predicted)"
  },
  "ocr_text": "50ML",
  "confidence": 0.92
}
```

---

## 💡 Examples

### Example 1: Product Image Analysis

**Input**:
```
Image: bottle.jpg (50ml PET bottle)
Command: analyze-image "bottle.jpg"
```

**Skill Action**:
```python
# Analyze with NexaAI Qwen3-VL
analysis = nexa.analyze_image(
    image_path="bottle.jpg",
    prompt="Describe this product in detail including shape, color, material, capacity, and any visible text or labels."
)
```

**Output**:
```
✓ Image Analysis Complete

Product Description:
  This is a small cylindrical plastic bottle with a transparent body.
  The bottle appears to be made of PET (polyethylene terephthalate)
  material based on its clarity and texture. It has a screw-top cap
  and appears to be designed for liquid storage.

Detected Features:
  • Shape: Cylindrical
  • Color: Transparent/Clear
  • Material: PET (predicted with 85% confidence)
  • Capacity: ~50ml (estimated from proportions)
  • Cap Type: Screw-top, white color
  • Neck Size: Approximately 24mm diameter

Visible Text (OCR):
  • "50ML" (on label)
  • "PET" (recycling symbol)

Visual Embeddings Generated:
  • CLIP: 1024-dimensional vector
  • Shape: 128-dimensional descriptor
  • Stored in Qdrant: image_vectors collection

Confidence Score: 0.92

Similar Products Found:
  1. 50ml PET 투명 용기 (similarity: 0.94)
  2. 50ml PET 크리스탈 보틀 (similarity: 0.91)
  3. 60ml PET 투명 용기 (similarity: 0.87)
```

### Example 2: PDF Catalog Processing

**Input**:
```
File: product_catalog.pdf (50 pages)
Command: ocr-document "product_catalog.pdf"
```

**Skill Action**:
```python
# Multi-engine OCR pipeline
from src.core.ocr import DocumentProcessor

processor = DocumentProcessor(use_gpu=True)

# Process PDF
result = processor.process_file("product_catalog.pdf")

# Extract entities
entities = processor.extract_entities(result['text'])

# Generate embeddings
embeddings = processor.process_to_rag_format("product_catalog.pdf")
```

**Output**:
```
✓ PDF Processing Complete

Document Info:
  • Pages: 50
  • Processing time: 2m 15s
  • OCR engine: PaddleOCR (primary)
  • Avg confidence: 0.89

Extracted Data:
  • Products found: 127
  • Product codes: 127
  • Specs extracted: 98%
  • Images extracted: 64

Entities Detected:
  • Capacity: 89 occurrences (50ml, 100ml, 150ml, etc.)
  • Materials: 72 occurrences (PET, PP, HDPE, etc.)
  • Neck sizes: 45 occurrences (24파이, 28파이, etc.)
  • MOQ: 67 occurrences

RAG Chunks Generated: 635
  • Text chunks: 520
  • Table chunks: 85
  • Image chunks: 30

Embeddings Stored:
  • Collection: documents_catalog
  • Vector count: 635
  • Dimension: 384

Sample Products:
  1. CODE-001: 50ml PET 투명 용기, Neck 24파이, MOQ 5000
  2. CODE-002: 100ml PP 반투명 용기, Neck 28파이, MOQ 3000
  ...
```

### Example 3: Visual Search

**Input**:
```
Image: user_photo.jpg (similar bottle needed)
Command: visual-search "user_photo.jpg"
```

**Skill Action**:
```python
# Extract features
visual_emb = extract_visual_features("user_photo.jpg")  # CLIP
shape_emb = extract_shape_features("user_photo.jpg")    # Hu Moments

# Multi-modal search
results = search_multimodal(
    visual_embedding=visual_emb,
    shape_embedding=shape_emb,
    top_k=10
)

# Analyze with vision model
for result in results[:3]:
    analysis = nexa.analyze_image(
        image_path=result['image_path'],
        prompt="Compare this product with the user's uploaded image. What are the similarities and differences?"
    )
    result['comparison'] = analysis
```

**Output**:
```
✓ Visual Search Complete

Query Image Analysis:
  • Detected: Clear plastic bottle, cylindrical shape
  • Estimated capacity: 50-60ml
  • Material: Transparent PET
  • Shape descriptor: [0.23, 0.45, 0.12, ...]

Search Results (Top 5):

1. Product: 50ml PET 투명 용기
   Visual Similarity: 0.94
   Shape Similarity: 0.91
   Combined Score: 0.93

   Comparison:
   "This product is very similar to the user's image. Both are
    transparent cylindrical PET bottles with similar proportions.
    The main difference is the cap design - this one has a flip-top
    while the user's image shows a screw cap."

2. Product: 60ml PET 크리스탈 보틀
   Visual Similarity: 0.89
   Shape Similarity: 0.88
   Combined Score: 0.89

   Comparison:
   "Similar bottle but slightly larger. Same transparent PET material
    and cylindrical shape. This one is taller and narrower."

3. Product: 50ml PET 스프레이 보틀
   Visual Similarity: 0.85
   Shape Similarity: 0.82
   Combined Score: 0.84

   Comparison:
   "Same capacity and material, but has a spray pump instead of
    a simple cap. Base shape is very similar."
```

### Example 4: Hybrid Text + Image Search

**Input**:
```
Query: "투명 용기"
Image: transparent_bottle.jpg
Command: hybrid-search "투명 용기" "transparent_bottle.jpg"
```

**Skill Action**:
```python
# Text search
text_results = search_semantic("투명 용기", top_k=20)

# Image search
image_results = search_visual("transparent_bottle.jpg", top_k=20)

# Fusion (Reciprocal Rank Fusion)
fused_results = reciprocal_rank_fusion(
    text_results,
    image_results,
    weights={"text": 0.6, "image": 0.4}
)
```

**Output**:
```
✓ Hybrid Search Complete

Search Strategy:
  • Text weight: 60%
  • Image weight: 40%
  • Fusion method: Reciprocal Rank Fusion (RRF)

Results (Top 5):

1. 50ml PET 투명 용기
   Text Score: 0.91 (rank #1)
   Image Score: 0.94 (rank #1)
   Fused Score: 0.92
   → Perfect match on both modalities!

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

---

## 🚀 Implementation

```python
# src/skills/multimodal_processor.py

from src.services.unified_llm_service import get_unified_llm
from src.core.ocr import DocumentProcessor
from src.core.image_matching import VisualEmbedder
from src.core.shape_processors import ShapeEmbedder

class MultiModalProcessor:
    """Multi-Modal Processing Skill"""

    def __init__(self):
        self.llm = get_unified_llm()
        self.ocr = DocumentProcessor(use_gpu=True)
        self.visual = VisualEmbedder()
        self.shape = ShapeEmbedder()

    async def analyze_image(self, image_path: str) -> dict:
        """Analyze image with NexaAI vision model"""

        # Vision-language analysis
        description = await self.llm.analyze_image(
            image_path=image_path,
            prompt="Describe this product in detail..."
        )

        # Feature extraction
        visual_emb = self.visual.embed(image_path)
        shape_emb = self.shape.embed(image_path)

        # OCR for text
        ocr_result = self.ocr.process_image(image_path)

        return {
            "description": description,
            "visual_embedding": visual_emb,
            "shape_embedding": shape_emb,
            "ocr_text": ocr_result.get("text", ""),
            "confidence": ocr_result.get("confidence", 0.0)
        }
```

---

**Skill Owner**: RAG Enterprise Team
**Last Updated**: 2025-11-08
**Version**: 1.0.0
