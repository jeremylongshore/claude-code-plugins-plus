---
name: coreweave-migration-deep-dive
description: |
  Migrate ML workloads from AWS/GCP/Azure to CoreWeave GPU cloud.
  Use when moving inference services from hyperscaler GPU instances,
  migrating training pipelines, or evaluating CoreWeave vs cloud GPU costs.
  Trigger with phrases like "migrate to coreweave", "coreweave migration",
  "move from aws to coreweave", "coreweave vs aws gpu".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Migration Deep Dive

## Cost Comparison

| Instance | AWS | CoreWeave | Savings |
|----------|-----|-----------|---------|
| 1x A100 80GB | ~$3.60/hr (p4d) | ~$2.21/hr | ~39% |
| 8x A100 80GB | ~$32/hr (p4d.24xl) | ~$17.70/hr | ~45% |
| 1x H100 80GB | ~$6.50/hr (p5) | ~$4.76/hr | ~27% |

## Migration Steps

### Phase 1: Containerize
```bash
# If running on bare EC2/GCE, containerize first
docker build -t inference-server:v1 .
docker push ghcr.io/myorg/inference-server:v1
```

### Phase 2: Adapt YAML for CoreWeave
Key changes from AWS EKS / GKE:
1. **Node affinity**: Use `gpu.nvidia.com/class` instead of `nvidia.com/gpu.product`
2. **Storage**: Use CoreWeave storage classes (`shared-ssd-ord1`)
3. **Networking**: CoreWeave provides flat networking within VPC

### Phase 3: Parallel Deploy
Run both old and new infrastructure simultaneously, gradually shift traffic.

### Phase 4: Cut Over
Decommission old GPU instances after validation period.

## Common Gotchas

| Issue | Solution |
|-------|----------|
| Different CUDA drivers | Match container CUDA to CoreWeave node drivers |
| Storage migration | Use rclone or rsync to move data to CoreWeave PVC |
| DNS changes | Update ingress/load balancer DNS |
| IAM differences | CoreWeave uses kubeconfig, not IAM roles |

## Resources

- [CoreWeave Pricing](https://www.coreweave.com/pricing)
- [CoreWeave Documentation](https://docs.coreweave.com)

## Next Steps

This completes the CoreWeave skill pack. Start with `coreweave-install-auth` for new deployments.
