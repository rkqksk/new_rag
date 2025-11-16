"""
OCR Module for RAG Enterprise
Multi-modal document processing with PaddleOCR, EasyOCR, and Tesseract
"""

from .entity_recognizer import EntityRecognizer
from .excel_parser import ExcelParser
from .image_preprocessor import ImagePreprocessor
from .ocr_engine import MultiEngineOCR, OCRResult
from .pdf_extractor import PDFExtractor

__all__ = [
    "MultiEngineOCR",
    "OCRResult",
    "ImagePreprocessor",
    "PDFExtractor",
    "ExcelParser",
    "EntityRecognizer",
]
