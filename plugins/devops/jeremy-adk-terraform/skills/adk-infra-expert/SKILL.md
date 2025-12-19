---
description: Use when provisioning Vertex AI ADK infrastructure with Terraform. Trigger with phrases like "deploy ADK terraform", "agent engine infrastructure", "provision ADK agent", "vertex AI agent terraform", or "code execution sandbox terraform". Provisions Agent Engine runtime, 14-day code execution sandbox, Memory Bank, VPC Service Controls, IAM roles, and secure multi-agent infrastructure.
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(terraform:*)
- Bash(gcloud:*)
name: adk-infra-expert
license: MIT
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

## Prerequisites

Before using this skill, ensure:
- Google Cloud project with billing enabled
- Terraform 1.0+ installed
- gcloud CLI authenticated with appropriate permissions
- Vertex AI API enabled in target project
- VPC Service Controls access policy created (for enterprise)
- Understanding of Agent Engine architecture and requirements

## Instructions

1. **Initialize Terraform**: Set up backend for remote state storage
2. **Configure Variables**: Define project_id, region, agent configuration
3. **Provision VPC**: Create network infrastructure with Private Service Connect
4. **Set Up IAM**: Create service accounts with least privilege roles
5. **Deploy Agent Engine**: Configure runtime with code execution and memory bank
6. **Enable VPC-SC**: Apply service perimeter for data exfiltration protection
7. **Configure Monitoring**: Set up Cloud Monitoring dashboards and alerts
8. **Validate Deployment**: Test agent endpoint and verify all components

## Output

**Agent Engine Deployment:**
```hcl
# {baseDir}/terraform/main.tf
resource "google_vertex_ai_agent_runtime" "adk_agent" {
  project  = var.project_id
  location = var.region
  display_name = "adk-production-agent"

  agent_config {
    model = "gemini-2.5-flash"
    code_execution {
      enabled = true
      state_ttl_days = 14
      sandbox_type = "SECURE_ISOLATED"
    }
    memory_bank {
      enabled = true
    }
  }

  vpc_config {
    vpc_network = google_compute_network.agent_vpc.id
    private_service_connect {
      enabled = true
    }
  }
}
```

**VPC Service Controls:**
```hcl
resource "google_access_context_manager_service_perimeter" "adk_perimeter" {
  parent = "accessPolicies/${var.access_policy_id}"
  title  = "ADK Agent Engine Perimeter"

  status {
    restricted_services = [
      "aiplatform.googleapis.com",
      "run.googleapis.com"
    ]
  }
}
```

**IAM Configuration:**
```hcl
resource "google_service_account" "adk_agent" {
  account_id   = "adk-agent-sa"
  display_name = "ADK Agent Service Account"
}

resource "google_project_iam_member" "agent_identity" {
  project = var.project_id
  role    = "roles/aiplatform.agentUser"
  member  = "serviceAccount:${google_service_account.adk_agent.email}"
}
```

## Error Handling

**Terraform State Lock**
- Error: "Error acquiring the state lock"
- Solution: Use `terraform force-unlock <lock-id>` or wait for lock expiry

**API Not Enabled**
- Error: "Vertex AI API has not been used"
- Solution: Enable with `gcloud services enable aiplatform.googleapis.com`

**VPC-SC Configuration**
- Error: "Access denied by VPC Service Controls"
- Solution: Add project to service perimeter or adjust ingress/egress policies

**IAM Permission Denied**
- Error: "does not have required permission"
- Solution: Grant roles/owner temporarily to service account running Terraform

**Resource Already Exists**
- Error: "Resource already exists"
- Solution: Import existing resource or use data source instead

## Resources

- Agent Engine: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- VPC-SC: https://cloud.google.com/vpc-service-controls/docs
- Terraform Google Provider: https://registry.terraform.io/providers/hashicorp/google/latest
- ADK Terraform examples in {baseDir}/examples/
