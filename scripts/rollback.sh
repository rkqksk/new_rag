#!/usr/bin/env bash
# Rollback Deployment Script
# Usage: ./scripts/rollback.sh [deployment-name] [namespace]

set -e

DEPLOYMENT=${1:-api}
NAMESPACE=${2:-rag-production}

echo "🔄 Rolling back deployment: $DEPLOYMENT in $NAMESPACE"

# Rollback
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE

# Wait for rollout
echo "✓ Waiting for rollback to complete..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=5m

echo "✅ Rollback completed successfully!"
kubectl get deployment $DEPLOYMENT -n $NAMESPACE
