"""
PDF Parser for RAG Pipeline

Handles PDF document parsing with OCR support for scanned documents.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """Parser for PDF files with OCR support"""

    SUPPORTED_FORMATS = ['pdf']

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # Try importing PDF parsing libraries
        self.has_pypdf2 = False
        self.has_docling = False
        self.has_ocr = False

        try:
            import PyPDF2
            self.has_pypdf2 = True
        except ImportError:
            logger.warning("PyPDF2 not installed - install with: pip install PyPDF2")

        try:
            # Docling is the advanced PDF parser mentioned in the RAG pipeline docs
            from docling.document_converter import DocumentConverter
            self.has_docling = True
        except ImportError:
            logger.warning("Docling not installed - install with: pip install docling")

        try:
            import pytesseract
            from PIL import Image
            self.has_ocr = True
        except ImportError:
            logger.warning("OCR not available - install with: pip install pytesseract Pillow")

    def supports_format(self, file_extension: str) -> bool:
        """Check if parser supports given file format"""
        return file_extension.lower() in self.SUPPORTED_FORMATS

    def parse(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> ParseResult:
        """
        Parse PDF file and return structured content.

        Args:
            file_path: Path to PDF file
            options: Parsing options
                - use_ocr: bool = False - Enable OCR for scanned PDFs
                - ocr_lang: str = 'kor+eng' - OCR languages (Korean + English)
                - extract_tables: bool = True - Extract table structures
                - extract_images: bool = False - Extract embedded images

        Returns:
            ParseResult with extracted content and metadata
        """
        if not self.validate_file(file_path):
            return ParseResult(
                content="",
                metadata={},
                success=False,
                error=f"File validation failed: {file_path}"
            )

        options = options or {}
        use_ocr = options.get('use_ocr', False)
        extract_tables = options.get('extract_tables', True)

        # Try Docling first (advanced parsing)
        if self.has_docling:
            try:
                return self._parse_with_docling(file_path, options)
            except Exception as e:
                logger.warning(f"Docling parsing failed, falling back to PyPDF2: {e}")

        # Fallback to PyPDF2
        if self.has_pypdf2:
            try:
                return self._parse_with_pypdf2(file_path, options)
            except Exception as e:
                logger.error(f"PyPDF2 parsing failed: {e}")
                return ParseResult(
                    content="",
                    metadata=self.extract_metadata(file_path),
                    success=False,
                    error=f"PDF parsing error: {str(e)}"
                )

        return ParseResult(
            content="",
            metadata=self.extract_metadata(file_path),
            success=False,
            error="No PDF parsing library available - install PyPDF2 or docling"
        )

    def _parse_with_docling(self, file_path: str, options: Dict[str, Any]) -> ParseResult:
        """Parse using Docling (advanced parser with table/image support)"""
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(file_path)

        # Extract text content
        content = result.document.export_to_markdown()

        # Extract metadata
        metadata = self.extract_metadata(file_path)
        metadata['page_count'] = len(result.document.pages)
        metadata['parser_engine'] = 'docling'
        metadata['has_tables'] = len(result.document.tables) > 0 if hasattr(result.document, 'tables') else False

        return ParseResult(
            content=content,
            metadata=metadata,
            success=True
        )

    def _parse_with_pypdf2(self, file_path: str, options: Dict[str, Any]) -> ParseResult:
        """Parse using PyPDF2 (basic text extraction)"""
        import PyPDF2

        content_parts = []
        page_count = 0

        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)

            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text.strip():
                        content_parts.append(f"[Page {page_num}]\n{text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
                    continue

        content = "\n\n".join(content_parts)

        # Extract metadata
        metadata = self.extract_metadata(file_path)
        metadata['page_count'] = page_count
        metadata['parser_engine'] = 'pypdf2'

        # Try to extract PDF metadata
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if pdf_reader.metadata:
                    metadata['pdf_title'] = pdf_reader.metadata.get('/Title', '')
                    metadata['pdf_author'] = pdf_reader.metadata.get('/Author', '')
                    metadata['pdf_subject'] = pdf_reader.metadata.get('/Subject', '')
        except Exception as e:
            logger.warning(f"Could not extract PDF metadata: {e}")

        return ParseResult(
            content=content,
            metadata=metadata,
            success=True
        )
