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

**Purpose**: Process multi-modal data (text + images + documents) using NexaAI Qwen3-VL models

## 🎯 Overview

Handles image analysis, OCR extraction, visual search, and hybrid text+image retrieval using vision-language models.

## 📋 When to Use

- User uploads image
- Analyze product photos
- Process PDF catalogs
- Visual similarity search
- Multi-modal data ingestion

## 🔧 Commands

### `analyze-image <path>`
Analyze product image with NexaAI Qwen3-VL.

**Output**: Description, features (shape, color, material), OCR text, confidence

### `ocr-document <path>`
Extract text from PDF/images with multi-engine OCR.

**Pipeline**: PaddleOCR → EasyOCR → Tesseract (fallback)

### `visual-search <image_path>`
Find similar products by visual + shape features.

**Features**: CLIP (1024-dim) + Hu Moments (128-dim)

### `hybrid-search <query> <image_path>`
Combined text + image search with RRF fusion.

**Weights**: Text 60% + Image 40%

## 🔄 Quick Workflow

```
Input → Preprocess → Feature Extraction (Visual + Shape + OCR) → NexaAI Analysis → Structured Output
```

## 📚 Progressive Disclosure

**For detailed information, see:**
- `references/vision_pipeline.md` - Complete vision processing pipeline
- `references/ocr_engines.md` - Multi-engine OCR strategy
- `references/fusion_methods.md` - Hybrid search fusion algorithms
- `examples/image_analysis.md` - Real-world examples

## 🚀 Quick Example

```bash
# Analyze bottle image
analyze-image "bottle.jpg"
→ "50ml transparent PET bottle with screw cap"
→ Confidence: 0.92

# Visual search
visual-search "user_photo.jpg"
→ Top 3 similar products with 0.94, 0.89, 0.85 similarity
```

---

**Version**: 1.0.0 | **Updated**: 2025-11-08
