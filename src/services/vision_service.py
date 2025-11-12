"""
Vision Service - YOLOv8/v10 Object Detection
Real-time product defect detection and classification
Version: v8.4.0
"""

import logging
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import torch

logger = logging.getLogger(__name__)


class VisionService:
    """Vision-based product inspection using YOLOv8/v10"""

    DEFECT_CLASSES = [
        'crack',
        'scratch',
        'dent',
        'discoloration',
        'contamination',
        'deformation',
        'missing_part',
        'excess_material',
    ]

    def __init__(self, model_path: Optional[str] = None, model_type: str = 'yolov8'):
        """
        Initialize vision service

        Args:
            model_path: Path to YOLO model weights
            model_type: 'yolov8' or 'yolov10'
        """
        self.model_path = model_path
        self.model_type = model_type
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f'Vision service initialized: {model_type} on {self.device}')

    def load_model(self):
        """Lazy load YOLO model"""
        if self.model is None:
            try:
                from ultralytics import YOLO

                if self.model_path and Path(self.model_path).exists():
                    logger.info(f'Loading custom model: {self.model_path}')
                    self.model = YOLO(self.model_path)
                else:
                    # Use pre-trained model
                    if self.model_type == 'yolov10':
                        logger.info('Loading YOLOv10n')
                        self.model = YOLO('yolov10n.pt')
                    else:
                        logger.info('Loading YOLOv8n')
                        self.model = YOLO('yolov8n.pt')

                self.model.to(self.device)
                logger.info('YOLO model loaded successfully')

            except Exception as e:
                logger.error(f'Failed to load YOLO model: {e}')
                raise

    async def detect_defects(
        self,
        image_data: bytes,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45
    ) -> Dict[str, Any]:
        """
        Detect defects in product image

        Args:
            image_data: Image bytes
            confidence_threshold: Minimum confidence score (0-1)
            iou_threshold: IoU threshold for NMS

        Returns:
            {
                'defects': List[dict],
                'total_defects': int,
                'quality_score': float,
                'pass': bool,
                'image_size': tuple
            }
        """
        try:
            # Load model if not loaded
            self.load_model()

            # Decode image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError('Failed to decode image')

            # Run inference
            results = self.model.predict(
                image,
                conf=confidence_threshold,
                iou=iou_threshold,
                device=self.device,
                verbose=False,
            )

            # Parse results
            defects = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    defect = {
                        'class': self.DEFECT_CLASSES[int(box.cls[0])] if int(box.cls[0]) < len(self.DEFECT_CLASSES) else 'unknown',
                        'confidence': float(box.conf[0]),
                        'bbox': [float(x) for x in box.xyxy[0].tolist()],
                        'center': [
                            float((box.xyxy[0][0] + box.xyxy[0][2]) / 2),
                            float((box.xyxy[0][1] + box.xyxy[0][3]) / 2),
                        ],
                        'area': float((box.xyxy[0][2] - box.xyxy[0][0]) * (box.xyxy[0][3] - box.xyxy[0][1])),
                    }
                    defects.append(defect)

            # Calculate quality score (100 - defect penalty)
            total_defects = len(defects)
            quality_score = max(0, 100 - total_defects * 10)

            # Determine pass/fail
            pass_inspection = total_defects == 0 or quality_score >= 70

            logger.info(f'Detected {total_defects} defects, quality={quality_score:.1f}, pass={pass_inspection}')

            return {
                'defects': defects,
                'total_defects': total_defects,
                'quality_score': quality_score,
                'pass': pass_inspection,
                'image_size': image.shape[:2],
                'success': True,
            }

        except Exception as e:
            logger.error(f'Defect detection failed: {e}')
            return {
                'defects': [],
                'total_defects': 0,
                'quality_score': 0,
                'pass': False,
                'image_size': (0, 0),
                'success': False,
                'error': str(e),
            }

    async def classify_product(
        self,
        image_data: bytes,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Classify product category from image

        Args:
            image_data: Image bytes
            top_k: Number of top predictions to return

        Returns:
            {
                'predictions': List[dict],
                'top_class': str,
                'confidence': float
            }
        """
        try:
            self.load_model()

            # Decode image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Run classification
            results = self.model.predict(image, device=self.device, verbose=False)

            predictions = []
            for result in results:
                probs = result.probs
                if probs is not None:
                    top_indices = probs.top5
                    top_confs = probs.top5conf

                    for idx, conf in zip(top_indices[:top_k], top_confs[:top_k]):
                        predictions.append({
                            'class': result.names[int(idx)],
                            'confidence': float(conf),
                        })

            if predictions:
                top_class = predictions[0]['class']
                confidence = predictions[0]['confidence']
            else:
                top_class = 'unknown'
                confidence = 0.0

            return {
                'predictions': predictions,
                'top_class': top_class,
                'confidence': confidence,
                'success': True,
            }

        except Exception as e:
            logger.error(f'Product classification failed: {e}')
            return {
                'predictions': [],
                'top_class': 'unknown',
                'confidence': 0.0,
                'success': False,
                'error': str(e),
            }

    async def annotate_image(
        self,
        image_data: bytes,
        defects: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Draw bounding boxes on image

        Args:
            image_data: Original image bytes
            defects: List of defects with bbox
            output_path: Optional path to save annotated image

        Returns:
            Annotated image bytes
        """
        try:
            # Decode image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Draw boxes
            for defect in defects:
                bbox = defect['bbox']
                x1, y1, x2, y2 = map(int, bbox)

                # Choose color based on defect type
                color = (0, 0, 255)  # Red for defects

                # Draw rectangle
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

                # Add label
                label = f"{defect['class']} {defect['confidence']:.2f}"
                cv2.putText(
                    image,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

            # Encode back to bytes
            success, encoded = cv2.imencode('.jpg', image)
            if not success:
                raise ValueError('Failed to encode image')

            annotated_bytes = encoded.tobytes()

            # Save if output path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(annotated_bytes)
                logger.info(f'Saved annotated image to {output_path}')

            return annotated_bytes

        except Exception as e:
            logger.error(f'Image annotation failed: {e}')
            return image_data

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            'model_type': self.model_type,
            'model_path': self.model_path,
            'device': self.device,
            'loaded': self.model is not None,
            'defect_classes': self.DEFECT_CLASSES,
        }


# Singleton instance
_vision_service = None


def get_vision_service(
    model_path: Optional[str] = None,
    model_type: str = 'yolov8'
) -> VisionService:
    """Get vision service singleton"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService(model_path, model_type)
    return _vision_service
