---
name: saas-operations
description: SaaS multi-tenancy billing Stripe subscription authentication Keycloak OAuth2 JWT tenant isolation usage tracking rate limiting 테넌트 관리 결제 인증 사용량 추적 구독 관리
---

# SaaS Operations & Tenant Management

## When to Use
- 테넌트 생성, create tenant
- 멀티테넌시, multi-tenancy
- 결제 설정, billing setup
- 구독 관리, subscription management
- 인증 설정, authentication setup
- 사용량 추적, usage tracking
- Rate limiting
- Keycloak, OAuth2, JWT

## Core Capabilities
1. **Tenant Management** - Create, configure, isolate tenants
2. **Billing** - Stripe integration, subscription plans
3. **Authentication** - Keycloak OAuth2/OIDC, JWT tokens
4. **Usage Tracking** - Per-tenant quotas, metering
5. **Rate Limiting** - API throttling, fair usage

## Quick Actions

### Create Tenant
```python
# Automated provisioning
python scripts/create_tenant.py \
  --name "acme-corp" \
  --plan enterprise \
  --admin admin@acme.com \
  --features rag,vision,analytics
```

### Configure Billing
```python
# Stripe setup
python scripts/configure_billing.py \
  --tenant acme-corp \
  --plan monthly \
  --price 299 \
  --trial-days 14
```

### Setup Authentication
```python
# Keycloak realm
python scripts/setup_keycloak_realm.py \
  --tenant acme-corp \
  --clients web,mobile,api \
  --roles admin,user,readonly
```

### Monitor Usage
```python
# Usage dashboard
python scripts/monitor_usage.py \
  --tenant acme-corp \
  --metrics queries,storage,api_calls \
  --period last_30_days
```

## Tenant Isolation

### Database Level
```sql
-- Schema per tenant
CREATE SCHEMA tenant_acme;
CREATE SCHEMA tenant_beta;

-- Row-level security
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON products
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

### Application Level
```python
# Middleware
class TenantMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request):
        tenant_id = extract_tenant_from_token(request)
        request.state.tenant_id = tenant_id
        return await self.app(request)
```

## Billing Plans

### Tiers
- **Starter**: $29/month - 1,000 queries, 10GB storage
- **Professional**: $99/month - 10,000 queries, 100GB storage
- **Enterprise**: $299/month - Unlimited queries, 1TB storage

### Usage Metering
```python
# Track API calls
meter = UsageMeter(tenant_id="acme-corp")
meter.record("api_call", endpoint="/search", count=1)
meter.record("storage", bytes=1024000)

# Get current usage
usage = meter.get_usage(period="current_month")
```

## Authentication Flow

### OAuth2 + JWT
```python
# 1. User logs in via Keycloak
# 2. Keycloak returns JWT token
# 3. API validates JWT
# 4. Extract tenant_id from token claims
# 5. Apply tenant isolation

claims = {
    "sub": "user-uuid",
    "tenant_id": "acme-corp",
    "roles": ["admin"],
    "exp": timestamp
}
```

## Rate Limiting

### Per-Tenant Quotas
```python
# Redis-based rate limiting
from fastapi_limiter import FastAPILimiter

@app.post("/api/v1/search")
@limiter.limit("100/hour")  # Per tenant
async def search(request: Request):
    tenant_id = request.state.tenant_id
    # ... search logic
```

## Integration
- **deployment-automation**: Provision tenant resources
- **testing-suite**: Tenant isolation tests
- **excel-processing**: Usage reports
- **rag-optimization**: Per-tenant search optimization

## Key Files
- `src/middleware/tenant_middleware.py` - Tenant isolation
- `src/services/billing_service.py` - Stripe integration
- `src/auth/keycloak_client.py` - Authentication

## Security Checklist
- ✅ Data isolation (schema/RLS)
- ✅ JWT token validation
- ✅ Rate limiting per tenant
- ✅ Audit logging
- ✅ Secret rotation (Vault)
