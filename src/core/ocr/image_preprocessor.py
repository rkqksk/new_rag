"""Image Preprocessing for OCR Optimization"""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Advanced image preprocessing for OCR optimization.
    
    Features:
    - Deskew (angle correction)
    - Denoise (Gaussian blur)
    - Binarization (Otsu's method)
    - Contrast enhancement (CLAHE)
    - Border removal
    """
    
    def __init__(
        self,
        target_dpi: int = 300,
        enable_denoising: bool = True,
        enable_deskew: bool = True,
        enable_contrast: bool = True
    ):
        self.target_dpi = target_dpi
        self.enable_denoising = enable_denoising
        self.enable_deskew = enable_deskew
        self.enable_contrast = enable_contrast
    
    def optimize_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Multi-stage preprocessing pipeline.
        
        Args:
            image: PIL Image
            
        Returns:
            Optimized PIL Image
        """
        # Convert PIL to OpenCV format
        img_cv = self._pil_to_cv2(image)
        
        # 1. Resize to target DPI if needed
        img_cv = self._resize_to_dpi(img_cv)
        
        # 2. Deskew (angle correction)
        if self.enable_deskew:
            img_cv = self._deskew(img_cv)
        
        # 3. Denoise
        if self.enable_denoising:
            img_cv = self._denoise(img_cv)
        
        # 4. Contrast enhancement (CLAHE)
        if self.enable_contrast:
            img_cv = self._enhance_contrast(img_cv)
        
        # 5. Binarization (Otsu's method)
        img_cv = self._binarize(img_cv)
        
        # 6. Remove borders
        img_cv = self._remove_borders(img_cv)
        
        # Convert back to PIL
        return self._cv2_to_pil(img_cv)
    
    def _pil_to_cv2(self, image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    def _cv2_to_pil(self, image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL format"""
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    def _resize_to_dpi(self, img: np.ndarray, current_dpi: int = 72) -> np.ndarray:
        """Resize image to target DPI"""
        if current_dpi == self.target_dpi:
            return img
        
        scale = self.target_dpi / current_dpi
        width = int(img.shape[1] * scale)
        height = int(img.shape[0] * scale)
        
        return cv2.resize(img, (width, height), interpolation=cv2.INTER_CUBIC)
    
    def _deskew(self, img: np.ndarray) -> np.ndarray:
        """
        Detect and correct skew angle using Hough transform.
        
        Args:
            img: OpenCV image
            
        Returns:
            Deskewed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        if lines is None:
            return img
        
        # Calculate skew angle from detected lines
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            
            # Filter out nearly horizontal/vertical lines
            if abs(angle) < 45:
                angles.append(angle)
        
        if not angles:
            return img
        
        # Use median angle
        skew_angle = np.median(angles)
        
        # Only correct if angle is significant
        if abs(skew_angle) < 0.5:
            return img
        
        logger.info(f"Detected skew angle: {skew_angle:.2f}°")
        
        # Rotate image
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
        rotated = cv2.warpAffine(
            img, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    def _denoise(self, img: np.ndarray) -> np.ndarray:
        """Apply denoising filter"""
        return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    
    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Args:
            img: OpenCV image
            
        Returns:
            Contrast-enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        
        # Split channels
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_clahe = clahe.apply(l)
        
        # Merge channels
        lab_clahe = cv2.merge([l_clahe, a, b])
        
        # Convert back to BGR
        return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
    
    def _binarize(self, img: np.ndarray) -> np.ndarray:
        """
        Apply Otsu's binarization.
        
        Args:
            img: OpenCV image
            
        Returns:
            Binarized image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        # Convert back to BGR for consistency
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    def _remove_borders(self, img: np.ndarray) -> np.ndarray:
        """
        Remove borders/margins from image.
        
        Args:
            img: OpenCV image
            
        Returns:
            Cropped image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return img
        
        # Find bounding box of largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Add small margin (5% on each side)
        margin_x = int(w * 0.05)
        margin_y = int(h * 0.05)
        
        x = max(0, x - margin_x)
        y = max(0, y - margin_y)
        w = min(img.shape[1] - x, w + 2 * margin_x)
        h = min(img.shape[0] - y, h + 2 * margin_y)
        
        # Crop
        return img[y:y+h, x:x+w]
    
    def detect_orientation(self, image: Image.Image) -> float:
        """
        Detect orientation angle of image using Hough transform.
        
        Args:
            image: PIL Image
            
        Returns:
            Detected angle in degrees (-45 to 45)
        """
        img_cv = self._pil_to_cv2(image)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        if lines is None:
            return 0.0
        
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            if abs(angle) < 45:
                angles.append(angle)
        
        return float(np.median(angles)) if angles else 0.0
