"""Multi-Engine OCR with Confidence-Based Fallback"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TextBox:
    """Single detected text box"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    language: Optional[str] = None


@dataclass
class OCRResult:
    """Complete OCR result with metadata"""
    text_boxes: List[TextBox]
    full_text: str
    avg_confidence: float
    engine: str  # "paddleocr", "easyocr", "tesseract"
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def text(self) -> str:
        """Alias for full_text"""
        return self.full_text


class MultiEngineOCR:
    """
    Orchestrate multiple OCR engines with confidence-based fallback.
    
    Engines (in order of priority):
    1. PaddleOCR (primary) - Best for Korean + English
    2. EasyOCR (fallback) - Better for artistic fonts
    3. Tesseract (last resort) - CPU-only fallback
    
    Features:
    - Automatic fallback if confidence < threshold
    - Result merging from multiple engines
    - Language detection
    - Performance tracking
    """
    
    def __init__(
        self,
        use_paddle: bool = True,
        use_easy: bool = True,
        use_tesseract: bool = True,
        min_confidence: float = 0.75,
        use_gpu: bool = True
    ):
        """
        Initialize OCR engines.
        
        Args:
            use_paddle: Enable PaddleOCR
            use_easy: Enable EasyOCR
            use_tesseract: Enable Tesseract
            min_confidence: Minimum confidence threshold for accepting results
            use_gpu: Use GPU acceleration if available
        """
        self.min_confidence = min_confidence
        self.use_gpu = use_gpu
        
        # Initialize engines
        self.paddle_ocr = None
        self.easy_ocr = None
        self.tesseract_available = False
        
        if use_paddle:
            self.paddle_ocr = self._init_paddle()
        
        if use_easy:
            self.easy_ocr = self._init_easy()
        
        if use_tesseract:
            self.tesseract_available = self._check_tesseract()
        
        logger.info(f"MultiEngineOCR initialized: PaddleOCR={use_paddle}, EasyOCR={use_easy}, Tesseract={use_tesseract}")
    
    def _init_paddle(self):
        """Initialize PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            
            return PaddleOCR(
                lang='korean',
                use_gpu=self.use_gpu,
                show_log=False,
                use_angle_cls=True,  # Enable angle classification
                det_db_thresh=0.3,   # Detection threshold
                det_db_box_thresh=0.5  # Box threshold
            )
        except ImportError:
            logger.warning("PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            return None
    
    def _init_easy(self):
        """Initialize EasyOCR"""
        try:
            import easyocr
            
            return easyocr.Reader(
                ['ko', 'en'],
                gpu=self.use_gpu,
                verbose=False
            )
        except ImportError:
            logger.warning("EasyOCR not installed. Install with: pip install easyocr")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            return None
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except:
            logger.warning("Tesseract not available. Install with: apt-get install tesseract-ocr tesseract-ocr-kor")
            return False
    
    def extract_text(
        self,
        image: Image.Image,
        enable_fallback: bool = True
    ) -> OCRResult:
        """
        Extract text from image with automatic fallback.
        
        Args:
            image: PIL Image
            enable_fallback: Enable fallback to other engines if confidence is low
            
        Returns:
            OCRResult with extracted text and metadata
        """
        import time
        
        # Try PaddleOCR first (fastest, most accurate for Korean)
        if self.paddle_ocr:
            start_time = time.time()
            result = self._extract_with_paddle(image)
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            if result.avg_confidence >= self.min_confidence or not enable_fallback:
                logger.info(f"PaddleOCR success: confidence={result.avg_confidence:.2f}")
                return result
            
            logger.warning(f"PaddleOCR low confidence ({result.avg_confidence:.2f}), trying fallback...")
        
        # Fallback to EasyOCR
        if self.easy_ocr and enable_fallback:
            start_time = time.time()
            result = self._extract_with_easy(image)
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            if result.avg_confidence >= self.min_confidence:
                logger.info(f"EasyOCR success: confidence={result.avg_confidence:.2f}")
                return result
            
            logger.warning(f"EasyOCR low confidence ({result.avg_confidence:.2f}), trying Tesseract...")
        
        # Last resort: Tesseract
        if self.tesseract_available and enable_fallback:
            start_time = time.time()
            result = self._extract_with_tesseract(image)
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Tesseract result: confidence={result.avg_confidence:.2f}")
            return result
        
        # If all engines failed or disabled, return empty result
        logger.error("All OCR engines failed or disabled")
        return OCRResult(
            text_boxes=[],
            full_text="",
            avg_confidence=0.0,
            engine="none",
            processing_time_ms=0.0
        )
    
    def _extract_with_paddle(self, image: Image.Image) -> OCRResult:
        """Extract text using PaddleOCR"""
        if not self.paddle_ocr:
            return OCRResult([], "", 0.0, "paddleocr", 0.0)
        
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Run OCR
        result = self.paddle_ocr.ocr(img_array, cls=True)
        
        if not result or not result[0]:
            return OCRResult([], "", 0.0, "paddleocr", 0.0)
        
        # Parse results
        text_boxes = []
        full_text_parts = []
        confidences = []
        
        for line in result[0]:
            bbox = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text_info = line[1]  # (text, confidence)
            
            text = text_info[0]
            confidence = text_info[1]
            
            # Convert bbox to (x1, y1, x2, y2)
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            bbox_simple = (
                int(min(x_coords)),
                int(min(y_coords)),
                int(max(x_coords)),
                int(max(y_coords))
            )
            
            text_boxes.append(TextBox(
                text=text,
                confidence=confidence,
                bbox=bbox_simple,
                language='ko' if self._is_korean(text) else 'en'
            ))
            
            full_text_parts.append(text)
            confidences.append(confidence)
        
        avg_confidence = np.mean(confidences) if confidences else 0.0
        full_text = '\n'.join(full_text_parts)
        
        return OCRResult(
            text_boxes=text_boxes,
            full_text=full_text,
            avg_confidence=float(avg_confidence),
            engine="paddleocr",
            processing_time_ms=0.0,
            metadata={'num_lines': len(text_boxes)}
        )
    
    def _extract_with_easy(self, image: Image.Image) -> OCRResult:
        """Extract text using EasyOCR"""
        if not self.easy_ocr:
            return OCRResult([], "", 0.0, "easyocr", 0.0)
        
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Run OCR
        result = self.easy_ocr.readtext(img_array)
        
        if not result:
            return OCRResult([], "", 0.0, "easyocr", 0.0)
        
        # Parse results
        text_boxes = []
        full_text_parts = []
        confidences = []
        
        for detection in result:
            bbox = detection[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = detection[1]
            confidence = detection[2]
            
            # Convert bbox to (x1, y1, x2, y2)
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            bbox_simple = (
                int(min(x_coords)),
                int(min(y_coords)),
                int(max(x_coords)),
                int(max(y_coords))
            )
            
            text_boxes.append(TextBox(
                text=text,
                confidence=confidence,
                bbox=bbox_simple,
                language='ko' if self._is_korean(text) else 'en'
            ))
            
            full_text_parts.append(text)
            confidences.append(confidence)
        
        avg_confidence = np.mean(confidences) if confidences else 0.0
        full_text = '\n'.join(full_text_parts)
        
        return OCRResult(
            text_boxes=text_boxes,
            full_text=full_text,
            avg_confidence=float(avg_confidence),
            engine="easyocr",
            processing_time_ms=0.0,
            metadata={'num_detections': len(text_boxes)}
        )
    
    def _extract_with_tesseract(self, image: Image.Image) -> OCRResult:
        """Extract text using Tesseract"""
        if not self.tesseract_available:
            return OCRResult([], "", 0.0, "tesseract", 0.0)
        
        try:
            import pytesseract
            
            # Configuration for Korean + English
            custom_config = r'--oem 3 --psm 6 -l kor+eng'
            
            # Get detailed data
            data = pytesseract.image_to_data(
                image,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Parse results
            text_boxes = []
            full_text_parts = []
            confidences = []
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                conf = int(data['conf'][i])
                text = data['text'][i]
                
                # Skip empty text and low confidence
                if conf < 0 or not text.strip():
                    continue
                
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                
                text_boxes.append(TextBox(
                    text=text,
                    confidence=conf / 100.0,  # Convert to 0-1
                    bbox=(x, y, x + w, y + h),
                    language='ko' if self._is_korean(text) else 'en'
                ))
                
                full_text_parts.append(text)
                confidences.append(conf / 100.0)
            
            avg_confidence = np.mean(confidences) if confidences else 0.0
            full_text = ' '.join(full_text_parts)  # Tesseract uses spaces
            
            return OCRResult(
                text_boxes=text_boxes,
                full_text=full_text,
                avg_confidence=float(avg_confidence),
                engine="tesseract",
                processing_time_ms=0.0,
                metadata={'num_words': len(text_boxes)}
            )
        
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return OCRResult([], "", 0.0, "tesseract", 0.0)
    
    def _is_korean(self, text: str) -> bool:
        """Check if text contains Korean characters"""
        for char in text:
            if '\uAC00' <= char <= '\uD7A3':  # Hangul syllables
                return True
        return False
    
    def batch_extract(
        self,
        images: List[Image.Image],
        enable_fallback: bool = True
    ) -> List[OCRResult]:
        """
        Extract text from multiple images.
        
        Args:
            images: List of PIL Images
            enable_fallback: Enable fallback for each image
            
        Returns:
            List of OCRResults
        """
        results = []
        for i, image in enumerate(images):
            logger.info(f"Processing image {i+1}/{len(images)}")
            result = self.extract_text(image, enable_fallback=enable_fallback)
            results.append(result)
        
        return results
