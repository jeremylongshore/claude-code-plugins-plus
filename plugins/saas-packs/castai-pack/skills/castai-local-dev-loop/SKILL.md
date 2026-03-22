---
name: castai-local-dev-loop
description: |
  Set up a local Kubernetes development loop with CAST AI cost monitoring.
  Use when building cost-aware deployments, testing autoscaler policies,
  or iterating on Terraform CAST AI configurations locally.
  Trigger with phrases like "cast ai dev setup", "cast ai local testing",
  "develop with cast ai", "cast ai terraform dev".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(helm:*), Bash(terraform:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Local Dev Loop

## Overview

Fast iteration workflow for CAST AI integrations: test autoscaler policies in a dev cluster, validate Terraform modules before applying to production, and use the CAST AI API to measure savings impact during development.

## Prerequisites

- Completed `castai-install-auth` setup
- A development Kubernetes cluster (kind, minikube, or cloud dev cluster)
- `kubectl`, `helm`, and optionally `terraform` installed

## Instructions

### Step 1: Project Structure

```
my-castai-infra/
├── terraform/
│   ├── environments/
│   │   ├── dev.tfvars
│   │   ├── staging.tfvars
│   │   └── prod.tfvars
│   ├── modules/
│   │   └── castai-cluster/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   └── main.tf
├── policies/
│   ├── dev-policy.json
│   └── prod-policy.json
├── scripts/
│   ├── check-savings.sh
│   └── validate-policies.sh
├── .env.dev            # Dev API key (git-ignored)
└── .env.example
```

### Step 2: Dev Cluster with Relaxed Policies

```bash
# Connect your dev cluster (read-only first)
helm upgrade --install castai-agent castai-helm/castai-agent \
  -n castai-agent --create-namespace \
  --set apiKey="${CASTAI_API_KEY_DEV}" \
  --set provider="eks"

# Apply development-safe autoscaler policy
curl -X PUT -H "X-API-Key: ${CASTAI_API_KEY_DEV}" \
  -H "Content-Type: application/json" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  -d '{
    "enabled": true,
    "unschedulablePods": { "enabled": true },
    "nodeDownscaler": {
      "enabled": true,
      "emptyNodes": { "enabled": true, "delaySeconds": 300 }
    },
    "clusterLimits": {
      "enabled": true,
      "cpu": { "minCores": 2, "maxCores": 16 }
    }
  }'
```

### Step 3: Quick Savings Check Script

```bash
#!/bin/bash
# scripts/check-savings.sh
set -euo pipefail

API_KEY="${CASTAI_API_KEY_DEV}"
CLUSTER_ID="${CASTAI_CLUSTER_ID}"

echo "=== CAST AI Dev Cluster Savings ==="
curl -s -H "X-API-Key: ${API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CLUSTER_ID}/savings" \
  | jq '{
    monthlySavings: .monthlySavings,
    percentage: .savingsPercentage,
    spotNodes: [.nodes[] | select(.lifecycle == "spot")] | length,
    totalNodes: [.nodes[]] | length
  }'
```

### Step 4: Terraform Plan-Apply Loop

```bash
# Plan with dev variables
cd terraform/
terraform plan -var-file=environments/dev.tfvars -out=plan.tfplan

# Apply and check CAST AI result
terraform apply plan.tfplan

# Verify policies took effect
curl -s -H "X-API-Key: ${CASTAI_API_KEY_DEV}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  | jq .
```

### Step 5: Watch Node Changes in Real Time

```bash
# Terminal 1: Watch CAST AI node operations
watch -n 15 'curl -s -H "X-API-Key: ${CASTAI_API_KEY_DEV}" \
  "https://api.cast.ai/v1/kubernetes/external-clusters/${CASTAI_CLUSTER_ID}/nodes" \
  | jq "[.items[] | {name, instanceType, lifecycle, age: .createdAt}] | length"'

# Terminal 2: Watch kubectl node status
kubectl get nodes -w
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Dev cluster not found | Wrong cluster ID | List clusters with API first |
| Policy rejected | Invalid JSON | Validate with `jq . < policy.json` |
| Terraform drift | Manual console changes | Run `terraform refresh` |
| Agent offline after restart | Helm release stale | `helm upgrade --install` again |

## Resources

- [CAST AI Terraform Provider](https://registry.terraform.io/providers/castai/castai/latest/docs)
- [Autoscaler Policies](https://docs.cast.ai/docs/autoscaler-settings)
- [Node Configuration](https://docs.cast.ai/docs/node-configuration)

## Next Steps

See `castai-sdk-patterns` for reusable API wrapper patterns.
