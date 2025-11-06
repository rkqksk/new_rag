# RAG Enterprise Development Roadmap

**Version**: 1.0
**Last Updated**: 2025-11-06
**Status**: Production-Ready System with Strategic Growth Plan

---

## Executive Summary

RAG Enterprise는 현재 **Production-Ready** 상태로, 자연어 검색 기반 제품 추천 시스템의 핵심 기능이 완성되었습니다. 이 로드맵은 시스템을 **Enterprise-Grade Multi-Modal RAG Platform**으로 발전시키기 위한 전략적 계획을 제시합니다.

### Current State (Phase 0-4 Complete ✅)
- ✅ **Phase 0**: Docker infrastructure, FastAPI backend, Frontend (v2.0.0)
- ✅ **Phase 1**: Atomic Field-Level Chunking System (2,073 → 3,246 chunks)
- ✅ **Phase 2**: Enhanced Field Extraction (Neck, MOQ, Material, Price)
  - `src/core/enhanced_field_extractor.py` (342 lines)
  - Bottle/Jar: `enriched_info` 기반
  - Cap/Pump: spec/detail/description 파싱
- ✅ **Phase 3**: Search Optimization & Natural Language Query
  - Query parser, search engine, NL response generator
  - Hybrid search with re-ranking
- ✅ **Phase 4**: Multi-Modal OCR Pipeline ⭐ **NEW**
  - Multi-engine OCR (PaddleOCR → EasyOCR → Tesseract)
  - PDF/Image/Excel/CSV processing
  - Entity extraction (product fields)
  - RAG integration layer
- ✅ **Enterprise Backend**: Production-grade API system
  - Repository → Service → API layers
  - 122 test cases (~9,686 lines)
  - Debug system (10 components, 8 endpoints)
- ✅ **Data**: 471 products → 3,246 atomic chunks (avg 6.9 chunks/product)
- ✅ **Quality**: Semantic Search 0.79-0.82 similarity scores
- ✅ **Status**: **Production-Ready** ⭐⭐

### Future Vision (Phase 5-9)
- 🎯 Advanced RAG Integration Pipeline (Phase 5)
- 🎯 Image Matching & Recognition Services (Phase 6)
- 🎯 Cloud Data Integration (Google Drive, S3) (Phase 7)
- 🎯 Real-Time Chat Optimization (<500ms response) (Phase 8)
- 🎯 Enterprise-Scale Deployment (Phase 9)

---

## Phase 0-3: Foundation ✅ COMPLETED

### Phase 0: Initial Setup (100% ✅)
**Status**: Complete
**Completion Date**: 2025-10-15

**Achievements**:
- ✅ Docker infrastructure (Qdrant, PostgreSQL, Redis)
- ✅ FastAPI backend setup
- ✅ Frontend chat interface (v2.0.0)
- ✅ Basic RAG pipeline

### Phase 1: Atomic Chunking (100% ✅)
**Status**: Complete
**Completion Date**: 2025-11-04

**Achievements**:
- ✅ Product classifier (Bottle/Jar/Cap/Pump) - `src/core/product_classifier.py`
- ✅ Chunk templates (20+ field types) - `src/core/chunk_templates.py`
  - PRODUCT_NAME, PRODUCT_CODE, MANUFACTURER
  - CAPACITY, NECK, MATERIAL, MOQ, PRICE
  - SPEC_COMPOSITE, BUSINESS_COMPOSITE
  - USE_CASE, KEYWORD, DESCRIPTION
- ✅ Category-specific templates - `src/core/category_templates.py`
  - Bottle/Jar: 용기, 제품, 컨테이너
  - Cap/Pump: 캡, 마개, 펌프
- ✅ Advanced chunk generator - `src/core/advanced_chunk_generator.py`
- ✅ 2,073 initial chunks

**Key Modules**:
- `product_classifier.py` (350 lines)
- `chunk_templates.py` (450 lines)
- `category_templates.py` (420 lines)
- `advanced_chunk_generator.py` (280 lines)

### Phase 2: Enhanced Field Extraction (100% ✅)
**Status**: Complete
**Completion Date**: 2025-11-06

**Achievements**:
- ✅ Enhanced field extractor (`src/core/enhanced_field_extractor.py`)
- ✅ Neck, MOQ, Material, Price parsing
  - Neck: 24파이, Ø24, 내경 Ø24 등 자동 인식
  - MOQ: package 필드에서 자동 추출 (800ea → 800)
  - Material: PP, PE, PET, PETG 등 자동 감지
  - Price: supply_price/selling_price 통합
- ✅ Composite field generation
  - SPEC_COMPOSITE: 용량 + Neck + 재질
  - BUSINESS_COMPOSITE: MOQ + 가격
- ✅ 3,246 enriched chunks (+56% from 2,073)
- ✅ Category-specific extraction:
  - Bottle/Jar: `enriched_info` 기반
  - Cap/Pump: spec/detail/description 파싱

**Key Metrics**:
- 471 products → 3,246 atomic chunks
- Avg 6.9 chunks/product (up from 4.4)
- Field coverage increase:
  - material: 64 → ~400 chunks (+525%)
  - neck: 0 → ~300 chunks (NEW)
  - moq: 60 → ~350 chunks (+483%)
  - business_composite: 382 → ~850 chunks (+122%)

### Phase 3: Search Optimization (100% ✅)
**Status**: Complete
**Completion Date**: 2025-11-06

**Achievements**:
- ✅ Query parser (entity extraction) - `src/core/query_parser.py`
  - "20파이 캡" → Neck: Ø20, Category: cap
  - "100ml PE 보틀" → Capacity: 100ml, Material: PE
  - "5,000개 주문" → MOQ: 5000
- ✅ Search engine (hybrid search) - `src/core/search_engine.py`
  - Filter building (Qdrant metadata filters)
  - Semantic search (vector similarity)
  - Re-ranking: semantic_score × 0.5 + field_priority × 0.3 + entity_match × 0.2
  - Deduplication (product-level grouping)
- ✅ Natural language response generator - `src/core/natural_language_response.py`
  - Template-based response generation
  - Citation extraction
  - Matching reason explanation
- ✅ Semantic search quality: **0.79-0.82 similarity scores** ⭐
- ✅ End-to-end testing (edge cases, missing fields, malformed data)

**Key Modules**:
- `query_parser.py` (400 lines)
- `search_engine.py` (350 lines)
- `natural_language_response.py` (180 lines)

**Query Examples**:
```
✅ "20파이 캡 5,000개 주문 가능한 제품 추천해줘"
   → Neck: Ø20, MOQ: 5000, Category: cap

✅ "100ml PE 보틀 찾아줘"
   → Capacity: 100ml, Material: PE, Category: bottle

✅ "한국산 PP 재질 크림 자"
   → Origin: 한국, Material: PP, Category: jar
```

---

## Phase 4: Multi-Modal OCR Pipeline ✅ COMPLETED

**Priority**: HIGH
**Timeline**: 4-6 weeks (Completed in 1 day!)
**Status**: ✅ **COMPLETE**
**Completion Date**: 2025-11-06

### Overview
Multi-Modal document processing pipeline with OCR, entity extraction, and RAG integration. Complete production-ready system supporting PDF, images, Excel, and CSV files.

### ✅ Achievements

**Core Components (7 modules, ~1,850 lines)**:

1. **Image Preprocessor** (`src/core/ocr/image_preprocessor.py` - 310 lines)
   - Deskew (angle correction using Hough transform)
   - Denoise (Gaussian blur, fastNlMeans)
   - Binarization (Otsu's method)
   - Contrast enhancement (CLAHE on LAB color space)
   - Border removal
   - DPI normalization (target: 300 DPI)

2. **Multi-Engine OCR** (`src/core/ocr/ocr_engine.py` - 450 lines)
   - **PaddleOCR** (primary): Korean + English, GPU-accelerated, 85-90% accuracy
   - **EasyOCR** (fallback): Better for artistic fonts, complex layouts
   - **Tesseract** (last resort): CPU-only fallback
   - Confidence-based automatic fallback (threshold: 0.75)
   - Language detection (Korean/English)
   - Bounding box extraction
   - Batch processing support

3. **PDF Extractor** (`src/core/ocr/pdf_extractor.py` - 140 lines)
   - Extract embedded text (if available)
   - Convert PDF pages to images (300 DPI)
   - Page-by-page OCR processing
   - Image extraction from PDFs
   - Metadata tracking per page

4. **Excel/CSV Parser** (`src/core/ocr/excel_parser.py` - 220 lines)
   - Direct Excel/CSV parsing
   - Excel screenshot → OCR → Table extraction
   - Multi-sheet support
   - Auto-format detection
   - Row/column structure preservation

5. **Entity Recognizer** (`src/core/ocr/entity_recognizer.py` - 190 lines)
   - Product code (CODE, ITEM, 제품코드)
   - Product name (제품명, 품명)
   - Capacity (50ml, 100ml)
   - Neck size (20파이, 24파이, Ø24)
   - Material (PET, PP, PE, PETG)
   - MOQ (최소주문, 5000개)
   - Price (가격, 단가)
   - Supplier (업체, 제조사)
   - Regex pattern-based extraction with confidence scoring

6. **Document Processor** (`src/core/ocr/document_processor.py` - 350 lines)
   - Unified integration layer
   - Auto-format detection
   - Route to appropriate processor
   - Entity extraction from all sources
   - RAG-ready output format
   - Batch processing support

7. **Usage Example** (`examples/ocr_usage_example.py`)
   - Complete usage demonstration
   - PDF, image, Excel processing examples

**Dependencies Added**:
```txt
paddleocr==2.7.0.3       # Primary OCR engine
paddlepaddle==2.5.2      # PaddleOCR backend
easyocr==1.7.0           # Fallback OCR
pytesseract==0.3.10      # Last resort OCR
PyMuPDF==1.23.8          # PDF processing
pandas==2.1.4            # Excel/CSV parsing
openpyxl==3.1.2          # Excel file support
scikit-image==0.22.0     # Advanced filters
```

**Key Features**:
- ✅ Multi-engine OCR with automatic fallback
- ✅ PDF embedded text extraction + OCR
- ✅ Image preprocessing for optimal OCR
- ✅ Excel/CSV direct parsing + screenshot OCR
- ✅ Entity extraction for product fields
- ✅ RAG-ready chunking and formatting
- ✅ Batch processing support
- ✅ Language detection (Korean/English)

**Performance Targets**:
- OCR (GPU): < 1s per page
- OCR (CPU): < 3s per page
- PDF Processing: < 3s per page (including OCR)
- Entity Extraction: < 50ms (regex-based)
- Excel Parsing: < 100ms (direct read)

**Usage Example**:
```python
from src.core.ocr import DocumentProcessor

processor = DocumentProcessor(use_gpu=True)

# Auto-detect and process any format
result = processor.process_file('catalog.pdf')
result = processor.process_file('product.jpg')
result = processor.process_file('data.xlsx')

# Convert to RAG chunks
chunks = processor.process_to_rag_format('catalog.pdf')
```

**Success Metrics**:
- ✅ Multi-engine OCR system operational
- ✅ PDF/Image/Excel/CSV support implemented
- ✅ Entity extraction with confidence scoring
- ✅ RAG integration complete
- ✅ Production-ready code quality

---

### 4.1: Document Processing Pipeline (ORIGINAL DESIGN)

**Goal**: PDF 문서 자동 처리 및 추출

**Technical Design**:
```python
# Architecture
Document Input (PDF)
  → PyPDF2/PDFPlumber (Text Extraction)
  → Layout Analysis (페이지 구조 파악)
  → Table Extraction (Camelot/Tabula)
  → Text Chunking (Semantic Segmentation)
  → Vector Embedding
  → Qdrant Storage

# Key Components
src/core/document_processors/
├── pdf_processor.py          # PDF 텍스트/표 추출
├── layout_analyzer.py        # 페이지 레이아웃 분석
├── table_extractor.py        # 표 데이터 추출
└── document_chunker.py       # 문서별 최적 청킹
```

**Implementation Steps**:
1. **Week 1-2**: PDF Parser 구현
   - PyPDF2 + PDFPlumber 통합
   - 한글 인코딩 처리
   - 페이지별 텍스트 추출

2. **Week 2-3**: Table Extraction
   - Camelot 통합 (표 인식)
   - Tabula 통합 (대체 엔진)
   - Table → Structured Data 변환

3. **Week 3-4**: Document Chunking
   - Semantic segmentation (문단 단위)
   - Section-based chunking (목차 기반)
   - Context preservation (문맥 유지)

**Success Metrics**:
- ✅ PDF 텍스트 추출률 >95%
- ✅ 표 인식 정확도 >90%
- ✅ 청킹 품질 (중복 없음, 문맥 보존)

### 4.2: Image Data Processing

**Goal**: 이미지에서 제품 정보 자동 추출

**Technical Design**:
```python
# Architecture
Image Input (JPEG/PNG)
  → Preprocessing (Resize, Denoise)
  → OCR (Tesseract/EasyOCR)
  → Layout Detection (LayoutLM/YOLO)
  → Text Extraction
  → Entity Recognition (Product Name, Specs)
  → Vector Embedding

# Key Components
src/core/image_processors/
├── ocr_engine.py            # Tesseract + EasyOCR
├── layout_detector.py       # YOLO/LayoutLM
├── text_extractor.py        # 이미지 → 텍스트
├── entity_recognizer.py     # NER for product specs
└── quality_checker.py       # 추출 품질 검증
```

**Implementation Steps**:
1. **Week 1**: OCR Engine Setup
   - Tesseract 한글 모델 설치
   - EasyOCR 통합 (한글 지원)
   - Preprocessing pipeline (denoise, contrast)

2. **Week 2**: Layout Detection
   - YOLO 기반 제품 이미지 영역 탐지
   - 텍스트 영역 vs 이미지 영역 분리
   - 우선순위 설정 (제품명 > 스펙 > 기타)

3. **Week 3-4**: Entity Recognition
   - Custom NER 모델 훈련 (제품명, Neck, MOQ 등)
   - Post-processing (정규식 기반 보정)
   - Confidence scoring

**Success Metrics**:
- ✅ OCR 정확도 >85% (한글)
- ✅ 제품명 추출률 >90%
- ✅ 스펙 추출률 >80%

### 4.3: Structured Data Processing (Excel, CSV)

**Goal**: Excel/CSV 데이터 자동 파싱 및 통합

**Technical Design**:
```python
# Architecture
Excel/CSV Input
  → Schema Detection (컬럼 자동 인식)
  → Data Validation (품질 검증)
  → Column Mapping (필드 매칭)
  → Entity Extraction
  → Vector Embedding

# Key Components
src/core/structured_processors/
├── excel_parser.py          # pandas + openpyxl
├── csv_parser.py            # pandas + encoding detection
├── schema_detector.py       # 컬럼 자동 인식
├── data_validator.py        # 품질 검증
└── column_mapper.py         # 필드 자동 매칭
```

**Implementation Steps**:
1. **Week 1**: Schema Detection
   - 컬럼명 패턴 인식 ("제품명", "Product Name", "품명" → PRODUCT_NAME)
   - Header row 자동 탐지
   - Multi-sheet 처리

2. **Week 2**: Data Validation
   - 필수 필드 검증 (제품명, 제품코드)
   - 데이터 타입 검증 (숫자, 문자, 날짜)
   - 중복 제거 및 병합

3. **Week 3**: Column Mapping
   - ML 기반 컬럼 매칭 (similarity)
   - Custom mapping rules
   - Confidence scoring

**Success Metrics**:
- ✅ 컬럼 자동 인식률 >90%
- ✅ 데이터 검증 정확도 >95%
- ✅ 처리 속도: 10,000 rows < 10초

### 4.4: Multi-Modal Integration ⭐

**Goal**: OCR + Text Embedding + Image Embedding 통합 시스템
**Related**: `docs/MULTIMODAL_RAG_STRATEGY.md` (Complete strategy document)

**Technical Design**:
```python
# Three-Modal Processing Pipeline
Input (PDF/Image/Excel/CSV)
  → Format Detector
  → Appropriate Processor (4.1/4.2/4.3)
  → Multi-Modal Embedding:
      ├── Text Embedding (384-dim, Sentence Transformers)
      ├── Image Embedding (1024-dim, OpenCLIP ViT-H-14)
      └── Shape Embedding (128-dim, Hu Moments + Fourier)
  → Qdrant Multi-Vector Storage (Named Vectors)
  → Hybrid Search Engine

# Key Components
src/core/multimodal/
├── format_detector.py           # 파일 포맷 자동 인식
├── multimodal_embedder.py      # 통합 임베딩 서비스 ⭐ NEW
├── ocr_to_embedding.py         # OCR → Embedding 파이프라인 ⭐ NEW
├── hybrid_search.py            # Text+Image+Shape 하이브리드 검색 ⭐ NEW
├── qdrant_uploader.py          # Multi-vector Qdrant 업로드 ⭐ NEW
└── reranker.py                 # Cross-encoder 재순위화 ⭐ NEW

src/core/shape_processors/      # Shape embedding pipeline ⭐ NEW
├── shape_embedder.py           # Hu Moments, Fourier, Zernike
└── background_remover.py       # U2-Net background removal
```

**Implementation Steps**:
1. **Week 1**: Unified Embedding Pipeline
   - `MultiModalEmbeddingService` 구현
   - Text + Image + Shape embedder 통합
   - Batch processing 지원
   - Unit tests for each modality

2. **Week 2**: Qdrant Multi-Vector Setup
   - `products_multimodal` collection 생성
   - Named vectors 설정 (text:384, image:1024, shape:128)
   - `MultiModalQdrantUploader` 구현
   - 기존 데이터 마이그레이션

3. **Week 3**: Hybrid Search Engine
   - `HybridSearchEngine` 구현
   - Fusion strategies (Weighted, RRF, Learned)
   - Cross-encoder re-ranking
   - Performance benchmarks

4. **Week 4**: OCR Integration
   - `OCRPipeline` → `MultiModalEmbedding` 연결
   - End-to-end: PDF → OCR → Embeddings → Qdrant
   - Caching layer 통합 (Phase 8.2)
   - Testing with 100+ documents

**Embedding Models**:
- **Text**: sentence-transformers/all-MiniLM-L6-v2 (384-dim) - Current
- **Image**: OpenCLIP ViT-H-14 (1024-dim) - Implemented
- **Shape**: Custom descriptors (128-dim) - New

**Success Metrics**:
- ✅ Text search accuracy: >85% @ Top-10
- ✅ Image search accuracy: >80% @ Top-10
- ✅ Hybrid search accuracy: >90% @ Top-10
- ✅ OCR → Embedding latency: <5s per page
- ✅ Search latency (cached): <50ms
- ✅ Search latency (uncached): <500ms

**Integration Points**:
- Phase 4.2 (OCR): Document → Text extraction
- Phase 4.3 (Excel): Structured data + embedded images
- Phase 6 (Image Matching): Shape-based similarity
- Phase 8.2 (Caching): Embedding cache layer

---

## Phase 5: Advanced RAG Integration Pipeline 🚀

**Priority**: HIGH
**Timeline**: 3-4 weeks
**Status**: Not Started

### Overview
여러 데이터 소스를 통합하여 하나의 통합 RAG 시스템을 구축. 현재 제품 데이터만 처리하는 시스템을 문서, 이미지, 구조화 데이터를 모두 포함하는 종합 검색 시스템으로 확장.

### 5.1: Unified Vector Store

**Goal**: Multi-Collection 통합 검색

**Technical Design**:
```python
# Architecture
Multiple Collections (Qdrant)
├── products_atomic        # 제품 정보
├── documents_semantic     # 문서 (PDF)
├── images_visual         # 이미지 (CLIP embeddings)
├── tables_structured     # 표 데이터
└── combined_hybrid       # 통합 임베딩

# Search Strategy
Query → Multiple Collections 병렬 검색
      → Score Normalization
      → Cross-Collection Re-ranking
      → Unified Results
```

**Implementation Steps**:
1. **Week 1**: Collection Architecture
   - Collection 설계 (각 데이터 타입별)
   - Index 최적화 (HNSW parameters)
   - Metadata schema 통일

2. **Week 2**: Parallel Search
   - AsyncIO 기반 병렬 검색
   - Timeout handling
   - Load balancing

3. **Week 3**: Score Normalization
   - Collection별 score 정규화
   - Weighted aggregation
   - Confidence scoring

**Success Metrics**:
- ✅ 검색 latency <200ms (parallel)
- ✅ Recall@10 >0.85
- ✅ Cross-collection relevance >0.80

### 5.2: Hybrid Retrieval

**Goal**: Dense + Sparse Retrieval 통합

**Technical Design**:
```python
# Architecture
Query
  ├── Dense Retrieval (Semantic)
  │   └── Sentence Transformers (현재)
  ├── Sparse Retrieval (Keyword)
  │   └── BM25 (Elasticsearch/Qdrant Sparse)
  └── Hybrid Scoring
      └── Reciprocal Rank Fusion (RRF)

# Components
src/core/retrieval/
├── dense_retriever.py       # 현재 시스템
├── sparse_retriever.py      # BM25 추가
├── hybrid_ranker.py         # RRF 구현
└── query_expander.py        # 쿼리 확장
```

**Implementation Steps**:
1. **Week 1**: Sparse Retrieval Setup
   - Qdrant Sparse Vectors 활용
   - BM25 인덱싱
   - Tokenization (한글 지원)

2. **Week 2**: Hybrid Scoring
   - RRF implementation
   - Weight tuning (dense:sparse = 0.7:0.3)
   - A/B testing

3. **Week 3**: Query Expansion
   - Synonym expansion (캡 ↔ 뚜껑 ↔ 마개)
   - Entity expansion (Ø20 → 20파이)
   - Context-aware expansion

**Success Metrics**:
- ✅ Recall improvement >10%
- ✅ Precision@10 >0.90
- ✅ Query expansion coverage >95%

### 5.3: Context-Aware Re-ranking

**Goal**: LLM 기반 정확도 향상

**Technical Design**:
```python
# Architecture
Initial Results (Top 50)
  → Cross-Encoder Re-ranking (Top 20)
  → LLM Re-ranking (Qwen2.5) (Top 10)
  → Final Results

# Components
src/core/reranking/
├── cross_encoder.py         # ms-marco-MiniLM
├── llm_reranker.py          # Qwen2.5 기반
├── context_analyzer.py      # 문맥 분석
└── relevance_scorer.py      # 최종 점수
```

**Implementation Steps**:
1. **Week 1**: Cross-Encoder Integration
   - ms-marco-MiniLM-L-6 모델
   - GPU 최적화
   - Batch processing

2. **Week 2**: LLM Re-ranking
   - Qwen2.5 prompt engineering
   - Relevance scoring (0-10)
   - Cache optimization

3. **Week 3**: Context Analysis
   - Intent classification (search/recommend/compare)
   - Entity matching score
   - Semantic similarity refinement

**Success Metrics**:
- ✅ NDCG@10 improvement >15%
- ✅ MRR (Mean Reciprocal Rank) >0.85
- ✅ Re-ranking latency <500ms

### 5.4: Incremental Learning

**Goal**: 실시간 데이터 업데이트 및 학습

**Technical Design**:
```python
# Architecture
New Data Input
  → Validation
  → Processing (Phase 4 pipeline)
  → Incremental Indexing (Qdrant)
  → Zero-Downtime Update

# Components
src/core/incremental/
├── data_validator.py        # 신규 데이터 검증
├── incremental_indexer.py   # 실시간 인덱싱
├── versioning.py            # 데이터 버저닝
└── rollback.py              # 롤백 지원
```

**Implementation Steps**:
1. **Week 1**: Validation Pipeline
   - Schema validation
   - Duplicate detection
   - Quality scoring

2. **Week 2**: Incremental Indexing
   - Qdrant upsert optimization
   - Batch vs streaming 전략
   - Lock-free updates

3. **Week 3**: Versioning & Rollback
   - Data versioning (Git-like)
   - Snapshot management
   - Rollback mechanism

**Success Metrics**:
- ✅ Update latency <5초 (1000 documents)
- ✅ Zero-downtime updates
- ✅ Rollback time <30초

---

## Phase 6: Image Matching Service 🎯

**Priority**: MEDIUM
**Timeline**: 4-5 weeks
**Status**: Not Started

### Overview
제품 이미지의 윤곽선 인식 및 유사 이미지 검색 서비스 구축. 사용자가 제품 이미지를 업로드하면 유사한 형태의 제품을 찾아주는 Visual Search 시스템.

### 6.1: Edge Detection & Contour Recognition

**Goal**: 제품 윤곽선 자동 추출

**Technical Design**:
```python
# Architecture
Product Image
  → Preprocessing (Background Removal)
  → Edge Detection (Canny/Sobel)
  → Contour Extraction (OpenCV)
  → Shape Descriptors (Hu Moments, Shape Context)
  → Vector Embedding (CLIP)

# Components
src/core/image_matching/
├── background_remover.py    # rembg/U2-Net
├── edge_detector.py         # Canny + Sobel
├── contour_extractor.py     # OpenCV contours
├── shape_descriptor.py      # Hu Moments, Fourier
└── visual_embedder.py       # CLIP/ResNet
```

**Implementation Steps**:
1. **Week 1**: Background Removal
   - rembg (U2-Net) 통합
   - Alpha matting
   - Quality validation

2. **Week 2**: Edge Detection
   - Canny edge detector (adaptive threshold)
   - Sobel operator (gradient 기반)
   - Edge linking & thinning

3. **Week 3**: Contour Extraction
   - OpenCV findContours
   - Contour hierarchy analysis
   - Polygon approximation

4. **Week 4**: Shape Descriptors
   - Hu Moments (scale/rotation invariant)
   - Shape Context descriptors
   - Fourier descriptors

**Success Metrics**:
- ✅ Background removal accuracy >90%
- ✅ Edge detection precision >85%
- ✅ Contour extraction completeness >95%

### 6.2: Visual Similarity Search

**Goal**: 이미지 기반 제품 검색

**Technical Design**:
```python
# Architecture
Query Image
  → Feature Extraction (CLIP/ResNet)
  → Vector Search (Qdrant)
  → Shape Matching (Contour similarity)
  → Hybrid Scoring (Visual + Shape)
  → Ranked Results

# Components
src/core/visual_search/
├── feature_extractor.py     # CLIP embeddings
├── shape_matcher.py         # Contour similarity
├── visual_searcher.py       # Qdrant search
└── hybrid_scorer.py         # Visual + Shape fusion
```

**Implementation Steps**:
1. **Week 1**: Feature Extraction
   - CLIP model (ViT-B/32)
   - ResNet50 fine-tuning
   - GPU optimization

2. **Week 2**: Shape Matching
   - Contour distance (Hausdorff)
   - Shape context matching
   - Procrustes analysis

3. **Week 3**: Hybrid Scoring
   - Visual similarity (CLIP) weight: 0.6
   - Shape similarity weight: 0.4
   - Normalization & fusion

**Success Metrics**:
- ✅ Top-10 accuracy >80%
- ✅ Search latency <1초
- ✅ Visual similarity >0.75

### 6.3: 3D Shape Recognition (Advanced)

**Goal**: 병/자 제품의 3D 형상 인식

**Technical Design**:
```python
# Architecture (Future)
Multiple Images (360° views)
  → 3D Reconstruction (NeRF/Photogrammetry)
  → 3D Shape Descriptors
  → 3D Similarity Search

# Components (Future Phase)
src/core/3d_matching/
├── reconstruction.py        # NeRF/MVS
├── mesh_analyzer.py         # 3D mesh 분석
├── shape_3d_descriptor.py   # 3D descriptors
└── 3d_searcher.py           # 3D similarity
```

**Implementation** (Phase 7):
- Week 1-2: NeRF setup
- Week 3-4: 3D descriptor extraction
- Week 5-6: 3D search pipeline

---

## Phase 7: Cloud Data Integration ☁️

**Priority**: MEDIUM
**Timeline**: 3-4 weeks
**Status**: Not Started

### Overview
클라우드 스토리지 (Google Drive, Dropbox, OneDrive, AWS S3)와의 통합으로 사용자가 클라우드에 업로드한 데이터를 자동으로 처리하는 시스템 구축.

### 7.1: Cloud Storage Connectors

**Goal**: 주요 클라우드 서비스 연동

**Technical Design**:
```python
# Architecture
Cloud Storage (Google Drive/S3/Dropbox)
  → OAuth2 Authentication
  → File Monitoring (Webhooks/Polling)
  → Download & Process
  → Upload Results

# Components
src/integrations/cloud/
├── google_drive.py          # Google Drive API
├── aws_s3.py                # boto3
├── dropbox.py               # Dropbox API
├── onedrive.py              # Microsoft Graph API
└── cloud_manager.py         # Unified interface
```

**Implementation Steps**:
1. **Week 1**: Google Drive Integration
   - OAuth2 setup
   - File list/download API
   - Webhook notifications
   - Folder watching

2. **Week 2**: AWS S3 Integration
   - boto3 setup
   - S3 event notifications
   - IAM permissions
   - Bucket policies

3. **Week 3**: Dropbox & OneDrive
   - API integration
   - Webhook setup
   - Rate limiting handling

**Success Metrics**:
- ✅ Authentication success rate 100%
- ✅ File detection latency <30초
- ✅ Download speed >10MB/s

### 7.2: Automated Data Pipeline

**Goal**: 클라우드 → 처리 → 업데이트 자동화

**Technical Design**:
```python
# Architecture
Cloud Upload Event
  → Event Queue (Redis/RabbitMQ)
  → Worker Pool (Celery)
  → Phase 4 Processing
  → Phase 5 Indexing
  → Notification (완료 알림)

# Components
src/integrations/pipeline/
├── event_listener.py        # Webhook handler
├── task_queue.py            # Celery tasks
├── worker_manager.py        # Worker pool
├── progress_tracker.py      # 진행 상황 추적
└── notifier.py              # 사용자 알림
```

**Implementation Steps**:
1. **Week 1**: Event Queue Setup
   - Redis/RabbitMQ 설정
   - Event schema 정의
   - Priority queue

2. **Week 2**: Worker Pool
   - Celery configuration
   - Task routing
   - Auto-scaling

3. **Week 3**: Progress Tracking
   - Real-time progress updates
   - WebSocket notifications
   - Error handling & retry

**Success Metrics**:
- ✅ Processing latency <5분 (100 files)
- ✅ Worker utilization >80%
- ✅ Error recovery rate >95%

### 7.3: Collaborative Features

**Goal**: 팀 협업 기능 추가

**Technical Design**:
```python
# Architecture
Team Workspace
  ├── Shared Collections
  ├── Access Control (RBAC)
  ├── Version History
  └── Activity Logs

# Components
src/collaboration/
├── workspace_manager.py     # 워크스페이스 관리
├── access_control.py        # RBAC
├── version_manager.py       # 버전 관리
└── activity_logger.py       # 활동 로그
```

**Implementation Steps**:
1. **Week 1**: Workspace Management
   - Multi-tenant architecture
   - Workspace isolation
   - Resource quotas

2. **Week 2**: Access Control
   - Role-based access (Admin/Editor/Viewer)
   - Permission management
   - Invitation system

3. **Week 3**: Version & Activity
   - Document versioning
   - Activity logs
   - Audit trail

**Success Metrics**:
- ✅ Workspace isolation 100%
- ✅ Permission check latency <50ms
- ✅ Version recovery time <5초

---

## Phase 8: Real-Time Chat Optimization ⚡

**Priority**: HIGH
**Timeline**: 3-4 weeks
**Status**: Not Started

### Overview
현재 채팅 응답 속도를 대폭 개선하여 사용자 경험을 향상. 목표: **First Response <500ms, Full Answer <2초**

### 8.1: Response Time Analysis

**Current Bottlenecks**:
```
Total Response Time: ~3-5초

Breakdown:
1. Query Parsing: ~100ms
2. Vector Search: ~200-300ms
3. Re-ranking: ~500-800ms (병목!)
4. LLM Generation: ~1500-2000ms (최대 병목!)
5. Response Formatting: ~50ms
```

**Target**:
```
Optimized Response Time: <2초

Breakdown:
1. Query Parsing: ~50ms (캐싱)
2. Vector Search: ~100ms (인덱스 최적화)
3. Re-ranking: ~200ms (모델 경량화)
4. LLM Generation: ~800ms (스트리밍)
5. Response Formatting: ~50ms
```

### 8.2: Caching Strategy

**Goal**: 반복 쿼리 즉시 응답

**Technical Design**:
```python
# Architecture
Query → Cache Check (Redis)
  ├── Cache Hit → Instant Response (<50ms)
  └── Cache Miss → Full Pipeline → Cache Result

# Cache Layers
1. Exact Match Cache (TTL: 1시간)
2. Semantic Cache (유사 쿼리, TTL: 30분)
3. Entity Cache (파싱 결과, TTL: 24시간)
4. Search Result Cache (벡터 검색, TTL: 10분)

# Components
src/optimization/caching/
├── query_cache.py           # Redis 통합
├── semantic_cache.py        # 유사 쿼리 매칭
├── result_cache.py          # 검색 결과 캐싱
└── cache_warmer.py          # 사전 캐싱
```

**Implementation Steps**:
1. **Week 1**: Redis Cache Setup
   - Exact match caching
   - TTL strategies
   - Cache invalidation

2. **Week 2**: Semantic Caching
   - Query embedding similarity
   - Threshold tuning (>0.95)
   - Cache hit rate monitoring

3. **Week 3**: Cache Warming
   - Popular query pre-caching
   - Background cache refresh
   - Peak time optimization

**Success Metrics**:
- ✅ Cache hit rate >60%
- ✅ Cached response time <50ms
- ✅ Memory usage <2GB

### 8.3: Async & Streaming

**Goal**: 점진적 응답으로 UX 개선

**Technical Design**:
```python
# Architecture
Query → Immediate Ack (100ms)
      → Search Results Stream (300ms)
      → Answer Stream (800ms)
      → Complete (2초)

# Streaming Response
1. [100ms] "검색 중..." (Status update)
2. [400ms] Top 3 Products (Preview)
3. [1200ms] Detailed Answer (Streaming)
4. [2000ms] Complete Response

# Components
src/optimization/streaming/
├── async_pipeline.py        # AsyncIO
├── stream_handler.py        # SSE/WebSocket
├── partial_results.py       # 중간 결과 생성
└── progress_reporter.py     # 진행 상황 보고
```

**Implementation Steps**:
1. **Week 1**: Async Pipeline
   - AsyncIO refactoring
   - Parallel search execution
   - Non-blocking I/O

2. **Week 2**: Streaming Response
   - SSE (Server-Sent Events) 구현
   - WebSocket fallback
   - Chunk-based streaming

3. **Week 3**: Progressive Enhancement
   - Immediate product previews
   - Incremental answer generation
   - User feedback integration

**Success Metrics**:
- ✅ First response <500ms
- ✅ Streaming latency <100ms per chunk
- ✅ User perceived speed improvement >50%

### 8.4: Model Optimization

**Goal**: LLM 응답 속도 향상

**Technical Design**:
```python
# Strategies
1. Model Quantization (INT8/INT4)
2. Prompt Optimization (토큰 수 감소)
3. GPU Optimization (vLLM)
4. Response Caching

# Components
src/optimization/models/
├── quantized_models.py      # INT8/INT4 quantization
├── prompt_optimizer.py      # 토큰 수 최소화
├── vllm_integration.py      # vLLM 통합
└── batch_inference.py       # 배치 처리
```

**Implementation Steps**:
1. **Week 1**: Model Quantization
   - Qwen2.5-7B → INT8 (50% 속도 향상)
   - 품질 검증 (perplexity <10% 증가)
   - GPU 메모리 최적화

2. **Week 2**: Prompt Engineering
   - 토큰 수 최소화 (현재 ~500 → 목표 ~300)
   - Few-shot → Zero-shot
   - Template optimization

3. **Week 3**: vLLM Integration
   - Continuous batching
   - PagedAttention
   - Dynamic batching

**Success Metrics**:
- ✅ LLM response time: 2000ms → 800ms
- ✅ Throughput: 10 req/s → 50 req/s
- ✅ GPU memory: 16GB → 8GB

### 8.5: Load Balancing & Scaling

**Goal**: 동시 사용자 처리 능력 향상

**Technical Design**:
```python
# Architecture
Load Balancer (Nginx)
  ├── API Server 1 (FastAPI)
  ├── API Server 2 (FastAPI)
  └── API Server 3 (FastAPI)

Backend Services
  ├── Qdrant Cluster (Sharding)
  ├── PostgreSQL (Read Replicas)
  └── Redis Cluster (Caching)

# Components
infrastructure/
├── docker-compose.scale.yml  # 스케일링 설정
├── nginx.conf                # 로드 밸런서
├── qdrant-cluster.yml        # Qdrant 클러스터
└── monitoring.yml            # Prometheus + Grafana
```

**Implementation Steps**:
1. **Week 1**: Horizontal Scaling
   - Docker Compose scale up
   - Nginx load balancing
   - Health checks

2. **Week 2**: Database Optimization
   - PostgreSQL read replicas
   - Connection pooling (PgBouncer)
   - Query optimization

3. **Week 3**: Monitoring & Auto-scaling
   - Prometheus metrics
   - Grafana dashboards
   - Auto-scaling rules (CPU >70%)

**Success Metrics**:
- ✅ Concurrent users: 10 → 1000
- ✅ Response time at peak <3초
- ✅ Error rate <0.1%

---

## Phase 9: Enterprise Deployment 🏢

**Priority**: LOW (Future)
**Timeline**: 6-8 weeks
**Status**: Not Started

### Overview
Production-grade 배포 및 운영 인프라 구축. CI/CD, 모니터링, 로깅, 보안, 백업 등 엔터프라이즈급 시스템 운영에 필요한 모든 요소.

### 9.1: CI/CD Pipeline

**Goal**: 자동화된 배포 파이프라인

**Technical Design**:
```yaml
# GitHub Actions Workflow
name: Production Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    - Run unit tests
    - Run integration tests
    - Code coverage check

  build:
    - Build Docker images
    - Push to registry
    - Tag versions

  deploy:
    - Rolling update (zero-downtime)
    - Health checks
    - Rollback on failure
```

**Components**:
- GitHub Actions workflows
- Docker Registry (AWS ECR)
- Kubernetes manifests
- Helm charts

### 9.2: Monitoring & Observability

**Goal**: 시스템 건강도 실시간 모니터링

**Stack**:
- Prometheus (메트릭 수집)
- Grafana (시각화)
- Loki (로그 수집)
- Jaeger (분산 추적)

**Key Metrics**:
- Response time (p50, p95, p99)
- Error rate
- Request throughput
- GPU/CPU utilization
- Memory usage
- Cache hit rate

### 9.3: Security & Compliance

**Goal**: 엔터프라이즈급 보안

**Features**:
- Authentication (OAuth2/OIDC)
- Authorization (RBAC)
- API Rate Limiting
- Data Encryption (at rest & in transit)
- Audit Logging
- GDPR Compliance

### 9.4: Disaster Recovery

**Goal**: 데이터 보호 및 복구

**Features**:
- Automated backups (daily/weekly)
- Point-in-time recovery
- Multi-region replication
- Failover automation
- RTO <1시간, RPO <15분

---

## Implementation Priority Matrix

### Critical Path (Must Have)

| Phase | Priority | Impact | Effort | Timeline |
|-------|----------|--------|--------|----------|
| 4.1 PDF Processing | ⭐⭐⭐⭐⭐ | HIGH | MEDIUM | 4 weeks |
| 4.3 Excel/CSV | ⭐⭐⭐⭐⭐ | HIGH | LOW | 3 weeks |
| 8.2 Caching | ⭐⭐⭐⭐⭐ | HIGH | LOW | 3 weeks |
| 8.3 Streaming | ⭐⭐⭐⭐⭐ | HIGH | MEDIUM | 3 weeks |
| 5.2 Hybrid Retrieval | ⭐⭐⭐⭐ | MEDIUM | MEDIUM | 3 weeks |

### High Value (Should Have)

| Phase | Priority | Impact | Effort | Timeline |
|-------|----------|--------|--------|----------|
| 4.2 Image OCR | ⭐⭐⭐⭐ | HIGH | HIGH | 4 weeks |
| 5.1 Unified Vector Store | ⭐⭐⭐⭐ | MEDIUM | MEDIUM | 3 weeks |
| 6.1 Edge Detection | ⭐⭐⭐⭐ | MEDIUM | HIGH | 4 weeks |
| 7.1 Cloud Storage | ⭐⭐⭐⭐ | MEDIUM | MEDIUM | 3 weeks |
| 8.4 Model Optimization | ⭐⭐⭐⭐ | HIGH | HIGH | 3 weeks |

### Nice to Have (Could Have)

| Phase | Priority | Impact | Effort | Timeline |
|-------|----------|--------|--------|----------|
| 5.3 LLM Re-ranking | ⭐⭐⭐ | LOW | MEDIUM | 3 weeks |
| 6.2 Visual Search | ⭐⭐⭐ | MEDIUM | HIGH | 3 weeks |
| 7.2 Automated Pipeline | ⭐⭐⭐ | MEDIUM | MEDIUM | 3 weeks |
| 7.3 Collaboration | ⭐⭐⭐ | LOW | HIGH | 3 weeks |
| 9.1 CI/CD | ⭐⭐⭐ | LOW | MEDIUM | 4 weeks |

### Future (Won't Have Now)

| Phase | Priority | Impact | Effort | Timeline |
|-------|----------|--------|--------|----------|
| 6.3 3D Recognition | ⭐⭐ | LOW | VERY HIGH | 6 weeks |
| 9.2 Monitoring | ⭐⭐ | LOW | MEDIUM | 4 weeks |
| 9.3 Security | ⭐⭐ | LOW | HIGH | 6 weeks |
| 9.4 Disaster Recovery | ⭐⭐ | LOW | HIGH | 6 weeks |

---

## Recommended Execution Plan

### Q1 2025 (Jan-Mar): Multi-Modal Foundation

**Focus**: Data Processing Pipeline

**Phases**: 4.1, 4.3, 4.4
- ✅ Week 1-4: PDF Processing
- ✅ Week 5-7: Excel/CSV Processing
- ✅ Week 8-10: Multi-Modal Integration
- ✅ Week 11-12: Testing & Validation

**Deliverables**:
- PDF → RAG pipeline
- Excel/CSV → RAG pipeline
- Unified data processing API

### Q2 2025 (Apr-Jun): Search Optimization

**Focus**: Speed & Accuracy

**Phases**: 8.2, 8.3, 8.4, 5.2
- ✅ Week 1-3: Caching Strategy
- ✅ Week 4-6: Async & Streaming
- ✅ Week 7-9: Model Optimization
- ✅ Week 10-12: Hybrid Retrieval

**Deliverables**:
- Response time <2초
- Cache hit rate >60%
- Hybrid search accuracy +10%

### Q3 2025 (Jul-Sep): Visual Intelligence

**Focus**: Image Processing

**Phases**: 4.2, 6.1, 6.2
- ✅ Week 1-4: Image OCR
- ✅ Week 5-8: Edge Detection & Contours
- ✅ Week 9-12: Visual Similarity Search

**Deliverables**:
- Image → Product matching
- Visual search API
- 80% accuracy in shape matching

### Q4 2025 (Oct-Dec): Cloud Integration

**Focus**: Scalability & Integration

**Phases**: 7.1, 7.2, 5.1
- ✅ Week 1-3: Cloud Storage Integration
- ✅ Week 4-6: Automated Data Pipeline
- ✅ Week 7-9: Unified Vector Store
- ✅ Week 10-12: Load Testing & Optimization

**Deliverables**:
- Google Drive / S3 integration
- Automated data sync
- 1000+ concurrent users support

---

## Success Metrics by Phase

### Phase 4: Multi-Modal Processing
- ✅ PDF processing success rate >95%
- ✅ Image OCR accuracy >85%
- ✅ Excel parsing accuracy >90%
- ✅ End-to-end processing time <5분 (100 documents)

### Phase 5: RAG Integration
- ✅ Recall@10 >0.85
- ✅ Precision@10 >0.90
- ✅ Cross-collection search <200ms
- ✅ Hybrid retrieval improvement >10%

### Phase 6: Image Matching
- ✅ Edge detection accuracy >85%
- ✅ Shape matching accuracy >80%
- ✅ Visual search latency <1초
- ✅ Top-10 accuracy >75%

### Phase 7: Cloud Integration
- ✅ Cloud sync latency <30초
- ✅ Processing throughput >1000 files/hour
- ✅ Error recovery rate >95%
- ✅ Storage utilization >80%

### Phase 8: Chat Optimization
- ✅ Response time <2초 (p95)
- ✅ First response <500ms
- ✅ Cache hit rate >60%
- ✅ Concurrent users >1000

### Phase 9: Enterprise
- ✅ Uptime >99.9%
- ✅ RTO <1시간
- ✅ RPO <15분
- ✅ Security audit compliance 100%

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OCR 정확도 낮음 | HIGH | MEDIUM | Multi-engine fallback (Tesseract + EasyOCR) |
| LLM latency 높음 | HIGH | HIGH | Quantization + caching + streaming |
| Cloud API rate limits | MEDIUM | MEDIUM | Request throttling + retry logic |
| Image processing 느림 | MEDIUM | MEDIUM | GPU acceleration + batch processing |
| Vector DB 확장성 | HIGH | LOW | Qdrant clustering + sharding |

### Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| 높은 클라우드 비용 | HIGH | MEDIUM | Cost optimization + usage monitoring |
| 데이터 품질 문제 | HIGH | HIGH | Validation pipeline + quality checks |
| 사용자 채택률 낮음 | HIGH | LOW | UX improvement + user training |
| 경쟁사 유사 제품 | MEDIUM | MEDIUM | Unique features + IP protection |

---

## Resource Requirements

### Development Team

**Phase 4-5 (Q1-Q2)**:
- 2x Backend Engineers (Python/FastAPI)
- 1x ML Engineer (NLP/CV)
- 1x DevOps Engineer
- 1x QA Engineer

**Phase 6-7 (Q3-Q4)**:
- 3x Backend Engineers
- 2x ML Engineers (Computer Vision)
- 1x Full-stack Engineer
- 1x DevOps Engineer

**Phase 8-9 (2026)**:
- 4x Backend Engineers
- 2x ML Engineers
- 2x Full-stack Engineers
- 2x DevOps Engineers
- 1x Security Engineer

### Infrastructure Budget (Monthly)

**Current** (Production-Ready):
- AWS/GCP: $500 (Compute, Storage)
- Qdrant Cloud: $200
- Total: **$700/month**

**Phase 4-6** (Multi-Modal + Image):
- AWS/GCP: $2,000 (GPU instances)
- Qdrant Cloud: $500
- OpenAI API: $300 (backup LLM)
- Total: **$2,800/month**

**Phase 7-8** (Cloud + Optimization):
- AWS/GCP: $5,000 (Load balancing, CDN)
- Qdrant Cluster: $1,000
- Redis Cluster: $500
- Monitoring: $200
- Total: **$6,700/month**

**Phase 9** (Enterprise):
- AWS/GCP: $15,000 (Multi-region, HA)
- Qdrant Enterprise: $3,000
- Databases: $2,000
- Monitoring & Logs: $1,000
- Security & Compliance: $1,000
- Total: **$22,000/month**

---

## Technology Stack Evolution

### Current Stack (Phase 0-3)
```
Backend: FastAPI, Python 3.11
Vector DB: Qdrant
Database: PostgreSQL + pgvector
Cache: Redis
LLM: Qwen2.5-7B (Ollama)
Embeddings: sentence-transformers/all-MiniLM-L6-v2
```

### Phase 4-6 (Multi-Modal + Image)
```
+ PyPDF2, PDFPlumber (PDF parsing)
+ Tesseract, EasyOCR (OCR)
+ OpenCV (Image processing)
+ rembg, U2-Net (Background removal)
+ CLIP, ResNet (Visual embeddings)
+ pandas, openpyxl (Excel/CSV)
```

### Phase 7-8 (Cloud + Optimization)
```
+ boto3 (AWS S3)
+ google-cloud-storage (Google Drive)
+ Celery, RabbitMQ (Task queue)
+ vLLM (LLM optimization)
+ AsyncIO (Async processing)
+ SSE, WebSocket (Streaming)
```

### Phase 9 (Enterprise)
```
+ Kubernetes (Orchestration)
+ Helm (Package management)
+ Prometheus, Grafana (Monitoring)
+ Loki, Jaeger (Logging, Tracing)
+ OAuth2, OIDC (Authentication)
+ HashiCorp Vault (Secrets)
```

---

## Conclusion

이 로드맵은 RAG Enterprise를 **Enterprise-Grade Multi-Modal RAG Platform**으로 발전시키기 위한 체계적인 계획을 제시합니다.

### Key Takeaways

1. **Foundation is Solid** ✅
   - Phase 0-3 완료: 3,246 chunks, 0.79-0.82 search quality
   - Production-ready 상태

2. **Clear Path Forward** 🎯
   - Phase 4-6: Multi-Modal & Image (6-9개월)
   - Phase 7-8: Cloud & Speed (6개월)
   - Phase 9: Enterprise (6개월)

3. **Balanced Approach** ⚖️
   - High-value features first (PDF, Excel, Caching)
   - Advanced features later (3D, Enterprise)
   - ROI-driven prioritization

4. **Scalable Architecture** 📈
   - Modular design (Phase별 독립적)
   - Incremental deployment
   - Risk mitigation strategies

### Next Immediate Steps

1. **Week 1-2**: Phase 4.1 시작 (PDF Processing)
2. **Week 3-4**: Phase 8.2 시작 (Caching Strategy)
3. **Week 5-6**: Phase 4.3 시작 (Excel/CSV Processing)

**Target**: Q1 2025 완료 시 **Multi-Modal RAG System** 구축 ✅

---

**Document Version**: 1.0
**Last Updated**: 2025-11-06
**Next Review**: 2025-12-01
**Owner**: RAG Enterprise Team
