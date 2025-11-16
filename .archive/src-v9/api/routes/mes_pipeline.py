"""
MES Pipeline Integration API Routes - v7.4.0
기존 MES 프로그램과 RAG 시스템 연동을 위한 파이프라인 API
"""

from typing import List, Dict, Optional, Any, Literal
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl


# ========================================================================
# Enums
# ========================================================================

class MESSystem(str, Enum):
    """MES system type"""
    SAP_MES = "sap_mes"
    ORACLE_MES = "oracle_mes"
    AVEVA_MES = "aveva_mes"
    SIEMENS_OPCENTER = "siemens_opcenter"
    DELMIA_APRISO = "delmia_apriso"
    CUSTOM = "custom"


class SyncMode(str, Enum):
    """Sync mode"""
    FULL = "full"              # 전체 동기화
    INCREMENTAL = "incremental"  # 증분 동기화
    REAL_TIME = "real_time"    # 실시간 동기화


class DataType(str, Enum):
    """Data type to sync"""
    MATERIALS = "materials"              # 원료 마스터
    PRODUCTS = "products"                # 제품 마스터
    BOMS = "boms"                        # BOM
    WORK_ORDERS = "work_orders"          # 작업지시
    PRODUCTION_REPORTS = "production_reports"  # 생산실적
    QUALITY_INSPECTIONS = "quality_inspections"  # 품질검사
    INVENTORY = "inventory"              # 재고
    EQUIPMENT_STATUS = "equipment_status"  # 설비 상태


class SyncStatus(str, Enum):
    """Sync status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


# ========================================================================
# Request/Response Models
# ========================================================================

class MESConnection(BaseModel):
    """MES connection configuration"""
    connection_id: str = Field(..., description="Connection ID")
    connection_name: str = Field(..., description="Connection name")
    mes_system: MESSystem = Field(..., description="MES system type")

    # Connection details
    host: str = Field(..., description="MES host/URL")
    port: int = Field(8080, description="Port")
    database: Optional[str] = Field(None, description="Database name")
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password (encrypted)")

    # API settings (if REST API)
    api_base_url: Optional[str] = Field(None, description="API base URL")
    api_key: Optional[str] = Field(None, description="API key")
    api_version: Optional[str] = Field("v1", description="API version")

    # Connection settings
    timeout_seconds: int = Field(30, description="Connection timeout")
    retry_attempts: int = Field(3, description="Retry attempts")
    connection_pool_size: int = Field(10, description="Connection pool size")

    # Status
    is_active: bool = Field(True, description="Connection active")
    last_tested: Optional[str] = None
    last_sync: Optional[str] = None


class DataMapping(BaseModel):
    """Data field mapping between MES and RAG"""
    mapping_id: str
    data_type: DataType
    mes_system: MESSystem

    # Source (MES)
    source_table: str = Field(..., description="MES table/endpoint")
    source_fields: Dict[str, str] = Field(..., description="MES field names")

    # Target (RAG)
    target_entity: str = Field(..., description="RAG entity name")
    target_fields: Dict[str, str] = Field(..., description="RAG field names")

    # Field mapping
    field_mappings: Dict[str, Any] = Field(
        ...,
        description="Field mapping rules {rag_field: mes_field or transformation}"
    )

    # Transformation rules
    transformations: Dict[str, str] = Field(
        default_factory=dict,
        description="Field transformation functions"
    )

    # Filters
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filter conditions for data sync"
    )


class SyncSchedule(BaseModel):
    """Sync schedule configuration"""
    schedule_id: str
    schedule_name: str
    connection_id: str
    data_types: List[DataType]
    sync_mode: SyncMode

    # Schedule settings
    enabled: bool = Field(True, description="Schedule enabled")
    cron_expression: str = Field("0 */1 * * *", description="Cron expression (every 1 hour)")

    # Sync settings
    batch_size: int = Field(1000, description="Batch size")
    enable_validation: bool = Field(True, description="Enable data validation")
    enable_deduplication: bool = Field(True, description="Enable deduplication")
    enable_notification: bool = Field(True, description="Enable sync notifications")

    # Status
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    last_status: Optional[SyncStatus] = None


class SyncRequest(BaseModel):
    """Manual sync request"""
    connection_id: str
    data_types: List[DataType]
    sync_mode: SyncMode = SyncMode.INCREMENTAL

    # Filters
    date_from: Optional[str] = Field(None, description="Sync data from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Sync data to date (YYYY-MM-DD)")
    filters: Dict[str, Any] = Field(default_factory=dict)

    # Options
    dry_run: bool = Field(False, description="Dry run (preview only)")
    force_full_sync: bool = Field(False, description="Force full sync")


class SyncResult(BaseModel):
    """Sync result"""
    sync_id: str
    connection_id: str
    data_types: List[DataType]
    sync_mode: SyncMode
    status: SyncStatus

    # Statistics
    total_records: int = 0
    synced_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0

    # Details
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None

    # Errors
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Data preview
    sample_data: List[Dict[str, Any]] = Field(default_factory=list)


# ========================================================================
# Predefined Mappings
# ========================================================================

PREDEFINED_MAPPINGS = {
    "materials_sap": DataMapping(
        mapping_id="materials_sap",
        data_type=DataType.MATERIALS,
        mes_system=MESSystem.SAP_MES,
        source_table="MARA",  # SAP Material Master table
        source_fields={
            "MATNR": "material_code",
            "MAKTX": "material_name",
            "MTART": "material_type",
            "MEINS": "uom",
            "BRGEW": "weight",
            "GEWEI": "weight_unit"
        },
        target_entity="materials",
        target_fields={
            "material_code": "material_code",
            "material_name": "material_name",
            "material_type": "material_type",
            "uom": "uom"
        },
        field_mappings={
            "material_code": "MATNR",
            "material_name": "MAKTX",
            "material_type": "MTART",
            "uom": "MEINS",
            "specifications": {
                "weight": "BRGEW",
                "weight_unit": "GEWEI"
            }
        },
        transformations={
            "material_code": "lambda x: x.lstrip('0')",  # Remove leading zeros
            "material_type": "lambda x: material_type_mapping.get(x, 'raw_material')"
        }
    ),

    "products_custom": DataMapping(
        mapping_id="products_custom",
        data_type=DataType.PRODUCTS,
        mes_system=MESSystem.CUSTOM,
        source_table="product_master",
        source_fields={
            "prd_code": "product_code",
            "prd_name": "product_name",
            "prd_cat": "category",
            "prd_desc": "description",
            "prd_price": "price"
        },
        target_entity="products",
        target_fields={
            "product_code": "product_code",
            "product_name": "product_name",
            "category": "category",
            "description": "description",
            "price": "price"
        },
        field_mappings={
            "product_code": "prd_code",
            "product_name": "prd_name",
            "category": "prd_cat",
            "description": "prd_desc",
            "price": "prd_price"
        }
    ),

    "work_orders_siemens": DataMapping(
        mapping_id="work_orders_siemens",
        data_type=DataType.WORK_ORDERS,
        mes_system=MESSystem.SIEMENS_OPCENTER,
        source_table="production_orders",
        source_fields={
            "order_no": "wo_number",
            "material_no": "product_material_code",
            "planned_qty": "quantity_planned",
            "start_date": "planned_start",
            "end_date": "planned_end"
        },
        target_entity="work_orders",
        target_fields={
            "wo_number": "wo_number",
            "product_material_id": "product_material_id",
            "quantity_planned": "quantity_planned",
            "planned_start": "planned_start",
            "planned_end": "planned_end"
        },
        field_mappings={
            "wo_number": "order_no",
            "product_material_id": "material_no",  # Needs lookup
            "quantity_planned": "planned_qty",
            "planned_start": "start_date",
            "planned_end": "end_date"
        },
        transformations={
            "planned_start": "lambda x: datetime.fromisoformat(x)",
            "planned_end": "lambda x: datetime.fromisoformat(x)"
        }
    )
}


# ========================================================================
# Router
# ========================================================================

class MESPipelineRouter:
    """MES Pipeline Integration API Router"""

    def __init__(self):
        self.router = APIRouter(prefix="/mes-pipeline", tags=["MES Pipeline"])
        self.connections: Dict[str, MESConnection] = {}
        self.mappings: Dict[str, DataMapping] = PREDEFINED_MAPPINGS.copy()
        self.schedules: Dict[str, SyncSchedule] = {}
        self.sync_history: List[SyncResult] = []
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        # ================================================================
        # Connection Management
        # ================================================================

        @self.router.post("/connections")
        async def create_connection(connection: MESConnection):
            """
            Create MES connection

            MES 연결 설정 생성

            Supports:
            - SAP MES
            - Oracle MES
            - AVEVA MES
            - Siemens Opcenter
            - Delmia Apriso
            - Custom MES systems

            Connection types:
            - Database connection (JDBC/ODBC)
            - REST API
            - SOAP Web Service
            - OPC UA
            """
            if connection.connection_id in self.connections:
                raise HTTPException(status_code=400, detail="Connection ID already exists")

            self.connections[connection.connection_id] = connection

            return {
                "status": "created",
                "connection": connection
            }

        @self.router.get("/connections")
        async def list_connections(mes_system: Optional[MESSystem] = None):
            """List MES connections"""
            connections = list(self.connections.values())

            if mes_system:
                connections = [c for c in connections if c.mes_system == mes_system]

            return {
                "connections": connections,
                "total": len(connections)
            }

        @self.router.get("/connections/{connection_id}")
        async def get_connection(connection_id: str):
            """Get connection details"""
            if connection_id not in self.connections:
                raise HTTPException(status_code=404, detail="Connection not found")

            return self.connections[connection_id]

        @self.router.post("/connections/{connection_id}/test")
        async def test_connection(connection_id: str):
            """
            Test MES connection

            MES 연결 테스트

            Tests:
            - Network connectivity
            - Authentication
            - Database/API accessibility
            - Query execution
            """
            if connection_id not in self.connections:
                raise HTTPException(status_code=404, detail="Connection not found")

            connection = self.connections[connection_id]

            try:
                # Simulate connection test
                test_result = await self._test_mes_connection(connection)

                connection.last_tested = datetime.now().isoformat()
                connection.is_active = test_result["success"]

                return test_result

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "tested_at": datetime.now().isoformat()
                }

        async def _test_mes_connection(self, connection: MESConnection) -> Dict[str, Any]:
            """Test MES connection (implementation placeholder)"""
            # TODO: Implement actual connection test based on MES system type
            await asyncio.sleep(0.5)  # Simulate network delay

            return {
                "success": True,
                "message": "Connection successful",
                "response_time_ms": 250,
                "tested_at": datetime.now().isoformat(),
                "details": {
                    "host": connection.host,
                    "port": connection.port,
                    "mes_system": connection.mes_system,
                    "database": connection.database or "N/A"
                }
            }

        # ================================================================
        # Data Mapping Management
        # ================================================================

        @self.router.get("/mappings")
        async def list_mappings(
            data_type: Optional[DataType] = None,
            mes_system: Optional[MESSystem] = None
        ):
            """
            List data mappings

            데이터 매핑 목록

            Predefined mappings:
            - materials_sap: SAP Material Master → RAG Materials
            - products_custom: Custom Product Master → RAG Products
            - work_orders_siemens: Siemens Production Orders → RAG Work Orders
            """
            mappings = list(self.mappings.values())

            if data_type:
                mappings = [m for m in mappings if m.data_type == data_type]
            if mes_system:
                mappings = [m for m in mappings if m.mes_system == mes_system]

            return {
                "mappings": [
                    {
                        "mapping_id": m.mapping_id,
                        "data_type": m.data_type,
                        "mes_system": m.mes_system,
                        "source_table": m.source_table,
                        "target_entity": m.target_entity
                    }
                    for m in mappings
                ],
                "total": len(mappings)
            }

        @self.router.get("/mappings/{mapping_id}")
        async def get_mapping(mapping_id: str):
            """Get mapping details"""
            if mapping_id not in self.mappings:
                raise HTTPException(status_code=404, detail="Mapping not found")

            return self.mappings[mapping_id]

        @self.router.post("/mappings")
        async def create_mapping(mapping: DataMapping):
            """
            Create custom data mapping

            사용자 정의 데이터 매핑 생성

            Mapping rules:
            - Simple field mapping: {"rag_field": "mes_field"}
            - Nested mapping: {"rag_field": {"sub_field": "mes_field"}}
            - Transformation: {"rag_field": "lambda x: transform(x)"}
            """
            if mapping.mapping_id in self.mappings:
                raise HTTPException(status_code=400, detail="Mapping ID already exists")

            self.mappings[mapping.mapping_id] = mapping

            return {
                "status": "created",
                "mapping": mapping
            }

        # ================================================================
        # Sync Schedule Management
        # ================================================================

        @self.router.post("/schedules")
        async def create_schedule(schedule: SyncSchedule):
            """
            Create sync schedule

            동기화 스케줄 생성

            Cron expressions:
            - "0 * * * *": Every hour
            - "0 */6 * * *": Every 6 hours
            - "0 0 * * *": Daily at midnight
            - "0 0 * * 0": Weekly on Sunday
            """
            if schedule.schedule_id in self.schedules:
                raise HTTPException(status_code=400, detail="Schedule ID already exists")

            # Calculate next run
            schedule.next_run = self._calculate_next_run(schedule.cron_expression)

            self.schedules[schedule.schedule_id] = schedule

            return {
                "status": "created",
                "schedule": schedule
            }

        @self.router.get("/schedules")
        async def list_schedules(enabled_only: bool = Query(False)):
            """List sync schedules"""
            schedules = list(self.schedules.values())

            if enabled_only:
                schedules = [s for s in schedules if s.enabled]

            return {
                "schedules": schedules,
                "total": len(schedules)
            }

        @self.router.put("/schedules/{schedule_id}/enable")
        async def enable_schedule(schedule_id: str, enabled: bool = Body(..., embed=True)):
            """Enable/disable schedule"""
            if schedule_id not in self.schedules:
                raise HTTPException(status_code=404, detail="Schedule not found")

            self.schedules[schedule_id].enabled = enabled

            return {
                "status": "updated",
                "schedule_id": schedule_id,
                "enabled": enabled
            }

        def _calculate_next_run(self, cron_expression: str) -> str:
            """Calculate next run time from cron expression"""
            # Simplified calculation (in production, use croniter library)
            # For now, return 1 hour from now
            next_run = datetime.now() + timedelta(hours=1)
            return next_run.isoformat()

        # ================================================================
        # Manual Sync
        # ================================================================

        @self.router.post("/sync")
        async def manual_sync(
            sync_request: SyncRequest,
            background_tasks: BackgroundTasks
        ):
            """
            Manual data sync

            수동 데이터 동기화

            Sync modes:
            - full: Full sync (all data)
            - incremental: Incremental sync (changed data only)
            - real_time: Real-time sync (live data stream)

            Process:
            1. Connect to MES
            2. Query data based on filters
            3. Apply field mappings
            4. Transform data
            5. Validate data
            6. Deduplicate
            7. Sync to RAG system
            8. Generate embeddings
            9. Index to vector DB
            """
            # Validate connection
            if sync_request.connection_id not in self.connections:
                raise HTTPException(status_code=404, detail="Connection not found")

            connection = self.connections[sync_request.connection_id]
            if not connection.is_active:
                raise HTTPException(status_code=400, detail="Connection is not active")

            # Create sync result
            sync_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            sync_result = SyncResult(
                sync_id=sync_id,
                connection_id=sync_request.connection_id,
                data_types=sync_request.data_types,
                sync_mode=sync_request.sync_mode,
                status=SyncStatus.PENDING,
                start_time=datetime.now().isoformat()
            )

            # Run sync in background
            background_tasks.add_task(
                self._execute_sync,
                sync_request,
                connection,
                sync_result
            )

            return {
                "status": "started",
                "sync_id": sync_id,
                "message": "Sync started in background",
                "check_status_url": f"/mes-pipeline/sync/{sync_id}"
            }

        async def _execute_sync(
            self,
            sync_request: SyncRequest,
            connection: MESConnection,
            sync_result: SyncResult
        ):
            """Execute sync (background task)"""
            try:
                sync_result.status = SyncStatus.RUNNING

                for data_type in sync_request.data_types:
                    # Find mapping
                    mapping = self._find_mapping(data_type, connection.mes_system)
                    if not mapping:
                        sync_result.errors.append({
                            "data_type": data_type,
                            "error": "No mapping found"
                        })
                        continue

                    # Query MES data
                    mes_data = await self._query_mes_data(
                        connection,
                        mapping,
                        sync_request
                    )

                    sync_result.total_records += len(mes_data)

                    # Transform and sync
                    for record in mes_data:
                        try:
                            # Transform data
                            transformed = self._transform_data(record, mapping)

                            # Sync to RAG (dry run check)
                            if not sync_request.dry_run:
                                await self._sync_to_rag(data_type, transformed)

                            sync_result.synced_records += 1

                        except Exception as e:
                            sync_result.failed_records += 1
                            sync_result.errors.append({
                                "record": record,
                                "error": str(e)
                            })

                # Complete
                sync_result.status = SyncStatus.COMPLETED
                sync_result.end_time = datetime.now().isoformat()

                start = datetime.fromisoformat(sync_result.start_time)
                end = datetime.fromisoformat(sync_result.end_time)
                sync_result.duration_seconds = (end - start).total_seconds()

                # Store in history
                self.sync_history.append(sync_result)

                # Update connection
                connection.last_sync = sync_result.end_time

            except Exception as e:
                sync_result.status = SyncStatus.FAILED
                sync_result.end_time = datetime.now().isoformat()
                sync_result.errors.append({
                    "error": "Sync failed",
                    "message": str(e)
                })
                self.sync_history.append(sync_result)

        def _find_mapping(self, data_type: DataType, mes_system: MESSystem) -> Optional[DataMapping]:
            """Find mapping for data type and MES system"""
            for mapping in self.mappings.values():
                if mapping.data_type == data_type and mapping.mes_system == mes_system:
                    return mapping
            return None

        async def _query_mes_data(
            self,
            connection: MESConnection,
            mapping: DataMapping,
            sync_request: SyncRequest
        ) -> List[Dict[str, Any]]:
            """Query data from MES (placeholder)"""
            # TODO: Implement actual MES query based on connection type
            await asyncio.sleep(1)  # Simulate query

            # Return dummy data
            return [
                {
                    "MATNR": "000000000000001234",
                    "MAKTX": "PET Resin Prime",
                    "MTART": "ROH",
                    "MEINS": "KG",
                    "BRGEW": 25.5,
                    "GEWEI": "KG"
                }
            ]

        def _transform_data(self, record: Dict[str, Any], mapping: DataMapping) -> Dict[str, Any]:
            """Transform MES data to RAG format"""
            transformed = {}

            for rag_field, mes_field in mapping.field_mappings.items():
                if isinstance(mes_field, str):
                    # Simple mapping
                    value = record.get(mes_field)

                    # Apply transformation if exists
                    if rag_field in mapping.transformations:
                        transform_func = mapping.transformations[rag_field]
                        # In production, safely evaluate transformation
                        # For now, just pass through
                        value = value

                    transformed[rag_field] = value

                elif isinstance(mes_field, dict):
                    # Nested mapping
                    nested = {}
                    for sub_field, source_field in mes_field.items():
                        nested[sub_field] = record.get(source_field)
                    transformed[rag_field] = nested

            return transformed

        async def _sync_to_rag(self, data_type: DataType, data: Dict[str, Any]):
            """Sync data to RAG system (placeholder)"""
            # TODO: Implement actual RAG sync
            # - Store in database
            # - Generate embeddings
            # - Index to vector DB
            await asyncio.sleep(0.1)

        # ================================================================
        # Sync Status & History
        # ================================================================

        @self.router.get("/sync/{sync_id}")
        async def get_sync_status(sync_id: str):
            """
            Get sync status

            동기화 상태 조회
            """
            for result in self.sync_history:
                if result.sync_id == sync_id:
                    return result

            raise HTTPException(status_code=404, detail="Sync not found")

        @self.router.get("/sync-history")
        async def get_sync_history(
            connection_id: Optional[str] = None,
            status: Optional[SyncStatus] = None,
            limit: int = Query(50, ge=1, le=500)
        ):
            """Get sync history"""
            history = self.sync_history.copy()

            if connection_id:
                history = [h for h in history if h.connection_id == connection_id]
            if status:
                history = [h for h in history if h.status == status]

            # Sort by start time (newest first)
            history.sort(key=lambda x: x.start_time, reverse=True)

            history = history[:limit]

            return {
                "history": history,
                "total": len(history)
            }

        @self.router.get("/stats")
        async def get_stats():
            """
            Get MES pipeline statistics

            MES 파이프라인 통계
            """
            total_syncs = len(self.sync_history)
            successful_syncs = sum(1 for h in self.sync_history if h.status == SyncStatus.COMPLETED)
            failed_syncs = sum(1 for h in self.sync_history if h.status == SyncStatus.FAILED)
            total_records = sum(h.synced_records for h in self.sync_history)

            return {
                "connections": {
                    "total": len(self.connections),
                    "active": sum(1 for c in self.connections.values() if c.is_active)
                },
                "mappings": {
                    "total": len(self.mappings),
                    "by_type": {
                        data_type: sum(1 for m in self.mappings.values() if m.data_type == data_type)
                        for data_type in DataType
                    }
                },
                "schedules": {
                    "total": len(self.schedules),
                    "enabled": sum(1 for s in self.schedules.values() if s.enabled)
                },
                "syncs": {
                    "total": total_syncs,
                    "successful": successful_syncs,
                    "failed": failed_syncs,
                    "success_rate": (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0,
                    "total_records_synced": total_records
                }
            }

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "MES Pipeline Integration",
                "version": "7.4.0",
                "connections": len(self.connections),
                "active_connections": sum(1 for c in self.connections.values() if c.is_active),
                "mappings": len(self.mappings),
                "schedules": len(self.schedules)
            }


def get_mes_pipeline_router() -> APIRouter:
    """Factory function to create router"""
    router_instance = MESPipelineRouter()
    return router_instance.router
