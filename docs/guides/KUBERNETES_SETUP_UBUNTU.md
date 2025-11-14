# Kubernetes Setup Guide for Ubuntu

**Complete guide for setting up Kubernetes on Ubuntu 22.04/24.04 LTS**

Version: v1.0.0
Last Updated: 2025-11-14

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation Options](#installation-options)
4. [Option 1: Minikube (Recommended for Development)](#option-1-minikube)
5. [Option 2: K3s (Lightweight Production)](#option-2-k3s)
6. [Option 3: MicroK8s (Canonical's Distribution)](#option-3-microk8s)
7. [Deploying RAG Enterprise](#deploying-rag-enterprise)
8. [Monitoring & Management](#monitoring--management)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This guide covers three Kubernetes distribution options for Ubuntu:

| Distribution | Best For | Resource Usage | Production Ready |
|--------------|----------|----------------|------------------|
| **Minikube** | Local development, testing | Low-Medium | ❌ Dev only |
| **K3s** | Edge, IoT, production | Very Low | ✅ Yes |
| **MicroK8s** | Ubuntu servers, production | Low-Medium | ✅ Yes |

**Our Recommendation:**
- **Development**: Minikube
- **Production (Ubuntu)**: MicroK8s or K3s

---

## ✅ Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB free space
- Ubuntu 22.04 or 24.04 LTS

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ free space
- SSD storage

### Required Software

```bash
# Docker (required for all options)
docker --version  # Should be 20.10+

# If Docker not installed:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

---

## 🚀 Option 1: Minikube

**Best for:** Local development, CI/CD testing, learning Kubernetes

### 1.1 Installation

```bash
# Download Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Install
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

# Verify
minikube version
```

### 1.2 Install kubectl

```bash
# Download kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# Verify
kubectl version --client
```

### 1.3 Start Minikube Cluster

```bash
# Start with Docker driver (recommended)
minikube start --driver=docker --cpus=4 --memory=8192 --disk-size=50g

# Or start with default resources
minikube start

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

### 1.4 Enable Addons

```bash
# Enable metrics-server (for monitoring)
minikube addons enable metrics-server

# Enable dashboard (optional)
minikube addons enable dashboard

# Enable ingress (for external access)
minikube addons enable ingress

# List all addons
minikube addons list
```

### 1.5 Access Dashboard

```bash
# Start dashboard
minikube dashboard

# Or get dashboard URL
minikube dashboard --url
```

### 1.6 Useful Commands

```bash
# Stop cluster
minikube stop

# Delete cluster
minikube delete

# SSH into cluster
minikube ssh

# Check cluster status
minikube status

# View logs
minikube logs
```

---

## 🔷 Option 2: K3s

**Best for:** Production edge deployments, lightweight clusters, resource-constrained environments

### 2.1 Installation

```bash
# Install K3s (single-node cluster)
curl -sfL https://get.k3s.io | sh -

# Install with custom options
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=traefik" sh -

# Verify installation
sudo systemctl status k3s

# Check nodes
sudo k3s kubectl get nodes
```

### 2.2 Configure kubectl

```bash
# Copy kubeconfig
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# Test
kubectl get nodes
```

### 2.3 Useful Commands

```bash
# Start K3s
sudo systemctl start k3s

# Stop K3s
sudo systemctl stop k3s

# Uninstall K3s
/usr/local/bin/k3s-uninstall.sh

# View logs
sudo journalctl -u k3s -f
```

---

## 🟦 Option 3: MicroK8s

**Best for:** Ubuntu servers, production deployments, snap ecosystem users

### 3.1 Installation

```bash
# Install MicroK8s via snap
sudo snap install microk8s --classic

# Add user to microk8s group
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube

# Refresh group membership (or logout/login)
newgrp microk8s

# Wait for cluster to be ready
microk8s status --wait-ready
```

### 3.2 Enable Addons

```bash
# Enable DNS
microk8s enable dns

# Enable storage
microk8s enable storage

# Enable dashboard
microk8s enable dashboard

# Enable ingress
microk8s enable ingress

# Enable metrics-server
microk8s enable metrics-server

# Enable registry (optional)
microk8s enable registry

# List all addons
microk8s status
```

### 3.3 Configure kubectl

```bash
# Option 1: Use microk8s kubectl
microk8s kubectl get nodes

# Option 2: Create alias
alias kubectl='microk8s kubectl'

# Option 3: Export config
microk8s config > ~/.kube/config
```

### 3.4 Access Dashboard

```bash
# Get dashboard token
microk8s kubectl create token default

# Get dashboard URL (in separate terminal)
microk8s dashboard-proxy
```

### 3.5 Useful Commands

```bash
# Check status
microk8s status

# Stop MicroK8s
microk8s stop

# Start MicroK8s
microk8s start

# Uninstall
sudo snap remove microk8s

# View logs
microk8s inspect
```

---

## 🚢 Deploying RAG Enterprise

### Prerequisites

1. Choose and install Kubernetes (Minikube, K3s, or MicroK8s)
2. Ensure kubectl is configured
3. Build Docker image

### Step 1: Build Docker Image

```bash
cd /home/rkqksk/projects/new_rag

# Build image
docker build -t rag-enterprise-api:latest .

# For Minikube, load image into cluster
minikube image load rag-enterprise-api:latest

# For K3s, import image
sudo k3s ctr images import rag-enterprise-api.tar

# For MicroK8s, import image
docker save rag-enterprise-api:latest > rag-enterprise-api.tar
microk8s ctr image import rag-enterprise-api.tar
```

### Step 2: Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### Step 3: Deploy Secrets

```bash
# Edit secrets first
nano k8s/secrets.yaml

# Apply secrets
kubectl apply -f k8s/secrets.yaml
```

### Step 4: Deploy ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### Step 5: Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgres-statefulset.yaml
```

### Step 6: Deploy Qdrant

```bash
kubectl apply -f k8s/qdrant-statefulset.yaml
```

### Step 7: Deploy Redis

```bash
kubectl apply -f k8s/redis-deployment.yaml
```

### Step 8: Deploy API

```bash
kubectl apply -f k8s/api-deployment.yaml
```

### Step 9: Deploy Ingress

```bash
kubectl apply -f k8s/ingress.yaml
```

### Step 10: Enable Auto-Scaling (Optional)

```bash
kubectl apply -f k8s/hpa.yaml
```

### Verify Deployment

```bash
# Check all resources
kubectl get all -n rag-enterprise

# Check pods
kubectl get pods -n rag-enterprise

# Check services
kubectl get svc -n rag-enterprise

# Check logs
kubectl logs -n rag-enterprise -l app=rag-api -f

# Check pod details
kubectl describe pod -n rag-enterprise <pod-name>
```

### Access Services

**Minikube:**
```bash
# Get service URL
minikube service -n rag-enterprise rag-api --url

# Port forward
kubectl port-forward -n rag-enterprise svc/rag-api 8001:8001
```

**K3s/MicroK8s:**
```bash
# Port forward
kubectl port-forward -n rag-enterprise svc/rag-api 8001:8001

# Or get NodePort
kubectl get svc -n rag-enterprise rag-api
```

---

## 📊 Monitoring & Management

### View Logs

```bash
# API logs
kubectl logs -n rag-enterprise -l app=rag-api -f

# PostgreSQL logs
kubectl logs -n rag-enterprise -l app=postgres -f

# All pods
kubectl logs -n rag-enterprise --all-containers=true -f
```

### Resource Usage

```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods -n rag-enterprise

# Detailed pod info
kubectl describe pod -n rag-enterprise <pod-name>
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment -n rag-enterprise rag-api --replicas=5

# Check HPA status
kubectl get hpa -n rag-enterprise

# Describe HPA
kubectl describe hpa -n rag-enterprise rag-api-hpa
```

### Updates

```bash
# Update image
kubectl set image deployment/rag-api -n rag-enterprise api=rag-enterprise-api:v2.0.0

# Rollout status
kubectl rollout status deployment/rag-api -n rag-enterprise

# Rollout history
kubectl rollout history deployment/rag-api -n rag-enterprise

# Rollback
kubectl rollout undo deployment/rag-api -n rag-enterprise
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Image Pull Errors

```bash
# For Minikube
minikube image load rag-enterprise-api:latest

# For MicroK8s
docker save rag-enterprise-api:latest | microk8s ctr image import -

# Update deployment to use local image
kubectl set image deployment/rag-api -n rag-enterprise api=rag-enterprise-api:latest
kubectl patch deployment rag-api -n rag-enterprise -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","imagePullPolicy":"IfNotPresent"}]}}}}'
```

#### 2. Pod Crashes

```bash
# Check pod status
kubectl get pods -n rag-enterprise

# View logs
kubectl logs -n rag-enterprise <pod-name>

# Describe pod
kubectl describe pod -n rag-enterprise <pod-name>

# Check events
kubectl get events -n rag-enterprise --sort-by=.metadata.creationTimestamp
```

#### 3. Service Not Accessible

```bash
# Check service
kubectl get svc -n rag-enterprise

# Port forward
kubectl port-forward -n rag-enterprise svc/rag-api 8001:8001

# Check endpoints
kubectl get endpoints -n rag-enterprise
```

#### 4. Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl get pods -n rag-enterprise -l app=postgres

# Test connection
kubectl exec -n rag-enterprise -it <postgres-pod> -- psql -U postgres -d rag_enterprise

# Check service DNS
kubectl run -n rag-enterprise debug --image=busybox:1.28 --rm -it --restart=Never -- nslookup postgres
```

### Cleanup

```bash
# Delete all resources in namespace
kubectl delete namespace rag-enterprise

# For Minikube
minikube stop
minikube delete

# For K3s
/usr/local/bin/k3s-uninstall.sh

# For MicroK8s
microk8s reset
sudo snap remove microk8s
```

---

## 📚 Additional Resources

- **Kubernetes Documentation**: https://kubernetes.io/docs/
- **Minikube**: https://minikube.sigs.k8s.io/docs/
- **K3s**: https://docs.k3s.io/
- **MicroK8s**: https://microk8s.io/docs

---

## 🎓 Next Steps

1. **Production Deployment**: See `docs/guides/DEPLOYMENT_GUIDE.md`
2. **Monitoring Setup**: Configure Prometheus & Grafana
3. **High Availability**: Multi-node cluster setup
4. **CI/CD Integration**: GitHub Actions → Kubernetes

---

**Updated:** 2025-11-14
**Author:** RAG Enterprise Team
**License:** MIT
