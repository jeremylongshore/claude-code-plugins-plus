---
name: castai-install-auth
description: |
  Install and configure CAST AI agent on a Kubernetes cluster with API key authentication.
  Use when onboarding a cluster to CAST AI, setting up Helm charts,
  or configuring Terraform provider authentication.
  Trigger with phrases like "install cast ai", "connect cluster to cast ai",
  "cast ai setup", "cast ai api key", "cast ai helm install".
allowed-tools: Read, Write, Edit, Bash(helm:*), Bash(kubectl:*), Bash(terraform:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Install & Auth

## Overview

Connect a Kubernetes cluster (EKS, GKE, AKS, or KOPS) to CAST AI for cost optimization, autoscaling, and security scanning. Covers API key generation, Helm chart installation of the CAST AI agent, and Terraform provider setup.

## Prerequisites

- A running Kubernetes cluster (EKS, GKE, AKS, or KOPS)
- `kubectl` configured with cluster admin access
- `helm` v3 installed
- A CAST AI account at https://console.cast.ai

## Instructions

### Step 1: Generate an API Key

Log in to https://console.cast.ai and navigate to **API** > **API Access Keys**. Create a Full Access key for Terraform-managed clusters, or Read-Only for monitoring-only.

```bash
export CASTAI_API_KEY="your-api-key-here"

# Verify the key works
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  https://api.cast.ai/v1/kubernetes/external-clusters | jq '.items | length'
```

### Step 2: Install the CAST AI Agent via Helm

```bash
# Add the CAST AI Helm repository
helm repo add castai-helm https://castai.github.io/helm-charts
helm repo update

# Install the read-only monitoring agent (Phase 1)
helm upgrade --install castai-agent castai-helm/castai-agent \
  -n castai-agent --create-namespace \
  --set apiKey="${CASTAI_API_KEY}" \
  --set provider="eks"  # eks | gke | aks

kubectl get pods -n castai-agent
```

### Step 3: Enable Full Automation (Phase 2)

```bash
export CASTAI_CLUSTER_ID="your-cluster-id"

# Cluster controller -- manages node lifecycle
helm upgrade --install cluster-controller castai-helm/castai-cluster-controller \
  -n castai-agent \
  --set castai.apiKey="${CASTAI_API_KEY}" \
  --set castai.clusterID="${CASTAI_CLUSTER_ID}"

# Evictor -- consolidates underutilized nodes
helm upgrade --install castai-evictor castai-helm/castai-evictor \
  -n castai-agent \
  --set castai.apiKey="${CASTAI_API_KEY}" \
  --set castai.clusterID="${CASTAI_CLUSTER_ID}"

# Spot handler -- graceful spot instance interruption
helm upgrade --install castai-spot-handler castai-helm/castai-spot-handler \
  -n castai-agent \
  --set castai.provider="eks" \
  --set castai.clusterID="${CASTAI_CLUSTER_ID}"
```

### Step 4: Terraform Provider (Alternative)

```hcl
terraform {
  required_providers {
    castai = {
      source  = "castai/castai"
      version = "~> 7.0"
    }
  }
}

provider "castai" {
  api_token = var.castai_api_token
}

variable "castai_api_token" {
  type      = string
  sensitive = true
}

resource "castai_eks_cluster" "this" {
  account_id = data.aws_caller_identity.current.account_id
  region     = var.aws_region
  name       = var.cluster_name
}
```

### Step 5: Verify Connection

```bash
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/external-clusters/${CASTAI_CLUSTER_ID}" \
  | jq '{name: .name, status: .status, agentStatus: .agentStatus}'
# => { "name": "my-cluster", "status": "ready", "agentStatus": "online" }
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired API key | Regenerate at console.cast.ai > API |
| `403 Forbidden` | Key lacks permissions | Use Full Access key for write operations |
| Agent `CrashLoopBackOff` | RBAC misconfiguration | Check `kubectl logs -n castai-agent` |
| `cluster not found` | Wrong cluster ID | Verify ID at console.cast.ai > Clusters |
| Helm chart not found | Repo not added | Run `helm repo add castai-helm ...` |

## Resources

- [CAST AI Getting Started](https://docs.cast.ai/docs/getting-started)
- [CAST AI Helm Charts](https://docs.cast.ai/docs/helm-charts)
- [Terraform Provider](https://registry.terraform.io/providers/castai/castai/latest/docs)
- [API Reference](https://api.cast.ai/v1/spec/openapi.json)

## Next Steps

Proceed to `castai-hello-world` to query cluster savings and node status.
