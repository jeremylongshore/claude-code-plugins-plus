#!/bin/bash
# init-terraform.sh - Initialize Terraform for Vertex AI infrastructure

set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT_ID:-}}"
REGION="${2:-us-central1}"

if [[ -z "$PROJECT_ID" ]]; then
    echo "Usage: $0 <PROJECT_ID> [REGION]"
    exit 1
fi

echo "Initializing Terraform for Vertex AI Infrastructure"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

mkdir -p terraform/modules/vertex-ai

cat > terraform/main.tf <<EOF
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "$PROJECT_ID"
  region  = "$REGION"
}

module "vertex_ai" {
  source     = "./modules/vertex-ai"
  project_id = var.project_id
  region     = var.region
}
EOF

cat > terraform/variables.tf <<EOF
variable "project_id" {
  default = "$PROJECT_ID"
}

variable "region" {
  default = "$REGION"
}
EOF

echo "✓ Terraform initialized for Vertex AI"
