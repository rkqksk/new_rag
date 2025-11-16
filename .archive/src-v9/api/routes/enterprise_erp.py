"""
Enterprise Manufacturing ERP API Routes - v7.4.0
완전한 제조 ERP API + Excel 템플릿 다운로드/업로드 기능
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
from decimal import Decimal
import io
import csv

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import pandas as pd

from src.services.enterprise_manufacturing_erp_service import (
    EnterpriseManufacturingERPService,
    MaterialType,
    MaterialGrade,
    UnitOfMeasure,
    PurchaseOrderStatus,
    QualityStatus,
    WorkOrderStatus,
    get_enterprise_manufacturing_erp_service
)


# ========================================================================
# Request/Response Models
# ========================================================================

class CreateMaterialRequest(BaseModel):
    """Request to create material"""
    material_code: str
    material_name: str
    material_type: MaterialType
    grade: MaterialGrade = MaterialGrade.STANDARD
    uom: UnitOfMeasure = UnitOfMeasure.EA
    specifications: Dict[str, Any] = Field(default_factory=dict)
    lead_time_days: int = 7
    standard_cost: float = 0.0


class CreateBOMRequest(BaseModel):
    """Request to create BOM"""
    parent_material_id: str
    components: List[Dict[str, Any]]
    bom_version: str = "1.0"


class CreatePORequest(BaseModel):
    """Request to create purchase order"""
    supplier_id: str
    supplier_name: str
    items: List[Dict[str, Any]]
    delivery_date: date


class ReceiveMaterialsRequest(BaseModel):
    """Request to receive materials"""
    po_id: str
    items: List[Dict[str, Any]]
    inspection_required: bool = True


class InspectReceiptRequest(BaseModel):
    """Request for quality inspection"""
    receipt_id: str
    inspection_status: QualityStatus
    inspection_results: Dict[str, Any]


class CreateWorkOrderRequest(BaseModel):
    """Request to create work order"""
    product_material_id: str
    quantity_planned: float
    planned_start: datetime
    planned_end: datetime
    priority: int = 5


class ReportProductionRequest(BaseModel):
    """Request to report production"""
    wo_id: str
    quantity_produced: float
    quantity_good: float
    quantity_scrap: float
    materials_consumed: List[Dict[str, Any]]


class CreateAssemblyRequest(BaseModel):
    """Request to create assembly"""
    wo_id: str
    parent_material_id: str
    parent_serial_number: Optional[str] = None
    components_used: List[Dict[str, Any]]
    assembled_by: str
    assembly_station: Optional[str] = None


# ========================================================================
# Excel Template Definitions
# ========================================================================

EXCEL_TEMPLATES = {
    "materials": {
        "columns": [
            "material_code",
            "material_name",
            "material_type",
            "grade",
            "uom",
            "lead_time_days",
            "standard_cost",
            "safety_stock",
            "reorder_point"
        ],
        "sample_data": [
            [
                "MAT-001",
                "PET Resin Prime",
                "raw_material",
                "prime",
                "kg",
                7,
                1500.00,
                1000,
                500
            ],
            [
                "MAT-002",
                "HDPE Resin Standard",
                "raw_material",
                "standard",
                "kg",
                7,
                1200.00,
                800,
                400
            ]
        ]
    },
    "boms": {
        "columns": [
            "parent_material_code",
            "component_material_code",
            "quantity",
            "uom",
            "scrap_factor",
            "position"
        ],
        "sample_data": [
            ["FG-001", "MAT-001", 0.95, "kg", 0.05, "001"],
            ["FG-001", "MAT-002", 0.03, "kg", 0.02, "002"]
        ]
    },
    "purchase_orders": {
        "columns": [
            "po_number",
            "supplier_id",
            "supplier_name",
            "material_code",
            "quantity",
            "uom",
            "unit_price",
            "grade",
            "delivery_date"
        ],
        "sample_data": [
            ["PO20250111001", "SUP-001", "Korea Plastics", "MAT-001", 1000, "kg", 1500.00, "prime", "2025-01-20"]
        ]
    },
    "material_receipts": {
        "columns": [
            "po_number",
            "material_code",
            "quantity",
            "uom",
            "grade",
            "lot_number",
            "location",
            "inspection_required"
        ],
        "sample_data": [
            ["PO20250111001", "MAT-001", 995.5, "kg", "prime", "LOT202501110001", "WH-A-01-01", "Y"]
        ]
    },
    "work_orders": {
        "columns": [
            "product_material_code",
            "quantity_planned",
            "planned_start",
            "planned_end",
            "priority",
            "production_line"
        ],
        "sample_data": [
            ["FG-001", 1000, "2025-01-15 08:00", "2025-01-15 17:00", 5, "LINE-01"]
        ]
    },
    "production_reports": {
        "columns": [
            "wo_number",
            "quantity_produced",
            "quantity_good",
            "quantity_scrap",
            "material_code",
            "consumed_quantity",
            "lot_number"
        ],
        "sample_data": [
            ["WO20250115001", 980, 970, 10, "MAT-001", 930.5, "LOT202501110001"]
        ]
    },
    "assemblies": {
        "columns": [
            "wo_number",
            "parent_material_code",
            "parent_serial_number",
            "component_material_code",
            "component_serial_number",
            "component_lot_number",
            "quantity",
            "assembled_by",
            "assembly_station"
        ],
        "sample_data": [
            ["WO20250115001", "FG-001", "SN123456", "MAT-001", None, "LOT202501110001", 1, "WORKER-01", "ASM-01"]
        ]
    }
}


# ========================================================================
# Router
# ========================================================================

class EnterpriseERPRouter:
    """Enterprise Manufacturing ERP API Router"""

    def __init__(self, tenant_id: str = "DEFAULT"):
        self.router = APIRouter(prefix="/enterprise-erp", tags=["Enterprise ERP"])
        self.tenant_id = tenant_id
        self.erp_services: Dict[str, EnterpriseManufacturingERPService] = {}
        self._setup_routes()

    def _get_erp_service(self, tenant_id: str) -> EnterpriseManufacturingERPService:
        """Get or create ERP service for tenant"""
        if tenant_id not in self.erp_services:
            self.erp_services[tenant_id] = get_enterprise_manufacturing_erp_service(tenant_id)
        return self.erp_services[tenant_id]

    def _setup_routes(self):
        """Setup API routes"""

        # ================================================================
        # Excel Template Download/Upload
        # ================================================================

        @self.router.get("/templates")
        async def list_templates():
            """
            List available Excel templates

            사용 가능한 Excel 템플릿 목록
            """
            return {
                "templates": list(EXCEL_TEMPLATES.keys()),
                "descriptions": {
                    "materials": "Material Master Data Template",
                    "boms": "Bill of Materials Template",
                    "purchase_orders": "Purchase Order Template",
                    "material_receipts": "Material Receipt Template",
                    "work_orders": "Work Order Template",
                    "production_reports": "Production Report Template",
                    "assemblies": "Assembly Record Template"
                }
            }

        @self.router.get("/templates/{template_name}/download")
        async def download_template(template_name: str):
            """
            Download Excel template

            Excel 템플릿 다운로드 (샘플 데이터 포함)

            Templates:
            - materials: Material master data
            - boms: Bill of Materials
            - purchase_orders: Purchase orders
            - material_receipts: Material receipts
            - work_orders: Work orders
            - production_reports: Production reports
            - assemblies: Assembly records
            """
            if template_name not in EXCEL_TEMPLATES:
                raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

            template = EXCEL_TEMPLATES[template_name]

            # Create DataFrame
            df = pd.DataFrame(template["sample_data"], columns=template["columns"])

            # Convert to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=template_name)

            output.seek(0)

            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={template_name}_template.xlsx"
                }
            )

        @self.router.get("/templates/{template_name}/download-csv")
        async def download_template_csv(template_name: str):
            """
            Download CSV template

            CSV 템플릿 다운로드
            """
            if template_name not in EXCEL_TEMPLATES:
                raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

            template = EXCEL_TEMPLATES[template_name]

            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(template["columns"])

            # Write sample data
            for row in template["sample_data"]:
                writer.writerow(row)

            # Convert to bytes
            csv_bytes = output.getvalue().encode('utf-8-sig')  # UTF-8 with BOM for Excel

            return StreamingResponse(
                io.BytesIO(csv_bytes),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={template_name}_template.csv"
                }
            )

        @self.router.post("/templates/{template_name}/upload")
        async def upload_template(
            template_name: str,
            tenant_id: str = Query("DEFAULT"),
            file: UploadFile = File(...)
        ):
            """
            Upload Excel/CSV data

            Excel/CSV 파일 업로드로 대량 데이터 등록

            Supports:
            - .xlsx (Excel)
            - .csv (CSV)

            Process:
            1. Parse file
            2. Validate data
            3. Import to database
            4. Return results
            """
            if template_name not in EXCEL_TEMPLATES:
                raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

            erp = self._get_erp_service(tenant_id)

            try:
                # Read file
                contents = await file.read()

                # Parse based on file type
                if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
                    df = pd.read_excel(io.BytesIO(contents))
                elif file.filename.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(contents))
                else:
                    raise HTTPException(status_code=400, detail="Unsupported file type. Use .xlsx or .csv")

                # Validate columns
                template = EXCEL_TEMPLATES[template_name]
                missing_cols = set(template["columns"]) - set(df.columns)
                if missing_cols:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing columns: {', '.join(missing_cols)}"
                    )

                # Process based on template type
                results = await self._process_template_upload(erp, template_name, df)

                return {
                    "template": template_name,
                    "total_rows": len(df),
                    "success_count": results["success_count"],
                    "error_count": results["error_count"],
                    "errors": results["errors"],
                    "message": f"Processed {len(df)} rows: {results['success_count']} succeeded, {results['error_count']} failed"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

        async def _process_template_upload(
            self, erp: EnterpriseManufacturingERPService, template_name: str, df: pd.DataFrame
        ) -> Dict[str, Any]:
            """Process uploaded template data"""
            success_count = 0
            error_count = 0
            errors = []

            for idx, row in df.iterrows():
                try:
                    if template_name == "materials":
                        erp.create_material(
                            material_code=str(row["material_code"]),
                            material_name=str(row["material_name"]),
                            material_type=MaterialType(row["material_type"]),
                            grade=MaterialGrade(row["grade"]),
                            uom=UnitOfMeasure(row["uom"]),
                            lead_time_days=int(row["lead_time_days"]),
                            standard_cost=Decimal(str(row["standard_cost"])),
                            safety_stock=Decimal(str(row.get("safety_stock", 0))),
                            reorder_point=Decimal(str(row.get("reorder_point", 0)))
                        )

                    elif template_name == "boms":
                        # Find parent material
                        parent_mat = None
                        for mat in erp.materials.values():
                            if mat.material_code == row["parent_material_code"]:
                                parent_mat = mat
                                break

                        component_mat = None
                        for mat in erp.materials.values():
                            if mat.material_code == row["component_material_code"]:
                                component_mat = mat
                                break

                        if parent_mat and component_mat:
                            # Check if BOM exists
                            existing_bom = erp._find_bom_for_material(parent_mat.material_id)
                            if existing_bom:
                                # Add component to existing BOM
                                existing_bom.components.append({
                                    "material_id": component_mat.material_id,
                                    "quantity": float(row["quantity"]),
                                    "uom": row["uom"],
                                    "scrap_factor": float(row.get("scrap_factor", 0)),
                                    "position": row.get("position", "001")
                                })
                            else:
                                # Create new BOM
                                erp.create_bom(
                                    parent_material_id=parent_mat.material_id,
                                    components=[{
                                        "material_id": component_mat.material_id,
                                        "quantity": float(row["quantity"]),
                                        "uom": row["uom"],
                                        "scrap_factor": float(row.get("scrap_factor", 0)),
                                        "position": row.get("position", "001")
                                    }]
                                )

                    elif template_name == "purchase_orders":
                        # Group items by PO number
                        po_number = str(row["po_number"])

                        # Find material
                        material = None
                        for mat in erp.materials.values():
                            if mat.material_code == row["material_code"]:
                                material = mat
                                break

                        if material:
                            # Check if PO exists
                            existing_po = None
                            for po in erp.purchase_orders.values():
                                if po.po_number == po_number:
                                    existing_po = po
                                    break

                            if existing_po:
                                # Add item to existing PO
                                existing_po.items.append({
                                    "material_id": material.material_id,
                                    "quantity": Decimal(str(row["quantity"])),
                                    "uom": row["uom"],
                                    "unit_price": Decimal(str(row["unit_price"])),
                                    "grade": row.get("grade", "standard")
                                })
                                existing_po.total_amount += Decimal(str(row["quantity"])) * Decimal(str(row["unit_price"]))
                            else:
                                # Create new PO
                                erp.create_purchase_order(
                                    supplier_id=str(row["supplier_id"]),
                                    supplier_name=str(row["supplier_name"]),
                                    items=[{
                                        "material_id": material.material_id,
                                        "quantity": Decimal(str(row["quantity"])),
                                        "uom": row["uom"],
                                        "unit_price": Decimal(str(row["unit_price"])),
                                        "grade": row.get("grade", "standard")
                                    }],
                                    delivery_date=pd.to_datetime(row["delivery_date"]).date()
                                )

                    elif template_name == "material_receipts":
                        # Find PO
                        po = None
                        for p in erp.purchase_orders.values():
                            if p.po_number == row["po_number"]:
                                po = p
                                break

                        # Find material
                        material = None
                        for mat in erp.materials.values():
                            if mat.material_code == row["material_code"]:
                                material = mat
                                break

                        if po and material:
                            inspection_required = str(row.get("inspection_required", "N")).upper() == "Y"

                            erp.receive_materials(
                                po_id=po.po_id,
                                items=[{
                                    "material_id": material.material_id,
                                    "quantity": Decimal(str(row["quantity"])),
                                    "uom": row["uom"],
                                    "grade": row.get("grade", "standard"),
                                    "lot_number": row.get("lot_number", f"LOT{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                                    "location": row.get("location", "WH-DEFAULT")
                                }],
                                inspection_required=inspection_required
                            )

                    elif template_name == "work_orders":
                        # Find product material
                        product_mat = None
                        for mat in erp.materials.values():
                            if mat.material_code == row["product_material_code"]:
                                product_mat = mat
                                break

                        if product_mat:
                            erp.create_work_order(
                                product_material_id=product_mat.material_id,
                                quantity_planned=Decimal(str(row["quantity_planned"])),
                                planned_start=pd.to_datetime(row["planned_start"]),
                                planned_end=pd.to_datetime(row["planned_end"]),
                                priority=int(row.get("priority", 5))
                            )

                    elif template_name == "production_reports":
                        # Find work order
                        wo = None
                        for w in erp.work_orders.values():
                            if w.wo_number == row["wo_number"]:
                                wo = w
                                break

                        # Find material
                        material = None
                        for mat in erp.materials.values():
                            if mat.material_code == row["material_code"]:
                                material = mat
                                break

                        if wo and material:
                            erp.report_production(
                                wo_id=wo.wo_id,
                                quantity_produced=Decimal(str(row["quantity_produced"])),
                                quantity_good=Decimal(str(row["quantity_good"])),
                                quantity_scrap=Decimal(str(row["quantity_scrap"])),
                                materials_consumed=[{
                                    "material_id": material.material_id,
                                    "quantity": Decimal(str(row["consumed_quantity"])),
                                    "lot_number": row.get("lot_number", "")
                                }]
                            )

                    elif template_name == "assemblies":
                        # Find work order
                        wo = None
                        for w in erp.work_orders.values():
                            if w.wo_number == row["wo_number"]:
                                wo = w
                                break

                        # Find parent material
                        parent_mat = None
                        for mat in erp.materials.values():
                            if mat.material_code == row["parent_material_code"]:
                                parent_mat = mat
                                break

                        # Find component material
                        component_mat = None
                        for mat in erp.materials.values():
                            if mat.material_code == row["component_material_code"]:
                                component_mat = mat
                                break

                        if wo and parent_mat and component_mat:
                            erp.create_assembly(
                                wo_id=wo.wo_id,
                                parent_material_id=parent_mat.material_id,
                                parent_serial_number=row.get("parent_serial_number"),
                                components_used=[{
                                    "material_id": component_mat.material_id,
                                    "serial_number": row.get("component_serial_number"),
                                    "lot_number": row.get("component_lot_number", ""),
                                    "quantity": Decimal(str(row["quantity"]))
                                }],
                                assembled_by=str(row["assembled_by"]),
                                assembly_station=row.get("assembly_station")
                            )

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append({
                        "row": idx + 2,  # +2 for header and 0-index
                        "error": str(e)
                    })

            return {
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:10]  # Return first 10 errors
            }

        # ================================================================
        # Material Management
        # ================================================================

        @self.router.post("/materials")
        async def create_material(request: CreateMaterialRequest, tenant_id: str = Query("DEFAULT")):
            """
            Create material master

            원료/부품 마스터 생성
            """
            try:
                erp = self._get_erp_service(tenant_id)

                material = erp.create_material(
                    material_code=request.material_code,
                    material_name=request.material_name,
                    material_type=request.material_type,
                    grade=request.grade,
                    uom=request.uom,
                    specifications=request.specifications,
                    lead_time_days=request.lead_time_days,
                    standard_cost=Decimal(str(request.standard_cost))
                )

                return material.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create material: {str(e)}")

        @self.router.get("/materials")
        async def get_materials(
            tenant_id: str = Query("DEFAULT"),
            material_type: Optional[MaterialType] = None,
            grade: Optional[MaterialGrade] = None
        ):
            """Get materials with filters"""
            try:
                erp = self._get_erp_service(tenant_id)

                if material_type:
                    materials = erp.get_materials_by_type(material_type, grade)
                else:
                    materials = list(erp.materials.values())

                return {
                    "materials": [m.dict() for m in materials],
                    "total": len(materials)
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get materials: {str(e)}")

        # ================================================================
        # BOM Management
        # ================================================================

        @self.router.post("/boms")
        async def create_bom(request: CreateBOMRequest, tenant_id: str = Query("DEFAULT")):
            """
            Create Bill of Materials

            BOM 생성
            """
            try:
                erp = self._get_erp_service(tenant_id)

                bom = erp.create_bom(
                    parent_material_id=request.parent_material_id,
                    components=request.components,
                    bom_version=request.bom_version
                )

                return bom.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create BOM: {str(e)}")

        @self.router.get("/boms/{bom_id}/explode")
        async def explode_bom(
            bom_id: str,
            quantity: float,
            tenant_id: str = Query("DEFAULT")
        ):
            """
            Explode BOM (BOM 폭발)

            Returns all required materials at all levels
            """
            try:
                erp = self._get_erp_service(tenant_id)

                exploded = erp.explode_bom(bom_id, Decimal(str(quantity)))

                return {
                    "bom_id": bom_id,
                    "quantity": quantity,
                    "requirements": exploded
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"BOM explosion failed: {str(e)}")

        @self.router.get("/materials/{material_id}/where-used")
        async def where_used(material_id: str, tenant_id: str = Query("DEFAULT")):
            """
            Where-used analysis

            해당 원료가 사용되는 모든 BOM 조회
            """
            try:
                erp = self._get_erp_service(tenant_id)

                where_used_list = erp.where_used(material_id)

                return {
                    "material_id": material_id,
                    "where_used": where_used_list,
                    "total": len(where_used_list)
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Where-used failed: {str(e)}")

        # ================================================================
        # Purchase Orders
        # ================================================================

        @self.router.post("/purchase-orders")
        async def create_purchase_order(request: CreatePORequest, tenant_id: str = Query("DEFAULT")):
            """
            Create purchase order

            발주서 생성
            """
            try:
                erp = self._get_erp_service(tenant_id)

                po = erp.create_purchase_order(
                    supplier_id=request.supplier_id,
                    supplier_name=request.supplier_name,
                    items=request.items,
                    delivery_date=request.delivery_date
                )

                return po.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create PO: {str(e)}")

        @self.router.post("/material-receipts")
        async def receive_materials(request: ReceiveMaterialsRequest, tenant_id: str = Query("DEFAULT")):
            """
            Receive materials (입고)

            원료 입고 처리
            """
            try:
                erp = self._get_erp_service(tenant_id)

                receipt = erp.receive_materials(
                    po_id=request.po_id,
                    items=request.items,
                    inspection_required=request.inspection_required
                )

                return receipt.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Material receipt failed: {str(e)}")

        @self.router.post("/quality-inspection")
        async def inspect_receipt(request: InspectReceiptRequest, tenant_id: str = Query("DEFAULT")):
            """
            Quality inspection (품질 검사)

            입고 품질 검사
            """
            try:
                erp = self._get_erp_service(tenant_id)

                receipt = erp.inspect_receipt(
                    receipt_id=request.receipt_id,
                    inspection_status=request.inspection_status,
                    inspection_results=request.inspection_results
                )

                return receipt.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Inspection failed: {str(e)}")

        # ================================================================
        # Work Orders
        # ================================================================

        @self.router.post("/work-orders")
        async def create_work_order(request: CreateWorkOrderRequest, tenant_id: str = Query("DEFAULT")):
            """
            Create work order

            작업 지시서 생성
            """
            try:
                erp = self._get_erp_service(tenant_id)

                wo = erp.create_work_order(
                    product_material_id=request.product_material_id,
                    quantity_planned=Decimal(str(request.quantity_planned)),
                    planned_start=request.planned_start,
                    planned_end=request.planned_end,
                    priority=request.priority
                )

                return wo.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create work order: {str(e)}")

        @self.router.post("/work-orders/{wo_id}/allocate")
        async def allocate_materials(wo_id: str, tenant_id: str = Query("DEFAULT")):
            """
            Allocate materials (MRP)

            작업 지시에 필요한 원료 할당
            """
            try:
                erp = self._get_erp_service(tenant_id)

                result = erp.allocate_materials(wo_id)

                return result

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Material allocation failed: {str(e)}")

        @self.router.post("/work-orders/{wo_id}/start")
        async def start_work_order(wo_id: str, tenant_id: str = Query("DEFAULT")):
            """
            Start work order

            작업 시작
            """
            try:
                erp = self._get_erp_service(tenant_id)

                wo = erp.start_work_order(wo_id)

                return wo.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to start work order: {str(e)}")

        @self.router.post("/production-reports")
        async def report_production(request: ReportProductionRequest, tenant_id: str = Query("DEFAULT")):
            """
            Report production

            생산 실적 보고
            """
            try:
                erp = self._get_erp_service(tenant_id)

                wo = erp.report_production(
                    wo_id=request.wo_id,
                    quantity_produced=Decimal(str(request.quantity_produced)),
                    quantity_good=Decimal(str(request.quantity_good)),
                    quantity_scrap=Decimal(str(request.quantity_scrap)),
                    materials_consumed=request.materials_consumed
                )

                return wo.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Production report failed: {str(e)}")

        # ================================================================
        # Assembly
        # ================================================================

        @self.router.post("/assemblies")
        async def create_assembly(request: CreateAssemblyRequest, tenant_id: str = Query("DEFAULT")):
            """
            Create assembly record

            조립 기록 생성 (추적성)
            """
            try:
                erp = self._get_erp_service(tenant_id)

                assembly = erp.create_assembly(
                    wo_id=request.wo_id,
                    parent_material_id=request.parent_material_id,
                    parent_serial_number=request.parent_serial_number,
                    components_used=request.components_used,
                    assembled_by=request.assembled_by,
                    assembly_station=request.assembly_station
                )

                return assembly.dict()

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Assembly creation failed: {str(e)}")

        # ================================================================
        # Traceability
        # ================================================================

        @self.router.get("/traceability/forward")
        async def forward_traceability(
            material_id: str,
            lot_number: str,
            tenant_id: str = Query("DEFAULT")
        ):
            """
            Forward traceability (원료 → 제품)

            특정 원료 LOT이 사용된 모든 제품 추적
            """
            try:
                erp = self._get_erp_service(tenant_id)

                trace = erp.forward_traceability(material_id, lot_number)

                return {
                    "material_id": material_id,
                    "lot_number": lot_number,
                    "trace_results": trace
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Forward traceability failed: {str(e)}")

        @self.router.get("/traceability/backward")
        async def backward_traceability(
            parent_material_id: str,
            parent_serial_number: str,
            tenant_id: str = Query("DEFAULT")
        ):
            """
            Backward traceability (제품 → 원료)

            특정 제품에 사용된 모든 원료 추적
            """
            try:
                erp = self._get_erp_service(tenant_id)

                trace = erp.backward_traceability(parent_material_id, parent_serial_number)

                return trace

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Backward traceability failed: {str(e)}")

        # ================================================================
        # Inventory & Reporting
        # ================================================================

        @self.router.get("/inventory/summary")
        async def get_inventory_summary(tenant_id: str = Query("DEFAULT")):
            """
            Get inventory summary

            재고 현황 요약
            """
            try:
                erp = self._get_erp_service(tenant_id)

                summary = erp.get_inventory_summary()

                return summary

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get inventory summary: {str(e)}")

        @self.router.get("/materials/{material_id}/requirements")
        async def get_material_requirements(
            material_id: str,
            quantity: float,
            tenant_id: str = Query("DEFAULT")
        ):
            """
            Get material requirements (MRP)

            특정 제품 생산에 필요한 모든 원료 계산
            """
            try:
                erp = self._get_erp_service(tenant_id)

                requirements = erp.get_material_requirements(material_id, Decimal(str(quantity)))

                return requirements

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"MRP calculation failed: {str(e)}")

        @self.router.get("/stats")
        async def get_stats(tenant_id: str = Query("DEFAULT")):
            """Get comprehensive ERP statistics"""
            try:
                erp = self._get_erp_service(tenant_id)

                stats = erp.get_stats()

                return stats

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "Enterprise Manufacturing ERP",
                "version": "7.4.0",
                "tenants": len(self.erp_services)
            }


def get_enterprise_erp_router(tenant_id: str = "DEFAULT") -> APIRouter:
    """Factory function to create router"""
    router_instance = EnterpriseERPRouter(tenant_id=tenant_id)
    return router_instance.router
