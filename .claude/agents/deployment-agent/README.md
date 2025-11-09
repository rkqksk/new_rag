# Deployment Agent

**Purpose**: Deployment and DevOps automation - Docker, Kubernetes, CI/CD

**Version**: 1.0.0
**Status**: ✅ Production-Ready

---

## 🎯 Overview

Specialized sub-agent for deployment automation and infrastructure management.

### Key Features

- ✅ **Docker deployment** (compose, swarm)
- ✅ **Kubernetes orchestration** (manifests, helm)
- ✅ **CI/CD automation** (GitHub Actions, GitLab CI)
- ✅ **Infrastructure as code** (declarative configs)
- ✅ **Rollback support** (zero-downtime)

---

## 🚀 Usage

### Via Task Tool

```python
# Launch deployment agent
Task(
    subagent_type="deployment-agent",
    prompt="Deploy to production with zero downtime"
)
```

### Common Commands

```bash
# Deploy development
./scripts/deploy-optimized.sh development

# Deploy production
./scripts/deploy-optimized.sh production

# Scale services
docker-compose up -d --scale api=3

# Kubernetes deployment
kubectl apply -f k8s/
```

---

## 🔧 Configuration

Located in `agent.json`:

```json
{
  "default_environment": "development",
  "container_registry": "local",
  "orchestration": "docker-compose",
  "auto_rollback": true
}
```

---

## 📊 Deployment Options

| Environment | Platform | Cost | Setup Time |
|-------------|----------|------|------------|
| Development | Docker Compose | $0 | 5 min |
| Staging | VPS | $10-20/mo | 30 min |
| Production | K8s Cluster | $200-500/mo | 2 hours |

---

## 📚 Related

- Scripts: `scripts/deploy-optimized.sh`, `scripts/restart-all.sh`
- Docs: `docs/DEPLOYMENT_GUIDE.md`
- Config: `docker-compose.yml`, `k8s/`

---

**Created**: 2025-11-08
**Last Updated**: 2025-11-08
