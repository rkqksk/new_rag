# Kubernetes Auto-scaling Guide (v6.0.0)

## Quick Start

```bash
kubectl apply -f k8s/
kubectl get hpa --watch
```

## HPA Configuration

- Min replicas: 3
- Max replicas: 20
- CPU target: 70%
- Memory target: 80%

## Scaling Behavior

- Scale up: +100% or +4 pods/min
- Scale down: -50% or -2 pods/5min

See hpa.yaml for full configuration.
