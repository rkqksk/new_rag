"""Unified Document Processor - Integration Layer"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from .entity_recognizer import EntityRecognizer
from .excel_parser import ExcelParser
from .image_preprocessor import ImagePreprocessor
from .ocr_engine import MultiEngineOCR
from .pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Unified document processing pipeline.

    Supports:
    - PDF files
    - Images (PNG, JPG, TIFF, BMP)
    - Excel files (XLSX, XLS)
    - CSV files
    - Excel screenshots (Image → OCR → Table)

    Features:
    - Auto-format detection
    - Multi-engine OCR with fallback
    - Entity extraction
    - RAG-ready output format
    """

    def __init__(
        self, use_gpu: bool = True, min_confidence: float = 0.75, enable_preprocessing: bool = True
    ):
        """
        Initialize document processor.

        Args:
            use_gpu: Enable GPU acceleration
            min_confidence: Minimum OCR confidence threshold
            enable_preprocessing: Enable image preprocessing
        """
        # Initialize components
        self.preprocessor = ImagePreprocessor() if enable_preprocessing else None

        self.ocr_engine = MultiEngineOCR(
            use_paddle=True,
            use_easy=True,
            use_tesseract=True,
            min_confidence=min_confidence,
            use_gpu=use_gpu,
        )

        self.pdf_extractor = PDFExtractor(
            ocr_engine=self.ocr_engine, preprocessor=self.preprocessor
        )

        self.excel_parser = ExcelParser(ocr_engine=self.ocr_engine, preprocessor=self.preprocessor)

        self.entity_recognizer = EntityRecognizer()

        logger.info("DocumentProcessor initialized")

    def process_file(self, file_path: str, extract_entities: bool = True) -> Dict[str, Any]:
        """
        Process any supported file type.

        Args:
            file_path: Path to file
            extract_entities: Extract product entities

        Returns:
            Processed result with text, entities, metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {"error": "File not found"}

        # Detect format
        format_type = self._detect_format(file_path)

        logger.info(f"Processing {format_type} file: {file_path.name}")

        # Route to appropriate processor
        if format_type == "pdf":
            return self._process_pdf(file_path, extract_entities)
        elif format_type == "image":
            return self._process_image(file_path, extract_entities)
        elif format_type == "excel":
            return self._process_excel(file_path, extract_entities)
        elif format_type == "csv":
            return self._process_csv(file_path, extract_entities)
        else:
            logger.error(f"Unsupported file format: {file_path.suffix}")
            return {"error": f"Unsupported format: {file_path.suffix}"}

    def _detect_format(self, file_path: Path) -> str:
        """Detect file format from extension"""
        ext = file_path.suffix.lower()

        if ext == ".pdf":
            return "pdf"
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return "image"
        elif ext in [".xlsx", ".xls", ".xlsm"]:
            return "excel"
        elif ext in [".csv", ".tsv"]:
            return "csv"
        else:
            return "unknown"

    def _process_pdf(self, file_path: Path, extract_entities: bool) -> Dict[str, Any]:
        """Process PDF file"""
        pages = self.pdf_extractor.extract_from_pdf(str(file_path))

        # Combine all page text
        full_text = "\n\n".join([page["text"] for page in pages])

        result = {
            "file_type": "pdf",
            "file_name": file_path.name,
            "pages": len(pages),
            "text": full_text,
            "page_details": pages,
        }

        # Extract entities from full text
        if extract_entities and full_text.strip():
            entities = self.entity_recognizer.extract_entities(full_text)
            result["entities"] = {k: v.__dict__ for k, v in entities.items()}
            result["product"] = self.entity_recognizer.to_product_dict(entities)

        return result

    def _process_image(self, file_path: Path, extract_entities: bool) -> Dict[str, Any]:
        """Process image file"""
        # Load image
        image = Image.open(file_path)

        # Preprocess
        if self.preprocessor:
            image = self.preprocessor.optimize_for_ocr(image)

        # Run OCR
        ocr_result = self.ocr_engine.extract_text(image)

        result = {
            "file_type": "image",
            "file_name": file_path.name,
            "text": ocr_result.full_text,
            "ocr_confidence": ocr_result.avg_confidence,
            "ocr_engine": ocr_result.engine,
            "processing_time_ms": ocr_result.processing_time_ms,
            "num_text_boxes": len(ocr_result.text_boxes),
        }

        # Extract entities
        if extract_entities and ocr_result.full_text.strip():
            entities = self.entity_recognizer.extract_from_ocr_result(ocr_result)
            result["entities"] = {k: v.__dict__ for k, v in entities.items()}
            result["product"] = self.entity_recognizer.to_product_dict(entities)

        return result

    def _process_excel(self, file_path: Path, extract_entities: bool) -> Dict[str, Any]:
        """Process Excel file"""
        records = self.excel_parser.parse_excel(str(file_path))

        result = {
            "file_type": "excel",
            "file_name": file_path.name,
            "num_rows": len(records),
            "records": records,
        }

        # If records look like products, extract entities from each
        if extract_entities and records:
            products = []
            for record in records:
                # Convert record to text for entity extraction
                record_text = "\n".join([f"{k}: {v}" for k, v in record.items()])
                entities = self.entity_recognizer.extract_entities(record_text)

                product = self.entity_recognizer.to_product_dict(entities)
                product["_original_record"] = record
                products.append(product)

            result["products"] = products

        return result

    def _process_csv(self, file_path: Path, extract_entities: bool) -> Dict[str, Any]:
        """Process CSV file"""
        records = self.excel_parser.parse_csv(str(file_path))

        result = {
            "file_type": "csv",
            "file_name": file_path.name,
            "num_rows": len(records),
            "records": records,
        }

        # Similar to Excel processing
        if extract_entities and records:
            products = []
            for record in records:
                record_text = "\n".join([f"{k}: {v}" for k, v in record.items()])
                entities = self.entity_recognizer.extract_entities(record_text)

                product = self.entity_recognizer.to_product_dict(entities)
                product["_original_record"] = record
                products.append(product)

            result["products"] = products

        return result

    def process_batch(
        self, file_paths: List[str], extract_entities: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple files.

        Args:
            file_paths: List of file paths
            extract_entities: Extract entities from each

        Returns:
            List of processing results
        """
        results = []

        for i, file_path in enumerate(file_paths):
            logger.info(f"Processing file {i+1}/{len(file_paths)}: {file_path}")
            result = self.process_file(file_path, extract_entities=extract_entities)
            results.append(result)

        return results

    def process_to_rag_format(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process file and convert to RAG-ready chunks.

        Args:
            file_path: Path to file

        Returns:
            List of chunks ready for RAG ingestion
        """
        result = self.process_file(file_path, extract_entities=True)

        if "error" in result:
            return []

        chunks = []

        # Create chunks based on file type
        if result["file_type"] == "pdf":
            # One chunk per page
            for page in result.get("page_details", []):
                if page["text"].strip():
                    chunk = {
                        "text": page["text"],
                        "metadata": {
                            "file_name": result["file_name"],
                            "page_number": page["page_number"],
                            "extraction_method": page["metadata"].get("extraction_method"),
                        },
                    }
                    chunks.append(chunk)

        elif result["file_type"] == "image":
            # Single chunk for image
            if result["text"].strip():
                chunk = {
                    "text": result["text"],
                    "metadata": {
                        "file_name": result["file_name"],
                        "ocr_confidence": result["ocr_confidence"],
                        "ocr_engine": result["ocr_engine"],
                    },
                }

                # Add product fields if extracted
                if "product" in result:
                    chunk["metadata"].update(result["product"])

                chunks.append(chunk)

        elif result["file_type"] in ["excel", "csv"]:
            # One chunk per product/record
            for product in result.get("products", []):
                # Create text representation
                text_parts = []
                for key, value in product.items():
                    if not key.startswith("_") and not key.endswith("_confidence"):
                        text_parts.append(f"{key}: {value}")

                if text_parts:
                    chunk = {
                        "text": "\n".join(text_parts),
                        "metadata": {"file_name": result["file_name"], **product},
                    }
                    chunks.append(chunk)

        logger.info(f"Generated {len(chunks)} RAG chunks from {result['file_name']}")
        return chunks
