---
name: packaging-expert
description: Expert knowledge for processing packaging and container manufacturing documents including material specs, regulatory compliance, quality control, and design specifications
license: MIT
metadata:
  version: "1.0.0"
  domain: "packaging"
  triggers:
    - "packaging document"
    - "container specification"
    - "material data sheet"
    - "regulatory compliance"
    - "barrier properties"
    - "bottle"
    - "pump"
    - "cap"
---

# Packaging Expert Skill

## Overview

This skill provides specialized knowledge for processing packaging and container manufacturing documents in the RAG Enterprise system. It handles material specifications, regulatory compliance, quality standards, and packaging design documentation.

## When to Activate

This skill activates when:
- Processing packaging-related documents (material specs, container drawings, etc.)
- User requests packaging document analysis
- Need to extract material properties and dimensions
- Identifying regulatory compliance requirements
- Classifying packaging and container specifications

## Core Capabilities

### 1. Document Classification

Automatically classifies documents into 6 packaging categories:

- **Material Spec**: Material specifications, data sheets, resin specs
- **Container Drawing**: Technical drawings, bottle specs, dimensional specs
- **Regulatory**: FDA compliance, food contact, migration testing
- **Quality Spec**: Inspection criteria, acceptance standards, quality specs
- **Testing Protocol**: Test methods, validation procedures
- **Design Spec**: Packaging design, artwork specifications

### 2. Material Recognition

Identifies **40+ packaging materials**:

**Plastics**:
- PET (Polyethylene Terephthalate)
- HDPE (High-Density Polyethylene)
- LDPE (Low-Density Polyethylene)
- PP (Polypropylene)
- PS (Polystyrene)
- PVC (Polyvinyl Chloride)
- PETG, PC, PLA, ABS

**Specialty Materials**:
- Barrier films (EVOH, PVDC)
- Biodegradable polymers
- Glass (Type I, II, III)
- Aluminum, Steel

### 3. Dimension Extraction

Extracts packaging dimensions and properties:

```python
{
  "dimensions": {
    "height": "150mm",
    "diameter": "65mm",
    "neck_size": "28/410",
    "capacity": "500ml",
    "thickness": "0.5mm",
    "weight": "25g"
  },
  "properties": {
    "barrier_oxygen": "<1.0 cc/pkg/day",
    "barrier_moisture": "<0.1 g/pkg/day",
    "drop_test": "1.2m",
    "burst_strength": "200 PSI"
  }
}
```

### 4. Regulatory Standards

Recognizes compliance requirements:

**FDA Regulations**:
- 21 CFR Part 177 (Indirect Food Additives)
- 21 CFR Part 178 (Adjuvants and Production Aids)
- Food Contact Notification (FCN)

**EU Regulations**:
- Regulation (EC) No 1935/2004
- Regulation (EU) No 10/2011
- REACH Regulation

**Environmental Standards**:
- Recyclability codes (1-7)
- RoHS Compliance
- ISO 14001 (Environmental Management)

### 5. Quality Metrics

Identifies packaging quality parameters:

- **Barrier Properties**: Oxygen permeability, moisture barrier
- **Mechanical Strength**: Burst strength, drop test, compression
- **Seal Integrity**: Leak testing, seal strength
- **Chemical Resistance**: pH stability, solvent resistance
- **Optical Properties**: Transparency, haze, color

## Usage

### Document Processing

```python
from .claude.skills.packaging_expert import skill

result = skill.process_document(document)

# Returns enriched document with:
# - doc_type classification
# - material identification
# - dimensional specifications
# - barrier properties
# - regulatory standards
```

### Classification

Documents are scored based on keyword presence:

- **Threshold**: ≥2 packaging indicators required
- **Indicators**: packaging, container, bottle, material, barrier, fda, food contact, etc.
- **Scoring**: Highest-scoring category wins

### Metadata Enhancement

Adds packaging-specific metadata:

```json
{
  "domain": "packaging",
  "doc_type": "material_spec",
  "categories": ["materials", "specifications", "technical"],
  "materials": ["PET", "HDPE"],
  "dimensions": {
    "capacity": "500ml",
    "neck_size": "28/410"
  },
  "regulatory": ["FDA 21 CFR 177", "EU 10/2011"],
  "properties": {
    "barrier_oxygen": "<1.0 cc/pkg/day"
  }
}
```

## Integration with RAG Pipeline

### Vector Search Enhancement

Use extracted metadata for improved retrieval:

```python
# Filter by material type
results = qdrant.search(
    collection="packaging_docs",
    filter={"materials": {"$contains": "PET"}}
)

# Filter by capacity range
results = qdrant.search(
    collection="packaging_docs",
    filter={"capacity_ml": {"$gte": 450, "$lte": 550}}
)

# Filter by regulatory compliance
results = qdrant.search(
    collection="packaging_docs",
    filter={"regulatory": {"$contains": "FDA"}}
)
```

### Example Queries

**Query**: "What PET bottles are available with 500ml capacity?"

**Enhanced Retrieval**:
1. Skill identifies: material=PET, capacity=500ml, type=container
2. Search filters: materials contains "PET", capacity=500ml
3. Returns: PET bottle specifications matching criteria

**Query**: "Show me FDA-compliant food contact materials"

**Enhanced Retrieval**:
1. Skill identifies: regulatory=FDA, application=food_contact
2. Search filters: regulatory contains "FDA", doc_type=material_spec OR regulatory
3. Returns: FDA-compliant material specifications

## Material Properties Reference

### Common Plastics

#### PET (Polyethylene Terephthalate)
- **Applications**: Beverage bottles, food containers
- **Properties**: Excellent barrier, clarity, recyclable
- **Recycling Code**: #1

#### HDPE (High-Density Polyethylene)
- **Applications**: Milk jugs, detergent bottles
- **Properties**: Chemical resistance, impact strength
- **Recycling Code**: #2

#### PP (Polypropylene)
- **Applications**: Caps, closures, containers
- **Properties**: Heat resistance, fatigue resistance
- **Recycling Code**: #5

#### PETG (PET Glycol-modified)
- **Applications**: Cosmetic containers, displays
- **Properties**: Impact resistance, clarity
- **Special**: Heat-sealable

### Barrier Materials

#### EVOH (Ethylene Vinyl Alcohol)
- **Barrier Type**: Oxygen barrier
- **Performance**: Excellent O₂ barrier
- **Application**: Multi-layer films

#### PVDC (Polyvinylidene Chloride)
- **Barrier Type**: Moisture & oxygen barrier
- **Performance**: Superior barrier properties
- **Application**: Film coatings

## Regulatory Compliance

### FDA Food Contact

**21 CFR Part 177**: Indirect Food Additives
- Polymers (§177.1520, §177.1630, etc.)
- Adhesives and coatings
- Paper and paperboard

**21 CFR Part 178**: Adjuvants and Production Aids
- Antioxidants, stabilizers
- Colorants, pigments
- Processing aids

**Food Contact Notification (FCN)**:
- Alternative to food additive petition
- Faster approval process
- Substance-specific clearance

### EU Regulations

**Regulation (EC) 1935/2004**: Framework regulation
- General safety requirements
- Good Manufacturing Practice (GMP)
- Active and intelligent materials

**Regulation (EU) 10/2011**: Plastic materials
- Positive list of monomers
- Migration limits (OML, SML)
- Functional barriers

### Environmental

**Recyclability**:
- Codes 1-7 classification
- Material identification
- Collection and sorting

**RoHS**: Restriction of Hazardous Substances
- Lead, mercury, cadmium limits
- Electrical/electronic packaging

**REACH**: Registration, Evaluation, Authorization
- Chemical substance registration
- SVHCs (Substances of Very High Concern)

## Quality Standards

### ASTM Standards

- **ASTM D3985**: Oxygen permeability
- **ASTM F1927**: Moisture vapor transmission
- **ASTM D2463**: Drop impact testing
- **ASTM D642**: Compression test

### ISO Standards

- **ISO 15747**: Plastic containers - Compression
- **ISO 2247**: Transport packaging - Vibration
- **ISO 8317**: Child-resistant packaging
- **ISO 14001**: Environmental management

## Best Practices

### Document Naming

Use clear naming conventions:
- `Material-Spec-PET-Grade-XXXX.pdf`
- `Container-Drawing-500ml-Bottle-vX.dwg`
- `FDA-FCN-Material-Name.pdf`

### Metadata Tagging

Always include:
- Material type and grade
- Dimensions and capacity
- Regulatory status
- Supplier information
- Revision date

### Specifications

Document clearly:
- Material properties with units
- Dimensional tolerances
- Test methods and criteria
- Acceptance limits
- Regulatory references

## Troubleshooting

### Material Not Identified

**Issue**: Material type not recognized

**Solution**:
- Use standard abbreviations (PET, HDPE, not polyester)
- Include full chemical name for specialty materials
- Add material to config/materials.yaml
- Check for typos in material names

### Missing Dimensions

**Issue**: Dimensions not extracted

**Solution**:
- Use standard format: "100mm", "500ml", "28/410"
- Include units with all measurements
- Use technical drawing conventions
- Specify tolerances clearly

## Related Skills

- **manufacturing-expert**: Complementary for production processes
- **rag-pipeline**: Orchestrates document processing workflow
- **rag-vector-search**: Uses enhanced metadata for retrieval

## Configuration

Custom terminology and patterns: `.claude/skills/packaging-expert/config/`

- `materials.yaml`: Packaging materials database
- `standards.yaml`: Regulatory standards mapping
- `patterns.yaml`: Regex patterns for extraction

## Resources

For detailed implementation, see:
- `skill.py`: Core processing logic
- `config/`: Configuration files
- Plugin tests: `tests/test_packaging_expert.py`
