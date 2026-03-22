---
name: coreweave-local-dev-loop
description: |
  Set up local development workflow for CoreWeave GPU deployments.
  Use when building containers locally, testing YAML manifests,
  or iterating on model serving configurations before deploying.
  Trigger with phrases like "coreweave dev setup", "coreweave local testing",
  "develop for coreweave", "coreweave container build".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Local Dev Loop

## Overview

Local development workflow for CoreWeave: build containers, test YAML manifests with dry-run, push to registry, and deploy to CoreWeave CKS.

## Prerequisites

- Completed `coreweave-install-auth` setup
- Docker installed locally
- Container registry access (Docker Hub, GHCR, or CoreWeave registry)

## Instructions

### Step 1: Project Structure

```
my-inference-service/
├── Dockerfile
├── src/
│   ├── server.py          # Inference server code
│   └── model_config.py    # Model configuration
├── k8s/
│   ├── deployment.yaml    # GPU deployment manifest
│   ├── service.yaml       # Service and ingress
│   └── hpa.yaml           # Horizontal pod autoscaler
├── scripts/
│   ├── build.sh           # Build and push container
│   └── deploy.sh          # Deploy to CoreWeave
├── .env.local
└── Makefile
```

### Step 2: Build and Push Container

```bash
# Build locally
docker build -t my-inference:latest .

# Tag for registry
docker tag my-inference:latest ghcr.io/myorg/my-inference:v1.0.0

# Push
docker push ghcr.io/myorg/my-inference:v1.0.0
```

### Step 3: Validate Manifests Before Deploy

```bash
# Dry-run against CoreWeave cluster
kubectl apply -f k8s/deployment.yaml --dry-run=server

# Diff against current state
kubectl diff -f k8s/deployment.yaml

# Check resource requests match available GPU types
kubectl get nodes -l gpu.nvidia.com/class=A100_PCIE_80GB --no-headers | wc -l
```

### Step 4: Deploy and Watch

```bash
kubectl apply -f k8s/
kubectl rollout status deployment/my-inference
kubectl logs -f deployment/my-inference
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Image pull backoff | Wrong registry or no pull secret | Create imagePullSecret |
| CUDA mismatch | Driver vs container version | Match CUDA version to node drivers |
| Dry-run fails | Invalid manifest | Fix YAML syntax |

## Resources

- [CoreWeave CKS Docs](https://docs.coreweave.com/docs/products/cks)
- [kubectl dry-run](https://kubernetes.io/docs/reference/kubectl/)

## Next Steps

See `coreweave-sdk-patterns` for inference client patterns.
