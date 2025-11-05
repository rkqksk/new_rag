---
name: xlsx-operations
description: Comprehensive Excel spreadsheet operations including creation, editing, analysis, formulas, formatting, and data visualization
---

# XLSX Operations

Advanced Excel spreadsheet manipulation for the RAG enterprise system, specializing in transaction records, inventory data, and manufacturing analytics.

## Core Capabilities

### 1. Spreadsheet Creation
- Generate structured Excel files from data
- Apply templates and layouts
- Set up workbook structure with multiple sheets
- Configure page setup and print areas

### 2. Data Analysis
- Parse and extract data from existing spreadsheets
- Perform calculations and aggregations
- Apply statistical functions
- Generate pivot tables and summaries

### 3. Formula Management
- Insert and update Excel formulas
- Handle complex formula dependencies
- Validate formula correctness
- Convert formulas to values when needed

### 4. Formatting & Styling
- Apply cell formatting (fonts, colors, borders)
- Set number formats and data types
- Create conditional formatting rules
- Style headers and data ranges

### 5. Data Validation
- Set up data validation rules
- Create dropdown lists
- Enforce data constraints
- Validate data integrity

## Manufacturing-Specific Operations

### Transaction Records (거래명세서)
```python
# Structure for transaction records
{
    'header': {
        'document_id': str,
        'date': datetime,
        'supplier': str,
        'buyer': str,
    },
    'items': [
        {
            'item_code': str,
            'description': str,
            'quantity': float,
            'unit_price': decimal,
            'amount': decimal,
            'tax': decimal
        }
    ],
    'totals': {
        'subtotal': decimal,
        'tax_total': decimal,
        'grand_total': decimal
    }
}
```

### Inventory Sheets
- Track stock levels and movements
- Calculate reorder points
- Monitor aging inventory
- Generate stock reports

### Quality Control Data
- Defect tracking and analysis
- Statistical process control (SPC)
- Trend analysis
- Compliance reporting

## Common Tasks

### Reading Excel Files
```python
import pandas as pd
from openpyxl import load_workbook

# Using pandas for data analysis
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')

# Using openpyxl for detailed cell access
wb = load_workbook('data.xlsx')
ws = wb.active
cell_value = ws['A1'].value
```

### Writing Excel Files
```python
# Create new workbook
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border

wb = Workbook()
ws = wb.active
ws.title = "Transaction Records"

# Apply formatting
header_font = Font(bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

# Write data
ws['A1'] = "Item Code"
ws['A1'].font = header_font
ws['A1'].fill = header_fill
```

### Formulas
```python
# Add formula
ws['D2'] = '=B2*C2'  # Quantity * Unit Price

# Sum formula
ws['D10'] = '=SUM(D2:D9)'

# Conditional formula
ws['E2'] = '=IF(D2>1000, "High", "Normal")'
```

### Data Validation
```python
from openpyxl.worksheet.datavalidation import DataValidation

# Dropdown list
dv = DataValidation(type="list", formula1='"Option1,Option2,Option3"')
ws.add_data_validation(dv)
dv.add('A2:A100')
```

## RAG System Integration

### Document Processing Pipeline
1. **Extract**: Read Excel from uploaded files or crawler results
2. **Parse**: Convert to structured data format
3. **Chunk**: Split large sheets into manageable sections
4. **Embed**: Generate vector embeddings for searchable content
5. **Index**: Store in Qdrant with metadata

### Metadata Structure
```python
{
    'file_name': str,
    'sheet_name': str,
    'row_range': tuple,
    'column_range': tuple,
    'data_type': str,  # 'transaction', 'inventory', 'quality'
    'date_created': datetime,
    'checksum': str
}
```

### Search Enhancement
- Enable natural language queries: "Show all transactions from last month"
- Support table structure queries: "Find sheets with tax calculations"
- Aggregate across multiple files: "Total sales by product category"

## Advanced Features

### Multi-Sheet Operations
```python
# Iterate through all sheets
for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    # Process each sheet
```

### Cell Styling
```python
from openpyxl.styles import Alignment, Border, Side

# Center align
ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

# Add borders
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
ws['A1'].border = thin_border
```

### Charts and Visualization
```python
from openpyxl.chart import BarChart, Reference

# Create chart
chart = BarChart()
data = Reference(ws, min_col=2, min_row=1, max_row=10)
cats = Reference(ws, min_col=1, min_row=2, max_row=10)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "E5")
```

### Performance Optimization
- Use `read_only=True` for large files
- Process data in chunks
- Avoid loading entire workbook when possible
- Use pandas for bulk operations

## Best Practices

### Data Integrity
- Validate input data before writing
- Use appropriate data types
- Implement error handling
- Create backup before modifications

### Performance
- Batch operations when possible
- Use efficient libraries (pandas for data, openpyxl for formatting)
- Close workbooks properly
- Monitor memory usage for large files

### Compatibility
- Save in Excel 2007+ format (.xlsx)
- Test with target Excel version
- Handle missing values appropriately
- Consider locale-specific formatting

## Error Handling

```python
try:
    wb = load_workbook('file.xlsx')
except FileNotFoundError:
    logger.error("File not found")
except InvalidFileException:
    logger.error("Invalid Excel file")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    if 'wb' in locals():
        wb.close()
```

## Testing

```python
import pytest

def test_excel_creation():
    wb = Workbook()
    ws = wb.active
    ws['A1'] = "Test"
    assert ws['A1'].value == "Test"
    
def test_formula_calculation():
    ws['A1'] = 10
    ws['B1'] = 20
    ws['C1'] = '=A1+B1'
    wb.save('test.xlsx')
    # Reopen to evaluate formula
    wb2 = load_workbook('test.xlsx', data_only=True)
    assert wb2.active['C1'].value == 30
```

## Resources

- **openpyxl**: https://openpyxl.readthedocs.io/
- **pandas**: https://pandas.pydata.org/docs/
- **xlsxwriter**: https://xlsxwriter.readthedocs.io/
- **Excel Formula Reference**: https://support.microsoft.com/en-us/excel

## Related Skills

- `python-testing-patterns`: Testing Excel operations
- `async-python-patterns`: Async file processing
- `data-validation`: Data quality checks
