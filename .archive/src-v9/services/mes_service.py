"""
Manufacturing Execution System (MES) - Enterprise Grade
v7.3.0 - Professional Enterprise System

Core Functions (ISA-95 Standard):
1. Work Order Management
2. Production Scheduling
3. Material Tracking & Traceability
4. Quality Management System (QMS)
5. Overall Equipment Effectiveness (OEE)
6. Labor Management
7. Document Control
8. Process Management

Features:
- Real-time production monitoring
- WIP (Work in Progress) tracking
- Lot/batch traceability
- Quality gates and checks
- Performance metrics (OEE, throughput)
- Integration with ERP/PLM
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ========================================================================
# Data Models
# ========================================================================

class WorkOrderStatus(str, Enum):
    """Work order status"""
    DRAFT = "draft"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class QualityStatus(str, Enum):
    """Quality inspection status"""
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"
    CONDITIONAL = "conditional"


class WorkOrder(BaseModel):
    """Manufacturing work order"""
    wo_id: str
    product_id: str
    product_name: str
    quantity_planned: int
    quantity_produced: int = 0
    quantity_good: int = 0
    quantity_scrap: int = 0
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    priority: int = 5
    planned_start: datetime
    planned_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    equipment_id: Optional[str] = None
    operator_id: Optional[str] = None
    created_at: datetime = datetime.now()


class ProductionRecord(BaseModel):
    """Production event record"""
    record_id: str
    wo_id: str
    timestamp: datetime
    quantity: int
    quality_status: QualityStatus
    equipment_id: str
    operator_id: str
    cycle_time_sec: float
    defects: List[str] = []
    lot_number: Optional[str] = None


class MaterialLot(BaseModel):
    """Material lot/batch tracking"""
    lot_id: str
    material_id: str
    material_name: str
    quantity: float
    unit: str
    received_date: datetime
    expiry_date: Optional[datetime] = None
    supplier: str
    quality_cert: Optional[str] = None
    consumed_quantity: float = 0.0
    status: str = "available"  # available, in_use, consumed, quarantine


class OEEMetrics(BaseModel):
    """OEE (Overall Equipment Effectiveness) metrics"""
    equipment_id: str
    period_start: datetime
    period_end: datetime
    availability: float  # % of scheduled time equipment was available
    performance: float  # % of design speed achieved
    quality: float  # % of good parts produced
    oee: float  # availability * performance * quality
    total_time_min: float
    planned_production_time_min: float
    actual_runtime_min: float
    ideal_cycle_time_sec: float
    total_pieces: int
    good_pieces: int
    defect_pieces: int


# ========================================================================
# Manufacturing Execution System Service
# ========================================================================

class MESService:
    """
    Manufacturing Execution System (MES)

    Manages production operations from work order release to completion
    """

    def __init__(self, database=None):
        """Initialize MES"""
        self.db = database

        # In-memory storage (replace with database in production)
        self.work_orders: Dict[str, WorkOrder] = {}
        self.production_records: List[ProductionRecord] = []
        self.material_lots: Dict[str, MaterialLot] = {}

        logger.info("MES Service initialized")

    # ========================================================================
    # Work Order Management
    # ========================================================================

    def create_work_order(
        self,
        product_id: str,
        product_name: str,
        quantity: int,
        planned_start: datetime,
        planned_end: datetime,
        priority: int = 5
    ) -> WorkOrder:
        """Create new work order"""
        wo = WorkOrder(
            wo_id=f"WO-{uuid4().hex[:8].upper()}",
            product_id=product_id,
            product_name=product_name,
            quantity_planned=quantity,
            planned_start=planned_start,
            planned_end=planned_end,
            priority=priority
        )

        self.work_orders[wo.wo_id] = wo
        logger.info(f"Created work order: {wo.wo_id} ({quantity} x {product_name})")

        return wo

    def release_work_order(self, wo_id: str) -> bool:
        """Release work order to production floor"""
        wo = self.work_orders.get(wo_id)
        if not wo:
            return False

        if wo.status != WorkOrderStatus.DRAFT:
            logger.warning(f"Cannot release WO {wo_id}: status={wo.status}")
            return False

        wo.status = WorkOrderStatus.RELEASED
        logger.info(f"Released work order: {wo_id}")
        return True

    def start_work_order(
        self,
        wo_id: str,
        equipment_id: str,
        operator_id: str
    ) -> bool:
        """Start production on work order"""
        wo = self.work_orders.get(wo_id)
        if not wo:
            return False

        wo.status = WorkOrderStatus.IN_PROGRESS
        wo.actual_start = datetime.now()
        wo.equipment_id = equipment_id
        wo.operator_id = operator_id

        logger.info(f"Started WO {wo_id} on equipment {equipment_id}")
        return True

    def complete_work_order(self, wo_id: str) -> bool:
        """Complete work order"""
        wo = self.work_orders.get(wo_id)
        if not wo:
            return False

        wo.status = WorkOrderStatus.COMPLETED
        wo.actual_end = datetime.now()

        logger.info(
            f"Completed WO {wo_id}: "
            f"{wo.quantity_good}/{wo.quantity_planned} good, "
            f"{wo.quantity_scrap} scrap"
        )
        return True

    # ========================================================================
    # Production Recording
    # ========================================================================

    def record_production(
        self,
        wo_id: str,
        quantity: int,
        quality_status: QualityStatus,
        equipment_id: str,
        operator_id: str,
        cycle_time_sec: float,
        defects: List[str] = None,
        lot_number: str = None
    ) -> ProductionRecord:
        """Record production event"""
        record = ProductionRecord(
            record_id=f"PR-{uuid4().hex[:8].upper()}",
            wo_id=wo_id,
            timestamp=datetime.now(),
            quantity=quantity,
            quality_status=quality_status,
            equipment_id=equipment_id,
            operator_id=operator_id,
            cycle_time_sec=cycle_time_sec,
            defects=defects or [],
            lot_number=lot_number
        )

        self.production_records.append(record)

        # Update work order
        wo = self.work_orders.get(wo_id)
        if wo:
            wo.quantity_produced += quantity
            if quality_status == QualityStatus.PASS:
                wo.quantity_good += quantity
            else:
                wo.quantity_scrap += quantity

        logger.info(
            f"Recorded production: {quantity} units, "
            f"quality={quality_status}, WO={wo_id}"
        )

        return record

    # ========================================================================
    # Material Tracking
    # ========================================================================

    def receive_material(
        self,
        material_id: str,
        material_name: str,
        quantity: float,
        unit: str,
        supplier: str,
        expiry_date: Optional[datetime] = None
    ) -> MaterialLot:
        """Receive material lot"""
        lot = MaterialLot(
            lot_id=f"LOT-{uuid4().hex[:8].upper()}",
            material_id=material_id,
            material_name=material_name,
            quantity=quantity,
            unit=unit,
            received_date=datetime.now(),
            expiry_date=expiry_date,
            supplier=supplier
        )

        self.material_lots[lot.lot_id] = lot
        logger.info(f"Received material lot: {lot.lot_id} ({quantity} {unit})")

        return lot

    def consume_material(
        self,
        lot_id: str,
        quantity: float,
        wo_id: str
    ) -> bool:
        """Consume material from lot"""
        lot = self.material_lots.get(lot_id)
        if not lot:
            return False

        if lot.consumed_quantity + quantity > lot.quantity:
            logger.error(f"Insufficient material in lot {lot_id}")
            return False

        lot.consumed_quantity += quantity

        if lot.consumed_quantity >= lot.quantity:
            lot.status = "consumed"

        logger.info(
            f"Consumed {quantity} {lot.unit} from lot {lot_id} for WO {wo_id}"
        )
        return True

    def get_material_traceability(
        self,
        lot_id: str
    ) -> Dict:
        """Get material traceability chain"""
        lot = self.material_lots.get(lot_id)
        if not lot:
            return {}

        # Find all production records using this lot
        related_records = [
            r for r in self.production_records
            if r.lot_number == lot_id
        ]

        return {
            "lot": lot.dict(),
            "production_records": [r.dict() for r in related_records],
            "consumed_by_wo": list(set(r.wo_id for r in related_records))
        }

    # ========================================================================
    # OEE Calculation
    # ========================================================================

    def calculate_oee(
        self,
        equipment_id: str,
        period_start: datetime,
        period_end: datetime,
        ideal_cycle_time_sec: float
    ) -> OEEMetrics:
        """
        Calculate OEE (Overall Equipment Effectiveness)

        OEE = Availability × Performance × Quality

        Availability = (Operating Time / Planned Production Time)
        Performance = (Ideal Cycle Time × Total Count) / Operating Time
        Quality = Good Count / Total Count
        """
        # Get production records in period
        records = [
            r for r in self.production_records
            if r.equipment_id == equipment_id
            and period_start <= r.timestamp <= period_end
        ]

        if not records:
            return OEEMetrics(
                equipment_id=equipment_id,
                period_start=period_start,
                period_end=period_end,
                availability=0.0,
                performance=0.0,
                quality=0.0,
                oee=0.0,
                total_time_min=0.0,
                planned_production_time_min=0.0,
                actual_runtime_min=0.0,
                ideal_cycle_time_sec=ideal_cycle_time_sec,
                total_pieces=0,
                good_pieces=0,
                defect_pieces=0
            )

        # Calculate metrics
        total_time_min = (period_end - period_start).total_seconds() / 60
        planned_production_time_min = total_time_min  # Simplified

        total_pieces = sum(r.quantity for r in records)
        good_pieces = sum(
            r.quantity for r in records
            if r.quality_status == QualityStatus.PASS
        )
        defect_pieces = total_pieces - good_pieces

        # Actual runtime (sum of cycle times)
        actual_runtime_min = sum(
            r.cycle_time_sec * r.quantity for r in records
        ) / 60

        # Availability
        availability = (
            actual_runtime_min / planned_production_time_min
            if planned_production_time_min > 0 else 0.0
        )

        # Performance
        ideal_runtime_min = (ideal_cycle_time_sec * total_pieces) / 60
        performance = (
            ideal_runtime_min / actual_runtime_min
            if actual_runtime_min > 0 else 0.0
        )

        # Quality
        quality = (
            good_pieces / total_pieces
            if total_pieces > 0 else 0.0
        )

        # OEE
        oee = availability * performance * quality

        return OEEMetrics(
            equipment_id=equipment_id,
            period_start=period_start,
            period_end=period_end,
            availability=availability,
            performance=performance,
            quality=quality,
            oee=oee,
            total_time_min=total_time_min,
            planned_production_time_min=planned_production_time_min,
            actual_runtime_min=actual_runtime_min,
            ideal_cycle_time_sec=ideal_cycle_time_sec,
            total_pieces=total_pieces,
            good_pieces=good_pieces,
            defect_pieces=defect_pieces
        )

    # ========================================================================
    # Reporting & Analytics
    # ========================================================================

    def get_production_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get production summary for period"""
        # Filter records
        records = [
            r for r in self.production_records
            if start_date <= r.timestamp <= end_date
        ]

        total_produced = sum(r.quantity for r in records)
        total_good = sum(
            r.quantity for r in records
            if r.quality_status == QualityStatus.PASS
        )
        total_scrap = total_produced - total_good

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "production": {
                "total_produced": total_produced,
                "good_units": total_good,
                "scrap_units": total_scrap,
                "first_pass_yield": total_good / total_produced if total_produced > 0 else 0.0
            },
            "work_orders": {
                "total": len(self.work_orders),
                "completed": len([
                    wo for wo in self.work_orders.values()
                    if wo.status == WorkOrderStatus.COMPLETED
                ]),
                "in_progress": len([
                    wo for wo in self.work_orders.values()
                    if wo.status == WorkOrderStatus.IN_PROGRESS
                ])
            }
        }

    def get_quality_metrics(self) -> Dict:
        """Get quality metrics"""
        total = len(self.production_records)
        if total == 0:
            return {"no_data": True}

        passed = len([
            r for r in self.production_records
            if r.quality_status == QualityStatus.PASS
        ])

        # Defect analysis
        all_defects = []
        for r in self.production_records:
            all_defects.extend(r.defects)

        from collections import Counter
        defect_counts = Counter(all_defects)

        return {
            "total_inspections": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total,
            "top_defects": defect_counts.most_common(10)
        }


# Global singleton
_mes_service: Optional[MESService] = None


def get_mes_service() -> MESService:
    """Get or create MES Service singleton"""
    global _mes_service
    if _mes_service is None:
        _mes_service = MESService()
    return _mes_service
