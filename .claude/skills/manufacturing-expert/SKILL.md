---
name: manufacturing-expert
description: Expert knowledge for processing manufacturing and production engineering documents including SOPs, equipment specs, FMEA, defect analysis, and quality control documentation
license: MIT
metadata:
  version: "1.0.0"
  domain: "manufacturing"
  triggers:
    - "manufacturing document"
    - "SOP processing"
    - "equipment specification"
    - "quality control"
    - "FMEA analysis"
    - "defect analysis"
    - "production records"
---

# Manufacturing Expert Skill

## Overview

This skill provides specialized knowledge for processing manufacturing and production engineering documents in the RAG Enterprise system. It handles document classification, terminology extraction, quality metrics identification, and compliance standards recognition.

## When to Activate

This skill activates when:
- Processing manufacturing-related documents (SOPs, equipment specs, FMEA, etc.)
- User requests manufacturing document analysis
- Need to extract quality metrics (Cpk, OEE, PPM, MTBF)
- Identifying manufacturing terminology and standards
- Classifying production and quality control documents

## Core Capabilities

### 1. Document Classification

Automatically classifies documents into 8 manufacturing categories:

- **SOP**: Standard Operating Procedures, Work Instructions
- **Equipment Spec**: Equipment specifications, machine manuals
- **Control Plan**: Process control plans, FMEA documents
- **Defect Analysis**: Root cause analysis, 8D reports
- **Maintenance**: PM schedules, preventive maintenance procedures
- **Batch Record**: Production records, lot records, traceability
- **Deviation**: Deviation reports, non-conformance reports (NCR)
- **General Manufacturing**: Other manufacturing documentation

### 2. Terminology Extraction

Recognizes **150+ manufacturing terms** across categories:

**Quality Metrics**:
- Cpk, Cp (Process Capability)
- OEE (Overall Equipment Effectiveness)
- PPM (Parts Per Million)
- MTBF, MTTR (Mean Time metrics)
- Yield, Defect Rate, First Pass Yield

**Process Parameters**:
- Temperature (°C, °F, K)
- Pressure (PSI, bar, Pa)
- Time (cycle time, takt time)
- Speed (RPM, m/s)
- Flow rate (L/min, CFM)

**Standards & Compliance**:
- ISO 9001, ISO 13485, ISO 14001
- FDA 21 CFR Part 11, Part 820
- GMP (Good Manufacturing Practice)
- IATF 16949 (Automotive)

### 3. Entity Recognition

Extracts structured data:

```python
{
  "quality_metrics": {
    "cpk": ["1.33", "1.67"],
    "oee": ["85%", "92%"],
    "ppm": ["<100", "50"]
  },
  "process_parameters": {
    "temperature": ["180°C ± 5°C"],
    "pressure": ["50 PSI"],
    "cycle_time": ["45 seconds"]
  },
  "standards": ["ISO 9001:2015", "FDA 21 CFR Part 11"]
}
```

## Usage

### Document Processing

```python
# The skill automatically activates when processing manufacturing docs
from .claude.skills.manufacturing_expert import skill

result = skill.process_document(document)

# Returns enriched document with:
# - doc_type classification
# - extracted terminology
# - quality metrics
# - compliance standards
# - categories and tags
```

### Classification

Documents are scored based on keyword presence:

- **Threshold**: ≥2 manufacturing indicators required
- **Indicators**: sop, equipment, fmea, cpk, oee, ppm, defect, quality control, etc.
- **Scoring**: Highest-scoring category wins

### Metadata Enhancement

Adds manufacturing-specific metadata:

```json
{
  "domain": "manufacturing",
  "doc_type": "sop",
  "categories": ["process", "quality", "compliance"],
  "terminology": ["cpk", "oee", "iso 9001"],
  "quality_metrics": {
    "cpk": ["1.33"],
    "oee": ["85%"]
  },
  "standards": ["ISO 9001:2015"]
}
```

## Integration with RAG Pipeline

### Vector Search Enhancement

Use extracted metadata for improved retrieval:

```python
# Filter by document type
results = qdrant.search(
    collection="manufacturing_docs",
    filter={"doc_type": "sop"}
)

# Filter by quality metric
results = qdrant.search(
    collection="manufacturing_docs",
    filter={"terminology": {"$contains": "cpk"}}
)

# Filter by compliance standard
results = qdrant.search(
    collection="manufacturing_docs",
    filter={"standards": {"$contains": "iso 9001"}}
)
```

### Example Queries

**Query**: "What are the Cpk requirements for the injection molding process?"

**Enhanced Retrieval**:
1. Skill identifies: domain=manufacturing, metric=cpk, process=injection_molding
2. Search filters: doc_type=sop OR control_plan, terminology contains "cpk"
3. Returns: Relevant SOPs and control plans with Cpk specifications

**Query**: "Show me FMEA documents for equipment failure modes"

**Enhanced Retrieval**:
1. Skill identifies: doc_type=control_plan, topic=fmea, focus=equipment
2. Search filters: doc_type=control_plan, terminology contains "fmea"
3. Returns: FMEA documents with equipment failure analysis

## Quality Metrics Reference

### Process Capability

- **Cpk**: Process capability index (≥1.33 acceptable, ≥1.67 excellent)
- **Cp**: Process capability ratio
- **Ppk**: Process performance index

### Efficiency Metrics

- **OEE**: Overall Equipment Effectiveness = Availability × Performance × Quality
  - Target: ≥85% (world-class)
- **TEEP**: Total Effective Equipment Performance
- **Yield**: First Pass Yield, Overall Yield

### Reliability Metrics

- **MTBF**: Mean Time Between Failures
- **MTTR**: Mean Time To Repair
- **Uptime**: Equipment availability percentage

### Defect Metrics

- **PPM**: Parts Per Million (defect rate)
- **DPMO**: Defects Per Million Opportunities
- **FPY**: First Pass Yield

## Standards & Compliance

### ISO Standards

- **ISO 9001**: Quality Management Systems
- **ISO 13485**: Medical Devices QMS
- **ISO 14001**: Environmental Management
- **IATF 16949**: Automotive QMS

### FDA Regulations

- **21 CFR Part 11**: Electronic Records
- **21 CFR Part 820**: Quality System Regulation
- **GMP**: Good Manufacturing Practice

### Industry Standards

- **Six Sigma**: DMAIC methodology
- **Lean Manufacturing**: 5S, Kaizen, JIT
- **8D**: Eight Disciplines problem solving

## Best Practices

### Document Naming

Use clear naming conventions:
- `SOP-XXX-ProcessName-vX.X.pdf`
- `FMEA-Equipment-Date.xlsx`
- `ControlPlan-ProductLine.docx`

### Metadata Tagging

Always include:
- Document type
- Process/equipment name
- Revision/version
- Approval date
- Applicable standards

### Quality Metrics

Document metrics clearly:
- Use standard notation (Cpk: 1.33, OEE: 85%)
- Include measurement date/period
- Specify control limits
- Note calculation method

## Troubleshooting

### Low Classification Confidence

**Issue**: Document not classified correctly

**Solution**:
- Ensure document contains ≥2 manufacturing indicators
- Add relevant keywords to content
- Check filename for classification hints
- Review terminology database for missing terms

### Missing Terminology

**Issue**: Important terms not extracted

**Solution**:
- Add custom terms to config/terminology.yaml
- Use standard notation for metrics
- Include units with measurements
- Reference relevant standards explicitly

## Related Skills

- **packaging-expert**: Complementary for packaging specifications
- **rag-pipeline**: Orchestrates document processing workflow
- **rag-vector-search**: Uses enhanced metadata for retrieval

## Configuration

Custom terminology and patterns: `.claude/skills/manufacturing-expert/config/`

- `terminology.yaml`: Custom manufacturing terms
- `patterns.yaml`: Regex patterns for extraction
- `standards.yaml`: Compliance standards mapping

## Resources

For detailed implementation, see:
- `skill.py`: Core processing logic
- `config/`: Configuration files
- Plugin tests: `tests/test_manufacturing_expert.py`
