---
name: castai-reference-architecture
description: |
  CAST AI reference architecture for multi-cluster Kubernetes cost optimization.
  Use when designing CAST AI deployment across environments, planning
  Terraform module structure, or establishing team standards.
  Trigger with phrases like "cast ai architecture", "cast ai best practices",
  "cast ai multi-cluster", "cast ai terraform structure".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Reference Architecture

## Overview

Production-grade architecture for managing CAST AI across multiple Kubernetes clusters. Covers Terraform module layout, per-environment policies, API key management, and observability integration.

## Prerequisites

- Multiple Kubernetes clusters (dev, staging, production)
- Terraform for infrastructure management
- Centralized secrets management
- Monitoring stack (Prometheus, Grafana, or Datadog)

## Terraform Module Structure

```
infrastructure/
├── modules/
│   └── castai-cluster/
│       ├── main.tf              # CAST AI provider resources
│       ├── variables.tf         # Cluster-specific inputs
│       ├── outputs.tf           # Cluster ID, savings metrics
│       ├── policies.tf          # Autoscaler policy configuration
│       ├── node-templates.tf    # Node template definitions
│       └── security.tf          # Kvisor, RBAC
├── environments/
│   ├── dev/
│   │   ├── main.tf              # Dev cluster onboarding
│   │   ├── terraform.tfvars     # Dev-specific values
│   │   └── backend.tf           # State storage
│   ├── staging/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       ├── terraform.tfvars
│       └── backend.tf
└── shared/
    ├── api-keys.tf              # Key management
    └── monitoring.tf            # Alerting rules
```

## Reusable Module

```hcl
# modules/castai-cluster/main.tf
variable "cluster_name" { type = string }
variable "cluster_id" { type = string }
variable "environment" { type = string }
variable "api_token" { type = string; sensitive = true }
variable "provider_type" { type = string }  # eks, gke, aks
variable "max_cpu_cores" { type = number; default = 100 }
variable "spot_enabled" { type = bool; default = true }
variable "hibernation_enabled" { type = bool; default = false }
variable "evictor_aggressive" { type = bool; default = false }

resource "castai_autoscaler" "this" {
  cluster_id = var.cluster_id

  autoscaler_policies_json = jsonencode({
    enabled = true
    unschedulablePods = {
      enabled = true
      headroom = {
        enabled          = true
        cpuPercentage    = var.environment == "prod" ? 15 : 5
        memoryPercentage = var.environment == "prod" ? 15 : 5
      }
    }
    nodeDownscaler = {
      enabled = true
      emptyNodes = {
        enabled      = true
        delaySeconds = var.environment == "prod" ? 300 : 60
      }
    }
    spotInstances = {
      enabled              = var.spot_enabled
      spotDiversityEnabled = true
    }
    clusterLimits = {
      enabled = true
      cpu     = { minCores = 2, maxCores = var.max_cpu_cores }
    }
  })
}

resource "castai_node_template" "default_spot" {
  cluster_id = var.cluster_id
  name       = "${var.environment}-spot-workers"
  is_enabled = var.spot_enabled

  constraints {
    spot               = true
    use_spot_fallbacks = true
    architectures      = ["amd64"]
  }
}
```

## Per-Environment Configuration

```hcl
# environments/dev/terraform.tfvars
environment          = "dev"
max_cpu_cores        = 16
spot_enabled         = true
hibernation_enabled  = true   # Hibernate off-hours
evictor_aggressive   = true   # Fast consolidation OK

# environments/prod/terraform.tfvars
environment          = "prod"
max_cpu_cores        = 200
spot_enabled         = true
hibernation_enabled  = false  # Never hibernate production
evictor_aggressive   = false  # Conservative eviction
```

## Architecture Diagram

```
                    ┌─────────────────────┐
                    │   CAST AI Console    │
                    │  console.cast.ai     │
                    └──────────┬──────────┘
                               │ API
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼──────┐ ┌──────▼────────┐ ┌─────▼───────┐
     │   Dev (EKS)   │ │ Staging (GKE) │ │  Prod (EKS) │
     │  Spot: 100%   │ │  Spot: 80%    │ │  Spot: 60%  │
     │  Hibernate: Y │ │  Hibernate: N │ │  Hibernate:N│
     │  Max: 16 CPU  │ │  Max: 50 CPU  │ │  Max:200CPU │
     └───────────────┘ └───────────────┘ └─────────────┘
              │                │                │
     ┌────────▼──────┐ ┌──────▼────────┐ ┌─────▼───────┐
     │  Terraform    │ │  Terraform    │ │  Terraform  │
     │  dev/         │ │  staging/     │ │  prod/      │
     └───────────────┘ └───────────────┘ └─────────────┘
```

## Monitoring Integration

```yaml
# Prometheus alert rules for CAST AI
groups:
  - name: castai
    rules:
      - alert: CastAIAgentDown
        expr: kube_pod_status_ready{namespace="castai-agent", pod=~"castai-agent.*"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "CAST AI agent is down on {{ $labels.cluster }}"

      - alert: CastAIHighSpotInterruptions
        expr: increase(castai_spot_interruptions_total[1h]) > 5
        labels:
          severity: warning
        annotations:
          summary: "High spot interruption rate on {{ $labels.cluster }}"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| State drift between envs | Manual console changes | Enforce Terraform-only policy |
| Module version mismatch | Independent env upgrades | Pin module versions |
| Cross-env key leak | Shared tfvars | Separate state and secrets per env |
| Monitoring gaps | Missing scrape config | Add castai-agent namespace to Prometheus |

## Resources

- [CAST AI Terraform Provider](https://registry.terraform.io/providers/castai/castai/latest/docs)
- [CAST AI Architecture Docs](https://docs.cast.ai/docs/getting-started)
- [Terraform Module Best Practices](https://developer.hashicorp.com/terraform/language/modules/develop)

## Next Steps

This completes the CAST AI skill pack. Start with `castai-install-auth` for new clusters.
