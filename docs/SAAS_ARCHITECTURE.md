# SaaS Architecture - Enterprise Multi-Tenancy System

**Version**: v5.0.0
**Symbol Domain**: §saas.*
**Production-ready SaaS platform with multi-tenancy, billing, and usage management**

---

## 📍 Symbol Navigation

**Quick Access**: Use these symbols for efficient documentation navigation

| Symbol | Description | Location |
|--------|-------------|----------|
| §saas.status | Platform status & capabilities | SYMBOLS.md |
| §saas.auth | Authentication (JWT + API keys) | This document, SYMBOLS.md |
| §saas.billing | Stripe billing integration | This document, SYMBOLS.md |
| §saas.usage | Usage tracking & quotas | This document, SYMBOLS.md |
| §saas.tenants | Multi-tenancy system | This document, SYMBOLS.md |
| §api.endpoints | All SaaS API endpoints | API_DOCUMENTATION.md |
| §deploy.docker | Docker deployment | DEPLOYMENT_GUIDE.md |

**See Also**:
- **CLAUDE.md**: Quick reference with all symbols
- **SYMBOLS.md**: Complete symbol map (§saas.* section)
- **Skills**: `.claude/skills/saas-platform/SKILL.md`

---

## ⚡ Quick Reference (Token-Optimized)

```
SaaS Platform v5.0.0
├─ Auth: JWT (24h) + API Keys (SHA-256) → §saas.auth
├─ Billing: Stripe (Free/Pro/Enterprise) → §saas.billing
├─ Usage: Redis + PostgreSQL tracking → §saas.usage
├─ Multi-Tenancy: PostgreSQL RLS → §saas.tenants
└─ API: 10+ endpoints → §api.endpoints

Tiers:
• Free: $0/mo, 1K calls, 1GB, 1 user, 10 req/min
• Pro: $49/mo, 100K calls, 50GB, 10 users, 100 req/min
• Enterprise: $499/mo, Unlimited, 500GB, ∞ users, 1000 req/min
```

**💡 Use symbols above to jump to detailed sections in SYMBOLS.md**

---

## Table of Contents

1. [Overview](#overview)
2. [Multi-Tenancy Strategy](#multi-tenancy-strategy)
3. [Authentication & Authorization](#authentication--authorization)
4. [Billing & Subscriptions](#billing--subscriptions)
5. [Usage Tracking & Quotas](#usage-tracking--quotas)
6. [API Key Management](#api-key-management)
7. [Admin Dashboard](#admin-dashboard)
8. [Database Schema](#database-schema)
9. [Implementation](#implementation)

---

## Overview

### SaaS Features

```
Enterprise SaaS Platform
├── Multi-Tenancy
│   ├── Tenant isolation (Row-Level Security)
│   ├── Tenant onboarding
│   └── Tenant management API
├── Authentication & Authorization
│   ├── JWT tokens
│   ├── API keys
│   ├── OAuth2
│   └── RBAC (Role-Based Access Control)
├── Billing & Subscriptions
│   ├── Plan management (Free, Pro, Enterprise)
│   ├── Stripe integration
│   ├── Usage-based billing
│   └── Invoice generation
├── Usage Tracking & Quotas
│   ├── API call tracking
│   ├── Storage quotas
│   ├── Rate limiting
│   └── Usage analytics
├── Admin Dashboard
│   ├── Tenant management
│   ├── Usage monitoring
│   ├── Billing overview
│   └── System health
└── Developer Portal
    ├── API documentation
    ├── API key management
    └── Usage statistics
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                         │
│  - Rate Limiting                                             │
│  - API Key Validation                                        │
│  - Tenant Detection                                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Search     │  │   Billing    │  │    Admin     │      │
│  │   API        │  │   API        │  │    API       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ PostgreSQL │  │   Qdrant   │  │   Redis    │            │
│  │ (Tenants)  │  │ (Vectors)  │  │  (Cache)   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Multi-Tenancy Strategy

### Approach: Row-Level Security (Shared Database)

**Why RLS over Separate Databases**:
- ✅ Cost-effective (single database)
- ✅ Easy backups and maintenance
- ✅ Efficient resource usage
- ✅ Simpler schema migrations
- ❌ Requires careful security (RLS policies)

**Alternative**: Database per Tenant (for enterprise customers)

### Tenant Identification

**Methods**:
1. **Subdomain**: `acme.rag-enterprise.com` → tenant_id: `acme`
2. **API Key**: `X-API-Key: tenant_xxx_apikey` → extract tenant_id
3. **JWT Token**: Claims include `tenant_id`

### Tenant Isolation

**PostgreSQL Row-Level Security (RLS)**:

```sql
-- Enable RLS on all tenant tables
ALTER TABLE search_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their tenant's data
CREATE POLICY tenant_isolation ON search_logs
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Set tenant context
SET app.current_tenant_id = '550e8400-e29b-41d4-a716-446655440000';

-- All queries automatically filtered by tenant
SELECT * FROM search_logs;  -- Only returns current tenant's logs
```

**Qdrant Tenant Isolation**:

```python
# Separate collection per tenant
collection_name = f"tenant_{tenant_id}_products"

# Or: Use filters
client.search(
    collection_name="products",
    query_vector=embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=tenant_id)
            )
        ]
    )
)
```

---

## Authentication & Authorization

### Authentication Methods

#### 1. JWT Tokens (User Authentication)

```python
# src/core/auth/jwt_handler.py

from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: str
    tenant_id: str
    role: str
    exp: datetime

def create_access_token(
    user_id: str,
    tenant_id: str,
    role: str,
    expires_delta: timedelta = timedelta(hours=24)
) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm="HS256"
    )

    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return TokenData(**payload)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Usage**:
```http
POST /api/v1/auth/login
{
    "email": "user@acme.com",
    "password": "secret"
}

Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 86400
}

GET /api/v1/search
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### 2. API Keys (Programmatic Access)

```python
# src/core/auth/api_key_handler.py

import secrets
import hashlib
from datetime import datetime

class APIKeyManager:
    """Manage API keys for tenants"""

    def generate_api_key(self, tenant_id: str, name: str) -> dict:
        """Generate new API key"""

        # Format: tenant_xxx_<random>
        prefix = f"tenant_{tenant_id[:8]}"
        random_part = secrets.token_urlsafe(32)
        api_key = f"{prefix}_{random_part}"

        # Hash for storage (never store plaintext)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Store in database
        db_api_key = APIKey(
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            created_at=datetime.utcnow(),
            last_used_at=None
        )

        return {
            "api_key": api_key,  # Return only once!
            "key_id": db_api_key.id,
            "name": name
        }

    def verify_api_key(self, api_key: str) -> str:
        """Verify API key and return tenant_id"""

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        db_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()

        if not db_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update last used
        db_key.last_used_at = datetime.utcnow()
        db.commit()

        return db_key.tenant_id
```

**Usage**:
```http
GET /api/v1/search
X-API-Key: tenant_550e8400_xxxxxxxxxxxxxxxxxxxxx

Response:
{
    "results": [...]
}
```

### Role-Based Access Control (RBAC)

```python
# src/core/auth/rbac.py

from enum import Enum
from typing import List

class Role(str, Enum):
    ADMIN = "admin"          # Full access
    MEMBER = "member"        # Read/Write
    VIEWER = "viewer"        # Read only
    BILLING = "billing"      # Billing management

class Permission(str, Enum):
    SEARCH_READ = "search:read"
    SEARCH_WRITE = "search:write"
    TENANT_MANAGE = "tenant:manage"
    BILLING_VIEW = "billing:view"
    BILLING_MANAGE = "billing:manage"
    API_KEY_MANAGE = "api_key:manage"

ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.SEARCH_READ,
        Permission.SEARCH_WRITE,
        Permission.TENANT_MANAGE,
        Permission.BILLING_VIEW,
        Permission.BILLING_MANAGE,
        Permission.API_KEY_MANAGE
    ],
    Role.MEMBER: [
        Permission.SEARCH_READ,
        Permission.SEARCH_WRITE
    ],
    Role.VIEWER: [
        Permission.SEARCH_READ
    ],
    Role.BILLING: [
        Permission.BILLING_VIEW,
        Permission.BILLING_MANAGE
    ]
}

def require_permission(permission: Permission):
    """Decorator to check permission"""
    def decorator(func):
        async def wrapper(*args, current_user: User, **kwargs):
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])

            if permission not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@router.delete("/tenants/{tenant_id}")
@require_permission(Permission.TENANT_MANAGE)
async def delete_tenant(tenant_id: str, current_user: User):
    # Only admins can access this
    ...
```

---

## Billing & Subscriptions

### Subscription Plans

```python
# src/models/billing.py

from enum import Enum
from pydantic import BaseModel

class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionPlan(BaseModel):
    tier: PlanTier
    name: str
    price_monthly: float
    price_yearly: float

    # Quotas
    max_api_calls_per_month: int
    max_storage_gb: int
    max_users: int
    max_api_keys: int

    # Features
    features: list[str]

PLANS = {
    PlanTier.FREE: SubscriptionPlan(
        tier=PlanTier.FREE,
        name="Free",
        price_monthly=0,
        price_yearly=0,
        max_api_calls_per_month=1000,
        max_storage_gb=1,
        max_users=1,
        max_api_keys=2,
        features=[
            "1,000 API calls/month",
            "1GB storage",
            "Community support"
        ]
    ),
    PlanTier.PRO: SubscriptionPlan(
        tier=PlanTier.PRO,
        name="Pro",
        price_monthly=49,
        price_yearly=490,  # 2 months free
        max_api_calls_per_month=100000,
        max_storage_gb=50,
        max_users=10,
        max_api_keys=10,
        features=[
            "100,000 API calls/month",
            "50GB storage",
            "Priority support",
            "Advanced analytics",
            "Custom domain"
        ]
    ),
    PlanTier.ENTERPRISE: SubscriptionPlan(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        price_monthly=499,
        price_yearly=4990,
        max_api_calls_per_month=-1,  # Unlimited
        max_storage_gb=-1,  # Unlimited
        max_users=-1,  # Unlimited
        max_api_keys=-1,  # Unlimited
        features=[
            "Unlimited API calls",
            "Unlimited storage",
            "Dedicated support",
            "SLA guarantee (99.9%)",
            "On-premise deployment option",
            "Custom integrations",
            "Dedicated account manager"
        ]
    )
}
```

### Stripe Integration

```python
# src/services/stripe_service.py

import stripe
from typing import Optional

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Handle Stripe billing operations"""

    def create_customer(
        self,
        tenant_id: str,
        email: str,
        company_name: str
    ) -> str:
        """Create Stripe customer"""

        customer = stripe.Customer.create(
            email=email,
            name=company_name,
            metadata={"tenant_id": tenant_id}
        )

        return customer.id

    def create_subscription(
        self,
        customer_id: str,
        plan_tier: PlanTier,
        billing_period: str = "monthly"
    ) -> dict:
        """Create subscription"""

        price_id = self._get_price_id(plan_tier, billing_period)

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )

        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret,
            "status": subscription.status
        }

    def handle_webhook(self, payload: dict, sig_header: str):
        """Handle Stripe webhook events"""

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")

        # Handle different event types
        if event.type == "customer.subscription.updated":
            self._handle_subscription_updated(event.data.object)
        elif event.type == "customer.subscription.deleted":
            self._handle_subscription_deleted(event.data.object)
        elif event.type == "invoice.payment_succeeded":
            self._handle_payment_succeeded(event.data.object)
        elif event.type == "invoice.payment_failed":
            self._handle_payment_failed(event.data.object)

    def _handle_subscription_updated(self, subscription):
        """Update tenant subscription status"""
        tenant_id = subscription.metadata.get("tenant_id")

        # Update in database
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        tenant.subscription_status = subscription.status
        tenant.current_period_end = datetime.fromtimestamp(
            subscription.current_period_end
        )
        db.commit()
```

---

## Usage Tracking & Quotas

### Usage Tracking

```python
# src/services/usage_tracker.py

from redis import Redis
from datetime import datetime, timedelta

class UsageTracker:
    """Track API usage and enforce quotas"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def track_api_call(
        self,
        tenant_id: str,
        endpoint: str,
        response_time_ms: float
    ):
        """Track API call"""

        # Daily counter
        today = datetime.utcnow().date().isoformat()
        key = f"usage:{tenant_id}:{today}:api_calls"

        self.redis.incr(key)
        self.redis.expire(key, 86400 * 31)  # Keep for 31 days

        # Store in PostgreSQL for long-term analytics
        usage_log = UsageLog(
            tenant_id=tenant_id,
            endpoint=endpoint,
            timestamp=datetime.utcnow(),
            response_time_ms=response_time_ms
        )
        db.add(usage_log)
        db.commit()

    def check_quota(self, tenant_id: str) -> dict:
        """Check if tenant is within quota"""

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        plan = PLANS[tenant.plan_tier]

        # Get current usage
        today = datetime.utcnow().date().isoformat()
        month_start = datetime.utcnow().replace(day=1).date().isoformat()

        monthly_calls = self._get_usage_range(tenant_id, month_start, today)

        # Check quota
        max_calls = plan.max_api_calls_per_month
        within_quota = (max_calls == -1) or (monthly_calls < max_calls)

        return {
            "within_quota": within_quota,
            "current_usage": monthly_calls,
            "quota_limit": max_calls,
            "usage_percentage": (monthly_calls / max_calls * 100) if max_calls > 0 else 0
        }

    def _get_usage_range(
        self,
        tenant_id: str,
        start_date: str,
        end_date: str
    ) -> int:
        """Get total API calls in date range"""

        total = 0
        current_date = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        while current_date <= end:
            key = f"usage:{tenant_id}:{current_date.isoformat()}:api_calls"
            count = self.redis.get(key)
            if count:
                total += int(count)
            current_date += timedelta(days=1)

        return total
```

### Rate Limiting

```python
# src/middleware/rate_limit.py

from fastapi import Request, HTTPException
from redis import Redis
import time

class RateLimiter:
    """Rate limiting middleware"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        request: Request,
        tenant_id: str
    ):
        """Check rate limit for tenant"""

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        plan = PLANS[tenant.plan_tier]

        # Rate limit: calls per minute
        limits = {
            PlanTier.FREE: 10,       # 10/min
            PlanTier.PRO: 100,       # 100/min
            PlanTier.ENTERPRISE: 1000  # 1000/min
        }

        max_calls = limits.get(plan.tier, 10)

        # Sliding window rate limiting
        now = int(time.time())
        window = 60  # 1 minute

        key = f"rate_limit:{tenant_id}:{now // window}"

        # Increment counter
        count = self.redis.incr(key)
        self.redis.expire(key, window)

        if count > max_calls:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {max_calls} requests/minute"
            )

        # Add rate limit headers
        request.state.rate_limit_remaining = max_calls - count
        request.state.rate_limit_limit = max_calls
```

---

## API Key Management

### API Key CRUD

```python
# src/api/v1/api_keys.py

from fastapi import APIRouter, Depends
from src.core.auth.api_key_handler import APIKeyManager

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user)
):
    """Create new API key"""

    manager = APIKeyManager()

    # Check if tenant can create more keys
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    plan = PLANS[tenant.plan_tier]

    existing_keys = db.query(APIKey).filter(
        APIKey.tenant_id == current_user.tenant_id,
        APIKey.is_active == True
    ).count()

    if plan.max_api_keys != -1 and existing_keys >= plan.max_api_keys:
        raise HTTPException(
            status_code=403,
            detail=f"Maximum API keys ({plan.max_api_keys}) reached"
        )

    # Generate key
    result = manager.generate_api_key(
        tenant_id=current_user.tenant_id,
        name=request.name
    )

    return APIKeyResponse(**result)

@router.get("/", response_model=List[APIKeyInfo])
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """List all API keys for tenant"""

    keys = db.query(APIKey).filter(
        APIKey.tenant_id == current_user.tenant_id
    ).all()

    return [
        APIKeyInfo(
            id=k.id,
            name=k.name,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            is_active=k.is_active
        )
        for k in keys
    ]

@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Revoke API key"""

    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.tenant_id == current_user.tenant_id
    ).first()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.is_active = False
    db.commit()

    return {"message": "API key revoked"}
```

---

## Admin Dashboard

### Admin API Endpoints

```python
# src/api/v1/admin.py

from fastapi import APIRouter, Depends
from src.core.auth.rbac import require_permission, Permission

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/tenants")
@require_permission(Permission.TENANT_MANAGE)
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin)
):
    """List all tenants (admin only)"""

    tenants = db.query(Tenant).offset(skip).limit(limit).all()

    return [
        {
            "id": t.id,
            "company_name": t.company_name,
            "plan_tier": t.plan_tier,
            "status": t.status,
            "created_at": t.created_at,
            "api_calls_this_month": get_usage(t.id)
        }
        for t in tenants
    ]

@router.get("/usage/summary")
async def usage_summary(current_user: User = Depends(get_current_admin)):
    """Get system-wide usage summary"""

    return {
        "total_tenants": db.query(Tenant).count(),
        "active_tenants": db.query(Tenant).filter(
            Tenant.status == "active"
        ).count(),
        "total_api_calls_today": get_total_usage_today(),
        "total_revenue_mrr": calculate_mrr(),
        "plan_distribution": {
            "free": db.query(Tenant).filter(Tenant.plan_tier == PlanTier.FREE).count(),
            "pro": db.query(Tenant).filter(Tenant.plan_tier == PlanTier.PRO).count(),
            "enterprise": db.query(Tenant).filter(Tenant.plan_tier == PlanTier.ENTERPRISE).count()
        }
    }

@router.post("/tenants/{tenant_id}/upgrade")
@require_permission(Permission.TENANT_MANAGE)
async def upgrade_tenant(
    tenant_id: str,
    new_plan: PlanTier,
    current_user: User = Depends(get_current_admin)
):
    """Manually upgrade tenant plan"""

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.plan_tier = new_plan
    db.commit()

    return {"message": f"Tenant upgraded to {new_plan}"}
```

---

## Database Schema

### SQL Schema

```sql
-- Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,

    -- Subscription
    plan_tier VARCHAR(50) NOT NULL DEFAULT 'free',
    subscription_status VARCHAR(50) NOT NULL DEFAULT 'active',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    current_period_end TIMESTAMP,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- active, suspended, canceled

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'member',  -- admin, member, viewer, billing

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP,

    UNIQUE(tenant_id, email)
);

-- API Keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP
);

-- Usage logs table
CREATE TABLE usage_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_usage_logs_tenant_timestamp ON usage_logs(tenant_id, timestamp DESC);
CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_users_tenant ON users(tenant_id);

-- Enable RLS
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;

-- RLS policy
CREATE POLICY tenant_isolation_usage_logs ON usage_logs
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

---

## Implementation

### Setup Steps

1. **Database Setup**:
```bash
# Run migrations
alembic revision --autogenerate -m "Add SaaS tables"
alembic upgrade head
```

2. **Environment Variables**:
```bash
# Stripe
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Plans
DEFAULT_PLAN=free
```

3. **Create Tenant**:
```python
# Example tenant creation
from src.services.tenant_service import TenantService

service = TenantService()

tenant = service.create_tenant(
    company_name="Acme Corp",
    subdomain="acme",
    admin_email="admin@acme.com",
    admin_password="secret123",
    plan_tier=PlanTier.PRO
)

print(f"Tenant created: {tenant.id}")
print(f"Access: https://acme.rag-enterprise.com")
```

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
