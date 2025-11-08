# SaaS Platform Architecture Reference

**Purpose**: Detailed architecture for multi-tenant SaaS platform.

**See Also**: `docs/SAAS_ARCHITECTURE.md` for complete documentation.

---

## Multi-Tenancy Architecture

```
┌──────────────────────────────────────────┐
│           API Gateway Layer              │
│  (Tenant identification via JWT/API key) │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│      Application Layer (FastAPI)         │
│  • Authentication (JWT + API keys)       │
│  • Authorization (role-based)            │
│  • Tenant context injection              │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│       Data Layer (PostgreSQL)            │
│  • Row-Level Security (RLS)              │
│  • Tenant isolation                      │
│  • Shared tables with tenant_id FK       │
└──────────────────────────────────────────┘
```

---

## Authentication System

### JWT Tokens

**Structure**:
```json
{
  "sub": "user-123",              // User ID
  "tenant_id": "tenant-456",      // Tenant ID
  "email": "user@example.com",
  "role": "admin",
  "exp": 1699459200,              // Expiration (24h)
  "iat": 1699372800               // Issued at
}
```

**Generation**:
```python
from src.core.auth.jwt_handler import create_access_token

token = create_access_token(
    user_id="user-123",
    tenant_id="tenant-456",
    email="user@example.com",
    role="admin"
)
# Returns: "eyJhbGciOiJIUzI1NiIs..."
```

**Verification**:
```python
from src.core.auth.jwt_handler import verify_token

try:
    payload = verify_token(token)
    # Returns: {"sub": "user-123", "tenant_id": "tenant-456", ...}
except InvalidTokenError:
    # Token expired, invalid signature, etc.
    raise HTTPException(status_code=401, detail="Invalid token")
```

### API Keys

**Format**: `sk_live_<32_chars>` or `sk_test_<32_chars>`

**Hashing** (SHA-256):
```python
import hashlib

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
```

**Storage**:
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    key_hash TEXT NOT NULL,  -- SHA-256 hash
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP
);
```

---

## Billing System

### Stripe Integration

**Subscription Flow**:
1. User clicks "Upgrade to Pro"
2. Backend creates Stripe Checkout Session
3. User completes payment on Stripe
4. Stripe sends webhook to `/api/v1/saas/billing/webhook`
5. Backend updates subscription status in database

**Webhook Events**:
```python
# subscription.created
# → Create subscription record in DB

# subscription.updated
# → Update plan tier, status, period_end

# invoice.payment_succeeded
# → Mark invoice as paid, extend subscription

# invoice.payment_failed
# → Send notification, mark subscription as past_due
```

### Database Schema

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT NOT NULL,
    plan_tier TEXT NOT NULL,  -- free | pro | enterprise
    status TEXT NOT NULL,     -- active | past_due | canceled
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Usage Tracking

### Dual-Storage Architecture

**Redis** (Fast Counters):
```
Key: usage:{tenant_id}:2025-11:api_calls
Value: 45230
TTL: End of month

Key: rate_limit:{tenant_id}:1699459200  # Window timestamp
Value: 87  # Requests in this minute
TTL: 60s
```

**PostgreSQL** (Long-term Analytics):
```sql
CREATE TABLE api_usage (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_api_usage_tenant_timestamp
ON api_usage(tenant_id, timestamp DESC);
```

### Quota Enforcement

```python
from src.services.usage_tracker import UsageTracker

tracker = UsageTracker()

# Check quota
quota = tracker.check_quota(tenant_id="tenant-123")

if not quota["within_quota"]:
    raise HTTPException(
        status_code=429,
        detail=f"Quota exceeded: {quota['current_usage']}/{quota['quota_limit']} API calls"
    )
```

### Rate Limiting (Sliding Window)

**Algorithm**:
```python
async def check_rate_limit(tenant_id: str, limit: int) -> bool:
    window = int(time.time()) // 60  # Current minute
    key = f"rate_limit:{tenant_id}:{window}"

    # Increment counter
    count = await redis.incr(key)

    # Set expiration on first request
    if count == 1:
        await redis.expire(key, 60)

    return count <= limit
```

---

## Database Design

### Tenant Isolation (Row-Level Security)

```sql
-- Enable RLS on all tenant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their own tenant's data
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- Set tenant context at session start
SET app.current_tenant = 'tenant-123';

-- All queries now automatically filter by tenant_id
SELECT * FROM users;  -- Only returns users for tenant-123
```

### Schema

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain TEXT UNIQUE,
    plan_tier TEXT NOT NULL DEFAULT 'free',
    stripe_customer_id TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    email TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',  -- admin | user
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    key_hash TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP
);
```

---

## Security

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash("SecurePassword123")

# Verify password
is_valid = pwd_context.verify("SecurePassword123", hashed)
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

**Full Documentation**: `docs/SAAS_ARCHITECTURE.md`
