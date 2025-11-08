"""
SaaS API Endpoints

Multi-tenancy, billing, and usage management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

from src.core.auth.jwt_handler import (
    get_current_user_from_token,
    TokenData,
    create_token_response,
    hash_password,
    verify_password
)
from src.core.auth.api_key_handler import APIKeyManager, get_current_tenant
from src.services.billing_service import billing_service
from src.services.usage_tracker import usage_tracker
from src.models.saas_models import (
    Tenant,
    User,
    APIKey,
    PlanTier,
    UserRole,
    TenantStatus
)


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class TenantCreate(BaseModel):
    """Create tenant request"""
    company_name: str
    subdomain: str
    email: EmailStr
    admin_name: str
    admin_password: str
    plan_tier: PlanTier = PlanTier.FREE


class TenantResponse(BaseModel):
    """Tenant response"""
    id: str
    company_name: str
    subdomain: str
    email: str
    plan_tier: PlanTier
    subscription_status: str
    status: str
    created_at: datetime


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class APIKeyCreate(BaseModel):
    """Create API key request"""
    name: str
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """API key response"""
    api_key: str  # Only shown once!
    key_id: str
    key_prefix: str
    name: str
    created_at: str
    expires_at: Optional[str]


class SubscriptionUpgrade(BaseModel):
    """Upgrade subscription request"""
    plan_tier: PlanTier
    billing_period: str = "monthly"  # monthly, yearly


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/auth/register", response_model=TenantResponse, tags=["Auth"])
async def register_tenant(request: TenantCreate):
    """
    Register new tenant

    Creates:
    - Tenant account
    - Admin user
    - Stripe customer (if not free tier)
    """
    from src.db.session import SessionLocal

    db = SessionLocal()

    try:
        # Check if subdomain exists
        existing = db.query(Tenant).filter(Tenant.subdomain == request.subdomain).first()
        if existing:
            raise HTTPException(status_code=400, detail="Subdomain already exists")

        # Create tenant
        tenant = Tenant(
            company_name=request.company_name,
            subdomain=request.subdomain,
            email=request.email,
            plan_tier=request.plan_tier,
            status=TenantStatus.ACTIVE
        )

        # Create Stripe customer if not free tier
        if request.plan_tier != PlanTier.FREE:
            stripe_customer_id = billing_service.create_customer(
                tenant_id=str(tenant.id),
                email=request.email,
                company_name=request.company_name
            )
            tenant.stripe_customer_id = stripe_customer_id

        db.add(tenant)
        db.flush()

        # Create admin user
        admin_user = User(
            tenant_id=tenant.id,
            email=request.email,
            password_hash=hash_password(request.admin_password),
            name=request.admin_name,
            role=UserRole.ADMIN,
            is_active=True,
            email_verified=False
        )
        db.add(admin_user)

        db.commit()
        db.refresh(tenant)

        return TenantResponse(
            id=str(tenant.id),
            company_name=tenant.company_name,
            subdomain=tenant.subdomain,
            email=tenant.email,
            plan_tier=tenant.plan_tier,
            subscription_status=tenant.subscription_status.value,
            status=tenant.status.value,
            created_at=tenant.created_at
        )

    finally:
        db.close()


@router.post("/auth/login", tags=["Auth"])
async def login(credentials: UserLogin):
    """
    User login

    Returns JWT token
    """
    from src.db.session import SessionLocal

    db = SessionLocal()

    try:
        # Find user
        user = db.query(User).filter(User.email == credentials.email).first()

        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        # Check tenant status
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not tenant or not tenant.is_active:
            raise HTTPException(status_code=403, detail="Tenant account is suspended")

        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()

        # Create JWT token
        token_response = create_token_response(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            role=user.role.value
        )

        return token_response

    finally:
        db.close()


# ============================================================================
# API Key Management
# ============================================================================

@router.post("/api-keys", response_model=APIKeyResponse, tags=["API Keys"])
async def create_api_key(
    request: APIKeyCreate,
    current_user: TokenData = Depends(get_current_user_from_token)
):
    """
    Create new API key

    Only for authenticated users.
    """
    manager = APIKeyManager()

    result = manager.generate_api_key(
        tenant_id=current_user.tenant_id,
        name=request.name,
        expires_days=request.expires_days
    )

    return APIKeyResponse(**result)


@router.get("/api-keys", tags=["API Keys"])
async def list_api_keys(
    current_user: TokenData = Depends(get_current_user_from_token)
):
    """List all API keys for current tenant"""
    manager = APIKeyManager()
    return manager.list_api_keys(current_user.tenant_id)


@router.delete("/api-keys/{key_id}", tags=["API Keys"])
async def revoke_api_key(
    key_id: str,
    current_user: TokenData = Depends(get_current_user_from_token)
):
    """Revoke API key"""
    manager = APIKeyManager()

    success = manager.revoke_api_key(key_id, current_user.tenant_id)

    return {"message": "API key revoked", "key_id": key_id}


# ============================================================================
# Billing & Subscriptions
# ============================================================================

@router.get("/billing/subscription", tags=["Billing"])
async def get_subscription(
    tenant_id: str = Depends(get_current_tenant)
):
    """Get current subscription info"""
    from src.db.session import SessionLocal

    db = SessionLocal()

    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        return {
            "plan_tier": tenant.plan_tier.value,
            "subscription_status": tenant.subscription_status.value,
            "current_period_end": tenant.current_period_end.isoformat() if tenant.current_period_end else None,
            "stripe_customer_id": tenant.stripe_customer_id,
            "stripe_subscription_id": tenant.stripe_subscription_id
        }

    finally:
        db.close()


@router.post("/billing/upgrade", tags=["Billing"])
async def upgrade_subscription(
    request: SubscriptionUpgrade,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Upgrade subscription plan

    Creates Stripe subscription if upgrading from free tier.
    Updates existing subscription if already subscribed.
    """
    from src.db.session import SessionLocal

    db = SessionLocal()

    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Upgrading from free tier
        if tenant.plan_tier == PlanTier.FREE:
            # Create Stripe customer if needed
            if not tenant.stripe_customer_id:
                customer_id = billing_service.create_customer(
                    tenant_id=tenant_id,
                    email=tenant.email,
                    company_name=tenant.company_name
                )
                tenant.stripe_customer_id = customer_id
                db.commit()

            # Create subscription
            result = billing_service.create_subscription(
                customer_id=tenant.stripe_customer_id,
                plan_tier=request.plan_tier,
                billing_period=request.billing_period
            )

            # Update tenant
            tenant.plan_tier = request.plan_tier
            tenant.stripe_subscription_id = result["subscription_id"]
            db.commit()

            return {
                "message": "Subscription created",
                "client_secret": result["client_secret"],
                "status": result["status"]
            }

        # Upgrading existing subscription
        else:
            result = billing_service.upgrade_subscription(
                subscription_id=tenant.stripe_subscription_id,
                new_plan_tier=request.plan_tier,
                billing_period=request.billing_period
            )

            # Update tenant
            tenant.plan_tier = request.plan_tier
            db.commit()

            return {
                "message": "Subscription upgraded",
                "subscription_id": result["subscription_id"],
                "status": result["status"]
            }

    finally:
        db.close()


@router.post("/billing/cancel", tags=["Billing"])
async def cancel_subscription(
    immediately: bool = False,
    tenant_id: str = Depends(get_current_tenant)
):
    """Cancel subscription"""
    from src.db.session import SessionLocal

    db = SessionLocal()

    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        if not tenant.stripe_subscription_id:
            raise HTTPException(status_code=400, detail="No active subscription")

        # Cancel via Stripe
        result = billing_service.cancel_subscription(
            subscription_id=tenant.stripe_subscription_id,
            immediately=immediately
        )

        return {
            "message": "Subscription canceled",
            "canceled_at": result["canceled_at"].isoformat() if result["canceled_at"] else None,
            "effective": "immediately" if immediately else "at period end"
        }

    finally:
        db.close()


@router.post("/billing/webhook", tags=["Billing"])
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """Handle Stripe webhooks"""
    payload = await request.body()

    try:
        result = billing_service.handle_webhook(payload, stripe_signature)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Usage & Analytics
# ============================================================================

@router.get("/usage/quota", tags=["Usage"])
async def check_quota(
    tenant_id: str = Depends(get_current_tenant)
):
    """Check current quota status"""
    return usage_tracker.check_quota(tenant_id)


@router.get("/usage/stats", tags=["Usage"])
async def get_usage_stats(
    days: int = 30,
    tenant_id: str = Depends(get_current_tenant)
):
    """Get usage statistics"""
    from datetime import timedelta

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return usage_tracker.get_usage_stats(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )


# ============================================================================
# Tenant Management (Admin only)
# ============================================================================

@router.get("/tenants", tags=["Admin"])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user_from_token)
):
    """
    List all tenants (admin only)

    Note: This endpoint would need additional authorization check
    to ensure only platform admins can access it.
    """
    # TODO: Check if user is platform admin
    # For now, allow any authenticated user (change in production)

    from src.db.session import SessionLocal

    db = SessionLocal()

    try:
        tenants = db.query(Tenant).offset(skip).limit(limit).all()

        return [
            {
                "id": str(t.id),
                "company_name": t.company_name,
                "subdomain": t.subdomain,
                "plan_tier": t.plan_tier.value,
                "status": t.status.value,
                "created_at": t.created_at.isoformat()
            }
            for t in tenants
        ]

    finally:
        db.close()
