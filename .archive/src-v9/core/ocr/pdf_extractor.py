"""PDF Extraction Pipeline"""

import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extract text and images from PDF files.

    Features:
    - Convert PDF pages to images
    - Extract embedded text (if available)
    - OCR on images
    - Page-by-page processing
    """

    def __init__(self, ocr_engine=None, preprocessor=None):
        """
        Initialize PDF extractor.

        Args:
            ocr_engine: OCR engine instance (MultiEngineOCR)
            preprocessor: Image preprocessor instance
        """
        self.ocr_engine = ocr_engine
        self.preprocessor = preprocessor

    def extract_from_pdf(
        self, pdf_path: str, use_ocr: bool = True, dpi: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Extract content from PDF.

        Args:
            pdf_path: Path to PDF file
            use_ocr: Use OCR for image pages
            dpi: DPI for converting PDF to images

        Returns:
            List of page results with text and metadata
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install PyMuPDF")
            return []

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return []

        doc = fitz.open(str(pdf_path))
        results = []

        for page_num in range(len(doc)):
            logger.info(f"Processing page {page_num + 1}/{len(doc)}")

            page = doc[page_num]
            page_result = {"page_number": page_num + 1, "text": "", "images": [], "metadata": {}}

            # Try to extract embedded text first
            text = page.get_text()

            if text.strip():
                # Has embedded text
                page_result["text"] = text
                page_result["metadata"]["extraction_method"] = "embedded_text"
                logger.info(f"Page {page_num + 1}: Extracted embedded text ({len(text)} chars)")

            elif use_ocr and self.ocr_engine:
                # No embedded text, use OCR
                # Convert page to image
                pix = page.get_pixmap(dpi=dpi)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))

                # Preprocess if available
                if self.preprocessor:
                    image = self.preprocessor.optimize_for_ocr(image)

                # Run OCR
                ocr_result = self.ocr_engine.extract_text(image)
                page_result["text"] = ocr_result.full_text
                page_result["metadata"]["extraction_method"] = "ocr"
                page_result["metadata"]["ocr_engine"] = ocr_result.engine
                page_result["metadata"]["ocr_confidence"] = ocr_result.avg_confidence

                logger.info(
                    f"Page {page_num + 1}: OCR extracted {len(ocr_result.full_text)} chars (confidence: {ocr_result.avg_confidence:.2f})"
                )

            # Extract embedded images
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                page_result["images"].append(
                    {
                        "index": img_index,
                        "width": base_image["width"],
                        "height": base_image["height"],
                        "ext": base_image["ext"],
                    }
                )

            results.append(page_result)

        doc.close()

        logger.info(f"PDF extraction complete: {len(results)} pages processed")
        return results

    def extract_text_only(self, pdf_path: str) -> str:
        """
        Extract all text from PDF (simple version).

        Args:
            pdf_path: Path to PDF file

        Returns:
            Combined text from all pages
        """
        results = self.extract_from_pdf(pdf_path, use_ocr=True)
        return "\n\n".join([page["text"] for page in results if page["text"]])
