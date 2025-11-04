# RAG Enterprise CI/CD Guide

Complete guide for continuous integration and deployment pipelines.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Workflows](#workflows)
- [Secret Management](#secret-management)
- [Deployment Procedures](#deployment-procedures)
- [Troubleshooting](#troubleshooting)
- [Operational Runbooks](#operational-runbooks)

## Architecture Overview

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │   Push   │───▶│    CI    │───▶│  Build   │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│                        │               │                    │
│                        ▼               ▼                    │
│                  ┌──────────┐    ┌──────────┐             │
│                  │ Security │    │ Registry │             │
│                  └──────────┘    └──────────┘             │
│                                       │                     │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Deployment Pipeline                    │  │
│  │                                                     │  │
│  │  Staging                    Production              │  │
│  │    ├─ Deploy                  ├─ Manual Approval   │  │
│  │    ├─ Health Check            ├─ Canary (10%)      │  │
│  │    ├─ Integration Test        ├─ Monitor (5 min)   │  │
│  │    └─ Pass/Fail               └─ Full Rollout      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Execution Flow

1. **Continuous Integration** (7-10 min)
   - Lint: Code quality checks (parallel)
   - Security: SAST, dependency scanning (parallel)
   - Test: Unit + integration tests (parallel, multi-version)
   - Docker: Build, scan, verify

2. **Continuous Deployment** (20-40 min)
   - Build: Create Docker image, push to registry
   - Deploy Staging: Auto-deploy, health checks, integration tests
   - Deploy Production: Manual approval, canary deployment, monitoring

3. **Scheduled Tasks**
   - Security Scan: Daily at 02:00 UTC
   - Performance Benchmarks: Daily at 03:00 UTC
   - Dependency Updates: Weekly on Monday

## Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Purpose**: Validate code quality, security, and functionality

**Triggers**:
- Push to any branch
- Pull requests to main/develop
- Manual dispatch

**Jobs**:

#### Lint (2-3 min, parallel)
```yaml
Checks:
  - black: Code formatting
  - isort: Import ordering
  - flake8: Python linting
  - mypy: Type checking (--strict)
```

#### Security (3-4 min, parallel)
```yaml
Scanners:
  - bandit: Python SAST
  - safety: Dependency vulnerabilities
```

#### Test (5-7 min, parallel)
```yaml
Matrix:
  - Python 3.11 × unit tests
  - Python 3.11 × integration tests
  - Python 3.12 × unit tests
  - Python 3.12 × integration tests

Services:
  - PostgreSQL 15
  - Redis 7.2
  - Qdrant 1.11.3

Coverage: 80% minimum (enforced)
```

#### Docker (4-5 min)
```yaml
Steps:
  1. Build Docker image
  2. Verify size <500MB
  3. Trivy security scan
  4. Container health test
```

**Quality Gates**:
- ✅ All lint checks pass
- ✅ No CRITICAL/HIGH security issues
- ✅ Test coverage ≥80%
- ✅ Docker image <500MB
- ✅ No critical container vulnerabilities

### 2. Deploy Pipeline (`.github/workflows/deploy.yml`)

**Purpose**: Deploy to staging and production environments

**Triggers**:
- Push to main branch
- Manual workflow dispatch

**Jobs**:

#### Build (5-7 min)
```yaml
Steps:
  1. Run full CI pipeline
  2. Build Docker image
  3. Push to GitHub Container Registry
  4. Generate SBOM
  5. Sign image with Cosign
```

#### Deploy Staging (10-15 min, auto)
```yaml
Steps:
  1. Create backup
  2. Run database migrations
  3. Deploy with Helm
  4. Health check validation
  5. Smoke tests
  6. Rollback on failure
```

#### Integration Tests (10-15 min)
```yaml
Tests:
  - E2E test suite
  - API validation
  - Database integration
  - Cache verification
```

#### Deploy Production (10-15 min, manual)
```yaml
Strategy: Canary Deployment
  1. Manual approval gate
  2. Create production backup
  3. Run migrations
  4. Deploy canary (10% traffic)
  5. Monitor metrics (5 min)
  6. Promote to 100% or rollback
  7. Final health verification
```

**Canary Metrics** (monitored for 5 min):
- Error rate <1%
- P99 latency <2s
- Memory usage stable
- No crash loops

### 3. Release Pipeline (`.github/workflows/release.yml`)

**Purpose**: Automated release creation

**Triggers**:
- Semantic version tags (v1.2.3)

**Steps**:
1. Validate semantic version format
2. Build Docker image with version tags
3. Generate changelog from git commits
4. Create GitHub release
5. Upload artifacts (tarball, SBOM, checksums)
6. Notify team (Slack, email)

**Version Tagging**:
```bash
Stable: v1.2.3
  → Docker tags: 1.2.3, 1.2, 1, latest

Pre-release: v1.2.3-beta.1
  → Docker tag: 1.2.3-beta.1 only
```

### 4. Security Pipeline (`.github/workflows/security.yml`)

**Purpose**: Proactive vulnerability detection

**Schedule**: Daily at 02:00 UTC

**Scans**:
1. **SAST** (Bandit): Python code analysis
2. **Dependencies** (Safety, pip-audit): Package vulnerabilities
3. **Container** (Trivy): Docker image scanning
4. **Secrets** (GitLeaks): Credential detection

**Alerting**:
- GitHub Security tab (SARIF upload)
- GitHub Issues for CRITICAL/HIGH
- Slack notifications

### 5. Performance Pipeline (`.github/workflows/performance.yml`)

**Purpose**: Continuous performance monitoring

**Schedule**: Daily at 03:00 UTC

**Benchmarks**:
1. **API**: Endpoint latency (p50, p95, p99)
2. **RAG**: Pipeline throughput
3. **Database**: Query performance
4. **Load**: 100 concurrent users

**Regression Detection**:
- >10% performance degradation triggers alert
- Historical trend analysis
- GitHub Issues created for regressions

## Secret Management

### Required Secrets (22 total)

See `.github/workflows/secrets.md` for detailed setup instructions.

#### Infrastructure (5 secrets)
```bash
AWS_ACCESS_KEY_ID              # AWS credentials for staging
AWS_SECRET_ACCESS_KEY          # AWS secret for staging
AWS_ACCESS_KEY_ID_PROD         # AWS credentials for production
AWS_SECRET_ACCESS_KEY_PROD     # AWS secret for production
AWS_REGION                     # AWS region (e.g., us-east-1)
```

#### Database (3 secrets)
```bash
POSTGRES_USER                  # PostgreSQL username
POSTGRES_PASSWORD              # PostgreSQL password
POSTGRES_DB                    # Database name
```

#### Container Registry (1 secret)
```bash
GITHUB_TOKEN                   # Auto-provided by GitHub Actions
```

#### Security (2 secrets)
```bash
COSIGN_PRIVATE_KEY            # Image signing key
COSIGN_PASSWORD               # Cosign key password
```

#### Monitoring (2 secrets)
```bash
CODECOV_TOKEN                 # Code coverage reporting
SENTRY_DSN                    # Error tracking
```

#### Notifications (4 secrets)
```bash
SLACK_WEBHOOK_URL             # General notifications
SLACK_SECURITY_WEBHOOK_URL    # Security alerts
SMTP_SERVER                   # Email server
SMTP_PORT                     # Email port
SMTP_USERNAME                 # Email username
SMTP_PASSWORD                 # Email password
RELEASE_NOTIFICATION_EMAIL    # Release notification recipient
```

#### Application (5 secrets)
```bash
JWT_SECRET_KEY                # JWT signing key
ANTHROPIC_API_KEY             # Claude API key (optional)
OPENAI_API_KEY                # OpenAI API key (optional)
EMBEDDING_MODEL               # Embedding model name
OLLAMA_DEFAULT_MODEL          # Default LLM model
```

### Setting Secrets

**Repository Secrets** (GitHub UI):
```
Settings → Secrets and variables → Actions → New repository secret
```

**Environment Secrets** (for staging/production):
```
Settings → Environments → [staging|production] → Add secret
```

**Secret Rotation**:
- Review quarterly
- Rotate immediately if compromised
- Update in both GitHub and deployed environments
- Test after rotation

## Deployment Procedures

### Standard Deployment to Staging

**Automatic** (on push to main):
```bash
git checkout main
git pull origin main
git merge feature/my-feature
git push origin main

# CI/CD automatically:
# 1. Runs CI pipeline
# 2. Builds Docker image
# 3. Deploys to staging
# 4. Runs integration tests
```

**Manual Deployment**:
```bash
# Via GitHub Actions UI
Actions → Deploy → Run workflow
  Environment: staging
  Version: latest (or specific tag)
```

### Production Deployment

**Prerequisites**:
1. ✅ Staging deployment successful
2. ✅ Integration tests passed
3. ✅ Manual testing completed
4. ✅ Team notification sent

**Process**:
```bash
# 1. Trigger deployment
Actions → Deploy → Run workflow
  Environment: production
  Version: v1.2.3

# 2. Approve deployment
# GitHub sends approval request to designated reviewers
# At least one approval required

# 3. Monitor canary deployment (automated)
# - 10% traffic for 5 minutes
# - Automatic rollback if metrics degrade

# 4. Full rollout (automated)
# - 100% traffic after canary success
# - Final health checks

# 5. Verify deployment
curl https://rag-enterprise.example.com/health
```

### Emergency Hotfix Deployment

For critical production issues requiring immediate fix:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-issue

# 2. Implement fix
# ... make changes ...

# 3. Fast-track testing
pytest tests/unit/ tests/integration/ -v

# 4. Merge to main
git checkout main
git merge hotfix/critical-issue
git push origin main

# 5. Tag hotfix version
git tag v1.2.4
git push origin v1.2.4

# 6. Manual deployment approval
# Actions → Deploy → production → Approve

# 7. Monitor deployment closely
# Watch logs, metrics, error rates

# 8. Document hotfix
# Create incident report
# Update CHANGELOG.md
```

### Rollback Procedures

#### Automatic Rollback

Automatic rollback triggers:
- Health check failures during deployment
- Canary metrics exceed thresholds
- Integration test failures

```bash
# Automatic process:
1. Detect failure condition
2. Stop current deployment
3. Restore previous version
4. Restore database from backup
5. Verify restoration
6. Notify team
```

#### Manual Rollback

```bash
# Using rollback script
./scripts/rollback.sh production

# Or via Helm
kubectl config use-context production
helm rollback rag-enterprise -n production

# Verify rollback
curl https://rag-enterprise.example.com/health/ready
```

#### Database Rollback

```bash
# List backups
ls -lah backups/backup-production-*.tar.gz

# Restore specific backup
./scripts/deploy.sh backup production 20250119-120000

# Manually restore database
kubectl exec -n production deployment/rag-api -- \
  psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB \
  < backups/db-production-20250119-120000.sql
```

## Troubleshooting

### CI Pipeline Failures

#### Lint Failures

```bash
# Black formatting
black --check --diff app/ tests/
# Fix:
black app/ tests/

# isort
isort --check-only app/ tests/
# Fix:
isort app/ tests/

# mypy type checking
mypy app/ --strict
# Fix type errors in code
```

#### Test Failures

```bash
# Run locally with services
docker-compose up -d
pytest tests/ -v --tb=short

# Check logs
docker-compose logs api

# Debug specific test
pytest tests/unit/test_specific.py::test_function -vv -s
```

#### Docker Build Failures

```bash
# Build locally
docker build -t rag-enterprise:test .

# Check size
docker images rag-enterprise:test

# Debug build
docker build -t rag-enterprise:test . --progress=plain --no-cache
```

### Deployment Failures

#### Health Check Failures

```bash
# Check pod status
kubectl get pods -n staging

# Check logs
kubectl logs deployment/rag-api -n staging

# Describe pod for events
kubectl describe pod -n staging -l app=rag-api

# Check service endpoints
kubectl get svc -n staging

# Test health endpoint
kubectl port-forward -n staging svc/rag-api 8000:8000
curl http://localhost:8000/health
```

#### Database Migration Failures

```bash
# Check migration status
kubectl exec -n staging deployment/rag-api -- \
  python -m alembic current

# View migration history
kubectl exec -n staging deployment/rag-api -- \
  python -m alembic history

# Manually run migration
kubectl exec -n staging deployment/rag-api -- \
  python -m alembic upgrade head

# Rollback one version
kubectl exec -n staging deployment/rag-api -- \
  python -m alembic downgrade -1
```

#### Canary Deployment Issues

```bash
# Check canary metrics in Prometheus
kubectl port-forward -n production svc/prometheus 9090:9090

# Query error rate
rate(http_requests_total{status=~"5..",version="canary"}[1m])

# Query latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{version="canary"}[1m]))

# Force rollback
./scripts/rollback.sh production
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n production

# View application metrics
kubectl port-forward -n production svc/prometheus 9090:9090
# Open http://localhost:9090

# Check database connections
kubectl exec -n production deployment/rag-api -- \
  psql -h postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Profile API endpoint
curl -w "@curl-format.txt" -o /dev/null -s http://api-endpoint/health
```

## Operational Runbooks

### Daily Operations

**Morning Health Check**:
```bash
# 1. Check GitHub Actions status
# Browse to Actions tab

# 2. Review security scan results
# Check GitHub Security tab

# 3. Verify production health
curl https://rag-enterprise.example.com/health

# 4. Check error rates in Sentry
# Review Sentry dashboard

# 5. Review performance metrics
# Check Prometheus/Grafana dashboards
```

### Weekly Operations

**Monday**:
- Review Dependabot PRs
- Check for security updates
- Review performance trends

**Wednesday**:
- Staging deployment (if pending features)
- Integration test verification

**Friday**:
- Production deployment (if ready)
- Weekly backup verification
- Incident review meeting

### Monthly Operations

1. **Security Review**: Audit secrets, rotate credentials
2. **Performance Review**: Analyze trends, capacity planning
3. **Backup Testing**: Verify restore procedures
4. **Documentation Update**: Update runbooks, procedures
5. **Dependency Audit**: Major version updates review

### Emergency Response

**Production Outage**:
```bash
# 1. Assess impact
curl https://rag-enterprise.example.com/health
kubectl get pods -n production

# 2. Check recent deployments
helm history rag-enterprise -n production

# 3. Rollback if needed
./scripts/rollback.sh production

# 4. Investigate root cause
kubectl logs deployment/rag-api -n production --tail=1000

# 5. Communicate status
# Post to Slack incident channel

# 6. Document incident
# Create incident report
```

**Security Incident**:
```bash
# 1. Assess severity
# Review security scan results

# 2. Rotate compromised secrets
# Update in GitHub and environments

# 3. Deploy security fix
# Emergency hotfix procedure

# 4. Audit access logs
# Check for unauthorized access

# 5. Notify stakeholders
# Security team, management
```

---

## Performance Targets

- **CI Pipeline**: <10 minutes
- **Deploy to Staging**: <20 minutes
- **Integration Tests**: <10 minutes
- **Deploy to Production**: <40 minutes total
- **Rollback Time**: <5 minutes

## Support

- **Documentation**: `/docs/README.md`
- **Issues**: GitHub Issues
- **Slack**: #rag-enterprise-ops
- **On-call**: PagerDuty rotation

## Change Log

- **2025-01-19**: Initial CI/CD implementation
- Version updates tracked in git commits

---

**Last Updated**: 2025-01-19
**Version**: 1.0
