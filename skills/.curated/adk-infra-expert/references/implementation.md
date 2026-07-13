# ADK Terraform - Implementation Details

## Configuration

### Backend Setup

```hcl
terraform {
  required_version = ">= 1.0"

  backend "gcs" {
    bucket = "my-project-tf-state"
    prefix = "adk-infrastructure"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.0"
    }
  }
}
```

### Provider Configuration

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
```

## Module Structure

```
modules/
├── agent-engine/       # Agent Engine runtime provisioning
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── iam/                # Service accounts and role bindings
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── networking/         # VPC, PSC subnets, firewall rules
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── vpc-service-controls/ # VPC-SC perimeters and access levels
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
```

## Advanced Patterns

### Code Execution Sandbox Configuration

The ADK Code Execution sandbox defaults to a 14-day TTL. Override with:

```hcl
resource "google_vertex_ai_agent_engine" "agent" {
  provider     = google-beta
  project      = var.project_id
  location     = var.region
  display_name = var.agent_config.display_name

  agent_engine_config {
    code_execution_config {
      enabled = var.agent_config.code_execution
      # Sandbox timeout: max 14 days (1209600 seconds)
      execution_timeout = "1209600s"
    }
    memory_bank_config {
      enabled = var.agent_config.memory_bank
    }
  }
}
```

### IAM Least Privilege Pattern

```hcl
resource "google_service_account" "agent_sa" {
  account_id   = "adk-agent-runner"
  display_name = "ADK Agent Runner (least privilege)"
}

resource "google_project_iam_member" "agent_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}
```

### Remote State Data Source

Reference ADK outputs from other Terraform configs:

```hcl
data "terraform_remote_state" "adk" {
  backend = "gcs"
  config = {
    bucket = "my-project-tf-state"
    prefix = "adk-infrastructure"
  }
}

# Use agent endpoint in another module
locals {
  agent_endpoint = data.terraform_remote_state.adk.outputs.agent_endpoint
}
```

## Troubleshooting

### API Enablement

Ensure the following APIs are enabled before running `terraform apply`:

```bash
gcloud services enable aiplatform.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  accesscontextmanager.googleapis.com \
  --project=PROJECT_ID
```

### State Lock Issues

If Terraform state is locked from a previous failed run:

```bash
terraform force-unlock LOCK_ID
```

### Quota Limits

Agent Engine has per-project quotas. Check current usage:

```bash
gcloud alpha quotas info list \
  --project=PROJECT_ID \
  --service=aiplatform.googleapis.com \
  --filter="metric:agent_engines"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
