#!/usr/bin/env bash
# Production Deployment Script
# Usage: ./scripts/deploy-production.sh [version]

set -e

VERSION=${1:-latest}
NAMESPACE="rag-production"

echo "🚀 RAG Enterprise Production Deployment"
echo "========================================"
echo "Version: $VERSION"
echo "Namespace: $NAMESPACE"
echo ""

# Verify kubectl connection
echo "✓ Verifying Kubernetes connection..."
kubectl cluster-info > /dev/null 2>&1 || {
  echo "❌ Cannot connect to Kubernetes cluster"
  exit 1
}

# Verify namespace
echo "✓ Checking namespace..."
kubectl get namespace $NAMESPACE > /dev/null 2>&1 || {
  echo "Creating namespace $NAMESPACE..."
  kubectl create namespace $NAMESPACE
}

# Apply base configurations
echo "✓ Applying base configurations..."
kubectl apply -f infrastructure/k8s/base/

# Apply production overlays
echo "✓ Applying production configurations..."
kubectl apply -f infrastructure/k8s/overlays/production/

# Update images
echo "✓ Updating container images to $VERSION..."
kubectl set image deployment/api api=ghcr.io/rkqksk/new_rag-api:$VERSION -n $NAMESPACE
kubectl set image deployment/web web=ghcr.io/rkqksk/new_rag-web:$VERSION -n $NAMESPACE

# Wait for rollout
echo "✓ Waiting for rollout to complete..."
kubectl rollout status deployment/api -n $NAMESPACE --timeout=5m
kubectl rollout status deployment/web -n $NAMESPACE --timeout=5m

# Verify deployment
echo "✓ Verifying deployment..."
kubectl get pods -n $NAMESPACE

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Status:"
kubectl get deployments -n $NAMESPACE
echo ""
echo "🌐 Access:"
echo "  - Web: https://rag-enterprise.com"
echo "  - API: https://api.rag-enterprise.com"
