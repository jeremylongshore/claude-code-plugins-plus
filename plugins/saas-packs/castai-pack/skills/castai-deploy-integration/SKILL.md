---
name: castai-deploy-integration
description: |
  Deploy CAST AI across multi-cloud Kubernetes clusters with Terraform modules.
  Use when onboarding EKS, GKE, or AKS clusters to CAST AI using
  infrastructure-as-code patterns.
  Trigger with phrases like "deploy cast ai", "cast ai eks",
  "cast ai gke", "cast ai aks", "cast ai terraform module".
allowed-tools: Read, Write, Edit, Bash(terraform:*), Bash(helm:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Deploy Integration

## Overview

Deploy CAST AI to EKS, GKE, and AKS clusters using official Terraform modules. Each cloud provider has a dedicated CAST AI module that handles IAM roles, node configuration, and autoscaler setup.

## Prerequisites

- Terraform 1.0+
- CAST AI Full Access API key
- Cloud provider credentials configured
- Existing Kubernetes cluster

## Instructions

### EKS Deployment

```hcl
# main.tf -- EKS cluster onboarding
module "castai_eks" {
  source  = "castai/eks-cluster/castai"
  version = "~> 3.0"

  api_token           = var.castai_api_token
  aws_account_id      = data.aws_caller_identity.current.account_id
  aws_cluster_region  = var.region
  aws_cluster_name    = var.cluster_name

  # IAM role for CAST AI to manage nodes
  aws_instance_profile_arn = aws_iam_instance_profile.castai.arn

  # Autoscaler configuration
  autoscaler_policies_json = jsonencode({
    enabled = true
    unschedulablePods = { enabled = true }
    nodeDownscaler = {
      enabled = true
      emptyNodes = { enabled = true, delaySeconds = 300 }
    }
    spotInstances = {
      enabled = true
      spotDiversityEnabled = true
    }
    clusterLimits = {
      enabled = true
      cpu = { minCores = 4, maxCores = 200 }
    }
  })

  # Node templates
  default_node_configuration = module.castai_eks.castai_node_configurations["default"]
}
```

### GKE Deployment

```hcl
module "castai_gke" {
  source  = "castai/gke-cluster/castai"
  version = "~> 2.0"

  api_token            = var.castai_api_token
  project_id           = var.gcp_project_id
  gke_cluster_name     = var.cluster_name
  gke_cluster_location = var.region

  gke_credentials = base64decode(
    google_container_cluster.this.master_auth[0].cluster_ca_certificate
  )

  autoscaler_policies_json = jsonencode({
    enabled = true
    unschedulablePods = { enabled = true }
    nodeDownscaler = {
      enabled = true
      emptyNodes = { enabled = true, delaySeconds = 300 }
    }
  })
}
```

### AKS Deployment

```hcl
module "castai_aks" {
  source  = "castai/aks/castai"
  version = "~> 1.0"

  api_token              = var.castai_api_token
  aks_cluster_name       = var.cluster_name
  aks_cluster_region     = var.region
  node_resource_group    = azurerm_kubernetes_cluster.this.node_resource_group
  azure_subscription_id  = data.azurerm_subscription.current.subscription_id
  azure_tenant_id        = data.azurerm_client_config.current.tenant_id

  autoscaler_policies_json = jsonencode({
    enabled = true
    unschedulablePods = { enabled = true }
    spotInstances = { enabled = true }
  })
}
```

### Multi-Cluster Deployment Pattern

```hcl
# Deploy CAST AI across all clusters with a for_each
variable "clusters" {
  type = map(object({
    name     = string
    provider = string  # eks, gke, aks
    region   = string
    max_cpu  = number
  }))
}

# Then reference the appropriate module per provider
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| IAM role error | Missing permissions | Check CAST AI IAM docs for required policies |
| Module version conflict | Terraform lock | Run `terraform init -upgrade` |
| Cluster not appearing | Wrong credentials | Verify cloud provider auth |
| Policies not applying | JSON encoding error | Validate `jsonencode()` output |

## Resources

- [EKS Module](https://registry.terraform.io/modules/castai/eks-cluster/castai/latest)
- [GKE Module](https://registry.terraform.io/modules/castai/gke-cluster/castai/latest)
- [AKS Module](https://registry.terraform.io/modules/castai/aks/castai/latest)
- [CAST AI Terraform Provider](https://registry.terraform.io/providers/castai/castai/latest/docs)

## Next Steps

For webhook-based automation, see `castai-webhooks-events`.
