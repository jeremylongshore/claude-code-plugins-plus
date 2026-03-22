---
name: coreweave-multi-env-setup
description: |
  Configure CoreWeave across development, staging, and production environments.
  Use when setting up multi-environment GPU infrastructure, separating namespaces,
  or managing per-environment GPU quotas.
  Trigger with phrases like "coreweave environments", "coreweave staging",
  "coreweave multi-env", "coreweave namespace setup".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(kustomize:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Multi-Env Setup

## Environment Strategy

| Environment | GPU Type | Scale-to-Zero | Replicas |
|-------------|----------|---------------|----------|
| Dev | L40 | Yes | 0-1 |
| Staging | A100 40GB | Yes | 0-2 |
| Production | A100 80GB | No | 2-10 |

## Kustomize Overlays

```yaml
# k8s/overlays/dev/gpu-patch.yaml
- op: replace
  path: /spec/template/spec/affinity/nodeAffinity/requiredDuringSchedulingIgnoredDuringExecution/nodeSelectorTerms/0/matchExpressions/0/values
  value: ["L40"]

# k8s/overlays/prod/gpu-patch.yaml
  value: ["A100_PCIE_80GB"]
```

```bash
# Deploy per environment
kubectl apply -k k8s/overlays/dev/
kubectl apply -k k8s/overlays/prod/
```

## Resources

- [CoreWeave CKS](https://docs.coreweave.com/docs/products/cks)

## Next Steps

For observability, see `coreweave-observability`.
