# Unified Crawl-to-RAG Pipeline Architecture

**Date**: 2025-11-04
**Goal**: End-to-end automation from web crawling to RAG-ready embeddings
**Status**: 🔄 Design Phase

---

## 🎯 Vision

Create a **fully automated pipeline** that transforms raw web data into production-ready RAG system:

```
Web Crawling → Data Preprocessing → Quality Validation → Embedding → Qdrant Storage → RAG Query
     ↓              ↓                    ↓                ↓             ↓             ↓
web-crawler    rag-pipeline        rag-pipeline    rag-pipeline   rag-pipeline   rag-pipeline
  skill       (preprocess)         (validate)       (embed)        (store)       (query)
```

---

## 🏗️ Current Architecture (Manual)

### Current Workflow:
```
1. Manual: Run web crawler
   └─> scripts/crawl_onehago_complete.py
   └─> Output: data/crawled/onehago/.../*.jsonl

2. Manual: Data inspection
   └─> Check data quality
   └─> Fix issues manually

3. Manual: Preprocessing
   └─> Parse specifications
   └─> Link images
   └─> Clean data

4. Manual: Embedding
   └─> scripts/embed_onehago_packaging.py
   └─> Output: Qdrant "onehago" collection

5. Manual: Testing
   └─> Test search quality
   └─> Iterate if needed
```

**Problems**:
- ❌ 5 manual steps
- ❌ No consistency checks
- ❌ Hard to reproduce
- ❌ Time consuming
- ❌ Error prone

---

## 🎨 Proposed Architecture (Automated)

### Unified Pipeline:
```
┌─────────────────────────────────────────────────────────────┐
│                  UNIFIED SKILL ORCHESTRATOR                 │
│            (.claude/skills/data-pipeline/)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        │                                       │
        ↓                                       ↓
┌──────────────────┐                   ┌──────────────────┐
│ web-crawler      │                   │ rag-pipeline     │
│ -pipeline        │ ─────────────────>│                  │
│                  │   raw JSONL        │                  │
│ Functions:       │                   │ Functions:       │
│ - crawl()        │                   │ - preprocess()   │
│ - monitor()      │                   │ - validate()     │
│ - checkpoint()   │                   │ - embed()        │
│                  │                   │ - store()        │
└──────────────────┘                   │ - query()        │
                                       └──────────────────┘
```

### Skill Integration Points:

**web-crawler-pipeline → rag-pipeline**:
```python
# web-crawler-pipeline/scripts/skill.py

def crawl_and_prepare(params):
    """Crawl website and prepare for RAG"""

    # 1. Crawl data
    crawl_result = execute('crawl', {
        'site': params['site'],
        'output_dir': params['output_dir']
    })

    # 2. Call rag-pipeline for preprocessing
    from rag_pipeline.skill import execute as rag_execute

    preprocess_result = rag_execute('preprocess', {
        'input_file': crawl_result['output_file'],
        'data_type': params['site'],  # onehago, chungjinkorea, etc.
        'preprocessing_config': params.get('preprocessing_config')
    })

    # 3. Validate quality
    validation_result = rag_execute('validate', {
        'input_file': preprocess_result['output_file']
    })

    # 4. Embed if validation passes
    if validation_result['quality_score'] >= 0.8:
        embed_result = rag_execute('embed', {
            'input_file': preprocess_result['output_file'],
            'collection_name': params['collection_name']
        })

        return {
            'status': 'success',
            'crawled': crawl_result['total_items'],
            'preprocessed': preprocess_result['total_items'],
            'embedded': embed_result['total_vectors'],
            'collection': params['collection_name']
        }
    else:
        return {
            'status': 'quality_check_failed',
            'quality_score': validation_result['quality_score'],
            'issues': validation_result['issues']
        }
```

---

## 📦 rag-pipeline Skill Enhancement

### New Commands to Add:

**1. preprocess** - Data preprocessing
```python
def preprocess(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess crawled data for RAG

    Args:
        input_file: Path to raw JSONL file
        data_type: Type of data (onehago, chungjinkorea, etc.)
        preprocessing_config: Optional config overrides

    Returns:
        {
            'status': 'success',
            'input_file': '...',
            'output_file': '...',
            'total_items': 22871,
            'preprocessing_steps': [
                'link_images',
                'parse_specifications',
                'clean_materials',
                'extract_capacity'
            ]
        }
    """

    input_file = Path(params['input_file'])
    data_type = params['data_type']

    # Load preprocessing strategy
    preprocessor = get_preprocessor(data_type)

    # Apply preprocessing pipeline
    processed_data = preprocessor.process(input_file)

    # Save enhanced data
    output_file = input_file.parent / f"{input_file.stem}_enhanced.jsonl"
    processed_data.save(output_file)

    return {
        'status': 'success',
        'input_file': str(input_file),
        'output_file': str(output_file),
        'total_items': len(processed_data),
        'preprocessing_steps': preprocessor.steps_applied
    }
```

**2. validate** - Quality validation
```python
def validate(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate data quality before embedding

    Checks:
    - Required fields present
    - Data types correct
    - Image paths valid
    - Specifications parsed
    - No duplicate IDs

    Returns:
        {
            'status': 'success',
            'quality_score': 0.95,
            'total_items': 22871,
            'passed': 22457,
            'failed': 414,
            'issues': {
                'missing_images': 414,
                'invalid_capacity': 0,
                'missing_product_name': 0
            }
        }
    """

    input_file = Path(params['input_file'])

    validator = DataValidator()
    results = validator.validate(input_file)

    return {
        'status': 'success',
        'quality_score': results.score,
        'total_items': results.total,
        'passed': results.passed,
        'failed': results.failed,
        'issues': results.issues
    }
```

**3. embed** - Embedding with preprocessing
```python
def embed(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Embed preprocessed data to Qdrant

    Args:
        input_file: Path to enhanced JSONL
        collection_name: Qdrant collection name
        batch_size: Batch size for embedding
        overwrite: Whether to overwrite existing collection

    Returns:
        {
            'status': 'success',
            'collection_name': 'onehago',
            'total_vectors': 22871,
            'embedding_time_sec': 203.5,
            'vectors_per_sec': 112.7
        }
    """

    input_file = Path(params['input_file'])
    collection_name = params['collection_name']

    # Create embedder
    embedder = SmartEmbedder(
        model='all-MiniLM-L6-v2',
        qdrant_url='http://localhost:6333'
    )

    # Embed with progress tracking
    result = embedder.embed_file(
        input_file=input_file,
        collection_name=collection_name,
        batch_size=params.get('batch_size', 100),
        overwrite=params.get('overwrite', False)
    )

    return result
```

---

## 🔄 Preprocessing Strategies

### Strategy Pattern:
```python
# .claude/skills/rag-pipeline/scripts/preprocessors/base.py

class BasePreprocessor:
    """Base class for data preprocessing"""

    def process(self, input_file: Path) -> ProcessedData:
        """Process raw data"""
        raise NotImplementedError

    def link_images(self, data):
        """Link local images to metadata"""
        pass

    def parse_specifications(self, data):
        """Parse specifications"""
        pass

    def clean_materials(self, data):
        """Clean material strings"""
        pass

    def extract_capacity(self, data):
        """Extract capacity from product name"""
        pass


# .claude/skills/rag-pipeline/scripts/preprocessors/onehago.py

class OnehagoPreprocessor(BasePreprocessor):
    """Onehago-specific preprocessing"""

    def process(self, input_file: Path) -> ProcessedData:
        # Load data
        products = self.load_jsonl(input_file)

        # Apply preprocessing steps
        products = self.link_images(products)
        products = self.parse_specifications(products)
        products = self.clean_materials(products)
        products = self.extract_capacity(products)

        return ProcessedData(products, steps_applied=[
            'link_images',
            'parse_specifications',
            'clean_materials',
            'extract_capacity'
        ])

    def link_images(self, products):
        """Link images from images/packaging/ folder"""
        images_root = Path('data/crawled/onehago/images/packaging')

        for product in products:
            product_id = product['product_id']
            image_folder = images_root / product_id

            if image_folder.exists():
                images = list(image_folder.glob('img_*.jpg'))
                product['local_images'] = [
                    {
                        'index': i + 1,
                        'filename': img.name,
                        'local_path': str(img),
                        'relative_path': f'images/packaging/{product_id}/{img.name}'
                    }
                    for i, img in enumerate(sorted(images))
                ]
                product['has_local_images'] = True
            else:
                product['has_local_images'] = False
                product['local_images'] = []

        return products

    def parse_specifications(self, products):
        """Parse specifications from raw fields"""
        for product in products:
            specs = product.get('specifications', {})

            # Extract capacity from product name
            capacity_match = re.search(r'(\d+)(ml|g|cc)', product['product_name'])
            capacity = capacity_match.group(0) if capacity_match else None

            # Extract neck_size from "용량" field
            capacity_field = specs.get('용량', '')
            neck_size = None
            if 'Neck' in capacity_field or 'neck' in capacity_field:
                neck_match = re.search(r'[Nn]eck\s*[×x]\s*(\d+)', capacity_field)
                if neck_match:
                    neck_size_num = int(neck_match.group(1))
                    neck_size = f"{neck_size_num}파이"

            # Parse materials
            material_str = specs.get('재질', '')
            materials = []
            for mat in material_str.split(','):
                mat = mat.strip()
                if mat and mat != '':
                    mat_map = {'OTHER': '기타', 'PP': 'PP', 'PET': 'PET', 'ABS': 'ABS'}
                    materials.append(mat_map.get(mat, mat))

            # Store parsed specs
            product['specifications_parsed'] = {
                'capacity': capacity,
                'neck_size': neck_size,
                'materials': materials,
                'moq': int(specs.get('MOQ', '0').replace(',', '')) if specs.get('MOQ') else None,
                'product_code': specs.get('코드', ''),
                'origin': specs.get('원산지', '')
            }

        return products


# .claude/skills/rag-pipeline/scripts/preprocessors/chungjinkorea.py

class ChungjinkoreaPreprocessor(BasePreprocessor):
    """Chungjinkorea-specific preprocessing"""

    def process(self, input_file: Path) -> ProcessedData:
        # Chungjinkorea data is already well-structured
        # Just validate and normalize

        products = self.load_json_files(input_file)
        products = self.normalize_fields(products)

        return ProcessedData(products, steps_applied=[
            'normalize_fields'
        ])
```

---

## 📋 Configuration System

### Preprocessing Configs:
```yaml
# config/preprocessing/onehago.yaml

name: "onehago"
description: "원하고 포장 용기 데이터 전처리"

steps:
  - name: "link_images"
    enabled: true
    config:
      images_root: "data/crawled/onehago/images/packaging"
      max_images_per_product: 3

  - name: "parse_specifications"
    enabled: true
    config:
      extract_capacity_from: "product_name"
      extract_neck_size_from: "specifications.용량"
      parse_materials_from: "specifications.재질"

  - name: "clean_materials"
    enabled: true
    config:
      material_mapping:
        "OTHER": "기타"
        "PP": "PP"
        "PET": "PET"
        "PETG": "PETG"

  - name: "extract_capacity"
    enabled: true
    config:
      patterns:
        - "\\d+ml"
        - "\\d+g"
        - "\\d+cc"

validation:
  required_fields:
    - "product_id"
    - "product_name"
    - "product_url"

  optional_fields:
    - "local_images"
    - "specifications_parsed"

  quality_thresholds:
    min_image_coverage: 0.90  # 90% of products should have images
    min_spec_coverage: 0.80   # 80% should have parsed specs
```

---

## 🚀 Implementation Plan

### Phase 1: rag-pipeline Enhancement (Week 1)

**Day 1-2**: Core preprocessing framework
- ✅ Create BasePreprocessor class
- ✅ Implement OnehagoPreprocessor
- ✅ Implement ChungjinkoreaPreprocessor
- ✅ Add preprocess() command to skill

**Day 3**: Validation framework
- ✅ Create DataValidator class
- ✅ Implement quality checks
- ✅ Add validate() command to skill

**Day 4**: Enhanced embedding
- ✅ Update embed() command
- ✅ Add batch processing
- ✅ Progress tracking

**Day 5**: Testing
- ✅ Unit tests for preprocessors
- ✅ Integration tests
- ✅ End-to-end test with onehago data

---

### Phase 2: web-crawler Integration (Week 2)

**Day 1-2**: Integration interface
- ✅ Add rag-pipeline dependency to web-crawler
- ✅ Implement crawl_and_prepare() function
- ✅ Add pipeline orchestration

**Day 3**: Configuration
- ✅ Create preprocessing configs
- ✅ Add site-specific configs
- ✅ Validation rules

**Day 4**: Checkpointing
- ✅ Save pipeline state
- ✅ Resume from checkpoint
- ✅ Rollback support

**Day 5**: Testing
- ✅ Full pipeline test
- ✅ Error handling
- ✅ Performance optimization

---

### Phase 3: Production Features (Week 3)

**Day 1-2**: Monitoring
- ✅ Pipeline metrics
- ✅ Quality dashboards
- ✅ Alerts for issues

**Day 3**: Documentation
- ✅ Usage guides
- ✅ API documentation
- ✅ Examples

**Day 4-5**: Optimization
- ✅ Parallel processing
- ✅ Caching
- ✅ Performance tuning

---

## 📊 Usage Examples

### Example 1: Crawl + Preprocess + Embed

```bash
# Using unified skill orchestrator
python3 .claude/skills/web-crawler-pipeline/scripts/skill.py

# Command: crawl_and_embed
{
  "command": "crawl_and_embed",
  "params": {
    "site": "onehago",
    "output_dir": "data/crawled/onehago",
    "collection_name": "onehago",
    "preprocessing_config": "config/preprocessing/onehago.yaml"
  }
}

# Output:
{
  "status": "success",
  "crawled": 22871,
  "preprocessed": 22871,
  "embedded": 22870,
  "quality_score": 0.98,
  "collection": "onehago",
  "pipeline_time_sec": 456.2
}
```

### Example 2: Preprocess Existing Data

```bash
# Using rag-pipeline directly
python3 .claude/skills/rag-pipeline/scripts/skill.py

# Command: preprocess
{
  "command": "preprocess",
  "params": {
    "input_file": "data/crawled/onehago/packaging_unique_for_images.jsonl",
    "data_type": "onehago",
    "output_file": "data/crawled/onehago/packaging_enhanced.jsonl"
  }
}

# Output:
{
  "status": "success",
  "input_file": "...",
  "output_file": "...",
  "total_items": 22871,
  "preprocessing_steps": [
    "link_images",
    "parse_specifications",
    "clean_materials",
    "extract_capacity"
  ],
  "stats": {
    "images_linked": 22457,
    "specs_parsed": 21890,
    "materials_cleaned": 22100,
    "capacity_extracted": 19500
  }
}
```

### Example 3: Validate + Embed

```bash
# Step 1: Validate
{
  "command": "validate",
  "params": {
    "input_file": "data/crawled/onehago/packaging_enhanced.jsonl"
  }
}

# Output:
{
  "status": "success",
  "quality_score": 0.95,
  "issues": {
    "missing_images": 414,
    "invalid_capacity": 23,
    "missing_neck_size": 1500
  }
}

# Step 2: Embed (if quality OK)
{
  "command": "embed",
  "params": {
    "input_file": "data/crawled/onehago/packaging_enhanced.jsonl",
    "collection_name": "onehago",
    "overwrite": true
  }
}

# Output:
{
  "status": "success",
  "collection_name": "onehago",
  "total_vectors": 22870,
  "embedding_time_sec": 203.5
}
```

---

## 📁 File Structure

```
.claude/skills/
├── rag-pipeline/
│   ├── skill.md                         # Skill documentation
│   ├── scripts/
│   │   ├── skill.py                     # Main skill interface
│   │   ├── collection_manager.py        # Existing
│   │   ├── preprocessors/               # NEW
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # BasePreprocessor
│   │   │   ├── onehago.py               # OnehagoPreprocessor
│   │   │   ├── chungjinkorea.py         # ChungjinkoreaPreprocessor
│   │   │   └── registry.py              # Preprocessor registry
│   │   ├── validators/                  # NEW
│   │   │   ├── __init__.py
│   │   │   ├── data_validator.py        # Quality checks
│   │   │   └── schema_validator.py      # Schema validation
│   │   └── embedders/                   # NEW
│   │       ├── __init__.py
│   │       └── smart_embedder.py        # Enhanced embedder
│   └── config/
│       └── preprocessing/               # NEW
│           ├── onehago.yaml
│           └── chungjinkorea.yaml
│
└── web-crawler-pipeline/
    ├── skill.md
    ├── scripts/
    │   ├── skill.py                     # Updated with RAG integration
    │   └── orchestrator.py              # NEW: Pipeline orchestration
    └── config/
        └── pipelines/                   # NEW
            ├── onehago_full.yaml
            └── chungjinkorea_full.yaml
```

---

## 🎯 Benefits

### Automation:
- ✅ Single command: crawl → embed
- ✅ No manual steps
- ✅ Consistent processing

### Quality:
- ✅ Automated validation
- ✅ Quality thresholds
- ✅ Issue detection

### Maintainability:
- ✅ Modular design
- ✅ Site-specific preprocessors
- ✅ Easy to extend

### Reproducibility:
- ✅ Configuration-driven
- ✅ Versioned configs
- ✅ Checkpointing

### Scalability:
- ✅ Batch processing
- ✅ Parallel execution
- ✅ Progress tracking

---

## 📊 Expected Results

### Before (Manual):
```
Time: 2-3 days for full pipeline
Steps: 5 manual steps
Quality: Inconsistent
Errors: Frequent manual errors
Reproducibility: Hard to reproduce
```

### After (Automated):
```
Time: 1-2 hours (mostly waiting)
Steps: 1 command
Quality: Consistent (95%+)
Errors: Automatic detection & reporting
Reproducibility: Perfect (config-driven)
```

---

## 🚀 Next Steps

### Immediate (This Week):
1. ✅ Design architecture (this document)
2. ✅ Get approval for approach
3. 🔄 Implement Phase 1 (rag-pipeline enhancement)

### Commands to create:
```bash
# Create preprocessor framework
mkdir -p .claude/skills/rag-pipeline/scripts/preprocessors
mkdir -p .claude/skills/rag-pipeline/scripts/validators
mkdir -p .claude/skills/rag-pipeline/scripts/embedders

# Create config structure
mkdir -p .claude/skills/rag-pipeline/config/preprocessing
```

---

## 💡 Key Design Decisions

### 1. Strategy Pattern for Preprocessing
**Why**: Different sites need different preprocessing logic
**Benefit**: Easy to add new sites without changing core code

### 2. Configuration-Driven
**Why**: Allows non-developers to adjust preprocessing
**Benefit**: Flexibility without code changes

### 3. Validation Before Embedding
**Why**: Catch issues early
**Benefit**: Higher quality embeddings

### 4. Checkpoint Support
**Why**: Long-running pipelines need recovery
**Benefit**: Resume from failures

### 5. Skill-to-Skill Communication
**Why**: Modular architecture
**Benefit**: Skills can be used independently or together

---

**Status**: 🎨 **Architecture Design Complete**
**Next Action**: Implement Phase 1 (rag-pipeline enhancement)
**Approval Needed**: ✅ User approval to proceed

**Version**: 1.0.0
**Date**: 2025-11-04
