---
name: castai-hello-world
description: 'Query CAST AI cluster savings report and node inventory.

  Use when verifying CAST AI connectivity, viewing cluster cost savings,

  or listing managed nodes after onboarding.

  Trigger with phrases like "cast ai hello world", "cast ai savings",

  "cast ai cluster status", "test cast ai connection".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(kubectl:*)
version: 1.4.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- kubernetes
- cost-optimization
- castai
compatibility: Designed for Claude Code
---
# CAST AI Hello World

## Overview

First API calls against the CAST AI REST API: list connected clusters, retrieve the savings report, and inspect node inventory. All examples use `curl` with the `X-API-Key` header -- no SDK required.

## Prerequisites

- Completed `castai-install-auth` setup
- `CASTAI_API_KEY` environment variable set
- At least one cluster connected to CAST AI

## Instructions

### Step 1: List Connected Clusters

```bash
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  https://api.cast.ai/v1/kubernetes/external-clusters \
  | jq '.items[] | {id, name, status, providerType}'
```

Expected output:

```json
{
  "id": "abc123-def456",
  "name": "production-eks",
  "status": "ready",
  "providerType": "eks"
}
```

### Step 2: Get Cluster Savings Report

```bash
export CASTAI_CLUSTER_ID="your-cluster-id"

# Current month savings
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/savings" \
  | jq '{
    monthlySavings: .monthlySavings,
    savingsPercentage: .savingsPercentage,
    currentCost: .currentMonthlyCost,
    optimizedCost: .optimizedMonthlyCost
  }'
```

### Step 3: List Cluster Nodes

```bash
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/external-clusters/${CASTAI_CLUSTER_ID}/nodes" \
  | jq '.items[] | {
    name: .name,
    instanceType: .instanceType,
    lifecycle: .lifecycle,
    cpu: .allocatableCpu,
    memory: .allocatableMemory,
    zone: .zone
  }'
```

### Step 4: Check Autoscaler Policies

```bash
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  | jq '{
    enabled: .enabled,
    unschedulablePods: .unschedulablePods.enabled,
    nodeDownscaler: .nodeDownscaler.enabled,
    spotInstances: .spotInstances.enabled
  }'
```

## Output

The first read-only run returns a list of connected clusters, a monthly-savings
snapshot, node inventory, and autoscaler-policy state. Save only the fields
needed for the onboarding record; cluster names, account metadata, and spend
data should be treated as environment-sensitive operational information.

## Examples

Run the cluster-list command against a non-production key, select one expected
cluster ID, then request its node inventory and policy state. A successful
onboarding result shows the expected cluster name and an online agent; a 401 or
offline agent is a stop condition, not a reason to retry with a broader key.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Bad API key | Regenerate at console.cast.ai |
| `404 Not Found` | Wrong cluster ID | List clusters first to get correct ID |
| Empty `items` array | No clusters connected | Run `castai-install-auth` to onboard |
| `agentStatus: offline` | Agent not running | Check `kubectl get pods -n castai-agent` |

## Resources

- [CAST AI API Reference](https://api.cast.ai/v1/spec/openapi.json)
- [CAST AI Console](https://console.cast.ai)
- [Savings Report Docs](https://docs.cast.ai/docs/getting-started)

## Next Steps

Proceed to `castai-local-dev-loop` to set up a development workflow.
