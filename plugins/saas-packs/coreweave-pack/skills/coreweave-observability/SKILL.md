---
name: coreweave-observability
description: |
  Set up GPU monitoring and observability for CoreWeave workloads.
  Use when implementing GPU metrics dashboards, configuring alerts,
  or tracking inference latency and throughput.
  Trigger with phrases like "coreweave monitoring", "coreweave observability",
  "coreweave gpu metrics", "coreweave grafana".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Observability

## GPU Metrics (DCGM Exporter)

CKS clusters come with DCGM exporter pre-installed. Key metrics:

| Metric | Description |
|--------|-------------|
| `DCGM_FI_DEV_GPU_UTIL` | GPU core utilization % |
| `DCGM_FI_DEV_FB_USED` | GPU memory used (MB) |
| `DCGM_FI_DEV_FB_FREE` | GPU memory free (MB) |
| `DCGM_FI_DEV_POWER_USAGE` | Power consumption (W) |
| `DCGM_FI_DEV_GPU_TEMP` | GPU temperature (C) |

## Prometheus Alert Rules

```yaml
groups:
  - name: coreweave-gpu
    rules:
      - alert: GPUUtilizationLow
        expr: avg(DCGM_FI_DEV_GPU_UTIL) < 20
        for: 30m
        labels: { severity: warning }
        annotations:
          summary: "GPU utilization below 20% for 30min -- consider scaling down"

      - alert: GPUMemoryHigh
        expr: DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE) > 0.95
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "GPU memory >95% -- risk of OOM"

      - alert: InferencePodDown
        expr: kube_deployment_status_replicas_available{deployment=~".*inference.*"} == 0
        for: 2m
        labels: { severity: critical }
```

## Resources

- [CoreWeave Observability](https://www.coreweave.com/observability)

## Next Steps

For incident response, see `coreweave-incident-runbook`.
