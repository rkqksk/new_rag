# /xlsx - Excel Spreadsheet Processing

Process Excel files (.xlsx, .xls) with advanced data analysis, creation, and manipulation capabilities.

## Core Capabilities
- **Read**: Extract data, formulas, formatting from Excel files
- **Create**: Generate new Excel workbooks with charts and styles
- **Analyze**: Data analysis, statistics, pivot tables
- **Modify**: Update cells, formulas, add/remove sheets
- **Convert**: Excel to CSV, JSON, or other formats
- **Extract**: Images, charts, and embedded objects

## Usage Examples

### Basic Reading
```
/xlsx read sales_data.xlsx
# Reads all data from Excel file
```

### Data Analysis
```
/xlsx analyze report.xlsx --summary
# Analyzes data with statistics and trends
```

### Create Spreadsheet
```
/xlsx create output.xlsx --from data.json
# Creates Excel file from JSON data
```

### Extract Images
```
/xlsx extract-images product_list.xlsx
# Extracts all embedded images
```

### Compare with Database
```
/xlsx compare products.xlsx --db qdrant
# Compares Excel data with database
```

## Available Scripts
- `recalc.py` - Recalculate formulas
- Data validation and cleaning
- Chart generation
- Format preservation

## Aliases
- `/excel` - Same functionality
- `/sc:excel` - SuperClaude variant with database comparison

## File Locations
- Input: Any .xlsx or .xls file
- Output: Same directory or specified
- Images: Extracted to /images subdirectory