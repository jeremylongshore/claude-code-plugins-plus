---
name: adk-infra-expert
description: |
  Terraform infrastructure specialist for Vertex AI ADK Agent Engine production deployments.
  Provisions Agent Engine runtime, Code Execution Sandbox, Memory Bank, VPC-SC, IAM, and secure multi-agent infrastructure.
  Triggers: "deploy adk terraform", "agent engine infrastructure", "adk production deployment", "vpc-sc agent engine"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## What This Skill Does

Expert in provisioning production Vertex AI ADK infrastructure with Agent Engine, Code Execution Sandbox (14-day state), Memory Bank, VPC Service Controls, and enterprise security.

## When This Skill Activates

Triggers: "adk terraform deployment", "agent engine infrastructure", "provision adk agent", "vertex ai agent terraform", "code execution sandbox terraform"

## Core Terraform Modules

### Agent Engine Deployment

```hcl
resource "google_vertex_ai_agent_runtime" "adk_agent" {
  project  = var.project_id
  location = var.region

  display_name = "adk-production-agent"

  agent_config {
    model         = "gemini-2.5-flash"

    code_execution {
      enabled           = true
      state_ttl_days    = 14
      sandbox_type      = "SECURE_ISOLATED"
    }

    memory_bank {
      enabled = true
    }

    tools = [
      {
        code_execution = {}
      },
      {
        memory_bank = {}
      }
    ]
  }

  vpc_config {
    vpc_network    = google_compute_network.agent_vpc.id
    private_service_connect {
      enabled = true
    }
  }
}
```

### VPC Service Controls

```hcl
resource "google_access_context_manager_service_perimeter" "adk_perimeter" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/adk_perimeter"
  title  = "ADK Agent Engine Perimeter"

  status {
    restricted_services = [
      "aiplatform.googleapis.com",
      "run.googleapis.com"
    ]

    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = [
        "aiplatform.googleapis.com"
      ]
    }
  }
}
```

### IAM for Native Agent Identity

```hcl
resource "google_project_iam_member" "agent_identity" {
  project = var.project_id
  role    = "roles/aiplatform.agentUser"
  member  = "serviceAccount:${google_service_account.adk_agent.email}"
}

resource "google_service_account" "adk_agent" {
  account_id   = "adk-agent-sa"
  display_name = "ADK Agent Service Account"
}

# Least privilege for Code Execution
resource "google_project_iam_member" "code_exec_permissions" {
  for_each = toset([
    "roles/compute.viewer",
    "roles/container.viewer",
    "roles/run.viewer"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.adk_agent.email}"
}
```

## Tool Permissions

Read, Write, Edit, Grep, Glob, Bash - Enterprise infrastructure provisioning

## References

- Agent Engine: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- VPC-SC: https://cloud.google.com/vpc-service-controls/docs
