---
name: coreweave-common-errors
description: |
  Diagnose and fix CoreWeave GPU scheduling, pod, and networking errors.
  Use when pods are stuck Pending, GPUs are not allocated,
  or experiencing CUDA and NCCL errors.
  Trigger with phrases like "coreweave error", "coreweave pod pending",
  "coreweave gpu not found", "coreweave debug", "fix coreweave".
allowed-tools: Read, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Common Errors

## Error Reference

### 1. Pod Stuck Pending -- No GPU Available
```bash
kubectl describe pod <pod-name> | grep -A5 Events
# "0/N nodes are available: insufficient nvidia.com/gpu"
```
**Fix**: Check GPU availability: `kubectl get nodes -l gpu.nvidia.com/class=A100_PCIE_80GB`. Try a different GPU type or region.

### 2. CUDA Out of Memory
```
torch.cuda.OutOfMemoryError: CUDA out of memory
```
**Fix**: Reduce batch size, enable gradient checkpointing, or use a larger GPU (A100-80GB instead of 40GB).

### 3. Image Pull BackOff
**Fix**: Create an imagePullSecret:
```bash
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=$GH_USER \
  --docker-password=$GH_TOKEN
```

### 4. NCCL Timeout (Multi-GPU)
```
NCCL error: unhandled system error
```
**Fix**: Ensure all GPUs are on the same node (NVLink). For multi-node, use InfiniBand-connected nodes.

### 5. PVC Not Mounting
**Fix**: Check storage class availability: `kubectl get sc`. Use CoreWeave storage classes like `shared-hdd-ord1` or `shared-ssd-ord1`.

### 6. Node Affinity Mismatch
**Fix**: List valid GPU class labels:
```bash
kubectl get nodes -o json | jq -r '.items[].metadata.labels["gpu.nvidia.com/class"]' | sort -u
```

### 7. Service Not Reachable
**Fix**: Check Service and Endpoints:
```bash
kubectl get svc,endpoints <service-name>
```

## Resources

- [CoreWeave Documentation](https://docs.coreweave.com)
- [GPU Instance Types](https://docs.coreweave.com/docs/platform/instances/gpu-instances)

## Next Steps

For diagnostics, see `coreweave-debug-bundle`.
