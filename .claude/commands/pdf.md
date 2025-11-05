# /pdf - PDF Document Processing

Process PDF documents with advanced capabilities including text extraction, form filling, creation, and manipulation.

## Core Capabilities
- **Extract**: Text, images, tables, and metadata from PDFs
- **Fill Forms**: Detect and fill PDF form fields programmatically
- **Create**: Generate new PDF documents from scratch
- **Manipulate**: Merge, split, rotate, watermark PDFs
- **Convert**: PDF to images, text, HTML, or other formats
- **OCR**: Extract text from scanned PDFs
- **Analyze**: Document structure, form fields, annotations

## Usage Examples

### Basic Text Extraction
```
/pdf extract document.pdf
# Extracts all text content from the PDF
```

### Form Processing
```
/pdf fill application.pdf --data form_data.json
# Fills PDF form with provided data
```

### Merge Multiple PDFs
```
/pdf merge doc1.pdf doc2.pdf doc3.pdf --output merged.pdf
# Combines multiple PDFs into one
```

### Convert to Images
```
/pdf convert report.pdf --to images --output folder/
# Converts each page to an image
```

## Available Scripts
- `extract_form_field_info.py` - Analyze form structure
- `fill_fillable_fields.py` - Fill form fields
- `convert_pdf_to_images.py` - Convert to images
- `check_bounding_boxes.py` - Validate text regions
- `fill_pdf_form_with_annotations.py` - Advanced form filling

## Implementation
When invoked, I will:
1. Identify the PDF operation needed
2. Use appropriate Python scripts from the skill
3. Process the PDF efficiently
4. Return results or create output files
5. Provide summary of operations performed

## File Locations
- Input PDFs: Any accessible path
- Output: Same directory or specified location
- Temp files: Cleaned up automatically