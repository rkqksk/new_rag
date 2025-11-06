"""
Contour Extraction Service
Extract product contours using OpenCV
"""

import logging
from typing import List, Tuple, Optional, Union
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class ContourExtractor:
    """
    Extract and process contours from images

    Features:
    - Edge detection (Canny, Sobel)
    - Contour extraction
    - Contour filtering and cleaning
    - Hierarchy analysis
    """

    def __init__(
        self,
        canny_low: int = 50,
        canny_high: int = 150,
        min_contour_area: int = 100,
        approx_epsilon: float = 0.01
    ):
        """
        Initialize contour extractor

        Args:
            canny_low: Canny low threshold
            canny_high: Canny high threshold
            min_contour_area: Minimum contour area to keep
            approx_epsilon: Epsilon for contour approximation
        """
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.min_contour_area = min_contour_area
        self.approx_epsilon = approx_epsilon

        # Check OpenCV availability
        try:
            import cv2
            self.cv2 = cv2
            self.available = True
            logger.info("✅ OpenCV initialized for contour extraction")
        except ImportError:
            logger.warning("OpenCV not installed. Install with: pip install opencv-python")
            self.available = False
            self.cv2 = None

    def is_available(self) -> bool:
        """Check if contour extraction is available"""
        return self.available

    def detect_edges(
        self,
        image: np.ndarray,
        method: str = 'canny'
    ) -> np.ndarray:
        """
        Detect edges in image

        Args:
            image: Input image (grayscale or RGB)
            method: Edge detection method ('canny', 'sobel')

        Returns:
            Edge map (binary image)
        """
        if not self.available:
            raise RuntimeError("OpenCV not available")

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = self.cv2.cvtColor(image, self.cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Apply Gaussian blur to reduce noise
        blurred = self.cv2.GaussianBlur(gray, (5, 5), 0)

        if method == 'canny':
            edges = self.cv2.Canny(blurred, self.canny_low, self.canny_high)

        elif method == 'sobel':
            # Sobel edge detection
            sobelx = self.cv2.Sobel(blurred, self.cv2.CV_64F, 1, 0, ksize=3)
            sobely = self.cv2.Sobel(blurred, self.cv2.CV_64F, 0, 1, ksize=3)
            edges = np.sqrt(sobelx**2 + sobely**2)
            edges = np.uint8(edges / edges.max() * 255)

        else:
            raise ValueError(f"Unknown method: {method}")

        return edges

    def extract_contours(
        self,
        image: np.ndarray,
        mode: str = 'external'
    ) -> List[np.ndarray]:
        """
        Extract contours from image

        Args:
            image: Input image or edge map
            mode: Contour retrieval mode ('external', 'tree', 'list')

        Returns:
            List of contours (each contour is Nx2 array)
        """
        if not self.available:
            raise RuntimeError("OpenCV not available")

        # If input is not binary, detect edges first
        if len(image.shape) == 3 or image.max() > 1:
            edges = self.detect_edges(image)
        else:
            edges = image

        # Contour retrieval mode
        if mode == 'external':
            retr_mode = self.cv2.RETR_EXTERNAL
        elif mode == 'tree':
            retr_mode = self.cv2.RETR_TREE
        elif mode == 'list':
            retr_mode = self.cv2.RETR_LIST
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # Find contours
        contours, hierarchy = self.cv2.findContours(
            edges,
            retr_mode,
            self.cv2.CHAIN_APPROX_SIMPLE
        )

        return list(contours)

    def filter_contours(
        self,
        contours: List[np.ndarray],
        min_area: Optional[int] = None,
        max_area: Optional[int] = None,
        min_perimeter: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        Filter contours by criteria

        Args:
            contours: List of contours
            min_area: Minimum contour area
            max_area: Maximum contour area
            min_perimeter: Minimum contour perimeter

        Returns:
            Filtered contours
        """
        if not self.available:
            raise RuntimeError("OpenCV not available")

        filtered = []

        min_area = min_area or self.min_contour_area

        for contour in contours:
            area = self.cv2.contourArea(contour)
            perimeter = self.cv2.arcLength(contour, True)

            # Check criteria
            if min_area and area < min_area:
                continue
            if max_area and area > max_area:
                continue
            if min_perimeter and perimeter < min_perimeter:
                continue

            filtered.append(contour)

        return filtered

    def approximate_contour(
        self,
        contour: np.ndarray,
        epsilon: Optional[float] = None
    ) -> np.ndarray:
        """
        Approximate contour to reduce points

        Args:
            contour: Input contour
            epsilon: Approximation epsilon (fraction of perimeter)

        Returns:
            Approximated contour
        """
        if not self.available:
            raise RuntimeError("OpenCV not available")

        epsilon = epsilon or self.approx_epsilon
        perimeter = self.cv2.arcLength(contour, True)
        approx = self.cv2.approxPolyDP(
            contour,
            epsilon * perimeter,
            True
        )

        return approx

    def get_largest_contour(
        self,
        contours: List[np.ndarray]
    ) -> Optional[np.ndarray]:
        """
        Get largest contour by area

        Args:
            contours: List of contours

        Returns:
            Largest contour or None
        """
        if not contours:
            return None

        if not self.available:
            raise RuntimeError("OpenCV not available")

        largest = max(contours, key=lambda c: self.cv2.contourArea(c))
        return largest

    def get_contour_properties(
        self,
        contour: np.ndarray
    ) -> dict:
        """
        Calculate contour properties

        Args:
            contour: Input contour

        Returns:
            Dictionary of properties
        """
        if not self.available:
            raise RuntimeError("OpenCV not available")

        # Basic properties
        area = self.cv2.contourArea(contour)
        perimeter = self.cv2.arcLength(contour, True)

        # Bounding rectangle
        x, y, w, h = self.cv2.boundingRect(contour)

        # Moments
        M = self.cv2.moments(contour)

        # Centroid
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
        else:
            cx, cy = 0, 0

        # Aspect ratio
        aspect_ratio = float(w) / h if h != 0 else 0

        # Extent (ratio of contour area to bounding box area)
        rect_area = w * h
        extent = float(area) / rect_area if rect_area != 0 else 0

        # Solidity (ratio of contour area to convex hull area)
        hull = self.cv2.convexHull(contour)
        hull_area = self.cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area != 0 else 0

        return {
            'area': float(area),
            'perimeter': float(perimeter),
            'centroid': (int(cx), int(cy)),
            'bounding_box': (int(x), int(y), int(w), int(h)),
            'aspect_ratio': float(aspect_ratio),
            'extent': float(extent),
            'solidity': float(solidity),
            'num_points': len(contour)
        }

    def draw_contours(
        self,
        image: np.ndarray,
        contours: List[np.ndarray],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        draw_all: bool = True
    ) -> np.ndarray:
        """
        Draw contours on image

        Args:
            image: Input image
            contours: List of contours
            color: Contour color (RGB)
            thickness: Line thickness (-1 for filled)
            draw_all: Draw all contours or just largest

        Returns:
            Image with drawn contours
        """
        if not self.available:
            raise RuntimeError("OpenCV not available")

        # Create copy
        output = image.copy()

        # Ensure RGB
        if len(output.shape) == 2:
            output = self.cv2.cvtColor(output, self.cv2.COLOR_GRAY2RGB)

        if draw_all:
            # Draw all contours
            self.cv2.drawContours(output, contours, -1, color, thickness)
        else:
            # Draw only largest
            largest = self.get_largest_contour(contours)
            if largest is not None:
                self.cv2.drawContours(output, [largest], -1, color, thickness)

        return output

    def extract_from_image(
        self,
        image_path: Union[str, Path],
        filter_size: bool = True,
        approximate: bool = True
    ) -> Tuple[List[np.ndarray], dict]:
        """
        Complete contour extraction workflow

        Args:
            image_path: Path to image
            filter_size: Filter by minimum area
            approximate: Approximate contours

        Returns:
            Tuple (contours, metadata)
        """
        if not self.available:
            raise RuntimeError("OpenCV not available")

        from PIL import Image

        # Load image
        image_path = Path(image_path)
        pil_image = Image.open(image_path)
        image = np.array(pil_image)

        # Detect edges
        edges = self.detect_edges(image)

        # Extract contours
        contours = self.extract_contours(edges)

        # Filter contours
        if filter_size:
            contours = self.filter_contours(contours)

        # Approximate contours
        if approximate:
            contours = [self.approximate_contour(c) for c in contours]

        # Get largest contour properties
        largest = self.get_largest_contour(contours)
        properties = self.get_contour_properties(largest) if largest is not None else {}

        metadata = {
            'num_contours': len(contours),
            'largest_contour_properties': properties,
            'image_shape': image.shape,
            'source_file': str(image_path)
        }

        return contours, metadata

    def __repr__(self):
        status = "available" if self.available else "not available"
        return f"ContourExtractor(status={status})"
