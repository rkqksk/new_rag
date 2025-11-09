# Security Policy & Best Practices

**Version**: 1.0.0
**Last Updated**: 2025-11-09
**Status**: Production-Ready

---

## 🔐 Table of Contents

1. [Overview](#overview)
2. [Environment Variables](#environment-variables)
3. [API Key Management](#api-key-management)
4. [Git Security](#git-security)
5. [Cleaning Leaked Secrets](#cleaning-leaked-secrets)
6. [Database Security](#database-security)
7. [Production Checklist](#production-checklist)
8. [Incident Response](#incident-response)

---

## Overview

This document outlines security best practices for the RAG Enterprise project. **Never commit secrets, API keys, or sensitive data to version control.**

### Quick Security Check

```bash
# Check if .env files are ignored
git check-ignore -v .env .env.local .env.production

# Search for potential secrets in git history
git log --all --full-history -p | grep -i -E "(api_key|secret|password|token)" | head -20

# Verify no .env files are tracked
git ls-files | grep -E "\.env$|\.env\." | grep -v ".env.example"
```

---

## Environment Variables

### ✅ DO

- **Use `.env.example` as template** - Commit this with placeholder values
- **Create local `.env` from template** - `cp .env.example .env`
- **Use strong, randomly generated secrets** - Minimum 32 characters
- **Rotate keys regularly** - At least every 90 days
- **Use different keys per environment** - dev, staging, production

### ❌ DON'T

- **Never commit `.env` files** - Already in `.gitignore`
- **Never hardcode secrets in code** - Use environment variables
- **Never share API keys in chat/email** - Use secure password managers
- **Never use default passwords in production** - Change all defaults
- **Never reuse API keys across projects** - One key per project

### Generating Secure Secrets

```bash
# JWT Secret Key (64 characters)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# API Key Salt (32 characters)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL Alternative
openssl rand -base64 64
```

### Required Environment Variables

**Critical (Must Change in Production)**:
- `JWT_SECRET_KEY` - Token signing key
- `DB_PASSWORD` - PostgreSQL password
- `STRIPE_SECRET_KEY` - Stripe API key (if using billing)
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook verification

**Optional (External Services)**:
- `OPENAI_API_KEY` - OpenAI API (if using GPT models)
- `ANTHROPIC_API_KEY` - Claude API (if using Anthropic)
- `NEXA_API_KEY` - NexaAI Cloud (if not using local)

---

## API Key Management

### Best Practices

1. **Separate Keys by Environment**
   ```bash
   # Development
   OPENAI_API_KEY=sk-proj-dev-xxx

   # Production
   OPENAI_API_KEY=sk-proj-prod-yyy
   ```

2. **Use Key Naming Convention**
   ```
   <service>_<environment>_<purpose>
   Example: STRIPE_PROD_WEBHOOK_SECRET
   ```

3. **Set Expiration Dates**
   - Add to `.env` as comments
   - Set calendar reminders for rotation

4. **Restrict Key Permissions**
   - Use read-only keys when possible
   - Enable IP restrictions on cloud providers
   - Set usage limits/quotas

### Stripe API Keys

```bash
# Test Mode (Development)
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...

# Live Mode (Production)
STRIPE_SECRET_KEY=sk_live_51...  # ⚠️ NEVER commit!
STRIPE_PUBLISHABLE_KEY=pk_live_51...  # OK to expose (frontend)
```

### OpenAI API Keys

```bash
# Project API Key (Recommended)
OPENAI_API_KEY=sk-proj-xxx  # Scoped to specific project

# Legacy API Key
OPENAI_API_KEY=sk-xxx  # Avoid using legacy keys
```

---

## Git Security

### .gitignore Configuration

The `.gitignore` file has been configured to exclude:

**Environment Files**:
- `.env`, `.env.local`, `.env.*.local`
- `*.env`, `*.env.*` (except `.env.example`)

**Credentials**:
- `*.key`, `*.pem`, `*.p12`, `*.pfx`
- `credentials.json`, `secrets.yaml`
- `*api_key*`, `*secret_key*`, `*token*`

**Cloud Provider Credentials**:
- `.aws/`, `.gcp/`, `.azure/`
- `terraform.tfstate`, `*.tfvars`

**Database Backups**:
- `*.sql`, `*.dump`, `*.backup`
- `database_backup/`, `db_backups/`

### Verify .gitignore

```bash
# Test if files are ignored
git check-ignore -v .env  # Should show .gitignore rule
git check-ignore -v credentials.json
git check-ignore -v secrets.yaml

# List all tracked files (should NOT include .env)
git ls-files | grep -E "\.env$|credentials|secrets"
```

---

## Cleaning Leaked Secrets

### If You Accidentally Committed Secrets

**⚠️ IMPORTANT**: Once pushed to GitHub, consider secrets compromised. Rotate them immediately!

### Step 1: Rotate All Exposed Keys

```bash
# OpenAI
1. Go to https://platform.openai.com/api-keys
2. Revoke compromised key
3. Create new key
4. Update .env with new key

# Stripe
1. Go to https://dashboard.stripe.com/apikeys
2. Click "..." → "Delete" on compromised key
3. Create new restricted key
4. Update .env with new key

# JWT Secret
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
# Update JWT_SECRET_KEY in .env
```

### Step 2: Remove from Git History

**Option A: BFG Repo-Cleaner** (Recommended - Fast & Safe)

```bash
# Install BFG
brew install bfg  # macOS
# OR download from: https://rtyley.github.io/bfg-repo-cleaner/

# Clone a fresh copy (backup!)
git clone --mirror git@github.com:rkqksk/rag-enterprise.git

# Remove all .env files from history
bfg --delete-files .env --delete-files '.env.*' rag-enterprise.git

# Clean up
cd rag-enterprise.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (⚠️ Dangerous - coordinate with team!)
git push --force
```

**Option B: git-filter-repo** (More Control)

```bash
# Install git-filter-repo
pip install git-filter-repo

# Analyze repository
git filter-repo --analyze

# Remove .env files
git filter-repo --invert-paths --path .env --path '.env.*' --force

# Force push
git push --force --all
git push --force --tags
```

**Option C: GitHub Secret Scanning** (Detection Only)

GitHub will automatically detect exposed secrets:
1. Go to repository Settings → Security → Secret scanning alerts
2. Review detected secrets
3. Follow remediation steps

### Step 3: Verify Cleanup

```bash
# Search for removed secrets
git log --all --full-history -p | grep -i "sk-proj-" | head -10
# Should return empty

# Verify .env is not in history
git log --all --full-history -- .env
# Should return empty after cleanup
```

### Step 4: Update .gitignore

```bash
# Ensure .gitignore has comprehensive patterns
git add .gitignore
git commit -m "security: Update .gitignore with comprehensive secret patterns"
git push
```

---

## Database Security

### PostgreSQL

```bash
# Strong password requirements
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words

# Generate secure password
python3 -c "import secrets; print(secrets.token_urlsafe(24))"

# Connection string (NEVER commit!)
postgresql://user:password@localhost:5432/database
```

### Redis

```bash
# Enable authentication
requirepass your_strong_redis_password

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

### Qdrant

```bash
# Enable API key authentication
QDRANT_API_KEY=your_secure_qdrant_key

# Use HTTPS in production
QDRANT_HTTPS=true
```

---

## Production Checklist

### Before Deployment

- [ ] All secrets rotated from development values
- [ ] `DEBUG=false` in production `.env`
- [ ] `ENVIRONMENT=production`
- [ ] Strong passwords (16+ characters)
- [ ] HTTPS enabled for all services
- [ ] CORS origins restricted (no `*`)
- [ ] Database backups configured
- [ ] Error tracking enabled (Sentry)
- [ ] Rate limiting enabled
- [ ] API key rotation schedule set
- [ ] Security headers configured
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection enabled

### Security Headers

```python
# app/middleware/security.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/qa/")
@limiter.limit("10/minute")  # 10 requests per minute
async def qa_endpoint(request: Request):
    pass
```

---

## Incident Response

### If API Key Leaked

1. **Immediate Actions (< 5 minutes)**
   - [ ] Revoke compromised key in service dashboard
   - [ ] Create new key with same permissions
   - [ ] Update production `.env` with new key
   - [ ] Restart affected services

2. **Investigation (< 1 hour)**
   - [ ] Check service logs for unauthorized usage
   - [ ] Review billing for unexpected charges
   - [ ] Identify how leak occurred (git, logs, error messages)
   - [ ] Document timeline of events

3. **Remediation (< 24 hours)**
   - [ ] Remove secret from git history (BFG/filter-repo)
   - [ ] Force push cleaned history
   - [ ] Notify team members to re-clone repository
   - [ ] Update `.gitignore` if needed
   - [ ] Add pre-commit hooks to prevent future leaks

4. **Prevention**
   - [ ] Enable GitHub secret scanning
   - [ ] Install git-secrets locally: `brew install git-secrets`
   - [ ] Add pre-commit hook for secret detection
   - [ ] Schedule key rotation (90 days)
   - [ ] Conduct security review

### Contact Information

**Security Issues**: security@yourcompany.com
**Emergency Contact**: +1-XXX-XXX-XXXX
**Incident Response Team**: [Link to team contacts]

---

## Tools & Resources

### Recommended Tools

1. **git-secrets** - Prevent committing secrets
   ```bash
   brew install git-secrets
   git secrets --install
   git secrets --register-aws
   ```

2. **BFG Repo-Cleaner** - Remove secrets from history
   ```bash
   brew install bfg
   ```

3. **1Password CLI** - Secure secret management
   ```bash
   brew install --cask 1password-cli
   ```

4. **Trivy** - Vulnerability scanning
   ```bash
   brew install trivy
   trivy fs .
   ```

5. **detect-secrets** - Baseline secret scanning
   ```bash
   pip install detect-secrets
   detect-secrets scan > .secrets.baseline
   ```

### GitHub Security Features

- **Secret Scanning**: Automatic detection of exposed secrets
- **Dependabot**: Automated dependency updates
- **Code Scanning**: Static analysis for vulnerabilities
- **Security Advisories**: Private vulnerability reporting

### External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Stripe Security Best Practices](https://stripe.com/docs/security/guide)
- [OpenAI API Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)

---

## Summary

**Golden Rules**:
1. 🔒 Never commit secrets to git
2. 🔄 Rotate keys every 90 days
3. 🔐 Use strong, unique passwords (16+ chars)
4. 🚫 Revoke exposed keys immediately
5. 📝 Document all security incidents

**Emergency Contacts**:
- Rotate keys immediately if compromised
- Document incident in `docs/incidents/`
- Notify team and stakeholders
- Review and improve security practices

---

**Version**: 1.0.0
**Last Reviewed**: 2025-11-09
**Next Review**: 2026-02-09 (90 days)
**Owner**: Security Team
