# OCR Processing - Quick Start Guide

**Version**: 1.0.0
**Updated**: 2025-11-06
**For**: Developers implementing Phase 4.2

---

## 🚀 Quick Decision Tree

**Which OCR engine should I use?**

```
Input: Your document type
    │
    ├─ Korean product catalog, spec sheet
    │  → PaddleOCR (lang='korean')
    │  ✅ Best accuracy, fast, table support
    │
    ├─ Artistic fonts, logos, complex layouts
    │  → EasyOCR (['ko', 'en'])
    │  ✅ Handles unusual fonts well
    │
    ├─ Simple English documents
    │  → Tesseract (lang='eng')
    │  ✅ Lightweight, CPU-only
    │
    ├─ Handwritten notes
    │  → TrOCR (microsoft/trocr)
    │  ✅ Best for handwriting
    │
    └─ Not sure / Need reliability
       → Multi-Engine Ensemble
       ✅ Run all, merge with voting
```

---

## 📦 Installation

### Option 1: PaddleOCR Only (Recommended)

```bash
# Install PaddleOCR with all dependencies
pip install paddlepaddle paddleocr

# For Mac M4 (MPS support)
pip install paddlepaddle==2.6.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

# Verify installation
python -c "from paddleocr import PaddleOCR; print('✅ PaddleOCR ready')"
```

### Option 2: Multi-Engine Setup

```bash
# Install all OCR engines
pip install paddlepaddle paddleocr easyocr pytesseract

# Install Tesseract binary (Mac)
brew install tesseract tesseract-lang

# Verify all engines
python scripts/verify_ocr_engines.py
```

### Option 3: Full Stack (with Layout Analysis)

```bash
# Install all OCR + Layout + NER
pip install paddlepaddle paddleocr easyocr pytesseract \
            opencv-python pillow scikit-image \
            transformers torch sentencepiece

# For table extraction
pip install tabula-py camelot-py[cv]

# Verify
python scripts/verify_full_stack.py
```

---

## 🎯 Quick Examples

### Example 1: Basic OCR (PaddleOCR)

```python
#!/usr/bin/env python3
"""Basic PaddleOCR usage"""

from paddleocr import PaddleOCR
from PIL import Image

# Initialize (use GPU if available)
ocr = PaddleOCR(lang='korean', use_gpu=True)

# Process image
image_path = "data/product_catalog.jpg"
result = ocr.ocr(image_path)

# Extract text
for line in result[0]:
    bbox = line[0]  # Bounding box
    text = line[1][0]  # Text
    confidence = line[1][1]  # Confidence

    print(f"[{confidence:.2f}] {text}")

# Output:
# [0.95] 제품코드: PE-001234
# [0.92] SPEC: 100ml
# [0.88] Ø20
```

### Example 2: Multi-Engine with Fallback

```python
#!/usr/bin/env python3
"""Multi-engine OCR with automatic fallback"""

from paddleocr import PaddleOCR
import easyocr
import pytesseract
from PIL import Image

class MultiEngineOCR:
    def __init__(self):
        self.paddle = PaddleOCR(lang='korean', use_gpu=True)
        self.easy = easyocr.Reader(['ko', 'en'], gpu=True)

    def extract_text(self, image_path: str, min_confidence: float = 0.75):
        """Extract with automatic fallback"""

        # Try PaddleOCR first
        result = self.paddle.ocr(image_path)
        avg_conf = sum([line[1][1] for line in result[0]]) / len(result[0])

        if avg_conf >= min_confidence:
            print(f"✅ PaddleOCR success (confidence: {avg_conf:.2f})")
            return self._format_paddle(result)

        # Fallback to EasyOCR
        print("⚠️ PaddleOCR low confidence, trying EasyOCR...")
        result = self.easy.readtext(image_path)
        avg_conf = sum([line[2] for line in result]) / len(result)

        if avg_conf >= min_confidence:
            print(f"✅ EasyOCR success (confidence: {avg_conf:.2f})")
            return self._format_easy(result)

        # Fallback to Tesseract
        print("⚠️ EasyOCR low confidence, trying Tesseract...")
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='kor+eng')
        print("✅ Tesseract result (no confidence)")
        return text

    def _format_paddle(self, result):
        return "\n".join([line[1][0] for line in result[0]])

    def _format_easy(self, result):
        return "\n".join([line[1] for line in result])

# Usage
ocr = MultiEngineOCR()
text = ocr.extract_text("data/difficult_image.jpg")
print(text)
```

### Example 3: Table Extraction (PP-Structure)

```python
#!/usr/bin/env python3
"""Extract tables from images using PP-Structure"""

from paddleocr import PPStructure
import pandas as pd

# Initialize PP-Structure
table_engine = PPStructure(
    table=True,
    ocr=True,
    layout=True,
    lang='korean',
    use_gpu=True
)

def extract_table(image_path: str) -> pd.DataFrame:
    """Extract table and convert to DataFrame"""

    result = table_engine(image_path)

    # Find table regions
    tables = [item for item in result if item['type'] == 'table']

    if not tables:
        print("❌ No tables found")
        return None

    # Get first table
    table_data = tables[0]
    html = table_data.get('res', {}).get('html', '')

    if not html:
        print("❌ Failed to extract table structure")
        return None

    # Parse HTML to DataFrame
    df = pd.read_html(html)[0]
    print(f"✅ Extracted table: {df.shape[0]} rows, {df.shape[1]} cols")

    return df

# Usage
df = extract_table("data/product_table.png")
if df is not None:
    print(df.head())
    df.to_csv("data/extracted_table.csv", index=False)
```

### Example 4: Entity Extraction (Pattern-Based)

```python
#!/usr/bin/env python3
"""Extract structured entities from OCR text"""

import re
from typing import Dict, Any, Optional

class EntityExtractor:
    """Extract packaging product entities"""

    PATTERNS = {
        'product_code': r'([A-Z]{2,4}-\d{3,6})',
        'capacity': r'(\d+(?:\.\d+)?)\s*(ml|ML|L|cc)',
        'neck_size': r'(?:Ø|직경|목)\s*(\d{2,3})',
        'moq': r'MOQ[:\s]*(\d+(?:,\d{3})*)',
        'price': r'₩?\s*(\d+(?:,\d{3})*)\s*원?',
        'material': r'\b(PE|PET|PETG|PP|PVC|PS|HDPE|LDPE)\b'
    }

    def extract(self, text: str) -> Dict[str, Any]:
        """Extract all entities from text"""

        entities = {}

        for entity_type, pattern in self.PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities[entity_type] = match.group(1)

        return entities

    def extract_from_ocr(self, ocr_result, label: str,
                        direction: str = 'right') -> Optional[str]:
        """
        Position-based extraction

        Example: Find "SPEC" label, get text to the right
        """

        # Find label
        label_items = [
            item for item in ocr_result
            if label.lower() in item['text'].lower()
        ]

        if not label_items:
            return None

        label_item = label_items[0]
        label_x = label_item['x']
        label_y = label_item['y']

        # Find text in specified direction
        if direction == 'right':
            candidates = [
                item for item in ocr_result
                if item['x'] > label_x + 30
                and abs(item['y'] - label_y) < 20
            ]
        elif direction == 'below':
            candidates = [
                item for item in ocr_result
                if item['y'] > label_y + 20
                and abs(item['x'] - label_x) < 30
            ]

        if not candidates:
            return None

        # Get closest item
        closest = min(candidates, key=lambda x: abs(x['x'] - label_x))
        return closest['text']

# Usage
extractor = EntityExtractor()

# Pattern-based
text = "제품코드: PE-001234, SPEC: 100ml, Ø20, MOQ: 5000개"
entities = extractor.extract(text)
print(entities)
# {'product_code': 'PE-001234', 'capacity': '100', 'neck_size': '20', 'moq': '5000'}

# Position-based
ocr_result = [
    {'text': 'SPEC', 'x': 100, 'y': 50},
    {'text': '100ml', 'x': 200, 'y': 52},
    {'text': 'Ø20', 'x': 300, 'y': 50}
]
spec_value = extractor.extract_from_ocr(ocr_result, 'SPEC', 'right')
print(f"SPEC: {spec_value}")  # "100ml"
```

### Example 5: Full Pipeline (Image → Entities → Chunks)

```python
#!/usr/bin/env python3
"""Complete OCR → Entity Extraction → Chunking pipeline"""

from paddleocr import PaddleOCR
from src.core.enhanced_field_extractor import EnhancedFieldExtractor
from src.core.advanced_chunk_generator import AdvancedChunkGenerator
import json

class OCRToPipeline:
    """Image → OCR → Entities → Chunks → Qdrant"""

    def __init__(self):
        self.ocr = PaddleOCR(lang='korean', use_gpu=True)
        self.extractor = EnhancedFieldExtractor()
        self.chunker = AdvancedChunkGenerator()

    def process_image(self, image_path: str):
        """Full pipeline execution"""

        print(f"\n📸 Processing: {image_path}")

        # Stage 1: OCR
        print("  [1/4] Running OCR...")
        result = self.ocr.ocr(image_path)
        text_elements = self._format_ocr(result)
        print(f"    ✅ Extracted {len(text_elements)} text elements")

        # Stage 2: Entity Extraction
        print("  [2/4] Extracting entities...")
        entities = self._extract_entities(text_elements)
        print(f"    ✅ Found {len(entities)} entities")

        # Stage 3: Structure as Product
        print("  [3/4] Structuring as product...")
        product = self._structure_product(entities)
        print(f"    ✅ Product: {product.get('product_name', 'N/A')}")

        # Stage 4: Generate Chunks
        print("  [4/4] Generating atomic chunks...")
        chunks = self.chunker.generate_chunks(product)
        print(f"    ✅ Generated {len(chunks)} chunks")

        return {
            'product': product,
            'chunks': chunks,
            'raw_ocr': text_elements
        }

    def _format_ocr(self, result):
        """Convert PaddleOCR result to structured format"""
        elements = []
        for line in result[0]:
            bbox = line[0]
            text = line[1][0]
            confidence = line[1][1]

            x_center = sum([p[0] for p in bbox]) / 4
            y_center = sum([p[1] for p in bbox]) / 4

            elements.append({
                'text': text,
                'confidence': confidence,
                'x': x_center,
                'y': y_center,
                'bbox': bbox
            })
        return elements

    def _extract_entities(self, text_elements):
        """Extract entities using patterns"""
        # Combine text for pattern matching
        full_text = " ".join([el['text'] for el in text_elements])

        entities = {}

        # Extract product code
        match = re.search(r'([A-Z]{2,4}-\d{3,6})', full_text)
        if match:
            entities['product_code'] = match.group(1)

        # Extract capacity
        match = re.search(r'(\d+)\s*ml', full_text, re.IGNORECASE)
        if match:
            entities['capacity'] = match.group(1)

        # Extract neck
        match = re.search(r'Ø\s*(\d{2,3})', full_text)
        if match:
            entities['neck'] = match.group(1)

        # Extract MOQ
        match = re.search(r'MOQ[:\s]*(\d+)', full_text, re.IGNORECASE)
        if match:
            entities['moq'] = match.group(1)

        return entities

    def _structure_product(self, entities):
        """Convert entities to product JSON"""
        return {
            'product_id': entities.get('product_code', 'UNKNOWN'),
            'product_name': f"Product {entities.get('product_code', 'N/A')}",
            'category': 'Bottle',  # Default, could be classified
            'specifications': {
                'capacity': entities.get('capacity'),
                'neck': entities.get('neck'),
            },
            'pricing': {
                'moq': entities.get('moq')
            },
            'source': 'ocr_extraction'
        }

# Usage
pipeline = OCRToPipeline()
result = pipeline.process_image("data/product_spec_sheet.jpg")

# Save results
with open("data/ocr_result.json", 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)

print(f"\n✅ Pipeline complete!")
print(f"   Product: {result['product']['product_name']}")
print(f"   Chunks: {len(result['chunks'])}")
```

---

## 🛠️ Common Tasks

### Task 1: Batch Process Multiple Images

```python
from pathlib import Path
from tqdm import tqdm

def batch_process(input_dir: str, output_dir: str):
    """Process all images in directory"""

    images = list(Path(input_dir).glob("*.{jpg,png,jpeg}"))
    print(f"📦 Found {len(images)} images")

    pipeline = OCRToPipeline()

    for image_path in tqdm(images, desc="Processing"):
        try:
            result = pipeline.process_image(str(image_path))

            # Save result
            output_file = Path(output_dir) / f"{image_path.stem}_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            print(f"❌ Failed: {image_path.name} - {e}")

# Usage
batch_process("data/product_images", "data/ocr_results")
```

### Task 2: Upload to Qdrant

```python
from qdrant_client import QdrantClient
from src.core.embedding_service import EmbeddingService

def upload_chunks_to_qdrant(chunks, collection_name: str = "products_atomic"):
    """Upload extracted chunks to Qdrant"""

    client = QdrantClient(host="localhost", port=6333)
    embedding_service = EmbeddingService()

    for chunk in tqdm(chunks, desc="Uploading"):
        # Generate embedding
        embedding = embedding_service.generate_embedding(chunk['chunk_text'])

        # Upload to Qdrant
        client.upsert(
            collection_name=collection_name,
            points=[{
                'id': chunk['chunk_id'],
                'vector': embedding,
                'payload': chunk
            }]
        )

    print(f"✅ Uploaded {len(chunks)} chunks to {collection_name}")

# Usage
result = pipeline.process_image("data/product.jpg")
upload_chunks_to_qdrant(result['chunks'])
```

### Task 3: Quality Validation

```python
def validate_ocr_quality(ocr_result, min_confidence: float = 0.75):
    """Check OCR quality and flag issues"""

    total_elements = len(ocr_result)
    low_conf_count = sum(1 for el in ocr_result if el['confidence'] < min_confidence)

    quality_score = 1 - (low_conf_count / total_elements)

    print(f"📊 OCR Quality Report:")
    print(f"   Total elements: {total_elements}")
    print(f"   Low confidence: {low_conf_count} ({low_conf_count/total_elements*100:.1f}%)")
    print(f"   Quality score: {quality_score:.2f}")

    if quality_score < 0.7:
        print("⚠️ LOW QUALITY - Consider:")
        print("   1. Preprocess image (denoise, contrast)")
        print("   2. Try different OCR engine")
        print("   3. Manual review required")

        return False

    print("✅ GOOD QUALITY")
    return True

# Usage
result = ocr.ocr("data/image.jpg")
text_elements = pipeline._format_ocr(result)
is_valid = validate_ocr_quality(text_elements)
```

---

## 🔧 Troubleshooting

### Issue 1: Low OCR Accuracy

**Symptoms**: Confidence < 0.7, garbled text

**Solutions**:
```python
from PIL import Image, ImageEnhance
import cv2
import numpy as np

def preprocess_for_ocr(image_path: str) -> str:
    """Enhance image before OCR"""

    # Load image
    img = Image.open(image_path)

    # 1. Convert to grayscale
    img = img.convert('L')

    # 2. Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # 3. Sharpen
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)

    # 4. Denoise (OpenCV)
    img_array = np.array(img)
    img_array = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)

    # Save preprocessed
    output_path = image_path.replace('.jpg', '_preprocessed.jpg')
    cv2.imwrite(output_path, img_array)

    return output_path

# Usage
preprocessed = preprocess_for_ocr("data/low_quality.jpg")
result = ocr.ocr(preprocessed)  # Should have better accuracy
```

### Issue 2: Table Structure Lost

**Symptom**: Table cells extracted as flat text

**Solution**: Use PP-Structure
```python
from paddleocr import PPStructure

table_engine = PPStructure(table=True, layout=True)
result = table_engine("data/table.png")

# Find table regions
tables = [item for item in result if item['type'] == 'table']
for table in tables:
    html = table['res']['html']
    # Parse HTML to preserve structure
```

### Issue 3: Korean Characters Garbled

**Symptom**: Korean text shows as "���" or boxes

**Solution**: Ensure UTF-8 encoding
```python
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Verify Korean support
ocr = PaddleOCR(lang='korean')  # NOT 'kor' or 'kr'
```

### Issue 4: Memory Error (Large PDFs)

**Solution**: Process page by page
```python
from pdf2image import convert_from_path

def process_large_pdf(pdf_path: str):
    """Process PDF page by page to avoid memory issues"""

    images = convert_from_path(pdf_path, dpi=200)

    all_results = []
    for i, image in enumerate(images, 1):
        print(f"Processing page {i}/{len(images)}...")

        # Save temp image
        temp_path = f"/tmp/page_{i}.jpg"
        image.save(temp_path)

        # Process
        result = pipeline.process_image(temp_path)
        all_results.append(result)

        # Clean up
        os.remove(temp_path)

    return all_results
```

---

## 📊 Performance Tips

### Tip 1: Use GPU Acceleration

```python
# Mac M4 MPS support
ocr = PaddleOCR(lang='korean', use_gpu=True, use_mps=True)

# NVIDIA CUDA
ocr = PaddleOCR(lang='korean', use_gpu=True, gpu_id=0)

# Verify GPU usage
import torch
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"CUDA available: {torch.cuda.is_available()}")
```

### Tip 2: Batch Processing

```python
# Process multiple images in one call (faster)
results = ocr.ocr_batch([
    "image1.jpg",
    "image2.jpg",
    "image3.jpg"
])
```

### Tip 3: Lower Resolution for Speed

```python
from PIL import Image

def resize_for_speed(image_path: str, max_width: int = 1200):
    """Resize large images before OCR"""

    img = Image.open(image_path)

    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

        # Save temp
        temp_path = image_path.replace('.jpg', '_resized.jpg')
        img.save(temp_path)
        return temp_path

    return image_path
```

---

## 📚 Next Steps

1. **Read Full Strategy**: `docs/OCR_PARSING_STRATEGY.md`
2. **Review Roadmap**: `docs/ROADMAP.md` Phase 4.2
3. **Test with Your Data**: Run examples on your product images
4. **Integrate with Pipeline**: Connect to `enhanced_field_extractor.py`

---

**Quick Reference Commands**:

```bash
# Test PaddleOCR installation
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='korean'); print('✅')"

# Process single image
python scripts/process_image_ocr.py data/product.jpg

# Batch process directory
python scripts/batch_ocr_process.py --input data/images --output data/results

# Upload to Qdrant
python scripts/ocr_to_qdrant.py --collection onehago_v2
```

---

**Support**: See `docs/OCR_PARSING_STRATEGY.md` for detailed architecture

**Status**: Ready to use 🚀
