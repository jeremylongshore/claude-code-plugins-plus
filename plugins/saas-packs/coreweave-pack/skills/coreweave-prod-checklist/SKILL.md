---
name: coreweave-prod-checklist
description: |
  Production readiness checklist for CoreWeave GPU workloads.
  Use when launching inference services, preparing GPU training for production,
  or validating deployment configurations.
  Trigger with phrases like "coreweave production", "coreweave go-live",
  "coreweave checklist", "coreweave launch".
allowed-tools: Read, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Production Checklist

## Inference Services
- [ ] GPU type and count validated for model size
- [ ] Autoscaling configured (KServe or HPA)
- [ ] Health and readiness probes set
- [ ] Resource requests AND limits specified
- [ ] Node affinity targeting correct GPU class
- [ ] `minReplicas >= 1` for production (no cold starts)

## Storage
- [ ] Model weights in PVC (not downloaded at startup)
- [ ] Checkpoints saved to persistent storage
- [ ] Storage class appropriate (SSD for inference, HDD for archival)

## Security
- [ ] Secrets for model tokens and registry access
- [ ] Network policies applied
- [ ] Container images from trusted registries

## Monitoring
- [ ] GPU utilization metrics collected
- [ ] Inference latency and throughput tracked
- [ ] Alert on pod restarts and OOM events
- [ ] Log aggregation configured

## Rollback
```bash
kubectl rollout undo deployment/my-inference
kubectl rollout status deployment/my-inference
```

## Resources

- [CoreWeave CKS](https://docs.coreweave.com/docs/products/cks)

## Next Steps

For upgrades, see `coreweave-upgrade-migration`.
