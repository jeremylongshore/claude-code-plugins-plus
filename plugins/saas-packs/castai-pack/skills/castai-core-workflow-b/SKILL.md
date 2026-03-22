---
name: castai-core-workflow-b
description: |
  Configure CAST AI Workload Autoscaler for pod-level right-sizing and VPA.
  Use when enabling workload autoscaling, configuring resource recommendations,
  or tuning pod CPU and memory requests with CAST AI.
  Trigger with phrases like "cast ai workload autoscaler", "cast ai pod sizing",
  "cast ai resource recommendations", "cast ai VPA".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Core Workflow: Workload Autoscaler

## Overview

CAST AI Workload Autoscaler right-sizes pod resource requests based on actual usage, reducing over-provisioning without manual VPA tuning. This skill covers enabling the workload autoscaler, configuring scaling policies per workload, and using annotations for fine-grained control.

## Prerequisites

- Completed `castai-core-workflow-a` (cluster-level policies)
- CAST AI agent v1.60+ installed
- Workload Autoscaler enabled in CAST AI console

## Instructions

### Step 1: Install Workload Autoscaler Components

```bash
helm upgrade --install castai-workload-autoscaler \
  castai-helm/castai-workload-autoscaler \
  -n castai-agent \
  --set castai.apiKey="${CASTAI_API_KEY}" \
  --set castai.clusterID="${CASTAI_CLUSTER_ID}"
```

### Step 2: Query Workload Recommendations

```bash
# Get resource recommendations for a specific workload
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/workload-autoscaling/clusters/${CASTAI_CLUSTER_ID}/workloads" \
  | jq '.items[] | {
    name: .workloadName,
    namespace: .namespace,
    currentCpu: .currentCpuRequest,
    recommendedCpu: .recommendedCpuRequest,
    currentMemory: .currentMemoryRequest,
    recommendedMemory: .recommendedMemoryRequest,
    savingsPercent: .estimatedSavingsPercent
  }'
```

### Step 3: Configure Per-Workload Policies via Annotations

```yaml
# Add annotations to deployments for CAST AI workload autoscaler
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-api
  annotations:
    # Enable workload autoscaling
    autoscaling.cast.ai/enabled: "true"
    # CPU configuration
    autoscaling.cast.ai/cpu-min: "100m"
    autoscaling.cast.ai/cpu-max: "4000m"
    autoscaling.cast.ai/cpu-headroom: "15"
    # Memory configuration
    autoscaling.cast.ai/memory-min: "128Mi"
    autoscaling.cast.ai/memory-max: "8Gi"
    autoscaling.cast.ai/memory-headroom: "20"
    # Apply changes automatically vs recommendation-only
    autoscaling.cast.ai/apply-type: "immediate"
spec:
  template:
    spec:
      containers:
        - name: api
          resources:
            requests:
              cpu: "500m"      # Will be auto-adjusted by CAST AI
              memory: "512Mi"  # Will be auto-adjusted by CAST AI
```

### Step 4: Create a Scaling Policy via API

```bash
curl -X POST -H "X-API-Key: ${CASTAI_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://api.cast.ai/v1/workload-autoscaling/clusters/${CASTAI_CLUSTER_ID}/policies" \
  -d '{
    "name": "cost-optimized",
    "applyType": "IMMEDIATE",
    "management": {
      "cpu": {
        "function": "QUANTILE",
        "args": { "quantile": 0.95 },
        "overhead": 0.15,
        "min": 50,
        "max": 8000
      },
      "memory": {
        "function": "MAX",
        "overhead": 0.20,
        "min": 64,
        "max": 16384
      }
    },
    "antiShrink": {
      "enabled": true,
      "cooldownSeconds": 300
    }
  }'
```

### Step 5: Monitor Workload Scaling Events

```bash
# Check scaling events
kubectl get events -n default --field-selector reason=CastAIWorkloadAutoscaled

# View current vs recommended via API
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/workload-autoscaling/clusters/${CASTAI_CLUSTER_ID}/workloads/${WORKLOAD_ID}" \
  | jq '.scalingEvents[-5:]'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Workload not appearing | Missing annotation | Add `autoscaling.cast.ai/enabled: "true"` |
| OOMKilled after scaling | Memory headroom too low | Increase `memory-headroom` to 25+ |
| CPU throttling | CPU recommendation too aggressive | Increase `cpu-headroom` or set higher min |
| No recommendations yet | Insufficient data | Wait 24h for usage data collection |

## Resources

- [Workload Autoscaler Overview](https://docs.cast.ai/docs/workload-autoscaling-overview)
- [Annotations Reference](https://docs.cast.ai/docs/workload-autoscaler-annotations-reference)
- [Scaling Policies](https://docs.cast.ai/docs/woop-scaling-policies-manage)

## Next Steps

For troubleshooting CAST AI errors, see `castai-common-errors`.
