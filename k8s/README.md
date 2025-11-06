# Kubernetes Deployment Guide

RAG Enterprise Kubernetes deployment manifests for production environments.

## Prerequisites

- Kubernetes cluster (v1.25+)
- kubectl configured
- Ingress controller (nginx recommended)
- cert-manager (for TLS certificates)
- StorageClass for persistent volumes

## Quick Deploy

```bash
# Deploy all resources
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n rag-enterprise
kubectl get svc -n rag-enterprise
kubectl get ingress -n rag-enterprise
```

## Deployment Steps

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Configure Secrets

Edit `k8s/secrets.yaml` with production values:

```bash
# Generate base64 encoded secrets
echo -n "your_postgres_password" | base64

# Apply secrets
kubectl apply -f k8s/secrets.yaml
```

### 3. Configure ConfigMap

Edit `k8s/configmap.yaml` if needed, then apply:

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Deploy Databases

```bash
# PostgreSQL
kubectl apply -f k8s/postgres-statefulset.yaml

# Redis
kubectl apply -f k8s/redis-deployment.yaml

# Qdrant
kubectl apply -f k8s/qdrant-statefulset.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n rag-enterprise --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n rag-enterprise --timeout=300s
kubectl wait --for=condition=ready pod -l app=qdrant -n rag-enterprise --timeout=300s
```

### 5. Deploy API

```bash
kubectl apply -f k8s/api-deployment.yaml

# Wait for API to be ready
kubectl wait --for=condition=ready pod -l app=rag-api -n rag-enterprise --timeout=300s
```

### 6. Configure Ingress

Edit `k8s/ingress.yaml` with your domain, then apply:

```bash
kubectl apply -f k8s/ingress.yaml
```

## Architecture

```
                        ┌─────────────┐
                        │   Ingress   │
                        │  (NGINX)    │
                        └──────┬──────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │   RAG API (3x)   │
                    │  HPA: 3-10 pods  │
                    └────┬────┬────┬───┘
                         │    │    │
           ┌─────────────┼────┼────┼──────────────┐
           │             │    │    │              │
           ▼             ▼    ▼    ▼              ▼
    ┌──────────┐   ┌─────────────────┐    ┌──────────┐
    │PostgreSQL│   │     Qdrant      │    │  Redis   │
    │(StatefulSet) │  (StatefulSet)  │    │(Deploy)  │
    │   1 pod   │   │     1 pod       │    │  1 pod   │
    └──────────┘   └─────────────────┘    └──────────┘
         │                  │                    │
         ▼                  ▼                    ▼
     PVC 20Gi           PVC 50Gi            (no PVC)
```

## Resource Requirements

| Component  | Replicas | CPU Request | CPU Limit | Memory Request | Memory Limit | Storage |
|------------|----------|-------------|-----------|----------------|--------------|---------|
| API        | 3-10     | 500m        | 2000m     | 512Mi          | 2Gi          | -       |
| Qdrant     | 1        | 500m        | 2000m     | 1Gi            | 4Gi          | 50Gi    |
| PostgreSQL | 1        | 250m        | 1000m     | 512Mi          | 2Gi          | 20Gi    |
| Redis      | 1        | 100m        | 500m      | 256Mi          | 1Gi          | -       |
| **Total**  | -        | 1.85-7.35   | 11-28     | 2.28-7.28Gi    | 9-28Gi       | 70Gi    |

## Scaling

### Horizontal Pod Autoscaler (HPA)

API pods auto-scale based on:
- CPU utilization: 70%
- Memory utilization: 80%
- Range: 3-10 pods

```bash
# Check HPA status
kubectl get hpa -n rag-enterprise

# Manual scaling
kubectl scale deployment rag-api --replicas=5 -n rag-enterprise
```

### Database Scaling

For database scaling, consider:
- PostgreSQL: Read replicas (not included in this config)
- Qdrant: Horizontal scaling with sharding
- Redis: Redis Cluster or Sentinel

## Monitoring

```bash
# Check pod status
kubectl get pods -n rag-enterprise -o wide

# View logs
kubectl logs -f deployment/rag-api -n rag-enterprise

# Check resource usage
kubectl top pods -n rag-enterprise
kubectl top nodes

# Describe resources
kubectl describe pod <pod-name> -n rag-enterprise
```

## Troubleshooting

### Pod Not Starting

```bash
# Check events
kubectl describe pod <pod-name> -n rag-enterprise

# Check logs
kubectl logs <pod-name> -n rag-enterprise --previous
```

### Database Connection Issues

```bash
# Test connectivity
kubectl exec -it deployment/rag-api -n rag-enterprise -- ping postgres-service
kubectl exec -it deployment/rag-api -n rag-enterprise -- ping qdrant-service

# Check database pods
kubectl logs statefulset/postgres -n rag-enterprise
kubectl logs statefulset/qdrant -n rag-enterprise
```

### Ingress Not Working

```bash
# Check ingress status
kubectl get ingress -n rag-enterprise
kubectl describe ingress rag-ingress -n rag-enterprise

# Check nginx ingress logs
kubectl logs -f -n ingress-nginx deployment/ingress-nginx-controller
```

## Backup and Restore

### PostgreSQL Backup

```bash
# Backup
kubectl exec statefulset/postgres -n rag-enterprise -- \
  pg_dump -U rag_user rag_enterprise > backup.sql

# Restore
kubectl exec -i statefulset/postgres -n rag-enterprise -- \
  psql -U rag_user rag_enterprise < backup.sql
```

### Qdrant Backup

```bash
# Create snapshot
curl -X POST http://qdrant-service.rag-enterprise:6333/collections/products_multimodal/snapshots

# Download snapshot (requires port-forward)
kubectl port-forward -n rag-enterprise statefulset/qdrant 6333:6333
curl http://localhost:6333/collections/products_multimodal/snapshots/<snapshot-name> -o snapshot.tar
```

## Updates and Rollouts

```bash
# Update API image
kubectl set image deployment/rag-api api=rag-enterprise-api:v2 -n rag-enterprise

# Check rollout status
kubectl rollout status deployment/rag-api -n rag-enterprise

# Rollback if needed
kubectl rollout undo deployment/rag-api -n rag-enterprise

# View rollout history
kubectl rollout history deployment/rag-api -n rag-enterprise
```

## Security Best Practices

1. **Secrets Management**: Use external secret managers (Vault, AWS Secrets Manager)
2. **Network Policies**: Restrict pod-to-pod communication
3. **RBAC**: Configure proper role-based access control
4. **Pod Security**: Use PodSecurityPolicies or PodSecurityStandards
5. **TLS**: Enable TLS for all services
6. **Image Scanning**: Scan container images for vulnerabilities

## Production Checklist

- [ ] Update secrets with production values
- [ ] Configure proper domain in ingress
- [ ] Set up TLS certificates
- [ ] Configure resource limits based on load testing
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Set up log aggregation
- [ ] Configure network policies
- [ ] Enable RBAC
- [ ] Set up disaster recovery plan

## Clean Up

```bash
# Delete all resources
kubectl delete -f k8s/

# Delete namespace (removes all resources)
kubectl delete namespace rag-enterprise
```

## Support

For issues and questions, see:
- Main README: `../README.md`
- Deployment Guide: `../docs/DEPLOYMENT_GUIDE.md`
- Architecture: `../docs/ARCHITECTURE.md`
