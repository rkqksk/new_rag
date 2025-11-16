"""
Manufacturing Execution System (MES) API Routes - v7.3.0
ISA-95 compliant MES for production management
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.mes_service import (
    MESService,
    WorkOrder,
    WorkOrderStatus,
    ProductionRecord,
    MaterialLot,
    QualityStatus,
    get_mes_service
)


# ========================================================================
# Request/Response Models
# ========================================================================

class CreateWorkOrderRequest(BaseModel):
    """Request model for creating work order"""
    product_id: str = Field(..., description="Product identifier")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., ge=1, description="Quantity to produce")
    planned_start: datetime = Field(..., description="Planned start time")
    planned_end: datetime = Field(..., description="Planned end time")
    equipment_id: Optional[str] = Field(None, description="Assigned equipment")
    priority: int = Field(5, ge=1, le=10, description="Priority (1=lowest, 10=highest)")


class StartWorkOrderRequest(BaseModel):
    """Request model for starting work order"""
    operator_id: str = Field(..., description="Operator identifier")
    equipment_id: Optional[str] = Field(None, description="Equipment being used")


class RecordProductionRequest(BaseModel):
    """Request model for recording production"""
    wo_id: str = Field(..., description="Work order ID")
    quantity: int = Field(..., ge=1, description="Quantity produced")
    quality_status: QualityStatus = Field(..., description="Quality status")
    equipment_id: str = Field(..., description="Equipment used")
    operator_id: str = Field(..., description="Operator ID")
    cycle_time_sec: float = Field(..., ge=0, description="Cycle time in seconds")
    defects: Optional[List[str]] = Field(None, description="List of defects")
    lot_number: Optional[str] = Field(None, description="Material lot number")


class ReceiveMaterialRequest(BaseModel):
    """Request model for receiving material"""
    material_id: str = Field(..., description="Material identifier")
    material_name: str = Field(..., description="Material name")
    quantity: float = Field(..., ge=0, description="Quantity received")
    unit: str = Field(..., description="Unit of measure")
    supplier: str = Field(..., description="Supplier name")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")


class ConsumeMaterialRequest(BaseModel):
    """Request model for consuming material"""
    wo_id: str = Field(..., description="Work order ID")
    quantity: float = Field(..., ge=0, description="Quantity to consume")


class OEERequest(BaseModel):
    """Request model for OEE calculation"""
    equipment_id: str = Field(..., description="Equipment identifier")
    period_start: datetime = Field(..., description="Period start time")
    period_end: datetime = Field(..., description="Period end time")
    ideal_cycle_time_sec: float = Field(..., ge=0, description="Ideal cycle time")


class OEEResponse(BaseModel):
    """Response model for OEE calculation"""
    oee: float = Field(..., ge=0, le=1, description="Overall Equipment Effectiveness")
    availability: float = Field(..., ge=0, le=1, description="Availability factor")
    performance: float = Field(..., ge=0, le=1, description="Performance factor")
    quality: float = Field(..., ge=0, le=1, description="Quality factor")
    metrics: Dict[str, Any] = Field(..., description="Detailed metrics")


class ProductionSummaryResponse(BaseModel):
    """Response model for production summary"""
    total_production: int
    good_quantity: int
    scrap_quantity: int
    first_pass_yield: float
    work_orders_completed: int
    work_orders_in_progress: int
    avg_cycle_time_sec: float
    period_start: datetime
    period_end: datetime


# ========================================================================
# Router Class
# ========================================================================

class MESRouter:
    """Manufacturing Execution System API Router"""

    def __init__(self, mes_service: Optional[MESService] = None):
        """
        Initialize MES Router

        Args:
            mes_service: MES service instance
        """
        self.router = APIRouter(prefix="/mes", tags=["Manufacturing Execution System"])
        self.mes_service = mes_service or get_mes_service()
        self._setup_routes()

    def _setup_routes(self):
        """Configure API routes"""

        # ====================================================================
        # Work Order Management
        # ====================================================================

        @self.router.post("/work-orders", response_model=WorkOrder)
        async def create_work_order(request: CreateWorkOrderRequest):
            """
            Create a new work order

            Creates a work order in DRAFT status. Must be released before production.

            Args:
                request: Work order details

            Returns:
                Created work order with generated WO ID
            """
            try:
                wo = self.mes_service.create_work_order(
                    product_id=request.product_id,
                    product_name=request.product_name,
                    quantity=request.quantity,
                    planned_start=request.planned_start,
                    planned_end=request.planned_end,
                    equipment_id=request.equipment_id,
                    priority=request.priority
                )
                return wo

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create work order: {str(e)}")

        @self.router.post("/work-orders/{wo_id}/release")
        async def release_work_order(wo_id: str):
            """
            Release work order for production

            Changes status from DRAFT to RELEASED, making it available for execution.

            Args:
                wo_id: Work order ID

            Returns:
                Success confirmation
            """
            try:
                success = self.mes_service.release_work_order(wo_id)
                if not success:
                    raise HTTPException(status_code=404, detail=f"Work order {wo_id} not found")

                return {
                    "wo_id": wo_id,
                    "status": "released",
                    "message": "Work order released for production"
                }

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to release work order: {str(e)}")

        @self.router.post("/work-orders/{wo_id}/start")
        async def start_work_order(wo_id: str, request: StartWorkOrderRequest):
            """
            Start work order execution

            Changes status to IN_PROGRESS and records actual start time.

            Args:
                wo_id: Work order ID
                request: Start details (operator, equipment)

            Returns:
                Updated work order
            """
            try:
                wo = self.mes_service.start_work_order(
                    wo_id=wo_id,
                    operator_id=request.operator_id,
                    equipment_id=request.equipment_id
                )

                if not wo:
                    raise HTTPException(status_code=404, detail=f"Work order {wo_id} not found")

                return wo

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to start work order: {str(e)}")

        @self.router.post("/work-orders/{wo_id}/complete")
        async def complete_work_order(wo_id: str):
            """
            Complete work order

            Changes status to COMPLETED and records actual end time.

            Args:
                wo_id: Work order ID

            Returns:
                Success confirmation with final counts
            """
            try:
                success = self.mes_service.complete_work_order(wo_id)
                if not success:
                    raise HTTPException(status_code=404, detail=f"Work order {wo_id} not found")

                # Get final work order details
                wo = self.mes_service.work_orders.get(wo_id)

                return {
                    "wo_id": wo_id,
                    "status": "completed",
                    "quantity_produced": wo.quantity_produced if wo else 0,
                    "quantity_good": wo.quantity_good if wo else 0,
                    "quantity_scrap": wo.quantity_scrap if wo else 0,
                    "message": "Work order completed"
                }

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to complete work order: {str(e)}")

        @self.router.get("/work-orders")
        async def get_work_orders(
            status: Optional[WorkOrderStatus] = None,
            limit: int = Query(50, ge=1, le=500)
        ):
            """
            Get work orders with filtering

            Args:
                status: Filter by status
                limit: Maximum number of results

            Returns:
                List of work orders
            """
            try:
                work_orders = list(self.mes_service.work_orders.values())

                # Filter by status if provided
                if status:
                    work_orders = [wo for wo in work_orders if wo.status == status]

                # Apply limit
                work_orders = work_orders[:limit]

                return {
                    "work_orders": work_orders,
                    "total": len(work_orders),
                    "filters": {"status": status}
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get work orders: {str(e)}")

        @self.router.get("/work-orders/{wo_id}", response_model=WorkOrder)
        async def get_work_order(wo_id: str):
            """
            Get work order details

            Args:
                wo_id: Work order ID

            Returns:
                Work order details
            """
            try:
                wo = self.mes_service.work_orders.get(wo_id)
                if not wo:
                    raise HTTPException(status_code=404, detail=f"Work order {wo_id} not found")

                return wo

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get work order: {str(e)}")

        # ====================================================================
        # Production Recording
        # ====================================================================

        @self.router.post("/production/record")
        async def record_production(request: RecordProductionRequest):
            """
            Record production event

            Records units produced with quality status, defects, and cycle time.

            Args:
                request: Production record details

            Returns:
                Created production record
            """
            try:
                record = self.mes_service.record_production(
                    wo_id=request.wo_id,
                    quantity=request.quantity,
                    quality_status=request.quality_status,
                    equipment_id=request.equipment_id,
                    operator_id=request.operator_id,
                    cycle_time_sec=request.cycle_time_sec,
                    defects=request.defects or [],
                    lot_number=request.lot_number
                )

                return {
                    "record": record,
                    "message": "Production recorded successfully"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to record production: {str(e)}")

        @self.router.get("/production/summary")
        async def get_production_summary(
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
        ) -> ProductionSummaryResponse:
            """
            Get production summary for period

            Args:
                start_date: Period start (default: 24 hours ago)
                end_date: Period end (default: now)

            Returns:
                Production metrics and KPIs
            """
            try:
                if not start_date:
                    start_date = datetime.now() - timedelta(hours=24)
                if not end_date:
                    end_date = datetime.now()

                summary = self.mes_service.get_production_summary(start_date, end_date)
                return ProductionSummaryResponse(**summary)

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get production summary: {str(e)}")

        # ====================================================================
        # Material Management
        # ====================================================================

        @self.router.post("/materials/receive")
        async def receive_material(request: ReceiveMaterialRequest):
            """
            Receive material lot

            Records incoming material with lot tracking.

            Args:
                request: Material receipt details

            Returns:
                Created material lot with generated lot ID
            """
            try:
                lot = self.mes_service.receive_material(
                    material_id=request.material_id,
                    material_name=request.material_name,
                    quantity=request.quantity,
                    unit=request.unit,
                    supplier=request.supplier,
                    expiry_date=request.expiry_date
                )

                return {
                    "lot": lot,
                    "message": "Material received successfully"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to receive material: {str(e)}")

        @self.router.post("/materials/{lot_id}/consume")
        async def consume_material(lot_id: str, request: ConsumeMaterialRequest):
            """
            Consume material from lot

            Records material consumption for work order.

            Args:
                lot_id: Material lot ID
                request: Consumption details

            Returns:
                Updated lot with remaining quantity
            """
            try:
                lot = self.mes_service.consume_material(
                    lot_id=lot_id,
                    wo_id=request.wo_id,
                    quantity=request.quantity
                )

                if not lot:
                    raise HTTPException(status_code=404, detail=f"Material lot {lot_id} not found")

                return {
                    "lot": lot,
                    "remaining_quantity": lot.quantity - lot.consumed_quantity,
                    "message": "Material consumed successfully"
                }

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to consume material: {str(e)}")

        @self.router.get("/materials/traceability")
        async def get_material_traceability(
            wo_id: Optional[str] = None,
            lot_id: Optional[str] = None
        ):
            """
            Get material traceability

            Trace materials used in work order or all work orders using a lot.

            Args:
                wo_id: Work order ID
                lot_id: Material lot ID

            Returns:
                Traceability records
            """
            try:
                if wo_id:
                    traceability = self.mes_service.get_material_traceability(wo_id=wo_id)
                elif lot_id:
                    traceability = self.mes_service.get_material_traceability(lot_id=lot_id)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Must provide either wo_id or lot_id"
                    )

                return {
                    "traceability": traceability,
                    "total_records": len(traceability)
                }

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get traceability: {str(e)}")

        @self.router.get("/materials")
        async def get_materials(
            status: Optional[str] = None,
            limit: int = Query(50, ge=1, le=500)
        ):
            """
            Get material lots

            Args:
                status: Filter by status (available/in_use/depleted)
                limit: Maximum number of results

            Returns:
                List of material lots
            """
            try:
                lots = list(self.mes_service.material_lots.values())

                # Filter by status if provided
                if status:
                    lots = [lot for lot in lots if lot.status == status]

                # Apply limit
                lots = lots[:limit]

                return {
                    "materials": lots,
                    "total": len(lots),
                    "filters": {"status": status}
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get materials: {str(e)}")

        # ====================================================================
        # OEE & Metrics
        # ====================================================================

        @self.router.post("/oee/calculate", response_model=OEEResponse)
        async def calculate_oee(request: OEERequest):
            """
            Calculate Overall Equipment Effectiveness (OEE)

            OEE = Availability × Performance × Quality

            Args:
                request: OEE calculation parameters

            Returns:
                OEE metrics with breakdown
            """
            try:
                result = self.mes_service.calculate_oee(
                    equipment_id=request.equipment_id,
                    period_start=request.period_start,
                    period_end=request.period_end,
                    ideal_cycle_time_sec=request.ideal_cycle_time_sec
                )

                return OEEResponse(**result)

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to calculate OEE: {str(e)}")

        @self.router.get("/quality/metrics")
        async def get_quality_metrics():
            """
            Get quality metrics

            Returns:
            - First Pass Yield (FPY)
            - Defect rate
            - Top defect types
            - Quality trends
            """
            try:
                metrics = self.mes_service.get_quality_metrics()
                return metrics

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get quality metrics: {str(e)}")

        # ====================================================================
        # Health & Status
        # ====================================================================

        @self.router.get("/health")
        async def health_check():
            """
            Health check endpoint

            Returns service status and statistics
            """
            return {
                "status": "healthy",
                "service": "Manufacturing Execution System",
                "version": "7.3.0",
                "standard": "ISA-95",
                "statistics": {
                    "total_work_orders": len(self.mes_service.work_orders),
                    "total_production_records": len(self.mes_service.production_records),
                    "total_material_lots": len(self.mes_service.material_lots),
                    "active_work_orders": sum(
                        1 for wo in self.mes_service.work_orders.values()
                        if wo.status in [WorkOrderStatus.RELEASED, WorkOrderStatus.IN_PROGRESS]
                    )
                }
            }


def get_mes_router(mes_service: Optional[MESService] = None) -> APIRouter:
    """
    Factory function to create MES router

    Args:
        mes_service: Optional MES service instance

    Returns:
        Configured APIRouter
    """
    router_instance = MESRouter(mes_service=mes_service)
    return router_instance.router
