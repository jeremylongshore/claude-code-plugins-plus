---
name: coreweave-upgrade-migration
description: |
  Upgrade CoreWeave deployments and migrate between GPU types.
  Use when migrating from A100 to H100, upgrading CUDA versions,
  or updating inference server versions.
  Trigger with phrases like "upgrade coreweave", "coreweave gpu migration",
  "coreweave cuda upgrade", "migrate coreweave".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Upgrade & Migration

## GPU Type Migration

```yaml
# Before: A100
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: gpu.nvidia.com/class
              operator: In
              values: ["A100_PCIE_80GB"]

# After: H100 (update affinity label)
              values: ["H100_SXM5"]
```

### Migration Steps

1. Build new container with updated CUDA version if needed
2. Deploy with new GPU affinity alongside old deployment
3. Shift traffic gradually (canary)
4. Validate latency and throughput match or improve
5. Scale down old deployment

### CUDA Version Matrix

| GPU Type | Recommended CUDA | Driver |
|----------|-----------------|--------|
| A100 | CUDA 12.2+ | 535+ |
| H100 | CUDA 12.4+ | 550+ |
| L40 | CUDA 12.2+ | 535+ |

### Rollback

```bash
kubectl rollout undo deployment/my-inference
```

## Resources

- [CoreWeave GPU Instances](https://docs.coreweave.com/docs/platform/instances/gpu-instances)

## Next Steps

For CI/CD, see `coreweave-ci-integration`.
