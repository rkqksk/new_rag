"""
OCR Module for RAG Enterprise
Multi-modal document processing with PaddleOCR, EasyOCR, and Tesseract
"""
from .ocr_engine import MultiEngineOCR, OCRResult
from .image_preprocessor import ImagePreprocessor
from .pdf_extractor import PDFExtractor
from .excel_parser import ExcelParser
from .entity_recognizer import EntityRecognizer

__all__ = [
    'MultiEngineOCR',
    'OCRResult',
    'ImagePreprocessor',
    'PDFExtractor',
    'ExcelParser',
    'EntityRecognizer'
]
