---
name: excel
description: "Intelligent Excel parsing and data quality verification for product databases"
category: data-quality
complexity: moderate
mcp-servers: [filesystem]
personas: []
---

# /sc:excel - Excel Data Quality Verification

## Triggers
- Excel file parsing and product data extraction needs
- Data quality comparison between Excel (source of truth) and database
- Multi-file Excel processing with varying layouts
- Product catalog verification and missing data identification

## Usage
```
/sc:excel [filename.xlsx] [--all] [--compare] [--extract-images] [--report json|markdown]
```

## Behavioral Flow
1. **Detect Layout**: Analyze Excel structure (multi-column vs simple table)
2. **Parse Intelligently**: Extract product codes, specs, packaging, and images
3. **Compare with DB**: Match Excel products against Qdrant database
4. **Identify Gaps**: Find missing products, missing codes, spec mismatches
5. **Generate Report**: Create actionable data quality report with recommendations

Key behaviors:
- Automatic layout detection for complex multi-column Excel files
- Handles multiple products per row (e.g., Row 5: CODE labels, Row 6: actual codes)
- Extracts embedded images from Excel for visual verification
- Compares product codes and specs with Qdrant vector database
- Generates comprehensive gap analysis and missing data reports

## Tool Coordination
- **Filesystem MCP**: Read Excel files from data/excel_uploads/raw/
- **Read**: Inspect Excel structure and validate file format
- **Bash**: Call FastAPI endpoints for database comparison
- **Write**: Generate quality reports and parsed JSON outputs

## Key Patterns
- **Layout Detection**: Row 5 CODE count → multi-column vs simple table parser
- **Data Extraction**: CODE (row 6), SPEC (row 8), 포장 (row 10), 금형 (row 11+)
- **Database Comparison**: Excel product codes → Qdrant payload specifications.제품 코드
- **Gap Analysis**: Missing in DB, missing codes, spec mismatches → actionable report

## Examples

### Parse Single Excel File
```
/sc:excel 제품 리스트_3.PET.xlsx
# Parses PET product list
# Extracts codes, specs, images
# Compares with database and generates report
```

### Process All Excel Files
```
/sc:excel --all --compare
# Processes all 7 Excel files:
#   - PE, PET, PETG, PP/PS/ABS
#   - 부자재, 전용몰드, 다층브로우
# Generates comprehensive quality report across all materials
```

### Extract Images Only
```
/sc:excel 제품 리스트_3.PET.xlsx --extract-images
# Extracts embedded product images to data/excel_uploads/images/
# Useful for visual verification and image search testing
```

### Generate JSON Report
```
/sc:excel --all --report json
# Processes all files
# Outputs machine-readable JSON for automation
# Includes: total_excel, total_db, missing_in_db, missing_codes, spec_mismatches
```

## Boundaries

**Will:**
- Parse complex multi-column Excel layouts automatically
- Extract product data: codes, specs, packaging, mold info, images
- Compare Excel (source of truth) with Qdrant database
- Generate detailed gap analysis with missing products and mismatches
- Handle all 7 Excel files in parallel for efficiency

**Will Not:**
- Modify Excel files or source data
- Automatically update Qdrant database (requires user confirmation)
- Parse non-product Excel files (e.g., financial reports)
- Handle password-protected or corrupted Excel files

## Expected Outputs

### Data Quality Report Format
```json
{
  "total_excel": 846,
  "total_db": 846,
  "total_db_with_codes": 751,
  "missing_in_db": 1,
  "missing_codes_in_db": 95,
  "spec_mismatches": 12,
  "details": {
    "missing_in_db": ["BT050-R002"],
    "missing_codes": ["43파이 룰렛캡", "60ml 펌프캡"],
    "spec_mismatches": [
      {
        "code": "BT050-R001",
        "excel_spec": "PET / 50ml",
        "db_spec": "50ml PET병"
      }
    ]
  }
}
```

### Recommended Actions
1. **Missing Products**: Re-crawl specific product pages
2. **Missing Codes**: Update crawler to extract 제품 코드 field
3. **Spec Mismatches**: Verify which is correct (Excel or web)

## Integration Points
- **FastAPI**: POST /api/v1/admin/excel/analyze
- **Qdrant**: Compare against products_all collection
- **LeadAgent**: Delegate parallel processing for multiple files
