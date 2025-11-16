"""
Ultimate Manufacturing AI API Routes - v7.4.0
"""

from typing import List, Dict, Optional, Any, Tuple
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from src.services.ultimate_manufacturing_ai_service import (
    UltimateManufacturingAIService,
    PLCProtocol,
    get_ultimate_manufacturing_ai_service
)


class InspectionRequest(BaseModel):
    """Request for multi-camera inspection"""
    defect_threshold: float = Field(0.8, ge=0, le=1.0)


class RobotMoveRequest(BaseModel):
    """Request for robot move"""
    target_position: Tuple[float, float, float]
    speed: float = Field(100.0, ge=0, le=1000.0)


class PLCOperationRequest(BaseModel):
    """Request for PLC operation"""
    plc_id: str
    protocol: PLCProtocol
    operation: str  # "read" or "write"
    address: int
    value: Optional[Any] = None


class UltimateManufacturingAIRouter:
    """Ultimate Manufacturing AI API Router"""

    def __init__(self, service: Optional[UltimateManufacturingAIService] = None):
        self.router = APIRouter(prefix="/ultimate-manufacturing-ai", tags=["Manufacturing AI"])
        self.service = service or get_ultimate_manufacturing_ai_service()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.router.post("/inspect")
        async def multi_camera_inspection(
            request: InspectionRequest,
            images: List[UploadFile] = File(...)
        ):
            """
            Multi-camera synchronized inspection
            
            Supports up to 16 cameras
            """
            try:
                images_dict = {}
                for i, image in enumerate(images):
                    camera_id = f"camera_{i+1}"
                    images_dict[camera_id] = await image.read()
                
                result = await self.service.multi_camera_inspection(
                    images_dict, request.defect_threshold
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Inspection failed: {str(e)}")

        @self.router.post("/robot/move")
        async def robot_move(request: RobotMoveRequest):
            """
            Move robot with collision avoidance
            
            Features:
            - Zero-collision path planning
            - Safety zone compliance
            - Dynamic replanning
            """
            try:
                result = await self.service.robot_move_with_collision_avoidance(
                    request.target_position, request.speed
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Robot move failed: {str(e)}")

        @self.router.post("/plc/operation")
        async def plc_operation(request: PLCOperationRequest):
            """
            PLC operation (read/write)
            
            Protocols:
            - Modbus TCP/RTU
            - OPC-UA
            - PROFINET
            - Ethernet/IP
            """
            try:
                result = await self.service.plc_operation(
                    request.plc_id,
                    request.protocol,
                    request.operation,
                    request.address,
                    request.value
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"PLC operation failed: {str(e)}")

        @self.router.get("/digital-twin")
        async def get_digital_twin():
            """Get current digital twin state"""
            try:
                return self.service.get_digital_twin_state()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get digital twin: {str(e)}")

        @self.router.get("/stats")
        async def get_stats():
            """Get manufacturing AI statistics"""
            try:
                return self.service.get_stats()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "Ultimate Manufacturing AI",
                "version": "7.4.0",
                "features": {
                    "num_cameras": self.service.num_cameras,
                    "digital_twin": self.service.enable_digital_twin,
                    "3d_vision": self.service.enable_3d_vision
                },
                "stats": self.service.get_stats()
            }


def get_ultimate_manufacturing_ai_router(service: Optional[UltimateManufacturingAIService] = None) -> APIRouter:
    """Factory function"""
    router_instance = UltimateManufacturingAIRouter(service=service)
    return router_instance.router
