"""
OCR Integration for Multi-Modal RAG Pipeline
Processes PDF/images with OCR and integrates with embedding service
"""

import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """OCR extraction result"""
    text: str
    confidence: float
    metadata: Dict[str, Any]
    source_file: str
    page_number: Optional[int] = None
    bounding_boxes: Optional[List[Dict]] = None


class OCRProcessor:
    """
    OCR Processor using PaddleOCR

    Supports:
    - PDF files (multi-page)
    - Image files (JPG, PNG, etc.)
    - Korean text recognition
    - Batch processing
    """

    def __init__(
        self,
        lang: str = 'korean',
        use_gpu: bool = True,
        enable_layout_analysis: bool = False
    ):
        """
        Initialize OCR processor

        Args:
            lang: OCR language ('korean', 'en', 'ch', etc.)
            use_gpu: Use GPU acceleration if available
            enable_layout_analysis: Enable layout detection (tables, columns)
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self.enable_layout_analysis = enable_layout_analysis
        self.ocr_engine = None

        # Initialize OCR engine
        self._init_ocr_engine()

    def _init_ocr_engine(self):
        """Initialize PaddleOCR engine"""
        try:
            from paddleocr import PaddleOCR

            self.ocr_engine = PaddleOCR(
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False
            )
            logger.info(f"✅ PaddleOCR initialized (lang={self.lang}, gpu={self.use_gpu})")

        except ImportError:
            logger.warning("PaddleOCR not installed. OCR functionality disabled.")
            logger.warning("Install with: pip install paddlepaddle paddleocr")
            self.ocr_engine = None

        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.ocr_engine = None

    def is_available(self) -> bool:
        """Check if OCR engine is available"""
        return self.ocr_engine is not None

    def process_image(
        self,
        image_path: Union[str, Path],
        min_confidence: float = 0.5
    ) -> OCRResult:
        """
        Process single image with OCR

        Args:
            image_path: Path to image file
            min_confidence: Minimum confidence threshold

        Returns:
            OCRResult with extracted text and metadata
        """
        if not self.is_available():
            raise RuntimeError("OCR engine not available. Install paddleocr first.")

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Run OCR
        result = self.ocr_engine.ocr(str(image_path), cls=True)

        # Parse results
        extracted_text = []
        bounding_boxes = []
        total_confidence = 0.0
        count = 0

        if result and result[0]:
            for line in result[0]:
                bbox, (text, confidence) = line

                if confidence >= min_confidence:
                    extracted_text.append(text)
                    bounding_boxes.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
                    total_confidence += confidence
                    count += 1

        # Calculate average confidence
        avg_confidence = total_confidence / count if count > 0 else 0.0

        return OCRResult(
            text="\n".join(extracted_text),
            confidence=avg_confidence,
            metadata={
                'line_count': len(extracted_text),
                'total_detections': count,
                'language': self.lang
            },
            source_file=str(image_path),
            bounding_boxes=bounding_boxes
        )

    def process_pdf(
        self,
        pdf_path: Union[str, Path],
        min_confidence: float = 0.5,
        max_pages: Optional[int] = None
    ) -> List[OCRResult]:
        """
        Process PDF with OCR (converts to images first)

        Args:
            pdf_path: Path to PDF file
            min_confidence: Minimum confidence threshold
            max_pages: Maximum pages to process (None = all)

        Returns:
            List of OCRResult (one per page)
        """
        if not self.is_available():
            raise RuntimeError("OCR engine not available")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Convert PDF to images
        page_images = self._pdf_to_images(pdf_path, max_pages)

        # Process each page
        results = []
        for page_num, image_path in enumerate(page_images, start=1):
            try:
                result = self.process_image(image_path, min_confidence)
                result.page_number = page_num
                results.append(result)

                logger.info(f"Processed page {page_num}: {len(result.text)} chars")

            except Exception as e:
                logger.error(f"Failed to process page {page_num}: {e}")
                continue

        return results

    def _pdf_to_images(
        self,
        pdf_path: Path,
        max_pages: Optional[int] = None
    ) -> List[Path]:
        """
        Convert PDF to images

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to convert

        Returns:
            List of image file paths
        """
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError("pdf2image not installed. Install with: pip install pdf2image")

        # Convert PDF to images
        images = convert_from_path(str(pdf_path))

        if max_pages:
            images = images[:max_pages]

        # Save images to temp directory
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())

        image_paths = []
        for i, image in enumerate(images, start=1):
            image_path = temp_dir / f"page_{i}.jpg"
            image.save(str(image_path), 'JPEG')
            image_paths.append(image_path)

        return image_paths

    def batch_process(
        self,
        file_paths: List[Union[str, Path]],
        min_confidence: float = 0.5
    ) -> List[OCRResult]:
        """
        Batch process multiple files

        Args:
            file_paths: List of file paths (images or PDFs)
            min_confidence: Minimum confidence threshold

        Returns:
            List of OCRResult objects
        """
        results = []

        for file_path in file_paths:
            file_path = Path(file_path)

            try:
                if file_path.suffix.lower() == '.pdf':
                    # Process PDF
                    pdf_results = self.process_pdf(file_path, min_confidence)
                    results.extend(pdf_results)
                else:
                    # Process image
                    result = self.process_image(file_path, min_confidence)
                    results.append(result)

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue

        return results


class OCRMultiModalIntegration:
    """
    Integration layer between OCR and Multi-Modal Embedding Service

    Workflow:
    1. OCR extracts text from PDF/image
    2. Generate text embedding
    3. Generate image embedding (from original image)
    4. Combine into multi-modal representation
    """

    def __init__(
        self,
        ocr_processor: OCRProcessor,
        embedding_service: Any,  # MultiModalEmbeddingService
        cache_embeddings: bool = True
    ):
        """
        Initialize OCR multi-modal integration

        Args:
            ocr_processor: OCR processor instance
            embedding_service: MultiModalEmbeddingService instance
            cache_embeddings: Enable embedding caching
        """
        self.ocr = ocr_processor
        self.embedder = embedding_service
        self.cache_embeddings = cache_embeddings
        self._cache = {} if cache_embeddings else None

    def process_document(
        self,
        file_path: Union[str, Path],
        product_id: Optional[str] = None,
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Process document end-to-end: OCR → Embeddings

        Args:
            file_path: Path to PDF or image
            product_id: Optional product ID
            extract_metadata: Extract additional metadata

        Returns:
            Dictionary with text, embeddings, and metadata
        """
        file_path = Path(file_path)

        # Check cache
        cache_key = str(file_path)
        if self.cache_embeddings and cache_key in self._cache:
            logger.debug(f"Using cached embeddings for {file_path.name}")
            return self._cache[cache_key]

        # Step 1: OCR extraction
        logger.info(f"Processing: {file_path.name}")

        if file_path.suffix.lower() == '.pdf':
            ocr_results = self.ocr.process_pdf(file_path)
            # Combine all pages
            combined_text = "\n\n".join([r.text for r in ocr_results])
            avg_confidence = sum([r.confidence for r in ocr_results]) / len(ocr_results)
        else:
            ocr_result = self.ocr.process_image(file_path)
            combined_text = ocr_result.text
            avg_confidence = ocr_result.confidence

        logger.info(f"✅ OCR extracted {len(combined_text)} characters")

        # Step 2: Generate embeddings
        embeddings = {}

        # Text embedding from OCR text
        if combined_text.strip():
            text_emb = self.embedder.embed_text(combined_text)
            embeddings['text'] = text_emb
            logger.info(f"✅ Generated text embedding ({len(text_emb)} dim)")

        # Image embedding from original file
        if self.embedder.is_available('image'):
            try:
                image_emb = self.embedder.embed_image(file_path)
                embeddings['image'] = image_emb
                logger.info(f"✅ Generated image embedding ({len(image_emb)} dim)")
            except Exception as e:
                logger.warning(f"Failed to generate image embedding: {e}")

        # Step 3: Build result
        result = {
            'product_id': product_id or file_path.stem,
            'source_file': str(file_path),
            'ocr_text': combined_text,
            'ocr_confidence': avg_confidence,
            'embeddings': embeddings,
            'metadata': {
                'filename': file_path.name,
                'file_type': file_path.suffix,
                'character_count': len(combined_text),
                'has_text_embedding': 'text' in embeddings,
                'has_image_embedding': 'image' in embeddings
            }
        }

        # Extract additional metadata if requested
        if extract_metadata:
            result['metadata'].update(
                self._extract_product_metadata(combined_text)
            )

        # Cache result
        if self.cache_embeddings:
            self._cache[cache_key] = result

        return result

    def process_batch(
        self,
        file_paths: List[Union[str, Path]],
        product_ids: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch

        Args:
            file_paths: List of file paths
            product_ids: Optional list of product IDs
            show_progress: Show progress bar

        Returns:
            List of processed documents
        """
        results = []

        if product_ids is None:
            product_ids = [None] * len(file_paths)

        # Progress tracking
        iterator = zip(file_paths, product_ids)
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(iterator, total=len(file_paths), desc="Processing documents")
            except ImportError:
                pass

        # Process each document
        for file_path, product_id in iterator:
            try:
                result = self.process_document(file_path, product_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue

        return results

    def _extract_product_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract product metadata from OCR text

        Uses regex patterns to extract:
        - Product code
        - Capacity
        - Material
        - MOQ
        - Price

        Args:
            text: OCR extracted text

        Returns:
            Dictionary of extracted metadata
        """
        import re

        metadata = {}

        # Product code patterns (e.g., PET-100, Bottle-200)
        code_pattern = r'[A-Z]{2,}-\d{2,}'
        codes = re.findall(code_pattern, text)
        if codes:
            metadata['product_code'] = codes[0]

        # Capacity patterns (e.g., 100ml, 200cc)
        capacity_pattern = r'(\d+)\s*(ml|cc|L|g|kg)'
        capacities = re.findall(capacity_pattern, text, re.IGNORECASE)
        if capacities:
            metadata['capacity'] = f"{capacities[0][0]}{capacities[0][1]}"

        # Material patterns
        materials = ['PET', 'HDPE', 'PP', 'PE', 'Glass', 'Aluminum']
        for material in materials:
            if material.lower() in text.lower():
                metadata['material'] = material
                break

        # MOQ pattern (e.g., MOQ: 5000, 최소주문: 1000)
        moq_pattern = r'(?:MOQ|최소주문|최소 주문)[\s:]*(\d+)'
        moq_match = re.search(moq_pattern, text, re.IGNORECASE)
        if moq_match:
            metadata['moq'] = int(moq_match.group(1))

        # Price pattern (e.g., 100원, ₩200, $1.50)
        price_pattern = r'(?:₩|원|$)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        price_match = re.search(price_pattern, text)
        if price_match:
            metadata['price'] = price_match.group(1)

        return metadata

    def clear_cache(self):
        """Clear embedding cache"""
        if self._cache:
            self._cache.clear()
            logger.info("Cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        if not self.cache_embeddings:
            return {"enabled": False}

        return {
            "enabled": True,
            "entries": len(self._cache),
            "size_mb": sum(
                len(str(v)) for v in self._cache.values()
            ) / (1024 * 1024)
        }
