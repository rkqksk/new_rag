"""
Model Zoo Service - Dynamic AI Model Management

v7.2.0 - Edge Computing Platform
Centralized management for multiple AI models on edge devices

Supported Models:
- YOLOv8 (object detection) - Already integrated
- DeepSORT (object tracking)
- MediaPipe (pose estimation)
- SAM (segmentation)
- PaddleOCR (text recognition)
- FaceNet (face recognition)

Features:
- Dynamic model loading/unloading
- TensorRT optimization
- Memory management
- Model versioning
- Performance monitoring
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from enum import Enum
import time
import psutil

import torch
import numpy as np

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Supported model types"""
    YOLO = "yolo"
    DEEPSORT = "deepsort"
    MEDIAPIPE = "mediapipe"
    SAM = "sam"
    OCR = "ocr"
    FACE_RECOGNITION = "face_recognition"


class ModelStatus(str, Enum):
    """Model loading status"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class ModelInfo:
    """Model metadata"""

    def __init__(
        self,
        model_id: str,
        model_type: ModelType,
        model_path: str,
        version: str = "1.0",
        device: str = "cuda"
    ):
        self.model_id = model_id
        self.model_type = model_type
        self.model_path = Path(model_path)
        self.version = version
        self.device = device
        self.status = ModelStatus.UNLOADED
        self.model = None
        self.loaded_at = None
        self.memory_mb = 0
        self.inference_count = 0
        self.total_inference_ms = 0.0


class ModelZooService:
    """
    Model Zoo Service for edge AI deployment

    Manages multiple AI models with:
    - Dynamic loading/unloading
    - TensorRT optimization
    - Memory management
    - Performance tracking
    """

    def __init__(
        self,
        models_dir: str = "models",
        max_memory_mb: int = 4096,  # 4GB default
        enable_tensorrt: bool = True
    ):
        """
        Initialize Model Zoo

        Args:
            models_dir: Directory containing model files
            max_memory_mb: Maximum memory for models (MB)
            enable_tensorrt: Enable TensorRT optimization
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.max_memory_mb = max_memory_mb
        self.enable_tensorrt = enable_tensorrt

        # Registry of available models
        self.models: Dict[str, ModelInfo] = {}

        # Performance metrics
        self.metrics = {
            "total_models": 0,
            "loaded_models": 0,
            "total_memory_mb": 0,
            "total_inferences": 0,
            "avg_inference_ms": 0.0
        }

        logger.info(f"Model Zoo initialized (max_memory={max_memory_mb}MB)")

    def register_model(
        self,
        model_id: str,
        model_type: ModelType,
        model_path: str,
        version: str = "1.0",
        device: str = "cuda"
    ) -> ModelInfo:
        """
        Register a model in the zoo

        Args:
            model_id: Unique model identifier
            model_type: Type of model
            model_path: Path to model file
            version: Model version
            device: Device to run on (cuda/cpu)

        Returns:
            ModelInfo object
        """
        model_info = ModelInfo(
            model_id=model_id,
            model_type=model_type,
            model_path=model_path,
            version=version,
            device=device
        )

        self.models[model_id] = model_info
        self.metrics["total_models"] += 1

        logger.info(
            f"Registered model: {model_id} "
            f"(type={model_type}, version={version})"
        )

        return model_info

    def load_model(self, model_id: str) -> bool:
        """
        Load model into memory

        Args:
            model_id: Model identifier

        Returns:
            Success status
        """
        if model_id not in self.models:
            logger.error(f"Model not registered: {model_id}")
            return False

        model_info = self.models[model_id]

        if model_info.status == ModelStatus.LOADED:
            logger.info(f"Model already loaded: {model_id}")
            return True

        try:
            model_info.status = ModelStatus.LOADING
            logger.info(f"Loading model: {model_id}")

            start_time = time.time()

            # Check available memory
            if not self._check_memory_available():
                logger.warning("Insufficient memory, unloading LRU models...")
                self._unload_lru_models()

            # Load model based on type
            if model_info.model_type == ModelType.YOLO:
                model = self._load_yolo(model_info)
            elif model_info.model_type == ModelType.DEEPSORT:
                model = self._load_deepsort(model_info)
            elif model_info.model_type == ModelType.MEDIAPIPE:
                model = self._load_mediapipe(model_info)
            elif model_info.model_type == ModelType.SAM:
                model = self._load_sam(model_info)
            elif model_info.model_type == ModelType.OCR:
                model = self._load_ocr(model_info)
            elif model_info.model_type == ModelType.FACE_RECOGNITION:
                model = self._load_face_recognition(model_info)
            else:
                raise ValueError(f"Unsupported model type: {model_info.model_type}")

            # Apply TensorRT optimization
            if self.enable_tensorrt and model_info.device == "cuda":
                model = self._optimize_tensorrt(model, model_info)

            model_info.model = model
            model_info.status = ModelStatus.LOADED
            model_info.loaded_at = datetime.now()

            # Estimate memory usage
            model_info.memory_mb = self._estimate_model_memory(model)
            self.metrics["total_memory_mb"] += model_info.memory_mb
            self.metrics["loaded_models"] += 1

            load_time = (time.time() - start_time) * 1000

            logger.info(
                f"Model loaded: {model_id} "
                f"(memory={model_info.memory_mb:.1f}MB, "
                f"load_time={load_time:.0f}ms)"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            model_info.status = ModelStatus.ERROR
            return False

    def unload_model(self, model_id: str) -> bool:
        """
        Unload model from memory

        Args:
            model_id: Model identifier

        Returns:
            Success status
        """
        if model_id not in self.models:
            logger.error(f"Model not registered: {model_id}")
            return False

        model_info = self.models[model_id]

        if model_info.status != ModelStatus.LOADED:
            logger.info(f"Model not loaded: {model_id}")
            return True

        try:
            # Delete model
            del model_info.model
            model_info.model = None
            model_info.status = ModelStatus.UNLOADED

            # Update metrics
            self.metrics["total_memory_mb"] -= model_info.memory_mb
            self.metrics["loaded_models"] -= 1
            model_info.memory_mb = 0

            # Force garbage collection
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(f"Model unloaded: {model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload model {model_id}: {e}")
            return False

    def inference(
        self,
        model_id: str,
        inputs: Any,
        **kwargs
    ) -> Dict:
        """
        Run inference on model

        Args:
            model_id: Model identifier
            inputs: Model inputs (image, text, etc.)
            **kwargs: Additional model-specific parameters

        Returns:
            Inference results
        """
        if model_id not in self.models:
            raise ValueError(f"Model not registered: {model_id}")

        model_info = self.models[model_id]

        if model_info.status != ModelStatus.LOADED:
            logger.info(f"Auto-loading model: {model_id}")
            success = self.load_model(model_id)
            if not success:
                raise RuntimeError(f"Failed to load model: {model_id}")

        try:
            start_time = time.time()

            # Run inference based on model type
            if model_info.model_type == ModelType.YOLO:
                results = self._inference_yolo(model_info, inputs, **kwargs)
            elif model_info.model_type == ModelType.DEEPSORT:
                results = self._inference_deepsort(model_info, inputs, **kwargs)
            elif model_info.model_type == ModelType.MEDIAPIPE:
                results = self._inference_mediapipe(model_info, inputs, **kwargs)
            elif model_info.model_type == ModelType.SAM:
                results = self._inference_sam(model_info, inputs, **kwargs)
            elif model_info.model_type == ModelType.OCR:
                results = self._inference_ocr(model_info, inputs, **kwargs)
            elif model_info.model_type == ModelType.FACE_RECOGNITION:
                results = self._inference_face(model_info, inputs, **kwargs)
            else:
                raise ValueError(f"Unsupported model type: {model_info.model_type}")

            inference_time = (time.time() - start_time) * 1000

            # Update metrics
            model_info.inference_count += 1
            model_info.total_inference_ms += inference_time

            self.metrics["total_inferences"] += 1
            total = self.metrics["total_inferences"]
            self.metrics["avg_inference_ms"] = (
                (self.metrics["avg_inference_ms"] * (total - 1) + inference_time) / total
            )

            results["inference_time_ms"] = inference_time
            results["model_id"] = model_id

            return results

        except Exception as e:
            logger.error(f"Inference failed for {model_id}: {e}")
            raise

    def list_models(self) -> List[Dict]:
        """List all registered models"""
        models_list = []

        for model_id, model_info in self.models.items():
            models_list.append({
                "model_id": model_id,
                "model_type": model_info.model_type,
                "version": model_info.version,
                "status": model_info.status,
                "device": model_info.device,
                "memory_mb": model_info.memory_mb,
                "inference_count": model_info.inference_count,
                "avg_inference_ms": (
                    model_info.total_inference_ms / model_info.inference_count
                    if model_info.inference_count > 0 else 0
                ),
                "loaded_at": model_info.loaded_at.isoformat() if model_info.loaded_at else None
            })

        return models_list

    def get_metrics(self) -> Dict:
        """Get Model Zoo metrics"""
        # System memory
        memory = psutil.virtual_memory()

        return {
            **self.metrics,
            "system_memory_used_mb": memory.used / (1024 ** 2),
            "system_memory_available_mb": memory.available / (1024 ** 2),
            "system_memory_percent": memory.percent
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _check_memory_available(self) -> bool:
        """Check if enough memory available"""
        memory = psutil.virtual_memory()
        available_mb = memory.available / (1024 ** 2)
        return available_mb > 512  # Need at least 512MB free

    def _unload_lru_models(self, target_free_mb: int = 512):
        """Unload least recently used models"""
        # Sort by last loaded time
        loaded_models = [
            (model_id, info)
            for model_id, info in self.models.items()
            if info.status == ModelStatus.LOADED
        ]
        loaded_models.sort(key=lambda x: x[1].loaded_at)

        # Unload oldest until target memory freed
        for model_id, _ in loaded_models:
            self.unload_model(model_id)

            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 ** 2)
            if available_mb > target_free_mb:
                break

    def _estimate_model_memory(self, model) -> float:
        """Estimate model memory usage (MB)"""
        try:
            if hasattr(model, 'parameters'):
                param_size = sum(p.numel() * p.element_size() for p in model.parameters())
                buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
                return (param_size + buffer_size) / (1024 ** 2)
            else:
                return 100.0  # Default estimate
        except:
            return 100.0

    def _optimize_tensorrt(self, model, model_info):
        """Apply TensorRT optimization (placeholder)"""
        # TODO: Implement TensorRT optimization
        logger.info(f"TensorRT optimization for {model_info.model_id} (not yet implemented)")
        return model

    # ========================================================================
    # Model Loading Methods
    # ========================================================================

    def _load_yolo(self, model_info):
        """Load YOLO model"""
        from ultralytics import YOLO
        model = YOLO(str(model_info.model_path))
        return model

    def _load_deepsort(self, model_info):
        """Load DeepSORT model"""
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort

            # Initialize DeepSORT tracker
            tracker = DeepSort(
                max_age=30,  # Max frames to keep alive track without detections
                n_init=3,  # Number of consecutive detections before track is confirmed
                nms_max_overlap=1.0,  # Non-maxima suppression threshold
                max_cosine_distance=0.3,  # Threshold for cosine distance metric
                nn_budget=None,  # Max size of appearance descriptor gallery
                embedder="mobilenet",  # Feature extractor: mobilenet, torchreid, clip
                embedder_gpu=model_info.device == "cuda"
            )

            logger.info(f"DeepSORT tracker loaded (device={model_info.device})")
            return tracker

        except ImportError:
            logger.error("deep-sort-realtime not installed. Install: pip install deep-sort-realtime")
            return None
        except Exception as e:
            logger.error(f"Failed to load DeepSORT: {e}")
            return None

    def _load_mediapipe(self, model_info):
        """Load MediaPipe model"""
        try:
            import mediapipe as mp

            # Get solution type from model path or default to pose
            solution_type = getattr(model_info, 'solution_type', 'pose')

            # Initialize MediaPipe solution
            if solution_type == 'pose':
                mp_solution = mp.solutions.pose
                model = mp_solution.Pose(
                    static_image_mode=False,
                    model_complexity=1,  # 0, 1, or 2 (higher = more accurate, slower)
                    smooth_landmarks=True,
                    enable_segmentation=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            elif solution_type == 'hands':
                mp_solution = mp.solutions.hands
                model = mp_solution.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    model_complexity=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            elif solution_type == 'face_mesh':
                mp_solution = mp.solutions.face_mesh
                model = mp_solution.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            elif solution_type == 'holistic':
                mp_solution = mp.solutions.holistic
                model = mp_solution.Holistic(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            else:
                logger.error(f"Unsupported MediaPipe solution: {solution_type}")
                return None

            logger.info(f"MediaPipe {solution_type} loaded")
            return {"model": model, "solution": mp_solution, "type": solution_type}

        except ImportError:
            logger.error("mediapipe not installed. Install: pip install mediapipe")
            return None
        except Exception as e:
            logger.error(f"Failed to load MediaPipe: {e}")
            return None

    def _load_sam(self, model_info):
        """Load SAM model"""
        try:
            from segment_anything import sam_model_registry, SamPredictor

            # Determine model type from path
            model_path_str = str(model_info.model_path)
            if "vit_h" in model_path_str:
                model_type = "vit_h"  # Huge model (2.4GB)
            elif "vit_l" in model_path_str:
                model_type = "vit_l"  # Large model (1.2GB)
            elif "vit_b" in model_path_str:
                model_type = "vit_b"  # Base model (375MB)
            else:
                model_type = "vit_b"  # Default to base
                logger.warning(f"Could not determine SAM model type from path, using {model_type}")

            # Load SAM model
            sam = sam_model_registry[model_type](checkpoint=str(model_info.model_path))

            # Move to device
            if model_info.device == "cuda" and torch.cuda.is_available():
                sam = sam.to(device="cuda")
            else:
                sam = sam.to(device="cpu")

            # Create predictor
            predictor = SamPredictor(sam)

            logger.info(f"SAM model loaded (type={model_type}, device={model_info.device})")
            return {"sam": sam, "predictor": predictor, "model_type": model_type}

        except ImportError:
            logger.error("segment-anything not installed. Install: pip install segment-anything")
            return None
        except Exception as e:
            logger.error(f"Failed to load SAM: {e}")
            return None

    def _load_ocr(self, model_info):
        """Load OCR model"""
        from paddleocr import PaddleOCR
        model = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=model_info.device == 'cuda')
        return model

    def _load_face_recognition(self, model_info):
        """Load face recognition model"""
        try:
            import face_recognition

            # face_recognition library uses dlib under the hood
            # No explicit model loading needed - it uses pre-trained models
            logger.info("Face recognition loaded (using face_recognition library)")

            return {
                "library": "face_recognition",
                "model_type": "HOG+CNN",  # HOG for CPU, CNN for GPU
                "encoding_model": "dlib"
            }

        except ImportError:
            logger.error(
                "face_recognition not installed. Install: "
                "pip install face-recognition (requires dlib and cmake)"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to load face recognition: {e}")
            return None

    # ========================================================================
    # Inference Methods
    # ========================================================================

    def _inference_yolo(self, model_info, image, **kwargs):
        """YOLO inference"""
        results = model_info.model(image, **kwargs)
        # Parse results...
        return {"detections": [], "model_type": "yolo"}

    def _inference_deepsort(self, model_info, detections, **kwargs):
        """
        DeepSORT inference

        Args:
            detections: List of detections in format [[x1, y1, x2, y2, confidence, class_id], ...]
            **kwargs: Additional parameters (frame for reid features)

        Returns:
            Dictionary with tracks information
        """
        tracker = model_info.model

        # Convert detections to DeepSORT format: [[x, y, w, h, confidence, class_id], ...]
        deepsort_detections = []
        for det in detections:
            if len(det) >= 5:
                x1, y1, x2, y2, conf = det[:5]
                class_id = det[5] if len(det) > 5 else 0

                # Convert to [x, y, w, h]
                x, y = x1, y1
                w, h = x2 - x1, y2 - y1

                deepsort_detections.append([[x, y, w, h], conf, class_id])

        # Update tracker
        frame = kwargs.get("frame", None)
        tracks = tracker.update_tracks(deepsort_detections, frame=frame)

        # Format output
        tracked_objects = []
        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ltrb = track.to_ltrb()  # [left, top, right, bottom]

            tracked_objects.append({
                "track_id": track_id,
                "bbox": [float(ltrb[0]), float(ltrb[1]), float(ltrb[2]), float(ltrb[3])],
                "class_id": int(track.get_det_class()) if track.get_det_class() is not None else -1,
                "confidence": float(track.get_det_conf()) if track.get_det_conf() is not None else 0.0,
                "age": track.age,  # Number of frames since track started
                "time_since_update": track.time_since_update
            })

        return {
            "tracks": tracked_objects,
            "num_tracks": len(tracked_objects),
            "model_type": "deepsort"
        }

    def _inference_mediapipe(self, model_info, image, **kwargs):
        """
        MediaPipe inference

        Args:
            image: RGB image (numpy array or PIL Image)
            **kwargs: Additional parameters

        Returns:
            Dictionary with landmarks and detection results
        """
        import cv2

        mp_model = model_info.model
        solution_type = mp_model["type"]
        model = mp_model["model"]

        # Convert BGR to RGB if needed
        if isinstance(image, np.ndarray):
            if len(image.shape) == 3 and image.shape[2] == 3:
                # Assume BGR from OpenCV, convert to RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
        else:
            # Convert PIL to numpy RGB
            image_rgb = np.array(image)

        # Process image
        results = model.process(image_rgb)

        # Extract landmarks based on solution type
        output = {
            "model_type": "mediapipe",
            "solution_type": solution_type
        }

        if solution_type == 'pose':
            if results.pose_landmarks:
                landmarks = []
                for lm in results.pose_landmarks.landmark:
                    landmarks.append({
                        "x": float(lm.x),
                        "y": float(lm.y),
                        "z": float(lm.z),
                        "visibility": float(lm.visibility)
                    })
                output["pose_landmarks"] = landmarks
                output["num_landmarks"] = len(landmarks)
            else:
                output["pose_landmarks"] = []
                output["num_landmarks"] = 0

        elif solution_type == 'hands':
            if results.multi_hand_landmarks:
                hands = []
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    landmarks = []
                    for lm in hand_landmarks.landmark:
                        landmarks.append({
                            "x": float(lm.x),
                            "y": float(lm.y),
                            "z": float(lm.z)
                        })

                    handedness = results.multi_handedness[hand_idx].classification[0]
                    hands.append({
                        "landmarks": landmarks,
                        "label": handedness.label,  # "Left" or "Right"
                        "score": float(handedness.score)
                    })
                output["hands"] = hands
                output["num_hands"] = len(hands)
            else:
                output["hands"] = []
                output["num_hands"] = 0

        elif solution_type == 'face_mesh':
            if results.multi_face_landmarks:
                faces = []
                for face_landmarks in results.multi_face_landmarks:
                    landmarks = []
                    for lm in face_landmarks.landmark:
                        landmarks.append({
                            "x": float(lm.x),
                            "y": float(lm.y),
                            "z": float(lm.z)
                        })
                    faces.append({"landmarks": landmarks})
                output["faces"] = faces
                output["num_faces"] = len(faces)
            else:
                output["faces"] = []
                output["num_faces"] = 0

        elif solution_type == 'holistic':
            # Combine pose, face, and hands
            output["pose_detected"] = results.pose_landmarks is not None
            output["face_detected"] = results.face_landmarks is not None
            output["left_hand_detected"] = results.left_hand_landmarks is not None
            output["right_hand_detected"] = results.right_hand_landmarks is not None

        return output

    def _inference_sam(self, model_info, image, **kwargs):
        """
        SAM inference

        Args:
            image: RGB image (numpy array or PIL Image)
            **kwargs: Additional parameters
                - point_coords: List of point prompts [[x, y], ...] (optional)
                - point_labels: List of labels [1=foreground, 0=background] (optional)
                - box: Bounding box [x1, y1, x2, y2] (optional)
                - mask_input: Previous mask for refinement (optional)
                - multimask_output: Return multiple masks (default True)

        Returns:
            Dictionary with segmentation masks
        """
        import cv2

        sam_model = model_info.model
        predictor = sam_model["predictor"]

        # Convert to numpy array if needed
        if not isinstance(image, np.ndarray):
            image = np.array(image)

        # Convert RGB to BGR if needed (SAM expects RGB)
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Assume BGR from OpenCV, convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image

        # Set image
        predictor.set_image(image_rgb)

        # Get prompts from kwargs
        point_coords = kwargs.get("point_coords", None)
        point_labels = kwargs.get("point_labels", None)
        box = kwargs.get("box", None)
        mask_input = kwargs.get("mask_input", None)
        multimask_output = kwargs.get("multimask_output", True)

        # Convert prompts to numpy arrays
        if point_coords is not None:
            point_coords = np.array(point_coords)
        if point_labels is not None:
            point_labels = np.array(point_labels)
        if box is not None:
            box = np.array(box)

        # Predict masks
        masks, scores, logits = predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            box=box,
            mask_input=mask_input,
            multimask_output=multimask_output
        )

        # Format output
        masks_list = []
        for i, (mask, score) in enumerate(zip(masks, scores)):
            # Find contours for this mask
            contours, _ = cv2.findContours(
                mask.astype(np.uint8),
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            # Calculate bounding box
            if len(contours) > 0:
                x, y, w, h = cv2.boundingRect(contours[0])
                bbox = [int(x), int(y), int(x + w), int(y + h)]
            else:
                bbox = [0, 0, 0, 0]

            masks_list.append({
                "mask_id": i,
                "score": float(score),
                "area": int(mask.sum()),
                "bbox": bbox,
                "mask": mask.tolist() if kwargs.get("return_mask", False) else None
            })

        return {
            "masks": masks_list,
            "num_masks": len(masks_list),
            "model_type": "sam",
            "image_shape": image_rgb.shape[:2]
        }

    def _inference_ocr(self, model_info, image, **kwargs):
        """OCR inference"""
        results = model_info.model.ocr(image, cls=True)
        texts = []
        for line in results:
            if line:
                for word_info in line:
                    texts.append({
                        "text": word_info[1][0],
                        "confidence": word_info[1][1],
                        "bbox": word_info[0]
                    })
        return {"texts": texts, "model_type": "ocr"}

    def _inference_face(self, model_info, image, **kwargs):
        """
        Face recognition inference

        Args:
            image: RGB image (numpy array or PIL Image)
            **kwargs: Additional parameters
                - known_encodings: List of known face encodings for matching
                - known_names: List of names corresponding to known_encodings
                - tolerance: Face matching tolerance (default 0.6, lower = stricter)
                - model: Detection model "hog" (CPU) or "cnn" (GPU)

        Returns:
            Dictionary with detected faces and matches
        """
        import face_recognition
        import cv2

        # Convert to numpy array if needed
        if not isinstance(image, np.ndarray):
            image = np.array(image)

        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Assume BGR from OpenCV
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image

        # Get parameters
        known_encodings = kwargs.get("known_encodings", [])
        known_names = kwargs.get("known_names", [])
        tolerance = kwargs.get("tolerance", 0.6)
        detection_model = kwargs.get("model", "hog")  # "hog" or "cnn"

        # Detect face locations
        face_locations = face_recognition.face_locations(
            image_rgb,
            model=detection_model
        )

        # Get face encodings
        face_encodings = face_recognition.face_encodings(
            image_rgb,
            face_locations
        )

        # Match faces if known encodings provided
        faces = []
        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            matches = []
            name = "Unknown"
            match_confidence = 0.0

            if len(known_encodings) > 0:
                # Compare with known faces
                face_distances = face_recognition.face_distance(
                    known_encodings,
                    encoding
                )

                # Find best match
                best_match_index = np.argmin(face_distances)
                if face_distances[best_match_index] < tolerance:
                    name = known_names[best_match_index]
                    # Convert distance to confidence (0-1)
                    match_confidence = 1.0 - face_distances[best_match_index]

                matches = [
                    {
                        "name": known_names[i],
                        "distance": float(face_distances[i]),
                        "confidence": float(1.0 - face_distances[i])
                    }
                    for i in range(len(known_names))
                ]

            faces.append({
                "bbox": [int(left), int(top), int(right), int(bottom)],
                "encoding": encoding.tolist() if kwargs.get("return_encoding", False) else None,
                "name": name,
                "match_confidence": float(match_confidence),
                "matches": matches if kwargs.get("return_all_matches", False) else []
            })

        return {
            "faces": faces,
            "num_faces": len(faces),
            "model_type": "face_recognition",
            "detection_model": detection_model
        }


# Global singleton
_model_zoo: Optional[ModelZooService] = None


def get_model_zoo() -> ModelZooService:
    """Get or create Model Zoo singleton"""
    global _model_zoo
    if _model_zoo is None:
        _model_zoo = ModelZooService()
    return _model_zoo
