# Enterprise Deployment Guide

**RAG Enterprise - Production Deployment**

---

## 🚀 Quick Start

### Local Development

```bash
# Start services
docker-compose up -d

# Run API server
python run_chat_server.py

# Open frontend
open http://localhost:8080/chat.html
```

### Production Deployment

```bash
# Build production image
docker build -f Dockerfile.prod -t rag-enterprise:latest .

# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=rag-enterprise
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Load Balancer (Nginx)           │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      │   API Pods      │  (Auto-scaling 2-10)
      │  (Python/FastAPI)│
      └────────┬────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼────┐
│Qdrant │ │ Redis │ │ Ollama │
│ (VDB) │ │(Cache)│ │  (LLM) │
└───────┘ └───────┘ └────────┘
```

---

## 📦 Components

### 1. API Service
- **Replicas**: 2-10 (auto-scaling)
- **Resources**: 2Gi RAM, 1 CPU (request)
- **Port**: 8001
- **Health**: /health, /ready

### 2. Qdrant (Vector Database)
- **Type**: StatefulSet
- **Storage**: 50Gi PVC
- **Resources**: 4Gi RAM, 2 CPU
- **Ports**: 6333 (HTTP), 6334 (gRPC)

### 3. Redis (Cache)
- **Type**: Deployment
- **Resources**: 1Gi RAM, 500m CPU
- **Port**: 6379

### 4. Ollama (LLM)
- **Type**: Deployment (GPU)
- **Model**: qwen2.5:7b-instruct
- **Resources**: 8Gi RAM, 4 CPU, 1 GPU

---

## 🔧 Configuration

### Environment Variables

```bash
# Qdrant
QDRANT_HOST=qdrant-service
QDRANT_PORT=6333

# Redis
REDIS_HOST=redis-service
REDIS_PORT=6379

# Ollama
OLLAMA_HOST=ollama-service
OLLAMA_PORT=11434

# API
API_HOST=0.0.0.0
API_PORT=8001
```

### Kubernetes Secrets

```bash
# Create secrets
kubectl create secret generic rag-secrets \
  --from-literal=api-key=your-api-key \
  --from-literal=db-password=your-db-password
```

---

## 📊 Monitoring

### Prometheus Metrics

```yaml
# Exposed at /metrics
- http_requests_total
- http_request_duration_seconds
- rag_query_duration_seconds
- vector_search_duration_seconds
- cache_hit_rate
```

### Grafana Dashboard

```bash
# Import dashboard
kubectl apply -f k8s/grafana-dashboard.yaml
```

---

## 🔒 Security

### 1. Network Policies

```bash
# Apply network policies
kubectl apply -f k8s/network-policy.yaml
```

### 2. RBAC

```bash
# Create service account
kubectl apply -f k8s/rbac.yaml
```

### 3. TLS/HTTPS

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create certificate
kubectl apply -f k8s/certificate.yaml
```

---

## 📈 Scaling

### Horizontal Pod Autoscaling

```yaml
# Already configured in deployment.yaml
minReplicas: 2
maxReplicas: 10

metrics:
  - CPU: 70%
  - Memory: 80%
```

### Vertical Pod Autoscaling

```bash
# Install VPA
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/download/vertical-pod-autoscaler-0.13.0/vpa-v0.13.0.yaml

# Apply VPA
kubectl apply -f k8s/vpa.yaml
```

---

## 🚨 Troubleshooting

### Check Logs

```bash
# API logs
kubectl logs -l app=rag-enterprise -f

# Qdrant logs
kubectl logs -l app=qdrant -f

# Redis logs
kubectl logs -l app=redis -f
```

### Debug Pod

```bash
# Shell into API pod
kubectl exec -it <pod-name> -- /bin/bash

# Check connectivity
curl http://qdrant-service:6333/collections
curl http://redis-service:6379
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods

# Check HPA status
kubectl get hpa

# Check events
kubectl get events --sort-by='.lastTimestamp'
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# Trigger: Push to main
1. Run tests (pytest)
2. Build Docker image
3. Push to registry
4. Deploy to K8s
5. Run smoke tests
```

### Manual Deployment

```bash
# Build
docker build -f Dockerfile.prod -t rag-enterprise:v1.0.0 .

# Tag
docker tag rag-enterprise:v1.0.0 your-registry/rag-enterprise:v1.0.0

# Push
docker push your-registry/rag-enterprise:v1.0.0

# Update K8s
kubectl set image deployment/rag-enterprise-api \
  api=your-registry/rag-enterprise:v1.0.0

# Rollout
kubectl rollout status deployment/rag-enterprise-api
```

---

## 💾 Backup & Restore

### Qdrant Backup

```bash
# Create snapshot
kubectl exec -it qdrant-0 -- /bin/bash -c \
  "curl -X POST http://localhost:6333/collections/products_multimodal/snapshots"

# Download snapshot
kubectl cp qdrant-0:/qdrant/storage/collections/products_multimodal/snapshots/<snapshot-name> \
  ./backup/qdrant-snapshot.tar
```

### Redis Backup

```bash
# Create RDB dump
kubectl exec -it redis-0 -- redis-cli SAVE

# Copy dump
kubectl cp redis-0:/data/dump.rdb ./backup/redis-dump.rdb
```

---

## 📋 Maintenance

### Update Dependencies

```bash
# Update Python packages
pip-compile requirements.in
pip install -r requirements.txt

# Rebuild image
docker build -f Dockerfile.prod -t rag-enterprise:latest .
```

### Database Maintenance

```bash
# Optimize Qdrant indices
curl -X POST http://qdrant-service:6333/collections/products_multimodal/optimize

# Clear Redis cache
kubectl exec -it redis-0 -- redis-cli FLUSHALL
```

---

## 🎯 Performance Tuning

### API Optimization
- Enable Redis caching (✅ Implemented)
- Use connection pooling
- Optimize batch sizes
- Enable HTTP/2

### Qdrant Optimization
- Tune HNSW parameters
- Use quantization
- Enable disk-based storage
- Optimize shard count

### Ollama Optimization
- Use GPU acceleration
- Optimize batch size
- Enable model caching
- Use smaller quantized models

---

## 📚 Additional Resources

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Qdrant Deployment Guide](https://qdrant.tech/documentation/cloud/)
- [FastAPI Production Guide](https://fastapi.tiangolo.com/deployment/)

---

**Version**: 1.0.0
**Last Updated**: 2025-11-06
