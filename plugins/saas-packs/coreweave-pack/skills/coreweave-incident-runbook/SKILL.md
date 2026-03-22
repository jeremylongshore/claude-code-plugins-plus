---
name: coreweave-incident-runbook
description: |
  Incident response runbook for CoreWeave GPU workload failures.
  Use when inference services are down, GPUs are unavailable,
  or responding to production incidents on CoreWeave.
  Trigger with phrases like "coreweave incident", "coreweave outage",
  "coreweave runbook", "coreweave service down".
allowed-tools: Read, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Incident Runbook

## Triage Steps

```bash
# 1. Check pod status
kubectl get pods -l app=inference -o wide

# 2. Check recent events
kubectl get events --sort-by=.lastTimestamp | tail -20

# 3. Check node status
kubectl get nodes -l gpu.nvidia.com/class -o wide

# 4. Check GPU health
kubectl exec -it $(kubectl get pod -l app=inference -o name | head -1) -- nvidia-smi
```

## Common Incidents

### Inference Service Down
1. Check pod status and events
2. If OOMKilled: reduce batch size or upgrade GPU
3. If ImagePullBackOff: check registry credentials
4. If Pending: check GPU quota and availability

### GPU Node Failure
1. Pods will be rescheduled automatically
2. If no capacity: scale down non-critical workloads
3. Contact CoreWeave support for extended outages

### Model Loading Failure
1. Check HuggingFace token secret exists
2. Verify model name spelling
3. Check PVC has sufficient storage
4. Review container logs for download errors

## Rollback

```bash
kubectl rollout undo deployment/inference
```

## Resources

- [CoreWeave Support](https://www.coreweave.com/support)
- [CoreWeave Status](https://status.coreweave.com)

## Next Steps

For data handling, see `coreweave-data-handling`.
