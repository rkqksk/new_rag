---
name: excel-processing
description: Excel XLSX CSV spreadsheet table parsing openpyxl pandas 엑셀 스프레드시트 테이블 파싱 거래명세서 재고 데이터 분석 formula pivot chart 수식 피벗 차트 manufacturing data
---

# Excel Spreadsheet Processing

## When to Use
- Excel 파일 처리, Excel file processing
- 스프레드시트 파싱, spreadsheet parsing
- CSV 데이터, CSV data
- 테이블 추출, table extraction
- 거래명세서, transaction records
- 재고 관리, inventory management
- 데이터 분석, data analysis
- 수식 생성, formula creation

## Core Capabilities
1. **Reading** - openpyxl, pandas, format detection
2. **Writing** - Create Excel from data, apply formatting
3. **Analysis** - Formulas, pivot tables, charts
4. **Manufacturing** - Transaction records (거래명세서), inventory sheets
5. **RAG Integration** - Parse tables for indexing

## Quick Actions

### Read Excel
```python
import pandas as pd
from openpyxl import load_workbook

# Using pandas
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')

# Using openpyxl
wb = load_workbook('data.xlsx')
ws = wb.active
value = ws['A1'].value
```

### Create Excel
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

wb = Workbook()
ws = wb.active
ws.title = "거래명세서"

# Headers
ws['A1'] = "품목코드"
ws['A1'].font = Font(bold=True)
ws['A1'].fill = PatternFill(start_color="366092", fill_type="solid")

wb.save('output.xlsx')
```

### Add Formulas
```python
# Calculations
ws['D2'] = '=B2*C2'  # Quantity * Price
ws['D10'] = '=SUM(D2:D9)'  # Total

# Conditional
ws['E2'] = '=IF(D2>1000, "High", "Normal")'
```

### Batch Processing
```python
# Process multiple files
python scripts/batch_excel.py \
  --input data/*.xlsx \
  --operation parse \
  --output parsed/
```

## Manufacturing Use Cases

### Transaction Records (거래명세서)
```python
structure = {
    'header': {
        'document_id': str,
        'date': datetime,
        'supplier': str,
        'buyer': str
    },
    'items': [
        {
            'item_code': str,
            'quantity': float,
            'unit_price': decimal,
            'amount': decimal
        }
    ],
    'totals': {
        'subtotal': decimal,
        'tax': decimal,
        'total': decimal
    }
}
```

### Inventory Tracking
- Stock levels and movements
- Reorder point calculations
- Aging inventory analysis
- SKU management

### Quality Control
- Defect tracking
- Statistical process control (SPC)
- Trend analysis
- Compliance reporting

## Integration
- **data-collection**: Parse crawled Excel files
- **rag-optimization**: Index table data
- **manufacturing-vision**: Inspection result reports
- **saas-operations**: Usage reports, billing statements

## Key Files
- `scripts/excel_processor.py` - Excel processing utilities
- `src/parsers/excel_parser.py` - Parsing logic

## Supported Formats
- `.xlsx` - Excel 2007+
- `.xls` - Legacy Excel
- `.csv` - Comma-separated values
- `.tsv` - Tab-separated values
