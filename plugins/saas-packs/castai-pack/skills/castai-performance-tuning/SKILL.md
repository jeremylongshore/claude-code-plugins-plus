---
name: castai-performance-tuning
description: |
  Optimize CAST AI autoscaler performance, node provisioning speed, and API efficiency.
  Use when nodes take too long to provision, autoscaler is not reacting fast enough,
  or optimizing API call patterns for multi-cluster dashboards.
  Trigger with phrases like "cast ai performance", "cast ai slow",
  "cast ai node provisioning", "cast ai autoscaler speed".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Performance Tuning

## Overview

Tune CAST AI for faster node provisioning, more responsive autoscaling, and efficient API usage. Covers headroom configuration, instance family selection, and API caching for multi-cluster dashboards.

## Prerequisites

- CAST AI Phase 2 (full automation) enabled
- Understanding of workload scheduling patterns
- Access to autoscaler policy configuration

## Instructions

### Step 1: Optimize Node Provisioning Speed

```bash
# Configure headroom for proactive scaling (avoids waiting for pending pods)
curl -X PUT -H "X-API-Key: ${CASTAI_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  -d '{
    "enabled": true,
    "unschedulablePods": {
      "enabled": true,
      "headroom": {
        "enabled": true,
        "cpuPercentage": 15,
        "memoryPercentage": 15
      }
    }
  }'
```

Headroom pre-provisions spare capacity so pods schedule immediately instead of waiting 2-5 minutes for new nodes.

### Step 2: Instance Family Optimization

```hcl
# Terraform: Prefer instance families with fast launch times
resource "castai_node_template" "fast_launch" {
  cluster_id = castai_eks_cluster.this.id
  name       = "fast-launch-workers"

  constraints {
    spot                  = true
    use_spot_fallbacks    = true
    fallback_restore_rate_seconds = 300

    # Newer instance types launch faster and have better availability
    instance_families {
      include = ["m6i", "m7i", "c6i", "c7i", "r6i", "r7i"]
    }

    # Enable spot diversity for faster provisioning
    spot_diversity_price_increase_limit_percent = 25

    architectures = ["amd64"]
  }
}
```

### Step 3: Evictor Tuning for Faster Consolidation

```bash
# Reduce empty node delay for dev/staging (faster downscale)
helm upgrade castai-evictor castai-helm/castai-evictor \
  -n castai-agent \
  --reuse-values \
  --set evictor.aggressiveMode=true \
  --set evictor.cycleInterval=120

# For production, use non-aggressive with longer intervals
# --set evictor.aggressiveMode=false
# --set evictor.cycleInterval=600
```

### Step 4: API Performance for Multi-Cluster Dashboards

```typescript
import { LRUCache } from "lru-cache";

const cache = new LRUCache<string, unknown>({ max: 100, ttl: 60_000 });

interface ClusterSummary {
  id: string;
  name: string;
  savings: number;
  savingsPercent: number;
  nodeCount: number;
  spotPercent: number;
}

async function getClusterSummary(clusterId: string): Promise<ClusterSummary> {
  const cacheKey = `summary:${clusterId}`;
  const cached = cache.get(cacheKey) as ClusterSummary | undefined;
  if (cached) return cached;

  const [cluster, savings, nodes] = await Promise.all([
    castaiGet(`/v1/kubernetes/external-clusters/${clusterId}`),
    castaiGet(`/v1/kubernetes/clusters/${clusterId}/savings`),
    castaiGet(`/v1/kubernetes/external-clusters/${clusterId}/nodes`),
  ]);

  const spotNodes = nodes.items.filter(
    (n: { lifecycle: string }) => n.lifecycle === "spot"
  ).length;

  const summary: ClusterSummary = {
    id: clusterId,
    name: cluster.name,
    savings: savings.monthlySavings,
    savingsPercent: savings.savingsPercentage,
    nodeCount: nodes.items.length,
    spotPercent: nodes.items.length > 0
      ? (spotNodes / nodes.items.length) * 100
      : 0,
  };

  cache.set(cacheKey, summary);
  return summary;
}

// Aggregate across all clusters
async function getDashboardData(
  clusterIds: string[]
): Promise<ClusterSummary[]> {
  return Promise.all(clusterIds.map(getClusterSummary));
}
```

### Step 5: Workload Autoscaler Tuning

```yaml
# Faster resource adjustment with shorter cooldown
# (use with caution in production)
metadata:
  annotations:
    autoscaling.cast.ai/cpu-headroom: "10"     # Lower headroom = tighter fit
    autoscaling.cast.ai/memory-headroom: "15"
    autoscaling.cast.ai/apply-type: "immediate" # Apply without waiting
```

## Performance Benchmarks

| Metric | Default | Tuned |
|--------|---------|-------|
| Node provision time | 3-5 min | 1-3 min (with headroom) |
| Empty node removal | 5 min | 2 min (aggressive evictor) |
| Workload resize | 5 min cooldown | Immediate |
| API response (cached) | 200ms | <5ms |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Headroom over-provisioning | Percentage too high | Reduce to 5-10% |
| Aggressive evictor causing disruptions | PDB not set | Add PodDisruptionBudgets |
| Cache stale data | TTL too long | Reduce cache TTL to 30s |
| Instance type unavailable | Too narrow constraints | Add more instance families |

## Resources

- [Autoscaler Settings](https://docs.cast.ai/docs/autoscaler-settings)
- [Workload Autoscaler Annotations](https://docs.cast.ai/docs/workload-autoscaler-annotations-reference)
- [Node Configuration](https://docs.cast.ai/docs/node-configuration)

## Next Steps

For cost optimization strategies, see `castai-cost-tuning`.
