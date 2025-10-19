# GitHub Actions Secrets Management Guide

Complete guide for setting up and managing the 22 required secrets for RAG Enterprise CI/CD pipelines.

## Overview

RAG Enterprise CI/CD requires 22 secrets across different categories. This guide provides detailed setup instructions for each secret.

## Secret Categories

### 1. Infrastructure Secrets (5)

#### `AWS_ACCESS_KEY_ID` (Staging)
**Purpose**: AWS credentials for staging environment deployment  
**Setup**:
```bash
# Create IAM user for CI/CD
aws iam create-user --user-name rag-enterprise-ci-staging

# Attach EKS policies
aws iam attach-user-policy --user-name rag-enterprise-ci-staging \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Create access key
aws iam create-access-key --user-name rag-enterprise-ci-staging
```
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `AKIAIOSFODNN7EXAMPLE`

#### `AWS_SECRET_ACCESS_KEY` (Staging)
**Purpose**: AWS secret key for staging  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

#### `AWS_ACCESS_KEY_ID_PROD` (Production)
**Purpose**: AWS credentials for production environment deployment  
**Setup**: Same as staging, but create separate IAM user `rag-enterprise-ci-production`  
**GitHub**: Settings → Environments → production → Add secret  
**Best Practice**: Use separate AWS accounts for staging/production

#### `AWS_SECRET_ACCESS_KEY_PROD` (Production)
**Purpose**: AWS secret key for production  
**GitHub**: Settings → Environments → production → Add secret

#### `AWS_REGION`
**Purpose**: AWS region for all deployments  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `us-east-1` (or your preferred region)

### 2. Database Secrets (3)

#### `POSTGRES_USER`
**Purpose**: PostgreSQL database username  
**Recommendation**: Use different credentials per environment  
**GitHub**: Repository secret (override in environments if needed)  
**Value Format**: `rag_user`

#### `POSTGRES_PASSWORD`
**Purpose**: PostgreSQL database password  
**Security**: Generate strong password (≥32 characters)  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Example Generation**:
```bash
openssl rand -base64 32
```

#### `POSTGRES_DB`
**Purpose**: Database name  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `rag_enterprise`

### 3. Container Registry Secrets (1)

#### `GITHUB_TOKEN`
**Purpose**: GitHub Container Registry authentication  
**Setup**: **Automatically provided by GitHub Actions** - no manual setup required  
**Permissions**: Ensure workflow has `packages: write` permission in workflow file

### 4. Security Secrets (2)

#### `COSIGN_PRIVATE_KEY`
**Purpose**: Container image signing with Cosign  
**Setup**:
```bash
# Generate signing key
cosign generate-key-pair

# This creates:
# - cosign.key (private key)
# - cosign.pub (public key)
```
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value**: Paste contents of `cosign.key` file

#### `COSIGN_PASSWORD`
**Purpose**: Password for Cosign private key  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value**: Password entered during `cosign generate-key-pair`

### 5. Monitoring Secrets (2)

#### `CODECOV_TOKEN`
**Purpose**: Code coverage reporting to Codecov  
**Setup**:
1. Sign up at https://codecov.io
2. Add repository
3. Copy upload token
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

#### `SENTRY_DSN`
**Purpose**: Error tracking with Sentry  
**Setup**:
1. Create Sentry project
2. Copy DSN from project settings
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `https://xxxxxxxxxxxx@sentry.io/1234567`

### 6. Notification Secrets (4)

#### `SLACK_WEBHOOK_URL`
**Purpose**: General deployment notifications  
**Setup**:
1. Go to Slack workspace settings
2. Create Incoming Webhook
3. Select channel (e.g., #rag-enterprise-deployments)
4. Copy webhook URL
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`

#### `SLACK_SECURITY_WEBHOOK_URL`
**Purpose**: Security alert notifications  
**Setup**: Same as above, but create webhook for security channel  
**Recommended Channel**: `#rag-enterprise-security`  
**GitHub**: Settings → Secrets → Actions → New repository secret

#### `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
**Purpose**: Email notifications for releases  
**Setup** (example with Gmail):
```yaml
SMTP_SERVER: smtp.gmail.com
SMTP_PORT: 587
SMTP_USERNAME: your-email@gmail.com
SMTP_PASSWORD: app-specific-password
```
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Note**: For Gmail, create app-specific password in account settings

#### `RELEASE_NOTIFICATION_EMAIL`
**Purpose**: Email recipient for release notifications  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `team@example.com` or comma-separated list

### 7. Application Secrets (5)

#### `JWT_SECRET_KEY`
**Purpose**: JWT token signing  
**Security**: Generate cryptographically secure random string  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Example Generation**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### `ANTHROPIC_API_KEY` (Optional)
**Purpose**: Claude API access  
**Setup**: Get from https://console.anthropic.com  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `sk-ant-api03-...`

#### `OPENAI_API_KEY` (Optional)
**Purpose**: OpenAI API access  
**Setup**: Get from https://platform.openai.com  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `sk-...`

#### `EMBEDDING_MODEL`
**Purpose**: Default embedding model name  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `sentence-transformers/all-MiniLM-L6-v2`

#### `OLLAMA_DEFAULT_MODEL`
**Purpose**: Default Ollama LLM model  
**GitHub**: Settings → Secrets → Actions → New repository secret  
**Value Format**: `qwen2.5:7b-instruct-q4_K_M`

## Security Best Practices

### Secret Generation

```bash
# Strong random password (32 bytes)
openssl rand -base64 32

# URL-safe token (64 bytes)
python -c "import secrets; print(secrets.token_urlsafe(64))"

# UUID
uuidgen
```

### Secret Rotation

**Rotation Schedule**:
- **Quarterly**: Database passwords, JWT keys
- **Annually**: AWS access keys, API tokens
- **Immediately**: If compromised or suspected exposure

**Rotation Process**:
1. Generate new secret
2. Update in GitHub Secrets
3. Deploy to staging
4. Verify functionality
5. Deploy to production
6. Revoke old secret
7. Document rotation in change log

### Secret Access Control

**Repository Secrets**: Accessible to all workflows  
**Environment Secrets**: Require environment approval

**Principle of Least Privilege**:
- Use environment secrets for production
- Limit IAM permissions to minimum required
- Use separate AWS accounts for environments
- Enable MFA for AWS IAM users

### Secret Verification

After setting all secrets, verify with:

```bash
# List configured secrets (names only, values hidden)
gh secret list

# Test deployment with secrets
Actions → Deploy → Run workflow (staging)
```

## Troubleshooting

### Missing Secret Error

**Error**: `Error: Input required and not supplied: AWS_ACCESS_KEY_ID`

**Solution**:
1. Verify secret name matches exactly (case-sensitive)
2. Check secret is in correct scope (repository vs environment)
3. Verify workflow has access to environment secrets

### Invalid Secret Format

**Error**: `Error: Invalid AWS credentials`

**Solution**:
1. Verify no extra whitespace in secret value
2. Check secret hasn't expired (AWS keys)
3. Verify IAM permissions are correct
4. Test credentials locally first

### Secret Not Available in Workflow

**Error**: `Warning: Secret 'PROD_SECRET' is not available`

**Solution**:
1. Environment secrets require environment specification in workflow
2. Check workflow has correct environment context
3. Verify approval requirements are met

## Quick Reference

**Total Secrets**: 22  
**Repository Secrets**: 17  
**Environment Secrets**: 5 (production-specific)

**Setup Time**: ~30-45 minutes for all secrets

**Verification Checklist**:
- [ ] All 22 secrets configured
- [ ] Production secrets in environment scope
- [ ] Slack webhooks tested
- [ ] AWS credentials verified
- [ ] Database passwords strong (≥32 chars)
- [ ] JWT secret generated securely
- [ ] Test deployment runs successfully

## Support

**Issues**: Create GitHub issue with `secrets` label  
**Documentation**: See `docs/CI_CD_GUIDE.md`  
**Security Concerns**: Contact security team immediately

---

**Last Updated**: 2025-01-19  
**Version**: 1.0
