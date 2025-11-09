---
name: saas-platform
description: SaaS Platform Skill
---

# SaaS Platform Skill

**Purpose**: Multi-tenant SaaS platform management including authentication, billing, usage tracking, and tenant administration.

**Version**: 1.0.0 (v5.0.0 Platform)
**Status**: Production-ready ✅

---

## 🎯 Skill Overview

This skill provides comprehensive SaaS platform management capabilities:
- **Multi-Tenancy**: Tenant isolation with PostgreSQL Row-Level Security
- **Authentication**: JWT tokens (24h expiration) + API keys (tenant-scoped)
- **Billing**: Stripe integration (subscriptions, webhooks, invoices)
- **Usage Tracking**: API call tracking, quota enforcement, rate limiting
- **Plans**: Free ($0), Pro ($49/mo), Enterprise ($499/mo)

**Use this skill when:**
- Setting up multi-tenant authentication
- Implementing subscription billing with Stripe
- Tracking API usage and enforcing quotas
- Managing tenant accounts and users
- Configuring rate limiting per plan tier

**Architecture Reference**: §saas.* symbols → `docs/SAAS_ARCHITECTURE.md`

---

## 📋 Available Commands

### 1. `auth`
**Description**: Manage authentication (JWT tokens, API keys)

**Sub-commands**:
- `register` - Register new tenant
- `login` - User login (get JWT token)
- `create-key` - Create API key
- `list-keys` - List API keys
- `revoke-key` - Revoke API key

**Usage**:
```bash
# Register tenant
auth register <tenant_name> <admin_email> <password>

# User login
auth login <email> <password>

# Create API key
auth create-key <key_name> [--tenant-id <id>]

# List API keys
auth list-keys [--tenant-id <id>]

# Revoke API key
auth revoke-key <key_id>
```

**Example**:
```bash
# Register tenant "Acme Corp"
auth register "Acme Corp" admin@acme.com SecurePassword123

# Login as admin
auth login admin@acme.com SecurePassword123

# Create API key for backend service
auth create-key "Backend Service" --tenant-id tenant-123
```

**Output**:
```json
{
  "tenant_id": "tenant-123",
  "api_key": "sk_live_abc123xyz789...",
  "message": "⚠️ Save this key now! It won't be shown again."
}
```

---

### 2. `billing`
**Description**: Manage Stripe billing and subscriptions

**Sub-commands**:
- `subscription` - Get current subscription
- `upgrade` - Upgrade to Pro/Enterprise
- `cancel` - Cancel subscription
- `invoices` - List invoices

**Usage**:
```bash
# Get current subscription
billing subscription [--tenant-id <id>]

# Upgrade to Pro (monthly)
billing upgrade pro monthly [--tenant-id <id>]

# Upgrade to Enterprise (yearly, 20% discount)
billing upgrade enterprise yearly [--tenant-id <id>]

# Cancel subscription
billing cancel [--tenant-id <id>]

# List invoices
billing invoices [--limit <n>]
```

**Example**:
```bash
# Upgrade to Pro monthly
billing upgrade pro monthly --tenant-id tenant-123

# View subscription
billing subscription --tenant-id tenant-123

# Cancel subscription (end of billing period)
billing cancel --tenant-id tenant-123
```

**Output**:
```json
{
  "plan_tier": "pro",
  "status": "active",
  "billing_period": "monthly",
  "current_period_end": "2025-12-08",
  "payment_url": "https://checkout.stripe.com/..."
}
```

---

### 3. `usage`
**Description**: Track and monitor API usage

**Sub-commands**:
- `quota` - Check current quota status
- `stats` - View usage statistics
- `limits` - Show plan limits

**Usage**:
```bash
# Check quota
usage quota [--tenant-id <id>]

# Usage statistics
usage stats [--tenant-id <id>] [--period <month|week|day>]

# Show plan limits
usage limits [--plan-tier <free|pro|enterprise>]
```

**Example**:
```bash
# Check quota for current month
usage quota --tenant-id tenant-123

# Weekly usage stats
usage stats --tenant-id tenant-123 --period week

# Show Pro plan limits
usage limits --plan-tier pro
```

**Output**:
```json
{
  "plan_tier": "pro",
  "period": "2025-11",
  "api_calls": {
    "current": 45230,
    "limit": 100000,
    "percentage": 45.2,
    "within_quota": true
  },
  "storage": {
    "current_gb": 12.5,
    "limit_gb": 50,
    "percentage": 25.0
  },
  "rate_limit": {
    "per_minute": 100,
    "remaining": 87,
    "reset_at": "2025-11-08T10:35:00Z"
  }
}
```

---

### 4. `tenants`
**Description**: Manage tenants (admin only)

**Sub-commands**:
- `list` - List all tenants
- `get` - Get tenant details
- `update` - Update tenant info
- `delete` - Delete tenant (soft delete)

**Usage**:
```bash
# List all tenants
tenants list [--limit <n>] [--offset <n>]

# Get tenant details
tenants get <tenant_id>

# Update tenant
tenants update <tenant_id> --name <new_name>

# Delete tenant (soft delete)
tenants delete <tenant_id>
```

**Example**:
```bash
# List first 20 tenants
tenants list --limit 20

# Get tenant details
tenants get tenant-123

# Update tenant name
tenants update tenant-123 --name "Acme Corporation"
```

**Output**:
```json
{
  "id": "tenant-123",
  "name": "Acme Corporation",
  "domain": "acme.com",
  "plan_tier": "pro",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z",
  "user_count": 5,
  "api_calls_month": 45230
}
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Authentication - JWT
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Stripe Billing
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs
STRIPE_PRICE_PRO_MONTHLY=price_1234567890
STRIPE_PRICE_PRO_YEARLY=price_1234567890
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_1234567890
STRIPE_PRICE_ENTERPRISE_YEARLY=price_1234567890

# Usage Limits
FREE_API_CALLS_LIMIT=1000
PRO_API_CALLS_LIMIT=100000
ENTERPRISE_API_CALLS_LIMIT=-1  # Unlimited

FREE_RATE_LIMIT_PER_MINUTE=10
PRO_RATE_LIMIT_PER_MINUTE=100
ENTERPRISE_RATE_LIMIT_PER_MINUTE=1000
```

**Full Config**: `.env.example`

---

## 📚 References

### Progressive Disclosure
- **Quick Start**: This file (SKILL.md) - ~400 lines
- **Architecture**: `references/saas_architecture.md` - System design
- **Examples**: `examples/saas_examples.md` - Integration examples

### Symbol Navigation
- `§saas.status` - Platform status and capabilities
- `§saas.auth` - Authentication system (JWT + API keys)
- `§saas.billing` - Stripe billing integration
- `§saas.usage` - Usage tracking and quotas
- `§saas.tenants` - Multi-tenancy system

### Full Documentation
- **Architecture**: `docs/SAAS_ARCHITECTURE.md` (~35KB)
- **System Integration**: `docs/SYSTEM_INTEGRATION_GUIDE.md`
- **CLAUDE.md**: Quick reference with symbols

---

## 💡 Best Practices

### Authentication

```python
# ✅ Good: Use JWT for user sessions (24h expiration)
from src.core.auth.jwt_handler import create_access_token

token = create_access_token(user_id="user-123", tenant_id="tenant-456")
# Store in HTTP-only cookie or return to client

# ✅ Good: Use API keys for server-to-server
from src.core.auth.api_key_handler import generate_api_key

api_key = generate_api_key(tenant_id="tenant-456")
# Show to user once, store hashed version in DB

# ❌ Avoid: Storing JWT tokens in localStorage (XSS vulnerability)
# ❌ Avoid: Sharing API keys across tenants
```

### Billing

```python
# ✅ Good: Handle Stripe webhooks for subscription updates
@app.post("/api/v1/saas/billing/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    result = billing_service.handle_webhook(payload, sig_header)
    # Automatically updates subscription status

# ✅ Good: Provide payment links for upgrades
subscription = billing_service.create_subscription(
    customer_id="cus_123",
    plan_tier="pro",
    billing_period="monthly"
)
# Returns Stripe checkout URL

# ❌ Avoid: Storing credit card details (use Stripe only)
```

### Usage Tracking

```python
# ✅ Good: Track API calls in middleware
@app.middleware("http")
async def track_usage(request: Request, call_next):
    response = await call_next(request)

    usage_tracker.track_api_call(
        tenant_id=request.state.tenant_id,
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code
    )

    return response

# ✅ Good: Check quota before expensive operations
quota_status = usage_tracker.check_quota(tenant_id)
if not quota_status["within_quota"]:
    raise HTTPException(status_code=429, detail="Quota exceeded")

# ❌ Avoid: Tracking usage asynchronously without confirmation
```

### Rate Limiting

```python
# ✅ Good: Implement sliding window rate limiting
rate_limit_status = usage_tracker.check_rate_limit(tenant_id)
if not rate_limit_status["allowed"]:
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded. Reset at {rate_limit_status['reset_at']}"
    )

# ✅ Good: Different limits per plan tier
limits = {
    "free": 10,        # 10 req/min
    "pro": 100,        # 100 req/min
    "enterprise": 1000 # 1000 req/min
}

# ❌ Avoid: Same rate limit for all users
```

---

## 🔍 Troubleshooting

### Common Issues

**Issue**: "Invalid JWT token" error
**Solution**:
- Check `JWT_SECRET_KEY` matches between services
- Verify token hasn't expired (24h default)
- Ensure `JWT_ALGORITHM` is HS256

**Issue**: "Stripe webhook signature verification failed"
**Solution**:
- Verify `STRIPE_WEBHOOK_SECRET` is correct
- Check webhook endpoint URL in Stripe Dashboard
- Ensure raw request body is used (not parsed JSON)

**Issue**: "Rate limit exceeded" for Free tier users
**Solution**:
- Expected behavior (10 req/min limit)
- Suggest upgrading to Pro tier (100 req/min)
- Implement client-side request throttling

**Issue**: "Quota exceeded" mid-month
**Solution**:
- Check current usage: `usage quota --tenant-id <id>`
- Offer plan upgrade: `billing upgrade pro monthly`
- Or wait until next month (quota resets)

---

## 📊 Plan Comparison

### Features by Tier

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| **Price** | $0/mo | $49/mo | $499/mo |
| **API Calls** | 1K/month | 100K/month | Unlimited |
| **Storage** | 1GB | 50GB | 500GB |
| **Users** | 1 | 10 | Unlimited |
| **Rate Limit** | 10 req/min | 100 req/min | 1000 req/min |
| **Support** | Community | Email | Priority + SLA |
| **Custom Domain** | ❌ | ✅ | ✅ |
| **SSO** | ❌ | ❌ | ✅ |
| **Audit Logs** | ❌ | ✅ | ✅ |

### Deployment Costs (Infrastructure)

| Tier | Monthly Cost | Servers |
|------|--------------|---------|
| Free | $13/mo | 1x API (2GB RAM), shared DBs |
| Mid-tier | $54/mo | 1x API (4GB RAM), dedicated DBs |
| Enterprise | $405/mo | 3x API (8GB RAM), replicated DBs, monitoring |

---

## 🚀 Quick Start

### 1. Tenant Registration

```bash
# Register new tenant
auth register "Acme Corp" admin@acme.com SecurePassword123

# Login and get JWT token
auth login admin@acme.com SecurePassword123
```

### 2. Create API Key

```bash
# Create API key for backend service
auth create-key "Backend Service" --tenant-id tenant-123

# Save the API key (shown only once!)
# sk_live_abc123xyz789...
```

### 3. Check Usage

```bash
# Check current quota
usage quota --tenant-id tenant-123

# View usage stats
usage stats --tenant-id tenant-123 --period month
```

### 4. Upgrade to Pro

```bash
# Upgrade to Pro monthly
billing upgrade pro monthly --tenant-id tenant-123

# Complete payment at provided URL
# https://checkout.stripe.com/...
```

---

## 🔐 Security Best Practices

### JWT Tokens
- ✅ Use HTTP-only cookies for web apps
- ✅ Set 24h expiration (implement refresh tokens for longer sessions)
- ✅ Validate `tenant_id` claim on every request
- ❌ Never store in localStorage (XSS risk)

### API Keys
- ✅ Use SHA-256 hashing (one-way, irreversible)
- ✅ Show plain key only once at creation
- ✅ Rotate keys periodically (every 90 days)
- ❌ Never log API keys in plain text

### Stripe Integration
- ✅ Use Stripe webhooks for subscription updates
- ✅ Verify webhook signatures (HMAC SHA-256)
- ✅ Use test keys in development
- ❌ Never store credit card data

### Multi-Tenancy
- ✅ Use Row-Level Security (PostgreSQL)
- ✅ Validate `tenant_id` on every query
- ✅ Separate data physically for enterprise tier
- ❌ Never allow cross-tenant data access

---

## 📖 See Also

- **Data Collector Skill**: Universal data ingestion
- **RAG Pipeline Skill**: Vector search and retrieval
- **Manufacturing Expert Skill**: Quality control and inspection

---

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Maintainer**: RAG Enterprise Platform Team
