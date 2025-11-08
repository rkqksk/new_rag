# SaaS Platform Integration Examples

**Purpose**: Real-world examples of SaaS platform integration.

---

## Example 1: Complete Tenant Onboarding Flow

### Scenario
New customer signs up, creates account, gets API key, starts using the platform.

### Implementation

```python
from src.services.tenant_service import TenantService
from src.services.billing_service import BillingService
from src.core.auth.jwt_handler import create_access_token
from src.core.auth.api_key_handler import generate_api_key

# 1. Register tenant (Signup)
tenant_service = TenantService()
billing_service = BillingService()

tenant = await tenant_service.create_tenant(
    name="Acme Corporation",
    domain="acme.com",
    admin_email="admin@acme.com",
    admin_password="SecurePassword123"
)
# Returns: {id, name, domain, plan_tier: "free", ...}

# 2. Create Stripe customer
stripe_customer = billing_service.create_customer(
    tenant_id=tenant["id"],
    email="admin@acme.com",
    name="Acme Corporation"
)

# 3. Login and get JWT token
jwt_token = create_access_token(
    user_id=tenant["admin_user_id"],
    tenant_id=tenant["id"],
    email="admin@acme.com",
    role="admin"
)
# Returns: "eyJhbGciOiJIUzI1NiIs..."

# 4. Create API key for backend service
api_key = generate_api_key(tenant_id=tenant["id"])
# Returns: "sk_live_abc123xyz789..." (show once!)

# 5. User can now make API calls
import httpx

headers = {
    "Authorization": f"Bearer {jwt_token}",
    # OR use API key:
    # "X-API-Key": api_key
}

response = httpx.post(
    "http://localhost:8001/api/v1/search",
    headers=headers,
    json={"query": "50ml PET bottle"}
)
```

---

## Example 2: Subscription Upgrade Flow

### Scenario
Free tier user hits quota limit, upgrades to Pro monthly.

### Implementation

```python
from src.services.usage_tracker import UsageTracker
from src.services.billing_service import BillingService

# 1. User makes API call
usage_tracker = UsageTracker()

# Check quota before processing
quota = usage_tracker.check_quota(tenant_id="tenant-123")

if not quota["within_quota"]:
    # Quota exceeded!
    return {
        "error": "Quota exceeded",
        "current": quota["current_usage"],
        "limit": quota["quota_limit"],
        "suggestion": "Upgrade to Pro for 100K API calls/month",
        "upgrade_url": "https://example.com/billing/upgrade"
    }

# 2. User decides to upgrade
billing_service = BillingService()

subscription = billing_service.create_subscription(
    customer_id="cus_123",  # From tenant.stripe_customer_id
    plan_tier="pro",
    billing_period="monthly"
)

# Returns:
# {
#   "subscription_id": "sub_abc123",
#   "status": "active",
#   "client_secret": "pi_123_secret_xyz",  # For Stripe.js
#   "payment_url": "https://checkout.stripe.com/..."
# }

# 3. User completes payment on Stripe
# Stripe sends webhook to /api/v1/saas/billing/webhook

# 4. Webhook handler updates subscription
@app.post("/api/v1/saas/billing/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    result = billing_service.handle_webhook(payload, sig_header)

    if result["event_type"] == "invoice.payment_succeeded":
        # Update tenant plan tier
        await tenant_service.update_plan_tier(
            tenant_id=result["tenant_id"],
            plan_tier="pro"
        )

# 5. User can now make 100K API calls/month
quota = usage_tracker.check_quota(tenant_id="tenant-123")
# {
#   "within_quota": True,
#   "current_usage": 1500,
#   "quota_limit": 100000,  # Now Pro tier!
#   "usage_percentage": 1.5
# }
```

---

## Example 3: API Key Authentication Middleware

### Scenario
Implement middleware to authenticate requests using API keys.

### Implementation

```python
from fastapi import Request, HTTPException
from src.core.auth.api_key_handler import verify_api_key
from src.services.tenant_service import TenantService

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Skip authentication for public endpoints
    if request.url.path in ["/health/live", "/health/ready"]:
        return await call_next(request)

    # Get API key from header
    api_key = request.headers.get("X-API-Key")

    if api_key:
        # Verify API key
        api_key_data = await verify_api_key(api_key)

        if not api_key_data:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Inject tenant context into request state
        request.state.tenant_id = api_key_data["tenant_id"]
        request.state.auth_type = "api_key"

        # Update last_used_at timestamp
        await update_api_key_last_used(api_key_data["id"])

    elif jwt_token := request.headers.get("Authorization"):
        # JWT authentication (alternative)
        token = jwt_token.replace("Bearer ", "")
        payload = verify_token(token)

        request.state.tenant_id = payload["tenant_id"]
        request.state.user_id = payload["sub"]
        request.state.auth_type = "jwt"

    else:
        raise HTTPException(status_code=401, detail="Missing authentication")

    # Continue to endpoint
    response = await call_next(request)
    return response
```

---

## Example 4: Usage Tracking and Rate Limiting

### Scenario
Track every API call, enforce rate limits per plan tier.

### Implementation

```python
from fastapi import Request, HTTPException
from src.services.usage_tracker import UsageTracker
import time

usage_tracker = UsageTracker()

@app.middleware("http")
async def usage_tracking_middleware(request: Request, call_next):
    tenant_id = request.state.tenant_id
    start_time = time.time()

    # 1. Check rate limit
    rate_limit = usage_tracker.check_rate_limit(tenant_id)

    if not rate_limit["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Reset at {rate_limit['reset_at']}",
            headers={"X-RateLimit-Remaining": "0"}
        )

    # 2. Check quota (optional: only for expensive endpoints)
    if request.url.path.startswith("/api/v1/search"):
        quota = usage_tracker.check_quota(tenant_id)

        if not quota["within_quota"]:
            raise HTTPException(
                status_code=429,
                detail=f"Quota exceeded: {quota['current_usage']}/{quota['quota_limit']}"
            )

    # 3. Process request
    response = await call_next(request)

    # 4. Track usage
    response_time_ms = (time.time() - start_time) * 1000

    usage_tracker.track_api_call(
        tenant_id=tenant_id,
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        response_time_ms=response_time_ms
    )

    # 5. Add rate limit headers to response
    response.headers["X-RateLimit-Limit"] = str(rate_limit["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_limit["remaining"])
    response.headers["X-RateLimit-Reset"] = rate_limit["reset_at"]

    return response
```

---

## Example 5: Multi-Tenant Query with Row-Level Security

### Scenario
Ensure all database queries are automatically scoped to current tenant.

### Implementation

```python
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from src.database import get_db

# 1. Set tenant context in middleware
@app.middleware("http")
async def set_tenant_context(request: Request, call_next):
    tenant_id = request.state.tenant_id

    # Set PostgreSQL session variable
    db = get_db()
    await db.execute(f"SET app.current_tenant = '{tenant_id}'")

    response = await call_next(request)
    return response

# 2. Row-Level Security (RLS) policies automatically filter queries
# (Already set up in database migration)

# 3. In endpoint, just query normally (RLS handles filtering)
@app.get("/api/v1/users")
async def list_users(db: Session = Depends(get_db)):
    # This query is automatically scoped to current tenant!
    users = db.query(User).all()

    # Only returns users for tenant_id = current_tenant
    return users

# 4. Prevent cross-tenant data access
@app.get("/api/v1/products/{product_id}")
async def get_product(
    product_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # Fetch product
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        # Either doesn't exist OR belongs to different tenant
        raise HTTPException(status_code=404, detail="Product not found")

    # product.tenant_id is guaranteed to match tenant_id due to RLS
    return product
```

---

## Example 6: Webhook Signature Verification

### Scenario
Securely handle Stripe webhooks with signature verification.

### Implementation

```python
import stripe
from fastapi import Request, HTTPException

@app.post("/api/v1/saas/billing/webhook")
async def stripe_webhook(request: Request):
    # 1. Get raw request body (IMPORTANT: Don't parse as JSON!)
    payload = await request.body()

    # 2. Get Stripe signature from headers
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature")

    # 3. Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 4. Handle event
    if event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        subscription_id = invoice["subscription"]

        # Update subscription in database
        await update_subscription_status(
            stripe_subscription_id=subscription_id,
            status="active",
            period_end=invoice["lines"]["data"][0]["period"]["end"]
        )

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice["subscription"]

        # Mark subscription as past_due
        await update_subscription_status(
            stripe_subscription_id=subscription_id,
            status="past_due"
        )

        # Send notification to tenant
        await send_payment_failed_email(invoice["customer_email"])

    return {"status": "success"}
```

---

## Example 7: Admin Dashboard - Tenant Management

### Scenario
Admin views all tenants, their usage, and can update plan tiers.

### Implementation

```python
from src.services.tenant_service import TenantService
from src.services.usage_tracker import UsageTracker

tenant_service = TenantService()
usage_tracker = UsageTracker()

@app.get("/api/v1/admin/tenants")
async def list_tenants(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_admin)
):
    # 1. Get all tenants
    tenants = await tenant_service.list_tenants(limit=limit, offset=offset)

    # 2. Enrich with usage data
    for tenant in tenants:
        usage = await usage_tracker.get_monthly_usage(tenant["id"])

        tenant["usage"] = {
            "api_calls": usage["api_calls"],
            "storage_gb": usage["storage_gb"],
            "quota_percentage": usage["quota_percentage"]
        }

    return {
        "tenants": tenants,
        "total": await tenant_service.count_tenants(),
        "limit": limit,
        "offset": offset
    }

@app.patch("/api/v1/admin/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    plan_tier: str,
    current_user: User = Depends(require_admin)
):
    # Admin can manually change plan tier
    await tenant_service.update_plan_tier(tenant_id, plan_tier)

    return {"status": "success", "tenant_id": tenant_id, "plan_tier": plan_tier}
```

---

## Best Practices Summary

### ✅ DO

1. **Always verify JWT/API key** on every request
2. **Use Row-Level Security** for automatic tenant isolation
3. **Track usage asynchronously** to avoid blocking requests
4. **Verify Stripe webhook signatures** (HMAC SHA-256)
5. **Rate limit per tenant** to prevent abuse
6. **Show API keys only once** at creation time
7. **Hash API keys** with SHA-256 (one-way)
8. **Use HTTP-only cookies** for JWT tokens (web apps)

### ❌ DON'T

1. **Don't store JWT in localStorage** (XSS vulnerability)
2. **Don't skip webhook signature verification** (security risk)
3. **Don't share API keys across tenants**
4. **Don't allow cross-tenant data access**
5. **Don't store plain API keys in database**
6. **Don't use same rate limit for all tiers**

---

**See Also**:
- `references/saas_architecture.md` - System architecture
- `docs/SAAS_ARCHITECTURE.md` - Complete documentation
