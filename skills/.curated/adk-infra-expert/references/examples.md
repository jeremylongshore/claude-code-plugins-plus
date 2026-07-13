# ADK Terraform Examples

## Example 1: Minimal Agent Engine Runtime

Deploy a basic ADK Agent Engine with default settings for development.

```hcl
# variables.tf
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Agent Engine"
  type        = string
  default     = "us-central1"
}

# main.tf
module "adk_agent" {
  source     = "./modules/agent-engine"
  project_id = var.project_id
  region     = var.region

  agent_config = {
    display_name      = "dev-agent"
    model             = "gemini-2.0-flash"
    code_execution    = true
    memory_bank       = false
  }
}

output "agent_endpoint" {
  value = module.adk_agent.endpoint_uri
}
```

**Validation commands:**

```bash
terraform plan -var="project_id=my-project"
terraform apply -var="project_id=my-project" -auto-approve
gcloud ai agent-engines list --project=my-project --region=us-central1
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/my-project/locations/us-central1/agentEngines"
```

## Example 2: Production Agent with Memory Bank and VPC-SC

Full enterprise deployment with Memory Bank, Code Execution sandbox, and VPC Service Controls.

```hcl
# terraform.tfvars
project_id           = "prod-ai-project"
region               = "us-central1"
enable_vpc_sc        = true
enable_memory_bank   = true
enable_code_execution = true
access_policy_id     = "123456789"

# main.tf
module "networking" {
  source     = "./modules/networking"
  project_id = var.project_id
  region     = var.region

  psc_config = {
    subnet_name  = "adk-psc-subnet"
    ip_cidr      = "10.0.1.0/24"
  }
}

module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id

  service_accounts = {
    agent_runner = {
      display_name = "ADK Agent Runner"
      roles = [
        "roles/aiplatform.user",
        "roles/storage.objectViewer",
      ]
    }
    memory_writer = {
      display_name = "Memory Bank Writer"
      roles = [
        "roles/aiplatform.user",
        "roles/datastore.user",
      ]
    }
  }
}

module "adk_agent" {
  source     = "./modules/agent-engine"
  project_id = var.project_id
  region     = var.region

  agent_config = {
    display_name      = "prod-agent-v1"
    model             = "gemini-2.0-pro"
    code_execution    = var.enable_code_execution
    memory_bank       = var.enable_memory_bank
    service_account   = module.iam.service_accounts["agent_runner"].email
  }

  networking = {
    vpc_id     = module.networking.vpc_id
    subnet_id  = module.networking.psc_subnet_id
  }
}

module "vpc_sc" {
  count          = var.enable_vpc_sc ? 1 : 0
  source         = "./modules/vpc-service-controls"
  project_id     = var.project_id
  access_policy  = var.access_policy_id

  perimeter_config = {
    title    = "adk-perimeter"
    resources = ["projects/${var.project_id}"]
    restricted_services = [
      "aiplatform.googleapis.com",
      "storage.googleapis.com",
    ]
  }
}
```

**Validation commands:**

```bash
# Verify agent is reachable
gcloud ai agent-engines describe prod-agent-v1 \
  --project=prod-ai-project --region=us-central1

# Test Memory Bank connectivity
gcloud firestore databases list --project=prod-ai-project

# Verify VPC-SC perimeter
gcloud access-context-manager perimeters describe adk-perimeter \
  --policy=123456789

# Test agent invocation through PSC
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello agent"}' \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/prod-ai-project/locations/us-central1/agentEngines/prod-agent-v1:query"
```

## Example 3: Multi-Agent Architecture

Deploy multiple cooperating agents with shared Memory Bank.

```hcl
locals {
  agents = {
    orchestrator = {
      model          = "gemini-2.0-pro"
      code_execution = false
      memory_bank    = true
    }
    researcher = {
      model          = "gemini-2.0-flash"
      code_execution = true
      memory_bank    = true
    }
    coder = {
      model          = "gemini-2.0-pro"
      code_execution = true
      memory_bank    = false
    }
  }
}

module "agents" {
  for_each   = local.agents
  source     = "./modules/agent-engine"
  project_id = var.project_id
  region     = var.region

  agent_config = {
    display_name      = each.key
    model             = each.value.model
    code_execution    = each.value.code_execution
    memory_bank       = each.value.memory_bank
    service_account   = module.iam.service_accounts["agent_runner"].email
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
