---
name: castai-core-workflow-a
description: |
  Configure CAST AI autoscaler policies and node templates for cost optimization.
  Use when enabling Phase 2 automation, setting spot instance policies,
  or configuring node downscaler and evictor settings.
  Trigger with phrases like "cast ai autoscaler", "cast ai policies",
  "cast ai spot instances", "cast ai node optimization".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Core Workflow: Autoscaler & Policies

## Overview

Primary workflow for CAST AI: configure autoscaler policies to optimize cluster costs. Covers enabling spot instances, configuring the node downscaler and evictor, setting cluster CPU/memory limits, and creating node templates for workload-specific requirements.

## Prerequisites

- Completed `castai-install-auth` with Phase 2 (cluster controller + evictor)
- `CASTAI_API_KEY` and `CASTAI_CLUSTER_ID` set
- Cluster in "ready" status

## Instructions

### Step 1: Read Current Policies

```bash
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  | jq .
```

### Step 2: Enable Cost-Optimized Autoscaling

```bash
curl -X PUT -H "X-API-Key: ${CASTAI_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  -d '{
    "enabled": true,
    "unschedulablePods": {
      "enabled": true,
      "headroom": {
        "cpuPercentage": 10,
        "memoryPercentage": 10,
        "enabled": true
      }
    },
    "nodeDownscaler": {
      "enabled": true,
      "emptyNodes": {
        "enabled": true,
        "delaySeconds": 180
      }
    },
    "spotInstances": {
      "enabled": true,
      "clouds": ["aws"],
      "spotDiversityEnabled": true,
      "spotDiversityPriceIncreaseLimitPercent": 20
    },
    "clusterLimits": {
      "enabled": true,
      "cpu": {
        "minCores": 4,
        "maxCores": 100
      }
    }
  }'
```

### Step 3: Configure Node Templates via Terraform

```hcl
resource "castai_node_template" "spot_workers" {
  cluster_id = castai_eks_cluster.this.id
  name       = "spot-workers"
  is_default = false
  is_enabled = true

  constraints {
    min_cpu               = 2
    max_cpu               = 16
    min_memory            = 4096
    max_memory            = 65536
    spot                  = true
    use_spot_fallbacks    = true
    fallback_restore_rate_seconds = 600

    instance_families {
      include = ["m5", "m6i", "c5", "c6i", "r5", "r6i"]
    }

    architectures = ["amd64"]
  }

  custom_labels = {
    "workload-type" = "batch"
  }
}

resource "castai_node_template" "gpu_ondemand" {
  cluster_id = castai_eks_cluster.this.id
  name       = "gpu-ondemand"
  is_default = false
  is_enabled = true

  constraints {
    spot                  = false
    gpu_manufacturers     = ["NVIDIA"]

    instance_families {
      include = ["p3", "p4d", "g4dn", "g5"]
    }
  }

  custom_labels = {
    "workload-type" = "gpu"
  }
}
```

### Step 4: Verify Autoscaler is Working

```bash
# Check if the autoscaler is processing nodes
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/external-clusters/${CASTAI_CLUSTER_ID}/nodes" \
  | jq '[.items[] | {name, instanceType, lifecycle, castaiManaged: .castaiManaged}]
        | group_by(.lifecycle)
        | map({lifecycle: .[0].lifecycle, count: length})'

# Expected: mix of spot and on-demand nodes
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Policy update returns 400 | Invalid policy JSON | Validate with `jq` before sending |
| Nodes not scaling | Policy not enabled | Verify `.enabled: true` in policy |
| Spot instances not used | Provider not configured | Add cloud provider to `spotInstances.clouds` |
| Evictor too aggressive | Low delay threshold | Increase `emptyNodes.delaySeconds` |
| Cluster limit hit | `maxCores` too low | Increase `clusterLimits.cpu.maxCores` |

## Resources

- [Autoscaler Policies](https://docs.cast.ai/docs/autoscaler-settings)
- [Node Configuration](https://docs.cast.ai/docs/node-configuration)
- [Terraform Node Templates](https://registry.terraform.io/providers/castai/castai/latest/docs/resources/node_template)

## Next Steps

For workload-level autoscaling, see `castai-core-workflow-b`.
