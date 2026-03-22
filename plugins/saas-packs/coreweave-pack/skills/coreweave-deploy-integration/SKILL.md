---
name: coreweave-deploy-integration
description: |
  Deploy inference services on CoreWeave with Helm charts and Kustomize.
  Use when deploying multi-model inference, managing GPU deployments at scale,
  or templating CoreWeave manifests.
  Trigger with phrases like "deploy coreweave", "coreweave helm",
  "coreweave kustomize", "coreweave deployment patterns".
allowed-tools: Read, Write, Edit, Bash(helm:*), Bash(kubectl:*), Bash(kustomize:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Deploy Integration

## Helm Chart for Inference Service

```yaml
# helm/values.yaml
replicaCount: 2
image:
  repository: vllm/vllm-openai
  tag: latest
gpu:
  type: A100_PCIE_80GB
  count: 1
  memory: 48Gi
model:
  name: meta-llama/Llama-3.1-8B-Instruct
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 5
  targetConcurrency: 2
```

```bash
helm install my-inference ./helm -f values-prod.yaml
helm upgrade my-inference ./helm -f values-prod.yaml
```

## Kustomize Overlays

```
k8s/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/
│   │   ├── gpu-patch.yaml       # L40 GPU for dev
│   │   └── kustomization.yaml
│   └── prod/
│       ├── gpu-patch.yaml       # A100/H100 for prod
│       ├── replicas-patch.yaml
│       └── kustomization.yaml
```

```bash
kubectl apply -k k8s/overlays/prod/
```

## Resources

- [CoreWeave CKS](https://docs.coreweave.com/docs/products/cks)
- [Helm Documentation](https://helm.sh/docs/)

## Next Steps

For event monitoring, see `coreweave-webhooks-events`.
