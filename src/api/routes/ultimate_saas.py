"""
Ultimate SaaS Platform API Routes - v7.4.0
"""

from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.ultimate_saas_platform_service import (
    UltimateSaaSPlatformService,
    TenantTier,
    BillingCycle,
    AccountingEntryType,
    get_ultimate_saas_platform_service
)


class CreateTenantRequest(BaseModel):
    """Request to create tenant"""
    tenant_name: str
    tier: TenantTier
    billing_cycle: BillingCycle


class AccountingEntryRequest(BaseModel):
    """Request for accounting entry"""
    tenant_id: str
    entry_type: AccountingEntryType
    account: str
    amount: float
    description: str
    reference: Optional[str] = None


class EmployeeRequest(BaseModel):
    """Request to add employee"""
    tenant_id: str
    employee_data: Dict


class PayrollRequest(BaseModel):
    """Request to process payroll"""
    tenant_id: str
    month: str


class AttendanceRequest(BaseModel):
    """Request to track attendance"""
    tenant_id: str
    employee_id: str
    date: datetime
    check_in: datetime
    check_out: datetime


class UltimateSaaSRouter:
    """Ultimate SaaS Platform API Router"""

    def __init__(self, service: Optional[UltimateSaaSPlatformService] = None):
        self.router = APIRouter(prefix="/ultimate-saas", tags=["SaaS Platform"])
        self.service = service or get_ultimate_saas_platform_service()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        # ================================================================
        # Tenant Management
        # ================================================================

        @self.router.post("/tenants")
        async def create_tenant(request: CreateTenantRequest):
            """
            Create new tenant with subscription
            
            Tiers:
            - Free (₩0)
            - Basic (₩50,000/month)
            - Professional (₩150,000/month)
            - Enterprise (₩500,000/month)
            
            Billing cycles:
            - Monthly (0% discount)
            - Quarterly (5% discount)
            - Annually (15% discount)
            """
            try:
                result = await self.service.create_tenant(
                    request.tenant_name,
                    request.tier,
                    request.billing_cycle
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Tenant creation failed: {str(e)}")

        @self.router.get("/tenants")
        async def get_tenants(
            status: Optional[str] = None,
            tier: Optional[TenantTier] = None,
            limit: int = Query(100, ge=1, le=1000)
        ):
            """Get list of tenants with filters"""
            try:
                tenants = list(self.service.tenants.values())
                
                if status:
                    tenants = [t for t in tenants if t.get("status") == status]
                if tier:
                    tenants = [t for t in tenants if t.get("tier") == tier]
                
                tenants = tenants[:limit]
                return {"tenants": tenants, "total": len(tenants)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get tenants: {str(e)}")

        @self.router.get("/tenants/{tenant_id}")
        async def get_tenant(tenant_id: str):
            """Get tenant details"""
            try:
                tenant = self.service.tenants.get(tenant_id)
                if not tenant:
                    raise HTTPException(status_code=404, detail="Tenant not found")
                return tenant
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get tenant: {str(e)}")

        @self.router.get("/tenants/{tenant_id}/analytics")
        async def get_tenant_analytics(tenant_id: str):
            """Get tenant analytics"""
            try:
                analytics = self.service.get_tenant_analytics(tenant_id)
                return analytics
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

        # ================================================================
        # Accounting
        # ================================================================

        @self.router.post("/accounting/entry")
        async def create_accounting_entry(request: AccountingEntryRequest):
            """
            Create accounting entry (복식부기)
            
            Auto-generates financial statements:
            - Balance Sheet
            - Income Statement
            - Cash Flow Statement
            """
            try:
                entry = await self.service.create_accounting_entry(
                    request.tenant_id,
                    request.entry_type,
                    request.account,
                    Decimal(str(request.amount)),
                    request.description,
                    request.reference
                )
                return entry
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Entry creation failed: {str(e)}")

        @self.router.get("/accounting/financial-statements/{tenant_id}")
        async def get_financial_statements(
            tenant_id: str,
            period_start: datetime,
            period_end: datetime
        ):
            """Generate financial statements for period"""
            try:
                statements = await self.service.generate_financial_statements(
                    tenant_id, period_start, period_end
                )
                return statements
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to generate statements: {str(e)}")

        @self.router.get("/accounting/ledger/{tenant_id}")
        async def get_ledger(tenant_id: str, limit: int = 100):
            """Get accounting ledger entries"""
            try:
                entries = [e for e in self.service.ledger if e["tenant_id"] == tenant_id][-limit:]
                return {"entries": entries, "total": len(entries)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get ledger: {str(e)}")

        # ================================================================
        # HR Management
        # ================================================================

        @self.router.post("/hr/employees")
        async def add_employee(request: EmployeeRequest):
            """Add employee to tenant"""
            try:
                employee = await self.service.add_employee(
                    request.tenant_id, request.employee_data
                )
                return employee
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to add employee: {str(e)}")

        @self.router.post("/hr/payroll")
        async def process_payroll(request: PayrollRequest):
            """
            Process monthly payroll
            
            Auto-calculates:
            - Base salary
            - Allowances
            - Deductions (8% income tax, 9% insurance)
            - Net salary
            """
            try:
                result = await self.service.process_payroll(
                    request.tenant_id, request.month
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Payroll processing failed: {str(e)}")

        @self.router.post("/hr/attendance")
        async def track_attendance(request: AttendanceRequest):
            """Track employee attendance"""
            try:
                record = await self.service.track_attendance(
                    request.tenant_id,
                    request.employee_id,
                    request.date,
                    request.check_in,
                    request.check_out
                )
                return record
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Attendance tracking failed: {str(e)}")

        @self.router.get("/hr/employees/{tenant_id}")
        async def get_employees(tenant_id: str):
            """Get employees for tenant"""
            try:
                employees = self.service.employees.get(tenant_id, [])
                return {"employees": employees, "total": len(employees)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get employees: {str(e)}")

        # ================================================================
        # Billing
        # ================================================================

        @self.router.post("/billing/process/{tenant_id}")
        async def process_billing(tenant_id: str):
            """
            Process billing for tenant
            
            Includes:
            - Subscription fee
            - Usage-based charges
            - Auto-invoice generation
            """
            try:
                invoice = await self.service.process_billing(tenant_id)
                return invoice
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Billing failed: {str(e)}")

        @self.router.get("/subscriptions/{tenant_id}")
        async def get_subscription(tenant_id: str):
            """Get subscription details"""
            try:
                subscription = self.service.subscriptions.get(tenant_id)
                if not subscription:
                    raise HTTPException(status_code=404, detail="Subscription not found")
                return subscription
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get subscription: {str(e)}")

        # ================================================================
        # Platform Stats
        # ================================================================

        @self.router.get("/platform/stats")
        async def get_platform_stats():
            """
            Get platform-wide statistics
            
            Returns:
            - Total tenants
            - Total revenue
            - Avg revenue per tenant
            - Churn rate
            """
            try:
                return self.service.get_platform_stats()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "Ultimate SaaS Platform",
                "version": "7.4.0",
                "stats": self.service.get_platform_stats()
            }


def get_ultimate_saas_router(service: Optional[UltimateSaaSPlatformService] = None) -> APIRouter:
    """Factory function"""
    router_instance = UltimateSaaSRouter(service=service)
    return router_instance.router
