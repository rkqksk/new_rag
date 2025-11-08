# Vision Processing Pipeline

## Architecture

```
Input Image (any size)
    ↓
[Preprocessing]
  • Resize to 512x512
  • Normalize colors
  • Optional: Remove background
    ↓
[Feature Extraction]
  ├─ Visual Features
  │   • CLIP embeddings (1024-dim)
  │   • Pretrained on 400M image-text pairs
  │
  ├─ Shape Features
  │   • Hu Moments (7 invariant moments)
  │   • Fourier Descriptors (128-dim)
  │
  └─ Text Features
      • PaddleOCR (primary, GPU-accelerated)
      • EasyOCR (fallback for complex text)
      • Tesseract (fallback for printed text)
    ↓
[NexaAI Vision-Language Analysis]
  • Model: Qwen3-VL-4B-Instruct
  • Detailed product description
  • Feature detection (shape, color, material)
  • Size estimation
    ↓
[Structured Output]
{
  "description": "Detailed text description",
  "features": {
    "shape": "cylindrical",
    "color": "transparent",
    "material": "PET",
    "capacity_estimate": "50ml"
  },
  "ocr_text": "50ML PET",
  "visual_embedding": [1024-dim vector],
  "shape_embedding": [128-dim vector],
  "confidence": 0.92
}
```

## Embedding Storage

**Qdrant Collections**:
- `image_vectors` - Visual embeddings (1024-dim)
- `shape_vectors` - Shape descriptors (128-dim)
- `text_vectors` - Text embeddings (384-dim)

## Search Strategy

1. **Text-only search**: Use `text_vectors`
2. **Image-only search**: Use `image_vectors` + `shape_vectors`
3. **Hybrid search**: Combine all with Reciprocal Rank Fusion (RRF)
