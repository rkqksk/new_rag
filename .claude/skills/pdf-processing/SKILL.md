---
name: pdf-processing
description: PDF document parsing extraction OCR tesseract PyPDF2 pdfplumber form fill table extract 문서 추출 양식 테이블 추출 이미지 텍스트 인식 optical character recognition
---

# PDF Document Processing

## When to Use
- PDF 파일 처리, PDF processing
- 텍스트 추출, text extraction
- OCR 필요, OCR needed
- 테이블 추출, table extraction
- 양식 작성, form filling
- 문서 변환, document conversion
- 이미지 추출, image extraction

## Core Capabilities
1. **Text Extraction** - PyPDF2, pdfplumber, high accuracy
2. **OCR** - Tesseract for scanned PDFs, Korean support
3. **Table Extraction** - Tabula, Camelot, structured data
4. **Form Processing** - Detect and fill PDF forms
5. **Image Extraction** - Extract embedded images
6. **Conversion** - PDF to text, images, HTML

## Quick Actions

### Extract Text
```python
import pdfplumber

with pdfplumber.open('document.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

### OCR Scanned PDF
```python
# With Korean language pack
python scripts/ocr_pdf.py \
  --input scanned.pdf \
  --lang kor+eng \
  --output text/
```

### Extract Tables
```python
# Using pdfplumber
import pdfplumber

with pdfplumber.open('tables.pdf') as pdf:
    page = pdf.pages[0]
    tables = page.extract_tables()
    for table in tables:
        df = pd.DataFrame(table[1:], columns=table[0])
```

### Fill PDF Forms
```python
# Detect form fields
python scripts/extract_form_fields.py \
  --input form.pdf \
  --output fields.json

# Fill form
python scripts/fill_pdf_form.py \
  --input form.pdf \
  --data data.json \
  --output filled.pdf
```

### Convert to Images
```python
# Each page as image
python scripts/pdf_to_images.py \
  --input document.pdf \
  --output images/ \
  --format png \
  --dpi 300
```

## OCR Optimization

### Tesseract Settings
```python
# Korean + English
tesseract --list-langs  # Check installed
sudo apt-get install tesseract-ocr-kor

# Preprocessing
- Deskew images
- Denoise
- Enhance contrast
- Binarization
```

### Quality Improvements
- **High DPI**: 300+ for better accuracy
- **Preprocessing**: Gaussian blur, threshold
- **Language packs**: Install Korean (kor), English (eng)

## Integration
- **data-collection**: Parse crawled PDFs
- **rag-optimization**: Index PDF content
- **excel-processing**: Convert PDF tables to Excel
- **testing-suite**: Validate extraction accuracy

## Key Files
- `scripts/pdf_processor.py` - PDF utilities
- `src/parsers/pdf_parser.py` - Parsing logic

## Supported Operations
- **Read**: Text, images, metadata
- **Write**: Create PDFs from scratch
- **Modify**: Merge, split, rotate, watermark
- **Forms**: Detect fields, fill data
- **OCR**: Scanned documents to text
- **Tables**: Extract structured data
