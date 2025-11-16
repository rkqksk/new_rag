---
name: deployment-automation
description: Kubernetes K8s deploy docker helm GitOps ArgoCD CI/CD GitHub Actions 배포 자동화 컨테이너 오케스트레이션 production staging manifest YAML ingress service 프로덕션 배포
---

# Deployment Automation

## When to Use
- 배포, deploy, deployment
- K8s, Kubernetes
- Docker, container
- Helm chart
- CI/CD pipeline
- Production release
- GitOps, ArgoCD
- Manifest generation
- Ingress, service setup

## Core Capabilities
1. **K8s Manifests** - Generate deployment, service, ingress YAML
2. **Helm Charts** - Create and manage Helm charts
3. **CI/CD** - GitHub Actions workflows
4. **GitOps** - ArgoCD, FluxCD integration
5. **Monitoring** - Prometheus, Grafana setup

## Quick Actions

### Generate K8s Manifests
```python
# Auto-generate manifests
python scripts/generate_manifests.py \
  --app rag-api \
  --image rag-api:v1.0.0 \
  --replicas 3 \
  --output k8s/
```

### Create Helm Chart
```python
# Scaffold Helm chart
python scripts/create_helm_chart.py \
  --name peter-stack \
  --version 1.0.0 \
  --output charts/
```

### Deploy to K8s
```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Using Helm
helm install peter charts/peter-stack \
  --namespace production \
  --create-namespace
```

### Setup CI/CD
```python
# Generate GitHub Actions
python scripts/setup_ci cd.py \
  --workflows test,build,deploy \
  --output .github/workflows/
```

## K8s Resource Templates

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
      - name: api
        image: rag-api:v1.0.0
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: rag-api
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8001
  selector:
    app: rag-api
```

### Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt
spec:
  rules:
  - host: api.peter.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: rag-api
            port:
              number: 80
  tls:
  - hosts:
    - api.peter.com
    secretName: peter-tls
```

## Deployment Strategies

### Rolling Update (Zero Downtime)
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```

### Blue-Green
```bash
# Deploy green
kubectl apply -f k8s/deployment-green.yaml

# Test green
curl https://green.peter.com/health

# Switch traffic
kubectl patch service rag-api -p '{"spec":{"selector":{"version":"green"}}}'
```

### Canary
```yaml
# 10% traffic to canary
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: rag-api
spec:
  hosts:
  - rag-api
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: rag-api
        subset: v2
  - route:
    - destination:
        host: rag-api
        subset: v1
      weight: 90
    - destination:
        host: rag-api
        subset: v2
      weight: 10
```

## CI/CD Pipeline

### GitHub Actions
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest tests/ --cov

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t rag-api:${{ github.sha }} .
      - name: Push to registry
        run: docker push rag-api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to K8s
        run: |
          kubectl set image deployment/rag-api \
            api=rag-api:${{ github.sha }}
```

## Monitoring Setup

### Prometheus
```python
# Add metrics to FastAPI
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total requests')
request_duration = Histogram('api_request_duration_seconds', 'Request duration')
```

### Grafana Dashboard
```python
# Auto-create dashboard
python scripts/create_dashboard.py \
  --service rag-api \
  --metrics requests,latency,errors \
  --output grafana/
```

## Integration
- **testing-suite**: Run tests before deployment
- **rag-optimization**: Performance monitoring
- **saas-operations**: Tenant resource provisioning

## Key Files
- `k8s/` - Kubernetes manifests
- `charts/` - Helm charts
- `.github/workflows/` - CI/CD pipelines
- `scripts/deployment/` - Deployment scripts

## Pre-Deployment Checklist
- ✅ Tests passing
- ✅ Image built and pushed
- ✅ Database migrations applied
- ✅ Secrets configured
- ✅ Health checks working
- ✅ Monitoring setup
