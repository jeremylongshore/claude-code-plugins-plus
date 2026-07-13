#!/bin/bash
# init-terraform.sh - Initialize Terraform for ADK infrastructure

set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT_ID:-}}"
REGION="${2:-us-central1}"

if [[ -z "$PROJECT_ID" ]]; then
    echo "Usage: $0 <PROJECT_ID> [REGION]"
    echo "Initialize Terraform configuration for ADK infrastructure"
    exit 1
fi

echo "Initializing Terraform for ADK Infrastructure"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Create terraform directory structure
mkdir -p terraform/{modules,envs/dev,envs/prod}

# Create main.tf
cat > terraform/main.tf <<'EOF'
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
EOF

# Create variables.tf
cat > terraform/variables.tf <<EOF
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "$PROJECT_ID"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "$REGION"
}

variable "agent_name" {
  description = "ADK Agent Name"
  type        = string
}

variable "enable_code_execution" {
  description = "Enable Code Execution Sandbox"
  type        = bool
  default     = true
}

variable "enable_memory_bank" {
  description = "Enable Memory Bank"
  type        = bool
  default     = true
}
EOF

# Create adk-agent module
mkdir -p terraform/modules/adk-agent
cat > terraform/modules/adk-agent/main.tf <<'EOF'
resource "google_service_account" "agent" {
  account_id   = "${var.agent_name}-sa"
  display_name = "Service Account for ${var.agent_name}"
}

resource "google_project_iam_member" "agent_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent.email}"
}

output "service_account_email" {
  value = google_service_account.agent.email
}
EOF

echo "✓ Terraform configuration initialized"
echo ""
echo "Next steps:"
echo "  cd terraform"
echo "  terraform init"
echo "  terraform plan"
echo "  terraform apply"
