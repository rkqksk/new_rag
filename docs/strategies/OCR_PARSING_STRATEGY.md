# OCR & Parsing Strategy - Production-Grade Document Processing

**Version**: 1.0.0
**Status**: Design Document
**Updated**: 2025-11-06
**Related**: Phase 4.2 (Image Processing), Phase 4.1 (PDF Processing)

---

## 📊 Executive Summary

This document outlines a comprehensive, production-grade OCR and parsing strategy for RAG Enterprise, designed to handle diverse document types (PDFs, Images, Excel screenshots, product catalogs) with high accuracy and reliability.

**Key Goals**:
- 85%+ OCR accuracy for Korean + English mixed content
- Robust table extraction and layout preservation
- Automatic entity recognition (product specs, prices, MOQ)
- Multi-engine fallback for reliability
- Real-time processing (< 3 seconds per page)

---

## 🔍 Current State Analysis

### Existing Implementation

**Files**:
- `scripts/archive/experiments/paddleocr_excel_parser.py` (396 lines)
- `scripts/archive/experiments/quick_ocr_test.py` (219 lines)
- `app/services/image_search_service.py` (OpenCLIP for visual search)

**Current Capabilities**:
✅ PaddleOCR for Korean text extraction
✅ Excel → Image → OCR workflow
✅ Basic position-based parsing (CODE, SPEC labels)
✅ Visual similarity search (OpenCLIP)

**Gaps**:
❌ Single OCR engine (no fallback)
❌ No layout analysis (tables, multi-column)
❌ Manual parsing logic (hard-coded patterns)
❌ No confidence-based quality validation
❌ Limited post-processing (no NER)

---

## 🎯 Multi-Engine OCR Strategy

### Engine Comparison Matrix

| Engine | Korean Support | Speed | Accuracy | Table Detection | GPU Support | License | Best For |
|--------|---------------|-------|----------|----------------|-------------|---------|----------|
| **PaddleOCR** | ⭐⭐⭐ Excellent | ⚡⚡⚡ Fast | 🎯 85-90% | ✅ Yes (PP-Structure) | ✅ CUDA/MPS | Apache 2.0 | **General OCR, Tables** |
| **Tesseract 5** | ⭐⭐ Good | ⚡⚡ Medium | 🎯 75-85% | ❌ No | ❌ CPU only | Apache 2.0 | Simple text, Fallback |
| **EasyOCR** | ⭐⭐⭐ Excellent | ⚡ Slow | 🎯 80-85% | ❌ No | ✅ CUDA/MPS | Apache 2.0 | Artistic fonts, Complex layouts |
| **Doctr** | ⭐⭐ Good | ⚡⚡⚡ Fast | 🎯 80-90% | ✅ Yes | ✅ PyTorch | Apache 2.0 | Documents, End-to-end |
| **TrOCR** | ⭐⭐ Good | ⚡ Very Slow | 🎯 90-95% | ❌ No | ✅ Transformers | MIT | Handwriting, High accuracy |

### Recommended Strategy

**Primary**: PaddleOCR (Korean lang model)
**Fallback 1**: EasyOCR (if confidence < 0.7)
**Fallback 2**: Tesseract 5 (if both fail)
**Specialized**: TrOCR for handwritten notes

**Decision Tree**:
```
Input Image/PDF
    ↓
Preprocessing (Denoise, Deskew, Contrast)
    ↓
PaddleOCR (confidence threshold: 0.75)
    ↓
[Confidence < 0.75?]
    YES → EasyOCR (retry)
    NO → Continue
    ↓
[Still low confidence?]
    YES → Tesseract 5 (last resort)
    NO → Continue
    ↓
Post-processing → Entity Extraction
```

---

## 🏗️ Architecture Design

### Layer 1: Preprocessing Pipeline

**Goal**: Optimize image quality before OCR

**Techniques**:
```python
# src/core/ocr_processors/image_preprocessor.py

class ImagePreprocessor:
    """Advanced image preprocessing for OCR optimization"""

    def optimize_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Multi-stage preprocessing:
        1. Deskew (angle correction)
        2. Denoise (Gaussian blur)
        3. Binarization (Otsu's method)
        4. Contrast enhancement (CLAHE)
        5. Border removal
        """

    def detect_orientation(self, image: Image.Image) -> float:
        """Auto-detect rotation angle using Hough transform"""

    def enhance_text_regions(self, image: Image.Image) -> Image.Image:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)"""
```

**Key Libraries**:
- OpenCV (cv2) for morphological operations
- Pillow (PIL) for image manipulation
- scikit-image for advanced filters

### Layer 2: Multi-Engine OCR Core

**Goal**: Robust text extraction with automatic fallback

```python
# src/core/ocr_processors/ocr_engine.py

class MultiEngineOCR:
    """Orchestrate multiple OCR engines with confidence-based fallback"""

    def __init__(self):
        self.paddle_ocr = PaddleOCR(lang='korean', use_gpu=True)
        self.easy_ocr = easyocr.Reader(['ko', 'en'], gpu=True)
        self.tesseract_config = '--oem 3 --psm 6 -l kor+eng'

    def extract_text(self, image: Image.Image,
                     min_confidence: float = 0.75) -> OCRResult:
        """
        Multi-stage extraction:
        1. Try PaddleOCR (fastest, most accurate for Korean)
        2. If confidence < threshold, retry with EasyOCR
        3. If still low, fallback to Tesseract
        4. Merge results from multiple engines (voting)
        """

        result_paddle = self._extract_with_paddle(image)

        if result_paddle.avg_confidence < min_confidence:
            logger.warning("PaddleOCR low confidence, trying EasyOCR...")
            result_easy = self._extract_with_easyocr(image)

            # Merge results using confidence-weighted voting
            result = self._merge_results([result_paddle, result_easy])
        else:
            result = result_paddle

        return result

    def _merge_results(self, results: List[OCRResult]) -> OCRResult:
        """
        Intelligent merging:
        - For overlapping bboxes, keep highest confidence
        - For non-overlapping, combine all
        - Apply NMS (Non-Maximum Suppression) to remove duplicates
        """
```

**OCRResult Schema**:
```python
@dataclass
class OCRResult:
    text_elements: List[TextElement]
    avg_confidence: float
    processing_time_ms: float
    engine_used: str

@dataclass
class TextElement:
    text: str
    confidence: float
    bbox: List[List[float]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    position: Dict[str, float]  # {'x': center_x, 'y': center_y}
    language: str  # 'ko', 'en', 'mixed'
    text_type: str  # 'header', 'body', 'table', 'caption'
```

### Layer 3: Layout Analysis

**Goal**: Understand document structure before parsing

**Components**:

#### 3.1 Document Layout Detection

```python
# src/core/ocr_processors/layout_detector.py

class DocumentLayoutDetector:
    """
    Detect document regions using:
    - PaddleOCR PP-Structure (table detection)
    - LayoutLM/LayoutLMv3 (semantic segmentation)
    - YOLO for custom region detection
    """

    def detect_layout(self, image: Image.Image) -> LayoutResult:
        """
        Returns regions classified as:
        - Table
        - Text block (single/multi-column)
        - Image/Figure
        - Header/Footer
        - Form fields
        """

    def extract_reading_order(self, layout: LayoutResult) -> List[Region]:
        """
        Determine reading order:
        - Top-to-bottom for single column
        - Left-to-right, then top-to-bottom for multi-column
        - Special handling for tables
        """
```

**Models**:
- **PP-Structure** (PaddleOCR's layout analysis) - Fast, table-focused
- **LayoutLMv3** (Microsoft) - Best accuracy, slower
- **Detectron2** (Facebook) - Custom training possible

#### 3.2 Table Extraction

```python
# src/core/ocr_processors/table_extractor.py

class TableExtractor:
    """
    Specialized table extraction:
    1. Detect table boundaries
    2. Identify rows and columns
    3. Extract cell contents
    4. Reconstruct structure
    """

    def extract_table(self, image: Image.Image,
                      table_bbox: List[float]) -> TableResult:
        """
        Two-stage extraction:
        1. PP-StructureV2 for structure detection
        2. PaddleOCR for cell text extraction
        """

    def parse_merged_cells(self, cells: List[Cell]) -> Table:
        """Handle merged cells, rowspan, colspan"""

    def validate_table(self, table: Table) -> TableQuality:
        """
        Quality checks:
        - All cells extracted?
        - Proper alignment?
        - Missing values?
        """
```

**Output Format**:
```python
@dataclass
class TableResult:
    headers: List[str]  # Column headers
    rows: List[List[str]]  # Data rows
    structure: List[List[CellInfo]]  # Full structure with positions
    confidence: float
    empty_cells: int
```

### Layer 4: Entity Recognition & Parsing

**Goal**: Extract structured data from OCR text

#### 4.1 Pattern-Based Extraction

```python
# src/core/ocr_processors/entity_extractor.py

class EntityExtractor:
    """Extract domain-specific entities using patterns and NER"""

    # Pattern library for packaging industry
    PATTERNS = {
        'product_code': [
            r'[A-Z]{2,4}-\d{3,6}',  # PE-001234
            r'CODE[:\s]+([A-Z0-9-]+)',
        ],
        'neck_size': [
            r'(\d{2,3})파이',  # 20파이
            r'Ø\s*(\d{2,3})',  # Ø20
            r'(\d{2,3})\s*mm\s*neck',
        ],
        'capacity': [
            r'(\d+(?:\.\d+)?)\s*(ml|ML|L|cc)',
            r'용량[:\s]+(\d+)\s*ml',
        ],
        'moq': [
            r'MOQ[:\s]+(\d+(?:,\d{3})*)',
            r'최소주문[:\s]+(\d+)',
        ],
        'price': [
            r'₩?\s*(\d+(?:,\d{3})*)\s*원?',
            r'가격[:\s]+(\d+)',
        ],
        'material': [
            r'\b(PE|PET|PETG|PP|PVC|PS|HDPE|LDPE)\b',
        ]
    }

    def extract_entities(self, text_elements: List[TextElement]) -> Dict[str, Any]:
        """
        Extract all entities using:
        1. Regex patterns (fast, deterministic)
        2. Position-based heuristics (e.g., price next to "단가")
        3. NER model (for complex cases)
        """

    def extract_with_position(self, text_elements: List[TextElement],
                              label_text: str,
                              search_direction: str = 'right') -> Optional[str]:
        """
        Position-based extraction:
        - Find label (e.g., "SPEC")
        - Search in direction (right, below, etc.)
        - Extract nearest text element
        """
```

#### 4.2 Named Entity Recognition (NER)

```python
# src/core/ocr_processors/ner_model.py

class ProductNER:
    """
    Custom NER model trained on packaging domain

    Entities:
    - PRODUCT_NAME: 제품명
    - PRODUCT_CODE: 제품 코드
    - SPEC: 규격 (용량, 사이즈)
    - NECK: 목 크기
    - MOQ: 최소 주문량
    - PRICE: 가격
    - MATERIAL: 재질
    - CATEGORY: 분류 (Bottle/Jar/Cap/Pump)
    """

    def __init__(self):
        # Fine-tune KoBERT or KoELECTRA for NER
        self.model = AutoModelForTokenClassification.from_pretrained(
            "monologg/koelectra-base-v3-discriminator"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            "monologg/koelectra-base-v3-discriminator"
        )

    def predict(self, text: str) -> List[Entity]:
        """
        Extract entities using transformer-based NER
        Returns: [(entity_text, entity_type, confidence)]
        """

    def train_on_domain_data(self, training_data: List[Tuple[str, List[Entity]]]):
        """Fine-tune on annotated packaging documents"""
```

**Training Data Format** (for NER):
```json
[
  {
    "text": "PE-001234 제품 SPEC: 100ml, Ø20 MOQ: 5000개",
    "entities": [
      {"start": 0, "end": 9, "label": "PRODUCT_CODE", "text": "PE-001234"},
      {"start": 18, "end": 23, "label": "SPEC", "text": "100ml"},
      {"start": 25, "end": 28, "label": "NECK", "text": "Ø20"},
      {"start": 34, "end": 38, "label": "MOQ", "text": "5000"}
    ]
  }
]
```

### Layer 5: Post-Processing & Validation

**Goal**: Clean, validate, and structure extracted data

```python
# src/core/ocr_processors/post_processor.py

class OCRPostProcessor:
    """Post-processing pipeline for OCR results"""

    def clean_text(self, text: str) -> str:
        """
        Text cleaning:
        - Remove OCR artifacts (▶, ■, □)
        - Fix common Korean OCR errors (ㅇ → O, etc.)
        - Normalize whitespace
        - Fix broken words
        """

    def validate_entities(self, entities: Dict[str, Any]) -> ValidationResult:
        """
        Entity validation:
        - Product code format check
        - Numeric field validation (capacity, price, MOQ)
        - Cross-field consistency (e.g., PET bottle shouldn't have PP material)
        """

    def confidence_scoring(self, ocr_result: OCRResult,
                          entities: Dict[str, Any]) -> float:
        """
        Overall confidence score:
        - OCR confidence (0-1)
        - Entity extraction confidence (0-1)
        - Layout detection confidence (0-1)
        - Validation score (0-1)

        Final score = weighted average
        """
```

**Validation Rules**:
```python
VALIDATION_RULES = {
    'product_code': {
        'regex': r'^[A-Z]{2,4}-\d{3,6}$',
        'required': True,
        'min_confidence': 0.8
    },
    'capacity': {
        'type': 'numeric',
        'min': 1,
        'max': 10000,  # ml
        'unit': ['ml', 'L', 'cc']
    },
    'moq': {
        'type': 'integer',
        'min': 100,
        'max': 1000000
    },
    'neck': {
        'regex': r'^\d{2,3}$',  # Numeric only (파이 removed)
        'common_values': [13, 15, 18, 20, 24, 28, 38, 43, 53]  # Standard sizes
    }
}
```

---

## 📦 Implementation Architecture

### Unified OCR Pipeline

```python
# src/core/ocr_processors/ocr_pipeline.py

class OCRPipeline:
    """
    End-to-end OCR processing pipeline

    Workflow:
    1. Preprocessing
    2. Multi-engine OCR
    3. Layout analysis
    4. Entity extraction
    5. Post-processing
    6. Validation
    7. Chunking & Embedding
    """

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = MultiEngineOCR()
        self.layout_detector = DocumentLayoutDetector()
        self.table_extractor = TableExtractor()
        self.entity_extractor = EntityExtractor()
        self.ner_model = ProductNER()
        self.post_processor = OCRPostProcessor()

    async def process_document(self,
                              file_path: str,
                              document_type: str = 'auto') -> ProcessedDocument:
        """
        Full pipeline execution

        Args:
            file_path: Path to image or PDF
            document_type: 'catalog', 'invoice', 'spec_sheet', 'table', 'auto'

        Returns:
            Structured, validated, chunk-ready document
        """

        # Stage 1: Load and preprocess
        image = self._load_image(file_path)
        optimized_image = self.preprocessor.optimize_for_ocr(image)

        # Stage 2: Layout detection
        layout = self.layout_detector.detect_layout(optimized_image)

        # Stage 3: Process each region
        processed_regions = []
        for region in layout.regions:
            if region.type == 'table':
                # Table-specific processing
                table = self.table_extractor.extract_table(optimized_image, region.bbox)
                processed_regions.append(table)
            else:
                # Standard OCR
                region_image = self._crop_region(optimized_image, region.bbox)
                ocr_result = self.ocr_engine.extract_text(region_image)
                processed_regions.append(ocr_result)

        # Stage 4: Entity extraction
        all_text_elements = self._merge_regions(processed_regions)
        entities = self.entity_extractor.extract_entities(all_text_elements)

        # Use NER for complex extraction
        text_combined = " ".join([el.text for el in all_text_elements])
        ner_entities = self.ner_model.predict(text_combined)

        # Merge pattern-based and NER entities
        final_entities = self._merge_entities(entities, ner_entities)

        # Stage 5: Post-processing
        cleaned_entities = self.post_processor.clean_entities(final_entities)
        validation = self.post_processor.validate_entities(cleaned_entities)
        confidence = self.post_processor.confidence_scoring(
            all_text_elements, cleaned_entities
        )

        # Stage 6: Structure as Product
        product = self._structure_as_product(cleaned_entities, validation)

        return ProcessedDocument(
            product=product,
            raw_ocr=all_text_elements,
            entities=cleaned_entities,
            validation=validation,
            confidence=confidence,
            processing_time_ms=processing_time
        )
```

### Integration with Existing RAG Pipeline

```python
# Connect to existing enhanced_field_extractor.py

from src.core.ocr_processors.ocr_pipeline import OCRPipeline
from src.core.enhanced_field_extractor import EnhancedFieldExtractor
from src.core.advanced_chunk_generator import AdvancedChunkGenerator

class MultiModalProcessor:
    """Process any input format (JSON, PDF, Image, Excel) → Chunks"""

    def __init__(self):
        self.ocr_pipeline = OCRPipeline()
        self.field_extractor = EnhancedFieldExtractor()
        self.chunk_generator = AdvancedChunkGenerator()

    async def process_file(self, file_path: str) -> List[AtomicChunk]:
        """
        Unified processing:
        - JSON → Field Extraction (existing)
        - PDF/Image → OCR → Field Extraction (new)
        - Excel → OCR or Parser (Phase 4.3 + new OCR)
        """

        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.json':
            # Existing JSON pipeline
            with open(file_path, 'r') as f:
                product_data = json.load(f)
        elif file_ext in ['.pdf', '.png', '.jpg', '.jpeg']:
            # New OCR pipeline
            processed = await self.ocr_pipeline.process_document(file_path)
            product_data = processed.product
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            # Hybrid: Use Excel parser + OCR for images
            product_data = self._process_spreadsheet(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        # Common path: Field extraction → Chunking
        extracted_fields = self.field_extractor.extract_from_product(product_data)
        chunks = self.chunk_generator.generate_chunks(extracted_fields)

        return chunks
```

---

## 🛠️ Technology Stack

### Core Libraries

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| **OCR** | PaddlePaddle & PaddleOCR | 2.6+ | Primary OCR engine |
| | EasyOCR | 1.7+ | Fallback OCR |
| | Tesseract | 5.3+ | Last resort OCR |
| | Doctr | 0.7+ | Alternative document OCR |
| **Layout Analysis** | PP-Structure | 2.6+ | Table detection (PaddleOCR) |
| | LayoutLMv3 | Latest | Semantic layout analysis |
| | Detectron2 | 0.6+ | Custom region detection |
| **Image Processing** | OpenCV | 4.8+ | Preprocessing, morphology |
| | Pillow | 10.0+ | Image I/O, basic ops |
| | scikit-image | 0.21+ | Advanced filters |
| **NER** | Transformers | 4.30+ | KoBERT/KoELECTRA NER |
| | spaCy | 3.6+ | Text processing |
| **Table Extraction** | tabula-py | 2.8+ | PDF table extraction |
| | camelot-py | 0.11+ | Advanced PDF tables |

### Hardware Acceleration

**Mac M4 Support**:
- PaddleOCR with MPS (Metal Performance Shaders)
- PyTorch with MPS backend
- TensorFlow with Metal plugin

**Configuration**:
```python
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

# PaddleOCR with MPS
ocr = PaddleOCR(lang='korean', use_gpu=True, use_mps=True)
```

---

## 🚀 Implementation Roadmap

### Phase 4.2.1: Core OCR Engine (Week 1-2)

**Deliverables**:
- `src/core/ocr_processors/image_preprocessor.py`
- `src/core/ocr_processors/ocr_engine.py` (Multi-engine)
- `src/core/ocr_processors/ocr_result.py` (Data models)

**Tasks**:
1. Install PaddleOCR, EasyOCR, Tesseract
2. Implement preprocessing pipeline
3. Implement multi-engine fallback logic
4. Unit tests with sample images

**Success Metrics**:
- ✅ OCR accuracy >85% on Korean+English documents
- ✅ Processing speed <2 seconds per page
- ✅ Fallback mechanism working correctly

### Phase 4.2.2: Layout Analysis (Week 3-4)

**Deliverables**:
- `src/core/ocr_processors/layout_detector.py`
- `src/core/ocr_processors/table_extractor.py`
- `src/core/ocr_processors/reading_order.py`

**Tasks**:
1. Integrate PP-Structure for table detection
2. Implement region classification (text/table/image)
3. Implement table extraction pipeline
4. Test with complex multi-column documents

**Success Metrics**:
- ✅ Table detection accuracy >90%
- ✅ Correct reading order for multi-column layouts
- ✅ Merged cell handling

### Phase 4.2.3: Entity Recognition & NER (Week 5-6)

**Deliverables**:
- `src/core/ocr_processors/entity_extractor.py`
- `src/core/ocr_processors/ner_model.py`
- `src/core/ocr_processors/post_processor.py`
- Annotated training data (100+ samples)

**Tasks**:
1. Implement pattern-based extraction
2. Fine-tune KoELECTRA for NER
3. Annotate 100+ product documents
4. Implement post-processing pipeline
5. Add validation rules

**Success Metrics**:
- ✅ Entity extraction accuracy >90% (product code, spec, neck, MOQ)
- ✅ NER model F1 score >0.85
- ✅ Post-processing reduces errors by 30%

### Phase 4.2.4: Integration & Testing (Week 7-8)

**Deliverables**:
- `src/core/ocr_processors/ocr_pipeline.py`
- `src/core/multimodal_processor.py`
- End-to-end tests
- Performance benchmarks

**Tasks**:
1. Integrate with existing RAG pipeline
2. Create unified processor (JSON/PDF/Image/Excel)
3. End-to-end testing with 100+ documents
4. Performance optimization
5. Documentation

**Success Metrics**:
- ✅ End-to-end accuracy >85%
- ✅ Processing speed: <3 seconds per page
- ✅ Seamless integration with existing pipeline
- ✅ 100+ test cases passing

---

## 📊 Quality Assurance

### Test Cases

**OCR Accuracy Tests**:
```python
# tests/test_ocr_accuracy.py

def test_korean_text_accuracy():
    """Test Korean text extraction accuracy"""
    test_images = [
        "tests/data/korean_catalog_page1.png",
        "tests/data/korean_spec_sheet.jpg",
    ]
    for image_path in test_images:
        result = ocr_engine.extract_text(image_path)
        ground_truth = load_ground_truth(image_path)
        accuracy = calculate_accuracy(result.text, ground_truth)
        assert accuracy > 0.85, f"Low accuracy: {accuracy}"

def test_table_extraction():
    """Test table structure preservation"""
    result = table_extractor.extract_table("tests/data/product_table.png")
    assert len(result.headers) == 5  # Expected columns
    assert len(result.rows) == 10  # Expected rows
    assert result.confidence > 0.8

def test_entity_extraction():
    """Test entity recognition accuracy"""
    text = "PE-001234 제품 SPEC: 100ml, Ø20 MOQ: 5000개"
    entities = entity_extractor.extract_entities(text)
    assert entities['product_code'] == 'PE-001234'
    assert entities['capacity'] == '100ml'
    assert entities['neck'] == '20'
    assert entities['moq'] == '5000'
```

### Performance Benchmarks

**Target Metrics**:

| Document Type | Pages | Processing Time | Accuracy | Memory |
|--------------|-------|----------------|----------|--------|
| Product Catalog | 10 | <30s | >85% | <2GB |
| Spec Sheet | 1 | <3s | >90% | <1GB |
| Excel Screenshot | 1 | <2s | >90% | <1GB |
| Invoice | 1 | <2s | >85% | <1GB |

### Error Handling

**Common Issues & Mitigations**:

1. **Low OCR Confidence**
   - Mitigation: Multi-engine fallback
   - Action: Flag for manual review if all engines fail

2. **Table Misalignment**
   - Mitigation: Use PP-Structure + post-processing
   - Action: Validate cell count, retry with different params

3. **Entity Extraction Failures**
   - Mitigation: Combine regex + NER + position heuristics
   - Action: Mark entity as "uncertain", require validation

4. **Memory Issues (Large PDFs)**
   - Mitigation: Page-by-page processing
   - Action: Batch processing with queue

---

## 🔗 Integration Points

### With Existing Phase 4.3 (Excel/CSV)

```python
# Enhanced file processor with OCR support

class UnifiedFileProcessor:
    """Process any file format with appropriate strategy"""

    def process_excel(self, file_path: str, use_ocr: bool = False):
        """
        Two modes:
        1. Direct parsing (Phase 4.3 existing)
        2. OCR-based (for complex/image-based Excel)
        """
        if use_ocr or self._needs_ocr(file_path):
            # Convert Excel → Image → OCR
            return self.ocr_pipeline.process_document(file_path)
        else:
            # Direct pandas parsing
            return self.excel_parser.parse_file(file_path)

    def _needs_ocr(self, file_path: str) -> bool:
        """
        Detect if Excel has images/complex layout
        - Check for embedded images
        - Check for merged cells > 30%
        - Check for irregular structure
        """
```

### With Phase 8.2 (Caching)

```python
# Cache OCR results to avoid reprocessing

class CachedOCRPipeline:
    """OCR with Redis caching"""

    def process_document(self, file_path: str) -> ProcessedDocument:
        # Generate file hash
        file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()

        # Check cache
        cached = self.cache_manager.get(f"ocr:{file_hash}")
        if cached:
            return cached

        # Process and cache
        result = self.ocr_pipeline.process_document(file_path)
        self.cache_manager.set(f"ocr:{file_hash}", result, ttl=86400)  # 24h

        return result
```

---

## 💡 Advanced Techniques

### 1. Ensemble OCR

Combine multiple OCR engines' results using voting:

```python
def ensemble_ocr(image: Image.Image) -> str:
    """
    Run 3 OCR engines, merge results
    - PaddleOCR
    - EasyOCR
    - Tesseract

    Use character-level voting:
    If 2/3 engines agree on a character, keep it
    """
    results = [
        paddle_ocr.extract(image),
        easy_ocr.extract(image),
        tesseract_ocr.extract(image)
    ]

    merged = character_level_voting(results)
    return merged
```

### 2. Active Learning for NER

Automatically improve NER model:

```python
class ActiveLearningNER:
    """
    Continuously improve NER with user feedback

    1. User corrects entity extraction
    2. Save as training example
    3. Retrain model weekly
    """

    def collect_feedback(self, document_id: str,
                        corrected_entities: Dict[str, Any]):
        """Store corrections for retraining"""

    def retrain_model(self, min_samples: int = 50):
        """Retrain when enough corrections accumulated"""
```

### 3. Domain-Specific OCR Models

Train custom PaddleOCR models for packaging domain:

```bash
# Fine-tune PaddleOCR on packaging-specific data
python tools/train.py \
  -c configs/rec/PP-OCRv4/en_PP-OCRv4_rec.yml \
  -o Global.pretrained_model=./pretrain_models/en_PP-OCRv4_rec_train/best_model \
  -o Train.dataset.data_dir=./train_data/packaging
```

---

## 📚 References

### Documentation
- [PaddleOCR Docs](https://github.com/PaddlePaddle/PaddleOCR/blob/main/README_en.md)
- [PP-Structure Table Recognition](https://github.com/PaddlePaddle/PaddleOCR/blob/main/ppstructure/README.md)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [LayoutLMv3](https://huggingface.co/docs/transformers/model_doc/layoutlmv3)

### Papers
- "PP-OCRv4: A New Model for OCR" (Baidu Research, 2023)
- "LayoutLMv3: Pre-training for Document AI" (Microsoft, 2022)
- "TrOCR: Transformer-based Optical Character Recognition" (Microsoft, 2021)

### Related Files
- `docs/ROADMAP.md` - Phase 4.2 implementation plan
- `src/core/enhanced_field_extractor.py` - Field extraction logic
- `src/core/advanced_chunk_generator.py` - Chunking pipeline
- `scripts/archive/experiments/paddleocr_excel_parser.py` - Existing OCR prototype

---

**Next Steps**:
1. Review this strategy document
2. Set up OCR development environment
3. Begin Phase 4.2.1 implementation
4. Create test dataset with ground truth annotations

**Status**: Ready for implementation 🚀
