"""
Manufacturing API Routes - Advanced Manufacturing v7.1.0

LORA + UR10e Robot Integration
Real-time vision inspection and collaborative robotics

Endpoints:
- LORA: Adapter management, inspection
- Robot: Control, pick and place, emergency stop
- Inspection: Live streaming, metrics
- Quality: Defect tracking, SPC charts
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import base64

# Import services
from src.services.lora_vision_service import get_lora_vision_service
from src.services.ur10e_service import get_ur10e_service, RobotState
from src.utils.robot_safety import get_safety_validator, SafetyLevel
from src.utils.coordinate_transform import get_coordinate_transform

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/manufacturing",
    tags=["manufacturing"],
    responses={404: {"description": "Not found"}}
)

# ============================================================================
# Pydantic Models
# ============================================================================

class LORAAdapterInfo(BaseModel):
    """LORA adapter information"""
    product_type: str
    adapter_name: str
    is_trained: bool
    is_active: bool
    defect_classes: List[str]
    file_size_mb: Optional[float] = None


class AdapterSwitchRequest(BaseModel):
    """Request to switch LORA adapter"""
    product_type: str = Field(..., description="Product type (pet_bottles, aluminum_cans, etc.)")


class InspectionRequest(BaseModel):
    """Image inspection request"""
    product_type: str = Field(default="pet_bottles", description="Product type")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class InspectionResult(BaseModel):
    """Inspection result"""
    timestamp: str
    product_type: str
    defects: List[Dict]
    defect_count: int
    has_defects: bool
    inference_time_ms: float
    lora_adapter: str


class RobotPosition(BaseModel):
    """Robot position (x, y, z, rx, ry, rz)"""
    x: float = Field(..., description="X coordinate (meters)")
    y: float = Field(..., description="Y coordinate (meters)")
    z: float = Field(..., description="Z coordinate (meters)")
    rx: float = Field(default=0.0, description="Rotation X (radians)")
    ry: float = Field(default=0.0, description="Rotation Y (radians)")
    rz: float = Field(default=0.0, description="Rotation Z (radians)")


class PickPlaceRequest(BaseModel):
    """Pick and place request"""
    pick_position: RobotPosition
    place_position: RobotPosition
    approach_height: float = Field(default=0.1, ge=0.01, le=0.2)


class PixelCoordinate(BaseModel):
    """Pixel coordinate with depth"""
    pixel_x: float = Field(..., description="Pixel X coordinate")
    pixel_y: float = Field(..., description="Pixel Y coordinate")
    depth_m: float = Field(..., description="Depth in meters")


# ============================================================================
# LORA Vision Endpoints
# ============================================================================

@router.get("/lora/adapters", response_model=List[LORAAdapterInfo])
async def list_adapters():
    """
    List all LORA adapters

    Returns:
        List of adapter information
    """
    try:
        lora_vision = get_lora_vision_service()
        adapters = lora_vision.list_adapters()
        return adapters

    except Exception as e:
        logger.error(f"Failed to list adapters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/lora/adapters/{product_type}/activate")
async def activate_adapter(product_type: str):
    """
    Switch to specified LORA adapter

    Args:
        product_type: Product type (pet_bottles, aluminum_cans, etc.)

    Returns:
        Switch result with timing
    """
    try:
        lora_vision = get_lora_vision_service()
        result = lora_vision.switch_adapter(product_type)

        return {
            "success": True,
            "product_type": product_type,
            **result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to switch adapter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lora/inspect", response_model=InspectionResult)
async def inspect_image(
    file: UploadFile = File(..., description="Image file (JPEG, PNG)"),
    product_type: str = Query(default="pet_bottles", description="Product type"),
    confidence_threshold: float = Query(default=0.5, ge=0.0, le=1.0)
):
    """
    Inspect uploaded image for defects

    Args:
        file: Image file (JPEG, PNG)
        product_type: Product category for LORA adapter
        confidence_threshold: Detection confidence threshold

    Returns:
        Inspection results with defects detected
    """
    try:
        # Read and decode image
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes))
        image_np = np.array(image)

        # Convert RGB to BGR for OpenCV
        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        # Run inspection
        lora_vision = get_lora_vision_service()
        result = lora_vision.inspect(
            image_np,
            product_type=product_type,
            confidence_threshold=confidence_threshold
        )

        return result

    except Exception as e:
        logger.error(f"Inspection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lora/metrics")
async def get_lora_metrics():
    """
    Get LORA vision service metrics

    Returns:
        Performance metrics
    """
    try:
        lora_vision = get_lora_vision_service()
        metrics = lora_vision.get_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UR10e Robot Endpoints
# ============================================================================

@router.post("/robot/connect")
async def connect_robot(simulation_mode: bool = Query(default=True)):
    """
    Connect to UR10e robot

    Args:
        simulation_mode: Run in simulation mode (default: True)

    Returns:
        Connection status
    """
    try:
        robot = get_ur10e_service(simulation_mode=simulation_mode)
        result = robot.connect()

        return {
            "success": result.get("connected", False),
            **result
        }

    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robot/disconnect")
async def disconnect_robot():
    """Disconnect from robot"""
    try:
        robot = get_ur10e_service()
        robot.disconnect()

        return {
            "success": True,
            "message": "Robot disconnected"
        }

    except Exception as e:
        logger.error(f"Disconnect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/robot/status")
async def get_robot_status():
    """
    Get current robot status

    Returns:
        Robot state, position, and metrics
    """
    try:
        robot = get_ur10e_service()

        return {
            "state": robot.state,
            "current_pose": robot.get_current_pose() if robot.state != RobotState.DISCONNECTED else None,
            "metrics": robot.get_metrics(),
            "emergency_stop_active": robot.emergency_stop_active
        }

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robot/move")
async def move_robot(position: RobotPosition):
    """
    Move robot to specified position

    Args:
        position: Target position (x, y, z, rx, ry, rz)

    Returns:
        Movement result
    """
    try:
        robot = get_ur10e_service()

        # Convert to tuple
        target_pose = (
            position.x, position.y, position.z,
            position.rx, position.ry, position.rz
        )

        result = robot.move_to_pose(target_pose)

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Movement failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Move failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robot/pick_and_place")
async def pick_and_place(request: PickPlaceRequest):
    """
    Execute pick and place operation

    Args:
        request: Pick and place coordinates

    Returns:
        Operation result with cycle time
    """
    try:
        robot = get_ur10e_service()

        # Convert to tuples
        pick_coords = (
            request.pick_position.x,
            request.pick_position.y,
            request.pick_position.z
        )
        place_coords = (
            request.place_position.x,
            request.place_position.y,
            request.place_position.z
        )

        result = robot.pick_and_place(
            pick_coords=pick_coords,
            place_coords=place_coords,
            approach_height=request.approach_height
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Pick and place failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pick and place failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robot/emergency_stop")
async def emergency_stop():
    """
    **EMERGENCY STOP - Safety Critical**

    Immediately stops all robot movement

    Returns:
        Emergency stop confirmation
    """
    try:
        robot = get_ur10e_service()
        result = robot.emergency_stop()

        # Broadcast via Socket.IO (if available)
        # await sio.emit('emergency_stop', result)

        return result

    except Exception as e:
        logger.critical(f"Emergency stop error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robot/reset_emergency_stop")
async def reset_emergency_stop():
    """
    Reset emergency stop (requires manual verification)

    Returns:
        Reset confirmation
    """
    try:
        robot = get_ur10e_service()
        result = robot.reset_emergency_stop()

        return result

    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Safety & Coordinate Transform Endpoints
# ============================================================================

@router.post("/safety/validate_position")
async def validate_position(position: RobotPosition):
    """
    Validate if position is safe

    Args:
        position: Position to validate

    Returns:
        Safety validation result
    """
    try:
        safety_validator = get_safety_validator()

        is_safe, safety_level, message = safety_validator.validate_position(
            (position.x, position.y, position.z)
        )

        return {
            "is_safe": is_safe,
            "safety_level": safety_level,
            "message": message,
            "position": {
                "x": position.x,
                "y": position.y,
                "z": position.z
            }
        }

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety/report")
async def get_safety_report():
    """
    Get safety report

    Returns:
        Safety violations and metrics
    """
    try:
        safety_validator = get_safety_validator()
        report = safety_validator.get_safety_report()
        return report

    except Exception as e:
        logger.error(f"Failed to get safety report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform/pixel_to_robot")
async def pixel_to_robot(coord: PixelCoordinate):
    """
    Convert pixel coordinates to robot frame

    Args:
        coord: Pixel coordinate with depth

    Returns:
        Robot frame coordinates (x, y, z)
    """
    try:
        transform = get_coordinate_transform()

        robot_coords = transform.pixel_to_robot(
            coord.pixel_x,
            coord.pixel_y,
            coord.depth_m
        )

        return {
            "pixel_x": coord.pixel_x,
            "pixel_y": coord.pixel_y,
            "depth_m": coord.depth_m,
            "robot_x": robot_coords[0],
            "robot_y": robot_coords[1],
            "robot_z": robot_coords[2]
        }

    except Exception as e:
        logger.error(f"Transform failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transform/calibration")
async def get_calibration_info():
    """
    Get camera calibration information

    Returns:
        Calibration status and transformation matrix
    """
    try:
        transform = get_coordinate_transform()
        info = transform.get_calibration_info()
        return info

    except Exception as e:
        logger.error(f"Failed to get calibration info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Live Inspection Endpoints
# ============================================================================

@router.get("/inspection/stream")
async def video_stream(
    product_type: str = Query(default="pet_bottles"),
    fps: int = Query(default=10, ge=1, le=30)
):
    """
    Live video stream with real-time inspection overlay

    Args:
        product_type: Product type for LORA adapter
        fps: Frames per second (1-30)

    Returns:
        Server-Sent Events (SSE) stream with inspection results
    """
    async def generate():
        """Generate inspection stream"""
        lora_vision = get_lora_vision_service()

        # Ensure correct adapter is loaded
        lora_vision.switch_adapter(product_type)

        frame_delay = 1.0 / fps

        # Simulate camera frames (in production, read from camera)
        while True:
            try:
                # Generate synthetic frame (640x640)
                # In production: frame = camera.capture()
                frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

                # Run inspection
                result = lora_vision.inspect(frame, product_type=product_type)

                # Draw bounding boxes (if defects detected)
                if result["defects"]:
                    for defect in result["defects"]:
                        bbox = defect["bbox"]
                        cv2.rectangle(
                            frame,
                            (int(bbox["x1"]), int(bbox["y1"])),
                            (int(bbox["x2"]), int(bbox["y2"])),
                            (0, 0, 255), 2
                        )
                        # Add label
                        label = f"{defect['defect_type']} {defect['confidence']:.2f}"
                        cv2.putText(
                            frame,
                            label,
                            (int(bbox["x1"]), int(bbox["y1"]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 0, 255),
                            2
                        )

                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                frame_b64 = base64.b64encode(frame_bytes).decode()

                # Create SSE message
                event_data = {
                    "frame": frame_b64,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }

                yield f"data: {event_data}\n\n"

                await asyncio.sleep(frame_delay)

            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
                break

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


# ============================================================================
# System Health & Metrics
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Manufacturing system health check

    Returns:
        Health status of all components
    """
    try:
        lora_vision = get_lora_vision_service()
        robot = get_ur10e_service()

        lora_metrics = lora_vision.get_metrics()
        robot_metrics = robot.get_metrics()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "lora_vision": {
                    "status": "active",
                    "current_product": lora_metrics["current_product"],
                    "total_inspections": lora_metrics["total_inspections"]
                },
                "robot": {
                    "status": robot.state,
                    "emergency_stop": robot.emergency_stop_active,
                    "total_cycles": robot_metrics["successful_cycles"]
                }
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
