---
name: coreweave-webhooks-events
description: |
  Monitor CoreWeave cluster events and GPU workload status.
  Use when tracking pod lifecycle events, monitoring GPU utilization,
  or alerting on inference service health changes.
  Trigger with phrases like "coreweave events", "coreweave monitoring",
  "coreweave pod alerts", "coreweave gpu monitoring".
allowed-tools: Read, Write, Edit, Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Webhooks & Events

## Kubernetes Event Monitoring

```bash
# Watch GPU pod events
kubectl get events --watch --field-selector=reason=Scheduled,reason=Pulled,reason=Failed

# Monitor GPU utilization via exec
kubectl exec -it deployment/inference -- nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 5
```

## Prometheus GPU Metrics

```yaml
# DCGM exporter for GPU metrics (pre-installed on CKS)
# Key metrics:
# DCGM_FI_DEV_GPU_UTIL - GPU utilization %
# DCGM_FI_DEV_FB_USED - GPU memory used
# DCGM_FI_DEV_POWER_USAGE - Power draw
```

## Slack Alert Integration

```python
import subprocess, json, requests

def check_inference_health(deployment: str, slack_url: str):
    result = subprocess.run(
        ["kubectl", "get", "deployment", deployment, "-o", "json"],
        capture_output=True, text=True,
    )
    deploy = json.loads(result.stdout)
    ready = deploy["status"].get("readyReplicas", 0)
    desired = deploy["spec"]["replicas"]

    if ready < desired:
        requests.post(slack_url, json={
            "text": f"CoreWeave: {deployment} has {ready}/{desired} replicas ready"
        })
```

## Resources

- [CoreWeave Observability](https://www.coreweave.com/observability)

## Next Steps

For performance optimization, see `coreweave-performance-tuning`.
