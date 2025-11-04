# Domain Expert Workflow

**Purpose**: Enrich documents with domain-specific metadata extraction and terminology recognition.

---

## Overview

Domain experts are plugins that add specialized knowledge processing to the RAG pipeline, extracting industry-specific metadata, terminology, and parameters from documents.

### Available Domain Experts
- **Manufacturing Expert** - SOP, FMEA, quality specs, process parameters
- **Packaging Expert** - Materials, regulatory compliance, container specs

---

## Architecture

```
Document
    ↓
SKILL: rag-pipeline
    ↓
Plugin: manufacturing_expert/ or packaging_expert/
    ├── plugin.py (logic)
    └── config/ (YAML files with terminology, patterns)
    ↓
Enriched Metadata
    ↓
Qdrant (stored with vectors)
```

---

## Manufacturing Expert

### Auto-Classification

**Document Types** (8 types):
- SOP (Standard Operating Procedures)
- Equipment specifications
- Quality control plans
- Defect analysis reports
- Batch records
- FMEA (Failure Mode and Effects Analysis)
- Calibration procedures
- Audit reports

### Terminology Extraction (150+ terms)

**Quality Metrics**:
- Cpk, Ppk (Process capability)
- OEE (Overall Equipment Effectiveness)
- PPM (Parts Per Million defects)
- MTBF/MTTR (Mean Time Between/To Failure/Repair)
- Yield, First Pass Yield

**Process Parameters**:
- Temperature, Pressure, Time, Speed
- Cycle time, Takt time
- Tolerances (±0.1mm, ±2°C)

**Standards & Compliance**:
- ISO 9001, ISO 13485, ISO 14001
- FDA 21 CFR Part 11, Part 820
- GMP, cGMP
- Six Sigma, Lean Manufacturing

### Usage Example

```python
from .claude.skills.rag_pipeline import skill

result = skill.execute('process', {
    'file_path': 'manufacturing_sop.pdf',
    'options': {
        'use_domain_expert': 'manufacturing'
    }
})

# Result includes enriched metadata:
{
    'doc_type': 'sop',
    'domain': 'manufacturing',
    'terminology': ['cpk', 'oee', 'iso 9001', 'calibration'],
    'quality_metrics': {
        'cpk': ['1.33', '1.67'],
        'oee': ['85%']
    },
    'parameters': {
        'temperature': ['150°C', '180°C'],
        'pressure': ['45 psi']
    },
    'standards': ['ISO 9001', 'FDA 21 CFR Part 11']
}
```

---

## Packaging Expert

### Auto-Classification

**Document Types** (6 types):
- Material specifications
- Container/bottle drawings
- Regulatory compliance docs
- Quality test reports
- Supplier data sheets
- Packaging design specs

### Material Extraction

**Core Plastics**:
- PET, PETG (Polyethylene Terephthalate)
- PP (Polypropylene)
- HDPE, LLDPE, LDPE (Polyethylene variants)
- PS (Polystyrene)

**Barrier Films**:
- EVOH (Ethylene Vinyl Alcohol)
- PVDC (Polyvinylidene Chloride)
- Aluminum oxide coatings

**Additives**:
- UV stabilizers, Colorants, Recycled content

### Regulatory Standards

**United States**:
- FDA 21 CFR 177 (Food Contact Substances)
- FDA 21 CFR 178 (Indirect additives)

**Europe**:
- EU 10/2011 (Plastic materials)
- REACH (Chemical safety)
- EU 2023/2006 (GMP for materials)

**Korea**:
- 식품위생법 (Food Sanitation Act)
- 식품용기규격 (Food Container Standards)

### Usage Example

```python
result = skill.execute('process', {
    'file_path': 'packaging_spec.pdf',
    'options': {
        'use_domain_expert': 'packaging'
    }
})

# Result includes:
{
    'doc_type': 'material_spec',
    'domain': 'packaging',
    'materials': ['PET', 'HDPE'],
    'capacity': '500ml',
    'dimensions': {
        'height': '180mm',
        'diameter': '65mm',
        'neck': '28/410'
    },
    'barrier_properties': {
        'oxygen': '<0.005 cc/pkg/day',
        'moisture': '<0.05 g/pkg/day'
    },
    'regulatory': ['FDA 21 CFR 177.1520', 'EU 10/2011']
}
```

---

## Plugin Architecture

### Base Structure

```
plugins/
├── base_plugin.py           # Abstract base class
└── {domain}_expert/
    ├── __init__.py
    ├── plugin.py            # Main logic
    └── config/
        ├── terminology.yaml # Domain terms
        ├── patterns.yaml    # Extraction patterns
        └── standards.yaml   # Standards/regulations
```

### Configuration-Driven Design

**Example: terminology.yaml**
```yaml
quality_metrics:
  - cpk
  - ppk
  - oee
  - yield

process_operations:
  - calibration
  - validation
  - changeover
```

**Example: patterns.yaml**
```yaml
parameters:
  temperature:
    patterns:
      - "(\d+\.?\d*)\s*°C"
      - "(\d+\.?\d*)\s*°F"
    unit_conversion:
      "°F": "°C"
```

---

## Integration with RAG Query

### Metadata Filtering

Once documents are processed with domain experts, you can filter by extracted metadata:

```python
# Find all SOPs with Cpk requirements
answer = skill.execute('query', {
    'question': 'What are the Cpk requirements?',
    'filters': {
        'doc_type': 'sop',
        'domain': 'manufacturing',
        'terminology': {'$contains': 'cpk'}
    }
})

# Find PET bottles with FDA compliance
results = skill.execute('search', {
    'query': 'PET bottle specifications',
    'filters': {
        'materials': {'$contains': 'PET'},
        'regulatory': {'$contains': 'FDA'}
    }
})
```

---

## Adding New Domain Experts

### Step 1: Create Plugin Structure
```bash
mkdir -p plugins/medical_expert/config
touch plugins/medical_expert/__init__.py
touch plugins/medical_expert/plugin.py
```

### Step 2: Implement Plugin Class
```python
# plugins/medical_expert/plugin.py
from plugins.base_plugin import BasePlugin

class MedicalExpertPlugin(BasePlugin):
    def __init__(self):
        super().__init__('medical')
        self.load_config()

    def can_process(self, document):
        # Check if document is medical-related
        indicators = ['patient', 'diagnosis', 'treatment', 'medical']
        return any(ind in document['content'].lower() for ind in indicators)

    def process_document(self, document):
        # Extract medical terminology
        result = self.extract_terminology(document['content'])
        return result
```

### Step 3: Create Config Files
```yaml
# plugins/medical_expert/config/terminology.yaml
procedures:
  - mri
  - ct scan
  - biopsy

conditions:
  - hypertension
  - diabetes
  - asthma
```

### Step 4: Register Plugin
```python
# plugins/__init__.py
from .medical_expert import MedicalExpertPlugin

AVAILABLE_PLUGINS = {
    'manufacturing': 'plugins.manufacturing_expert',
    'packaging': 'plugins.packaging_expert',
    'medical': 'plugins.medical_expert'  # Add new plugin
}
```

---

## Related Resources

- `/component plugins` - Plugin architecture details
- `/workflow document-processing` - How plugins are integrated
- `/workflow rag-query` - Querying with metadata filters

---

**Last Updated**: 2025-11-03
