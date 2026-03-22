---
name: castai-upgrade-migration
description: |
  Upgrade CAST AI Helm charts, Terraform provider, and agent components.
  Use when upgrading CAST AI versions, checking for breaking changes,
  or migrating between CAST AI agent releases.
  Trigger with phrases like "upgrade cast ai", "update cast ai agent",
  "cast ai helm upgrade", "cast ai terraform upgrade".
allowed-tools: Read, Write, Edit, Bash(helm:*), Bash(terraform:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Upgrade & Migration

## Overview

Upgrade CAST AI components: Helm charts for the agent/controller/evictor, Terraform provider version, and workload autoscaler. Includes rollback procedures for each component.

## Prerequisites

- Current CAST AI components installed
- Staging cluster for testing upgrades first
- Helm and kubectl access
- Change management approval for production

## Instructions

### Step 1: Check Current Versions

```bash
# Helm chart versions
helm list -n castai-agent -o json | jq '.[] | {name: .name, chart: .chart, appVersion: .app_version}'

# Available versions
helm repo update
helm search repo castai-helm --versions | head -20

# Terraform provider version
grep "castai/castai" .terraform.lock.hcl
terraform providers
```

### Step 2: Review Changelog

```bash
# Check CAST AI changelog for breaking changes
# https://docs.cast.ai/changelog/

# Check Terraform provider releases
# https://github.com/castai/terraform-provider-castai/releases
```

### Step 3: Upgrade on Staging First

```bash
# Upgrade agent
helm upgrade castai-agent castai-helm/castai-agent \
  -n castai-agent --reuse-values

# Upgrade cluster controller
helm upgrade cluster-controller castai-helm/castai-cluster-controller \
  -n castai-agent --reuse-values

# Upgrade evictor
helm upgrade castai-evictor castai-helm/castai-evictor \
  -n castai-agent --reuse-values

# Upgrade workload autoscaler
helm upgrade castai-workload-autoscaler castai-helm/castai-workload-autoscaler \
  -n castai-agent --reuse-values

# Verify all pods restarted cleanly
kubectl get pods -n castai-agent -w
```

### Step 4: Upgrade Terraform Provider

```hcl
# Update version constraint in versions.tf
terraform {
  required_providers {
    castai = {
      source  = "castai/castai"
      version = "~> 7.5"  # Update to target version
    }
  }
}
```

```bash
# Upgrade provider
terraform init -upgrade
terraform plan -var-file=environments/staging.tfvars

# Review plan carefully for resource recreation
# Apply if plan looks safe
terraform apply -var-file=environments/staging.tfvars
```

### Step 5: Validate After Upgrade

```bash
# Verify agent is online
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/external-clusters/${CASTAI_CLUSTER_ID}" \
  | jq '{agentStatus, name}'

# Verify autoscaler policies still applied
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  | jq '.enabled'

# Check for errors in new agent version
kubectl logs -n castai-agent deployment/castai-agent --tail=50 | grep -i error
```

### Rollback Procedure

```bash
# Helm rollback to previous release
helm rollback castai-agent -n castai-agent
helm rollback cluster-controller -n castai-agent

# Terraform rollback
terraform plan -var-file=environments/staging.tfvars  # Review
# If needed, pin previous provider version:
# version = "= 7.4.2"
terraform init -upgrade
terraform apply -var-file=environments/staging.tfvars
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent CrashLoop after upgrade | Breaking chart change | `helm rollback` to previous |
| Terraform plan shows destroy | Major provider version jump | Pin intermediate version |
| Policies reset after upgrade | Chart default values changed | Pass `--reuse-values` |
| Spot handler incompatible | Node format changed | Upgrade all components together |

## Resources

- [CAST AI Changelog](https://docs.cast.ai/changelog/)
- [Terraform Provider Releases](https://github.com/castai/terraform-provider-castai/releases)
- [Helm Charts](https://docs.cast.ai/docs/helm-charts)

## Next Steps

For CI pipeline integration, see `castai-ci-integration`.
