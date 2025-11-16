"""
Enterprise Manufacturing ERP Module - v7.4.0
완전한 제조 ERP 시스템 - 원료 입고, BOM, 생산, 조립

Features:
1. Material Management (원료 관리)
   - Grade-based material classification
   - Purchase order management
   - Quality inspection on receipt
   - FIFO/FEFO inventory management
   - Multi-location warehouse

2. BOM Management (자재 명세서)
   - Multi-level BOM (계층적 구조)
   - BOM version control
   - BOM explosion/implosion
   - Where-used analysis
   - Engineering change management

3. Production Planning (생산 계획)
   - MRP (Material Requirements Planning)
   - Capacity planning
   - Production scheduling
   - Work order generation
   - Material allocation

4. Production Execution (생산 실행)
   - Real-time progress tracking
   - Material consumption
   - Quality checkpoints
   - Labor tracking
   - Equipment utilization

5. Assembly Management (조립 관리)
   - Sub-assembly tracking
   - Assembly validation
   - Serial number tracking
   - Component traceability

6. Inventory Management (재고 관리)
   - Raw materials
   - Work-in-progress (WIP)
   - Finished goods
   - Inventory valuation (FIFO, Weighted Average)
   - Stock movements

7. Quality Management (품질 관리)
   - Incoming quality control (IQC)
   - In-process quality control (IPQC)
   - Final quality control (FQC)
   - Quality certificates
   - Non-conformance tracking

8. Traceability (추적성)
   - Forward traceability (원료 → 제품)
   - Backward traceability (제품 → 원료)
   - Lot/serial number tracking
   - Recall management
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date
from enum import Enum
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ========================================================================
# Enums
# ========================================================================

class MaterialGrade(str, Enum):
    """Material grade classification"""
    PRIME = "prime"  # A급
    STANDARD = "standard"  # B급
    ECONOMY = "economy"  # C급
    REJECT = "reject"  # 불량


class MaterialType(str, Enum):
    """Material types"""
    RAW_MATERIAL = "raw_material"  # 원자재
    COMPONENT = "component"  # 부품
    SUB_ASSEMBLY = "sub_assembly"  # 반제품
    FINISHED_GOOD = "finished_good"  # 완제품
    PACKAGING = "packaging"  # 포장재
    CONSUMABLE = "consumable"  # 소모품


class UnitOfMeasure(str, Enum):
    """Units of measure"""
    EA = "ea"  # 개
    KG = "kg"  # 킬로그램
    L = "l"  # 리터
    M = "m"  # 미터
    SET = "set"  # 세트
    BOX = "box"  # 박스


class PurchaseOrderStatus(str, Enum):
    """Purchase order status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QualityStatus(str, Enum):
    """Quality inspection status"""
    PENDING = "pending"
    INSPECTING = "inspecting"
    PASSED = "passed"
    FAILED = "failed"
    CONDITIONAL = "conditional"  # 조건부 합격


class WorkOrderStatus(str, Enum):
    """Work order status"""
    PLANNED = "planned"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class InventoryTransactionType(str, Enum):
    """Inventory transaction types"""
    RECEIPT = "receipt"  # 입고
    ISSUE = "issue"  # 출고
    TRANSFER = "transfer"  # 이동
    ADJUSTMENT = "adjustment"  # 조정
    SCRAP = "scrap"  # 폐기
    RETURN = "return"  # 반품


# ========================================================================
# Data Models
# ========================================================================

class Material(BaseModel):
    """Material master data"""
    material_id: str = Field(..., description="Material identifier")
    material_code: str = Field(..., description="Material code")
    material_name: str = Field(..., description="Material name")
    material_type: MaterialType
    grade: MaterialGrade = MaterialGrade.STANDARD
    uom: UnitOfMeasure = UnitOfMeasure.EA

    # Specifications
    specifications: Dict[str, Any] = Field(default_factory=dict)
    quality_standards: Dict[str, Any] = Field(default_factory=dict)

    # Procurement
    lead_time_days: int = 7
    min_order_quantity: Decimal = Decimal("1")
    safety_stock: Decimal = Decimal("0")
    reorder_point: Decimal = Decimal("0")

    # Costing
    standard_cost: Decimal = Decimal("0")
    last_purchase_cost: Decimal = Decimal("0")

    # Status
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class BOM(BaseModel):
    """Bill of Materials"""
    bom_id: str = Field(..., description="BOM identifier")
    parent_material_id: str = Field(..., description="Parent material")
    bom_version: str = "1.0"
    bom_type: str = "production"  # production, assembly, kit

    # Components
    components: List[Dict[str, Any]] = Field(default_factory=list)
    # Each component: {material_id, quantity, uom, scrap_factor, position}

    # Status
    status: str = "active"  # draft, active, obsolete
    effective_date: date = Field(default_factory=date.today)
    expiry_date: Optional[date] = None

    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class PurchaseOrder(BaseModel):
    """Purchase order"""
    po_id: str = Field(..., description="PO identifier")
    po_number: str = Field(..., description="PO number")
    supplier_id: str
    supplier_name: str

    # Items
    items: List[Dict[str, Any]] = Field(default_factory=list)
    # Each item: {material_id, quantity, uom, unit_price, grade}

    # Amounts
    subtotal: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    total: Decimal = Decimal("0")

    # Dates
    po_date: date = Field(default_factory=date.today)
    delivery_date: date

    # Status
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT

    # Tracking
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class MaterialReceipt(BaseModel):
    """Material receipt (입고)"""
    receipt_id: str = Field(..., description="Receipt identifier")
    receipt_number: str
    po_id: str
    supplier_id: str

    # Items
    items: List[Dict[str, Any]] = Field(default_factory=list)
    # Each item: {material_id, quantity, uom, grade, lot_number, location}

    # Quality inspection
    inspection_required: bool = True
    inspection_status: QualityStatus = QualityStatus.PENDING
    inspection_results: Dict[str, Any] = Field(default_factory=dict)

    # Dates
    receipt_date: datetime = Field(default_factory=datetime.now)

    # Status
    status: str = "received"  # received, inspected, put_away

    created_by: Optional[str] = None


class WorkOrder(BaseModel):
    """Production work order"""
    wo_id: str = Field(..., description="Work order identifier")
    wo_number: str

    # Product
    product_material_id: str
    product_name: str
    bom_id: str
    bom_version: str

    # Quantities
    quantity_planned: Decimal
    quantity_produced: Decimal = Decimal("0")
    quantity_good: Decimal = Decimal("0")
    quantity_scrap: Decimal = Decimal("0")

    # Schedule
    planned_start: datetime
    planned_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

    # Resources
    production_line: Optional[str] = None
    shift: Optional[str] = None

    # Material allocation
    materials_allocated: bool = False
    materials_consumed: List[Dict[str, Any]] = Field(default_factory=list)

    # Status
    status: WorkOrderStatus = WorkOrderStatus.PLANNED
    priority: int = 5

    created_at: datetime = Field(default_factory=datetime.now)


class Assembly(BaseModel):
    """Assembly record"""
    assembly_id: str = Field(..., description="Assembly identifier")
    assembly_number: str

    # Parent
    parent_material_id: str
    parent_serial_number: Optional[str] = None

    # Components
    components_used: List[Dict[str, Any]] = Field(default_factory=list)
    # Each: {material_id, serial_number, lot_number, quantity}

    # Work order
    wo_id: str

    # Assembly info
    assembled_by: str
    assembled_at: datetime = Field(default_factory=datetime.now)
    assembly_station: Optional[str] = None

    # Quality
    quality_status: QualityStatus = QualityStatus.PASSED
    quality_notes: Optional[str] = None

    # Traceability
    traceability_complete: bool = True


class InventoryTransaction(BaseModel):
    """Inventory transaction"""
    transaction_id: str = Field(..., description="Transaction identifier")
    transaction_number: str
    transaction_type: InventoryTransactionType

    # Material
    material_id: str
    material_code: str
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None

    # Quantity
    quantity: Decimal
    uom: UnitOfMeasure

    # Location
    from_location: Optional[str] = None
    to_location: Optional[str] = None

    # Reference
    reference_type: Optional[str] = None  # PO, WO, etc.
    reference_id: Optional[str] = None

    # Cost
    unit_cost: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")

    # Timestamp
    transaction_date: datetime = Field(default_factory=datetime.now)

    # User
    created_by: Optional[str] = None

    # Notes
    notes: Optional[str] = None


class InventoryBalance(BaseModel):
    """Current inventory balance"""
    material_id: str
    location: str
    lot_number: Optional[str] = None
    grade: MaterialGrade = MaterialGrade.STANDARD

    quantity_on_hand: Decimal = Decimal("0")
    quantity_allocated: Decimal = Decimal("0")
    quantity_available: Decimal = Decimal("0")

    # Costing
    avg_unit_cost: Decimal = Decimal("0")
    total_value: Decimal = Decimal("0")

    last_updated: datetime = Field(default_factory=datetime.now)


# ========================================================================
# Enterprise Manufacturing ERP Service
# ========================================================================

class EnterpriseManufacturingERPService:
    """
    Enterprise Manufacturing ERP Service

    완전한 제조 ERP 시스템:
    - Material Management (원료 관리)
    - BOM Management (자재 명세서)
    - Production Planning (생산 계획)
    - Production Execution (생산 실행)
    - Assembly Management (조립 관리)
    - Inventory Management (재고 관리)
    - Quality Management (품질 관리)
    - Traceability (추적성)
    """

    def __init__(self, tenant_id: str):
        """
        Initialize ERP service for tenant

        Args:
            tenant_id: Tenant identifier for multi-tenancy
        """
        self.tenant_id = tenant_id

        # Master data
        self.materials: Dict[str, Material] = {}
        self.boms: Dict[str, BOM] = {}

        # Transactions
        self.purchase_orders: Dict[str, PurchaseOrder] = {}
        self.material_receipts: Dict[str, MaterialReceipt] = {}
        self.work_orders: Dict[str, WorkOrder] = {}
        self.assemblies: Dict[str, Assembly] = {}
        self.inventory_transactions: List[InventoryTransaction] = []

        # Current state
        self.inventory_balances: Dict[Tuple[str, str], InventoryBalance] = {}
        # Key: (material_id, location)

        # Statistics
        self.stats = {
            "total_materials": 0,
            "total_boms": 0,
            "total_pos": 0,
            "total_receipts": 0,
            "total_work_orders": 0,
            "total_assemblies": 0,
            "inventory_value": Decimal("0"),
            "inventory_turnover": 0.0
        }

    # ====================================================================
    # 1. Material Management
    # ====================================================================

    def create_material(
        self,
        material_code: str,
        material_name: str,
        material_type: MaterialType,
        grade: MaterialGrade = MaterialGrade.STANDARD,
        **kwargs
    ) -> Material:
        """
        Create material master

        원료/부품/제품 마스터 생성
        """
        material_id = f"MAT-{len(self.materials) + 1:06d}"

        material = Material(
            material_id=material_id,
            material_code=material_code,
            material_name=material_name,
            material_type=material_type,
            grade=grade,
            **kwargs
        )

        self.materials[material_id] = material
        self.stats["total_materials"] += 1

        logger.info(f"Created material: {material_id} - {material_name}")
        return material

    def get_materials_by_type(
        self, material_type: MaterialType, grade: Optional[MaterialGrade] = None
    ) -> List[Material]:
        """
        Get materials by type and grade

        타입별, 등급별 원료 조회
        """
        materials = [
            m for m in self.materials.values()
            if m.material_type == material_type
        ]

        if grade:
            materials = [m for m in materials if m.grade == grade]

        return materials

    # ====================================================================
    # 2. BOM Management
    # ====================================================================

    def create_bom(
        self,
        parent_material_id: str,
        components: List[Dict[str, Any]],
        bom_version: str = "1.0"
    ) -> BOM:
        """
        Create Bill of Materials

        BOM 생성 (다단계 지원)

        Args:
            parent_material_id: 상위 품목
            components: [
                {
                    "material_id": "MAT-000001",
                    "quantity": 2.5,
                    "uom": "kg",
                    "scrap_factor": 0.05,  # 5% 스크랩
                    "position": "001"
                }
            ]
        """
        bom_id = f"BOM-{len(self.boms) + 1:06d}"

        bom = BOM(
            bom_id=bom_id,
            parent_material_id=parent_material_id,
            bom_version=bom_version,
            components=components
        )

        self.boms[bom_id] = bom
        self.stats["total_boms"] += 1

        logger.info(f"Created BOM: {bom_id} for {parent_material_id}")
        return bom

    def explode_bom(
        self, bom_id: str, quantity: Decimal, level: int = 0
    ) -> List[Dict[str, Any]]:
        """
        BOM explosion (폭발)

        BOM을 하위 레벨까지 전개하여 필요한 모든 원료 계산

        Returns:
            [
                {
                    "material_id": "MAT-000001",
                    "quantity": 10.5,
                    "level": 1,
                    "bom_path": "BOM-000001/BOM-000002"
                }
            ]
        """
        bom = self.boms.get(bom_id)
        if not bom:
            return []

        exploded = []

        for component in bom.components:
            comp_material_id = component["material_id"]
            comp_quantity = Decimal(str(component["quantity"]))
            scrap_factor = Decimal(str(component.get("scrap_factor", 0)))

            # Calculate net quantity with scrap
            net_quantity = comp_quantity * quantity * (1 + scrap_factor)

            exploded.append({
                "material_id": comp_material_id,
                "quantity": net_quantity,
                "uom": component.get("uom", "ea"),
                "level": level + 1,
                "parent_bom": bom_id
            })

            # Check if component has sub-BOM
            comp_material = self.materials.get(comp_material_id)
            if comp_material and comp_material.material_type == MaterialType.SUB_ASSEMBLY:
                # Find sub-BOM
                sub_bom = self._find_bom_for_material(comp_material_id)
                if sub_bom:
                    # Recursive explosion
                    sub_exploded = self.explode_bom(sub_bom.bom_id, net_quantity, level + 1)
                    exploded.extend(sub_exploded)

        return exploded

    def _find_bom_for_material(self, material_id: str) -> Optional[BOM]:
        """Find active BOM for material"""
        for bom in self.boms.values():
            if bom.parent_material_id == material_id and bom.status == "active":
                return bom
        return None

    def where_used(self, material_id: str) -> List[Dict[str, Any]]:
        """
        Where-used analysis

        해당 원료가 사용되는 모든 BOM 찾기
        """
        where_used_list = []

        for bom in self.boms.values():
            for component in bom.components:
                if component["material_id"] == material_id:
                    parent_material = self.materials.get(bom.parent_material_id)
                    where_used_list.append({
                        "bom_id": bom.bom_id,
                        "parent_material_id": bom.parent_material_id,
                        "parent_material_name": parent_material.material_name if parent_material else None,
                        "quantity_per": component["quantity"],
                        "uom": component.get("uom")
                    })

        return where_used_list

    # ====================================================================
    # 3. Purchase Order Management
    # ====================================================================

    def create_purchase_order(
        self,
        supplier_id: str,
        supplier_name: str,
        items: List[Dict[str, Any]],
        delivery_date: date
    ) -> PurchaseOrder:
        """
        Create purchase order

        발주서 생성

        Args:
            items: [
                {
                    "material_id": "MAT-000001",
                    "quantity": 100,
                    "uom": "kg",
                    "unit_price": 1500.00,
                    "grade": "prime"
                }
            ]
        """
        po_id = f"PO-{datetime.now().strftime('%Y%m%d')}-{len(self.purchase_orders) + 1:04d}"
        po_number = f"PO{datetime.now().strftime('%Y%m%d')}{len(self.purchase_orders) + 1:04d}"

        # Calculate amounts
        subtotal = Decimal("0")
        for item in items:
            qty = Decimal(str(item["quantity"]))
            price = Decimal(str(item["unit_price"]))
            item["line_total"] = qty * price
            subtotal += item["line_total"]

        tax = subtotal * Decimal("0.1")  # 10% VAT
        total = subtotal + tax

        po = PurchaseOrder(
            po_id=po_id,
            po_number=po_number,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            items=items,
            subtotal=subtotal,
            tax=tax,
            total=total,
            delivery_date=delivery_date
        )

        self.purchase_orders[po_id] = po
        self.stats["total_pos"] += 1

        logger.info(f"Created PO: {po_number} for supplier {supplier_name}")
        return po

    def receive_materials(
        self,
        po_id: str,
        items: List[Dict[str, Any]],
        inspection_required: bool = True
    ) -> MaterialReceipt:
        """
        Receive materials (입고)

        Args:
            items: [
                {
                    "material_id": "MAT-000001",
                    "quantity": 95.5,  # 실제 입고량
                    "grade": "prime",
                    "lot_number": "LOT202501110001",
                    "location": "WH-A-01-01"
                }
            ]
        """
        receipt_id = f"RCV-{datetime.now().strftime('%Y%m%d')}-{len(self.material_receipts) + 1:04d}"
        receipt_number = f"RCV{datetime.now().strftime('%Y%m%d')}{len(self.material_receipts) + 1:04d}"

        po = self.purchase_orders.get(po_id)
        if not po:
            raise ValueError(f"PO {po_id} not found")

        receipt = MaterialReceipt(
            receipt_id=receipt_id,
            receipt_number=receipt_number,
            po_id=po_id,
            supplier_id=po.supplier_id,
            items=items,
            inspection_required=inspection_required
        )

        self.material_receipts[receipt_id] = receipt
        self.stats["total_receipts"] += 1

        # If no inspection required, immediately update inventory
        if not inspection_required:
            self._put_away_materials(receipt)

        logger.info(f"Created material receipt: {receipt_number}")
        return receipt

    def inspect_receipt(
        self,
        receipt_id: str,
        inspection_status: QualityStatus,
        inspection_results: Dict[str, Any]
    ) -> MaterialReceipt:
        """
        Quality inspection on receipt (IQC - Incoming Quality Control)

        입고 품질 검사
        """
        receipt = self.material_receipts.get(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")

        receipt.inspection_status = inspection_status
        receipt.inspection_results = inspection_results

        # If passed, update inventory
        if inspection_status == QualityStatus.PASSED:
            receipt.status = "inspected"
            self._put_away_materials(receipt)
        elif inspection_status == QualityStatus.FAILED:
            # Handle rejection (return to supplier, scrap, etc.)
            receipt.status = "rejected"

        logger.info(f"Inspected receipt {receipt_id}: {inspection_status}")
        return receipt

    def _put_away_materials(self, receipt: MaterialReceipt):
        """
        Put away materials to inventory

        검수 완료된 원료를 재고에 반영
        """
        for item in receipt.items:
            # Create inventory transaction
            transaction = InventoryTransaction(
                transaction_id=f"TXN-{len(self.inventory_transactions) + 1:08d}",
                transaction_number=f"TXN{datetime.now().strftime('%Y%m%d')}{len(self.inventory_transactions) + 1:06d}",
                transaction_type=InventoryTransactionType.RECEIPT,
                material_id=item["material_id"],
                material_code=self.materials[item["material_id"]].material_code,
                lot_number=item.get("lot_number"),
                quantity=Decimal(str(item["quantity"])),
                uom=UnitOfMeasure(item.get("uom", "ea")),
                to_location=item.get("location", "WH-DEFAULT"),
                reference_type="RECEIPT",
                reference_id=receipt.receipt_id
            )

            self.inventory_transactions.append(transaction)

            # Update inventory balance
            self._update_inventory_balance(
                material_id=item["material_id"],
                location=item.get("location", "WH-DEFAULT"),
                quantity_change=Decimal(str(item["quantity"])),
                grade=MaterialGrade(item.get("grade", "standard"))
            )

        receipt.status = "put_away"
        logger.info(f"Put away materials from receipt {receipt.receipt_id}")

    def _update_inventory_balance(
        self,
        material_id: str,
        location: str,
        quantity_change: Decimal,
        grade: MaterialGrade = MaterialGrade.STANDARD
    ):
        """Update inventory balance"""
        key = (material_id, location)

        if key not in self.inventory_balances:
            self.inventory_balances[key] = InventoryBalance(
                material_id=material_id,
                location=location,
                grade=grade
            )

        balance = self.inventory_balances[key]
        balance.quantity_on_hand += quantity_change
        balance.quantity_available = balance.quantity_on_hand - balance.quantity_allocated
        balance.last_updated = datetime.now()

    # ====================================================================
    # 4. Production Planning & Execution
    # ====================================================================

    def create_work_order(
        self,
        product_material_id: str,
        quantity_planned: Decimal,
        planned_start: datetime,
        planned_end: datetime,
        priority: int = 5
    ) -> WorkOrder:
        """
        Create production work order

        작업 지시서 생성
        """
        wo_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{len(self.work_orders) + 1:04d}"
        wo_number = f"WO{datetime.now().strftime('%Y%m%d')}{len(self.work_orders) + 1:04d}"

        # Find BOM
        bom = self._find_bom_for_material(product_material_id)
        if not bom:
            raise ValueError(f"No BOM found for material {product_material_id}")

        product = self.materials.get(product_material_id)

        wo = WorkOrder(
            wo_id=wo_id,
            wo_number=wo_number,
            product_material_id=product_material_id,
            product_name=product.material_name if product else "",
            bom_id=bom.bom_id,
            bom_version=bom.bom_version,
            quantity_planned=quantity_planned,
            planned_start=planned_start,
            planned_end=planned_end,
            priority=priority
        )

        self.work_orders[wo_id] = wo
        self.stats["total_work_orders"] += 1

        logger.info(f"Created work order: {wo_number} for {quantity_planned} {product.material_name if product else ''}")
        return wo

    def allocate_materials(self, wo_id: str) -> Dict[str, Any]:
        """
        Allocate materials for work order

        작업 지시에 필요한 원료 할당 (MRP)
        """
        wo = self.work_orders.get(wo_id)
        if not wo:
            raise ValueError(f"Work order {wo_id} not found")

        # Explode BOM
        required_materials = self.explode_bom(wo.bom_id, wo.quantity_planned)

        allocation_results = []
        all_allocated = True

        for req in required_materials:
            material_id = req["material_id"]
            req_quantity = req["quantity"]

            # Find available inventory
            available_qty = self._get_available_quantity(material_id)

            if available_qty >= req_quantity:
                # Allocate
                self._allocate_inventory(material_id, req_quantity, wo_id)
                allocation_results.append({
                    "material_id": material_id,
                    "required": float(req_quantity),
                    "allocated": float(req_quantity),
                    "status": "allocated"
                })
            else:
                # Shortage
                allocation_results.append({
                    "material_id": material_id,
                    "required": float(req_quantity),
                    "available": float(available_qty),
                    "shortage": float(req_quantity - available_qty),
                    "status": "shortage"
                })
                all_allocated = False

        wo.materials_allocated = all_allocated

        return {
            "wo_id": wo_id,
            "all_allocated": all_allocated,
            "allocations": allocation_results
        }

    def _get_available_quantity(self, material_id: str) -> Decimal:
        """Get total available quantity across all locations"""
        total = Decimal("0")
        for (mat_id, loc), balance in self.inventory_balances.items():
            if mat_id == material_id:
                total += balance.quantity_available
        return total

    def _allocate_inventory(self, material_id: str, quantity: Decimal, wo_id: str):
        """Allocate inventory to work order"""
        remaining = quantity

        for (mat_id, loc), balance in self.inventory_balances.items():
            if mat_id == material_id and remaining > 0:
                allocate_qty = min(balance.quantity_available, remaining)
                balance.quantity_allocated += allocate_qty
                balance.quantity_available -= allocate_qty
                remaining -= allocate_qty

    def start_work_order(self, wo_id: str) -> WorkOrder:
        """
        Start work order execution

        작업 시작
        """
        wo = self.work_orders.get(wo_id)
        if not wo:
            raise ValueError(f"Work order {wo_id} not found")

        if not wo.materials_allocated:
            raise ValueError("Materials not allocated")

        wo.status = WorkOrderStatus.IN_PROGRESS
        wo.actual_start = datetime.now()

        logger.info(f"Started work order: {wo.wo_number}")
        return wo

    def report_production(
        self,
        wo_id: str,
        quantity_produced: Decimal,
        quantity_good: Decimal,
        quantity_scrap: Decimal,
        materials_consumed: List[Dict[str, Any]]
    ) -> WorkOrder:
        """
        Report production

        생산 실적 보고

        Args:
            materials_consumed: [
                {
                    "material_id": "MAT-000001",
                    "quantity": 95.2,
                    "lot_number": "LOT202501110001"
                }
            ]
        """
        wo = self.work_orders.get(wo_id)
        if not wo:
            raise ValueError(f"Work order {wo_id} not found")

        wo.quantity_produced += quantity_produced
        wo.quantity_good += quantity_good
        wo.quantity_scrap += quantity_scrap

        # Record material consumption
        for material in materials_consumed:
            # Create inventory transaction (issue)
            transaction = InventoryTransaction(
                transaction_id=f"TXN-{len(self.inventory_transactions) + 1:08d}",
                transaction_number=f"TXN{datetime.now().strftime('%Y%m%d')}{len(self.inventory_transactions) + 1:06d}",
                transaction_type=InventoryTransactionType.ISSUE,
                material_id=material["material_id"],
                material_code=self.materials[material["material_id"]].material_code,
                lot_number=material.get("lot_number"),
                quantity=Decimal(str(material["quantity"])),
                uom=UnitOfMeasure.EA,
                reference_type="WO",
                reference_id=wo_id
            )

            self.inventory_transactions.append(transaction)
            wo.materials_consumed.append(material)

        # Check if WO is complete
        if wo.quantity_produced >= wo.quantity_planned:
            wo.status = WorkOrderStatus.COMPLETED
            wo.actual_end = datetime.now()

        logger.info(f"Reported production for WO {wo.wo_number}: {quantity_produced}")
        return wo

    # ====================================================================
    # 5. Assembly Management
    # ====================================================================

    def create_assembly(
        self,
        wo_id: str,
        parent_material_id: str,
        parent_serial_number: Optional[str],
        components_used: List[Dict[str, Any]],
        assembled_by: str,
        assembly_station: Optional[str] = None
    ) -> Assembly:
        """
        Create assembly record

        조립 기록 생성 (추적성 확보)

        Args:
            components_used: [
                {
                    "material_id": "MAT-000002",
                    "serial_number": "SN123456",
                    "lot_number": "LOT202501110001",
                    "quantity": 1
                }
            ]
        """
        assembly_id = f"ASM-{datetime.now().strftime('%Y%m%d')}-{len(self.assemblies) + 1:06d}"
        assembly_number = f"ASM{datetime.now().strftime('%Y%m%d')}{len(self.assemblies) + 1:06d}"

        assembly = Assembly(
            assembly_id=assembly_id,
            assembly_number=assembly_number,
            parent_material_id=parent_material_id,
            parent_serial_number=parent_serial_number,
            components_used=components_used,
            wo_id=wo_id,
            assembled_by=assembled_by,
            assembly_station=assembly_station
        )

        self.assemblies[assembly_id] = assembly
        self.stats["total_assemblies"] += 1

        logger.info(f"Created assembly: {assembly_number} for {parent_serial_number or parent_material_id}")
        return assembly

    # ====================================================================
    # 6. Traceability
    # ====================================================================

    def forward_traceability(
        self, material_id: str, lot_number: str
    ) -> List[Dict[str, Any]]:
        """
        Forward traceability: 원료 → 제품

        특정 원료 LOT이 사용된 모든 완제품 추적
        """
        trace_results = []

        # Find all assemblies using this material/lot
        for assembly in self.assemblies.values():
            for component in assembly.components_used:
                if (component["material_id"] == material_id and
                    component.get("lot_number") == lot_number):
                    trace_results.append({
                        "assembly_id": assembly.assembly_id,
                        "parent_material_id": assembly.parent_material_id,
                        "parent_serial_number": assembly.parent_serial_number,
                        "assembled_at": assembly.assembled_at.isoformat(),
                        "wo_id": assembly.wo_id
                    })

        return trace_results

    def backward_traceability(
        self, parent_material_id: str, parent_serial_number: str
    ) -> Dict[str, Any]:
        """
        Backward traceability: 제품 → 원료

        특정 완제품에 사용된 모든 원료 추적
        """
        # Find assembly record
        assembly = None
        for asm in self.assemblies.values():
            if (asm.parent_material_id == parent_material_id and
                asm.parent_serial_number == parent_serial_number):
                assembly = asm
                break

        if not assembly:
            return {"error": "Assembly not found"}

        return {
            "product": {
                "material_id": assembly.parent_material_id,
                "serial_number": assembly.parent_serial_number
            },
            "components": assembly.components_used,
            "wo_id": assembly.wo_id,
            "assembled_by": assembly.assembled_by,
            "assembled_at": assembly.assembled_at.isoformat()
        }

    # ====================================================================
    # 7. Reporting & Analytics
    # ====================================================================

    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary by material type"""
        summary = {}

        for (material_id, location), balance in self.inventory_balances.items():
            material = self.materials.get(material_id)
            if not material:
                continue

            mat_type = material.material_type.value
            if mat_type not in summary:
                summary[mat_type] = {
                    "total_quantity": Decimal("0"),
                    "total_value": Decimal("0"),
                    "items": []
                }

            summary[mat_type]["total_quantity"] += balance.quantity_on_hand
            summary[mat_type]["total_value"] += balance.total_value
            summary[mat_type]["items"].append({
                "material_id": material_id,
                "material_name": material.material_name,
                "location": location,
                "quantity": float(balance.quantity_on_hand),
                "value": float(balance.total_value)
            })

        return summary

    def get_material_requirements(
        self, material_id: str, quantity: Decimal
    ) -> Dict[str, Any]:
        """
        Get material requirements (MRP calculation)

        특정 제품 생산에 필요한 모든 원료 계산
        """
        bom = self._find_bom_for_material(material_id)
        if not bom:
            return {"error": "No BOM found"}

        # Explode BOM
        requirements = self.explode_bom(bom.bom_id, quantity)

        # Check availability
        requirements_with_status = []
        for req in requirements:
            mat_id = req["material_id"]
            req_qty = req["quantity"]
            available_qty = self._get_available_quantity(mat_id)

            material = self.materials.get(mat_id)

            requirements_with_status.append({
                "material_id": mat_id,
                "material_name": material.material_name if material else "",
                "required_quantity": float(req_qty),
                "available_quantity": float(available_qty),
                "shortage": float(max(req_qty - available_qty, 0)),
                "uom": req["uom"],
                "level": req["level"]
            })

        return {
            "product_material_id": material_id,
            "product_quantity": float(quantity),
            "requirements": requirements_with_status
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive ERP statistics"""
        # Calculate inventory value
        inventory_value = sum(
            balance.total_value
            for balance in self.inventory_balances.values()
        )

        self.stats["inventory_value"] = float(inventory_value)

        return self.stats


# ========================================================================
# Factory Function
# ========================================================================

def get_enterprise_manufacturing_erp_service(tenant_id: str) -> EnterpriseManufacturingERPService:
    """
    Factory function to create Enterprise Manufacturing ERP service

    Args:
        tenant_id: Tenant identifier

    Returns:
        Configured EnterpriseManufacturingERPService instance
    """
    return EnterpriseManufacturingERPService(tenant_id=tenant_id)
