---
name: castai-cost-tuning
description: |
  Maximize Kubernetes cost savings with CAST AI spot strategies and right-sizing.
  Use when analyzing cloud spend, optimizing spot-to-on-demand ratios,
  or configuring CAST AI for maximum savings.
  Trigger with phrases like "cast ai cost", "cast ai savings",
  "cast ai spot strategy", "reduce kubernetes cost", "cast ai budget".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Cost Tuning

## Overview

Maximize Kubernetes cost savings through CAST AI: spot instance strategies, workload right-sizing, cluster hibernation, and savings tracking. Typical savings: 50-70% on cloud compute costs.

## Prerequisites

- CAST AI Phase 2 enabled with full automation
- Savings report available (requires 24h+ of data)
- Understanding of workload criticality tiers

## Instructions

### Step 1: Analyze Current Savings

```bash
# Get savings breakdown
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/savings" \
  | jq '{
    currentMonthlyCost: .currentMonthlyCost,
    optimizedMonthlyCost: .optimizedMonthlyCost,
    monthlySavings: .monthlySavings,
    savingsPercentage: .savingsPercentage,
    spotSavings: .spotSavings,
    rightSizingSavings: .rightSizingSavings
  }'
```

### Step 2: Maximize Spot Usage

```bash
# Enable aggressive spot with diversity and fallbacks
curl -X PUT -H "X-API-Key: ${CASTAI_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  -d '{
    "enabled": true,
    "spotInstances": {
      "enabled": true,
      "clouds": ["aws"],
      "spotDiversityEnabled": true,
      "spotDiversityPriceIncreaseLimitPercent": 20,
      "spotBackups": {
        "enabled": true,
        "spotBackupRestoreRateSeconds": 600
      }
    }
  }'
```

**Spot allocation strategy by workload tier:**

| Workload Type | Spot % | Rationale |
|---------------|--------|-----------|
| Batch jobs, CI runners | 100% spot | Interruptible, restartable |
| Stateless APIs (behind LB) | 80% spot | Can handle brief interruptions |
| Stateful services, databases | 0% spot | Use on-demand or reserved |
| ML training | 80-100% spot | Checkpointing handles interrupts |

### Step 3: Workload Right-Sizing

```bash
# Get resource waste analysis
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/workload-autoscaling/clusters/${CASTAI_CLUSTER_ID}/workloads" \
  | jq '[.items[] | select(.estimatedSavingsPercent > 20) | {
    name: .workloadName,
    namespace: .namespace,
    wastedCpu: (.currentCpuRequest - .recommendedCpuRequest),
    wastedMemory: (.currentMemoryRequest - .recommendedMemoryRequest),
    savingsPercent: .estimatedSavingsPercent
  }] | sort_by(-.savingsPercent) | .[0:10]'
```

### Step 4: Cluster Hibernation (Dev/Staging)

```bash
# Hibernate non-production clusters during off-hours
# Scales nodes to zero, resume on demand

# Enable hibernation
curl -X POST -H "X-API-Key: ${CASTAI_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/hibernate" \
  -d '{
    "schedule": {
      "enabled": true,
      "hibernateAt": "20:00",
      "wakeUpAt": "08:00",
      "timezone": "America/New_York",
      "weekdaysOnly": true
    }
  }'
```

### Step 5: Cost Tracking Dashboard

```typescript
interface CostReport {
  cluster: string;
  period: string;
  currentCost: number;
  optimizedCost: number;
  savings: number;
  spotPercent: number;
}

async function generateMonthlyCostReport(
  clusterIds: string[]
): Promise<CostReport[]> {
  const reports: CostReport[] = [];

  for (const clusterId of clusterIds) {
    const [cluster, savings, nodes] = await Promise.all([
      castaiGet(`/v1/kubernetes/external-clusters/${clusterId}`),
      castaiGet(`/v1/kubernetes/clusters/${clusterId}/savings`),
      castaiGet(`/v1/kubernetes/external-clusters/${clusterId}/nodes`),
    ]);

    const spotNodes = nodes.items.filter(
      (n: { lifecycle: string }) => n.lifecycle === "spot"
    ).length;

    reports.push({
      cluster: cluster.name,
      period: new Date().toISOString().slice(0, 7),
      currentCost: savings.currentMonthlyCost,
      optimizedCost: savings.optimizedMonthlyCost,
      savings: savings.monthlySavings,
      spotPercent:
        nodes.items.length > 0
          ? (spotNodes / nodes.items.length) * 100
          : 0,
    });
  }

  return reports;
}
```

## Cost Optimization Checklist

- [ ] Spot instances enabled with diversity
- [ ] Workload autoscaler right-sizing resources
- [ ] Dev/staging clusters hibernated off-hours
- [ ] Empty node downscaler enabled
- [ ] Instance families include latest generation (cheaper)
- [ ] Reserved/savings plan for baseline on-demand nodes
- [ ] Weekly savings report review

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Savings lower than expected | Too many on-demand constraints | Relax node template constraints |
| Spot interruptions too frequent | Single instance type | Enable spot diversity |
| Hibernation not triggering | Schedule timezone wrong | Use IANA timezone format |
| Right-sizing too aggressive | Low headroom | Increase memory headroom to 20% |

## Resources

- [CAST AI Savings Report](https://docs.cast.ai/docs/getting-started)
- [Spot Instance Best Practices](https://docs.cast.ai/docs/autoscaler-settings)
- [Cluster Hibernation](https://docs.cast.ai/docs/autoscaling-cluster-hibernation)

## Next Steps

For architecture patterns, see `castai-reference-architecture`.
