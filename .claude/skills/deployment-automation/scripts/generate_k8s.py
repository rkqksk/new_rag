#!/usr/bin/env python3
"""Generate Kubernetes manifests"""
import argparse
from pathlib import Path

K8S_TEMPLATE = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {image}
        ports:
        - containerPort: {port}
        env:
        - name: ENV
          value: "production"
---
apiVersion: v1
kind: Service
metadata:
  name: {app_name}
spec:
  selector:
    app: {app_name}
  ports:
  - port: 80
    targetPort: {port}
  type: ClusterIP
"""

def generate_manifests(app_name: str, image: str, port: int, replicas: int, output: str):
    """Generate K8s deployment and service manifests"""
    manifest = K8S_TEMPLATE.format(
        app_name=app_name,
        image=image,
        port=port,
        replicas=replicas
    )

    output_file = Path(output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(manifest)
    print(f"✅ Generated: {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--replicas', type=int, default=3)
    parser.add_argument('--output', default='k8s/deployment.yaml')
    args = parser.parse_args()
    generate_manifests(args.app, args.image, args.port, args.replicas, args.output)
