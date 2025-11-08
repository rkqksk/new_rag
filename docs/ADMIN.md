# Admin Configuration

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Purpose**: System administrator configuration and superuser management

---

## 🔐 Superuser Configuration

### Default Superuser

**Email**: `rkqksk@gmail.com`

**Permissions**:
- Full system access
- User management
- Tenant management
- Billing configuration
- System settings
- API key generation
- Debug endpoints

### Initial Setup

#### 1. Create Superuser Account

```python
# Run this script to create superuser
from app.services.auth import create_superuser

superuser = create_superuser(
    email="rkqksk@gmail.com",
    password="your-secure-password",  # Change this!
    full_name="System Administrator"
)
```

#### 2. Verify Superuser Access

```bash
# Test login API
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "rkqksk@gmail.com",
    "password": "your-password"
  }'

# Expected response:
# {
#   "access_token": "eyJ...",
#   "token_type": "bearer",
#   "user": {
#     "email": "rkqksk@gmail.com",
#     "is_superuser": true
#   }
# }
```

---

## 👥 Additional Administrators

**Important**: Only the superuser (`rkqksk@gmail.com`) can create additional admin accounts.

### Creating Admin Users

```python
from app.services.auth import create_admin_user

# Superuser creates new admin
new_admin = create_admin_user(
    email="admin2@example.com",
    password="secure-password",
    full_name="Secondary Admin",
    permissions=["user_management", "tenant_management"]
)
```

### Admin Permission Levels

| Permission Level | Description | Capabilities |
|------------------|-------------|--------------|
| **superuser** | Full system access | Everything |
| **admin** | Limited admin access | User/tenant management |
| **tenant_admin** | Tenant-level admin | Manage own tenant |
| **user** | Regular user | Basic access |

---

## 🔑 API Key Management

### Generate Superuser API Key

```bash
# Using superuser JWT token
curl -X POST http://localhost:8001/api/v1/admin/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Superuser API Key",
    "permissions": ["admin:*"]
  }'

# Response includes API key (save this - shown only once!)
```

### Using Superuser API Key

```bash
# Example: List all users
curl http://localhost:8001/api/v1/admin/users \
  -H "X-API-Key: YOUR_API_KEY"

# Example: Create tenant
curl -X POST http://localhost:8001/api/v1/admin/tenants \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Tenant",
    "plan": "pro"
  }'
```

---

## 🛡️ Security Best Practices

### Password Requirements

- Minimum 12 characters
- Must include uppercase, lowercase, numbers, special characters
- Cannot be common passwords
- Must be changed every 90 days (recommended)

### API Key Security

- Store API keys in environment variables or secrets manager
- Never commit API keys to git
- Rotate keys every 6 months
- Use different keys for different environments (dev/staging/prod)
- Set expiration dates for temporary keys

### JWT Token Security

- Tokens expire after 24 hours (default)
- Refresh tokens before expiration
- Implement token blacklisting for logout
- Use HTTPS only in production

---

## 🔧 Environment Variables

### Required for Production

```bash
# Superuser credentials
SUPERUSER_EMAIL=rkqksk@gmail.com
SUPERUSER_PASSWORD=your-secure-password  # Set via environment

# JWT configuration
JWT_SECRET_KEY=your-random-secret-key  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API security
API_RATE_LIMIT=1000  # Requests per hour
API_CORS_ORIGINS=["https://yourdomain.com"]
```

---

## 📊 Admin Endpoints

### User Management

```bash
# List all users
GET /api/v1/admin/users

# Get user details
GET /api/v1/admin/users/{user_id}

# Update user
PUT /api/v1/admin/users/{user_id}

# Delete user
DELETE /api/v1/admin/users/{user_id}

# Grant admin privileges
POST /api/v1/admin/users/{user_id}/promote
```

### Tenant Management

```bash
# List all tenants
GET /api/v1/admin/tenants

# Create tenant
POST /api/v1/admin/tenants

# Update tenant plan
PUT /api/v1/admin/tenants/{tenant_id}/plan

# Suspend tenant
POST /api/v1/admin/tenants/{tenant_id}/suspend
```

### System Monitoring

```bash
# System health
GET /api/v1/admin/health

# System statistics
GET /api/v1/admin/stats

# Performance metrics
GET /api/v1/admin/metrics

# Recent errors
GET /api/v1/admin/errors
```

---

## 🚨 Emergency Procedures

### Password Reset (Superuser)

If superuser password is lost:

```bash
# Connect to database
docker exec -it postgres psql -U user -d rag_enterprise

# Reset password (hashed)
UPDATE users
SET password_hash = '$2b$12$...'  -- Generate with bcrypt
WHERE email = 'rkqksk@gmail.com';
```

### Lock User Account

```bash
# Temporarily disable account
curl -X POST http://localhost:8001/api/v1/admin/users/{user_id}/lock \
  -H "X-API-Key: YOUR_API_KEY"
```

### Emergency System Shutdown

```bash
# Graceful shutdown
docker-compose down

# Emergency shutdown (force)
docker-compose kill

# Stop specific service
docker-compose stop api
```

---

## 📝 Audit Logging

### Enable Audit Logs

```bash
# In .env
AUDIT_ENABLED=true
AUDIT_LOG_FILE=/var/log/rag-enterprise/audit.log
```

### Query Audit Logs

```bash
# View recent admin actions
curl http://localhost:8001/api/v1/admin/audit-logs \
  -H "X-API-Key: YOUR_API_KEY"

# Filter by user
curl "http://localhost:8001/api/v1/admin/audit-logs?user_email=rkqksk@gmail.com"

# Filter by action type
curl "http://localhost:8001/api/v1/admin/audit-logs?action=user_delete"
```

---

## 🔄 Backup & Recovery

### Database Backup (Admin Only)

```bash
# Manual backup
docker exec postgres pg_dump -U user rag_enterprise > backup_$(date +%Y%m%d).sql

# Automated backup (cron)
0 2 * * * docker exec postgres pg_dump -U user rag_enterprise > /backups/db_$(date +\%Y\%m\%d).sql
```

### Restore Database

```bash
# Restore from backup
docker exec -i postgres psql -U user rag_enterprise < backup_20251108.sql
```

---

## 📚 Related Documentation

- [OPEN_SOURCE_ARCHITECTURE.md](./OPEN_SOURCE_ARCHITECTURE.md) - System architecture
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment guide
- [docs/guides/LOCAL_SETUP.md](./guides/LOCAL_SETUP.md) - Local setup guide
- [SAAS_ARCHITECTURE.md](./SAAS_ARCHITECTURE.md) - SaaS platform details

---

## ⚠️ Important Notes

1. **Single Superuser**: Only `rkqksk@gmail.com` has superuser privileges
2. **No Self-Registration**: Admins cannot self-register, must be created by superuser
3. **Production Security**: Always use HTTPS, strong passwords, and rotate keys
4. **Audit Everything**: Enable audit logging for all admin actions
5. **Regular Backups**: Schedule automated database backups
6. **Monitor Access**: Review admin access logs regularly

---

**Superuser**: rkqksk@gmail.com
**Last Updated**: 2025-11-08
**Status**: ✅ Production Configuration
