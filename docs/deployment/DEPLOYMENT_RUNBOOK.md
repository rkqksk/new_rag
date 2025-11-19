# Deployment Runbook - v10.0.0

**Owner**: DevOps Team
**Last Updated**: 2025-11-16
**Version**: 10.0.0

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Deployment Process](#deployment-process)
4. [Rollback Procedure](#rollback-procedure)
5. [Health Checks](#health-checks)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- `kubectl` v1.28+
- `docker` v24+
- `pnpm` v9+
- `python` 3.11+
- GitHub account with repository access

### Required Access
- Kubernetes cluster credentials
- GitHub Container Registry (ghcr.io)
- Production environment secrets

### Pre-Deployment Checklist
- [ ] All CI tests passing
- [ ] Code review approved
- [ ] Database migrations tested
- [ ] Secrets updated in Kubernetes
- [ ] Backup created
- [ ] Team notified

---

## Environment Setup

### 1. Configure kubectl
```bash
# Download kubeconfig
mkdir -p ~/.kube
echo "$KUBE_CONFIG_PRODUCTION" | base64 -d > ~/.kube/config

# Verify connection
kubectl cluster-info
kubectl get nodes
```

### 2. Verify Namespace
```bash
kubectl get namespace rag-production
kubectl config set-context --current --namespace=rag-production
```

### 3. Check Secrets
```bash
kubectl get secrets -n rag-production
# Required: db-credentials, redis-credentials, api-keys
```

---

## Deployment Process

### Option A: Automated Deployment (Recommended)

#### 1. Staging Deployment
```bash
# Push to main branch
git checkout main
git pull origin main
git push origin main

# CI/CD automatically deploys to staging
# Monitor: https://github.com/rkqksk/new_rag/actions
```

#### 2. Production Deployment
```bash
# Create version tag
git tag -a v10.0.1 -m "Release v10.0.1"
git push origin v10.0.1

# Approve deployment in GitHub Actions
# Navigate to: Actions → CD → Approve production deployment
```

### Option B: Manual Deployment

#### 1. Build Docker Images
```bash
# Build API
docker build -f apps/api/Dockerfile.prod -t ghcr.io/rkqksk/new_rag-api:v10.0.1 .
docker push ghcr.io/rkqksk/new_rag-api:v10.0.1

# Build Web
docker build -f apps/web/Dockerfile.prod -t ghcr.io/rkqksk/new_rag-web:v10.0.1 .
docker push ghcr.io/rkqksk/new_rag-web:v10.0.1
```

#### 2. Deploy to Kubernetes
```bash
# Use deployment script
./scripts/deploy-production.sh v10.0.1

# Or manually
kubectl set image deployment/api api=ghcr.io/rkqksk/new_rag-api:v10.0.1 -n rag-production
kubectl set image deployment/web web=ghcr.io/rkqksk/new_rag-web:v10.0.1 -n rag-production
```

#### 3. Monitor Rollout
```bash
# Watch deployment
kubectl rollout status deployment/api -n rag-production --timeout=5m
kubectl rollout status deployment/web -n rag-production --timeout=5m

# Check pods
kubectl get pods -n rag-production -w
```

---

## Rollback Procedure

### Quick Rollback (< 30 seconds)
```bash
./scripts/rollback.sh api rag-production
./scripts/rollback.sh web rag-production
```

### Manual Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/api -n rag-production
kubectl rollout undo deployment/web -n rag-production

# Rollback to specific revision
kubectl rollout history deployment/api -n rag-production
kubectl rollout undo deployment/api --to-revision=5 -n rag-production
```

### Verify Rollback
```bash
kubectl get deployment api -n rag-production -o wide
kubectl get pods -l app=api -n rag-production
```

---

## Health Checks

### API Health
```bash
# Health endpoint
curl https://api.rag-enterprise.com/health

# Expected response:
{
  "status": "healthy",
  "version": "10.0.1",
  "timestamp": "2025-11-16T22:45:00Z"
}
```

### Web Health
```bash
curl -I https://rag-enterprise.com
# Expected: HTTP/2 200
```

### Kubernetes Health
```bash
# Check pod status
kubectl get pods -n rag-production

# Check pod logs
kubectl logs -f deployment/api -n rag-production --tail=50

# Check resource usage
kubectl top pods -n rag-production
```

### Database Health
```bash
# Connect to API pod
kubectl exec -it deployment/api -n rag-production -- bash

# Test database
python -c "
from sqlalchemy import create_engine
engine = create_engine('$DATABASE_URL')
print(engine.execute('SELECT 1').scalar())
"
```

---

## Troubleshooting

### Issue: Pods Not Starting

**Symptoms**:
- Pods in `CrashLoopBackOff` or `Error` state
- `kubectl get pods` shows restarts

**Diagnosis**:
```bash
kubectl describe pod <pod-name> -n rag-production
kubectl logs <pod-name> -n rag-production --previous
```

**Common Causes**:
1. Missing environment variables
2. Database connection failure
3. Image pull errors
4. Resource limits exceeded

**Solution**:
```bash
# Check secrets
kubectl get secret db-credentials -n rag-production -o yaml

# Verify image exists
docker pull ghcr.io/rkqksk/new_rag-api:v10.0.1

# Check resource usage
kubectl top pods -n rag-production
```

### Issue: High Latency

**Symptoms**:
- API responses > 500ms
- Timeout errors

**Diagnosis**:
```bash
# Check pod CPU/memory
kubectl top pods -n rag-production

# Check database connections
kubectl exec -it deployment/api -n rag-production -- \
  python -c "import psycopg2; print('DB OK')"
```

**Solution**:
```bash
# Scale up if needed
kubectl scale deployment/api --replicas=5 -n rag-production

# Check slow queries
# Access database and run: EXPLAIN ANALYZE <query>
```

### Issue: 502 Bad Gateway

**Symptoms**:
- Nginx returns 502
- Users cannot access site

**Diagnosis**:
```bash
# Check ingress
kubectl describe ingress rag-ingress -n rag-production

# Check service endpoints
kubectl get endpoints -n rag-production
```

**Solution**:
```bash
# Restart ingress controller
kubectl rollout restart deployment/nginx-ingress-controller -n ingress-nginx

# Verify service
kubectl get svc -n rag-production
```

---

## Monitoring

### Metrics to Watch

#### API Metrics
- Request rate: < 1000 req/min normal
- Error rate: < 1% acceptable
- Response time: < 500ms p95
- CPU usage: < 80%
- Memory usage: < 80%

#### Database Metrics
- Active connections: < 100
- Query time: < 100ms p95
- Disk usage: < 80%

### Alerts

**Critical** (Immediate action):
- API down (all pods failing)
- Database connection pool exhausted
- Disk > 90% full

**Warning** (Monitor):
- Error rate > 5%
- Response time > 1s p95
- CPU > 80% for 10 minutes

---

## Post-Deployment

### Verification Checklist
- [ ] All pods running (3 API, 2 Web)
- [ ] Health endpoints returning 200
- [ ] No error logs in past 5 minutes
- [ ] Response times < 500ms
- [ ] Database connections stable
- [ ] Monitoring dashboards updated
- [ ] Team notified of completion

### Rollback Decision Tree
```
Deployment successful?
├─ Yes → Monitor for 30 minutes → Complete
└─ No → Check health
    ├─ API down → Immediate rollback
    ├─ High errors (>10%) → Rollback
    ├─ Slow response (>2s) → Investigate → Rollback if not fixed in 10 min
    └─ Minor issues → Monitor → Fix in next release
```

---

## Contacts

**On-Call**: DevOps team (Slack: #devops-oncall)
**Database**: DBA team (Slack: #database)
**Security**: Security team (Slack: #security)

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-16 | 10.0.0 | Initial v10 runbook | Claude |

---

**Next Review**: 2025-12-16
