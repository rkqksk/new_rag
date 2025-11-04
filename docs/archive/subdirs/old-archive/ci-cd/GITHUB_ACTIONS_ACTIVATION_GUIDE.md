# GitHub Actions Activation Guide

**Last Updated**: 2025-11-03
**Project**: RAG Enterprise
**Status**: 4 workflows disabled, 1 active (minimal CI)

---

## 📊 Current Status

### ✅ Active Workflows (1)

| Workflow | File | Triggers | Purpose | Status |
|----------|------|----------|---------|--------|
| **CI** | `.github/workflows/ci.yml` | Push to any branch, PR to main/develop | Basic validation: Python setup, project structure check | ✅ **Running** |

**What CI Does**:
- Sets up Python 3.11
- Installs dependencies (with error tolerance)
- Verifies project structure (`app/`, `tests/`, `requirements.txt`)
- Runs basic validation (Python version check)

**Limitations**:
- ❌ No actual tests run (no pytest execution)
- ❌ No code quality checks (no linting, type checking)
- ❌ No security scanning
- ❌ No performance benchmarks
- ❌ No deployment capabilities

---

### ❌ Disabled Workflows (4)

Located in `.github/workflows/_disabled/`:

| Workflow | File | Size | Purpose | Why Disabled |
|----------|------|------|---------|--------------|
| **Deploy** | `deploy.yml` | 20KB | Automated deployment (staging/production) with canary strategy | Missing infrastructure, secrets, registry access |
| **Performance** | `performance.yml` | 14KB | Performance testing, load testing, benchmarking | Resource-intensive, requires load testing setup |
| **Security** | `security.yml` | 15KB | Security scanning (CodeQL, Trivy, dependency audit) | May need tokens/licenses, comprehensive setup |
| **Release** | `release.yml` | 13KB | Automated GitHub releases, changelog generation, version management | Needs semantic versioning setup |

---

## 🚀 Activation Strategy

### **Recommended Order**

Activate workflows progressively based on immediate value and setup complexity:

```
Priority 1: Security (High value, low complexity)
Priority 2: Release (Moderate value, moderate complexity)
Priority 3: Performance (Moderate value, moderate complexity)
Priority 4: Deploy (High value, high complexity - requires infrastructure)
```

---

## 🔐 1. Activate Security Workflow

**Benefits**:
- 🛡️ Automated dependency vulnerability scanning
- 📊 Code quality and security issue detection
- 🐳 Container image security scanning
- 🔒 Secret detection in code

**Setup Steps**:

### Step 1: Move workflow file

```bash
cd /Users/oypnus/Project/rag-enterprise/.github/workflows
mv _disabled/security.yml .
```

### Step 2: Configure GitHub secrets (if needed)

The security workflow may require these **optional** secrets:

| Secret Name | Purpose | Required? | How to Get |
|-------------|---------|-----------|------------|
| `SNYK_TOKEN` | Snyk vulnerability scanning | Optional | https://snyk.io → Settings → API Token |
| `SONAR_TOKEN` | SonarCloud code quality | Optional | https://sonarcloud.io → My Account → Security |
| `GITHUB_TOKEN` | Already available | ✅ Auto-provided | No action needed |

**To add secrets**:
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add name and value
4. Save

### Step 3: Test manually

```bash
# In GitHub UI:
# 1. Go to Actions tab
# 2. Select "Security" workflow
# 3. Click "Run workflow"
# 4. Select branch: main
# 5. Click "Run workflow" button
```

### Step 4: Review results

Check the Actions tab for:
- ✅ CodeQL Analysis (free for public repos)
- ✅ Dependency Audit (npm/pip)
- ✅ Container Scanning (if Dockerfile exists)
- ✅ Secret Detection

---

## 📦 2. Activate Release Workflow

**Benefits**:
- 📝 Automated changelog generation
- 🏷️ Semantic versioning tags
- 📦 GitHub Releases creation
- 📄 Release notes compilation

**Setup Steps**:

### Step 1: Move workflow file

```bash
cd /Users/oypnus/Project/rag-enterprise/.github/workflows
mv _disabled/release.yml .
```

### Step 2: Configure semantic versioning

The release workflow expects commits following **Conventional Commits** format:

```
feat: Add new feature (minor version bump)
fix: Bug fix (patch version bump)
docs: Documentation (no version bump)
chore: Maintenance (no version bump)

feat!: Breaking change (major version bump)
BREAKING CHANGE: ... (major version bump)
```

### Step 3: Initial version tag

Create your first version tag:

```bash
cd /Users/oypnus/Project/rag-enterprise

# Tag current state as v1.0.0
git tag -a v1.0.0 -m "Initial release: RAG Enterprise v1.0.0

Features:
- SKILL-centric architecture (75% token reduction)
- Multi-model RAG support
- Domain experts (manufacturing, packaging)
- Vector search with Qdrant
"

# Push tag to GitHub
git push origin v1.0.0
```

### Step 4: Test release creation

```bash
# Make a change with conventional commit
git add .
git commit -m "feat: Add automated release workflow

- Semantic versioning support
- Automated changelog generation
- GitHub Releases integration
"

git push origin main

# Workflow will automatically:
# 1. Detect "feat:" → minor version bump (v1.0.0 → v1.1.0)
# 2. Generate changelog
# 3. Create GitHub Release
```

---

## ⚡ 3. Activate Performance Workflow

**Benefits**:
- 📊 Automated performance benchmarks
- 🔥 Load testing for API endpoints
- 📈 Performance regression detection
- 💾 Memory and CPU profiling

**Setup Steps**:

### Step 1: Move workflow file

```bash
cd /Users/oypnus/Project/rag-enterprise/.github/workflows
mv _disabled/performance.yml .
```

### Step 2: Configure performance tests

The workflow expects performance tests in `tests/performance/`:

```bash
mkdir -p /Users/oypnus/Project/rag-enterprise/tests/performance

# Example performance test
cat > /Users/oypnus/Project/rag-enterprise/tests/performance/test_api_performance.py << 'EOF'
"""
API Performance Tests
"""
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rag_query_performance():
    """Test RAG query response time < 2 seconds"""
    start = time.time()

    response = client.post("/api/v1/rag/query", json={
        "query": "What are the Cpk requirements?",
        "top_k": 5
    })

    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 2.0, f"Query took {elapsed:.2f}s (target: <2s)"

def test_vector_search_performance():
    """Test vector search response time < 100ms"""
    start = time.time()

    response = client.post("/api/v1/search", json={
        "query": "50ml PET bottle",
        "top_k": 10
    })

    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 0.1, f"Search took {elapsed:.2f}s (target: <0.1s)"
EOF
```

### Step 3: Configure benchmarking tools

Install performance testing dependencies:

```bash
# Add to requirements.txt
echo "pytest-benchmark>=4.0.0" >> requirements.txt
echo "locust>=2.15.0" >> requirements.txt
echo "memory-profiler>=0.61.0" >> requirements.txt
```

### Step 4: Test manually

```bash
cd /Users/oypnus/Project/rag-enterprise

# Run performance tests locally
pytest tests/performance/ -v --benchmark-only
```

---

## 🚀 4. Activate Deploy Workflow (Advanced)

**Benefits**:
- 🔄 Automated deployment to staging/production
- 🐳 Docker image building and registry push
- 🎯 Canary deployment strategy (10% → 100% traffic)
- ↩️ Automatic rollback on failure
- 📊 Health check validation

**Prerequisites** (MUST be configured first):

1. **Container Registry Access**:
   - GitHub Container Registry (GHCR) - free for public repos
   - OR Docker Hub, AWS ECR, Google GCR

2. **Deployment Infrastructure**:
   - Kubernetes cluster OR
   - Docker Compose environment OR
   - Cloud platform (AWS ECS, GCP Cloud Run, Azure Container Instances)

3. **Environment Secrets**:
   - Database credentials
   - API keys (OpenAI, Anthropic, etc.)
   - Vector DB credentials (Qdrant)

### Step 1: Container Registry Setup

**Option A: GitHub Container Registry (Recommended)**

```bash
# GHCR is free for public repos and integrated with GitHub Actions
# No additional setup needed - uses GITHUB_TOKEN automatically

# Test GHCR access:
echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
```

**Option B: Docker Hub**

```bash
# 1. Create account at https://hub.docker.com
# 2. Generate access token: Account Settings → Security → New Access Token
# 3. Add secrets to GitHub:
#    - DOCKERHUB_USERNAME: your-username
#    - DOCKERHUB_TOKEN: your-access-token
```

### Step 2: Configure deployment target

The workflow supports multiple deployment strategies:

**Strategy 1: Kubernetes**

Add to GitHub secrets:
- `KUBE_CONFIG`: Base64-encoded kubeconfig file
- `KUBE_NAMESPACE`: Kubernetes namespace (e.g., `rag-enterprise-prod`)

```bash
# Encode kubeconfig
cat ~/.kube/config | base64 > /tmp/kubeconfig_b64.txt

# Add to GitHub secrets as KUBE_CONFIG
```

**Strategy 2: Docker Compose (Simple)**

Add to GitHub secrets:
- `DEPLOY_SSH_KEY`: SSH private key for deployment server
- `DEPLOY_HOST`: Server hostname/IP
- `DEPLOY_USER`: SSH username

```bash
# Generate deployment SSH key
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N ""

# Add public key to deployment server
ssh-copy-id -i ~/.ssh/deploy_key.pub user@deploy-server

# Add private key to GitHub secrets as DEPLOY_SSH_KEY
cat ~/.ssh/deploy_key | base64
```

### Step 3: Move workflow file

```bash
cd /Users/oypnus/Project/rag-enterprise/.github/workflows
mv _disabled/deploy.yml .
```

### Step 4: Configure environment variables

Edit `deploy.yml` to set your deployment configuration:

```yaml
env:
  REGISTRY: ghcr.io  # Or docker.io for Docker Hub
  IMAGE_NAME: ${{ github.repository }}
  DEPLOYMENT_TARGET: kubernetes  # Or 'docker-compose', 'ecs', 'cloud-run'
```

### Step 5: Test staging deployment

```bash
# Push to main branch
git add .
git commit -m "feat: Activate deployment workflow"
git push origin main

# Workflow will automatically:
# 1. Build Docker image
# 2. Push to registry
# 3. Deploy to staging
# 4. Run integration tests
# 5. Wait for manual approval for production
```

---

## 🔧 Configuration Reference

### GitHub Secrets Required

| Workflow | Secret Name | Description | Required? |
|----------|-------------|-------------|-----------|
| **All** | `GITHUB_TOKEN` | Auto-provided by GitHub | ✅ Auto |
| **Security** | `SNYK_TOKEN` | Snyk vulnerability scanning | Optional |
| **Security** | `SONAR_TOKEN` | SonarCloud code quality | Optional |
| **Deploy** | `DOCKERHUB_USERNAME` | Docker Hub username (if not GHCR) | Optional |
| **Deploy** | `DOCKERHUB_TOKEN` | Docker Hub access token | Optional |
| **Deploy** | `KUBE_CONFIG` | Kubernetes config (base64) | For K8s deploy |
| **Deploy** | `DEPLOY_SSH_KEY` | SSH key for deployment server | For Docker Compose |
| **Deploy** | `DEPLOY_HOST` | Deployment server hostname | For Docker Compose |

### Workflow Permissions

Ensure workflows have correct permissions in `.github/workflows/*.yml`:

```yaml
permissions:
  contents: read        # Read repository contents
  packages: write       # Push to GHCR
  security-events: write  # Security scan results
  actions: read         # Read workflow status
```

---

## 🧪 Testing Workflows

### Manual Trigger

All workflows support manual triggering:

```bash
# In GitHub UI:
# 1. Go to Actions tab
# 2. Select workflow (CI, Security, Performance, Deploy, Release)
# 3. Click "Run workflow"
# 4. Select branch
# 5. Configure inputs (if any)
# 6. Click "Run workflow" button
```

### Local Testing (Act)

Test workflows locally before pushing:

```bash
# Install act: https://github.com/nektos/act
brew install act

# Test CI workflow
cd /Users/oypnus/Project/rag-enterprise
act -W .github/workflows/ci.yml

# Test security workflow
act -W .github/workflows/security.yml -s GITHUB_TOKEN=$GITHUB_TOKEN
```

---

## 📝 Maintenance Tasks

### Weekly

- ✅ Check Actions tab for failed workflows
- ✅ Review security scan results
- ✅ Monitor performance benchmarks

### Monthly

- ✅ Update workflow dependencies (actions versions)
- ✅ Review and rotate secrets
- ✅ Audit workflow permissions

### Before Production Deployment

- ✅ Run all tests locally: `pytest tests/ -v --cov=src`
- ✅ Verify Docker image builds: `docker build -t rag-enterprise:test .`
- ✅ Test deployment to staging environment first
- ✅ Validate health checks and monitoring

---

## 🐛 Troubleshooting

### Common Issues

**1. Workflow fails with "permission denied"**

**Solution**: Check repository settings:
- Settings → Actions → General → Workflow permissions
- Enable "Read and write permissions"

**2. Security workflow fails: "CodeQL not supported for Python 3.11"**

**Solution**: Downgrade Python version in workflow to 3.10:
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.10'  # CodeQL supports up to 3.10
```

**3. Deploy workflow fails: "Cannot connect to Docker daemon"**

**Solution**: Ensure Docker is installed on runner:
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```

**4. Release workflow doesn't create release**

**Solution**: Ensure commits follow Conventional Commits format:
```bash
# ❌ Wrong:
git commit -m "added new feature"

# ✅ Correct:
git commit -m "feat: Add new feature description"
```

---

## 📚 Additional Resources

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Semantic Versioning**: https://semver.org/
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **Kubernetes Deployment**: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/

---

## ✅ Quick Start Checklist

- [ ] Read this activation guide completely
- [ ] Activate Security workflow (highest value, lowest complexity)
- [ ] Configure GitHub secrets (as needed)
- [ ] Test manually from Actions tab
- [ ] Review security scan results
- [ ] Activate Release workflow (when ready for versioning)
- [ ] Create initial version tag (v1.0.0)
- [ ] Activate Performance workflow (when tests are ready)
- [ ] Activate Deploy workflow (when infrastructure is ready)
- [ ] Monitor all workflows in Actions tab

---

**For questions or issues, refer to `.github/workflows/_disabled/secrets.md` for detailed secret configuration examples.**
